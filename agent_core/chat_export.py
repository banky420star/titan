from pathlib import Path
from datetime import datetime
import re

from agent_core.chat_history import history_list, list_sections, current_section

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
EXPORTS = BASE / "docs" / "project_logs"
EXPORTS.mkdir(parents=True, exist_ok=True)


def slug(value):
    value = str(value or "").strip() or "all-history"
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value)
    return value.strip("-") or "history"


def export_history(section=None, limit=10000):
    section = str(section or "").strip() or None
    data = history_list(section=section, limit=limit)
    items = list(reversed(data.get("items", [])))

    label = section or "all-history"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORTS / f"{slug(label)}_{stamp}.md"

    lines = [
        f"# Titan Chat History: {label}",
        "",
        f"Exported: {datetime.now().isoformat(timespec='seconds')}",
        f"Current section: {data.get('current_section', current_section())}",
        f"Entries: {len(items)}",
        "",
        "---",
        ""
    ]

    for item in items:
        role = item.get("role", "unknown")
        sec = item.get("section", "General")
        time = item.get("time", "")
        content = str(item.get("content", ""))

        lines.append(f"## {time} · {sec} · {role}")
        lines.append("")
        lines.append(content)
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "result": "exported",
        "section": label,
        "entries": len(items),
        "path": str(path)
    }


def export_all_sections():
    outputs = []
    sections = list_sections()

    for item in sections:
        name = item.get("section")
        outputs.append(export_history(name))

    return {
        "result": "exported sections",
        "count": len(outputs),
        "exports": outputs
    }
