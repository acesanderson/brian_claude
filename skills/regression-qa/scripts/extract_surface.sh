#!/usr/bin/env bash
# extract_surface.sh — Extract public API/CLI surface from a project
# Usage: extract_surface.sh <project_root>
# Output: JSON array of discovered endpoints/commands

set -euo pipefail

PROJECT_ROOT="${1:-.}"
cd "$PROJECT_ROOT"

python3 - <<'PYEOF'
import os, re, json, sys
from pathlib import Path

root = Path(".")
findings = []

def find_files(pattern, *exts):
    results = []
    for ext in exts:
        results.extend(root.rglob(f"*.{ext}"))
    return [f for f in results if not any(p in f.parts for p in ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'])]

# ── OpenAPI / Swagger ─────────────────────────────────────────────────────────
for spec_name in ["openapi.yaml", "openapi.json", "swagger.yaml", "swagger.json", "api.yaml", "api.json"]:
    for spec_path in list(root.rglob(spec_name)):
        if any(p in spec_path.parts for p in ['.git', 'node_modules']):
            continue
        try:
            import yaml
            with open(spec_path) as f:
                spec = yaml.safe_load(f) if spec_name.endswith('.yaml') else json.load(f)
            for path, methods in (spec.get("paths") or {}).items():
                for method in methods:
                    if method.lower() in ("get","post","put","patch","delete","head","options"):
                        findings.append({"type": "http", "method": method.upper(), "path": path, "source": str(spec_path)})
        except Exception as e:
            findings.append({"type": "error", "source": str(spec_path), "error": str(e)})

# ── Python web frameworks ─────────────────────────────────────────────────────
py_route_pattern = re.compile(
    r'@(?:app|router|blueprint|bp|api)\.(get|post|put|patch|delete|head|options)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE
)
py_route_pattern2 = re.compile(
    r'@(?:app|blueprint|bp)\.route\s*\(\s*["\']([^"\']+)["\'].*?methods\s*=\s*\[([^\]]+)\]',
    re.IGNORECASE | re.DOTALL
)

for f in find_files("*", "py"):
    try:
        text = f.read_text(errors='ignore')
        for m in py_route_pattern.finditer(text):
            findings.append({"type": "http", "method": m.group(1).upper(), "path": m.group(2), "source": str(f)})
        for m in py_route_pattern2.finditer(text):
            methods = [x.strip().strip('"\'') for x in m.group(2).split(',')]
            for method in methods:
                findings.append({"type": "http", "method": method.upper(), "path": m.group(1), "source": str(f)})
    except Exception:
        pass

# Django urlpatterns
django_pattern = re.compile(r'path\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE)
for f in find_files("urls", "py"):
    try:
        text = f.read_text(errors='ignore')
        for m in django_pattern.finditer(text):
            findings.append({"type": "http", "method": "ANY", "path": "/" + m.group(1), "source": str(f)})
    except Exception:
        pass

# ── Python CLI (Click / Typer) ────────────────────────────────────────────────
cli_pattern = re.compile(r'@(?:\w+)\.command\s*\(\s*(?:name\s*=\s*)?["\']?(\w*)["\']?\s*\)')
for f in find_files("*", "py"):
    try:
        text = f.read_text(errors='ignore')
        for m in cli_pattern.finditer(text):
            name = m.group(1) or "default"
            findings.append({"type": "cli_command", "name": name, "source": str(f)})
    except Exception:
        pass

# argparse subparsers
argparse_pattern = re.compile(r'add_parser\s*\(\s*["\']([^"\']+)["\']')
for f in find_files("*", "py"):
    try:
        text = f.read_text(errors='ignore')
        for m in argparse_pattern.finditer(text):
            findings.append({"type": "cli_command", "name": m.group(1), "source": str(f)})
    except Exception:
        pass

# ── JavaScript / TypeScript (Express) ─────────────────────────────────────────
js_route_pattern = re.compile(
    r'(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\`]([^"\'`]+)["\`]',
    re.IGNORECASE
)
for f in find_files("*", "js", "ts", "mjs"):
    try:
        text = f.read_text(errors='ignore')
        for m in js_route_pattern.finditer(text):
            findings.append({"type": "http", "method": m.group(1).upper(), "path": m.group(2), "source": str(f)})
    except Exception:
        pass

# ── Go (chi / gin / mux) ─────────────────────────────────────────────────────
go_route_pattern = re.compile(
    r'(?:r|router|mux)\.(Get|Post|Put|Patch|Delete|Handle)\s*\(\s*"([^"]+)"',
    re.IGNORECASE
)
for f in find_files("*", "go"):
    try:
        text = f.read_text(errors='ignore')
        for m in go_route_pattern.finditer(text):
            findings.append({"type": "http", "method": m.group(1).upper(), "path": m.group(2), "source": str(f)})
    except Exception:
        pass

# ── Deduplicate ───────────────────────────────────────────────────────────────
seen = set()
deduped = []
for item in findings:
    key = (item.get("type"), item.get("method",""), item.get("path", item.get("name","")))
    if key not in seen:
        seen.add(key)
        deduped.append(item)

print(json.dumps(deduped, indent=2))
PYEOF
