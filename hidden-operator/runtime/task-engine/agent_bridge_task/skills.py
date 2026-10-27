"""Versioned skills, observed episodes, evaluation and durable execution claims.

The caller/model writes candidates. Only actual task executions generate evidence.
No model API, background worker or automatic spending is started by this library.
"""
from __future__ import annotations

import json
import re
import sqlite3
import uuid
from typing import Any

from .adapters import _field, verify_expectation
from .engine import Engine, redact
from .models import Authority, utc_now
from .skill_schema import canonical, digest, instantiate, validate_inputs, validate_outcome, validate_spec
from .store import Store

SCHEMA = """
CREATE TABLE IF NOT EXISTS skill_versions (
  skill_id TEXT NOT NULL, version INTEGER NOT NULL, parent INTEGER,
  status TEXT NOT NULL, spec_json TEXT NOT NULL, content_hash TEXT NOT NULL,
  sources_json TEXT NOT NULL, created_at TEXT NOT NULL,
  PRIMARY KEY(skill_id, version)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_skill ON skill_versions(skill_id) WHERE status='active';
CREATE TABLE IF NOT EXISTS skill_executions (
  request_id TEXT PRIMARY KEY, skill_id TEXT NOT NULL, version INTEGER NOT NULL,
  inputs_hash TEXT NOT NULL, task_id TEXT NOT NULL UNIQUE, result_json TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS skill_evaluations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, skill_id TEXT NOT NULL, version INTEGER NOT NULL,
  content_hash TEXT NOT NULL, suite_json TEXT NOT NULL, report_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


class SkillLibrary:
    def __init__(self, store: Store, adapters: dict):
        self.store = store
        self.adapters = adapters
        self.store.db.executescript(SCHEMA)

    def _row(self, skill_id: str, version: int | None = None) -> dict:
        if version is None:
            row = self.store.db.execute(
                "SELECT * FROM skill_versions WHERE skill_id=? AND status='active'", (skill_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f"no active admitted skill {skill_id!r}")
        else:
            row = self.store.db.execute(
                "SELECT * FROM skill_versions WHERE skill_id=? AND version=?", (skill_id, version)
            ).fetchone()
            if row is None:
                raise KeyError(f"unknown skill {skill_id!r} version {version}")
        result = dict(row)
        if digest(json.loads(result["spec_json"])) != result["content_hash"]:
            raise ValueError("stored skill content hash mismatch")
        return result

    def propose(self, spec: dict, sources: list[str] | None = None, parent: int | None = None) -> dict:
        spec = validate_spec(spec)
        skill_id = spec["id"]
        sources = sources or []
        if not isinstance(sources, list) or not all(isinstance(x, str) for x in sources):
            raise ValueError("sources must contain task IDs")
        for task_id in sources:
            self.store.task_row(task_id)
        # Unknown adapters are rejected before a candidate can enter the library.
        for step in spec["plan"]["steps"]:
            if step["adapter"] not in self.adapters:
                raise ValueError(f"unknown adapter {step['adapter']!r}")
        lock = self.store.acquire_named_lock("skill", skill_id)
        if lock is None:
            raise ValueError("skill is being changed by another process")
        try:
            if parent is not None:
                prior = self._row(skill_id, parent)
            latest = self.store.db.execute(
                "SELECT MAX(version) FROM skill_versions WHERE skill_id=?", (skill_id,)
            ).fetchone()[0]
            if latest is not None and parent is None:
                raise ValueError("existing skill revisions need an admitted parent version")
            version = (latest or 0) + 1
            with self.store.db:
                self.store.db.execute(
                    "INSERT INTO skill_versions VALUES (?,?,?,'candidate',?,?,?,?)",
                    (skill_id, version, parent, canonical(spec), digest(spec), canonical(sources), utc_now()),
                )
            return {"id": skill_id, "version": version, "status": "candidate", "content_hash": digest(spec)}
        finally:
            self.store.release_task_lock(lock)

    def export(self, skill_id: str, version: int | None = None) -> dict:
        row = self._row(skill_id, version)
        return {"id": skill_id, "version": row["version"], "status": row["status"],
                "parent": row["parent"], "content_hash": row["content_hash"],
                "spec": json.loads(row["spec_json"]), "source_task_ids": json.loads(row["sources_json"])}

    def catalog(self, query: str = "", include_candidates: bool = False) -> list[dict]:
        rows = self.store.db.execute(
            "SELECT * FROM skill_versions" + ("" if include_candidates else " WHERE status='active'")
        ).fetchall()
        tokens = set(re.findall(r"\w+", query.lower()))
        result = []
        for row in rows:
            spec = json.loads(row["spec_json"])
            haystack = set(re.findall(r"\w+", " ".join([spec["id"], spec["description"], *spec.get("tags", [])]).lower()))
            score = len(tokens & haystack)
            if tokens and not score:
                continue
            result.append({"id": row["skill_id"], "version": row["version"], "status": row["status"],
                           "description": spec["description"], "inputs": spec["inputs"], "score": score})
        return sorted(result, key=lambda r: (-r["score"], r["id"], -r["version"]))

    def _execute(self, row: dict, inputs: dict, request_id: str) -> dict:
        if not isinstance(request_id, str) or not 1 <= len(request_id) <= 200:
            raise ValueError("execution needs a stable request_id of 1 to 200 characters")
        spec = json.loads(row["spec_json"])
        inputs = validate_inputs(spec, inputs)
        bound_hash = digest({"skill": row["content_hash"], "inputs": inputs})
        existing = self.store.db.execute(
            "SELECT * FROM skill_executions WHERE request_id=?", (request_id,)
        ).fetchone()
        if existing:
            if existing["inputs_hash"] != bound_hash or existing["skill_id"] != row["skill_id"] or existing["version"] != row["version"]:
                raise ValueError("request_id already belongs to different inputs or skill content")
            if existing["result_json"]:
                return json.loads(existing["result_json"])
            return {"status": "outcome_unknown", "request_id": request_id, "task_id": existing["task_id"],
                    "reason": "execution was claimed; inspect task evidence before any new request"}
        task_id = "skill-task-" + uuid.uuid4().hex
        plan = instantiate(spec, inputs, task_id)
        # The claim is durable BEFORE any adapter is invoked. A lost reply cannot replay work.
        try:
            with self.store.db:
                self.store.db.execute(
                    "INSERT INTO skill_executions VALUES (?,?,?,?,?,NULL,?)",
                    (request_id, row["skill_id"], row["version"], bound_hash, task_id, utc_now()),
                )
        except sqlite3.IntegrityError:
            return self._execute(row, inputs, request_id)
        try:
            result = Engine(self.store, self.adapters).create_and_run(plan)
        except Exception as error:
            # An exception may have followed an outside effect. Do not make it retryable.
            result = {"status": "outcome_unknown", "task_id": task_id,
                      "reason": type(error).__name__ + ": " + str(error)}
        failure = result.get("failure") or {}
        if isinstance(failure, dict) and isinstance(failure.get("result"), dict) and failure["result"].get("outcome") == "unknown":
            result["status"] = "outcome_unknown"
        result.update({"request_id": request_id, "skill_id": row["skill_id"], "skill_version": row["version"]})
        if result["status"] in {"completed", "completed_slow"}:
            observed = {}
            for event in self.store.events(task_id):
                if event["status"] == "success" and event["verified"]:
                    observed[str(event["step_index"])] = json.loads(event["result_json"])
            try:
                result["outputs"] = {name: _field(observed, path) for name, path in spec["outputs"].items()}
            except KeyError as error:
                result["status"] = "failed"
                result["output_error"] = f"observed result is missing {error.args[0]}"
        result = redact(result)
        with self.store.db:
            self.store.db.execute("UPDATE skill_executions SET result_json=? WHERE request_id=?",
                                  (canonical(result), request_id))
        return result

    def execute(self, skill_id: str, inputs: dict, request_id: str, version: int | None = None) -> dict:
        # Pin a repeated request to the original version even if a newer version was promoted.
        prior = self.store.db.execute("SELECT skill_id,version FROM skill_executions WHERE request_id=?", (request_id,)).fetchone()
        if prior:
            if prior["skill_id"] != skill_id or (version is not None and version != prior["version"]):
                raise ValueError("request_id already belongs to a different skill version")
            version = prior["version"]
        row = self._row(skill_id, version)
        if row["status"] not in {"active", "retired"}:
            raise ValueError("skill has not been admitted; evaluate the candidate first")
        return self._execute(row, inputs, request_id)

    def trial(self, skill_id: str, version: int, inputs: dict, request_id: str) -> dict:
        """One explicitly requested attempt. Evaluation never repeats its effects."""
        row = self._row(skill_id, version)
        if row["status"] != "candidate":
            raise ValueError("trial is for candidate skills; use execute for admitted skills")
        return self._execute(row, inputs, request_id)

    def _latest_evaluation(self, skill_id: str, version: int) -> dict | None:
        row = self.store.db.execute(
            "SELECT * FROM skill_evaluations WHERE skill_id=? AND version=? ORDER BY id DESC LIMIT 1",
            (skill_id, version),
        ).fetchone()
        return dict(row) if row else None

    def evaluate(self, skill_id: str, version: int, cases: list[dict]) -> dict:
        lock = self.store.acquire_named_lock("skill", skill_id)
        if lock is None:
            raise ValueError("skill is being changed by another process")
        try:
            return self._evaluate_locked(skill_id, version, cases)
        finally:
            self.store.release_task_lock(lock)

    def _evaluate_locked(self, skill_id: str, version: int, cases: list[dict]) -> dict:
        row = self._row(skill_id, version)
        if row["status"] != "candidate":
            raise ValueError("evaluate a new candidate; admitted evaluation evidence is immutable")
        spec = json.loads(row["spec_json"])
        if not isinstance(cases, list) or not 2 <= len(cases) <= 50:
            raise ValueError("evaluation needs two to fifty distinct input cases")
        ids, input_hashes = set(), set()
        for case in cases:
            if not isinstance(case, dict) or set(case) - {"id", "inputs", "expect", "request_id"} or not {"id", "inputs", "expect"} <= set(case):
                raise ValueError("each case needs id, inputs, expect and optional recorded request_id")
            if not isinstance(case["id"], str) or not case["id"] or case["id"] in ids:
                raise ValueError("case IDs must be unique non-empty strings")
            ids.add(case["id"])
            inputs = validate_inputs(spec, case["inputs"])
            input_hashes.add(digest(inputs))
            validate_outcome(case["expect"])
            # Catch invalid case bindings before running ANY case.
            plan = instantiate(spec, inputs, "evaluation-preview")
            preview = Engine(self.store, self.adapters).preflight(plan)
            if not preview["allowed"]:
                raise ValueError("evaluation plan failed preflight: " + canonical(preview["checks"]))
            if "request_id" in case:
                recorded = self.store.db.execute("SELECT * FROM skill_executions WHERE request_id=?", (case["request_id"],)).fetchone()
                if not recorded or recorded["skill_id"] != skill_id or recorded["version"] != version or recorded["inputs_hash"] != digest({"skill": row["content_hash"], "inputs": inputs}) or not recorded["result_json"]:
                    raise ValueError("recorded evidence must belong to this exact version and inputs and have a final result")
            elif any(check["required_level"] >= int(Authority.LOCAL) for check in preview["checks"]):
                raise ValueError("evaluation never repeats mutations; supply recorded request_id evidence from explicit trial calls")
        if len(input_hashes) < 2:
            raise ValueError("evaluation needs at least two distinct input sets")
        def criteria(case):
            return {k: v for k, v in case.items() if k != "request_id"}
        previous = [self._latest_evaluation(skill_id, version)]
        if row["parent"] is not None:
            previous.append(self._latest_evaluation(skill_id, row["parent"]))
        for parent in filter(None, previous):
            old = {c["id"]: criteria(c) for c in json.loads(parent["suite_json"])}
            new = {c["id"]: criteria(c) for c in cases}
            if any(key not in new or canonical(new[key]) != canonical(case) for key, case in old.items()):
                raise ValueError("evaluation must retain every unchanged regression case")
        evaluation_id = "evaluation-" + uuid.uuid4().hex
        results = []
        for index, case in enumerate(cases):
            if "request_id" in case:
                execution = json.loads(self.store.db.execute("SELECT result_json FROM skill_executions WHERE request_id=?", (case["request_id"],)).fetchone()[0])
            else:
                execution = self._execute(row, case["inputs"], f"{evaluation_id}:{index}")
            success = execution["status"] in {"completed", "completed_slow"}
            matched, reason = verify_expectation(execution.get("outputs", {}), case["expect"])
            results.append({"case_id": case["id"], "task_id": execution["task_id"],
                            "passed": success and matched, "status": execution["status"],
                            "reason": reason if success else "execution did not complete",
                            "outputs": execution.get("outputs", {}),
                            "elapsed_ms": execution.get("elapsed_ms")})
        report = {"id": evaluation_id, "skill_id": skill_id, "version": version,
                  "total": len(cases), "passed": sum(r["passed"] for r in results), "results": results}
        with self.store.db:
            self.store.db.execute(
                "INSERT INTO skill_evaluations(skill_id,version,content_hash,suite_json,report_json,created_at) VALUES (?,?,?,?,?,?)",
                (skill_id, version, row["content_hash"], canonical(cases), canonical(report), utc_now()),
            )
        return report

    def promote(self, skill_id: str, version: int) -> dict:
        lock = self.store.acquire_named_lock("skill", skill_id)
        if lock is None:
            raise ValueError("skill is being changed by another process")
        try:
            row = self._row(skill_id, version)
            if row["status"] != "candidate":
                raise ValueError("only a candidate can be promoted")
            evaluation = self._latest_evaluation(skill_id, version)
            if not evaluation or evaluation["content_hash"] != row["content_hash"]:
                raise ValueError("candidate needs an evaluation for this exact content")
            report = json.loads(evaluation["report_json"])
            if report["passed"] != report["total"] or report["total"] < 2:
                raise ValueError("all evaluation cases must pass before promotion")
            active = self.store.db.execute("SELECT version FROM skill_versions WHERE skill_id=? AND status='active'", (skill_id,)).fetchone()
            ancestor = row["parent"]
            while ancestor is not None:
                parent = self._row(skill_id, ancestor)
                if parent["status"] in {"active", "retired"}:
                    break
                ancestor = parent["parent"]
            if active and active["version"] != ancestor:
                raise ValueError("active parent changed; revise and evaluate against the current parent")
            with self.store.db:
                self.store.db.execute("UPDATE skill_versions SET status='retired' WHERE skill_id=? AND status='active'", (skill_id,))
                self.store.db.execute("UPDATE skill_versions SET status='active' WHERE skill_id=? AND version=?", (skill_id, version))
            return self.export(skill_id, version)
        finally:
            self.store.release_task_lock(lock)

    def diagnose(self, task_id: str) -> dict:
        status = self.store.task_status(task_id)
        events = []
        for row in self.store.events(task_id):
            events.append({"step": row["step_index"], "adapter": row["adapter"], "verb": row["verb"],
                           "status": row["status"], "verified": bool(row["verified"]),
                           "args": json.loads(row["args_json"]), "observed": json.loads(row["result_json"])})
        failed = next((event["step"] for event in events if event["status"] != "success"), None)
        return {"task_id": task_id, "status": status["status"], "failed_step": failed,
                "events": events, "instruction": "Diagnose from observed evidence. Separate environment failure from skill failure. Propose a new version; never overwrite the admitted skill."}
