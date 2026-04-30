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

    user = f"Mode: {mode}\nInstruction: {style}\n\nUser:\n{task}"

    return safe_chat(
        [
            {"role": "system", "content": IDEA_SYSTEM},
            {"role": "user", "content": user},
        ],
        model=model,
        timeout=int(cfg.get("idea_timeout", 180)),
    )
