#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p agent_core memory/project memory/user memory/sessions docs backups logs

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase6_$STAMP"

cp titan_terminal.py "backups/phase6_$STAMP/titan_terminal.py" 2>/dev/null || true
cp agent_core/tools.py "backups/phase6_$STAMP/tools.py" 2>/dev/null || true
cp agent_core/agent.py "backups/phase6_$STAMP/agent.py" 2>/dev/null || true
cp config.json "backups/phase6_$STAMP/config.json" 2>/dev/null || true

echo "[1/5] Writing agent_core/memory.py..."

cat > agent_core/memory.py <<'PY'
from pathlib import Path
from datetime import datetime
import json
import re
import uuid

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
MEMORY = BASE / "memory"
PROJECT_MEMORY = MEMORY / "project" / "memories.jsonl"
USER_MEMORY = MEMORY / "user" / "memories.jsonl"

for path in [PROJECT_MEMORY, USER_MEMORY]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)


def now():
    return datetime.now().isoformat(timespec="seconds")


def tokenize(text):
    return set(re.findall(r"[a-zA-Z0-9_+-]+", str(text).lower()))


def read_store(scope="project"):
    path = USER_MEMORY if scope == "user" else PROJECT_MEMORY
    items = []

    if not path.exists():
        return items

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            items.append(json.loads(line))
        except Exception:
            continue

    return items


def write_store(items, scope="project"):
    path = USER_MEMORY if scope == "user" else PROJECT_MEMORY
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def memory_save(text, kind="project_fact", scope="project", tags=None):
    text = str(text or "").strip()

    if not text:
        return "No memory text provided."

    if scope not in ["project", "user"]:
        scope = "project"

    tags = tags or []

    item = {
        "id": "mem-" + uuid.uuid4().hex[:10],
        "scope": scope,
        "kind": kind or "project_fact",
        "text": text,
        "tags": tags,
        "created_at": now(),
        "updated_at": now()
    }

    path = USER_MEMORY if scope == "user" else PROJECT_MEMORY

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return f"Saved memory: {item['id']}"


def memory_list(scope="project", limit=40):
    if scope not in ["project", "user", "all"]:
        scope = "project"

    items = []

    if scope in ["project", "all"]:
        items.extend(read_store("project"))

    if scope in ["user", "all"]:
        items.extend(read_store("user"))

    items = sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)

    if not items:
        return "No memories found."

    lines = []

    for item in items[:int(limit)]:
        lines.append(
            f"{item.get('id')} | {item.get('scope')} | {item.get('kind')}\n"
            f"  {item.get('text')}"
        )

    return "\n\n".join(lines)


def memory_search(query, scope="all", limit=8):
    query = str(query or "").strip()

    if not query:
        return "No memory search query provided."

    qtokens = tokenize(query)

    items = []

    if scope in ["project", "all"]:
        items.extend(read_store("project"))

    if scope in ["user", "all"]:
        items.extend(read_store("user"))

    scored = []

    for item in items:
        text = item.get("text", "")
        tags = " ".join(item.get("tags", []))
        haystack = text + " " + tags + " " + item.get("kind", "")
        tokens = tokenize(haystack)

        overlap = len(qtokens & tokens)
        bonus = 0

        if query.lower() in haystack.lower():
            bonus += 4

        score = overlap + bonus

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: (x[0], x[1].get("updated_at", "")), reverse=True)

    if not scored:
        return "No matching memories found."

    lines = [f"Memory matches for: {query}", ""]

    for score, item in scored[:int(limit)]:
        lines.append(
            f"Score: {score}\n"
            f"ID: {item.get('id')}\n"
            f"Scope: {item.get('scope')}\n"
            f"Kind: {item.get('kind')}\n"
            f"Text: {item.get('text')}\n"
        )

    return "\n".join(lines)


