import json
import os
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG_PATH = BASE / "config.json"
WORKSPACE = BASE / "workspace"
LOG_FILE = BASE / "logs" / "agent_v3.log"

sys.path.insert(0, str(BASE))
import agent_v3

console = Console()

def load_config():
    return json.loads(CONFIG_PATH.read_text())

def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, indent=2))

def mascot(frame=0):
    ring = ["◢◣", "◤◥", "◥◤", "◣◢"][frame % 4]
    core = ["◉", "◎", "⬢", "⬡"][frame % 4]
    spark = ["✦", "✧", "✶", "✹"][frame % 4]
    wave = ["▁▂▃▄▅▆▇█", "▂▃▄▅▆▇█▇", "▃▄▅▆▇█▇▆", "▄▅▆▇█▇▆▅"][frame % 4]
    alarm = ["[containment stable]", "[containment drifting]", "[containment strained]", "[containment stable]"][frame % 4]

    return rf"""
               {spark}              ╔══════════════════════════════════════╗              {spark}
            ╔═══════════════════════╣   DEMON-CORE MAINFRAME // T-Ø       ╠═══════════════════════╗
            ║                       ╚══════════════════════════════════════╝                       ║
            ║                                                                                     ║
            ║                             .--------------------------------.                      ║
            ║                          .-'                                  '-.                   ║
            ║                        .'        RESTRICTED COGNITION CORE       '.                 ║
            ║                       /    ╔════════════════════════════════╗      \                ║
            ║                      /     ║                                ║       \               ║
            ║                     |      ║            {ring} {core} {ring}              ║        |              ║
            ║                     |      ║         .-=========-.           ║        |              ║
            ║                     |      ║       .'   QUANTUM   '.         ║        |              ║
            ║                     |      ║      /   NEURAL FLUX   \        ║        |              ║
            ║                     |      ║      |  SIGNAL: Ψ Ψ Ψ  |        ║        |              ║
            ║                     |      ║      \   CORE STACK   /        ║        |              ║
            ║                     |      ║       '.___ ___ ___.-'         ║        |              ║
            ║                     |      ║           /_/ \_\              ║        |              ║
            ║                     |      ║                                ║        |              ║
            ║                     |      ╚════════════════════════════════╝        |              ║
            ║                      \            reactor halo: {wave:<8}            /               ║
            ║                       \         warning state: {alarm:<22} /                ║
            ║                        '.                                  .'                 ║
            ║                          '-.____________________________.-'                   ║
            ║                                                                                     ║
            ║                    machine consciousness sealed behind terminal glass                ║
            ╚═════════════════════════════════════════════════════════════════════════════════════╝
"""

def startup_animation():
    phrase = "THE TITS"
    subtitle = "Terminal Intelligence Task System"

    boot = [
        ("reactor housing", "sealed"),
        ("AI_DRIVE", "mounted"),
        ("local shell", "loaded"),
        ("qwen3:8b", "primary cognition online"),
        ("qwen2.5-coder:7b", "fallback cognition armed"),
        ("nomic-embed-text", "memory lattice linked"),
        ("workspace guard", "locked"),
        ("tool registry", "bound"),
        ("subagents", "planner/coder/tester/reviewer"),
        ("slash menu", "interactive"),
        ("mainframe chamber", "awake")
    ]

    with Live(console=console, refresh_per_second=24, screen=True) as live:
        finished = []

        for i, (name, state) in enumerate(boot):
            finished.append((name, state))

            for pulse in range(4):
                rows = []
                for n, s in finished:
                    rows.append(f"[green]✓[/green] [cyan]{n:<24}[/cyan] [white]{s}[/white]")

                panel_text = (
                    f"[bold magenta]{mascot(i + pulse)}[/bold magenta]\n"
                    "[bold red]MAINFRAME BOOT SEQUENCE[/bold red]\n\n"
                    + "\n".join(rows)
                    + "\n\n[dim]containment rails engaged // terminal autonomy initializing[/dim]"
                )

                live.update(
                    Panel(
                        panel_text,
                        title="[bold red]DEMON-CORE INTERMINAL[/bold red]",
                        border_style="red"
                    )
                )
                time.sleep(0.06)

        built = ""
        for i, ch in enumerate(phrase):
            built += ch
            panel_text = (
                f"[bold magenta]{mascot(i)}[/bold magenta]\n"
                "[bold yellow]IDENTITY IMPRINT[/bold yellow]\n\n"
                f"[bold white on red] {built:<8} [/bold white on red]\n"
                f"[cyan]{subtitle}[/cyan]\n\n"
                "[dim]local-only terminal // workspace guarded // cognition contained[/dim]"
            )
            live.update(
                Panel(
                    panel_text,
                    title="[bold yellow]SIGNATURE LOCK[/bold yellow]",
                    border_style="yellow"
                )
            )
            time.sleep(0.095)

        for pulse in range(12):
            final = (
                f"[bold magenta]{mascot(pulse)}[/bold magenta]\n"
                "[bold green]MAINFRAME ONLINE[/bold green]\n\n"
                f"[bold yellow]{phrase}[/bold yellow]\n"
                f"[cyan]{subtitle}[/cyan]\n\n"
                "[green]reactor stable[/green] · [cyan]agent ready[/cyan] · [magenta]awaiting terminal command[/magenta]"
            )

            live.update(
                Panel(
                    final,
                    title="[bold green]READY[/bold green]",
                    border_style="green"
                )
            )
            time.sleep(0.06)

