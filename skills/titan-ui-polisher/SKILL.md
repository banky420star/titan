# titan-ui-polisher

Improve Titan's visual identity across terminal and dashboard.

## When to use

When enhancing the mascot, colors, animations, or visual polish of any Titan interface.

## Workflow

1. Identify which surface needs work: terminal (titan_terminal.py) or dashboard (control_panel.py).
2. For terminal: modify `startup()` for banner, `repl()` for prompt style, or add Rich markup to output.
3. For dashboard: edit CSS in the `<style>` block of control_panel.py. Key variables: `--bg`, `--surface`, `--accent`, `--text`, `--muted`.
4. Keep changes small and targeted. One visual improvement per pass.
5. Test both surfaces after any change.

## Visual guidelines

- **Colors**: Dark background (#111214), accent green (#00e87b), surface panels (#1a1a2e).
- **Mascot**: Three horizontal bars (≡) — the Titan logo. Use in startup, dashboard header, and chat welcome.
- **Typography**: System font stack. Monospace for code areas.
- **Animations**: Keep them subtle — blinks, fades, slides. No spinners or bouncing.

## Dependencies

- rich (terminal colors/formatting)

## Notes

Visual changes are subjective — always show the result and let the user decide. Don't overhaul the entire theme in one pass.