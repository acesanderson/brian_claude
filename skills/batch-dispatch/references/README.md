# Batch Dispatch - Native Sandboxing

## Overview

The batch-dispatch skill leverages **Claude Code's built-in sandboxing** to provide secure isolation for parallel task execution. This eliminates the need for Docker while maintaining strong security guarantees.

## Architecture

```
Main Process (batch_runner.py)
├── Worker 1
│   ├── Working directory: batch_runs/.../task_0/
│   ├── Sandbox: Can only write to task_0/
│   └── OS enforcement: Seatbelt (macOS) or bubblewrap (Linux)
├── Worker 2
│   ├── Working directory: batch_runs/.../task_1/
│   ├── Sandbox: Can only write to task_1/
│   └── OS enforcement: Seatbelt (macOS) or bubblewrap (Linux)
└── ... (up to max-workers)
```

## How It Works

### 1. Claude Code's Native Sandboxing

When you enable sandboxing (`/sandbox` command), Claude Code uses OS-level primitives to enforce security:

**macOS:**
- Uses Apple's **Seatbelt** framework (built-in)
- Process-level filesystem restrictions
- Network filtering via proxy

**Linux/WSL2:**
- Uses **bubblewrap** for namespace isolation
- Requires: `sudo apt-get install bubblewrap socat`
- Same security model as macOS

### 2. Worker Isolation

Each worker is spawned with:
```python
subprocess.create_subprocess_exec(
    "claude", "-p", prompt, "--dangerously-skip-permissions",
    cwd=task_dir  # Worker starts in isolated directory
)
```

**Key insight:** The sandbox restricts writes to the current working directory (`cwd`). By setting each worker's `cwd` to a unique task directory, they're automatically isolated.

### 3. Security Enforcement

**Filesystem:**
- Workers can only write within their `task_N/` directory
- Attempts to write elsewhere are blocked at OS level
- Protected paths (like `~/.ssh`, `~/.bashrc`) are denied

**Network:**
- All connections go through proxy server
- Only allowed domains are accessible
- Domain allowlist configured in `~/.claude/settings.json`

**Process:**
- Child processes inherit sandbox restrictions
- No privilege escalation
- Resource limits enforced

## Security Guarantees

### What Workers CANNOT Do

Even with `--dangerously-skip-permissions`:

- ❌ **Modify files outside task directory**
  - Blocked: `~/.ssh/id_rsa`, `~/.bashrc`, `/etc/hosts`
  - OS-level enforcement, not prompt-based

- ❌ **Access unauthorized domains**
  - Network proxy blocks non-allowed domains
  - Immediate notification on violation

- ❌ **Escape sandbox**
  - All child processes inherit restrictions
  - Cannot use sudo/privilege escalation

### What Workers CAN Do

- ✅ **Read files** (subject to deny rules)
- ✅ **Write to task directory**
- ✅ **Access allowed domains**
- ✅ **Use approved skills**

### Protection Against Attacks

**Prompt Injection:**
```python
# Even if malicious prompt tricks Claude:
claude -p "rm -rf ~/*"  # In sandbox

# Result: Only deletes files in task_dir
# Your actual ~/ is untouched
```

**Malicious Dependencies:**
```bash
# NPM package with malicious postinstall script
npm install evil-package

# Sandbox blocks:
# - Writing to ~/.bashrc
# - Exfiltrating data to unapproved domains
# - Modifying files outside task directory
```

## Setup

### 1. Enable Sandboxing (Required)

```bash
# In Claude Code
> /sandbox

# Choose:
# - "Auto-allow mode" (recommended for batch-dispatch)
# - This auto-approves sandboxed commands
```

### 2. Configure Permissions (Recommended)

In `~/.claude/settings.json`:
```json
{
  "permissions": {
    "Bash": {
      "mode": "auto-allow"  // Auto-approve sandboxed bash commands
    },
    "Edit": {
      "deny": [
        "~/.ssh/*",
        "~/.aws/*",
        "~/.bashrc",
        "~/.zshrc",
        "/etc/*"
      ]
    },
    "Read": {
      "deny": [
        "~/.ssh/*",
        "~/.aws/*",
        "~/secrets/*"
      ]
    }
  },
  "sandbox": {
    "network": {
      "allowedDomains": [
        "*.anthropic.com",
        "api.example.com"
      ]
    }
  }
}
```

### 3. Verify Setup

```bash
# Check sandbox is configured
uv run batch_runner.py test '["item"]' "Test {{ item }}"

# Should NOT see:
# "⚠️ WARNING: Sandboxing does not appear to be configured"
```

