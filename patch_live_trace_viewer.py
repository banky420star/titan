from pathlib import Path
import re

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

# -------------------------------------------------------------------
# 1. Replace Jobs view with proper live trace UI
# -------------------------------------------------------------------
new_jobs_section = r'''
        <section id="view-jobs" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Jobs / Live Trace</strong>
              <div class="row compact-row">
                <label class="toggle-label">
                  <input type="checkbox" id="jobsAutoRefresh" checked>
                  Auto-refresh
                </label>
                <button class="btn" onclick="loadJobs()">Refresh</button>
              </div>
            </div>

            <div class="panel-body">
              <div class="jobs-layout">
                <div class="job-list-wrap">
                  <div class="section-title">Recent Jobs</div>
                  <div id="jobsList" class="job-list">Loading...</div>
                </div>

                <div class="job-detail-wrap">
                  <div class="section-title" id="selectedJobTitle">Select a job</div>

                  <div class="job-tabs">
                    <button class="btn active" onclick="showJobTab('summary', this)">Summary</button>
                    <button class="btn" onclick="showJobTab('result', this)">Result</button>
                    <button class="btn" onclick="showJobTab('trace', this)">Trace</button>
                    <button class="btn" onclick="showJobTab('log', this)">Log</button>
                  </div>

                  <div class="job-pane active" id="jobPane-summary">
                    <pre id="jobSummary">No job selected.</pre>
                  </div>

                  <div class="job-pane" id="jobPane-result">
                    <pre id="jobResult">No result yet.</pre>
                  </div>

                  <div class="job-pane" id="jobPane-trace">
                    <pre id="jobTrace">No trace yet.</pre>
                  </div>

                  <div class="job-pane" id="jobPane-log">
                    <pre id="jobLog">No log yet.</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
'''

text = re.sub(
    r'<section id="view-jobs" class="view">.*?</section>',
    new_jobs_section,
    text,
    count=1,
    flags=re.S
)

# -------------------------------------------------------------------
# 2. Add CSS for job viewer
# -------------------------------------------------------------------
css = r'''
    /* TITAN_LIVE_TRACE_VIEWER_START */
    .compact-row {
      margin: 0;
      align-items: center;
    }

    .toggle-label {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      user-select: none;
    }

    .jobs-layout {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 16px;
      min-height: 520px;
    }

    .job-list-wrap,
    .job-detail-wrap {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.035);
      border-radius: 18px;
      overflow: hidden;
    }

    .section-title {
      padding: 13px 15px;
      border-bottom: 1px solid var(--line);
      font-weight: 800;
      color: #f4f4f5;
      background: rgba(255,255,255,.035);
    }

    .job-list {
      max-height: 680px;
      overflow-y: auto;
      padding: 12px;
      display: grid;
      gap: 10px;
    }

    .job-card {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.045);
      border-radius: 16px;
      padding: 12px;
      cursor: pointer;
      transition: transform .14s ease, background .14s ease, border-color .14s ease;
    }

    .job-card:hover {
      background: rgba(255,255,255,.075);
      transform: translateY(-1px);
    }

    .job-card.active {
      border-color: rgba(232,171,67,.38);
      background: rgba(232,171,67,.09);
    }

    .job-card-title {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
      margin-bottom: 8px;
      font-weight: 800;
      font-size: 13px;
    }

    .job-card-task {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.055);
      color: #d4d4d8;
      white-space: nowrap;
    }

    .status-pill.running,
    .status-pill.queued {
      color: #fbbf24;
      border-color: rgba(251,191,36,.28);
      background: rgba(251,191,36,.09);
    }

    .status-pill.done {
      color: #22c55e;
      border-color: rgba(34,197,94,.25);
      background: rgba(34,197,94,.08);
    }

    .status-pill.error {
      color: #fb7185;
      border-color: rgba(251,113,133,.28);
      background: rgba(251,113,133,.09);
    }

    .job-tabs {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      padding: 12px;
      border-bottom: 1px solid var(--line);
    }

    .job-tabs .btn.active {
      background: rgba(232,171,67,.18);
      border-color: rgba(232,171,67,.34);
    }

    .job-pane {
      display: none;
      padding: 14px;
    }

    .job-pane.active {
      display: block;
    }

    .job-pane pre {
      max-height: 590px;
      overflow-y: auto;
      background: rgba(0,0,0,.18);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
    }

    @media (max-width: 980px) {
      .jobs-layout {
        grid-template-columns: 1fr;
      }

      .job-list {
        max-height: 320px;
      }
    }
    /* TITAN_LIVE_TRACE_VIEWER_END */
'''

if "TITAN_LIVE_TRACE_VIEWER_START" not in text:
    text = text.replace("</style>", css + "\n  </style>", 1)

