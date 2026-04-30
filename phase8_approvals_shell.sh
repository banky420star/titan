#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p agent_core docs backups logs approvals

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase8_$STAMP"

cp titan_terminal.py "backups/phase8_$STAMP/titan_terminal.py" 2>/dev/null || true
cp agent_core/tools.py "backups/phase8_$STAMP/tools.py" 2>/dev/null || true
cp config.json "backups/phase8_$STAMP/config.json" 2>/dev/null || true

echo "[1/5] Updating config..."

python3 - <<'PY'
import json
from pathlib import Path

path = Path("config.json")
config = json.loads(path.read_text()) if path.exists() else {}

config.setdefault("permission_mode", "power")

config["allowed_command_prefixes"] = [
    "python",
    "python3",
    "pip",
    "ls",
    "pwd",
    "cat",
    "find",
    "grep",
    "mkdir",
    "touch",
    "pytest",
    "node",
    "npm",
    "git",
    "ollama"
]

config["blocked_command_fragments"] = [
    "sudo ",
    " rm -rf /",
    "rm -rf /",
    "diskutil erase",
    "mkfs",
    "dd if=",
    "dd of=",
    ":(){",
    "chmod -R 777 /",
    "chown -R",
    "curl ",
    "wget "
]

path.write_text(json.dumps(config, indent=2))
print("Config updated with permission_mode and command rules.")
PY

echo "[2/5] Writing agent_core/approvals.py..."

cat > agent_core/approvals.py <<'PY'
from pathlib import Path
import json
import shlex

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG = BASE / "config.json"

SAFE_READ_PREFIXES = {
    "ls",
    "pwd",
    "cat",
    "find",
    "grep"
}

WRITE_PREFIXES = {
    "python",
    "python3",
    "pip",
    "mkdir",
    "touch",
    "pytest",
    "node",
    "npm",
    "git",
    "ollama"
}

HARD_BLOCK_FRAGMENTS = [
    "sudo ",
    " rm -rf /",
    "rm -rf /",
    "diskutil erase",
    "mkfs",
    "dd if=",
    "dd of=",
    ":(){",
    "chmod -R 777 /",
    "chown -R"
]


def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def save_config(config):
    CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")


def get_mode():
    return load_config().get("permission_mode", "power")


def set_mode(mode):
    mode = str(mode or "").strip().lower()

    if mode not in ["safe", "power", "agentic"]:
        return "Unknown mode. Use safe, power, or agentic."

    config = load_config()
    config["permission_mode"] = mode
    save_config(config)

    return "Permission mode set to: " + mode


def permission_status():
    config = load_config()
    mode = config.get("permission_mode", "power")
    allowed = config.get("allowed_command_prefixes", [])

    return (
        f"Permission mode: {mode}\n\n"
        "Modes:\n"
        "- safe: read/check commands only\n"
        "- power: normal workspace build commands\n"
        "- agentic: broader autonomous build commands, still blocks destructive commands\n\n"
        "Allowed prefixes:\n"
        + "\n".join("- " + x for x in allowed)
    )


def validate_command(command):
    config = load_config()
    mode = config.get("permission_mode", "power")
    command = str(command or "").strip()

    if not command:
        return False, "No command provided.", []

    lowered = command.lower()

    blocked = config.get("blocked_command_fragments", HARD_BLOCK_FRAGMENTS)

    for fragment in blocked:
        if fragment.lower() in lowered:
            return False, "Blocked dangerous fragment: " + fragment, []

    try:
        parts = shlex.split(command)
    except Exception as e:
        return False, "Could not parse command: " + repr(e), []

    if not parts:
        return False, "No command provided.", []

    prefix = parts[0]

    allowed = set(config.get("allowed_command_prefixes", []))

    if prefix not in allowed:
        return False, "Command prefix is not allowed: " + prefix, parts

    if mode == "safe":
        if prefix not in SAFE_READ_PREFIXES:
            return False, "Safe mode blocks non-read command: " + prefix, parts

    if mode == "power":
        if prefix not in SAFE_READ_PREFIXES and prefix not in WRITE_PREFIXES:
            return False, "Power mode blocks command: " + prefix, parts

    if mode == "agentic":
        # Agentic allows configured prefixes, but hard-blocks destructive fragments above.
        return True, "Allowed in agentic mode.", parts

    return True, "Allowed.", parts
PY

echo "[3/5] Patching agent_core/tools.py run_command..."

python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/tools.py")
text = path.read_text()

