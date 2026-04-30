import json
import os
import sys
import time
import webbrowser
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
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
AGENTIC_MODE = False

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
    "/trace",
    "/agentic", "Show logs"),
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
    "/dashboard",
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

def run_named_subagent(role, display_name, prompt):
    try:
        result = agent_v3.call_subagent(role, prompt)
        return display_name, result
    except Exception as e:
        return display_name, f"Subagent failed: {e}"



def compact_agent_text(value, limit=3500):
    text = str(value or "")
    text = text.replace("\x00", "")
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[TRUNCATED: output was shortened to keep Titan responsive.]"

def agentic_team_task(task):
    console.print(Panel(
        task,
        title="Agentic Task",
        border_style="red"
    ))

    if TRACE_MODE:
        console.print(Panel(
            "Agentic mode is active.\n\n"
            "Parallel team loop:\n"
            "1. Planner Voss creates execution plan\n"
            "2. Milton proposes implementation\n"
            "3. Tripwire defines verification\n"
            "4. Blackglass reviews risks\n"
            "5. Titan performs unified execution\n\n"
            "Normal workspace-safe actions do not require approval.",
            title="Trace: Agentic Team",
            border_style="yellow"
        ))

    prompts = {
        "planner": (
            "You are Planner Voss. Create a concise execution plan for this task. "
            "Prefer concrete file/tool steps and avoid vague enterprise suggestions. "
            "Task: " + task
        ),
        "coder": (
            "You are Milton. Determine the exact implementation approach, files likely needed, "
            "and code changes likely required. Prefer local Titan files and workspace-safe edits. "
            "Task: " + task
        ),
        "tester": (
            "You are Tripwire. Define concrete verification commands and failure checks for this task. "
            "Prefer python3 -m py_compile, /doctor, /models, /where, /find, and safe local checks. "
            "Task: " + task
        ),
        "reviewer": (
            "You are Blackglass. Identify risks, missing context, unsafe actions, and the safest path "
            "to complete the task without unnecessary approval gates. "
            "Task: " + task
        ),
    }

    display_names = {
        "planner": "Planner Voss",
        "coder": "Milton",
        "tester": "Tripwire",
        "reviewer": "Blackglass",
    }

    outputs = {}

    with console.status("[bold red]Agentic team running in parallel...[/bold red]", spinner="dots"):
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(run_named_subagent, role, display_names[role], prompt): role
                for role, prompt in prompts.items()
            }

            for future in as_completed(futures):
                role = futures[future]
                display_name, result = future.result()
                outputs[role] = result

    console.print(Panel(outputs.get("planner", ""), title="Planner Voss", border_style="cyan"))
    console.print(Panel(outputs.get("coder", ""), title="Milton", border_style="green"))
    console.print(Panel(outputs.get("tester", ""), title="Tripwire", border_style="yellow"))
    console.print(Panel(outputs.get("reviewer", ""), title="Blackglass", border_style="magenta"))

    unified_task = (
        "AGENTIC MODE IS ON. Complete the user's task using the team guidance below.\\n\\n"
        "Rules:\\n"
        "- Proceed without asking approval for normal workspace-safe actions.\\n"
        "- Use computer_search/computer_read if files are outside the workspace.\\n"
        "- Use web_search for current best practices or improvements if useful.\\n"
        "- Use safe commands to verify work.\\n"
        "- Do not run destructive or privileged Mac-wide actions silently.\\n"
        "- If privileged_command is required, stop and explain why.\\n"
        "- Prefer completing the job over asking for clarification when the goal is clear.\\n\\n"
        "Original task:\\n" + task + "\\n\\n"
        "Planner Voss output:\\n" + str(outputs.get("planner", "")) + "\\n\\n"
        "Milton output:\\n" + str(outputs.get("coder", "")) + "\\n\\n"
        "Tripwire output:\\n" + str(outputs.get("tester", "")) + "\\n\\n"
        "Blackglass output:\\n" + str(outputs.get("reviewer", ""))
    )

    with console.status("[bold red]Titan executing unified agentic task...[/bold red]", spinner="dots"):
        result = agent_v3.run_agent(
            unified_task,
            max_steps=load_config().get("max_agent_steps", 28)
        )

    console.print(Panel(str(result), title="Agentic Result", border_style="green"))

