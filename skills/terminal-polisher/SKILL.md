# terminal-polisher

Improve Titan's terminal REPL: slash commands, autocomplete, startup, and UX.

## When to use

When adding/modifying slash commands, fixing tab completion, or improving terminal behavior.

## Workflow

1. Read `titan_terminal.py` — it's the main REPL file.
2. **Slash commands**: Add the command string to `TITAN_SLASH_COMMANDS` list. Add metadata to `TITAN_SLASH_META` dict.
3. **Handler**: Add a function that implements the command, then add an `elif` branch in `repl()`.
4. **Autocomplete**: prompt_toolkit's `WordCompleter` reads `TITAN_SLASH_COMMANDS` automatically.
5. **Startup**: Modify the `startup()` function for banner text and animation.
6. After changes, test: `python3 titan_terminal.py` → type `/` and verify dropdown shows all commands.

## Key structures

- `TITAN_SLASH_COMMANDS`: List of all `/command` strings (drives autocomplete)
- `TITAN_SLASH_META`: Dict of `command → description` (drives help text)
- `repl()`: Main loop — `elif text.startswith("/command"):` branches handle each command
- `safe_chat()`: The Ollama call — don't touch unless model config is broken

## Dependencies

- rich (for console output)
- prompt_toolkit (for autocomplete)

## Notes

Never remove existing slash commands — only add. Keep command names short and consistent. Test with `python3 -c "import titan_terminal; print('OK')"` after edits.