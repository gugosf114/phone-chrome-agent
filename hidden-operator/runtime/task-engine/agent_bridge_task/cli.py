from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sqlite3
import statistics
import sys
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from .adapters import default_adapters
from .engine import Engine
from .models import Authority, PermissionGrant, TaskPlan
from .permissions import permission_receipt
from .store import Store


DEFAULT_DB = Path(
    os.environ.get(
        "AGENT_BRIDGE_TASK_DB",
        str(Path.home() / ".local" / "state" / "agent-bridge" / "task-engine.sqlite3"),
    )
)


def load_json(path: str) -> dict[str, Any]:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="bridge checkpoint")
    root.add_argument("--db", default=str(DEFAULT_DB), help="SQLite state file")
    commands = root.add_subparsers(dest="command", required=True)

    check = commands.add_parser(
        "check", help="validate a plan and its permission before acting"
    )
    check.add_argument("plan")
    check.add_argument("--session")

    run = commands.add_parser("run", help="save and execute a new plan")
    run.add_argument("plan")
    run.add_argument("--session")

    resume = commands.add_parser(
        "resume", help="continue from the exact failed or blocked step"
    )
    resume.add_argument("task_id")
    resume.add_argument("--session")

    status = commands.add_parser(
        "status", help="show a task, permission, and checkpoint"
    )
    status.add_argument("task_id")

    events = commands.add_parser("events", help="show the proof log for a task")
    events.add_argument("task_id")

    recipe = commands.add_parser("recipe", help="show a saved fast path")
    recipe.add_argument("recipe_key")

    replay = commands.add_parser(
        "replay", help="run a saved fast path with a new permission"
    )
    replay.add_argument("recipe_key")
    replay.add_argument("permission", help="JSON file containing the new permission")
    replay.add_argument("--goal")
    replay.add_argument("--baseline-ms", type=int)
    replay.add_argument(
        "--race", help="race clock started when George made the request"
    )
    replay.add_argument(
        "--browser-backend",
        choices=("phone-headless", "android-chrome", "laptop-chrome", "cdp"),
        help="explicit browser route for a browser recipe",
    )
    replay.add_argument("--session")

    benchmark = commands.add_parser(
        "benchmark", help="run a timed race over the same plan"
    )
    benchmark.add_argument("plan")
    benchmark.add_argument("--runs", type=int, default=5)
    benchmark.add_argument("--warmup", type=int, default=1)
    benchmark.add_argument("--session")

    race_start = commands.add_parser(
        "race-start", help="start the user-visible timer before planning"
    )
    race_start.add_argument("--goal", default="timed task")

    race_status = commands.add_parser("race-status", help="show a request timer")
    race_status.add_argument("race_id")

    grant = commands.add_parser("grant", help="create a shared permission")
    grant.add_argument("permission", help="permission JSON file")

    grant_status = commands.add_parser("grant-status", help="show a shared permission")
    grant_status.add_argument("grant_id")

    grant_revoke = commands.add_parser(
        "grant-revoke", help="revoke a shared permission"
    )
    grant_revoke.add_argument("grant_id")

    permit = commands.add_parser("permit", help="replace a task permission immediately")
    permit.add_argument("task_id")
    permit.add_argument("permission", help="new permission JSON file")

    revoke = commands.add_parser("revoke", help="close a task permission immediately")
    revoke.add_argument("task_id")

    explain = commands.add_parser(
        "explain", help="print the exact meaning of a permission"
    )
    explain.add_argument("permission", help="permission JSON file")
    return root


