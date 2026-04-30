from pathlib import Path

path = Path("control_panel_titan_ui.py")
if not path.exists():
    path = Path("control_panel.py")

if not path.exists():
    raise SystemExit("Could not find control_panel_titan_ui.py or control_panel.py")

text = path.read_text()

script_marker = "</script>"
if script_marker not in text:
    raise SystemExit("Could not find </script>")

js = r'''
    // BACKGROUND CHAT POLLING PATCH
    function sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }

    function shortJobStatus(job) {
      if (!job) return "No job data.";
      const status = job.status || "unknown";
      const id = job.id || job.job_id || "unknown";
      const task = job.task || "";
      return `Job ${id}\nStatus: ${status}\n\n${task}`;
    }

    async function pollJob(jobId) {
      let attempts = 0;
      let lastStatus = "";

      while (attempts < 240) {
        attempts += 1;

        try {
          const response = await fetch("/api/job/" + encodeURIComponent(jobId));
          const job = await response.json();

          if (job.error) {
            setTitanState("error", "!");
            showResult(job);
            resetTitanState(2400);
            return;
          }

          const status = job.status || "unknown";

          if (status !== lastStatus) {
            lastStatus = status;
            if (status === "running") {
              setTitanState("working", "⚙");
            }
          }

          if (status === "done") {
            setTitanState("happy", "✓");
            showResult({
              job_id: jobId,
              status: status,
              result: job.result || "Done.",
              trace: job.trace || ""
            });
            resetTitanState(1600);
            return;
          }

          if (status === "error") {
            setTitanState("error", "!");
            showResult({
              job_id: jobId,
              status: status,
              result: job.result || "Job failed.",
              stderr: job.stderr || "",
              trace: job.trace || ""
            });
            resetTitanState(2600);
            return;
          }

          if (status === "cancelled") {
            setTitanState("error", "!");
            showResult({
              job_id: jobId,
              status: status,
              result: job.result || "Job cancelled."
            });
            resetTitanState(2200);
            return;
          }

        } catch (err) {
          setTitanState("error", "!");
          showResult("Job polling failed: " + String(err));
          resetTitanState(2400);
          return;
        }

        await sleep(2000);
      }

      setTitanState("thinking", "…");
      showResult({
        job_id: jobId,
        status: "still-running",
        message: "Titan is still working. Check the Jobs panel or reload later."
      });
    }

    window.postJSON = async function(url, data) {
      appendTyping();

      try {
        setTitanState("working", "⚙");

        const response = await fetch(url, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(data || {})
        });

        const json = await response.json();

        if (json.error) {
          setTitanState("error", "!");
          showResult(json);
          resetTitanState(2400);
          return;
        }

        if (json.job_id) {
          removeTyping();
          appendMessage(
            "assistant",
            "Started background job: " + json.job_id + "\nI’ll watch it and post the result here.",
            "Titan"
          );
          setTitanState("working", "⚙");
          pollJob(json.job_id);
          return;
        }

        setTitanState("happy", "✓");
        showResult(json);
        resetTitanState(1400);

      } catch (err) {
        setTitanState("error", "!");
        showResult(String(err));
        resetTitanState(2400);
      }
    };
'''

if "// BACKGROUND CHAT POLLING PATCH" not in text:
    text = text.replace(script_marker, js + "\n  " + script_marker)

path.write_text(text)
print(f"Patched frontend chat polling in {path}")
