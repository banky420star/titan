from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_slash_dropdown.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

helper = r'''
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

        value = prompt(
            prompt_text,
            completer=TitanSlashCompleter(),
            complete_style=CompleteStyle.MULTI_COLUMN,
            complete_while_typing=True,
            reserve_space_for_menu=8,
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
        return input(prompt_text)
# TITAN_SLASH_DROPDOWN_END

'''

if "TITAN_SLASH_DROPDOWN_START" not in text:
    if "def repl():" not in text:
        raise SystemExit("Could not find def repl()")
    text = text.replace("def repl():", helper + "\ndef repl():", 1)

replacements = [
    (
        r'command\s*=\s*console\.input\(([^)]*)\)',
        r'command = titan_prompt_input(\1)'
    ),
    (
        r'command\s*=\s*Prompt\.ask\(([^)]*)\)',
        r'command = titan_prompt_input(str(\1))'
    ),
    (
        r'command\s*=\s*input\(([^)]*)\)',
        r'command = titan_prompt_input(\1)'
    ),
    (
        r'user_input\s*=\s*console\.input\(([^)]*)\)',
        r'user_input = titan_prompt_input(\1)'
    ),
    (
        r'user_input\s*=\s*Prompt\.ask\(([^)]*)\)',
        r'user_input = titan_prompt_input(str(\1))'
    ),
    (
        r'user_input\s*=\s*input\(([^)]*)\)',
        r'user_input = titan_prompt_input(\1)'
    ),
]

changed = 0
for pattern, repl in replacements:
    text, count = re.subn(pattern, repl, text)
    changed += count

if changed == 0:
    marker = "command ="
    raise SystemExit("No input line patched. Search manually for the terminal input line.")

path.write_text(text, encoding="utf-8")
print(f"slash dropdown patched, input replacements: {changed}")