def memory_delete(memory_id):
    memory_id = str(memory_id or "").strip()

    if not memory_id:
        return "No memory id provided."

    deleted = []

    for scope in ["project", "user"]:
        items = read_store(scope)
        kept = []

        for item in items:
            if item.get("id") == memory_id:
                deleted.append(item)
            else:
                kept.append(item)

        write_store(kept, scope)

    if not deleted:
        return "Memory not found: " + memory_id

    return "Deleted memory: " + memory_id


def seed_core_memories():
    existing = memory_list("all", 200)

    seeds = [
        "Titan dashboard runs on http://127.0.0.1:5050.",
        "The old UI on port 5000 should stay archived and should not be launched as Titan dashboard.",
        "Titan mascot style is three vertical bars: yellow left, taller orange center, coral right, with two large glossy dark eyes.",
        "Titan should use local Ollama models by default and avoid cloud models unless explicitly requested.",
        "Titan terminal prompt icon should remain the small glossy two-eye icon that the user liked.",
        "Titan project base path is /Volumes/AI_DRIVE/TitanAgent."
    ]

    created = 0

    for seed in seeds:
        if seed not in existing:
            memory_save(seed, kind="project_fact", scope="project", tags=["titan", "system"])
            created += 1

    return f"Seeded {created} core memories."
PY

echo "[2/5] Seeding core Titan memories..."

python3 - <<'PY'
from agent_core.memory import seed_core_memories
print(seed_core_memories())
PY

echo "[3/5] Patching agent_core/tools.py..."

python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/tools.py")
text = path.read_text()

if "from agent_core.memory import" not in text:
    # Insert after existing imports.
    anchor = "from agent_core.rag import rag_status, rag_index, rag_search\n"
    import_line = "from agent_core.memory import memory_save, memory_search, memory_list, memory_delete\n"

    if anchor in text:
        text = text.replace(anchor, anchor + import_line)
    else:
        text = import_line + text

unknown = '    return "Unknown tool: " + str(name)\n'

memory_dispatch = '''    if name == "memory_save":
        return memory_save(inp.get("text", ""), inp.get("kind", "project_fact"), inp.get("scope", "project"), inp.get("tags", []))
    if name == "memory_search":
        return memory_search(inp.get("query", ""), inp.get("scope", "all"), inp.get("limit", 8))
    if name == "memory_list":
        return memory_list(inp.get("scope", "all"), inp.get("limit", 40))
    if name == "memory_delete":
        return memory_delete(inp.get("id", ""))

'''

if memory_dispatch.strip() not in text:
    if unknown not in text:
        raise SystemExit("Could not find Unknown tool return in agent_core/tools.py")
    text = text.replace(unknown, memory_dispatch + unknown)

path.write_text(text)
print("Patched tools with memory dispatch.")
PY

echo "[4/5] Patching agent_core/agent.py..."

python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/agent.py")
text = path.read_text()

# Add memory tools to system prompt.
addition = """- memory_save {"text":"memory text","kind":"project_fact|preference|decision|bug_fix","scope":"project|user","tags":[]}
- memory_search {"query":"search terms","scope":"all|project|user","limit":8}
- memory_list {"scope":"all|project|user","limit":40}
- memory_delete {"id":"mem-id"}
"""

if "memory_save" not in text:
    marker = "Available tools:\n"
    if marker in text:
        text = text.replace(marker, marker + addition)
    else:
        text = addition + text

# Add light memory context into run_agent without making it huge.
if "TITAN_MEMORY_CONTEXT_PATCH" not in text:
    old = '''    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": str(task)}
    ]
'''
    new = '''    # TITAN_MEMORY_CONTEXT_PATCH
    memory_context = ""
    try:
        from agent_core.memory import memory_search
        memory_context = memory_search(str(task), scope="all", limit=5)
        if "No matching memories found" in memory_context:
            memory_context = ""
    except Exception:
        memory_context = ""

    user_content = str(task)
    if memory_context:
        user_content = "Relevant Titan memory:\\n" + memory_context + "\\n\\nTask:\\n" + str(task)

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_content}
    ]
'''
    if old in text:
        text = text.replace(old, new)
    else:
        print("Could not find exact messages block; memory tools added but auto-memory context not inserted.")