def main(
    argv: list[str] | None = None,
    adapters: dict[str, Any] | None = None,
) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "explain":
            raw = load_json(args.permission)
            grant = PermissionGrant.from_dict(raw.get("id", "preview"), raw)
            emit({"permission": permission_receipt(grant)})
            return 0

        store = Store(args.db)
        try:
            engine = Engine(
                store, adapters if adapters is not None else default_adapters()
            )
            if args.command == "race-start":
                race_id = f"race-{uuid.uuid4().hex[:16]}"
                emit(store.create_race(race_id, args.goal))
                return 0
            if args.command == "race-status":
                emit(store.race(args.race_id))
                return 0
            if args.command in {"check", "run"}:
                raw = load_json(args.plan)
                generated_id = f"task-{uuid.uuid4().hex[:16]}"
                plan = TaskPlan.from_dict(raw, generated_id)
                if args.command == "check":
                    if plan.permission is None:
                        plan = replace(
                            plan, permission=store.grant(str(plan.permission_ref))
                        )
                    emit(
                        {
                            "task_id": plan.id,
                            "goal": plan.goal,
                            **engine.preflight(plan, session_id=args.session),
                        }
                    )
                    return 0
                result = engine.create_and_run(plan, session_id=args.session)
            elif args.command == "resume":
                result = engine.run(args.task_id, session_id=args.session)
            elif args.command == "status":
                emit(store.task_status(args.task_id))
                return 0
            elif args.command == "events":
                emit(store.events(args.task_id))
                return 0
            elif args.command == "recipe":
                found = store.recipe(args.recipe_key)
                if found is None:
                    raise KeyError(f"Unknown recipe {args.recipe_key!r}.")
                emit(found)
                return 0
            elif args.command == "replay":
                result = engine.replay(
                    args.recipe_key,
                    load_json(args.permission),
                    goal=args.goal,
                    baseline_ms=args.baseline_ms,
                    race_ref=args.race,
                    browser_backend=args.browser_backend,
                    session_id=args.session,
                )
            elif args.command == "permit":
                current = store.grant_for_task(args.task_id)
                replacement = PermissionGrant.from_dict(
                    current.id, load_json(args.permission)
                )
                store.replace_permission(args.task_id, replacement)
                emit(store.task_status(args.task_id))
                return 0
            elif args.command == "revoke":
                store.revoke_permission(args.task_id)
                emit(store.task_status(args.task_id))
                return 0
            elif args.command == "benchmark":
                if args.runs < 1 or args.warmup < 0:
                    raise ValueError(
                        "benchmark runs must be positive and warmup cannot be negative"
                    )
                template = load_json(args.plan)
                template_task = template.get("task", template)
                if template_task.get("race_ref"):
                    raise ValueError(
                        "benchmark measures the saved executor; remove race_ref or run one real request"
                    )
                preview = copy.deepcopy(template)
                preview.setdefault("task", {})["id"] = "benchmark-safety-check"
                safety_plan = TaskPlan.from_dict(preview, "benchmark-safety-check")
                for step in safety_plan.steps:
                    adapter = engine.adapters.get(step.adapter)
                    if adapter is None:
                        raise ValueError(
                            f"benchmark has unknown adapter {step.adapter!r}"
                        )
                    if adapter.required_authority(step) > Authority.READ:
                        raise ValueError(
                            "benchmark accepts read-only steps; run a mutating plan once"
                        )
                results = []
                total = args.warmup + args.runs
                for index in range(total):
                    raw = copy.deepcopy(template)
                    raw.setdefault("task", {})["id"] = f"bench-{uuid.uuid4().hex[:16]}"
                    if "permission_ref" not in raw["task"]:
                        raw["task"].setdefault("permission", {})["id"] = (
                            f"grant-{uuid.uuid4().hex[:16]}"
                        )
                    plan = TaskPlan.from_dict(raw, raw["task"]["id"])
                    measured = engine.create_and_run(plan, session_id=args.session)
                    if index >= args.warmup:
                        results.append(measured)
                elapsed = [item["elapsed_ms"] for item in results]
                successful = [
                    item
                    for item in results
                    if item["status"] in {"completed", "completed_slow"}
                ]
                ordered = sorted(elapsed)
                p95 = ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]
                speed_passes = sum(bool(item["speed_pass"]) for item in results)
                if len(successful) != len(results):
                    benchmark_status = "failed"
                elif speed_passes != len(results):
                    benchmark_status = "completed_slow"
                else:
                    benchmark_status = "completed"
                result = {
                    "status": benchmark_status,
                    "runs": len(results),
                    "successful_runs": len(successful),
                    "elapsed_ms": elapsed,
                    "minimum_ms": min(elapsed),
                    "median_ms": round(statistics.median(elapsed)),
                    "p95_ms": p95,
                    "maximum_ms": max(elapsed),
                    "speed_passes": speed_passes,
                }
            elif args.command == "grant":
                raw = load_json(args.permission)
                grant_id = str(raw.get("id") or f"grant-{uuid.uuid4().hex[:16]}")
                shared = PermissionGrant.from_dict(grant_id, raw)
                store.create_grant(shared)
                emit({"id": shared.id, "permission": permission_receipt(shared)})
                return 0
            elif args.command == "grant-status":
                shared = store.grant(args.grant_id)
                emit(
                    {
                        "id": shared.id,
                        "permission": permission_receipt(shared),
                        "revoked_at": shared.revoked_at,
                    }
                )
                return 0
            elif args.command == "grant-revoke":
                store.revoke_grant(args.grant_id)
                shared = store.grant(args.grant_id)
                emit(
                    {
                        "id": shared.id,
                        "permission": permission_receipt(shared),
                        "revoked_at": shared.revoked_at,
                    }
                )
                return 0
            else:
                raise AssertionError(args.command)
        finally:
            store.close()
    except (
        ValueError,
        KeyError,
        OSError,
        json.JSONDecodeError,
        sqlite3.Error,
    ) as error:
        emit({"status": "error", "error": str(error)})
        return 2

    emit(result)
    return {
        "completed": 0,
        "completed_slow": 4,
        "blocked": 3,
        "failed": 5,
    }.get(result.get("status"), 2)


if __name__ == "__main__":
    raise SystemExit(main())
