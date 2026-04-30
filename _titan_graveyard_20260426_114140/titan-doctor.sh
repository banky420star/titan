#!/usr/bin/env bash
set -u

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"

have() {
  command -v "$1" >/dev/null 2>&1
}

section() {
  printf '\n== %s ==\n' "$1"
}

note() {
  printf '%s\n' "$1"
}

check_json() {
  local file="$1"
  if have jq; then
    if jq empty "$file" >/dev/null 2>&1; then
      note "[ok] json syntax: $file"
    else
      note "[bad] json syntax: $file"
    fi
    return
  fi

  python3 - <<'PY' "$file"
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
try:
    json.loads(path.read_text())
    print(f"[ok] json syntax: {path}")
except Exception:
    print(f"[bad] json syntax: {path}")
PY
}

check_toml() {
  local file="$1"
  python3 - <<'PY' "$file"
import pathlib, sys, tomllib
path = pathlib.Path(sys.argv[1])
try:
    tomllib.loads(path.read_text())
    print(f"[ok] toml syntax: {path}")
except Exception:
    print(f"[bad] toml syntax: {path}")
PY
}

check_yaml() {
  local file="$1"
  python3 - <<'PY' "$file"
import pathlib, sys
path = pathlib.Path(sys.argv[1])
try:
    import yaml  # type: ignore
except Exception:
    print(f"[skip] yaml syntax not checked (PyYAML missing): {path}")
    raise SystemExit(0)
try:
    yaml.safe_load(path.read_text())
    print(f"[ok] yaml syntax: {path}")
except Exception:
    print(f"[bad] yaml syntax: {path}")
PY
}

section "Titan Doctor"
note "root: $ROOT"
note "time_utc: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

section "Runtime"
TTY_VALUE="$(tty 2>/dev/null || true)"
if [ -z "$TTY_VALUE" ] || [ "$TTY_VALUE" = "not a tty" ]; then
  TTY_VALUE="none"
fi
note "shell: ${SHELL:-unknown}"
note "pwd: $(pwd)"
note "user: $(id -un 2>/dev/null || echo unknown)"
note "tty: $TTY_VALUE"
note "os: $(uname -srmo 2>/dev/null || uname -a)"
note "node: $(node --version 2>/dev/null || echo missing)"
note "npm: $(npm --version 2>/dev/null || echo missing)"
note "python: $(python3 --version 2>/dev/null || echo missing)"

section "Command Availability"
for cmd in rg jq git curl wget tmux screen ollama codex titan; do
  if have "$cmd"; then
    note "[ok] $cmd -> $(command -v "$cmd")"
  else
    note "[missing] $cmd"
  fi
done

section "Environment Hints"
for key in \
  OPENAI_API_KEY OPENAI_BASE_URL OPENAI_ORG_ID \
  ANTHROPIC_API_KEY GOOGLE_API_KEY GEMINI_API_KEY \
  OLLAMA_HOST OLLAMA_MODELS \
  TITAN_CONFIG TITAN_HOME TITAN_MODEL TITAN_ROUTER \
  AGENT_MODEL PLANNER_MODEL CODER_MODEL REVIEWER_MODEL TOOL_MODEL; do
  if [ -n "${!key:-}" ]; then
    note "[set] $key"
  else
    note "[unset] $key"
  fi
done

section "Candidate Config Files"
mapfile -t CONFIG_FILES < <(find "$ROOT" -maxdepth 3 -type f \( \
  -iname '*titan*.json' -o -iname '*titan*.yaml' -o -iname '*titan*.yml' -o \
  -iname '*titan*.toml' -o -iname '.env' -o -iname '.env.*' -o \
  -iname 'config.json' -o -iname 'config.yaml' -o -iname 'config.yml' -o -iname 'config.toml' \
  \) | sort)

if [ "${#CONFIG_FILES[@]}" -eq 0 ]; then
  note "[warn] no likely config files found under $ROOT"
else
  printf '%s\n' "${CONFIG_FILES[@]}"
fi

section "Config Syntax"
for file in "${CONFIG_FILES[@]}"; do
  case "$file" in
    *.json) check_json "$file" ;;
    *.toml) check_toml "$file" ;;
    *.yaml|*.yml) check_yaml "$file" ;;
    *) note "[skip] env-like file not syntax checked: $file" ;;
  esac
done

section "Routing Signals"
if have rg; then
  rg -n -S \
    -e 'planner|coder|reviewer|router|routing|fallback|provider|model|tools?|approval|sandbox|timeout|stream|shell' \
    "$ROOT" \
    --glob '!**/.git/**' \
    --glob '!**/node_modules/**' \
    --glob '!**/.venv/**' \
    --glob '!**/dist/**' \
    --glob '!**/build/**' \
    --glob '!**/output/**' \
    2>/dev/null | head -n 120
else
  note "[skip] rg missing, routing scan not run"
fi

section "Recent Log Files"
mapfile -t LOG_FILES < <(find "$ROOT" -maxdepth 4 -type f \( \
  -iname '*.log' -o -path '*/logs/*' -o -path '*/.logs/*' \
  \) | sort | tail -n 20)

if [ "${#LOG_FILES[@]}" -eq 0 ]; then
  note "[warn] no log files found"
else
  printf '%s\n' "${LOG_FILES[@]}"
fi

section "Likely Misconfigurations"
if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -z "${GOOGLE_API_KEY:-}" ] && [ -z "${GEMINI_API_KEY:-}" ] && [ -z "${OLLAMA_HOST:-}" ]; then
  note "[risk] no provider credentials or local model host env vars detected"
fi

if [ -n "${PLANNER_MODEL:-}" ] || [ -n "${CODER_MODEL:-}" ] || [ -n "${REVIEWER_MODEL:-}" ]; then
  note "[hint] role-specific model env vars are present; verify every referenced model exists in the selected provider"
else
  note "[hint] no role-specific model env vars detected; Titan may be using one default model for everything"
fi

if [ -z "${TERM:-}" ]; then
  note "[risk] TERM is unset; interactive terminal features may fail"
fi

if [ -z "${SHELL:-}" ]; then
  note "[risk] SHELL is unset; shell tool routing can become brittle"
fi

section "Next Command"
cat <<EOF
Share these three things when you want deeper help:
1. The full output of: $(basename "$0") "$ROOT"
2. One failing command or prompt and the exact error text
3. The main config file that defines Titan models/tools/routes
EOF
