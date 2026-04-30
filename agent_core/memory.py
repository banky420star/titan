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
