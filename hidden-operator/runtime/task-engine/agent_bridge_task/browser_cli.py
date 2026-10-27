"""One JSON interface for persistent browser tasks and the conductor."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys

from .browser_tasks import BrowserTasks, BrowserDriver
from .store import Store


def schema():
    return {
        "environment": {"operation": "environment"},
        "start": {"operation": "start", "goal": "user's actual objective", "url": "https://example.com",
                  "backend": "phone-headless", "profile": "default", "requirements": {"dates": "requested dates"},
                  "success_checks": [{"contains": {"text": "required visible result"}}], "transactional": False},
        "observe": {"operation": "observe", "task_id": "browse-...", "screenshot": True},
        "act": {"operation": "act", "task_id": "browse-...", "request_id": "unique stable action ID",
                "observation_id": "view-...", "action": {"kind": "click", "control_id": "f0-c3"}, "intent": "why this advances the goal", "strategy": "the actual approach, e.g. direct date entry"},
        "actions": {"navigate": ["url"], "click": ["control_id"], "fill": ["control_id", "value"],
                    "select": ["control_id", "value"], "check": ["control_id"], "uncheck": ["control_id"],
                    "press": ["key"], "scroll": ["pixels"], "back": [], "wait": ["milliseconds"], "click_xy": ["x", "y"]},
        "recover": {"operation": "recover", "task_id": "browse-...", "inspect_url": "optional account/receipt URL for GET inspection"},
        "resolve": {"operation": "resolve", "task_id": "browse-...", "request_id": "pending action ID",
                    "outcome": "applied or not_applied", "evidence_checks": [{"contains": {"text": "positive observed evidence"}}]},
        "complete": {"operation": "complete", "task_id": "browse-...", "recheck_url": "persistent receipt/account URL for a transaction", "reference": "actual observed confirmation reference"},
        "status": {"operation": "status", "task_id": "browse-..."},
        "release_site": {"operation": "release_site", "task_id": "browse-...", "evidence_checks": [{"contains": {"text": "positive evidence that the restriction has been resolved"}}]},
        "list": {"operation": "list"}, "cancel": {"operation": "cancel", "task_id": "browse-..."},
        "rules": ["No site-specific recipe is needed: observe, decide one action, inspect its returned page, repeat.",
                  "Choose controls from the current observation; use screenshots for visual widgets.",
                  "success_checks are fixed at start and must cover the requested result, not tool exit codes.",
                  "After lost acknowledgement, recover, inspect the real account/receipt, then reconcile. Never retry a submission blindly.",
                  "A transaction requires a reference present before and after reopening a persistent record URL.",
                  "Site warnings and failed approaches persist across restart, recover and new task IDs. Honor site_advice; never disguise traffic or rotate accounts to work around a restriction.",
                  "Use diagnosis.alternatives for ordinary UI failures. After two identical failed approaches, change the actual method or fix missing input, not just the strategy label.",
                  "Do not invent personal details, dates or account access; ask the operator when required facts are missing."]}


def dispatch(tasks, request):
    if not isinstance(request, dict): raise ValueError("request must be an object")
    op = request.get("operation")
    if op == "schema": return schema()
    if op == "environment": return BrowserDriver.environment()
    if op == "list": return tasks.list()
    if op == "start":
        arguments = {k: v for k, v in request.items() if k != "operation"}
        return tasks.start(**arguments)
    task_id = request["task_id"]
    if op == "status": return tasks.status(task_id)
    if op == "observe": return tasks.observe(task_id, request.get("screenshot", False))
    if op == "act": return tasks.act(task_id, request["request_id"], request["observation_id"], request["action"], request.get("intent", ""), request.get('strategy', ''))
    if op == "recover": return tasks.recover(task_id, request.get("inspect_url"), request.get("screenshot", False))
    if op == "resolve": return tasks.resolve(task_id, request["request_id"], request["outcome"], request["evidence_checks"])
    if op == "complete": return tasks.complete(task_id, request.get("recheck_url"), request.get("reference"))
    if op == "cancel": return tasks.cancel(task_id)
    if op == "release_site": return tasks.release_site(task_id, request['evidence_checks'])
    raise ValueError("unknown browser operation")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="bridge browse")
    parser.add_argument("--db", default=os.environ.get("AGENT_BRIDGE_TASK_DB", str(Path.home() / ".local/state/agent-bridge/task-engine.sqlite3")))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("schema")
    commands.add_parser("list")
    request = commands.add_parser("request")
    source = request.add_mutually_exclusive_group(required=True)
    source.add_argument("--json")
    source.add_argument("--file")
    args = parser.parse_args(argv)
    store = None
    try:
        if args.command != "request": payload = {"operation": args.command}
        elif args.json is not None: payload = json.loads(args.json)
        elif args.file == "-": payload = json.load(sys.stdin)
        else: payload = json.loads(Path(args.file).read_text(encoding="utf-8-sig"))
        store = Store(args.db)
        result = dispatch(BrowserTasks(store), payload)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except (ValueError, KeyError, TypeError, RuntimeError, OSError, sqlite3.Error) as error:
        print(json.dumps({"status": "error", "error": str(error)}))
        return 2
    finally:
        if store: store.close()


if __name__ == "__main__":
    raise SystemExit(main())
