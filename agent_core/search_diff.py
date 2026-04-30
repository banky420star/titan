from pathlib import Path
from datetime import datetime
import difflib
import json
import re

from agent_core.file_browser import ROOTS, TEXT_SUFFIXES, safe_path, root_path

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
SNAPSHOTS = BASE / "memory" / "file_snapshots"
SNAPSHOTS.mkdir(parents=True, exist_ok=True)

MAX_TEXT_SIZE = 1_500_000


def is_text_file(path):
    return path.is_file() and (path.suffix.lower() in TEXT_SUFFIXES or path.suffix == "")


def read_text_safe(path):
    try:
        if path.stat().st_size > MAX_TEXT_SIZE:
            return None
        if not is_text_file(path):
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def compact(text, limit=900):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[:limit] + "\n[TRUNCATED]"


def search_files(query, root="all", max_results=80):
    query = str(query or "").strip()
    root = str(root or "all").strip()

    if not query:
        return {"error": "No search query provided."}

    q = query.lower()

    roots = ROOTS.keys() if root == "all" else [root]
    results = []

    for root_name in roots:
        try:
            root_dir = root_path(root_name)
        except Exception:
            continue

        for path in sorted(root_dir.rglob("*")):
            if len(results) >= int(max_results):
                break

            if path.is_dir():
                continue

            try:
                rel = str(path.relative_to(root_dir))
                name_hit = q in path.name.lower() or q in rel.lower()

                content_hit = False
                snippet = ""

                text = read_text_safe(path)
                if text is not None and q in text.lower():
                    content_hit = True
                    idx = text.lower().find(q)
                    start = max(0, idx - 180)
                    end = min(len(text), idx + 420)
                    snippet = text[start:end].strip()

                if name_hit or content_hit:
                    results.append({
                        "root": root_name,
                        "path": rel,
                        "name": path.name,
                        "match": "name/path" if name_hit and not content_hit else "content" if content_hit and not name_hit else "name/path+content",
                        "size": path.stat().st_size,
                        "snippet": compact(snippet, 700)
                    })

            except Exception:
                continue

    return {
        "query": query,
        "root": root,
        "count": len(results),
        "results": results
    }


def search_files_text(query, root="all"):
    data = search_files(query, root=root)

    if data.get("error"):
        return data["error"]

    if not data["results"]:
        return "No matching files found."

    lines = [f"Search: {data['query']} | Root: {data['root']} | Results: {data['count']}", ""]

    for item in data["results"]:
        lines.append(
            f"{item['root']}:/{item['path']}\n"
            f"  match: {item['match']} | size: {item['size']}"
        )
        if item.get("snippet"):
            lines.append("  snippet: " + item["snippet"].replace("\n", "\n           "))
        lines.append("")

    return "\n".join(lines)


def snapshot_path(root="workspace"):
    root = str(root or "workspace").strip()
    return SNAPSHOTS / f"{root}.json"


def make_snapshot(root="workspace"):
    root = str(root or "workspace").strip()

    if root not in ROOTS:
        return {"error": "Unknown root: " + root}

    root_dir = root_path(root)
    files = {}

    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue

        text = read_text_safe(path)
        if text is None:
            continue

        rel = str(path.relative_to(root_dir))
        files[rel] = text

    data = {
        "root": root,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "files": files
    }

    snapshot_path(root).write_text(json.dumps(data), encoding="utf-8")

    return {
        "result": "snapshot saved",
        "root": root,
        "files": len(files),
        "path": str(snapshot_path(root))
    }


def load_snapshot(root="workspace"):
    path = snapshot_path(root)

    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def changed_files(root="workspace"):
    root = str(root or "workspace").strip()

    if root not in ROOTS:
        return {"error": "Unknown root: " + root}

    snap = load_snapshot(root)

    if not snap:
        return {"error": f"No snapshot found for root: {root}. Run /snapshot {root} first."}

    root_dir = root_path(root)
    old_files = snap.get("files", {})
    current_files = {}

    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue

        text = read_text_safe(path)
        if text is None:
            continue

        current_files[str(path.relative_to(root_dir))] = text

    changed = []

    all_paths = sorted(set(old_files.keys()) | set(current_files.keys()))

    for rel in all_paths:
        old = old_files.get(rel)
        new = current_files.get(rel)

        if old is None:
            status = "added"
        elif new is None:
            status = "deleted"
        elif old != new:
            status = "modified"
        else:
            continue

        changed.append({
            "root": root,
            "path": rel,
            "status": status
        })

    return {
        "root": root,
        "snapshot_created_at": snap.get("created_at"),
        "count": len(changed),
        "changed": changed
    }


def changed_files_text(root="workspace"):
    data = changed_files(root)

    if data.get("error"):
        return data["error"]

    if not data["changed"]:
        return f"No changed files since snapshot for root: {root}"

    lines = [
        f"Changed files for root: {root}",
        f"Snapshot: {data.get('snapshot_created_at')}",
        ""
    ]

    for item in data["changed"]:
        lines.append(f"- {item['status']}: {item['root']}:/{item['path']}")

    return "\n".join(lines)


def diff_file(root="workspace", rel_path=""):
    root = str(root or "workspace").strip()
    rel_path = str(rel_path or "").strip()

    if root not in ROOTS:
        return "Unknown root: " + root

    if not rel_path:
        return "No file path provided."

    snap = load_snapshot(root)

    if not snap:
        return f"No snapshot found for root: {root}. Run /snapshot {root} first."

    root_dir, target = safe_path(root, rel_path)
    current = read_text_safe(target) if target.exists() else ""

    old = snap.get("files", {}).get(rel_path)

    if old is None and current == "":
        return "File is not present in snapshot or current root: " + rel_path

    if old is None:
        old = ""

    old_lines = old.splitlines(keepends=True)
    new_lines = str(current or "").splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"snapshot/{root}/{rel_path}",
        tofile=f"current/{root}/{rel_path}",
        lineterm=""
    )

    diff_text = "".join(diff)

    if not diff_text.strip():
        return "No diff for: " + rel_path

    if len(diff_text) > 16000:
        diff_text = diff_text[:16000] + "\n\n[TRUNCATED DIFF]"

    return diff_text