def run_agent_task(task):
    if AGENTIC_MODE:
        agentic_team_task(task)
        return

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
    "/agentic",
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
    "/dashboard",
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


def show_agentic_state():
    if AGENTIC_MODE:
        console.print(Panel(
            "[bold red]AGENTIC MODE ON[/bold red]\n\n"
            "Titan will now use the full team loop automatically:\n"
            "- Planner Voss plans\n"
            "- Milton builds\n"
            "- Tripwire verifies\n"
            "- Blackglass reviews\n"
            "- Web search is used for improvement ideas when useful\n"
            "- Normal workspace-safe actions proceed without approval\n\n"
            "Privileged or destructive Mac-wide actions remain guarded.",
            title="Agentic Mode",
            border_style="red"
        ))
    else:
        console.print(Panel(
            "[bold dim]AGENTIC MODE OFF[/bold dim]\n\n"
            "Normal Titan mode restored. Use /team for explicit subagent orchestration.",
            title="Agentic Mode",
            border_style="dim"
        ))


def toggle_agentic():
    global AGENTIC_MODE
    AGENTIC_MODE = not AGENTIC_MODE
    show_agentic_state()


def build_keybindings():
    kb = KeyBindings()

    @kb.add("c-e")
    def _(event):
        toggle_trace()

    @kb.add("c-a")
    def _(event):
        toggle_agentic()

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


def dashboard_is_running():
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:5050", timeout=1.5) as response:
            return response.status == 200
    except Exception:
        return False


def launch_dashboard():
    dashboard_file = BASE / "control_panel_titan_ui.py"

    if not dashboard_file.exists():
        dashboard_file = BASE / "control_panel.py"

    if not dashboard_file.exists():
        console.print(Panel(
            "Could not find control_panel_titan_ui.py or control_panel.py",
            title="Dashboard",
            border_style="red"
        ))
        return

    if dashboard_is_running():
        webbrowser.open("http://127.0.0.1:5050")
        console.print(Panel(
            "Dashboard is already running.\n\nOpened: http://127.0.0.1:5050",
            title="Dashboard",
            border_style="green"
        ))
        return

    logs_dir = BASE / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    stdout_log = logs_dir / "dashboard_stdout.log"
    stderr_log = logs_dir / "dashboard_stderr.log"

    env = os.environ.copy()
    env["FLASK_DEBUG"] = "0"

    subprocess.Popen(
        [sys.executable, str(dashboard_file)],
        cwd=str(BASE),
        env=env,
        stdout=stdout_log.open("a"),
        stderr=stderr_log.open("a"),
        start_new_session=True
    )

    time.sleep(1.2)

    webbrowser.open("http://127.0.0.1:5050")

    console.print(Panel(
        "Dashboard launch requested.\n\n"
        "URL: http://127.0.0.1:5050\n"
        f"File: {dashboard_file}\n\n"
        f"stdout log: {stdout_log}\n"
        f"stderr log: {stderr_log}",
        title="Dashboard",
        border_style="green"
    ))



# TITAN_TERMINAL_JOBS_HELPERS
def _job_base():
    from pathlib import Path
    base = Path("/Volumes/AI_DRIVE/TitanAgent")
    jobs = base / "jobs"
    for folder in [
        jobs / "running",
        jobs / "done",
        jobs / "cancelled",
        jobs / "logs",
        jobs / "traces",
    ]:
        folder.mkdir(parents=True, exist_ok=True)
    return base, jobs


