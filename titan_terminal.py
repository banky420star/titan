#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG = BASE / "config.json"
DASHBOARD_URL = "http://127.0.0.1:5050"

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except Exception:
    Console = None
    Panel = None
    Table = None
    Text = None

console = Console() if Console else None


TITAN_FACE = r"""
          .
         /|\
      .-~~~~~-.
     /  o   o  \
    |     v     |
     \  \___/  /
      '-.____.-'
        /|   |\
       /_|___|_\
"""


def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def say_panel(body, title="Titan", style="cyan"):
    if console and Panel:
        console.print(Panel(str(body), title=title, border_style=style))
    else:
        print(f"\n[{title}]\n{body}\n")


def titan_logo_text(open_eyes=True):
    logo = Text()

    # Pixel-cell colours.
    colors = {
        ".": None,
        "Y": "#F8E45C",
        "y": "#DDBB24",
        "O": "#F6A623",
        "o": "#D97817",
        "R": "#EF7C73",
        "r": "#C94C4C",
        "B": "#0F172A",
        "W": "#FFFFFF",
        "S": "#CBD5E1",
    }

    # Pixel-art Titan.
    # Y = yellow block, O = orange block, R = coral block
    # B/W/S = eye and shine pixels
    if open_eyes:
        rows = [
            "........OOOOO........",
            ".......OOOOOOO.......",
            ".......OOOOOOO.......",
            "....YYYYOOOOOOORRR...",
            "...YYYYYOOOOOOORRRR..",
            "..YYYYYYOOBWOOOBWRRR.",
            "..YYYYYYOOBBOOOBBRRR.",
            ".YYYYYYYOOOOOOORRRRR.",
            ".YYYYYYYOOOBOOORRRRR.",
            "..YYYYYYOOOBBOORRRR..",
            "...YYYYYOOOOOOORRR...",
            "....YYY..OOO..RRR....",
            "....YY...OOO...RR....",
            ".........ooo.........",
        ]
    else:
        rows = [
            "........OOOOO........",
            ".......OOOOOOO.......",
            ".......OOOOOOO.......",
            "....YYYYOOOOOOORRR...",
            "...YYYYYOOOOOOORRRR..",
            "..YYYYYYOOBBBOOBBBRR.",
            "..YYYYYYOOOOOOORRRRR.",
            ".YYYYYYYOOOOOOORRRRR.",
            ".YYYYYYYOOOBOOORRRRR.",
            "..YYYYYYOOOBBOORRRR..",
            "...YYYYYOOOOOOORRR...",
            "....YYY..OOO..RRR....",
            "....YY...OOO...RR....",
            ".........ooo.........",
        ]

    logo.append("\n")

    for row in rows:
        logo.append("      ")
        for cell in row:
            color = colors.get(cell)
            if color:
                logo.append("  ", style=f"on {color}")
            else:
                logo.append("  ")
        logo.append("\n")

    logo.append("\n")
    return logo


def startup_frame(open_eyes=True):
    cfg = load_config()

    body = Text()
    body.append(titan_logo_text(open_eyes=open_eyes))
    body.append("Titan clean terminal\n", style="bold white")
    body.append(f"Base: {BASE}\n", style="dim")
    body.append(f"Workspace: {cfg.get('workspace', BASE / 'workspace')}\n", style="dim")
    body.append(f"Model: {cfg.get('model', 'unset')}\n", style="cyan")
    body.append(f"Fallback: {cfg.get('fallback_model', 'unset')}\n", style="cyan")
    body.append("Dashboard: http://127.0.0.1:5050\n", style="green")

    console.print(Panel(body, title="Titan", border_style="magenta"))


def titan_prompt():
    reset = "\033[0m"

    yellow = "\033[48;2;232;221;105m  " + reset

    orange_eye = (
        "\033[48;2;232;171;67m"
        "\033[38;2;15;23;42m⬤"
        "\033[38;2;255;255;255m•"
        "\033[48;2;232;171;67m "
        + reset
    )

    coral_eye = (
        "\033[48;2;221;134;123m"
        "\033[38;2;15;23;42m⬤"
        "\033[38;2;255;255;255m•"
        "\033[48;2;221;134;123m "
        + reset
    )

    return f"\n{yellow}{orange_eye}{coral_eye} titan ▸ "


def startup():
    cfg = load_config()

    if console and Panel and Text:
        # Blink animation: open → closed → open.
        try:
            for open_eyes, delay in [(True, 0.35), (False, 0.14), (True, 0.28)]:
                console.clear()
                startup_frame(open_eyes=open_eyes)
                time.sleep(delay)
        except Exception:
            startup_frame(open_eyes=True)

    else:
        body = (
            "\n"
            "                ████████\n"
            "                ████████\n"
            "        ████████ ████████ ████████\n"
            "        ████████ ████████ ████████\n"
            "        ████████   ●      ●  █████\n"
            "        ████████ ████████ ████████\n"
            "        ████████ ████████ ████████\n"
            "        ████████ ████████ ████████\n"
            "                ████████\n"
            "                ████████\n\n"
            "Titan clean terminal\n"
            f"Base: {BASE}\n"
            f"Workspace: {cfg.get('workspace', BASE / 'workspace')}\n"
            f"Model: {cfg.get('model', 'unset')}\n"
            f"Fallback: {cfg.get('fallback_model', 'unset')}\n"
            "Dashboard: http://127.0.0.1:5050\n"
        )
        say_panel(body, title="Titan", style="magenta")

