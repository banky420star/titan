from pathlib import Path
from datetime import datetime
import json

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")

ROOTS = {
    "workspace": BASE / "workspace",
    "products": BASE / "products",
    "skills": BASE / "skills",
    "rag": BASE / "rag" / "docs",
    "docs": BASE / "docs",
    "downloads": BASE / "downloads",
}

TEXT_SUFFIXES = {
    ".txt", ".md", ".py", ".json", ".yaml", ".yml",
    ".html", ".css", ".js", ".ts", ".tsx", ".jsx",
    ".sh", ".zsh", ".sql", ".csv", ".toml", ".ini",
    ".env", ".gitignore"
}

for root in ROOTS.values():
    root.mkdir(parents=True, exist_ok=True)


def root_path(root_name):
    root_name = str(root_name or "workspace").strip()

    if root_name not in ROOTS:
        raise ValueError("Unknown root: " + root_name)

    root = ROOTS[root_name].resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_path(root_name, rel_path=""):
    root = root_path(root_name)
    rel = Path(str(rel_path or "").strip())

    if rel.is_absolute():
        raise ValueError("Absolute paths are not allowed.")

    target = (root / rel).resolve()

    if target != root and not str(target).startswith(str(root) + "/"):
        raise ValueError("Path escapes allowed root.")

    return root, target


def file_info(root, path):
    stat = path.stat()
    return {
        "name": path.name,
        "path": str(path.relative_to(root)),
        "type": "dir" if path.is_dir() else "file",
        "size": stat.st_size if path.is_file() else None,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "text": path.is_file() and (path.suffix.lower() in TEXT_SUFFIXES or path.suffix == "")
    }


def list_dir(root_name="workspace", rel_path=""):
    root, target = safe_path(root_name, rel_path)

    if not target.exists():
        return {
            "root": root_name,
            "path": str(rel_path or ""),
            "error": "Path not found."
        }

    if not target.is_dir():
        target = target.parent

    dirs = []
    files = []

    for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if item.name.startswith(".DS_Store"):
            continue

        info = file_info(root, item)

        if item.is_dir():
            dirs.append(info)
        else:
            files.append(info)

    parent = ""
    if target != root:
        parent = str(target.parent.relative_to(root))

    return {
        "root": root_name,
        "path": str(target.relative_to(root)) if target != root else "",
        "parent": parent,
        "items": dirs + files,
        "roots": list(ROOTS.keys())
    }


def read_file(root_name="workspace", rel_path=""):
    root, target = safe_path(root_name, rel_path)

    if not target.exists():
        return {"error": "File not found."}

    if target.is_dir():
        return {"error": "Path is a folder."}

    if target.stat().st_size > 2_000_000:
        return {"error": "File too large for dashboard editor."}

    if target.suffix.lower() not in TEXT_SUFFIXES and target.suffix != "":
        return {"error": "Not a supported text file type."}

    return {
        "root": root_name,
        "path": str(target.relative_to(root)),
        "content": target.read_text(encoding="utf-8", errors="ignore"),
        "size": target.stat().st_size,
        "modified": datetime.fromtimestamp(target.stat().st_mtime).isoformat(timespec="seconds")
    }


def write_file(root_name="workspace", rel_path="", content=""):
    if root_name == "downloads":
        return {"error": "Downloads root is read-only from dashboard editor."}

    root, target = safe_path(root_name, rel_path)

    if target.exists() and target.is_dir():
        return {"error": "Cannot write over a folder."}

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(str(content or ""), encoding="utf-8")

    return {
        "result": "saved",
        "root": root_name,
        "path": str(target.relative_to(root)),
        "size": target.stat().st_size
    }


def make_dir(root_name="workspace", rel_path=""):
    if root_name == "downloads":
        return {"error": "Downloads root is read-only from dashboard editor."}

    root, target = safe_path(root_name, rel_path)
    target.mkdir(parents=True, exist_ok=True)

    return {
        "result": "folder created",
        "root": root_name,
        "path": str(target.relative_to(root))
    }
