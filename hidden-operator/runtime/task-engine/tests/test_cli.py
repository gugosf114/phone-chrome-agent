from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from agent_bridge_task.adapters import NoopAdapter
from agent_bridge_task.cli import main


class CliTests(unittest.TestCase):
    def test_race_clock_can_start_before_plan_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "state.sqlite3")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--db", database, "race-start", "--goal", "new task"])
            started = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(started["goal"], "new task")
            self.assertIsNone(started["claimed_by"])

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--db", database, "race-status", started["id"]])
            shown = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(shown["id"], started["id"])

    def benchmark(self, delay_ms: int, baseline_ms: int) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = root / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "task": {
                            "goal": "timed noop",
                            "permission": {
                                "authority": "read",
                                "scope": {"kind": "test"},
                                "targets": ["test:*"],
                            },
                            "baseline_ms": baseline_ms,
                        },
                        "steps": [
                            {
                                "adapter": "noop",
                                "verb": "read",
                                "target": "test:item",
                                "args": {"delay_ms": delay_ms},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(
                    [
                        "--db",
                        str(root / "state.sqlite3"),
                        "benchmark",
                        str(plan),
                        "--warmup",
                        "0",
                        "--runs",
                        "2",
                    ],
                    adapters={"noop": NoopAdapter()},
                )
            return code, json.loads(output.getvalue())

    def test_speed_miss_is_not_reported_as_a_win(self) -> None:
        code, result = self.benchmark(delay_ms=15, baseline_ms=1)
        self.assertEqual(code, 4)
        self.assertEqual(result["status"], "completed_slow")
        self.assertEqual(result["speed_passes"], 0)

    def test_fast_benchmark_returns_success(self) -> None:
        code, result = self.benchmark(delay_ms=0, baseline_ms=100)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["speed_passes"], 2)

    def test_benchmark_rejects_external_steps_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = root / "external.json"
            plan.write_text(
                json.dumps(
                    {
                        "task": {
                            "goal": "must run once",
                            "permission": {
                                "authority": "full",
                                "scope": {"kind": "test"},
                                "targets": ["test:*"],
                            },
                        },
                        "steps": [
                            {
                                "adapter": "noop",
                                "verb": "external",
                                "target": "test:item",
                                "expect": {"equals": {"verb": "external"}},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(
                    [
                        "--db",
                        str(root / "state.sqlite3"),
                        "benchmark",
                        str(plan),
                        "--runs",
                        "2",
                    ],
                    adapters={"noop": NoopAdapter()},
                )
            result = json.loads(output.getvalue())
            self.assertEqual(code, 2)
            self.assertIn("read-only", result["error"])
            database = root / "state.sqlite3"
            self.assertNotIn(b"bench-", database.read_bytes())


if __name__ == "__main__":
    unittest.main()
