from pathlib import Path
import json
import re
import subprocess
import sys

from agent_core.models import safe_chat

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
SKILLS = BASE / "skills"
CONFIG = BASE / "config.json"

SKILLS.mkdir(parents=True, exist_ok=True)


def slug(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    return value.strip("-") or "skill"


def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def skill_path(name):
    return SKILLS / slug(name)


def create_skill_pack(name, description="", dependencies=None):
    name = slug(name)
    dependencies = dependencies or []
    root = skill_path(name)

    root.mkdir(parents=True, exist_ok=True)
    (root / "scripts").mkdir(exist_ok=True)
    (root / "templates").mkdir(exist_ok=True)

    skill_md = f"""# {name}

{description or "Titan local skill."}

## When to use

Use this skill when the task matches this workflow.

## Workflow

1. Inspect relevant files and context.
2. Plan the smallest useful change.
3. Make safe workspace edits only when needed.
4. Run verification.
5. Report exact changes and next actions.

## Dependencies

{chr(10).join("- " + str(x) for x in dependencies) if dependencies else "- none"}

## Notes

Keep outputs concise. Do not pretend tools were used unless tool output was provided.
"""

    meta = {
        "name": name,
        "description": description or "Titan local skill.",
        "dependencies": dependencies,
        "entry": "SKILL.md"
    }

    (root / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (root / "skill.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return f"Created skill pack: {root}"


def list_skills():
    rows = []

    for root in sorted(SKILLS.iterdir()):
        if not root.is_dir():
            continue

        meta_path = root / "skill.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                rows.append(f"- {meta.get('name', root.name)}: {meta.get('description', '')}")
                continue
            except Exception:
                pass

        rows.append(f"- {root.name}")

    return "\n".join(rows) if rows else "No skills found."


def read_skill(name):
    root = skill_path(name)
    md = root / "SKILL.md"

    if not md.exists():
        return None, f"Skill not found: {name}"

    return md.read_text(encoding="utf-8", errors="ignore"), None


def run_skill(name, task, context=""):
    skill_text, error = read_skill(name)

    if error:
        return error

    cfg = load_config()
    model = cfg.get("model", "qwen3:8b")

    system = (
        "You are Titan running a local skill.\n"
        "Follow the SKILL.md instructions.\n"
        "Return concise actionable output.\n"
        "Do not claim tool use unless tool output is provided.\n\n"
        "SKILL.md:\n"
        + skill_text
    )

    user = "Task:\n" + str(task)

    if context:
        user += "\n\nContext:\n" + str(context)

    return safe_chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        model=model,
        timeout=int(cfg.get("skill_timeout", 180))
    )


def install_dependency(package):
    package = str(package or "").strip()

    if not package:
        return "No package provided."

    if not re.match(r"^[A-Za-z0-9_.\\-\\[\\],=<>~!]+$", package):
        return "Blocked unsafe package name."

    cmd = [sys.executable, "-m", "pip", "install", "-U", package]

    try:
        r = subprocess.run(
            cmd,
            cwd=str(BASE),
            capture_output=True,
            text=True,
            timeout=240
        )

        return (
            f"exit_code: {r.returncode}\n"
            f"stdout:\n{r.stdout[-6000:]}\n"
            f"stderr:\n{r.stderr[-6000:]}"
        )
    except Exception as e:
        return "Dependency install failed safely: " + repr(e)