def help_menu():
    say_panel(
        "/help        Show commands\n"
        "/doctor      Check core folders/files\n"
        "/models      Show model config\n"
        "/dashboard   Launch dashboard on 5050\n"
        "/tree        Show workspace tree\n"
        "/bg <task>   Start a simple background job record\n"
        "/jobs        Show jobs\n"
        "/exit        Quit\n\n"
        "Plain text prompts are currently echoed in clean-reset mode.\n"
        "Next step: wire agent_core and Ollama back in cleanly.",
        title="Help",
        style="cyan"
    )


def doctor():
    checks = [
        ("Base", BASE.exists(), str(BASE)),
        ("Config", CONFIG.exists(), str(CONFIG)),
        ("Workspace", (BASE / "workspace").exists(), str(BASE / "workspace")),
        ("Models", (BASE / "models").exists(), str(BASE / "models")),
        ("Venv", (BASE / "venv").exists(), str(BASE / "venv")),
        ("Dashboard", (BASE / "control_panel.py").exists(), str(BASE / "control_panel.py")),
        ("Launcher", (BASE / "launch_dashboard.py").exists(), str(BASE / "launch_dashboard.py")),
        ("Jobs", (BASE / "jobs").exists(), str(BASE / "jobs")),
    ]

    if console and Table:
        table = Table(title="Titan Doctor")
        table.add_column("Check")
        table.add_column("Status")
        table.add_column("Detail")
        for name, ok, detail in checks:
            table.add_row(name, "OK" if ok else "FAIL", detail)
        console.print(table)
    else:
        for name, ok, detail in checks:
            print(name, "OK" if ok else "FAIL", detail)



def set_model_profile(profile):
    cfg = load_config()
    profiles = cfg.get("model_profiles", {})

    if profile not in profiles:
        say_panel(
            "Unknown profile: " + profile + "\n\nAvailable: " + ", ".join(profiles.keys()),
            title="Models",
            style="yellow"
        )
        return

    selected = profiles[profile]

    for key, value in selected.items():
        cfg[key] = value

    cfg["active_profile"] = profile
    CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    say_panel(
        f"Profile enabled: {profile}\n\n"
        f"Model: {cfg.get('model')}\n"
        f"Fallback: {cfg.get('fallback_model')}\n"
        f"Context: {cfg.get('num_ctx')}\n"
        f"Predict: {cfg.get('num_predict')}\n"
        f"Max steps: {cfg.get('max_agent_steps')}",
        title="Models",
        style="green"
    )


def models():
    cfg = load_config()
    role_models = cfg.get("role_models", {})
    lines = [
        f"Main: {cfg.get('model', 'unset')}",
        f"Fallback: {cfg.get('fallback_model', 'unset')}",
        "",
        "Role models:"
    ]
    for role, model in role_models.items():
        lines.append(f"- {role}: {model}")
    say_panel("\n".join(lines), title="Models", style="green")


def dashboard_running():
    try:
        with urllib.request.urlopen(DASHBOARD_URL, timeout=1.2) as response:
            return response.status == 200
    except Exception:
        return False


def launch_dashboard():
    launcher = BASE / "launch_dashboard.py"
    if not launcher.exists():
        say_panel("launch_dashboard.py is missing.", title="Dashboard", style="red")
        return

    result = subprocess.run(
        [sys.executable, str(launcher)],
        cwd=str(BASE),
        capture_output=True,
        text=True,
        timeout=20
    )

    body = (
        f"exit_code: {result.returncode}\n\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    say_panel(body, title="Dashboard", style="green" if result.returncode == 0 else "red")


def workspace_tree():
    root = BASE / "workspace"
    root.mkdir(exist_ok=True)

    lines = ["workspace/"]
    items = sorted(root.rglob("*"))

    if not items:
        lines.append("  empty")
    else:
        for p in items[:120]:
            rel = p.relative_to(root)
            lines.append("  " + str(rel) + ("/" if p.is_dir() else ""))

    say_panel("\n".join(lines), title="Workspace", style="cyan")


def bg_job(task):
    jobs_dir = BASE / "jobs"
    running = jobs_dir / "running"
    logs = jobs_dir / "logs"
    running.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    job_id = "term-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    job = {
        "id": job_id,
        "task": task,
        "status": "queued",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": "terminal",
        "max_steps": 8
    }

    (running / f"{job_id}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")

    worker = BASE / "background_worker.py"
    subprocess.Popen(
        [sys.executable, str(worker), job_id],
        cwd=str(BASE),
        stdout=(logs / f"{job_id}.stdout.log").open("w"),
        stderr=(logs / f"{job_id}.stderr.log").open("w"),
        start_new_session=True
    )

    say_panel(
        f"Started background job: {job_id}\\n\\nUse /jobs or /job {job_id}",
        title="Background Job",
        style="green"
    )