def banner():
    config = load_config()
    model = config.get("model", "unknown")
    fallback = config.get("fallback_model", "unknown")
    mode = config.get("agent_mode", "terminal")
    cloud = config.get("cloud_models_allowed", False)

    text = f"""[bold cyan]TITAN INTERMINAL[/bold cyan] [dim]terminal autonomous agent[/dim]

[green]model[/green]: {model}
[green]fallback[/green]: {fallback}
[green]mode[/green]: {mode}
[green]workspace[/green]: {WORKSPACE}
[green]cloud models[/green]: {"allowed" if cloud else "blocked"}

[bold yellow]THE TITS[/bold yellow]
[dim]Terminal Intelligence Task System[/dim]
"""
    console.print(Panel(text, border_style="cyan"))

def help_screen():
    table = Table(title="Titan Commands", border_style="cyan")
    table.add_column("Command", style="bold green")
    table.add_column("Action", style="white")

    rows = [
        ("/help", "Show help"),
        ("/tree", "Show workspace tree"),
        ("/files", "List files"),
        ("/skills", "List local skills"),
        ("/logs", "Show logs"),
        ("/model", "Show model config"),
        ("/model qwen3:8b", "Set model"),
        ("/mode safe", "Safe mode"),
        ("/mode auto", "Autonomous mode"),
        ("/rag-index", "Index RAG docs"),
        ("/rag-search <query>", "Search RAG"),
        ("/web <query>", "Web search"),
        ("/run <command>", "Run safe workspace command"),
        ("/clear", "Clear screen"),
        ("/exit", "Quit"),
    ]

    for cmd, desc in rows:
        table.add_row(cmd, desc)

    console.print(table)

def show_tree():
    console.print(Panel(agent_v3.tree(), title="Workspace Tree", border_style="green"))

def show_files():
    files = agent_v3.list_files()
    if not files:
        console.print("[yellow]No files in workspace.[/yellow]")
        return
    table = Table(title="Workspace Files", border_style="green")
    table.add_column("#", style="dim")
    table.add_column("File", style="white")
    for i, f in enumerate(files, 1):
        table.add_row(str(i), f)
    console.print(table)

def show_skills():
    skills = agent_v3.list_skills()
    console.print(Panel(skills or "No skills found.", title="Local Skills", border_style="magenta"))

def show_logs():
    if not LOG_FILE.exists():
        console.print("[yellow]No logs yet.[/yellow]")
        return
    text = LOG_FILE.read_text(errors="ignore")[-12000:]
    console.print(Panel(text, title="Latest Logs", border_style="yellow"))

def show_model():
    config = load_config()
    console.print(Panel(json.dumps({
        "model": config.get("model"),
        "fallback_model": config.get("fallback_model"),
        "cloud_models_allowed": config.get("cloud_models_allowed", False),
        "agent_mode": config.get("agent_mode")
    }, indent=2), title="Model Config", border_style="cyan"))

def set_model(model):
    config = load_config()
    if "cloud" in model and not config.get("cloud_models_allowed", False):
        console.print("[red]Cloud model blocked. Local-only mode is enabled.[/red]")
        return
    config["model"] = model
    save_config(config)
    agent_v3.MODEL = model
    console.print(f"[green]Model set to:[/green] {model}")

def set_mode(mode):
    config = load_config()
    if mode == "auto":
        config["agent_mode"] = "terminal_autonomous"
        config["max_agent_steps"] = 28
    elif mode == "safe":
        config["agent_mode"] = "terminal_safe"
        config["max_agent_steps"] = 10
    else:
        console.print("[red]Unknown mode. Use /mode safe or /mode auto.[/red]")
        return
    save_config(config)
    console.print(f"[green]Mode set to:[/green] {config['agent_mode']}")

