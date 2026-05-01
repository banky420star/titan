# dashboard-polisher

Improve Titan's Flask dashboard: UI, navigation, API routes, and real-time features.

## When to use

When adding tabs, fixing layout, adding API endpoints, or improving dashboard UX.

## Workflow

1. Read `control_panel.py` — all HTML/CSS/JS is embedded. Search for the relevant section.
2. Navigation buttons are in the `showView()` button row. Each button calls `showView('tab-name', this)`.
3. Tab content goes in `<section id="view-tab-name" class="view">`.
4. JS functions go before `</script>` — use `jsonFetch()` for API calls (already defined).
5. API routes go before `if __name__ == "__main__":` — use `safe()` wrapper for error handling.
6. After changes, verify syntax: `python3 -c "compile(open('control_panel.py').read(), 'cp', 'exec')"`.
7. Test: `python3 control_panel.py` → open `http://127.0.0.1:5050`.

## Dashboard structure

- **Nav row**: horizontal button bar at the top, each triggers `showView()`
- **Views**: `<section class="view">` — only one visible at a time (CSS `.view { display:none }`, `.view.active { display:block }`)
- **API pattern**: `@app.route("/api/X")` → return `jsonify(...)` or `safe(lambda: ...)`
- **JS pattern**: `async function name() { const data = await jsonFetch("/api/X"); ... }`
- **Downloads**: `/downloads/<path>` serves files from `BASE / "downloads"`

## Dependencies

- flask

## Notes

The file is 4000+ lines. Use `search_files` to find sections instead of scrolling. Keep CSS in the existing `<style>` block, JS in the existing `<script>` block.