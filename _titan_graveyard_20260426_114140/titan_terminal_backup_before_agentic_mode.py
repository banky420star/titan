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
from prompt_toolkit.key_binding import KeyBindings

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG_PATH = BASE / "config.json"
WORKSPACE = BASE / "workspace"
LOG_FILE = BASE / "logs" / "agent_v3.log"

sys.path.insert(0, str(BASE))
import agent_v3

console = Console()

TRACE_MODE = False

def load_config():
    return json.loads(CONFIG_PATH.read_text())

def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, indent=2))



def core_line(frame=0):
    cores = ["◉", "◎", "⬢", "⬡"]
    bars = ["██░░░░░░", "████░░░░", "██████░░", "████░░░░"]
    states = ["cold", "warming", "hot", "stable"]
    i = frame % 4
    return cores[i], bars[i], states[i]


def startup_animation():
    phrase = "THE TITS"
    subtitle = "Terminal Intelligence Task System"

    boot = [
        "mounting AI_DRIVE",
        "loading qwen3:8b",
        "arming qwen2.5-coder fallback",
        "locking workspace",
        "binding tools",
        "ready"
    ]

    with Live(console=console, refresh_per_second=12, screen=True) as live:
        done = []

        for i, line in enumerate(boot):
            done.append(line)
            core, bar, state = core_line(i)

            body = (
                f"[bold red]DEMON-CORE MAINFRAME[/bold red]\n"
                f"[bold yellow]{phrase}[/bold yellow]\n"
                f"[dim]{subtitle}[/dim]\n\n"
                f"[magenta]core[/magenta] {core}  [red]{bar}[/red]  {state}\n\n"
                + "\n".join(f"[green]✓[/green] {x}" for x in done)
            )

            live.update(Panel(body, title="Titan Boot", border_style="red"))
            time.sleep(0.14)

        for i in range(6):
            core, bar, state = core_line(i)
            body = (
                f"[bold red]DEMON-CORE MAINFRAME[/bold red]\n"
                f"[bold yellow]{phrase}[/bold yellow]\n"
                f"[dim]{subtitle}[/dim]\n\n"
                f"[magenta]core[/magenta] {core}  [red]{bar}[/red]  stable\n"
                f"[cyan]model[/cyan] qwen3:8b\n"
                f"[cyan]workspace[/cyan] locked\n\n"
                f"[green]ready[/green]"
            )

            live.update(Panel(body, title="Titan Ready", border_style="green"))
            time.sleep(0.08)