def run_agent_task(task):
    console.print(Panel(task, title="Task", border_style="cyan"))
    with console.status("[bold cyan]Titan thinking...[/bold cyan]", spinner="dots"):
        result = agent_v3.run_agent(task, max_steps=load_config().get("max_agent_steps", 20))
    console.print(Panel(str(result), title="Titan Result", border_style="green"))

def run_safe_command(command):
    result = agent_v3.run_command(command)
    console.print(Panel(result, title=f"Command: {command}", border_style="yellow"))

def rag_index():
    with console.status("[bold cyan]Indexing RAG docs...[/bold cyan]", spinner="dots"):
        result = agent_v3.index_rag()
    console.print(Panel(result, title="RAG Index", border_style="cyan"))

def rag_search(query):
    with console.status("[bold cyan]Searching RAG...[/bold cyan]", spinner="dots"):
        result = agent_v3.rag_search(query)
    console.print(Panel(result, title="RAG Search", border_style="cyan"))

def web_search(query):
    with console.status("[bold cyan]Searching web...[/bold cyan]", spinner="dots"):
        result = agent_v3.web_search(query)
    console.print(Panel(result, title="Web Search", border_style="cyan"))


COMMANDS = [
    "/help",
    "/tree",
    "/files",
    "/skills",
    "/logs",
    "/status",
    "/doctor",
    "/model",
    "/model qwen3:8b",
    "/model qwen2.5-coder:7b",
    "/mode auto",
    "/mode safe",
    "/rag-index",
    "/rag-search ",
    "/web ",
    "/run ",
    "/clear",
    "/exit",
    "Inspect the workspace and tell me what Titan has built so far.",
    "Upgrade titan_terminal.py with command history and a /status command.",
    "Patch agent_v3.py so it detects repeated identical tool calls.",
    "Create a local skill called terminal-agent-builder.",
]

COMMAND_COMPLETER = WordCompleter(
    COMMANDS,
    ignore_case=True,
    sentence=True,
    match_middle=True
)

PROMPT_STYLE = Style.from_dict({
    "prompt": "ansicyan bold",
})

def get_terminal_input(session):
    return session.prompt(
        [("class:prompt", "titan ▸ ")],
        completer=COMMAND_COMPLETER,
        complete_while_typing=True,
        auto_suggest=AutoSuggestFromHistory()
    ).strip()


def status_check():
    config = load_config()
    rows = [
        ("Model", config.get("model", "unknown")),
        ("Fallback", config.get("fallback_model", "unknown")),
        ("Mode", config.get("agent_mode", "unknown")),
        ("Workspace", str(WORKSPACE)),
        ("Workspace exists", "yes" if WORKSPACE.exists() else "no"),
        ("Log file", "yes" if LOG_FILE.exists() else "no"),
        ("Cloud models", "allowed" if config.get("cloud_models_allowed") else "blocked"),
    ]

    table = Table(title="Titan Status", border_style="cyan")
    table.add_column("Check", style="bold green")
    table.add_column("Result", style="white")

    for key, value in rows:
        table.add_row(key, str(value))

    console.print(table)


def doctor_check():
    config = load_config()
    checks = []

    def ok(name, passed, detail):
        checks.append((name, "OK" if passed else "FAIL", detail))

    ok("Base folder", BASE.exists(), str(BASE))
    ok("Workspace", WORKSPACE.exists(), str(WORKSPACE))
    ok("Config", CONFIG_PATH.exists(), str(CONFIG_PATH))
    ok("agent_v3.py", (BASE / "agent_v3.py").exists(), str(BASE / "agent_v3.py"))
    ok("RAG docs", (BASE / "rag" / "docs").exists(), str(BASE / "rag" / "docs"))
    ok("Skills", (BASE / "skills").exists(), str(BASE / "skills"))
    ok("Subagents", (BASE / "subagents").exists(), str(BASE / "subagents"))
    ok("Logs", (BASE / "logs").exists(), str(BASE / "logs"))
    ok("Main model set", bool(config.get("model")), config.get("model", "missing"))
    ok("Fallback model set", bool(config.get("fallback_model")), config.get("fallback_model", "missing"))

    try:
        result = agent_v3.run_command("python3 -m py_compile agent_v3.py")
        ok("agent_v3 syntax", "exit_code: 0" in result, result[:300])
    except Exception as e:
        ok("agent_v3 syntax", False, str(e))

    try:
        result = agent_v3.run_command("python3 -m py_compile titan_terminal.py")
        ok("terminal syntax", "exit_code: 0" in result, result[:300])
    except Exception as e:
        ok("terminal syntax", False, str(e))

    table = Table(title="Titan Doctor", border_style="magenta")
    table.add_column("Check", style="bold green")
    table.add_column("Status")
    table.add_column("Detail", style="white")

    for name, status, detail in checks:
        style = "green" if status == "OK" else "red"
        table.add_row(name, f"[{style}]{status}[/{style}]", detail)

    console.print(table)