## Performance

**No Docker Overhead:**
- Worker startup: ~0ms (no container)
- Uses native Claude binary
- Works cross-platform (macOS, Linux, WSL2)

**Compared to Docker approach:**
| Metric | Docker | Native Sandbox |
|--------|--------|----------------|
| Startup | ~1s | ~0ms |
| Platform | All | macOS, Linux, WSL2 |
| Setup | Build image | Run `/sandbox` |
| Isolation | Container | OS-level sandbox |

## Limitations

### Platform Support
- ✅ **macOS**: Full support (Seatbelt)
- ✅ **Linux**: Full support (requires bubblewrap)
- ✅ **WSL2**: Full support (requires bubblewrap)
- ❌ **WSL1**: Not supported (bubblewrap requires WSL2)
- ❌ **Native Windows**: Planned but not yet available

### Known Issues

**Unix Sockets:**
- If you allow access to `/var/run/docker.sock`, workers can escape via Docker
- Only allow trusted sockets

**Broad Write Permissions:**
- Allowing writes to directories in `$PATH` enables privilege escalation
- Keep write access narrow (task directory only)

**Nested Sandboxes:**
- Running inside Docker with `enableWeakerNestedSandbox: true` reduces security
- Avoid if possible

## Troubleshooting

### Sandbox Not Detected

**Problem:**
```
⚠️ WARNING: Sandboxing does not appear to be configured
```

**Solution:**
```bash
# Enable sandboxing
> /sandbox

# Or skip check (not recommended)
batch_runner.py ... --skip-sandbox-check
```

### Linux: Missing Dependencies

**Problem:**
```
bubblewrap: command not found
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install bubblewrap socat

# Fedora
sudo dnf install bubblewrap socat

# Arch
sudo pacman -S bubblewrap socat
```

### Workers Can Access Unexpected Files

**Problem:**
Workers can read files they shouldn't.

**Solution:**
Add deny rules to `~/.claude/settings.json`:
```json
{
  "permissions": {
    "Read": {
      "deny": ["~/secrets/*", "~/.ssh/*", "~/.aws/*"]
    }
  }
}
```

### Network Access Blocked

**Problem:**
Workers can't access required APIs.

**Solution:**
Add domains to allowlist:
```json
{
  "sandbox": {
    "network": {
      "allowedDomains": ["api.service.com", "*.example.com"]
    }
  }
}
```

## Advanced Usage

### Custom Proxy Configuration

For enterprise security:
```json
{
  "sandbox": {
    "network": {
      "httpProxyPort": 8080,
      "socksProxyPort": 8081,
      "allowedDomains": ["*.corp.com"]
    }
  }
}
```

### Monitoring Violations

Watch for sandbox violations:
```bash
# Check worker logs
tail -f batch_runs/*/task_*/*.log | grep -i "sandbox\|denied\|blocked"
```

### Testing Sandbox

Verify workers are sandboxed:
```python
# Test script
test_items = ['{"cmd": "touch ~/test.txt"}']  # Should fail
batch_runner.py test test_items "Run: {{ item }}"

# Check: ~/test.txt should NOT exist
ls ~/test.txt  # Should be "No such file"
```

## Development

### Running Tests

```bash
# Test sandbox enforcement
python -m pytest tests/test_sandbox.py

# Test with real workers
./tests/integration_test.sh
```

### Debugging Workers

```bash
# Enable verbose logging
export BATCH_DEBUG=1
uv run batch_runner.py ...

# Check worker output
cat batch_runs/*/task_*/stdout.log
```

## Learn More

- [Claude Code Sandboxing Docs](https://docs.anthropic.com/claude-code/sandboxing)
- [Security Best Practices](https://docs.anthropic.com/claude-code/security)
- [Permissions Reference](https://docs.anthropic.com/claude-code/permissions)
- [Sandbox Runtime (Open Source)](https://github.com/anthropics/sandbox-runtime)

## FAQ

**Q: Is this as secure as Docker?**
A: Yes - it uses the same OS-level primitives (namespaces, capabilities, filesystem restrictions). Docker provides additional process isolation, but for our use case (filesystem/network restrictions), they're equivalent.

**Q: Can I use this with other AI agents?**
A: The sandbox-runtime is open source and can sandbox any process, not just Claude Code. See: https://github.com/anthropics/sandbox-runtime

**Q: What if I need Docker for other reasons?**
A: You can still use Docker for environment isolation (dependencies, etc.) while relying on Claude's sandbox for security. They're complementary.

**Q: How do I report security issues?**
A: Report to Anthropic's security team: security@anthropic.com