def jobs():
    rows = []
    for folder_name in ["running", "done", "cancelled"]:
        folder = BASE / "jobs" / folder_name
        folder.mkdir(parents=True, exist_ok=True)

        for p in sorted(folder.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                rows.append(f"{data.get('id', p.stem)} | {data.get('status', folder_name)} | {data.get('task', '')[:120]}")
            except Exception as e:
                rows.append(f"{p.name} | unreadable | {e!r}")

    say_panel("\\n".join(rows) if rows else "No jobs found.", title="Jobs", style="cyan")


def show_job(job_id):
    job_id = str(job_id).strip()
    for folder_name in ["running", "done"]:
        p = BASE / "jobs" / folder_name / f"{job_id}.json"
        if p.exists():
            body = p.read_text(encoding="utf-8")
            say_panel(body[-12000:], title=f"Job: {job_id}", style="cyan")
            return
    say_panel("Job not found: " + job_id, title="Job", style="yellow")


def show_trace(job_id):
    job_id = str(job_id).strip()
    p = BASE / "jobs" / "traces" / f"{job_id}.trace.md"
    if p.exists():
        say_panel(p.read_text(errors="ignore")[-12000:], title=f"Trace: {job_id}", style="yellow")
    else:
        say_panel("Trace not found: " + job_id, title="Trace", style="yellow")



def run_titan_prompt(command):
    # TITAN_NATURAL_MEDIA_ROUTER_V1
    try:
        from agent_core.natural_media import route_natural_media
        _media = route_natural_media(command)
        if _media and _media.get("handled"):
            return _media.get("text", "")
    except Exception as _media_error:
        return "Media request failed: " + repr(_media_error)


    cmd = str(command or "").strip()
    low = cmd.lower()

    user_log_id = None
    try:
        from agent_core.chat_history import log_event
        user_log_id = log_event("user", cmd, meta={"source": "terminal"})
    except Exception:
        pass

    try:
        # Fast shortcuts: no Ollama call.
        if low in ["show me the workspace tree.", "show me the workspace tree", "workspace tree", "tree"]:
            from agent_core.tools import workspace_tree
            result = workspace_tree()
        elif low in ["list files", "show files", "list workspace files"]:
            from agent_core.tools import list_files
            result = list_files()
        elif low in ["list products", "show products", "products"]:
            from agent_core.products import list_products_text
            result = list_products_text()
        elif low in ["list skills", "show skills", "skills"]:
            from agent_core.skills import list_skills
            result = list_skills()
        elif low.startswith("read "):
            from agent_core.tools import read_file
            result = read_file(cmd[5:].strip())
        elif low.startswith("create product "):
            from agent_core.products import create_product
            name = cmd.replace("create product ", "", 1).strip()
            result = create_product(name, "python_cli", "Created from fast terminal shortcut.")
        else:
            from agent_core.agent import run_agent
            cfg = load_config()
            result = run_agent(cmd, max_steps=int(cfg.get("max_agent_steps", 5)))

        try:
            from agent_core.chat_history import log_event
            log_event("assistant", result, meta={"source": "terminal", "reply_to": user_log_id})
        except Exception:
            pass

        return result

    except Exception as e:
        result = "Titan brain failed safely: " + repr(e)
        try:
            from agent_core.chat_history import log_event
            log_event("assistant", result, meta={"source": "terminal", "reply_to": user_log_id, "error": True})
        except Exception:
            pass
        return result


def terminal_section(name):
    try:
        from agent_core.chat_history import set_section
        say_panel(set_section(name), title="Chat Section", style="green")
    except Exception as e:
        say_panel("Section failed: " + repr(e), title="Chat Section", style="red")


def terminal_sections():
    try:
        from agent_core.chat_history import list_sections
        say_panel(json.dumps(list_sections(), indent=2), title="Chat Sections", style="cyan")
    except Exception as e:
        say_panel("Sections failed: " + repr(e), title="Chat Sections", style="red")


def terminal_history(args=""):
    try:
        from agent_core.chat_history import history_text
        section = str(args or "").strip() or None
        say_panel(history_text(section=section, limit=80), title="Chat History", style="magenta")
    except Exception as e:
        say_panel("History failed: " + repr(e), title="Chat History", style="red")


def terminal_history_search(query):
    try:
        from agent_core.chat_history import history_search_text
        say_panel(history_search_text(query, limit=40), title="History Search", style="cyan")
    except Exception as e:
        say_panel("History search failed: " + repr(e), title="History Search", style="red")




def terminal_export_history(args=""):
    try:
        from agent_core.chat_export import export_history, export_all_sections

        section = str(args or "").strip()

        if section.lower() == "all-sections":
            result = export_all_sections()
        else:
            result = export_history(section or None)

        say_panel(json.dumps(result, indent=2), title="History Export", style="green")
    except Exception as e:
        say_panel("History export failed: " + repr(e), title="History Export", style="red")



def terminal_templates():
    try:
        import json
        from agent_core.product_templates import list_templates
        say_panel(json.dumps(list_templates(), indent=2), title="Product Templates", style="cyan")
    except Exception as e:
        say_panel("Templates failed: " + repr(e), title="Product Templates", style="red")


def terminal_product_template(args):
    try:
        import json
        from agent_core.product_templates import build_product
        parts = str(args or "").strip().split(" ", 1)
        if len(parts) < 2:
            say_panel("Usage: /product-template <template> <name>", title="Product Templates", style="yellow")
            return
        template, name = parts[0], parts[1]
        result = build_product(name, template, f"Created from Titan template: {template}")
        say_panel(json.dumps(result, indent=2), title="Product Template", style="green")
    except Exception as e:
        say_panel("Product template failed: " + repr(e), title="Product Templates", style="red")



def terminal_products():
    try:
        from agent_core.products import list_products_text
        say_panel(list_products_text(), title="Products", style="cyan")
    except Exception as e:
        say_panel("Products failed: " + repr(e), title="Products", style="red")


def terminal_product_create(args):
    try:
        from agent_core.products import create_product

        parts = str(args or "").strip().split()
        if not parts:
            say_panel("Usage: /product-create <name> [template]", title="Products", style="yellow")
            return

        name = parts[0]
        kind = parts[1] if len(parts) > 1 else "python_cli"

        result = create_product(name, kind, "Created from Titan terminal.")
        say_panel(str(result), title="Product Created", style="green")
    except Exception as e:
        say_panel("Create product failed: " + repr(e), title="Products", style="red")


def terminal_product_start(name):
    try:
        import json
        from agent_core.products import start_product
        result = start_product(name)
        say_panel(json.dumps(result, indent=2), title="Product Start", style="green")
    except Exception as e:
        say_panel("Start product failed: " + repr(e), title="Products", style="red")


def terminal_product_stop(name):
    try:
        import json
        from agent_core.products import stop_product
        result = stop_product(name)
        say_panel(json.dumps(result, indent=2), title="Product Stop", style="yellow")
    except Exception as e:
        say_panel("Stop product failed: " + repr(e), title="Products", style="red")


def terminal_product_logs(name):
    try:
        import json
        from agent_core.products import product_logs
        result = product_logs(name)
        say_panel(json.dumps(result, indent=2), title="Product Logs", style="magenta")
    except Exception as e:
        say_panel("Product logs failed: " + repr(e), title="Products", style="red")




def show_permission_mode():
    try:
        from agent_core.approvals import permission_status
        say_panel(permission_status(), title="Permissions", style="cyan")
    except Exception as e:
        say_panel("Permission status failed: " + repr(e), title="Permissions", style="red")


def set_permission_mode_terminal(mode):
    try:
        from agent_core.approvals import set_mode
        say_panel(set_mode(mode), title="Permissions", style="green")
    except Exception as e:
        say_panel("Permission mode failed: " + repr(e), title="Permissions", style="red")


def terminal_idea_chat(args, mode="idea"):
    try:
        from agent_core.idea_chat import idea_chat

        task = str(args or "").strip()
        if not task:
            say_panel("Usage: /idea <your idea>", title="Idea Chat", style="yellow")
            return

        result = idea_chat(task, mode=mode)
        say_panel(result, title=f"Titan {mode.title()}", style="cyan")
    except Exception as e:
        say_panel("Idea chat failed: " + repr(e), title="Idea Chat", style="red")


def terminal_set_idea_model(model):
    try:
        import json
        from pathlib import Path

        cfg_path = Path("config.json")
        cfg = json.loads(cfg_path.read_text())
        cfg["idea_model"] = str(model or "").strip() or cfg.get("model", "qwen3:8b")
        cfg_path.write_text(json.dumps(cfg, indent=2))
        say_panel("Idea model set to: " + cfg["idea_model"], title="Idea Model", style="green")
    except Exception as e:
        say_panel("Idea model failed: " + repr(e), title="Idea Model", style="red")




def terminal_create_image(args):
    try:
        import json
        from agent_core.image_tools import create_image

        prompt = str(args or "").strip()
        if not prompt:
            say_panel("Usage: /image <prompt>", title="Image", style="yellow")
            return

        result = create_image(prompt)
        say_panel(json.dumps(result, indent=2), title="Image Created", style="green")
    except Exception as e:
        say_panel("Image creation failed: " + repr(e), title="Image", style="red")


def terminal_create_gif(args):
    try:
        import json
        from agent_core.image_tools import create_gif

        prompt = str(args or "").strip()
        if not prompt:
            say_panel("Usage: /gif <prompt>", title="GIF", style="yellow")
            return

        result = create_gif(prompt)
        say_panel(json.dumps(result, indent=2), title="GIF Created", style="green")
    except Exception as e:
        say_panel("GIF creation failed: " + repr(e), title="GIF", style="red")


def terminal_list_images():
    try:
        import json
        from agent_core.image_tools import list_images
        say_panel(json.dumps(list_images(), indent=2), title="Images", style="cyan")
    except Exception as e:
        say_panel("Images failed: " + repr(e), title="Images", style="red")




# TITAN_SLASH_DROPDOWN_START
TITAN_SLASH_COMMANDS = [
    "/help",
    "/doctor",
    "/models",
    "/dashboard",
    "/tree",
    "/bg ",
    "/jobs",
    "/job ",
    "/trace-job ",
    "/cancel ",
    "/web ",
    "/fetch ",
    "/download ",
    "/mode",
    "/safe",
    "/power",
    "/agentic",
    "/run ",
    "/products",
    "/product-create ",
    "/product-template ",
    "/product-start ",
    "/product-stop ",
    "/product-logs ",
    "/templates",
    "/search ",
    "/snapshot ",
    "/changed ",
    "/diff ",
    "/section ",
    "/sections",
    "/history",
    "/history-search ",
    "/export-history ",
    "/idea ",
    "/brainstorm ",
    "/critic ",
    "/builder ",
    "/simple ",
    "/idea-model ",
    "/image ",
    "/gif ",
    "/images",
    "/image-backend ",
    "/image-enhance ",
    "/memory",
    "/remember ",
    "/forget ",
    "/rag",
    "/skills",
    "/exit",
]

TITAN_SLASH_META = {
    "/help": "Show commands",
    "/doctor": "Check Titan folders/files",
    "/models": "Show model config",
    "/dashboard": "Launch dashboard",
    "/tree": "Show workspace tree",
    "/bg ": "Start background job",
    "/jobs": "Show jobs",
    "/job ": "Show job detail",
    "/trace-job ": "Show job trace",
    "/cancel ": "Cancel job",
    "/web ": "Search web",
    "/fetch ": "Fetch URL",
    "/download ": "Download URL",
    "/mode": "Show permission mode",
    "/safe": "Read/check mode",
    "/power": "Workspace build mode",
    "/agentic": "Autonomous build mode",
    "/run ": "Run approved shell command",
    "/products": "Show products",
    "/product-create ": "Create product",
    "/product-template ": "Create product from template",
    "/product-start ": "Start product",
    "/product-stop ": "Stop product",
    "/product-logs ": "Show product logs",
    "/templates": "Show product templates",
    "/search ": "Search files",
    "/snapshot ": "Save snapshot",
    "/changed ": "Show changed files",
    "/diff ": "Show file diff",
    "/section ": "Set project section",
    "/sections": "List project sections",
    "/history": "Show chat history",
    "/history-search ": "Search chat history",
    "/export-history ": "Export history markdown",
    "/idea ": "Chat about an idea",
    "/brainstorm ": "Generate options",
    "/critic ": "Find weak spots",
    "/builder ": "Turn idea into build plan",
    "/simple ": "Explain simply",
    "/idea-model ": "Set idea model",
    "/image ": "Create image",
    "/gif ": "Create short GIF",
    "/images": "List images",
    "/image-backend ": "Set image backend",
    "/image-enhance ": "Toggle prompt enhancement",
    "/memory": "Show memory",
    "/remember ": "Save memory",
    "/forget ": "Delete memory",
    "/rag": "RAG tools",
    "/skills": "Show skills",
    "/exit": "Quit Titan",
}


def titan_prompt_input(prompt_text):
    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.completion import Completer, Completion
        from prompt_toolkit.shortcuts import CompleteStyle
        from prompt_toolkit.styles import Style
        from prompt_toolkit.formatted_text import ANSI

        class TitanSlashCompleter(Completer):
            def get_completions(self, document, complete_event):
                before = document.text_before_cursor
                stripped = before.strip()

                if not stripped.startswith("/") and not stripped.startswith("\\"):
                    return

                normalized = "/" + stripped[1:] if stripped.startswith("\\") else stripped

                for cmd in TITAN_SLASH_COMMANDS:
                    if cmd.startswith(normalized):
                        meta = TITAN_SLASH_META.get(cmd, "")
                        yield Completion(
                            cmd,
                            start_position=-len(stripped),
                            display=cmd,
                            display_meta=meta,
                        )

        style = Style.from_dict({
            "completion-menu.completion": "bg:#202124 #f4f4f5",
            "completion-menu.completion.current": "bg:#e8ab43 #111214 bold",
            "completion-menu.meta.completion": "bg:#202124 #a1a1aa",
            "completion-menu.meta.completion.current": "bg:#e8ab43 #111214",
        })

        raw_prompt = str(prompt_text or "titan ▸ ")

        value = prompt(
            ANSI(raw_prompt),
            completer=TitanSlashCompleter(),
            complete_style=CompleteStyle.COLUMN,
            complete_while_typing=True,
            reserve_space_for_menu=10,
            style=style,
        )

        value = str(value or "")

        if value.startswith("\\"):
            value = "/" + value[1:]

        return value

    except KeyboardInterrupt:
        raise
    except EOFError:
        raise
    except Exception:
        return input("titan ▸ ")

# TITAN_SLASH_DROPDOWN_END



def terminal_image_status():
    try:
        import json
        from pathlib import Path

        cfg_path = Path("config.json")
        cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}

        info = {
            "image_backend": cfg.get("image_backend", "local"),
            "image_enhance_prompt": cfg.get("image_enhance_prompt", False),
            "verify_ssl": cfg.get("verify_ssl", True),
            "usage": {
                "/image-backend local": "Use local fallback generator",
                "/image-backend pollinations": "Use web image generator",
                "/image-enhance on": "Enhance image prompts",
                "/image-enhance off": "Use exact prompt",
                "/image <prompt>": "Create image",
                "/gif <prompt>": "Create short GIF"
            }
        }

        say_panel(json.dumps(info, indent=2), title="Image Backend", style="cyan")
    except Exception as e:
        say_panel("Image backend status failed: " + repr(e), title="Image Backend", style="red")




