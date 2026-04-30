from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_prompt_ansi_fix.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

start = text.find("def titan_prompt_input(prompt_text):")
if start == -1:
    raise SystemExit("Could not find titan_prompt_input()")

end = text.find("\n# TITAN_SLASH_DROPDOWN_END", start)
if end == -1:
    raise SystemExit("Could not find TITAN_SLASH_DROPDOWN_END")

new_func = r'''def titan_prompt_input(prompt_text):
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
'''

text = text[:start] + new_func + text[end:]

path.write_text(text, encoding="utf-8")
print("Fixed prompt ANSI rendering for dropdown menu.")
