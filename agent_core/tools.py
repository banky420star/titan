from pathlib import Path
import json
import re
import shlex
import subprocess
import sys
from agent_core.skills import create_skill_pack, list_skills, run_skill, install_dependency
from agent_core.rag import rag_status, rag_index, rag_search
from agent_core.memory import memory_save, memory_search, memory_list, memory_delete
from agent_core.web_tools import web_search, fetch_url, download_url

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
WORKSPACE = BASE / "workspace"
PRODUCTS = BASE / "products"
DOWNLOADS = BASE / "downloads"
SKILLS = BASE / "skills"
CONFIG_PATH = BASE / "config.json"

for folder in [WORKSPACE, PRODUCTS, DOWNLOADS, SKILLS]:
    folder.mkdir(parents=True, exist_ok=True)


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def compact(text, limit=12000):
    text = str(text or "")
    if text.startswith("%PDF-") or "\x00" in text[:2000]:
        return "[BINARY_OR_PDF_SUPPRESSED]"
    if len(text) > limit:
        return text[:limit] + "\n\n[TRUNCATED]"
    return text


def slug(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    return value.strip("-") or "item"


def workspace_path(filename):
    rel = Path(str(filename or "").strip())
    if rel.is_absolute():
        raise ValueError("Use workspace-relative paths only.")
    target = (WORKSPACE / rel).resolve()
    if not str(target).startswith(str(WORKSPACE.resolve())):
        raise ValueError("Path escapes workspace.")
    return target


def workspace_tree(max_items=180):
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    lines = ["workspace/"]
    items = sorted(WORKSPACE.rglob("*"))[:int(max_items)]

    if not items:
        lines.append("  empty")
    else:
        for p in items:
            rel = p.relative_to(WORKSPACE)
            lines.append("  " + str(rel) + ("/" if p.is_dir() else ""))

    return "\n".join(lines)


def list_files():
    return json.dumps(
        [str(p.relative_to(WORKSPACE)) for p in sorted(WORKSPACE.rglob("*")) if p.is_file()],
        indent=2
    )


def read_file(filename):
    p = workspace_path(filename)
    if not p.exists():
        return "File not found: " + str(filename)
    if p.is_dir():
        return "Path is a directory: " + str(filename)
    return compact(p.read_text(encoding="utf-8", errors="ignore"))


def write_file(filename, content):
    p = workspace_path(filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(str(content or ""), encoding="utf-8")
    return "Wrote file: " + str(p)


def append_file(filename, content):
    p = workspace_path(filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(str(content or ""))
    return "Appended file: " + str(p)


def list_products():
    PRODUCTS.mkdir(parents=True, exist_ok=True)
    items = [str(p) for p in sorted(PRODUCTS.iterdir()) if p.is_dir()]
    return "\n".join(items) if items else "No products found."


def run_command(command):
    from agent_core.approvals import validate_command, permission_status

    command = str(command or "").strip()

    ok, reason, parts = validate_command(command)

    if not ok:
        return (
            "Command blocked: " + reason + "\n\n"
            + permission_status()
        )

    try:
        r = subprocess.run(
            parts,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=120
        )

        return compact(
            f"Command: {command}\n"
            f"Reason: {reason}\n"
            f"cwd: {WORKSPACE}\n"
            f"exit_code: {r.returncode}\n\n"
            f"stdout:\n{r.stdout}\n\n"
            f"stderr:\n{r.stderr}",
            12000
        )
    except Exception as e:
        return "Command failed safely: " + repr(e)


def dispatch_tool(name, inp):
    inp = inp or {}

    # ── Workspace / file tools ──────────────────────────────
    if name == "workspace_tree":
        return workspace_tree(inp.get("max_items", 180))
    if name == "list_files":
        return list_files()
    if name == "read_file":
        return read_file(inp.get("filename", ""))
    if name == "write_file":
        return write_file(inp.get("filename", ""), inp.get("content", ""))
    if name == "append_file":
        return append_file(inp.get("filename", ""), inp.get("content", ""))
    if name == "run_command":
        return run_command(inp.get("command", ""))

    # ── Products (6 templates via products module) ──────────
    if name == "create_product":
        from agent_core.products import create_product as _create_product
        return _create_product(inp.get("name", ""), inp.get("kind", "python_cli"), inp.get("description", ""))
    if name == "list_products":
        return list_products()
    if name == "start_product":
        from agent_core.products import start_product
        return start_product(inp.get("name", ""))
    if name == "stop_product":
        from agent_core.products import stop_product
        return stop_product(inp.get("name", ""))
    if name == "product_logs":
        from agent_core.products import product_logs
        return product_logs(inp.get("name", ""))
    if name == "list_product_templates":
        from agent_core.product_templates import list_templates
        return list_templates()

    # ── Skills ──────────────────────────────────────────────
    if name == "list_skills":
        return list_skills()
    if name == "create_skill_pack":
        return create_skill_pack(inp.get("name", ""), inp.get("description", ""), inp.get("dependencies", []))
    if name == "run_skill":
        return run_skill(inp.get("name", ""), inp.get("task", ""), inp.get("context", ""))
    if name == "install_dependency":
        return install_dependency(inp.get("package", ""))

    # ── RAG ─────────────────────────────────────────────────
    if name == "rag_status":
        return rag_status()
    if name == "rag_index":
        return rag_index()
    if name == "rag_search":
        return rag_search(inp.get("query", ""), inp.get("top_k", 5))

    # ── Memory ──────────────────────────────────────────────
    if name == "memory_save":
        return memory_save(inp.get("text", ""), inp.get("kind", "project_fact"), inp.get("scope", "project"), inp.get("tags", []))
    if name == "memory_search":
        return memory_search(inp.get("query", ""), inp.get("scope", "all"), inp.get("limit", 8))
    if name == "memory_list":
        return memory_list(inp.get("scope", "all"), inp.get("limit", 40))
    if name == "memory_delete":
        return memory_delete(inp.get("id", ""))

    # ── Web ─────────────────────────────────────────────────
    if name == "web_search":
        return web_search(inp.get("query", ""), inp.get("max_results", 6))
    if name == "fetch_url":
        return fetch_url(inp.get("url", ""))
    if name == "download_url":
        return download_url(inp.get("url", ""), inp.get("filename", ""))

    # ── Image generation ────────────────────────────────────
    if name == "create_image":
        from agent_core.media_engine import create_image
        return create_image(inp.get("prompt", ""), inp.get("width"), inp.get("height"), inp.get("open_file", True), inp.get("nsfw", False))
    if name == "create_gif":
        from agent_core.media_engine import create_gif
        return create_gif(inp.get("prompt", ""), inp.get("width"), inp.get("height"), inp.get("frames", 28), inp.get("open_file", True), inp.get("nsfw", False))
    if name == "list_images":
        from agent_core.media_engine import list_images
        return list_images(inp.get("limit", 40))
    if name == "set_image_backend":
        from agent_core.media_engine import set_image_backend
        return set_image_backend(inp.get("backend", "pollinations"))
    if name == "set_image_enhance":
        from agent_core.media_engine import set_image_enhance
        return set_image_enhance(inp.get("value", "on"))

    # ── Video generation ────────────────────────────────────
    if name == "create_video":
        from agent_core.video_tools import create_video
        return create_video(inp.get("prompt", ""), seconds=inp.get("seconds"), fps=inp.get("fps"))
    if name == "list_videos":
        from agent_core.video_tools import list_videos
        return list_videos(inp.get("limit", 40))
    if name == "video_status":
        from agent_core.media_engine import video_status
        return video_status()
    if name == "set_video_quality":
        from agent_core.media_engine import set_video_quality
        return set_video_quality(inp.get("quality", "medium"))
    if name == "set_video_motion":
        from agent_core.media_engine import set_video_motion
        return set_video_motion(inp.get("motion", "high"))

    # ── ComfyUI ─────────────────────────────────────────────
    if name == "comfy_status":
        from agent_core.comfyui_bridge import comfy_info
        return comfy_info()
    if name == "start_comfyui":
        from agent_core.comfyui_bridge import start_comfyui
        return start_comfyui()
    if name == "stop_comfyui":
        from agent_core.comfyui_bridge import stop_comfyui
        return stop_comfyui()
    if name == "comfy_image":
        from agent_core.comfyui_bridge import comfy_image
        return comfy_image(inp.get("prompt", ""), inp.get("width", 1024), inp.get("height", 1536))

    # ── Search / diff / snapshot ───────────────────────────
    if name == "search_files":
        from agent_core.search_diff import search_files_text
        return search_files_text(inp.get("query", ""), root=inp.get("root", "all"))
    if name == "snapshot":
        from agent_core.search_diff import make_snapshot
        return make_snapshot(inp.get("root", "workspace"))
    if name == "changed_files":
        from agent_core.search_diff import changed_files_text
        return changed_files_text(inp.get("root", "workspace"))
    if name == "diff_file":
        from agent_core.search_diff import diff_file
        return diff_file(inp.get("root", "workspace"), inp.get("path", ""))

    # ── Subagents / team ────────────────────────────────────
    if name == "call_subagent":
        from agent_core.subagents import call_subagent
        return call_subagent(inp.get("role", "coder"), inp.get("task", ""), inp.get("context", ""))
    if name == "run_team":
        from agent_core.subagents import run_team
        return run_team(inp.get("task", ""))
    if name == "list_subagents":
        from agent_core.subagents import format_subagents
        return format_subagents()

    # ── Chat history ───────────────────────────────────────
    if name == "log_event":
        from agent_core.chat_history import log_event
        return log_event(inp.get("role", "user"), inp.get("content", ""), section=inp.get("section"), meta=inp.get("meta"))
    if name == "set_section":
        from agent_core.chat_history import set_section
        return set_section(inp.get("section", ""))
    if name == "history_text":
        from agent_core.chat_history import history_text
        return history_text(section=inp.get("section"), limit=inp.get("limit", 60))

    # ── Permissions ────────────────────────────────────────
    if name == "set_permission_mode":
        from agent_core.approvals import set_mode
        return set_mode(inp.get("mode", "safe"))

    # ── Upscale ─────────────────────────────────────────────
    if name == "upscale_image":
        from agent_core.upscale_tools import upscale_image
        return upscale_image(inp.get("src", ""), inp.get("scale", 2))

    # ── Idea chat ──────────────────────────────────────────
    if name == "idea_chat":
        from agent_core.idea_chat import idea_chat
        return idea_chat(inp.get("task", ""), mode=inp.get("mode", "idea"))

    return "Unknown tool: " + str(name)
