#!/usr/bin/env bash
# Usage: sdd-state.sh <state_name>
# Writes {"state": "...", "cwd": "..."} to ~/.claude/sdd_state.json
jq -n --arg s "$1" --arg c "$PWD" '{state:$s,cwd:$c}' > "$HOME/.claude/sdd_state.json"