def terminal_upscale_image(args):
    try:
        import json
        from agent_core.upscale_tools import upscale_image

        raw = str(args or "").strip()
        if not raw:
            say_panel("Usage: /upscale <file_path> [scale]", title="Upscale", style="yellow")
            return

        parts = raw.split()
        file_path = parts[0]
        scale = int(parts[1]) if len(parts) > 1 else 2

        result = upscale_image(file_path, scale=scale)
        say_panel(json.dumps(result, indent=2), title="Upscale", style="green")
    except Exception as e:
        say_panel("Upscale failed: " + repr(e), title="Upscale", style="red")



def terminal_comfy_status():
    try:
        import json
        from agent_core.comfyui_bridge import comfy_info
        say_panel(json.dumps(comfy_info(), indent=2), title="ComfyUI", style="cyan")
    except Exception as e:
        say_panel("ComfyUI status failed: " + repr(e), title="ComfyUI", style="red")


def terminal_comfy_start():
    try:
        import json
        from agent_core.comfyui_bridge import start_comfyui
        say_panel(json.dumps(start_comfyui(), indent=2), title="ComfyUI Start", style="green")
    except Exception as e:
        say_panel("ComfyUI start failed: " + repr(e), title="ComfyUI", style="red")


def terminal_comfy_stop():
    try:
        import json
        from agent_core.comfyui_bridge import stop_comfyui
        say_panel(json.dumps(stop_comfyui(), indent=2), title="ComfyUI Stop", style="yellow")
    except Exception as e:
        say_panel("ComfyUI stop failed: " + repr(e), title="ComfyUI", style="red")


