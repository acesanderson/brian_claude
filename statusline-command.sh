#!/usr/bin/env bash
input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
model=$(echo "$input" | jq -r '.model.id // ""')
ctx_remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // ""')
duration_ms=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')
cost_usd=$(echo "$input" | jq -r '.cost.total_cost_usd // ""')

# Abbreviate home as ~
display_dir="${cwd/#$HOME/\~}"

# Git branch
git_branch=$(git -C "$cwd" rev-parse --abbrev-ref HEAD 2>/dev/null)

# Format duration: ms -> h?m?s
duration_s=$(( duration_ms / 1000 ))
if (( duration_s >= 3600 )); then
    duration_fmt="$(( duration_s / 3600 ))h$(( (duration_s % 3600) / 60 ))m"
elif (( duration_s >= 60 )); then
    duration_fmt="$(( duration_s / 60 ))m$(( duration_s % 60 ))s"
else
    duration_fmt="${duration_s}s"
fi

# Colors
dim=$'\033[2m'
cyan=$'\033[36m'
yellow=$'\033[33m'
red=$'\033[31m'
green=$'\033[32m'
reset=$'\033[0m'

# ctx progress bar with true-color gradient (green->yellow->red, fixed positions)
grad_r=(0 44 88 132 176 200 200 200 200 200)
grad_g=(200 200 200 200 200 176 132 88 44 0)

if [[ -n "$ctx_remaining" ]]; then
    if (( ctx_remaining > 50 )); then
        pct_color="$green"
    elif (( ctx_remaining > 20 )); then
        pct_color="$yellow"
    else
        pct_color="$red"
    fi
    filled=$(( (100 - ctx_remaining) * 10 / 100 ))
    bar=""
    for i in $(seq 1 10); do
        if (( i <= filled )); then
            r=${grad_r[$((i-1))]}
            g=${grad_g[$((i-1))]}
            bar="${bar}\033[38;2;${r};${g};0m█"
        else
            bar="${bar}${dim}░"
        fi
    done
    ctx_str="$(printf "[${bar}${reset}]") ${pct_color}${ctx_remaining}%${reset}"
else
    ctx_str="${dim}[░░░░░░░░░░] --%${reset}"
fi

if [[ -n "$cost_usd" && "$cost_usd" != "null" ]]; then
    cost_str=$(printf "${dim}\$%.2f${reset}" "$cost_usd")
else
    cost_str="${dim}\$--.--${reset}"
fi

sep="${dim} | ${reset}"

if [[ -n "$git_branch" ]]; then
    printf "${cyan}%s${reset}${sep}${dim}%s${reset}${sep}${dim}%s${reset}${sep}%s${sep}${dim}%s${reset}${sep}%s" \
        "$display_dir" "$git_branch" "$model" "$ctx_str" "$duration_fmt" "$cost_str"
else
    printf "${cyan}%s${reset}${sep}${dim}%s${reset}${sep}%s${sep}${dim}%s${reset}${sep}%s" \
        "$display_dir" "$model" "$ctx_str" "$duration_fmt" "$cost_str"
fi
