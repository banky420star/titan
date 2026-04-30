from pathlib import Path

path = Path("control_panel_titan_ui.py")
text = path.read_text()

marker = "</script>"
if marker not in text:
    raise SystemExit("Could not find </script>")

js = r'''
    // VISIBLE DASHBOARD DEBUG PATCH
    async function titanDebugPing() {
      try {
        const res = await fetch("/api/jobs");
        const json = await res.json();
        console.log("Titan API online:", json);
      } catch (err) {
        console.error("Titan API failed:", err);
        appendMessage("assistant", "Dashboard API is not responding: " + String(err), "Titan");
      }
    }

    window.addEventListener("load", () => {
      titanDebugPing();
    });

    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
      console.log("Titan fetch:", args[0]);
      try {
        const res = await originalFetch(...args);
        console.log("Titan fetch response:", args[0], res.status);
        return res;
      } catch (err) {
        console.error("Titan fetch error:", args[0], err);
        appendMessage("assistant", "Network request failed: " + String(err), "Titan");
        throw err;
      }
    };
'''

if "// VISIBLE DASHBOARD DEBUG PATCH" not in text:
    text = text.replace(marker, js + "\n" + marker)

path.write_text(text)
print("Added visible dashboard debug patch.")
