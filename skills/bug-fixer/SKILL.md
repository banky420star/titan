# bug-fixer

Find, patch, and verify bugs in Titan's agent_core, terminal, and dashboard code.

## When to use

When something crashes, returns an error, or behaves unexpectedly in Titan's Python stack.

## Workflow

1. Read the error traceback or symptom description.
2. Use `search_files` to locate the failing function/module.
3. Use `read_file` on the suspect file — understand the logic before touching anything.
4. Identify the root cause (wrong import, missing function, bad path, type mismatch, recursion).
5. Apply the smallest fix that addresses the root cause. No refactoring, no "while I'm here" changes.
6. If the fix involves a path or config value, check `config.json` for the correct setting.
7. Run `run_command` with `python3 -c "from agent_core.X import Y; print('OK')"` to verify imports.
8. Report: what was broken, what changed, and which file:line.

## Common patterns

- `NameError`: function called but never defined — add the function or fix the import.
- `ModuleNotFoundError`: missing `sys.path.insert` or wrong module name.
- `InfiniteRecursion`: two modules call each other — add a direct path that bypasses the cycle.
- `FileNotFoundError`: hardcoded path wrong — use `BASE / "correct" / "path"` instead.
- `JSONDecodeError`: model returned prose instead of JSON — the agent's `extract_json_objects` handles this, but check if the system prompt is intact.

## Dependencies

- none

## Notes

Never skip reading the file before editing. Never assume — verify with a test import.