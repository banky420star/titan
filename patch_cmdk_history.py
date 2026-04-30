from pathlib import Path

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/control_panel_before_cmdk_history.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

# Add History command after Open Chat in paletteCommands.
needle = '''  {
    title: "Open Chat",
    desc: "Go to Titan chat.",
    keywords: "chat home",
    run: () => clickNavByView("chat")
  },'''

insert = '''  {
    title: "Open Chat",
    desc: "Go to Titan chat.",
    keywords: "chat home",
    run: () => clickNavByView("chat")
  },
  {
    title: "Open History",
    desc: "Open chat history and project sections.",
    keywords: "history sections logs chat project tasks sessions",
    run: () => { clickNavByView("history"); loadHistory(); }
  },
  {
    title: "Refresh History",
    desc: "Reload chat history and sections.",
    keywords: "refresh history sections logs",
    run: () => loadHistory()
  },'''

if 'title: "Open History"' not in text:
    if needle not in text:
        raise SystemExit("Could not find Open Chat command block in command palette.")
    text = text.replace(needle, insert, 1)
else:
    print("History command already exists.")

path.write_text(text, encoding="utf-8")
print("Added History to Cmd+K command palette.")