def _read_json_file(path):
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def start_terminal_bg_job(task):
    import json
    import subprocess
    import sys
    from datetime import datetime

    base, jobs = _job_base()
    running = jobs / "running"
    logs = jobs / "logs"

    job_id = "term-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    job = {
        "id": job_id,
        "task": str(task),
        "status": "queued",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "max_steps": 12,
        "source": "terminal"
    }

    job_path = running / f"{job_id}.json"
    job_path.write_text(json.dumps(job, indent=2), encoding="utf-8")

    worker = base / "background_worker.py"
    if not worker.exists():
        console.print(Panel(
            "background_worker.py is missing. Create it before using /bg.",
            title="Background Job",
            border_style="red"
        ))
        return

    subprocess.Popen(
        [sys.executable, str(worker), job_id],
        cwd=str(base),
        stdout=(logs / f"{job_id}.stdout.log").open("w"),
        stderr=(logs / f"{job_id}.stderr.log").open("w"),
        start_new_session=True
    )

    console.print(Panel(
        f"Started background job: {job_id}\n\n"
        f"Task: {task}\n\n"
        f"Use:\n"
        f"/job {job_id}\n"
        f"/trace-job {job_id}\n"
        f"/jobs",
        title="Background Job",
        border_style="green"
    ))


def show_terminal_jobs():
    import json

    base, jobs = _job_base()
    running = jobs / "running"
    done = jobs / "done"

    rows = []

    for folder, label in [(running, "running"), (done, "done")]:
        for p in sorted(folder.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                rows.append(
                    f"{data.get('id', p.stem)} | {data.get('status', label)} | {data.get('created_at', '')}\n"
                    f"  {str(data.get('task', ''))[:150]}"
                )
            except Exception as e:
                rows.append(f"{p.name} | unreadable | {repr(e)}")

    body = "\n\n".join(rows) if rows else "No jobs found."
    console.print(Panel(body, title="Jobs", border_style="cyan"))


def show_terminal_job(job_id):
    import json

    job_id = str(job_id).strip()
    base, jobs = _job_base()

    candidates = [
        jobs / "running" / f"{job_id}.json",
        jobs / "done" / f"{job_id}.json",
    ]

    job_path = next((p for p in candidates if p.exists()), None)

    if not job_path:
        console.print(Panel(
            f"Job not found: {job_id}",
            title="Job",
            border_style="yellow"
        ))
        return

    data = json.loads(job_path.read_text(encoding="utf-8"))

    body = json.dumps(data, indent=2)
    if len(body) > 14000:
        body = body[:14000] + "\n\n[TRUNCATED]"

    console.print(Panel(body, title=f"Job: {job_id}", border_style="cyan"))


def show_terminal_job_trace(job_id):
    job_id = str(job_id).strip()
    base, jobs = _job_base()

    candidates = [
        jobs / "traces" / f"{job_id}.trace.md",
        jobs / "logs" / f"{job_id}.trace.md",
    ]

    trace_path = next((p for p in candidates if p.exists()), None)

    if not trace_path:
        console.print(Panel(
            f"No trace found for: {job_id}",
            title="Job Trace",
            border_style="yellow"
        ))
        return

    body = trace_path.read_text(errors="ignore")
    if len(body) > 16000:
        body = body[-16000:]

    console.print(Panel(body, title=f"Trace: {job_id}", border_style="yellow"))


def cancel_terminal_job(job_id):
    from datetime import datetime

    job_id = str(job_id).strip()
    base, jobs = _job_base()
    cancel_path = jobs / "cancelled" / f"{job_id}.cancel"
    cancel_path.write_text(
        "cancelled_at=" + datetime.now().isoformat(timespec="seconds"),
        encoding="utf-8"
    )

    console.print(Panel(
        f"Cancel signal written for: {job_id}",
        title="Cancel Job",
        border_style="yellow"
    ))



# TITAN_BG_JOB_HELPERS_V2
def titan_jobs_base():
    base = Path("/Volumes/AI_DRIVE/TitanAgent")
    jobs = base / "jobs"

    for folder in [
        jobs / "running",
        jobs / "done",
        jobs / "cancelled",
        jobs / "logs",
        jobs / "traces",
    ]:
        folder.mkdir(parents=True, exist_ok=True)

    return base, jobs


def titan_start_bg_job(task):
    base, jobs = titan_jobs_base()
    running = jobs / "running"
    logs = jobs / "logs"

    job_id = "term-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    job = {
        "id": job_id,
        "task": str(task),
        "status": "queued",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "max_steps": 12,
        "source": "terminal"
    }

    (running / f"{job_id}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")

    worker = base / "background_worker.py"
    if not worker.exists():
        console.print(Panel(
            "background_worker.py is missing. Create it before using /bg.",
            title="Background Job",
            border_style="red"
        ))
        return

    subprocess.Popen(
        [sys.executable, str(worker), job_id],
        cwd=str(base),
        stdout=(logs / f"{job_id}.stdout.log").open("w"),
        stderr=(logs / f"{job_id}.stderr.log").open("w"),
        start_new_session=True
    )

    console.print(Panel(
        f"Started background job: {job_id}\n\n"
        f"Task: {task}\n\n"
        f"Use:\n"
        f"/jobs\n"
        f"/job {job_id}\n"
        f"/trace-job {job_id}\n"
        f"/cancel {job_id}",
        title="Background Job",
        border_style="green"
    ))


