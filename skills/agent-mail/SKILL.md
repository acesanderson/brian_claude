---
name: agent-mail
description: >
  Inter-agent messaging via the agent-mail CLI. Use this skill whenever you need to communicate
  with another Claude Code agent: sending information one-way, starting a structured negotiation
  (e.g., agreeing on an API contract, data schema, or interface), replying to an ongoing thread,
  or checking for messages from peers. This is the standard inter-agent communication channel —
  invoke it any time you're in a multi-agent workflow and need to talk to a peer, hand off context,
  or reach agreement on a shared design. Also use it when the user asks an agent to "check its inbox",
  "message another agent", "coordinate with", or "define an interface with" another agent.
---

# Agent Mail

`agent-mail` is a Postgres-backed CLI for inter-agent messaging. It supports one-way emails and
structured multi-turn chat threads.

## Invocation — read this first

`agent-mail` is a **local project**, not a PyPI package. Do NOT use `uv tool install`, `uv tool run`, `pip install`, or any package registry. It will not be found there.

The one correct invocation:

```bash
uv run --directory /Users/bianders/vibe/agent-mail agent-mail <command>
```

Set an alias at the start of your session and use it throughout:

```bash
alias agent-mail='uv run --directory /Users/bianders/vibe/agent-mail agent-mail'
```

Do not search for `migrate.py`. The database is already provisioned. Just run commands.

## Your identity

Pick a short, role-descriptive name for yourself and use it consistently throughout the session.

Good names: `frontend-agent`, `api-designer`, `data-pipeline-agent`, `test-agent`

Bad names: `claude`, `assistant`, `agent` (too generic — collisions likely)

If you were told your name by the user or by a message you received, use that name exactly.

**Register immediately at session start** — before doing anything else:

```bash
agent-mail register --as <your-name> --json
```

This is a no-op if you later send messages, but it lets other agents find you and start threads
without waiting for you to speak first.

## When to use email vs chat

**Use `send` (one-way email)** when:
- You're broadcasting information with no reply expected
- You're handing off a result to another agent
- The message is a status update

**Use `chat` (multi-turn thread)** when:
- You need agreement from the other agent (API contracts, schemas, interfaces)
- The outcome requires back-and-forth negotiation
- You need the other agent to confirm before you proceed

## Command reference

All commands support `--json` for machine-readable output. Always use it when parsing output programmatically.

The examples below assume the alias is set. If not, prefix every `agent-mail` with `uv run --directory /Users/bianders/vibe/agent-mail agent-mail`.

### Send a one-way email

```bash
agent-mail send \
  --from <your-name> \
  --to <recipient-name> \
  --subject "<subject>" \
  --body "<body>" \
  --json
```

### Start a chat thread

```bash
agent-mail chat \
  --from <your-name> \
  --to <recipient-name> \
  --purpose "<what this conversation is for>" \
  --end-state "<what 'done' looks like — concrete and verifiable>" \
  --body "<your opening message>" \
  --json
```

The response includes `thread_id` — save it, you'll need it for replies.

`--turn-limit N` is optional. Useful when you want to cap a negotiation (e.g., `--turn-limit 6`).

### Reply to a thread

```bash
agent-mail reply \
  --thread <thread-uuid> \
  --from <your-name> \
  --body "<your message>" \
  --json
```

Add `--resolve` when the thread has reached its `end-state` and no further turns are needed:

```bash
agent-mail reply \
  --thread <thread-uuid> \
  --from <your-name> \
  --body "Agreed. Proceeding with that interface." \
  --resolve \
  --json
```

### Check your inbox

```bash
agent-mail inbox <your-name> --json          # sent + received (default)
agent-mail inbox <your-name> --received --json  # only messages to you
agent-mail inbox <your-name> --sent --json      # only messages from you
```

Each item in the response is either an email (`type: "email"`) or the latest turn of a chat thread
(`type: "chat"`). Check `status` on chat items: `"open"` means waiting for a reply.

### Read a full thread

```bash
agent-mail thread <thread-uuid> --json
```

Returns all turns in order. Read this before replying if you need the full context.

### Register without sending

```bash
agent-mail register --as <your-name> --json
```

### Find another agent's UUID (debugging only)

```bash
agent-mail find <name> --json
```

Do **not** call `find` before starting a chat to check if the recipient exists. The recipient
does not need to be pre-registered — just send. Checking first and bailing on `AGENT_NOT_FOUND`
is the anti-pattern that caused latching failures.

### List everything (all agents, all mail)

```bash
agent-mail list --json
```

## JSON response format

**Success:**
```json
{"success": true, "data": { ... }}
```

**Error:**
```json
{"success": false, "error": "...", "code": "THREAD_RESOLVED"}
```

Exit code 0 = success. Exit code 1 = runtime error. Exit code 2 = bad input.

### Error codes

| Code | Meaning |
|------|---------|
| `THREAD_RESOLVED` | Thread is closed — no more replies |
| `THREAD_NOT_FOUND` | UUID doesn't exist |
| `NOT_PARTICIPANT` | You're not in this thread |
| `TURN_LIMIT_EXCEEDED` | Turn cap reached |
| `AGENT_NOT_FOUND` | No agent registered with that name |
| `BAD_INPUT` | Validation failed (empty name, body too large, self-message) |
| `DB_UNREACHABLE` | Can't connect — check VPN |

## Workflow: negotiating a shared interface

This is the core use case for `chat`. Use it when two agents need to agree on something before either
can proceed (API contract, data schema, shared protocol, etc.).

**Initiating agent:**

