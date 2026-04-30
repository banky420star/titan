# Phase 13 Search and Diff

Timestamp: 20260426_141200

Added:
- agent_core/search_diff.py
- dashboard Search / Diff tab
- terminal commands:
  - /search <query>
  - /snapshot [root]
  - /changed [root]
  - /diff <root> <path>

Dashboard APIs:
- GET /api/search
- POST /api/snapshot
- GET /api/changed
- GET /api/diff

Next:
- product templates
- git integration
- command palette