def titan_show_jobs():
    base, jobs = titan_jobs_base()
    rows = []

    for folder_name in ["running", "done"]:
        folder = jobs / folder_name
        for p in sorted(folder.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:25]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                rows.append(
                    f"{data.get('id', p.stem)} | {data.get('status', folder_name)} | {data.get('created_at', '')}\n"
                    f"  {str(data.get('task', ''))[:160]}"
                )
            except Exception as e:
                rows.append(f"{p.name} | unreadable | {repr(e)}")

    console.print(Panel(
        "\n\n".join(rows) if rows else "No jobs found.",
        title="Jobs",
        border_style="cyan"
    ))


def titan_show_job(job_id):
    job_id = str(job_id).strip()
    base, jobs = titan_jobs_base()

    candidates = [
        jobs / "running" / f"{job_id}.json",
        jobs / "done" / f"{job_id}.json",
    ]

    job_path = next((p for p in candidates if p.exists()), None)

    if not job_path:
        console.print(Panel(
            f"Job not found: {job_id}",
            title="Job",
            border_style="yellow"
        ))
        return

    data = json.loads(job_path.read_text(encoding="utf-8"))
    body = json.dumps(data, indent=2)

    if len(body) > 14000:
        body = body[:14000] + "\n\n[TRUNCATED]"

    console.print(Panel(body, title=f"Job: {job_id}", border_style="cyan"))


def titan_show_trace(job_id):
    job_id = str(job_id).strip()
    base, jobs = titan_jobs_base()

    candidates = [
        jobs / "traces" / f"{job_id}.trace.md",
        jobs / "logs" / f"{job_id}.trace.md",
    ]

    trace_path = next((p for p in candidates if p.exists()), None)

    if not trace_path:
        console.print(Panel(
            f"No trace found for: {job_id}",
            title="Job Trace",
            border_style="yellow"
        ))
        return

    body = trace_path.read_text(errors="ignore")
    if len(body) > 16000:
        body = body[-16000:]

    console.print(Panel(body, title=f"Trace: {job_id}", border_style="yellow"))