def terminal_comfy_image(args):
    try:
        import json
        from agent_core.comfyui_bridge import comfy_image

        prompt = str(args or "").strip()
        if not prompt:
            say_panel("Usage: /comfy-image <prompt>", title="ComfyUI Image", style="yellow")
            return

        result = comfy_image(prompt)
        say_panel(json.dumps(result, indent=2), title="ComfyUI Image", style="green")
    except Exception as e:
        say_panel("ComfyUI image failed: " + repr(e), title="ComfyUI Image", style="red")



# TITAN_MULTILINE_QUEUE_V1
_titan_command_queue = []

def titan_next_command(prompt_text):
    global _titan_command_queue

    if _titan_command_queue:
        return _titan_command_queue.pop(0)

    raw = titan_prompt_input(prompt_text)
    raw = str(raw or "").replace("\r\n", "\n").replace("\r", "\n")

    parts = [line.strip() for line in raw.split("\n") if line.strip()]

    if not parts:
        return ""

    if len(parts) > 1:
        _titan_command_queue.extend(parts[1:])

    return parts[0]


def terminal_set_image_backend_simple(backend):
    try:
        import json
        from pathlib import Path

        cfg_path = Path("config.json")
        cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}

        backend = str(backend or "").strip() or "comfyui"
        cfg["image_backend"] = backend

        if backend == "comfyui":
            cfg["image_width"] = int(cfg.get("image_width", 768))
            cfg["image_height"] = int(cfg.get("image_height", 768))
            cfg["comfy_steps"] = int(cfg.get("comfy_steps", 4))
            cfg["comfy_cfg"] = float(cfg.get("comfy_cfg", 1.0))

        cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

        say_panel(json.dumps({
            "result": "image backend updated",
            "image_backend": cfg["image_backend"],
            "image_width": cfg.get("image_width"),
            "image_height": cfg.get("image_height"),
            "comfy_steps": cfg.get("comfy_steps"),
            "comfy_cfg": cfg.get("comfy_cfg")
        }, indent=2), title="Image Backend", style="green")
    except Exception as e:
        say_panel("Image backend failed: " + repr(e), title="Image Backend", style="red")




