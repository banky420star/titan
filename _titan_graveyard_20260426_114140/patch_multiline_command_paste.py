from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_multiline_paste.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

if "TITAN_MULTILINE_QUEUE_V1" not in text:
    text = text.replace(
        "def repl():",
        '''# TITAN_MULTILINE_QUEUE_V1
_titan_command_queue = []

def titan_next_command(prompt_text):
    global _titan_command_queue

    if _titan_command_queue:
        return _titan_command_queue.pop(0)

    raw = titan_prompt_input(prompt_text)
    raw = str(raw or "").replace("\\r\\n", "\\n").replace("\\r", "\\n")

    parts = [line.strip() for line in raw.split("\\n") if line.strip()]

    if not parts:
        return ""

    if len(parts) > 1:
        _titan_command_queue.extend(parts[1:])

    return parts[0]

def repl():''',
        1
    )

replaced = False

for old in [
    'command = titan_prompt_input(prompt_text)',
    'command = titan_prompt_input(prompt)',
    'command = titan_prompt_input("titan ▸ ")',
    "command = titan_prompt_input('titan ▸ ')",
    'user_input = titan_prompt_input(prompt_text)',
    'user_input = titan_prompt_input(prompt)',
    'user_input = titan_prompt_input("titan ▸ ")',
    "user_input = titan_prompt_input('titan ▸ ')",
]:
    if old in text:
        text = text.replace(old, old.replace("titan_prompt_input", "titan_next_command"))
        replaced = True

if not replaced:
    text = text.replace(
        'command = input(prompt_text)',
        'command = titan_next_command(prompt_text)'
    )
    text = text.replace(
        'user_input = input(prompt_text)',
        'user_input = titan_next_command(prompt_text)'
    )

path.write_text(text, encoding="utf-8")
print("Installed multiline paste queue.")