```bash
# Start the thread
RESULT=$(agent-mail chat \
  --from frontend-agent \
  --to backend-agent \
  --purpose "Agree on the /api/auth/login request and response schema" \
  --end-state "Both agents have confirmed the schema in writing and are ready to implement" \
  --body "I need to implement the login form. What should the POST body look like, and what will you return?" \
  --json)

THREAD_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['thread_id'])")
echo "Thread: $THREAD_ID"
```

Then poll your inbox for the reply:

```bash
# Poll inbox until you see an open thread from backend-agent
agent-mail inbox frontend-agent --received --json
```

**Receiving agent** (checks inbox, reads thread, replies):

```bash
# Check inbox
agent-mail inbox backend-agent --received --json

# Read the full thread if needed
agent-mail thread <thread-uuid> --json

# Reply
agent-mail reply \
  --thread <thread-uuid> \
  --from backend-agent \
  --body "POST /api/auth/login with {\"email\": string, \"password\": string}. Returns {\"token\": string, \"user\": {\"id\": int, \"email\": string}} or 401." \
  --json
```

**Initiating agent** confirms and resolves:

```bash
agent-mail reply \
  --thread <thread-uuid> \
  --from frontend-agent \
  --body "Confirmed. Implementing against that schema now." \
  --resolve \
  --json
```

Once resolved, both agents can proceed with implementation independently.

## Keeping the human informed

The human operator is watching both agents and needs to follow the conversation. Whenever you send
or receive a message, print a brief readable summary to your conversation — not the raw JSON.

**When you send:**
```
[agent-mail] → backend-agent
Subject: API contract for /auth/login
"I need to implement the login form. What should the POST body look like..."
Thread: a3f2b1c4-...
```

**When you receive (from inbox or thread):**
```
[agent-mail] ← frontend-agent (turn 1, open)
"I need to implement the login form. What should the POST body look like..."
```

**When a thread resolves:**
```
[agent-mail] Thread a3f2b1c4-... resolved.
Outcome: Both agents agreed on POST /api/auth/login schema.
```

Keep summaries short — one header line, then the message body (truncated at ~200 chars if long).
The goal is that the human can read the conversation in their session without having to query the
database themselves.

## Autonomous negotiation loop

When participating in a chat thread, **run the full negotiation autonomously** — don't take one turn and stop. After sending a reply, background a polling task, wait for the notification, then act on it. Repeat until the thread resolves.

### Step 1 — Load TaskCreate

TaskCreate is a deferred tool. Load it before starting any polling:

```
ToolSearch query="select:TaskCreate,TaskOutput"
```

### Step 2 — Background the poll

After sending each reply, immediately create a background task to watch for the next turn. Do NOT use a raw Bash for-loop — that requires a permission approval for the whole script. TaskCreate runs it cleanly in the background and wakes you when it's done.

```python
# Pseudocode for what to pass to TaskCreate:
description = "Poll thread <thread-uuid> for turn > <N> from anyone except <my-name>"
command = """
THREAD_ID="<thread-uuid>"
MY_NAME="<your-name>"
CURRENT_TURN=<turn-you-just-sent>

for i in $(seq 1 24); do
  RESULT=$(uv run --directory /Users/bianders/vibe/agent-mail agent-mail thread "$THREAD_ID" --json)
  TURN=$(echo "$RESULT" | python3 -c "import sys,json; t=json.load(sys.stdin)['data']; print(t[-1]['turn'])")
  FROM=$(echo "$RESULT" | python3 -c "import sys,json; t=json.load(sys.stdin)['data']; print(t[-1]['from_name'])")
  STATUS=$(echo "$RESULT" | python3 -c "import sys,json; t=json.load(sys.stdin)['data']; print(t[-1]['status'])")
  if [ "$STATUS" = "resolved" ]; then echo "resolved"; exit 0; fi
  if [ "$TURN" -gt "$CURRENT_TURN" ] && [ "$FROM" != "$MY_NAME" ]; then echo "new turn $TURN"; exit 0; fi
  sleep 5
done
echo "timeout"
"""
```

### Step 3 — Wait for the notification, then reply

When the background task completes, you'll receive a `<task-notification>`. At that point:

1. Read the thread to get the latest turn
2. Compose and send your reply
3. If the thread is now resolved (status = "resolved"), stop — don't send another reply
4. Otherwise, go back to Step 2

```bash
# Read the thread after notification
uv run --directory /Users/bianders/vibe/agent-mail agent-mail thread "$THREAD_ID" --json
```

### Step 4 — Resolve when done

When the end-state is reached:

```bash
uv run --directory /Users/bianders/vibe/agent-mail agent-mail reply \
  --thread "$THREAD_ID" --from "$MY_NAME" \
  --body "Agreed. Proceeding." --resolve --json
```

**The loop terminates when:**
- You send `--resolve`
- The other agent sent `--resolve` (status = "resolved" in the thread)
- The poll task exits with "timeout" — bail and tell the user the other agent hasn't responded

## After resolution: persist the outcome

Once a thread resolves, the agreed contract only lives in the database and your session output.
**Always persist it in two places:**

### 1. Contract file in the project directory

Write the outcome to a file in your project's working directory:

```
CONTRACT.md         # if the whole project is about this contract
contracts/<topic>.md  # if the project has multiple contracts
```

Format it as a simple, human-readable spec — not JSON, not prose. Future agents and humans should
be able to implement from it without reading the thread.

### 2. Send a copy to the `contracts` inbox

```bash
agent-mail send \
  --from <your-name> \
  --to contracts \
  --subject "<topic> — agreed contract" \
  --body "<the full agreed spec, same content as the file>" \
  --json
```

The `contracts` inbox is a shared archive. Anyone can run `agent-mail inbox contracts --json` to
retrieve all finalized agreements across sessions.

**Both steps are required.** The file is for your project; the email is for the shared record.
