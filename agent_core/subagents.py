from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time

from agent_core.models import safe_chat

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG_PATH = BASE / "config.json"
SUBAGENTS_DIR = BASE / "subagents"
LOGS = BASE / "logs"

SUBAGENTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

DEFAULT_ORDER = ["planner", "coder", "tester", "reviewer"]


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def load_subagent(role):
    path = SUBAGENTS_DIR / f"{role}.json"
    if not path.exists():
        return {
            "role": role,
            "name": role.title(),
            "codename": role,
            "description": "",
            "style": "concise"
        }
    return json.loads(path.read_text(encoding="utf-8"))


def list_subagents():
    cfg = load_config()
    role_models = cfg.get("role_models", {})

    rows = []
    for role in DEFAULT_ORDER:
        spec = load_subagent(role)
        rows.append({
            "role": role,
            "name": spec.get("name", role),
            "codename": spec.get("codename", role),
            "description": spec.get("description", ""),
            "model": role_models.get(role, cfg.get("model", "unset"))
        })

    return rows


def format_subagents():
    rows = list_subagents()
    lines = ["Titan subagents:"]
    for row in rows:
        lines.append(
            f"- {row['name']} ({row['role']})\n"
            f"  Model: {row['model']}\n"
            f"  Role: {row['description']}"
        )
    return "\n\n".join(lines)


def call_subagent(role, task, context=""):
    cfg = load_config()
    spec = load_subagent(role)
    role_models = cfg.get("role_models", {})
    model = role_models.get(role, cfg.get("model", "qwen3:8b"))

    system = (
        f"You are {spec.get('name', role)}, a Titan subagent.\n"
        f"Codename: {spec.get('codename', role)}\n"
        f"Role: {spec.get('description', '')}\n"
        f"Style: {spec.get('style', 'concise')}\n\n"
        "Return concise, useful, actionable output.\n"
        "Do not pretend you used tools unless tool output is provided.\n"
        "Do not use markdown tables.\n"
        "Be concrete."
    )

    user = "Task:\n" + str(task)
    if context:
        user += "\n\nShared context:\n" + str(context)

    started = time.time()
    try:
        result = safe_chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            model=model,
            timeout=int(cfg.get("subagent_timeout", 180))
        )
    except Exception as e:
        result = f"{spec.get('name', role)} failed safely: {repr(e)}"

    elapsed = round(time.time() - started, 2)

    return {
        "role": role,
        "name": spec.get("name", role),
        "model": model,
        "elapsed": elapsed,
        "output": str(result).strip()
    }


def synthesize_team(task, outputs):
    cfg = load_config()
    model = cfg.get("model", "qwen3:8b")

    joined = []
    for item in outputs:
        joined.append(
            f"## {item['name']} [{item['role']}]\n"
            f"Model: {item['model']}\n"
            f"Elapsed: {item['elapsed']}s\n"
            f"{item['output']}"
        )

    system = (
        "You are Titan, synthesizing a subagent team result.\n"
        "Return a concise final answer with:\n"
        "1. Best plan\n"
        "2. Risks/checks\n"
        "3. Exact next actions\n"
        "No fake tool claims."
    )

    user = "Original task:\n" + str(task) + "\n\nSubagent outputs:\n\n" + "\n\n".join(joined)

    return safe_chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        model=model,
        timeout=int(cfg.get("team_synthesis_timeout", 180))
    )


def run_team(task):
    cfg = load_config()

    # Stage 1: Planner Voss creates the shared plan first.
    planner = call_subagent("planner", task)

    shared_context = (
        "Planner Voss initial plan:\n"
        + planner["output"]
    )

    roles = ["coder", "tester", "reviewer"]

    outputs = [planner]

    # Stage 2: other agents work in parallel using the plan.
    max_workers = int(cfg.get("team_max_workers", 3))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(call_subagent, role, task, shared_context): role
            for role in roles
        }

        for future in as_completed(futures):
            try:
                outputs.append(future.result())
            except Exception as e:
                role = futures[future]
                spec = load_subagent(role)
                outputs.append({
                    "role": role,
                    "name": spec.get("name", role),
                    "model": "unknown",
                    "elapsed": 0,
                    "output": "Subagent failed safely: " + repr(e)
                })

    final = synthesize_team(task, outputs)

    report = {
        "task": task,
        "outputs": outputs,
        "final": final
    }

    report_path = LOGS / "last_team_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = ["Titan Team Result", ""]
    for item in outputs:
        lines.append(f"## {item['name']} [{item['role']}]")
        lines.append(f"Model: {item['model']} | {item['elapsed']}s")
        lines.append(item["output"])
        lines.append("")

    lines.append("## Final synthesis")
    lines.append(str(final).strip())
    lines.append("")
    lines.append(f"Saved: {report_path}")

    return "\n".join(lines)
