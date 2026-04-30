# Phase 8 Approvals and Shell

Timestamp: 20260426_133107

Added:
- agent_core/approvals.py
- /mode
- /safe
- /power
- /agentic
- /run <command>

Behavior:
- Commands run inside workspace.
- Dangerous fragments are blocked.
- Safe mode allows read/check commands.
- Power mode allows normal build commands.
- Agentic mode allows configured command prefixes but still blocks destructive commands.

Next:
- dashboard settings page for mode switching
- approval queue for destructive actions
- stronger autonomous taskboard
