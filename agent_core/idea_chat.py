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
        "idea": "Sharpen this idea. Give it teeth. What's the strongest version of this?",
        "brainstorm": "Fire off rapid, diverse directions. No filters, no hedging — just raw possibilities. Give at least 5 angles the user hasn't considered.",
        "critic": "Tear this apart constructively. Find the fatal flaw, the blind spot, the thing nobody wants to admit. Then suggest the fix.",
        "builder": "Turn this into a concrete build plan. Steps, files, dependencies, order of operations. No hand-holding — just the moves.",
        "simple": "Explain this in plain language. No jargon, no fluff. If a 10-year-old wouldn't get it, rewrite it.",
    }.get(mode, "Sharpen this idea. Give it teeth. What's the strongest version of this?")

    user = f"Mode: {mode}\nInstruction: {style}\n\nUser:\n{task}"

    return safe_chat(
        [
            {"role": "system", "content": IDEA_SYSTEM},
            {"role": "user", "content": user},
        ],
        model=model,
        timeout=int(cfg.get("idea_timeout", 180)),
    )