def banner():
    config = load_config()
    model = config.get("model", "unknown")
    fallback = config.get("fallback_model", "unknown")
    mode = config.get("agent_mode", "terminal")
    cloud = config.get("cloud_models_allowed", False)

    text = f"""[bold red]DEMON-CORE INTERMINAL[/bold red] [dim]terminal autonomous agent[/dim]

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
        ("/logs",
    "/trace", "Show logs"),
        ("/model",
    "/models", "Show model config"),
        ("/model qwen3:8b", "Set model"),
        ("/mode safe", "Safe mode"),
        ("/mode auto", "Autonomous mode"),
        ("/rag-index", "Index RAG docs"),
        ("/rag-search <query>", "Search RAG"),
        ("/web <query>", "Web search"),
        ("/run <command>", "Run safe workspace command"),
        ("/clear", "Clear screen"),
        ("/products",
    "/product ",
    "/skill-new ",
    "/install ",
    "/download ",
    "/exit", "Quit"),
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

    if TRACE_MODE:
        console.print(Panel(
            "[bold cyan]Visible trace enabled[/bold cyan]\n"
            "- I will show task framing before execution.\n"
            "- Tool calls are printed by agent_v3 during execution.\n"
            "- Subagent outputs are shown when /team is used.\n"
            "- Hidden private chain-of-thought is not displayed.",
            title="Trace",
            border_style="yellow"
        ))

    with console.status("[bold cyan]Titan thinking...[/bold cyan]", spinner="dots"):
        result = agent_v3.run_agent(task, max_steps=load_config().get("max_agent_steps", 20))

    if TRACE_MODE:
        console.print(Panel(
            str(result),
            title="Trace Result Summary",
            border_style="yellow"
        ))

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
    "/trace",
    "/status",
    "/doctor",
    "/model",
    "/models",
    "/model qwen3:8b",
    "/model qwen2.5-coder:7b",
    "/mode auto",
    "/mode safe",
    "/rag-index",
    "/rag-search ",
    "/web ",
    "/run ",
    "/read "
    "/find "
    "/clear",
    "/products",
    "/product ",
    "/skill-new ",
    "/install ",
    "/download ",
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


def show_trace_state():
    if TRACE_MODE:
        console.print(Panel(
            "[bold yellow]TRACE PANEL OPEN[/bold yellow]\n\n"
            "Visible trace is enabled.\n"
            "- Task framing will be shown.\n"
            "- Tool calls/results printed by agent_v3 will remain visible.\n"
            "- /team will show Planner Voss, Milton, Tripwire, and Blackglass outputs.\n"
            "- Hidden private chain-of-thought is not displayed.",
            title="Trace",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[bold dim]TRACE PANEL CLOSED[/bold dim]\n\n"
            "Visible trace is now hidden. Titan will still show final results and normal command output.",
            title="Trace",
            border_style="dim"
        ))


def toggle_trace():
    global TRACE_MODE
    TRACE_MODE = not TRACE_MODE
    show_trace_state()


def build_keybindings():
    kb = KeyBindings()

    @kb.add("c-e")
    def _(event):
        toggle_trace()

    return kb


def get_terminal_input(session):
    return session.prompt(
        [("class:prompt", "titan ▸ ")],
        completer=COMMAND_COMPLETER,
        complete_while_typing=True,
        auto_suggest=AutoSuggestFromHistory(),
        key_bindings=build_keybindings()
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
        result = agent_v3.run_command("python3 -m py_compile ../agent_v3.py")
        ok("agent_v3 syntax", "exit_code: 0" in result, result[:300])
    except Exception as e:
        ok("agent_v3 syntax", False, str(e))

    try:
        result = agent_v3.run_command("python3 -m py_compile ../titan_terminal.py")
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
        result = agent_v3.run_command("python3 -m py_compile ../agent_v3.py")
        ok("agent_v3 syntax", "exit_code: 0" in result, result[:300])
    except Exception as e:
        ok("agent_v3 syntax", False, str(e))

    try:
        result = agent_v3.run_command("python3 -m py_compile ../titan_terminal.py")
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


def find_computer_files(query):
    if not hasattr(agent_v3, "computer_search"):
        console.print("[red]agent_v3.computer_search is missing. Patch agent_v3.py first.[/red]")
        return

    result = agent_v3.computer_search(
        query=query,
        name_pattern="*",
        max_results=80
    )
    console.print(Panel(result, title=f"Computer Search: {query}", border_style="cyan"))


def read_computer_file(path_value):
    if not hasattr(agent_v3, "computer_read"):
        console.print("[red]agent_v3.computer_read is missing. Patch agent_v3.py first.[/red]")
        return

    result = agent_v3.computer_read(
        path_value,
        max_chars=20000
    )
    console.print(Panel(result, title=f"Read File: {path_value}", border_style="green"))


def where_file(query):
    if not hasattr(agent_v3, "computer_search"):
        console.print("[red]agent_v3.computer_search is missing.[/red]")
        return

    result = agent_v3.computer_search(
        query=query,
        name_pattern=query,
        max_results=30
    )
    console.print(Panel(result, title=f"Where: {query}", border_style="cyan"))


def team_task(task):
    console.print(Panel(task, title="Team Task", border_style="magenta"))

    if TRACE_MODE:
        console.print(Panel(
            "Subagent trace is active.\n\n"
            "Flow:\n"
            "1. Planner Voss creates the execution plan\n"
            "2. Milton proposes implementation\n"
            "3. Tripwire defines verification\n"
            "4. Blackglass checks risk and gaps\n"
            "5. Titan executes the combined task",
            title="Trace: Team Flow",
            border_style="yellow"
        ))

    planner_prompt = "You are Planner Voss, the strategic planner. Plan this task in clear executable steps. Task: " + task
    coder_prompt = "You are Milton, the implementation engineer. Identify files/tools needed and the implementation approach. Task: " + task
    tester_prompt = "You are Tripwire, the verification specialist. Define verification commands and checks. Task: " + task
    reviewer_prompt = "You are Blackglass, the skeptical reviewer. Identify risks, missing details, and the safer execution path. Task: " + task

    with console.status("[bold cyan]Planner Voss thinking...[/bold cyan]", spinner="dots"):
        plan = agent_v3.call_subagent("planner", planner_prompt)
    console.print(Panel(plan, title="Planner Voss · Planner", border_style="cyan"))

    with console.status("[bold green]Milton building...[/bold green]", spinner="dots"):
        code = agent_v3.call_subagent("coder", coder_prompt)
    console.print(Panel(code, title="Milton · Coder", border_style="green"))

    with console.status("[bold yellow]Tripwire testing...[/bold yellow]", spinner="dots"):
        test = agent_v3.call_subagent("tester", tester_prompt)
    console.print(Panel(test, title="Tripwire · Tester", border_style="yellow"))

    with console.status("[bold magenta]Blackglass reviewing...[/bold magenta]", spinner="dots"):
        review = agent_v3.call_subagent("reviewer", reviewer_prompt)
    console.print(Panel(review, title="Blackglass · Reviewer", border_style="magenta"))

    final_task = (
        "Use this subagent guidance to execute the original task if safe and possible.\\n\\n"
        "Original task:\\n" + task + "\\n\\n"
        "Planner:\\n" + str(plan) + "\\n\\n"
        "Coder:\\n" + str(code) + "\\n\\n"
        "Tester:\\n" + str(test) + "\\n\\n"
        "Reviewer:\\n" + str(review)
    )

    run_agent_task(final_task)



def show_role_models():
    config = load_config()
    role_models = config.get("role_models", {})

    table = Table(title="Titan Role Models", border_style="cyan")
    table.add_column("Role", style="bold green")
    table.add_column("Subagent", style="white")
    table.add_column("Model", style="cyan")

    rows = [
        ("planner", "Planner Voss"),
        ("coder", "Milton"),
        ("tester", "Tripwire"),
        ("reviewer", "Blackglass")
    ]

    for role, subagent in rows:
        table.add_row(role, subagent, role_models.get(role, "default"))

    console.print(table)


def show_products():
    try:
        products_dir = BASE / "products"
        products_dir.mkdir(parents=True, exist_ok=True)

        items = []
        for p in sorted(products_dir.iterdir()):
            if p.is_dir():
                items.append(str(p))

        result = "\n".join(items) if items else "No products found."
        console.print(Panel(result, title="Products", border_style="cyan"))

    except Exception as e:
        console.print(Panel(
            "Products command failed but Titan stayed alive.\n\n" + repr(e),
            title="Products Error",
            border_style="red"
        ))


def terminal_create_product(raw):
    try:
        parts = raw.strip().split(" ", 1)
        name = parts[0].strip() if parts and parts[0].strip() else "new-product"
        kind = parts[1].strip() if len(parts) > 1 else "python_cli"

        if hasattr(agent_v3, "create_product"):
            result = agent_v3.create_product(
                name=name,
                kind=kind,
                description="Created from Titan Terminal."
            )
        else:
            result = "agent_v3.create_product() is missing."

        console.print(Panel(str(result), title="Create Product", border_style="green"))

    except Exception as e:
        console.print(Panel(
            "Create product failed but Titan stayed alive.\n\n" + repr(e),
            title="Create Product Error",
            border_style="red"
        ))


def terminal_create_skill(raw):
    name = raw.strip()
    if not name:
        console.print("[red]Usage:[/red] /skill-new <name>")
        return

    result = agent_v3.create_skill_pack(
        name=name,
        description="Created from Titan Terminal.",
        dependencies=[]
    )
    console.print(Panel(result, title="Create Skill", border_style="magenta"))


def terminal_install(package):
    result = agent_v3.install_dependency(package)
    console.print(Panel(result, title=f"Install Dependency: {package}", border_style="yellow"))


def terminal_download(url):
    result = agent_v3.builder_download_url(url)
    console.print(Panel(result, title=f"Download: {url}", border_style="cyan"))


def safe_execute_command(label, fn, *args):
    try:
        return fn(*args)
    except Exception as e:
        console.print(Panel(
            "Command failed but Titan stayed alive.\n\n"
            f"Command: {label}\n"
            f"Error: {repr(e)}",
            title="Command Error",
            border_style="red"
        ))
        return None

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

        command = user_input.strip()

        if command in ["/products",
    "/product ",
    "/skill-new ",
    "/install ",
    "/download ",
    "/exit", "exit", "quit", "/bye"]:
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

        if command == "/trace":
            toggle_trace()
            continue

        if command == "/status":
            status_check()
            continue

        if command == "/doctor":
            doctor_check()
            continue

        if command == "/models":
            show_role_models()
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

        if command == "/products":
            try:
                show_products()
            except Exception as e:
                console.print(Panel("Command failed but Titan stayed alive.\n\n" + repr(e), title="Command Error", border_style="red"))
            continue

        if command.startswith("/product "):
            terminal_create_product(command.replace("/product ", "", 1).strip())
            continue

        if command.startswith("/skill-new "):
            terminal_create_skill(command.replace("/skill-new ", "", 1).strip())
            continue

        if command.startswith("/install "):
            terminal_install(command.replace("/install ", "", 1).strip())
            continue

        if command.startswith("/download "):
            terminal_download(command.replace("/download ", "", 1).strip())
            continue

        if command.startswith("/team "):
            team_task(command.replace("/team ", "", 1).strip())
            continue

        if command.startswith("/where "):
            where_file(command.replace("/where ",
    "/team ", "", 1).strip())
            continue

        if command.startswith("/find "):
            find_computer_files(command.replace("/find ",
    "/where ",
    "/team ", "", 1).strip())
            continue

        if command.startswith("/read "):
            read_computer_file(command.replace("/read ", "", 1).strip())
            continue

        if command.startswith("/run "):
            run_safe_command(command.replace("/run ", "", 1).strip())
            continue

        if command.startswith("/"):
            console.print(f"[red]Unknown command:[/red] {command}")
            console.print("[dim]Type /help to see available commands.[/dim]")
            continue

        run_agent_task(command)


if __name__ == "__main__":
    repl()
