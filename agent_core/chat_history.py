from pathlib import Path
from datetime import datetime
import json
import re
import uuid

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
HISTORY_DIR = BASE / "memory" / "chat_history"
SECTION_FILE = BASE / "memory" / "current_section.txt"

HISTORY_DIR.mkdir(parents=True, exist_ok=True)
SECTION_FILE.parent.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now().isoformat(timespec="seconds")


def today_path():
    return HISTORY_DIR / (datetime.now().strftime("%Y-%m-%d") + ".jsonl")


def slug_section(value):
    value = str(value or "").strip()
    if not value:
        value = "General"
    return value[:80]


def current_section():
    if SECTION_FILE.exists():
        value = SECTION_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value
    return "General"


def set_section(name):
    name = slug_section(name)
    SECTION_FILE.write_text(name, encoding="utf-8")
    log_event("system", "Section changed to: " + name, section=name, meta={"event": "section_change"})
    return "Current section: " + name


def log_event(role, content, section=None, meta=None):
    item = {
        "id": "chat-" + uuid.uuid4().hex[:10],
        "time": now(),
        "section": section or current_section(),
        "role": str(role or "system"),
        "content": str(content or ""),
        "meta": meta or {}
    }

    with today_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return item["id"]


def iter_events():
    for path in sorted(HISTORY_DIR.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def list_sections():
    sections = {}

    for item in iter_events():
        sec = item.get("section", "General")
        sections.setdefault(sec, 0)
        sections[sec] += 1

    if current_section() not in sections:
        sections[current_section()] = 0

    return [
        {"section": name, "count": count, "active": name == current_section()}
        for name, count in sorted(sections.items(), key=lambda x: x[0].lower())
    ]


def history_list(section=None, limit=80):
    items = list(iter_events())

    if section:
        items = [x for x in items if x.get("section") == section]

    items = items[-int(limit):]
    items.reverse()

    return {
        "current_section": current_section(),
        "count": len(items),
        "items": items
    }


def history_text(section=None, limit=60):
    data = history_list(section, limit)

    if not data["items"]:
        return "No chat history found."

    lines = [f"Current section: {data['current_section']}", ""]

    for item in data["items"]:
        lines.append(
            f"{item.get('time')} | {item.get('section')} | {item.get('role')}\n"
            f"{item.get('content')}\n"
        )

    return "\n".join(lines)


def history_search(query, limit=40):
    query = str(query or "").strip()

    if not query:
        return {"query": query, "count": 0, "items": []}

    q = query.lower()
    results = []

    for item in iter_events():
        hay = (
            str(item.get("section", "")) + " " +
            str(item.get("role", "")) + " " +
            str(item.get("content", ""))
        ).lower()

        if q in hay:
            results.append(item)

    results = results[-int(limit):]
    results.reverse()

    return {
        "query": query,
        "count": len(results),
        "items": results
    }


def history_search_text(query, limit=30):
    data = history_search(query, limit)

    if not data["items"]:
        return "No history matches."

    lines = [f"History matches for: {query}", ""]

    for item in data["items"]:
        lines.append(
            f"{item.get('time')} | {item.get('section')} | {item.get('role')}\n"
            f"{item.get('content')}\n"
        )

    return "\n".join(lines)
