#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/AI_DRIVE/TitanAgent
mkdir -p backups
STAMP="$(date +%Y%m%d_%H%M%S)"

cp config.json "backups/config_before_speed_$STAMP.json" 2>/dev/null || true
cp titan_terminal.py "backups/titan_terminal_before_speed_$STAMP.py" 2>/dev/null || true
cp agent_core/models.py "backups/models_before_speed_$STAMP.py" 2>/dev/null || true
cp agent_core/agent.py "backups/agent_before_speed_$STAMP.py" 2>/dev/null || true

echo "[1/4] Updating config for fast mode..."
python3 - <<'PY'
import json
from pathlib import Path

path = Path("config.json")
config = json.loads(path.read_text())

# Faster default. qwen3:8b can be smarter, but it often thinks longer.
config["model"] = config.get("fast_model", "qwen2.5-coder:7b")
config["fallback_model"] = config.get("fallback_model", "qwen3:8b")

config["fast_model"] = "qwen2.5-coder:7b"
config["smart_model"] = "qwen3:8b"

config["num_ctx"] = 4096
config["num_predict"] = 450
config["model_timeout"] = 90
config["fallback_timeout"] = 90
config["max_agent_steps"] = 5

path.write_text(json.dumps(config, indent=2))
print("Fast config applied.")
PY

echo "[2/4] Patching Ollama options for shorter responses..."
python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/models.py")
text = path.read_text()

old = '''        "options": {
            "temperature": 0.1,
            "num_ctx": int(cfg.get("num_ctx", 8192))
        }
'''

new = '''        "options": {
            "temperature": 0.0,
            "num_ctx": int(cfg.get("num_ctx", 4096)),
            "num_predict": int(cfg.get("num_predict", 450)),
            "top_p": 0.9
        },
        "keep_alive": "10m"
'''

if old in text:
    text = text.replace(old, new)
else:
    print("Options block not found exactly; no options patch applied.")

path.write_text(text)
print("Model options patched.")
PY

echo "[3/4] Making the agent stricter and shorter..."
python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/agent.py")
text = path.read_text()

text = text.replace(
    "You MUST respond with JSON.",
    "You MUST respond with JSON only. No prose. No markdown. No explanations outside JSON."
)

text = text.replace(
    "Return exactly one JSON object at a time.",
    "Return exactly one JSON object at a time whenever possible. Use the fewest tool calls possible."
)

text = text.replace(
    "Keep output concise.",
    "Keep output extremely concise."
)

text = text.replace(
    "def run_agent(task, max_steps=8):",
    "def run_agent(task, max_steps=5):"
)

path.write_text(text)
print("Agent prompt patched.")
PY

echo "[4/4] Adding fast local shortcuts before Ollama..."
python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

start = text.find("def run_titan_prompt(command):")
if start == -1:
    raise SystemExit("Could not find run_titan_prompt()")

end = text.find("\ndef repl():", start)
if end == -1:
    raise SystemExit("Could not find repl() after run_titan_prompt()")

new_func = r'''def run_titan_prompt(command):
    cmd = str(command or "").strip()
    low = cmd.lower()

    try:
        # Fast shortcuts: no Ollama call.
        if low in ["show me the workspace tree.", "show me the workspace tree", "workspace tree", "tree"]:
            from agent_core.tools import workspace_tree
            return workspace_tree()

        if low in ["list files", "show files", "list workspace files"]:
            from agent_core.tools import list_files
            return list_files()

        if low in ["list products", "show products", "products"]:
            from agent_core.tools import list_products
            return list_products()

        if low.startswith("read "):
            from agent_core.tools import read_file
            return read_file(cmd[5:].strip())

        if low.startswith("create product "):
            from agent_core.tools import create_product
            name = cmd.replace("create product ", "", 1).strip()
            return create_product(name, "python_cli", "Created from fast terminal shortcut.")

        from agent_core.agent import run_agent
        cfg = load_config()
        return run_agent(cmd, max_steps=int(cfg.get("max_agent_steps", 5)))

    except Exception as e:
        return "Titan brain failed safely: " + repr(e)


'''
text = text[:start] + new_func + text[end:]
path.write_text(text)
print("Fast terminal shortcuts patched.")
PY

python3 -m py_compile titan_terminal.py agent_core/models.py agent_core/agent.py

echo ""
echo "Speed patch done."
echo "Relaunch with:"
echo "python3 titan_terminal.py"
