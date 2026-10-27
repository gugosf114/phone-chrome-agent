from __future__ import annotations

import json
import hashlib
import os
import sqlite3
import time
import uuid
import fcntl
from dataclasses import replace
from pathlib import Path
from typing import Any, BinaryIO

from .models import Authority, PermissionGrant, Scope, Step, TaskPlan, utc_now


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS grants (
    id TEXT PRIMARY KEY,
    authority INTEGER NOT NULL,
    scope_kind TEXT NOT NULL,
    scope_value TEXT,
    remaining_uses INTEGER,
    targets_json TEXT NOT NULL,
    denied_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    revoked_at TEXT
);
CREATE TABLE IF NOT EXISTS race_clocks (
    id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    started_at TEXT NOT NULL,
    started_unix_ns INTEGER NOT NULL,
    claimed_by TEXT,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    grant_id TEXT NOT NULL REFERENCES grants(id),
    status TEXT NOT NULL,
    plan_json TEXT NOT NULL,
    recipe_key TEXT,
    baseline_ms INTEGER,
    speed_ratio REAL NOT NULL,
    next_step INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_elapsed_ms INTEGER,
    result_json TEXT
);
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    elapsed_ms INTEGER,
    permission_receipt TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(id),
    task_id TEXT NOT NULL REFERENCES tasks(id),
    step_index INTEGER NOT NULL,
    adapter TEXT NOT NULL,
    verb TEXT NOT NULL,
    target TEXT NOT NULL,
    args_json TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    elapsed_ms INTEGER NOT NULL,
    status TEXT NOT NULL,
    verified INTEGER NOT NULL,
    result_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recipes (
    key TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    steps_json TEXT NOT NULL,
    successes INTEGER NOT NULL DEFAULT 0,
    failures INTEGER NOT NULL DEFAULT 0,
    total_ms INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        os.chmod(self.path, 0o600)

    def close(self) -> None:
        self.db.close()

    def acquire_named_lock(self, namespace: str, name: str) -> BinaryIO | None:
        """Hold an exclusive process-lifetime lock for one named owner resource."""
        lock_dir = self.path.parent / f".{self.path.name}.{namespace}-locks"
        lock_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(lock_dir, 0o700)
        lock_name = hashlib.sha256(name.encode("utf-8")).hexdigest()
        lock_path = lock_dir / f"{lock_name}.lock"
        descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        handle = os.fdopen(descriptor, "rb+", buffering=0)
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            return None
        return handle

    def acquire_task_lock(self, task_id: str) -> BinaryIO | None:
        """Hold exclusive ownership of a task until the returned handle is closed."""
        return self.acquire_named_lock("task", task_id)

    def acquire_resource_lock(self, resource: str) -> BinaryIO | None:
        """Prevent separate tasks from interleaving one stateful resource."""
        return self.acquire_named_lock("resource", resource)

    @staticmethod
    def release_task_lock(handle: BinaryIO) -> None:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()

    release_resource_lock = release_task_lock

    def create_race(self, race_id: str, goal: str = "timed task") -> dict[str, Any]:
        started_at = utc_now()
        started_unix_ns = time.time_ns()
        with self.db:
            self.db.execute(
                """
                INSERT INTO race_clocks (
                    id, goal, started_at, started_unix_ns, claimed_by, finished_at
                ) VALUES (?, ?, ?, ?, NULL, NULL)
                """,
                (race_id, goal, started_at, started_unix_ns),
            )
        return self.race(race_id)

    def race(self, race_id: str) -> dict[str, Any]:
        row = self.db.execute(
            "SELECT * FROM race_clocks WHERE id = ?", (race_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown race clock {race_id!r}.")
        return dict(row)

    def finish_race(self, race_id: str) -> None:
        with self.db:
            self.db.execute(
                "UPDATE race_clocks SET finished_at = ? WHERE id = ?",
                (utc_now(), race_id),
            )

    def save_plan(self, plan: TaskPlan) -> None:
        plan.validate_for_storage()
        now = utc_now()
        race = None
        if plan.race_ref:
            race = self.race(plan.race_ref)
            if race["claimed_by"] not in {None, plan.id}:
                raise ValueError(
                    f"Race clock {plan.race_ref!r} already belongs to {race['claimed_by']!r}."
                )
        grant = plan.permission
        if grant and grant.scope.kind in {"task", "test"}:
            if grant.scope.value not in {None, plan.id}:
                raise ValueError("inline task/test permission belongs to another task")
            grant = replace(grant, scope=replace(grant.scope, value=plan.id))
            plan = replace(plan, permission=grant)
        if plan.permission_ref:
            existing = self.db.execute(
                "SELECT id, scope_kind, scope_value FROM grants WHERE id = ?",
                (plan.permission_ref,),
            ).fetchone()
            if existing is None:
                raise KeyError(f"Unknown shared permission {plan.permission_ref!r}.")
            if (
                existing["scope_kind"] in {"task", "test"}
                and existing["scope_value"] != plan.id
            ):
                raise ValueError("shared task/test permission belongs to another task")
            grant_id = plan.permission_ref
        elif grant:
            grant_id = grant.id
        else:
            raise ValueError("The plan has no permission.")
        with self.db:
            if grant:
                self._insert_grant(grant)
            self.db.execute(
                """
                INSERT INTO tasks (
                    id, goal, grant_id, status, plan_json, recipe_key,
                    baseline_ms, speed_ratio, created_at, updated_at
                ) VALUES (?, ?, ?, 'ready', ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan.id,
                    plan.goal,
                    grant_id,
                    json.dumps(plan.to_dict(), separators=(",", ":")),
                    plan.recipe_key,
                    plan.baseline_ms,
                    plan.speed_ratio,
                    now,
                    now,
                ),
            )
            if plan.race_ref:
                claimed = self.db.execute(
                    """
                    UPDATE race_clocks SET claimed_by = ?
                    WHERE id = ? AND (claimed_by IS NULL OR claimed_by = ?)
                    """,
                    (plan.id, plan.race_ref, plan.id),
                )
                if claimed.rowcount != 1:
                    raise ValueError(
                        f"Race clock {plan.race_ref!r} could not be claimed."
                    )

    def _insert_grant(self, grant: PermissionGrant) -> None:
        grant.validate_for_storage()
        if grant.scope.kind in {"task", "test"} and not grant.scope.value:
            raise ValueError("stored task/test permission needs a concrete task ID")
        if grant.scope.kind == "session" and not grant.scope.value:
            raise ValueError("stored session permission needs a concrete session ID")
        self.db.execute(
            """
            INSERT INTO grants (
                id, authority, scope_kind, scope_value, remaining_uses,
                targets_json, denied_json, created_at, expires_at, revoked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                grant.id,
                int(grant.authority),
                grant.scope.kind,
                grant.scope.value,
                grant.scope.remaining_uses,
                json.dumps(grant.targets),
                json.dumps(grant.denied_actions),
                grant.created_at,
                grant.expires_at,
                grant.revoked_at,
            ),
        )

    def create_grant(self, grant: PermissionGrant) -> None:
        with self.db:
            self._insert_grant(grant)

    def grant(self, grant_id: str) -> PermissionGrant:
        row = self.db.execute(
            "SELECT * FROM grants WHERE id = ?", (grant_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown permission {grant_id!r}.")
        return self._grant_from_row(row)

    @staticmethod
    def _grant_from_row(row: sqlite3.Row) -> PermissionGrant:
        return PermissionGrant(
            id=row["id"],
            authority=Authority(row["authority"]),
            scope=Scope(row["scope_kind"], row["scope_value"], row["remaining_uses"]),
            targets=tuple(json.loads(row["targets_json"])),
            denied_actions=tuple(json.loads(row["denied_json"])),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
        )

    def task_row(self, task_id: str) -> sqlite3.Row:
        row = self.db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown task {task_id!r}.")
        return row

    def grant_for_task(self, task_id: str) -> PermissionGrant:
        row = self.db.execute(
            """
            SELECT g.* FROM grants g
            JOIN tasks t ON t.grant_id = g.id
            WHERE t.id = ?
            """,
            (task_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"No permission exists for task {task_id!r}.")
        return self._grant_from_row(row)

    def revoke_grant(self, grant_id: str) -> None:
        if (
            self.db.execute("SELECT 1 FROM grants WHERE id = ?", (grant_id,)).fetchone()
            is None
        ):
            raise KeyError(f"Unknown permission {grant_id!r}.")
        with self.db:
            self.db.execute(
                "UPDATE grants SET revoked_at = ? WHERE id = ?", (utc_now(), grant_id)
            )

    def plan_for_task(self, task_id: str) -> TaskPlan:
        row = self.task_row(task_id)
        return TaskPlan.from_dict(json.loads(row["plan_json"]), task_id)

    def start_run(
        self,
        run_id: str,
        task_id: str,
        receipt: str,
        expected_next_step: int,
    ) -> bool:
        now = utc_now()
        with self.db:
            claimed = self.db.execute(
                """
                UPDATE tasks SET status = 'running', updated_at = ?
                WHERE id = ? AND next_step = ?
                  AND status IN ('ready', 'blocked', 'failed', 'running')
                """,
                (now, task_id, expected_next_step),
            )
            if claimed.rowcount != 1:
                return False
            self.db.execute(
                """
                UPDATE runs SET status = 'abandoned', ended_at = ?
                WHERE task_id = ? AND status = 'running'
                """,
                (now, task_id),
            )
            self.db.execute(
                "INSERT INTO runs VALUES (?, ?, 'running', ?, NULL, NULL, ?)",
                (run_id, task_id, now, receipt),
            )
        return True

    def record_event(self, event: dict[str, Any]) -> None:
        with self.db:
            self.db.execute(
                """
                INSERT INTO events (
                    run_id, task_id, step_index, adapter, verb, target,
                    args_json, started_at, ended_at, elapsed_ms, status,
                    verified, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["run_id"],
                    event["task_id"],
                    event["step_index"],
                    event["adapter"],
                    event["verb"],
                    event["target"],
                    json.dumps(event["args"], separators=(",", ":")),
                    event["started_at"],
                    event["ended_at"],
                    event["elapsed_ms"],
                    event["status"],
                    int(event["verified"]),
                    json.dumps(event["result"], separators=(",", ":")),
                ),
            )

    def checkpoint(self, task_id: str, next_step: int, status: str = "running") -> None:
        with self.db:
            self.db.execute(
                "UPDATE tasks SET next_step = ?, status = ?, updated_at = ? WHERE id = ?",
                (next_step, status, utc_now(), task_id),
            )

    def block_task_if_idle(self, task_id: str, next_step: int) -> None:
        with self.db:
            self.db.execute(
                """
                UPDATE tasks SET status = 'blocked', updated_at = ?
                WHERE id = ? AND next_step = ?
                  AND status IN ('ready', 'blocked', 'failed')
                """,
                (utc_now(), task_id, next_step),
            )

    def finish_run(
        self,
        run_id: str,
        task_id: str,
        status: str,
        elapsed_ms: int,
        result: dict[str, Any],
        next_step: int,
    ) -> None:
        now = utc_now()
        with self.db:
            self.db.execute(
                "UPDATE runs SET status = ?, ended_at = ?, elapsed_ms = ? WHERE id = ?",
                (status, now, elapsed_ms, run_id),
            )
            self.db.execute(
                """
                UPDATE tasks SET status = ?, next_step = ?, updated_at = ?,
                    last_elapsed_ms = ?, result_json = ?
                WHERE id = ?
                """,
                (
                    status,
                    next_step,
                    now,
                    elapsed_ms,
                    json.dumps(result, separators=(",", ":")),
                    task_id,
                ),
            )

    def reserve_permission_run(self, grant_id: str) -> bool:
        with self.db:
            reserved = self.db.execute(
                """
                UPDATE grants
                SET remaining_uses = CASE
                    WHEN remaining_uses IS NULL THEN NULL
                    ELSE remaining_uses - 1
                END
                WHERE id = ? AND (remaining_uses IS NULL OR remaining_uses > 0)
                """,
                (grant_id,),
            )
        return reserved.rowcount == 1

    def replace_permission(self, task_id: str, grant: PermissionGrant) -> None:
        self.task_row(task_id)
        if grant.scope.kind in {"task", "test"}:
            if grant.scope.value not in {None, task_id}:
                raise ValueError(
                    "replacement task/test permission belongs to another task"
                )
            grant = replace(grant, scope=replace(grant.scope, value=task_id))
        if grant.scope.kind == "session" and not grant.scope.value:
            raise ValueError(
                "replacement session permission needs a concrete session ID"
            )
        grant = replace(
            grant,
            id=f"grant-{task_id}-{uuid.uuid4().hex[:12]}",
            revoked_at=None,
        )
        with self.db:
            self._insert_grant(grant)
            self.db.execute(
                "UPDATE tasks SET grant_id = ?, updated_at = ? WHERE id = ?",
                (grant.id, utc_now(), task_id),
            )

    def revoke_permission(self, task_id: str) -> None:
        current = self.grant_for_task(task_id)
        revoked = replace(
            current,
            id=f"grant-{task_id}-{uuid.uuid4().hex[:12]}",
            revoked_at=utc_now(),
        )
        with self.db:
            self._insert_grant(revoked)
            self.db.execute(
                "UPDATE tasks SET grant_id = ?, updated_at = ? WHERE id = ?",
                (revoked.id, utc_now(), task_id),
            )

    def save_recipe(
        self, key: str, goal: str, steps: list[dict[str, Any]], elapsed_ms: int
    ) -> None:
        now = utc_now()
        checked_steps = [Step.from_dict(step).to_dict() for step in steps]
        encoded = json.dumps(checked_steps, separators=(",", ":"))
        with self.db:
            self.db.execute(
                """
                INSERT INTO recipes (key, goal, steps_json, successes, failures, total_ms, updated_at)
                VALUES (?, ?, ?, 1, 0, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    goal = excluded.goal,
                    steps_json = excluded.steps_json,
                    successes = recipes.successes + 1,
                    total_ms = recipes.total_ms + excluded.total_ms,
                    updated_at = excluded.updated_at
                """,
                (key, goal, encoded, elapsed_ms, now),
            )

    def mark_recipe_failure(self, key: str) -> None:
        with self.db:
            self.db.execute(
                "UPDATE recipes SET failures = failures + 1, updated_at = ? WHERE key = ?",
                (utc_now(), key),
            )

    def recipe(self, key: str) -> dict[str, Any] | None:
        row = self.db.execute("SELECT * FROM recipes WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["steps"] = json.loads(result.pop("steps_json"))
        result["average_ms"] = (
            result["total_ms"] / result["successes"] if result["successes"] else None
        )
        return result

    def task_status(self, task_id: str) -> dict[str, Any]:
        row = dict(self.task_row(task_id))
        plan_raw = json.loads(row["plan_json"])
        task_raw = plan_raw.get("task", plan_raw)
        row["browser_backend"] = task_raw.get("browser_backend")
        if row.get("result_json"):
            row["result"] = json.loads(row.pop("result_json"))
        row.pop("plan_json", None)
        grant = self.grant_for_task(task_id)
        row["permission"] = {
            "authority": int(grant.authority),
            "authority_name": grant.authority.name.lower(),
            "scope": grant.scope.kind,
            "remaining_uses": grant.scope.remaining_uses,
            "targets": list(grant.targets),
            "denied_actions": list(grant.denied_actions),
        }
        return row

    def events(self, task_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT * FROM events WHERE task_id = ? ORDER BY id", (task_id,)
        ).fetchall()
        return [dict(row) for row in rows]
