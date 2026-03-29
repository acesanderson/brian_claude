#!/usr/bin/env bash
input=$(cat)

skill=$(echo "$input" | jq -r '.tool_input.skill_name // ""')

case "$skill" in
  kickoff_interview|design_review|adversarial_review|plan_generation|executing|wrap_up_adr|wrap_up_claude_md)
    cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
    [[ -z "$cwd" ]] && exit 0
    state_file="$HOME/.claude/sdd_state.json"
    tmp=$(mktemp)
    if [[ -f "$state_file" ]]; then
      jq --arg cwd "$cwd" --arg state "$skill" '.[$cwd] = $state' "$state_file" > "$tmp"
    else
      jq -n --arg cwd "$cwd" --arg state "$skill" '{($cwd): $state}' > "$tmp"
    fi
    mv "$tmp" "$state_file"
    ;;
esac
