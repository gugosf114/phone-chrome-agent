"""JSON command protocol shared by terminal agents and the conductor."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

from .adapters import default_adapters
from .glance import critic_packet, name_break, press_or_stop, revise_step, run_plan
from .models import Step
from .skills import SkillLibrary
from .store import Store

OPERATIONS = ["schema", "catalog", "propose", "trial", "evaluate", "promote", "execute", "export", "diagnose", "observe", "glance", "critic", "revise", "follow"]


def schema() -> dict:
    return {
        "operations": OPERATIONS,
        "requests": {
            "catalog": {"operation": "catalog", "query": "optional words", "include_candidates": False},
            "propose": {"operation": "propose", "spec": "skill object below", "sources": ["actual task IDs"], "parent": "optional integer version"},
            "trial": {"operation": "trial", "id": "skill-id", "version": 1, "inputs": {}, "request_id": "stable unique attempt ID"},
            "evaluate": {"operation": "evaluate", "id": "skill-id", "version": 1, "cases": [
                {"id": "case-name", "inputs": {}, "expect": {"equals": {"output_name": "expected value"}}, "request_id": "required for mutations; omit for read-only evaluation"}]},
            "promote": {"operation": "promote", "id": "skill-id", "version": 1},
            "execute": {"operation": "execute", "id": "skill-id", "inputs": {}, "request_id": "stable unique request ID"},
            "export": {"operation": "export", "id": "skill-id", "version": "optional integer"},
            "diagnose": {"operation": "diagnose", "task_id": "failed or successful task ID"},
            "observe": {"operation": "observe", "display": "main", "package": "optional exact package", "query": "optional text", "offset": 0, "limit": 20},
        },
        "skill_example": {
            "id": "read-hidden-app", "description": "Read current text in an already-open hidden app", "tags": ["phone", "read"],
            "inputs": {"display": {"type": "string"}, "package": {"type": "string"}},
            "plan": {"task": {"goal": "Read {{package}} on {{display}}"}, "steps": [
                {"adapter": "hidden", "verb": "observe", "target": "hidden:{{display}}", "args": {},
                 "expect": {"equals": {"screen.package": {"$input": "package"}}}}]},
            "outputs": {"text": "0.screen.text", "nodes": "0.screen.nodes"},
        },
        "rules": [
            "Acquire: inspect the real app or an existing tool; use docs/demonstrations as evidence to draft a parameterized candidate.",
            "Trial dispatches exactly once per request_id. A lost acknowledgement returns outcome_unknown on reuse; inspect evidence before issuing a new ID.",
            "Evaluate requires at least two distinct inputs and nonempty outcome expectations. It runs read-only plans; mutations use evidence from explicit trial requests.",
            "For failure, diagnose the task from observed events and propose a new version with parent set. Keep regression cases unchanged.",
            "Only an evaluation passing every case can promote a version. Prefer unseen inputs and independently authored expected outcomes.",
            "The model supplies reasoning; this runtime does not start background learning or paid model calls.",
        ],
    }


def dispatch(library: SkillLibrary, request: dict):
    if not isinstance(request, dict):
        raise ValueError("request must be a JSON object")
    op = request.get("operation")
    if op == "schema":
        return schema()
    if op == "catalog":
        return library.catalog(request.get("query", ""), request.get("include_candidates", False))
    if op == "propose":
        return library.propose(request["spec"], request.get("sources"), request.get("parent"))
    if op == "trial":
        return library.trial(request["id"], request["version"], request["inputs"], request["request_id"])
    if op == "evaluate":
        return library.evaluate(request["id"], request["version"], request["cases"])
    if op == "promote":
        return library.promote(request["id"], request["version"])
    if op == "execute":
        return library.execute(request["id"], request["inputs"], request["request_id"], request.get("version"))
    if op == "export":
        return library.export(request["id"], request.get("version"))
    if op == "diagnose":
        return library.diagnose(request["task_id"])
    if op == "glance":
        return press_or_stop(request["button"], request["controls"], request.get("backups") or ())
    if op == "critic":
        packet = critic_packet(
            request["instruction"],
            request.get("observations") or [],
            request.get("actions") or [],
        )
        packet["break"] = name_break(packet["actions"])
        return packet
    if op == "revise":
        return revise_step(request["spec"], request["step"], request["button"])
    if op == "follow":
        answer = request.get("model_answer")
        model = (lambda packet: answer) if isinstance(answer, str) else None
        return run_plan(request["goal"], request["steps"], request["pages"], model, request.get("book"), request.get("failures"))
    if op == "observe":
        result = library.adapters["hidden"].execute(Step("hidden", "observe", "hidden:" + request.get("display", "main")))
        data = {"status": "completed" if result.ok and result.verified else "failed", **result.data}
        if "screen" in data:
            package, query = request.get("package", ""), request.get("query", "")
            offset, limit = request.get("offset", 0), request.get("limit", 20)
            if not isinstance(package, str) or not isinstance(query, str) or type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= 100:
                raise ValueError("observe needs string package/query, offset >= 0 and limit 1..100")
            screen = dict(data["screen"])
            nodes = screen["nodes"]
            matched = [n for n in nodes if (not package or n.get("package") == package)
                       and (not query or query.casefold() in " ".join(str(n.get(key, "")) for key in ("text", "description", "resource_id")).casefold())]
            page = matched[offset:offset + limit]
            text = "\n".join(n.get("text", "") for n in page if n.get("text"))
            screen.update({"nodes": page, "text": text[:4000], "text_truncated": len(text) > 4000,
                           "total_nodes": len(nodes), "matched_nodes": len(matched), "offset": offset,
                           "next_offset": offset + limit if offset + limit < len(matched) else None})
            data["screen"] = screen
        return data
    raise ValueError("unknown operation; use schema")


def main(argv=None, adapters=None) -> int:
    parser = argparse.ArgumentParser(prog="bridge learn", description="Acquire, evaluate, revise and reuse tested skills")
    parser.add_argument("--db", default=os.environ.get("AGENT_BRIDGE_TASK_DB", str(Path.home() / ".local/state/agent-bridge/task-engine.sqlite3")))
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("schema", "catalog"):
        sub.add_parser(name)
    request = sub.add_parser("request", help="JSON operation; input is data, never shell code")
    source = request.add_mutually_exclusive_group(required=True)
    source.add_argument("--json", help="inline JSON request")
    source.add_argument("--file", help="UTF-8 request file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        if args.command in {"schema", "catalog"}:
            payload = {"operation": args.command}
        elif args.json is not None:
            payload = json.loads(args.json)
        elif args.file == "-":
            payload = json.load(sys.stdin)
        else:
            payload = json.loads(Path(args.file).read_text(encoding="utf-8-sig"))
        store = Store(args.db)
        try:
            result = dispatch(SkillLibrary(store, default_adapters() if adapters is None else adapters), payload)
        finally:
            store.close()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if isinstance(result, dict):
            if result.get("status") in {"failed", "blocked", "outcome_unknown"}:
                return 1
            if "passed" in result and result["passed"] != result["total"]:
                return 1
        return 0
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error) as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