def status_check():
    config = load_config()
    rows = [
        ("Model", config.get("model", "unknown")),
        ("Fallback", config.get("fallback_model", "unknown")),
        ("Mode", config.get("agent_mode", "unknown")),
        ("Workspace", str(WORKSPACE)),
        ("Workspace exists", "yes" if WORKSPACE.exists() else "no"),
        ("Log file", "yes" if LOG_FILE.exists() else "no"),
        ("Cloud models", "allowed" if config.get("cloud_models_allowed") else "blocked"),
    ]

    table = Table(title="Titan Status", border_style="cyan")
    table.add_column("Check", style="bold green")
    table.add_column("Result", style="white")

    for key, value in rows:
        table.add_row(key, str(value))

    console.print(table)


def doctor_check():
    config = load_config()
    checks = []

    def ok(name, passed, detail):
        checks.append((name, "OK" if passed else "FAIL", detail))

    ok("Base folder", BASE.exists(), str(BASE))
    ok("Workspace", WORKSPACE.exists(), str(WORKSPACE))
    ok("Config", CONFIG_PATH.exists(), str(CONFIG_PATH))
    ok("agent_v3.py", (BASE / "agent_v3.py").exists(), str(BASE / "agent_v3.py"))
    ok("RAG docs", (BASE / "rag" / "docs").exists(), str(BASE / "rag" / "docs"))
    ok("Skills", (BASE / "skills").exists(), str(BASE / "skills"))
    ok("Subagents", (BASE / "subagents").exists(), str(BASE / "subagents"))
    ok("Logs", (BASE / "logs").exists(), str(BASE / "logs"))
    ok("Main model set", bool(config.get("model")), config.get("model", "missing"))
    ok("Fallback model set", bool(config.get("fallback_model")), config.get("fallback_model", "missing"))

    try:
        result = agent_v3.run_command("python3 -m py_compile agent_v3.py")
        ok("agent_v3 syntax", "exit_code: 0" in result, result[:300])
    except Exception as e:
        ok("agent_v3 syntax", False, str(e))

    try:
        result = agent_v3.run_command("python3 -m py_compile titan_terminal.py")
        ok("terminal syntax", "exit_code: 0" in result, result[:300])
    except Exception as e:
        ok("terminal syntax", False, str(e))

    table = Table(title="Titan Doctor", border_style="magenta")
    table.add_column("Check", style="bold green")
    table.add_column("Status")
    table.add_column("Detail", style="white")

    for name, status, detail in checks:
        style = "green" if status == "OK" else "red"
        table.add_row(name, f"[{style}]{status}[/{style}]", detail)

    console.print(table)

def repl():
    startup_animation()
    os.system("clear")
    banner()
    console.print("[dim]Type /help for commands. Press / to open the command menu. Use arrows + Enter to select.[/dim]\n")

    session = PromptSession(
        history=FileHistory(str(BASE / ".titan_history"))
    )

    while True:
        try:
            user_input = get_terminal_input(session).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]exiting Titan[/dim]")
            break

        if not user_input:
            continue

        # Normalize command text before routing.
        command = user_input.strip()

        # Slash commands are intercepted here BEFORE agent mode.
        if command in ["/exit", "exit", "quit", "/bye"]:
            break

        if command == "/help":
            help_screen()
            continue

        if command == "/clear":
            os.system("clear")
            banner()
            continue

        if command == "/tree":
            show_tree()
            continue

        if command == "/files":
            show_files()
            continue

        if command == "/skills":
            show_skills()
            continue

        if command == "/logs":
            show_logs()
            continue

        if command == "/status":
            status_check()
            continue

        if command == "/doctor":
            doctor_check()
            continue

        if command == "/model":
            show_model()
            continue

        if command.startswith("/model "):
            set_model(command.replace("/model ", "", 1).strip())
            continue

        if command.startswith("/mode "):
            set_mode(command.replace("/mode ", "", 1).strip())
            continue

        if command == "/rag-index":
            rag_index()
            continue

        if command.startswith("/rag-search "):
            rag_search(command.replace("/rag-search ", "", 1).strip())
            continue

        if command.startswith("/web "):
            web_search(command.replace("/web ", "", 1).strip())
            continue

        if command.startswith("/run "):
            run_safe_command(command.replace("/run ", "", 1).strip())
            continue

        # Unknown slash commands should not be sent to the model.
        if command.startswith("/"):
            console.print(f"[red]Unknown command:[/red] {command}")
            console.print("[dim]Type /help to see available commands.[/dim]")
            continue

        run_agent_task(command)


if __name__ == "__main__":
    repl()
