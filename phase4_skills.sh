#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p agent_core skills docs backups logs

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase4_$STAMP"

cp titan_terminal.py "backups/phase4_$STAMP/titan_terminal.py" 2>/dev/null || true
cp agent_core/tools.py "backups/phase4_$STAMP/tools.py" 2>/dev/null || true
cp agent_core/agent.py "backups/phase4_$STAMP/agent.py" 2>/dev/null || true
cp config.json "backups/phase4_$STAMP/config.json" 2>/dev/null || true

echo "[1/5] Writing agent_core/skills.py..."

cat > agent_core/skills.py <<'PY'
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
PY

echo "[2/5] Creating starter skills..."

python3 - <<'PY'
from agent_core.skills import create_skill_pack

create_skill_pack(
    "product-builder",
    "Scaffold and improve local products, CLI tools, Flask apps, and static sites.",
    []
)

create_skill_pack(
    "dashboard-polisher",
    "Improve Titan dashboard UI, chat layout, mascot behavior, and micro-interactions.",
    []
)

create_skill_pack(
    "bug-fixer",
    "Find, patch, and verify bugs in Titan's local Python files.",
    []
)

create_skill_pack(
    "terminal-polisher",
    "Improve Titan terminal UX, slash commands, prompt behavior, and startup mascot.",
    []
)
PY

echo "[3/5] Patching agent_core/tools.py..."

python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/tools.py")
text = path.read_text()

if "from agent_core.skills import" not in text:
    insert_after = "import sys\n"
    import_line = "from agent_core.skills import create_skill_pack, list_skills, run_skill, install_dependency\n"
    if insert_after in text:
        text = text.replace(insert_after, insert_after + import_line)
    else:
        text = import_line + text

unknown = '    return "Unknown tool: " + str(name)\n'

skill_dispatch = '''    if name == "list_skills":
        return list_skills()
    if name == "create_skill_pack":
        return create_skill_pack(inp.get("name", ""), inp.get("description", ""), inp.get("dependencies", []))
    if name == "run_skill":
        return run_skill(inp.get("name", ""), inp.get("task", ""), inp.get("context", ""))
    if name == "install_dependency":
        return install_dependency(inp.get("package", ""))

'''

if skill_dispatch.strip() not in text:
    if unknown not in text:
        raise SystemExit("Could not find Unknown tool return in agent_core/tools.py")
    text = text.replace(unknown, skill_dispatch + unknown)

path.write_text(text)
print("Patched agent_core/tools.py with skill tools.")
PY

echo "[4/5] Patching agent_core/agent.py tool list..."

python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/agent.py")
text = path.read_text()

needle = "- list_products {}\n"

addition = """- list_skills {}
- create_skill_pack {"name":"skill-name","description":"text","dependencies":[]}
- run_skill {"name":"skill-name","task":"task","context":"optional context"}
- install_dependency {"package":"package-name"}
"""

if "create_skill_pack" not in text:
    if needle in text:
        text = text.replace(needle, needle + addition)
    else:
        text = text.replace("Available tools:\n", "Available tools:\n" + addition)

path.write_text(text)
print("Patched agent_core/agent.py skill tool list.")
PY

echo "[5/5] Patching titan_terminal.py commands..."

python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

if "def show_skills(" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
def show_skills():
    try:
        from agent_core.skills import list_skills
        say_panel(list_skills(), title="Skills", style="cyan")
    except Exception as e:
        say_panel("Could not list skills: " + repr(e), title="Skills", style="red")


def create_skill_terminal(args):
    try:
        from agent_core.skills import create_skill_pack

        parts = str(args or "").strip().split(" ", 1)
        if not parts or not parts[0]:
            say_panel("Usage: /skill-create <name> <description>", title="Skills", style="yellow")
            return

        name = parts[0]
        description = parts[1] if len(parts) > 1 else "Titan local skill."

        say_panel(create_skill_pack(name, description, []), title="Skills", style="green")
    except Exception as e:
        say_panel("Could not create skill: " + repr(e), title="Skills", style="red")


def run_skill_terminal(args):
    try:
        from agent_core.skills import run_skill

        parts = str(args or "").strip().split(" ", 1)
        if len(parts) < 2:
            say_panel("Usage: /skill <name> <task>", title="Skills", style="yellow")
            return

        name, task = parts[0], parts[1]
        result = run_skill(name, task)
        say_panel(result, title=f"Skill: {name}", style="magenta")
    except Exception as e:
        say_panel("Skill failed safely: " + repr(e), title="Skills", style="red")


def install_dependency_terminal(package):
    try:
        from agent_core.skills import install_dependency
        result = install_dependency(package)
        say_panel(result, title="Install Dependency", style="green")
    except Exception as e:
        say_panel("Dependency install failed safely: " + repr(e), title="Install Dependency", style="red")


'''
    text = text.replace(marker, helpers + marker)

if 'lower == "/skills"' not in text:
    target = '''            if lower == "/agents":
                show_agents()
                continue
'''
    replacement = '''            if lower == "/agents":
                show_agents()
                continue

            if lower == "/skills":
                show_skills()
                continue

            if lower.startswith("/skill-create "):
                create_skill_terminal(command.replace("/skill-create ", "", 1).strip())
                continue

            if lower.startswith("/skill "):
                run_skill_terminal(command.replace("/skill ", "", 1).strip())
                continue

            if lower.startswith("/pip "):
                install_dependency_terminal(command.replace("/pip ", "", 1).strip())
                continue
'''

    if target in text:
        text = text.replace(target, replacement, 1)
    else:
        target = '''            if lower == "/models":
                models()
                continue
'''
        replacement = target + '''
            if lower == "/skills":
                show_skills()
                continue

            if lower.startswith("/skill-create "):
                create_skill_terminal(command.replace("/skill-create ", "", 1).strip())
                continue

            if lower.startswith("/skill "):
                run_skill_terminal(command.replace("/skill ", "", 1).strip())
                continue

            if lower.startswith("/pip "):
                install_dependency_terminal(command.replace("/pip ", "", 1).strip())
                continue
'''
        if target not in text:
            raise SystemExit("Could not find insertion point for skills commands.")
        text = text.replace(target, replacement, 1)

text = text.replace(
    "/agents      Show Titan subagents\n",
    "/agents      Show Titan subagents\n/skills      Show Titan skills\n/skill-create <name> <description>\n/skill <name> <task>\n/pip <package> Install Python package safely\n"
)

path.write_text(text)
print("Patched titan_terminal.py with skills commands.")
PY

python3 -m py_compile agent_core/skills.py agent_core/tools.py agent_core/agent.py titan_terminal.py

cat > docs/PHASE4_SKILLS.md <<EOF
# Phase 4 Skills

Timestamp: $STAMP

Added:
- agent_core/skills.py
- /skills
- /skill-create <name> <description>
- /skill <name> <task>
- /pip <package>

Agent tools:
- list_skills
- create_skill_pack
- run_skill
- install_dependency

Starter skills:
- product-builder
- dashboard-polisher
- bug-fixer
- terminal-polisher

Next:
- dashboard skills page
- RAG ingestion/search
- stronger product builder
EOF

echo "Phase 4 complete."