def terminal_create_video(args):
    try:
        import json
        from agent_core.video_tools import create_video

        prompt = str(args or "").strip()
        if not prompt:
            say_panel("Usage: /video <prompt>", title="Video", style="yellow")
            return

        result = create_video(prompt)
        say_panel(json.dumps(result, indent=2), title="Video Created", style="green")
    except Exception as e:
        say_panel("Video creation failed: " + repr(e), title="Video", style="red")


def terminal_list_videos():
    try:
        import json
        from agent_core.video_tools import list_videos
        say_panel(json.dumps(list_videos(), indent=2), title="Videos", style="cyan")
    except Exception as e:
        say_panel("Videos failed: " + repr(e), title="Videos", style="red")


def terminal_video_quality(args):
    try:
        import json
        from agent_core.video_tools import set_video_quality
        result = set_video_quality(args)
        say_panel(json.dumps(result, indent=2), title="Video Quality", style="green")
    except Exception as e:
        say_panel("Video quality failed: " + repr(e), title="Video Quality", style="red")




def terminal_video_motion(args):
    try:
        import json
        from agent_core.video_tools import set_video_motion
        result = set_video_motion(args)
        say_panel(json.dumps(result, indent=2), title="Video Motion", style="green")
    except Exception as e:
        say_panel("Video motion failed: " + repr(e), title="Video Motion", style="red")