def titan_cancel_job(job_id):
    job_id = str(job_id).strip()
    base, jobs = titan_jobs_base()

    cancel_path = jobs / "cancelled" / f"{job_id}.cancel"
    cancel_path.write_text(
        "cancelled_at=" + datetime.now().isoformat(timespec="seconds"),
        encoding="utf-8"
    )

    console.print(Panel(
        f"Cancel signal written for: {job_id}",
        title="Cancel Job",
        border_style="yellow"
    ))


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
        # TITAN_BG_HARD_INTERCEPT_V2
        _cmd_raw = str(command if "command" in locals() else user_input).strip()

        if _cmd_raw.startswith("/bg "):
            try:
                titan_start_bg_job(_cmd_raw.replace("/bg ", "", 1).strip())
            except Exception as _e:
                console.print(Panel(
                    "Background job command failed but Titan stayed alive.\n\n" + repr(_e),
                    title="Background Job Error",
                    border_style="red"
                ))
            continue

        if _cmd_raw == "/jobs":
            try:
                titan_show_jobs()
            except Exception as _e:
                console.print(Panel(
                    "Jobs command failed but Titan stayed alive.\n\n" + repr(_e),
                    title="Jobs Error",
                    border_style="red"
                ))
            continue

        if _cmd_raw.startswith("/job "):
            try:
                titan_show_job(_cmd_raw.replace("/job ", "", 1).strip())
            except Exception as _e:
                console.print(Panel(
                    "Job command failed but Titan stayed alive.\n\n" + repr(_e),
                    title="Job Error",
                    border_style="red"
                ))
            continue

        if _cmd_raw.startswith("/trace-job "):
            try:
                titan_show_trace(_cmd_raw.replace("/trace-job ", "", 1).strip())
            except Exception as _e:
                console.print(Panel(
                    "Trace command failed but Titan stayed alive.\n\n" + repr(_e),
                    title="Trace Error",
                    border_style="red"
                ))
            continue

        if _cmd_raw.startswith("/cancel "):
            try:
                titan_cancel_job(_cmd_raw.replace("/cancel ", "", 1).strip())
            except Exception as _e:
                console.print(Panel(
                    "Cancel command failed but Titan stayed alive.\n\n" + repr(_e),
                    title="Cancel Error",
                    border_style="red"
                ))
            continue

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]exiting Titan[/dim]")
            break

        if not user_input:
            continue

        command = user_input.strip()
        # TITAN_HARD_DASHBOARD_INTERCEPT
        if str(command).strip().lower() in ["/dashboard", "launch dashboard", "open dashboard", "start dashboard", "launch dash board", "open dash board"]:
            try:
                import subprocess as _subprocess
                import sys as _sys
                from pathlib import Path as _Path

                _base = _Path("/Volumes/AI_DRIVE/TitanAgent")
                _launcher = _base / "launch_dashboard.py"

                if not _launcher.exists():
                    console.print(Panel(
                        "launch_dashboard.py is missing. Run the launcher creation step first.",
                        title="Dashboard",
                        border_style="red"
                    ))
                    continue

                _result = _subprocess.run(
                    [_sys.executable, str(_launcher)],
                    cwd=str(_base),
                    capture_output=True,
                    text=True,
                    timeout=12
                )

                _body = (
                    "exit_code: " + str(_result.returncode) + "\n\n"
                    "stdout:\n" + _result.stdout + "\n"
                    "stderr:\n" + _result.stderr
                )

                console.print(Panel(
                    _body,
                    title="Dashboard",
                    border_style="green" if _result.returncode == 0 else "red"
                ))

            except Exception as _e:
                try:
                    console.print(Panel(
                        "Dashboard command failed but Titan stayed alive.\n\n" + repr(_e),
                        title="Dashboard Error",
                        border_style="red"
                    ))
                except Exception:
                    print("Dashboard command failed:", repr(_e))
            continue


        if command in ["/products",
    "/product ",
    "/skill-new ",
    "/install ",
    "/download ",
    "/dashboard",
    "/exit", "exit", "quit", "/bye"]:
            break

        if command == "/dashboard":
            launch_dashboard()
            continue

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

        if command == "/agentic":
            toggle_agentic()
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

        # TITAN_DASHBOARD_ALIAS_HANDLER
        if command == "/dashboard" or command.lower().strip() in ["launch dashboard", "open dashboard", "start dashboard", "launch dash board", "open dash board"]:
            safe_execute_command("/dashboard", launch_dashboard)
            continue

        # TITAN_TERMINAL_JOB_HANDLERS
        if str(command).strip().startswith("/bg "):
            start_terminal_bg_job(str(command).replace("/bg ", "", 1).strip())
            continue

        if str(command).strip() == "/jobs":
            show_terminal_jobs()
            continue

        if str(command).strip().startswith("/job "):
            show_terminal_job(str(command).replace("/job ", "", 1).strip())
            continue

        if str(command).strip().startswith("/trace-job "):
            show_terminal_job_trace(str(command).replace("/trace-job ", "", 1).strip())
            continue

        if str(command).strip().startswith("/cancel "):
            cancel_terminal_job(str(command).replace("/cancel ", "", 1).strip())
            continue

        run_agent_task(command)


if __name__ == "__main__":
    repl()
