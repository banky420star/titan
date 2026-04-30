from pathlib import Path
import json
import re

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
BACKUPS = BASE / "backups"
BACKUPS.mkdir(exist_ok=True)

# -----------------------------
# 1. Ensure idea_chat.py exists
# -----------------------------
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
                content = str(item.get("content", ""))[:600]
                lines.append(f"{item.get('time')} | {item.get('section')} | {item.get('role')}: {content}")
            chunks.append("Relevant chat history:\\n" + "\\n".join(lines))
    except Exception:
        pass

    try:
        from agent_core.memory import memory_search
        mem = memory_search(str(task), scope="all", limit=5)
        if mem and "No matching memories found" not in mem:
            chunks.append("Relevant memory:\\n" + mem[:2400])
    except Exception:
        pass

    return "\\n\\n".join(chunks)


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

    user = f"Mode: {mode}\\nInstruction: {style}\\n\\nUser idea/task:\\n{task}"

    if context:
        user = "Context Titan found:\\n" + context + "\\n\\n" + user

    return safe_chat(
        [
            {"role": "system", "content": IDEA_SYSTEM},
            {"role": "user", "content": user},
        ],
        model=model,
        timeout=int(cfg.get("idea_timeout", 180)),
    )
''', encoding="utf-8")

# -----------------------------
# 2. Patch config
# -----------------------------
cfg_path = BASE / "config.json"
cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
cfg["idea_model"] = cfg.get("idea_model") or cfg.get("model") or "qwen3:8b"
cfg["idea_timeout"] = 180
cfg["plain_text_mode"] = "idea_chat"
cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

# -----------------------------
# 3. Patch titan_terminal.py
# -----------------------------
term = BASE / "titan_terminal.py"
text = term.read_text(encoding="utf-8")
(BACKUPS / "titan_terminal_before_phase19_fix.py").write_text(text, encoding="utf-8")

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

        user_id = None
        try:
            from agent_core.chat_history import log_event
            user_id = log_event("user", task, meta={"source": "terminal", "mode": mode})
        except Exception:
            pass

        result = idea_chat(task, mode=mode)

        try:
            from agent_core.chat_history import log_event
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
    if "def repl():" not in text:
        raise SystemExit("Could not find def repl()")
    text = text.replace("def repl():", helpers + "\n\ndef repl():", 1)
else:
    if "def set_permission_mode_terminal(" not in text:
        text = text.replace("def repl():", helpers + "\n\ndef repl():", 1)

intercept = r'''
            # TITAN_IDEA_PERMISSION_INTERCEPT_V1
            _titan_cmd = str(command or "").strip()
            _titan_low = _titan_cmd.lower()

            if _titan_low == "/mode":
                show_permission_mode()
                continue

            if _titan_low == "/safe":
                set_permission_mode_terminal("safe")
                continue

            if _titan_low == "/power":
                set_permission_mode_terminal("power")
                continue

            if _titan_low == "/agentic":
                set_permission_mode_terminal("agentic")
                continue

            if _titan_low.startswith("/idea "):
                terminal_idea_chat(_titan_cmd.replace("/idea ", "", 1).strip(), mode="idea")
                continue

            if _titan_low.startswith("/brainstorm "):
                terminal_idea_chat(_titan_cmd.replace("/brainstorm ", "", 1).strip(), mode="brainstorm")
                continue

            if _titan_low.startswith("/critic "):
                terminal_idea_chat(_titan_cmd.replace("/critic ", "", 1).strip(), mode="critic")
                continue

            if _titan_low.startswith("/builder "):
                terminal_idea_chat(_titan_cmd.replace("/builder ", "", 1).strip(), mode="builder")
                continue

            if _titan_low.startswith("/simple "):
                terminal_idea_chat(_titan_cmd.replace("/simple ", "", 1).strip(), mode="simple")
                continue

            if _titan_low.startswith("/idea-model "):
                terminal_set_idea_model(_titan_cmd.replace("/idea-model ", "", 1).strip())
                continue

'''

if "TITAN_IDEA_PERMISSION_INTERCEPT_V1" not in text:
    repl_start = text.find("def repl():")
    if repl_start == -1:
        raise SystemExit("Could not find repl")

    after_repl = text[repl_start:]
    match = re.search(r"\n\s*lower\s*=\s*.*\n", after_repl)

    if match:
        insert_pos = repl_start + match.end()
        text = text[:insert_pos] + intercept + text[insert_pos:]
    else:
        match = re.search(r"\n\s*if\s+lower\b", after_repl)
        if not match:
            raise SystemExit("Could not find lower assignment or first lower handler in repl")
        insert_pos = repl_start + match.start()
        text = text[:insert_pos] + intercept + text[insert_pos:]

help_lines = """/idea <text> Chat about an idea
/brainstorm <text> Generate stronger options
/critic <text> Find risks and weak spots
/builder <text> Turn idea into build plan
/simple <text> Explain simply
/idea-model <model> Set model used for idea chat
/mode Show permission mode
/safe Read/check mode
/power Workspace build mode
/agentic Autonomous build mode
"""

if "/idea <text>" not in text:
    text = text.replace("/help", "/help\\n" + help_lines, 1)

term.write_text(text, encoding="utf-8")
print("patched titan_terminal.py")