start = text.find("def run_command(command):")
if start == -1:
    raise SystemExit("Could not find run_command() in agent_core/tools.py")

end = text.find("\ndef dispatch_tool", start)
if end == -1:
    raise SystemExit("Could not find dispatch_tool after run_command()")

new_run_command = r'''def run_command(command):
    from agent_core.approvals import validate_command, permission_status

    command = str(command or "").strip()

    ok, reason, parts = validate_command(command)

    if not ok:
        return (
            "Command blocked: " + reason + "\n\n"
            + permission_status()
        )

    try:
        r = subprocess.run(
            parts,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=120
        )

        return compact(
            f"Command: {command}\n"
            f"Reason: {reason}\n"
            f"cwd: {WORKSPACE}\n"
            f"exit_code: {r.returncode}\n\n"
            f"stdout:\n{r.stdout}\n\n"
            f"stderr:\n{r.stderr}",
            12000
        )
    except Exception as e:
        return "Command failed safely: " + repr(e)

'''

text = text[:start] + new_run_command + text[end:]
path.write_text(text)
print("Patched run_command with approvals.")
PY

echo "[4/5] Patching titan_terminal.py commands..."

python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

if "def show_permission_mode(" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
def show_permission_mode():
    try:
        from agent_core.approvals import permission_status
        say_panel(permission_status(), title="Permissions", style="cyan")
    except Exception as e:
        say_panel("Permission status failed: " + repr(e), title="Permissions", style="red")


def set_permission_mode_terminal(mode):
    try:
        from agent_core.approvals import set_mode
        say_panel(set_mode(mode), title="Permissions", style="green")
    except Exception as e:
        say_panel("Permission mode failed: " + repr(e), title="Permissions", style="red")


def run_shell_terminal(command):
    try:
        from agent_core.tools import run_command
        result = run_command(command)
        say_panel(result, title="Run Command", style="magenta")
    except Exception as e:
        say_panel("Run command failed safely: " + repr(e), title="Run Command", style="red")


'''
    text = text.replace(marker, helpers + marker)

if 'lower == "/mode"' not in text:
    target = '''            if lower == "/memory":
                show_memory()
                continue
'''

    replacement = '''            if lower == "/memory":
                show_memory()
                continue

            if lower == "/mode":
                show_permission_mode()
                continue

            if lower == "/safe":
                set_permission_mode_terminal("safe")
                continue

            if lower == "/power":
                set_permission_mode_terminal("power")
                continue

            if lower == "/agentic":
                set_permission_mode_terminal("agentic")
                continue

            if lower.startswith("/run "):
                run_shell_terminal(command.replace("/run ", "", 1).strip())
                continue
'''

    if target not in text:
        target = '''            if lower == "/models":
                models()
                continue
'''
        replacement = target + '''
            if lower == "/mode":
                show_permission_mode()
                continue

            if lower == "/safe":
                set_permission_mode_terminal("safe")
                continue

            if lower == "/power":
                set_permission_mode_terminal("power")
                continue

            if lower == "/agentic":
                set_permission_mode_terminal("agentic")
                continue

            if lower.startswith("/run "):
                run_shell_terminal(command.replace("/run ", "", 1).strip())
                continue
'''

    if target not in text:
        raise SystemExit("Could not find insertion point.")

    text = text.replace(target, replacement, 1)

text = text.replace(
    "/web <query> Search the web\n",
    "/web <query> Search the web\n/mode       Show permission mode\n/safe       Read/check mode\n/power      Workspace build mode\n/agentic    Autonomous build mode\n/run <cmd>  Run approved shell command\n"
)

path.write_text(text)
print("Patched terminal permission commands.")
PY

echo "[5/5] Verifying..."

python3 -m py_compile agent_core/approvals.py agent_core/tools.py titan_terminal.py

cat > docs/PHASE8_APPROVALS_AND_SHELL.md <<EOF
# Phase 8 Approvals and Shell

Timestamp: $STAMP

Added:
- agent_core/approvals.py
- /mode
- /safe
- /power
- /agentic
- /run <command>

Behavior:
- Commands run inside workspace.
- Dangerous fragments are blocked.
- Safe mode allows read/check commands.
- Power mode allows normal build commands.
- Agentic mode allows configured command prefixes but still blocks destructive commands.

Next:
- dashboard settings page for mode switching
- approval queue for destructive actions
- stronger autonomous taskboard
EOF

echo "Phase 8 complete."