path.write_text(text)
print("Patched agent with memory tools and lightweight memory context.")
PY

echo "[5/5] Patching titan_terminal.py commands..."

python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

if "def show_memory(" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
def show_memory():
    try:
        from agent_core.memory import memory_list
        say_panel(memory_list("all", 50), title="Memory", style="cyan")
    except Exception as e:
        say_panel("Memory list failed: " + repr(e), title="Memory", style="red")


def remember_terminal(text):
    try:
        from agent_core.memory import memory_save
        result = memory_save(text, kind="project_fact", scope="project", tags=["manual"])
        say_panel(result, title="Memory", style="green")
    except Exception as e:
        say_panel("Remember failed: " + repr(e), title="Memory", style="red")


def recall_terminal(query):
    try:
        from agent_core.memory import memory_search
        result = memory_search(query, scope="all", limit=8)
        say_panel(result, title="Memory Search", style="magenta")
    except Exception as e:
        say_panel("Recall failed: " + repr(e), title="Memory", style="red")


def forget_terminal(memory_id):
    try:
        from agent_core.memory import memory_delete
        result = memory_delete(memory_id)
        say_panel(result, title="Memory", style="yellow")
    except Exception as e:
        say_panel("Forget failed: " + repr(e), title="Memory", style="red")


'''
    text = text.replace(marker, helpers + marker)

if 'lower == "/memory"' not in text:
    target = '''            if lower == "/rag":
                show_rag_status()
                continue
'''
    replacement = '''            if lower == "/rag":
                show_rag_status()
                continue

            if lower == "/memory":
                show_memory()
                continue

            if lower.startswith("/remember "):
                remember_terminal(command.replace("/remember ", "", 1).strip())
                continue

            if lower.startswith("/recall "):
                recall_terminal(command.replace("/recall ", "", 1).strip())
                continue

            if lower.startswith("/forget "):
                forget_terminal(command.replace("/forget ", "", 1).strip())
                continue
'''

    if target not in text:
        target = '''            if lower == "/skills":
                show_skills()
                continue
'''
        replacement = target + '''
            if lower == "/memory":
                show_memory()
                continue

            if lower.startswith("/remember "):
                remember_terminal(command.replace("/remember ", "", 1).strip())
                continue

            if lower.startswith("/recall "):
                recall_terminal(command.replace("/recall ", "", 1).strip())
                continue

            if lower.startswith("/forget "):
                forget_terminal(command.replace("/forget ", "", 1).strip())
                continue
'''
        if target not in text:
            raise SystemExit("Could not find insertion point for memory commands.")

    text = text.replace(target, replacement, 1)

text = text.replace(
    "/rag         Show RAG status\n",
    "/rag         Show RAG status\n/memory      Show saved Titan memories\n/remember <text>\n/recall <query>\n/forget <memory_id>\n"
)

path.write_text(text)
print("Patched terminal memory commands.")
PY

python3 -m py_compile agent_core/memory.py agent_core/tools.py agent_core/agent.py titan_terminal.py

cat > docs/PHASE6_MEMORY.md <<EOF
# Phase 6 Memory

Timestamp: $STAMP

Added:
- agent_core/memory.py
- /memory
- /remember <text>
- /recall <query>
- /forget <memory_id>

Agent tools:
- memory_save
- memory_search
- memory_list
- memory_delete

Stores:
- memory/project/memories.jsonl
- memory/user/memories.jsonl

Seeded core Titan memories:
- dashboard port 5050
- old UI archived
- official mascot style
- local Ollama default
- prompt icon preference
- project base path

Next:
- dashboard memory page
- approvals system
- taskboard/jobs upgrade
EOF

echo "Phase 6 complete."
