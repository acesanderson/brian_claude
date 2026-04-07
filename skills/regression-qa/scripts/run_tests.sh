#!/usr/bin/env bash
# run_tests.sh — Universal test runner with structured JSON output
# Usage: run_tests.sh <project_root> [test_id]
#   project_root: path to the project
#   test_id:      optional specific test to run (pytest node id, test name, etc.)

set -euo pipefail

PROJECT_ROOT="${1:-.}"
TEST_ID="${2:-}"
cd "$PROJECT_ROOT"

# Detect test framework
detect_framework() {
    if [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "setup.cfg" ]; then
        if python -c "import pytest" 2>/dev/null || command -v pytest &>/dev/null; then
            echo "pytest"
            return
        fi
    fi
    if [ -f "package.json" ]; then
        if grep -q '"vitest"' package.json 2>/dev/null; then echo "vitest"; return; fi
        if grep -q '"jest"' package.json 2>/dev/null; then echo "jest"; return; fi
    fi
    if [ -f "go.mod" ]; then echo "gotest"; return; fi
    if [ -f "Cargo.toml" ]; then echo "cargo"; return; fi
    echo "unknown"
}

FRAMEWORK=$(detect_framework)

# Look for regression-qa tests dir first, fall back to project test dirs
find_test_dir() {
    for d in "regression-qa/tests" "tests" "test" "spec"; do
        [ -d "$d" ] && echo "$d" && return
    done
    echo "."
}

TEST_DIR=$(find_test_dir)

run_pytest() {
    local extra_args=()
    [ -n "$TEST_ID" ] && extra_args+=("$TEST_ID") || extra_args+=("$TEST_DIR")

    # Run pytest with JSON report
    local tmp_json
    tmp_json=$(mktemp /tmp/pytest_report_XXXXXX.json)

    set +e
    python -m pytest "${extra_args[@]}" \
        --json-report --json-report-file="$tmp_json" \
        --tb=short -q 2>/tmp/pytest_stderr.txt
    local exit_code=$?
    set -e

    if [ -f "$tmp_json" ]; then
        python3 - "$tmp_json" <<'PYEOF'
import sys, json

with open(sys.argv[1]) as f:
    report = json.load(f)

summary = report.get("summary", {})
failures = []

for test in report.get("tests", []):
    if test["outcome"] in ("failed", "error"):
        call = test.get("call") or test.get("setup") or {}
        failures.append({
            "test": test["nodeid"],
            "outcome": test["outcome"],
            "error": call.get("longrepr", "")[:2000]
        })

print(json.dumps({
    "framework": "pytest",
    "passed": summary.get("passed", 0),
    "failed": summary.get("failed", 0),
    "errors": summary.get("error", 0),
    "skipped": summary.get("skipped", 0),
    "failures": failures
}, indent=2))
PYEOF
        rm -f "$tmp_json"
    else
        # Fallback: parse pytest stdout
        echo '{"framework":"pytest","passed":0,"failed":0,"errors":1,"skipped":0,"failures":[{"test":"unknown","outcome":"error","error":"pytest-json-report not available or pytest failed to start"}]}'
    fi
}

run_jest() {
    local extra_args=()
    [ -n "$TEST_ID" ] && extra_args+=("--testNamePattern=$TEST_ID")

    set +e
    local output
    output=$(npx jest "${extra_args[@]}" --json 2>/dev/null)
    set -e

    echo "$output" | python3 -c "
import sys, json
data = json.load(sys.stdin)
failures = []
for suite in data.get('testResults', []):
    for t in suite.get('testResults', []):
        if t['status'] == 'failed':
            failures.append({'test': t['fullName'], 'outcome': 'failed', 'error': ' '.join(t.get('failureMessages', []))[:2000]})
print(json.dumps({
    'framework': 'jest',
    'passed': data.get('numPassedTests', 0),
    'failed': data.get('numFailedTests', 0),
    'errors': 0,
    'skipped': data.get('numPendingTests', 0),
    'failures': failures
}, indent=2))
"
}

run_gotest() {
    local pkg="${TEST_ID:-./...}"
    set +e
    local output
    output=$(go test -json "$pkg" 2>&1)
    set -e

    echo "$output" | python3 -c "
import sys, json
passed = failed = 0
failures = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        ev = json.loads(line)
    except:
        continue
    action = ev.get('Action')
    if action == 'pass':
        passed += 1
    elif action == 'fail':
        failed += 1
        failures.append({'test': ev.get('Test', ev.get('Package', 'unknown')), 'outcome': 'failed', 'error': ev.get('Output', '')[:2000]})
print(json.dumps({'framework':'gotest','passed':passed,'failed':failed,'errors':0,'skipped':0,'failures':failures}, indent=2))
"
}

run_cargo() {
    set +e
    local output
    output=$(cargo test 2>&1)
    set -e

    echo "$output" | python3 -c "
import sys, re
text = sys.stdin.read()
passed = int((re.search(r'(\d+) passed', text) or [None,'0'])[1])
failed = int((re.search(r'(\d+) failed', text) or [None,'0'])[1])
failures = []
for m in re.finditer(r'---- (.+?) stdout ----\n(.*?)(?=\n---- |\Z)', text, re.DOTALL):
    failures.append({'test': m.group(1), 'outcome': 'failed', 'error': m.group(2)[:2000]})
import json
print(json.dumps({'framework':'cargo','passed':passed,'failed':failed,'errors':0,'skipped':0,'failures':failures}, indent=2))
"
}

case "$FRAMEWORK" in
    pytest)   run_pytest ;;
    jest)     run_jest ;;
    vitest)   run_jest ;;  # vitest has jest-compatible JSON output
    gotest)   run_gotest ;;
    cargo)    run_cargo ;;
    *)
        echo '{"framework":"unknown","passed":0,"failed":0,"errors":1,"skipped":0,"failures":[{"test":"detection","outcome":"error","error":"Could not detect test framework. Supported: pytest, jest, vitest, go test, cargo test"}]}'
        ;;
esac