# -------------------------------------------------------------------
# 3. Append/override JS functions for jobs live trace viewer
# -------------------------------------------------------------------
js = r'''
// TITAN_LIVE_TRACE_VIEWER_JS_START
let selectedJobId = null;
let jobsRefreshTimer = null;

function statusClass(status) {
  status = String(status || "").toLowerCase();
  if (["running", "queued", "done", "error", "cancelled"].includes(status)) return status;
  return "";
}

function compactTask(text, max = 180) {
  text = String(text || "");
  return text.length > max ? text.slice(0, max) + "..." : text;
}

function showJobTab(name, btn) {
  document.querySelectorAll(".job-pane").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".job-tabs .btn").forEach(b => b.classList.remove("active"));
  const pane = document.getElementById("jobPane-" + name);
  if (pane) pane.classList.add("active");
  if (btn) btn.classList.add("active");
}

async function loadJobs() {
  const data = await jsonFetch("/api/jobs");
  const jobs = data.jobs || [];
  const list = document.getElementById("jobsList");

  if (!list) return;

  if (!jobs.length) {
    list.textContent = "No jobs yet.";
    return;
  }

  list.innerHTML = "";

  jobs.forEach(job => {
    const card = document.createElement("div");
    card.className = "job-card" + (job.id === selectedJobId ? " active" : "");
    card.onclick = () => selectJob(job.id);

    const title = document.createElement("div");
    title.className = "job-card-title";

    const id = document.createElement("span");
    id.textContent = job.id || "unknown-job";

    const status = document.createElement("span");
    status.className = "status-pill " + statusClass(job.status);
    status.textContent = job.status || "unknown";

    title.appendChild(id);
    title.appendChild(status);

    const task = document.createElement("div");
    task.className = "job-card-task";
    task.textContent = compactTask(job.task || "(no task)");

    card.appendChild(title);
    card.appendChild(task);
    list.appendChild(card);
  });

  if (!selectedJobId && jobs[0] && jobs[0].id) {
    selectJob(jobs[0].id);
  }
}

async function selectJob(id) {
  selectedJobId = id;
  document.querySelectorAll(".job-card").forEach(c => c.classList.remove("active"));

  const title = document.getElementById("selectedJobTitle");
  if (title) title.textContent = "Job: " + id;

  await loadJobDetail(id);
  await loadJobs();
}

async function loadJobDetail(id) {
  if (!id) return;

  const data = await jsonFetch("/api/job/" + encodeURIComponent(id));

  const summary = {
    id: data.id,
    status: data.status,
    source: data.source,
    created_at: data.created_at,
    started_at: data.started_at,
    finished_at: data.finished_at,
    task: data.task,
    error: data.error
  };

  const summaryEl = document.getElementById("jobSummary");
  const resultEl = document.getElementById("jobResult");
  const traceEl = document.getElementById("jobTrace");
  const logEl = document.getElementById("jobLog");

  if (summaryEl) summaryEl.textContent = JSON.stringify(summary, null, 2);
  if (resultEl) resultEl.textContent = data.result || "(no result yet)";
  if (traceEl) traceEl.textContent = data.trace || "(no trace yet)";
  if (logEl) logEl.textContent = data.log || "(no log yet)";
}

function ensureJobsAutoRefresh() {
  if (jobsRefreshTimer) clearInterval(jobsRefreshTimer);

  jobsRefreshTimer = setInterval(async () => {
    const auto = document.getElementById("jobsAutoRefresh");
    const jobsView = document.getElementById("view-jobs");

    if (!auto || !auto.checked) return;
    if (!jobsView || !jobsView.classList.contains("active")) return;

    await loadJobs();
    if (selectedJobId) await loadJobDetail(selectedJobId);
  }, 2500);
}

setTimeout(ensureJobsAutoRefresh, 500);

// Patch quick chat job output to include a visible trace hint.
const oldQuickTitan = typeof quick === "function" ? quick : null;
if (oldQuickTitan) {
  quick = async function(task) {
    addMessage("user", task);
    addMessage("assistant", "Started background job...");
    const data = await jsonFetch("/api/task", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({task})
    });

    if (data.error) {
      addMessage("assistant", data.error);
      return;
    }

    addMessage("assistant", "Job: " + data.job_id + "\nOpen Jobs tab to watch trace/log live.");
    selectedJobId = data.job_id;
    pollJob(data.job_id);
  }
}
// TITAN_LIVE_TRACE_VIEWER_JS_END
'''

if "TITAN_LIVE_TRACE_VIEWER_JS_START" not in text:
    text = text.replace("</script>", js + "\n</script>", 1)

path.write_text(text, encoding="utf-8")
print("Patched dashboard live trace/job viewer.")
