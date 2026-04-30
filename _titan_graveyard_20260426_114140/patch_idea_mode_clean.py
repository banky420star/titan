from pathlib import Path
import json
import re

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
BACKUPS = BASE / "backups"
BACKUPS.mkdir(exist_ok=True)

idea_path = BASE / "agent_core" / "idea_chat.py"
idea_path.parent.mkdir(exist_ok=True)

idea_path.write_text('''import json
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
"""


def idea_chat(task, mode="idea"):
    cfg = load_config()
    model = cfg.get("idea_model") or cfg.get("model") or "qwen3:8b"
    mode = str(mode or "idea").strip().lower()

    style = {
        "idea": "Improve and expand this idea.",
        "brainstorm": "Generate multiple strong directions.",
        "critic": "Find flaws, risks, missing pieces, and better alternatives.",
        "builder": "Turn this into a build plan with next actions.",
        "simple": "Explain simply and clearly.",
    }.get(mode, "Improve and expand this idea.")

    user = f"Mode: {mode}\\nInstruction: {style}\\n\\nUser:\\n{task}"

    return safe_chat(
        [
            {"role": "system", "content": IDEA_SYSTEM},
            {"role": "user", "content": user},
        ],
        model=model,
        timeout=int(cfg.get("idea_timeout", 180)),
    )
''', encoding="utf-8")

cfg_path = BASE / "config.json"
cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
cfg["idea_model"] = cfg.get("idea_model") or cfg.get("model") or "qwen3:8b"
cfg["idea_timeout"] = 180
cfg["plain_text_mode"] = "idea_chat"
cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

term = BASE / "titan_terminal.py"
text = term.read_text(encoding="utf-8")
(BACKUPS / "titan_terminal_before_clean_idea_patch.py").write_text(text, encoding="utf-8")

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


def terminal_idea_chat(args, mode="idea"):
    try:
        from agent_core.idea_chat import idea_chat

        task = str(args or "").strip()
        if not task:
            say_panel("Usage: /idea <your idea>", title="Idea Chat", style="yellow")
            return

        result = idea_chat(task, mode=mode)
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
    text = text.replace("def repl():", helpers + "\ndef repl():", 1)

intercept = r'''
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

if 'lower.startswith("/idea ")' not in text:
    repl_start = text.find("def repl():")
    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\b", after)
    if not match:
        raise SystemExit("Could not find command handler insertion point")
    pos = repl_start + match.start()
    text = text[:pos] + intercept + text[pos:]

term.write_text(text, encoding="utf-8")
print("clean idea patch applied")
