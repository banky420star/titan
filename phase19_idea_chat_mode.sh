#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p agent_core backups docs memory/chat_history

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase19_$STAMP"

cp titan_terminal.py "backups/phase19_$STAMP/titan_terminal.py" 2>/dev/null || true
cp config.json "backups/phase19_$STAMP/config.json" 2>/dev/null || true

cat > agent_core/idea_chat.py <<'PY'
import json
from pathlib import Path

from agent_core.models import safe_chat

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG = BASE / "config.json"


def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


IDEA_SYSTEM = """You are Titan's idea-chat brain.

You are not just a command executor. You are a sharp project partner.

Behavior:
- Talk naturally about ideas, projects, product strategy, architecture, UI, business models, automation, and code direction.
- Be useful, creative, direct, and practical.
- Upgrade weak ideas with stronger options the user may not have considered.
- Ask at most one question only when absolutely needed.
- Prefer giving concrete next moves.
- Keep answers short unless the user asks for depth.
- If the user is building something, think like a product designer, senior developer, systems architect, and startup operator.
- Do not force JSON.
- Do not claim tools were used unless tool output was actually provided.
- Do not expose hidden reasoning.
"""


def get_context(task):
    chunks = []

    try:
        from agent_core.chat_history import current_section, history_search
        chunks.append("Current project section: " + current_section())

        hist = history_search(str(task), limit=6)
        if hist.get("items"):
            lines = []
            for item in hist["items"]:
                lines.append(f"{item.get('time')} | {item.get('section')} | {item.get('role')}: {item.get('content')[:600]}")
            chunks.append("Relevant chat history:\n" + "\n".join(lines))
    except Exception:
        pass

    try:
        from agent_core.memory import memory_search
        mem = memory_search(str(task), scope="all", limit=5)
        if mem and "No matching memories found" not in mem:
            chunks.append("Relevant memory:\n" + mem[:2400])
    except Exception:
        pass

    try:
        from agent_core.rag import rag_search
        rag = rag_search(str(task), top_k=3)
        if rag and "RAG index not found" not in rag and "RAG index is empty" not in rag:
            chunks.append("Relevant local docs:\n" + rag[:2400])
    except Exception:
        pass

    return "\n\n".join(chunks)


def idea_chat(task, mode="idea"):
    cfg = load_config()

    model = cfg.get("idea_model") or cfg.get("model") or "qwen3:8b"

    mode = str(mode or "idea").strip().lower()

    style = {
        "idea": "Focus on improving and expanding the idea.",
        "brainstorm": "Generate multiple strong directions. Be inventive but practical.",
        "critic": "Find flaws, risks, missing pieces, and stronger alternatives.",
        "builder": "Turn the idea into a build plan with next actions.",
        "simple": "Explain simply and clearly.",
    }.get(mode, "Focus on improving and expanding the idea.")

    context = get_context(task)

    user = f"Mode: {mode}\nInstruction: {style}\n\nUser idea/task:\n{task}"

    if context:
        user = "Context Titan found:\n" + context + "\n\n" + user

    return safe_chat(
        [
            {"role": "system", "content": IDEA_SYSTEM},
            {"role": "user", "content": user},
        ],
        model=model,
        timeout=int(cfg.get("idea_timeout", 180)),
    )
PY

python3 - <<'PY'
import json
from pathlib import Path

path = Path("config.json")
cfg = json.loads(path.read_text()) if path.exists() else {}

cfg["idea_model"] = cfg.get("idea_model", cfg.get("model", "qwen3:8b"))
cfg["idea_timeout"] = 180
cfg["plain_text_mode"] = "idea_chat"

path.write_text(json.dumps(cfg, indent=2))
print("config patched")
PY

python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_idea_chat_mode.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

helpers = r'''
def terminal_idea_chat(args, mode="idea"):
    try:
        from agent_core.idea_chat import idea_chat
        from agent_core.chat_history import log_event

        task = str(args or "").strip()
        if not task:
            say_panel("Usage: /idea <your idea>", title="Idea Chat", style="yellow")
            return

        user_id = None
        try:
            user_id = log_event("user", task, meta={"source": "terminal", "mode": mode})
        except Exception:
            pass

        result = idea_chat(task, mode=mode)

        try:
            log_event("assistant", result, meta={"source": "terminal", "mode": mode, "reply_to": user_id})
        except Exception:
            pass

        say_panel(result, title=f"Titan {mode.title()}", style="cyan")
    except Exception as e:
        say_panel("Idea chat failed: " + repr(e), title="Idea Chat", style="red")


def terminal_set_idea_model(model):
    try:
        import json
        from pathlib import Path

        cfg_path = Path("config.json")
        cfg = json.loads(cfg_path.read_text())
        cfg["idea_model"] = str(model or "").strip() or cfg.get("model", "qwen3:8b")
        cfg_path.write_text(json.dumps(cfg, indent=2))

        say_panel("Idea model set to: " + cfg["idea_model"], title="Idea Model", style="green")
    except Exception as e:
        say_panel("Idea model failed: " + repr(e), title="Idea Model", style="red")


'''

if "def terminal_idea_chat(" not in text:
    text = text.replace("def repl():", helpers + "\n\ndef repl():", 1)

if 'lower.startswith("/idea ")' not in text:
    target = '''            if lower == "/help":
                show_help()
                continue
'''
    insert = target + '''
            if lower.startswith("/idea "):
                terminal_idea_chat(command.replace("/idea ", "", 1).strip(), mode="idea")
                continue

            if lower.startswith("/brainstorm "):
                terminal_idea_chat(command.replace("/brainstorm ", "", 1).strip(), mode="brainstorm")
                continue

            if lower.startswith("/critic "):
                terminal_idea_chat(command.replace("/critic ", "", 1).strip(), mode="critic")
                continue

            if lower.startswith("/builder "):
                terminal_idea_chat(command.replace("/builder ", "", 1).strip(), mode="builder")
                continue

            if lower.startswith("/simple "):
                terminal_idea_chat(command.replace("/simple ", "", 1).strip(), mode="simple")
                continue

            if lower.startswith("/idea-model "):
                terminal_set_idea_model(command.replace("/idea-model ", "", 1).strip())
                continue
'''
    if target not in text:
        raise SystemExit("Could not find /help handler.")
    text = text.replace(target, insert, 1)

help_add = '''/idea <text> Chat about an idea
/brainstorm <text> Generate stronger options
/critic <text> Find risks and weak spots
/builder <text> Turn idea into build plan
/simple <text> Explain simply
/idea-model <model> Set model used for idea chat
'''

if "/idea <text>" not in text:
    text = text.replace("/help        Show commands\n", "/help        Show commands\n" + help_add, 1)

path.write_text(text, encoding="utf-8")
print("terminal patched")
PY

python3 -m py_compile agent_core/idea_chat.py titan_terminal.py

cat > docs/PHASE19_IDEA_CHAT_MODE.md <<EOF
# Phase 19 Idea Chat Mode

Added:
- agent_core/idea_chat.py
- /idea
- /brainstorm
- /critic
- /builder
- /simple
- /idea-model

Purpose:
Titan can now discuss ideas naturally instead of only executing JSON tool commands.
EOF

echo "Phase 19 complete."