def repl():
    startup()
    print("Type /help for commands.")

    while True:
        try:
            command = titan_next_command(titan_prompt()).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not command:
            continue

        try:
            lower = command.lower()
            # TITAN_COMFY_COMMANDS_V1
            # TITAN_VIDEO_KEYFRAME_COMMANDS_V3
            if lower.startswith("/video "):
                terminal_create_video(command.replace("/video ", "", 1).strip())
                continue

            if lower == "/videos":
                terminal_list_videos()
                continue

            if lower == "/video-status":
                terminal_video_status()
                continue

            if lower.startswith("/video-quality "):
                terminal_video_quality(command.replace("/video-quality ", "", 1).strip())
                continue

            if lower.startswith("/video-motion "):
                terminal_video_motion(command.replace("/video-motion ", "", 1).strip())
                continue

            if lower.startswith("/video-image-backend "):
                terminal_video_image_backend(command.replace("/video-image-backend ", "", 1).strip())
                continue


            if lower.startswith("/video-motion "):
                terminal_video_motion(command.replace("/video-motion ", "", 1).strip())
                continue


            if lower.startswith("/video "):
                terminal_create_video(command.replace("/video ", "", 1).strip())
                continue

            if lower == "/videos":
                terminal_list_videos()
                continue

            if lower.startswith("/video-quality "):
                terminal_video_quality(command.replace("/video-quality ", "", 1).strip())
                continue


            if lower == "/comfy-status":
                terminal_comfy_status()
                continue

            if lower == "/comfy-start":
                terminal_comfy_start()
                continue

            if lower == "/comfy-stop":
                terminal_comfy_stop()
                continue

            if lower.startswith("/comfy-image "):
                terminal_comfy_image(command.replace("/comfy-image ", "", 1).strip())
                continue

            if lower == "/image-backend comfyui":
                terminal_set_image_backend_simple("comfyui")
                continue


            if lower == "/comfy-status":
                terminal_comfy_status()
                continue

            if lower == "/comfy-start":
                terminal_comfy_start()
                continue

            if lower == "/comfy-stop":
                terminal_comfy_stop()
                continue

            if lower.startswith("/comfy-image "):
                terminal_comfy_image(command.replace("/comfy-image ", "", 1).strip())
                continue


            if lower.startswith("/upscale "):
                terminal_upscale_image(command.replace("/upscale ", "", 1).strip())
                continue


            if lower == "/image-backend":
                terminal_image_status()
                continue

            if lower == "/image-enhance":
                terminal_image_status()
                continue


            if lower.startswith("/image "):
                terminal_create_image(command.replace("/image ", "", 1).strip())
                continue

            if lower.startswith("/gif "):
                terminal_create_gif(command.replace("/gif ", "", 1).strip())
                continue

            if lower == "/images":
                terminal_list_images()
                continue


            if lower == "/mode":
                show_permission_mode()
                continue

            if lower == "/safe":
                set_permission_mode_terminal("safe")
                continue

            if lower == "/power":
                set_permission_mode_terminal("power")
                continue

            if lower == "/agentic":
                set_permission_mode_terminal("agentic")
                continue

            if lower.startswith("/idea "):
                terminal_idea_chat(command.replace("/idea ", "", 1).strip(), mode="idea")
                continue

            if lower.startswith("/brainstorm "):
                terminal_idea_chat(command.replace("/brainstorm ", "", 1).strip(), mode="brainstorm")
                continue

            if lower.startswith("/critic "):
                terminal_idea_chat(command.replace("/critic ", "", 1).strip(), mode="critic")
                continue

            if lower.startswith("/builder "):
                terminal_idea_chat(command.replace("/builder ", "", 1).strip(), mode="builder")
                continue

            if lower.startswith("/simple "):
                terminal_idea_chat(command.replace("/simple ", "", 1).strip(), mode="simple")
                continue

            if lower.startswith("/idea-model "):
                terminal_set_idea_model(command.replace("/idea-model ", "", 1).strip())
                continue



            if lower in ["/exit", "exit", "quit"]:
                break

            if lower == "/help":
                help_menu()
                continue

            if lower == "/doctor":
                doctor()
                continue

            if lower == "/models":
                models()
                continue

            if lower == "/agents":
                show_agents()
                continue

            if lower == "/skills":
                show_skills()
                continue

            if lower == "/products":
                terminal_products()
                continue

            if lower == "/templates":
                terminal_templates()
                continue

            if lower.startswith("/product-template "):
                terminal_product_template(command.replace("/product-template ", "", 1).strip())
                continue

            if lower.startswith("/search "):
                terminal_search_files(command.replace("/search ", "", 1).strip())
                continue

            if lower.startswith("/snapshot"):
                terminal_snapshot(command.replace("/snapshot", "", 1).strip())
                continue

            if lower.startswith("/changed"):
                terminal_changed(command.replace("/changed", "", 1).strip())
                continue

            if lower.startswith("/diff "):
                terminal_diff(command.replace("/diff ", "", 1).strip())
                continue

            if lower.startswith("/product-create "):
                terminal_product_create(command.replace("/product-create ", "", 1).strip())
                continue

            if lower.startswith("/product-start "):
                terminal_product_start(command.replace("/product-start ", "", 1).strip())
                continue

            if lower.startswith("/product-stop "):
                terminal_product_stop(command.replace("/product-stop ", "", 1).strip())
                continue

            if lower.startswith("/product-logs "):
                terminal_product_logs(command.replace("/product-logs ", "", 1).strip())
                continue

            if lower == "/rag":
                show_rag_status()
                continue

            if lower == "/memory":
                show_memory()
                continue

            if lower.startswith("/section "):
                terminal_section(command.replace("/section ", "", 1).strip())
                continue

            if lower == "/sections":
                terminal_sections()
                continue

            if lower.startswith("/history-search "):
                terminal_history_search(command.replace("/history-search ", "", 1).strip())
                continue

            if lower.startswith("/history"):
                terminal_history(command.replace("/history", "", 1).strip())
                continue

            if lower.startswith("/export-history"):
                terminal_export_history(command.replace("/export-history", "", 1).strip())
                continue

            if lower == "/mode":
                show_permission_mode()
                continue

            if lower == "/safe":
                set_permission_mode_terminal("safe")
                continue

            if lower == "/power":
                set_permission_mode_terminal("power")
                continue

            if lower == "/agentic":
                set_permission_mode_terminal("agentic")
                continue

            if lower.startswith("/run "):
                run_shell_terminal(command.replace("/run ", "", 1).strip())
                continue

            if lower.startswith("/web "):
                web_search_terminal(command.replace("/web ", "", 1).strip())
                continue

            if lower.startswith("/fetch "):
                fetch_url_terminal(command.replace("/fetch ", "", 1).strip())
                continue

            if lower.startswith("/download "):
                download_url_terminal(command.replace("/download ", "", 1).strip())
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

            if lower == "/rag-index":
                run_rag_index()
                continue

            if lower.startswith("/rag-search "):
                run_rag_search(command.replace("/rag-search ", "", 1).strip())
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

            if lower.startswith("/team "):
                run_team_task(command.replace("/team ", "", 1).strip())
                continue

            if lower == "/tiny":
                set_model_profile("tiny")
                continue

            if lower == "/fast":
                set_model_profile("fast")
                continue

            if lower == "/coder":
                set_model_profile("coder")
                continue

            if lower == "/smart":
                set_model_profile("smart")
                continue

            if lower == "/heavy":
                set_model_profile("heavy")
                continue

            if lower == "/max":
                set_model_profile("max")
                continue

            if lower in ["/dashboard", "launch dashboard", "open dashboard", "start dashboard"]:
                launch_dashboard()
                continue

            if lower == "/tree":
                workspace_tree()
                continue

            if lower.startswith("/bg "):
                bg_job(command.replace("/bg ", "", 1).strip())
                continue

            if lower == "/jobs":
                jobs()
                continue

            if lower.startswith("/job "):
                show_job(command.replace("/job ", "", 1).strip())
                continue

            if lower.startswith("/trace-job "):
                show_trace(command.replace("/trace-job ", "", 1).strip())
                continue

            if lower.startswith("/"):
                say_panel(f"Unknown command: {command}\nType /help.", title="Unknown Command", style="yellow")
                continue

            result = run_titan_prompt(command)
            say_panel(result, title="Titan", style="magenta")

        except Exception as e:
            say_panel(f"Titan stayed alive.\n\nError: {e!r}", title="Command Error", style="red")


if __name__ == "__main__":
    repl()
