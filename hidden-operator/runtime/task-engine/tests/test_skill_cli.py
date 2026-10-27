import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from agent_bridge_task.adapters import NoopAdapter
from agent_bridge_task.adapters import AdapterResult
from test_skills import specification, cases

try:
    from agent_bridge_task.skill_cli import main
except ImportError:
    main = None


class SkillCliTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(main, "learning CLI is missing")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = str(Path(self.tmp.name) / "skills.sqlite3")

    def call(self, request):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--db", self.db, "request", "--json", json.dumps(request)],
                        adapters={"noop": NoopAdapter()})
        return code, json.loads(output.getvalue())

    def test_full_propose_evaluate_promote_execute_protocol(self):
        code, result = self.call({"operation": "propose", "spec": specification()})
        self.assertEqual(code, 0)
        self.assertEqual(result["version"], 1)
        code, result = self.call({"operation": "evaluate", "id": "echo-value", "version": 1, "cases": cases()})
        self.assertEqual((code, result["passed"]), (0, 2))
        self.assertEqual(self.call({"operation": "promote", "id": "echo-value", "version": 1})[0], 0)
        code, result = self.call({"operation": "execute", "id": "echo-value", "inputs": {"value": "new"}, "request_id": "new-request"})
        self.assertEqual(code, 0)
        self.assertEqual(result["outputs"]["value"], "new")

    def test_failed_evaluation_has_nonzero_exit_and_machine_readable_result(self):
        self.call({"operation": "propose", "spec": specification()})
        suite = cases()
        suite[0]["expect"]["equals"]["value"] = "wrong"
        code, result = self.call({"operation": "evaluate", "id": "echo-value", "version": 1, "cases": suite})
        self.assertNotEqual(code, 0)
        self.assertEqual(result["passed"], 1)

    def test_malformed_requests_return_structured_errors(self):
        for request in [{"operation": "invented"}, {"operation": "execute", "id": "missing"}, []]:
            code, result = self.call(request)
            self.assertEqual(code, 2)
            self.assertIn("error", result)

    def test_schema_exposes_actual_operations_and_example(self):
        code, result = self.call({"operation": "schema"})
        self.assertEqual(code, 0)
        self.assertIn("propose", result["operations"])
        self.assertIn("trial", result["operations"])
        self.assertIn("inputs", result["skill_example"])

    def test_observation_can_filter_and_page_large_trees(self):
        from agent_bridge_task.skill_cli import dispatch
        from agent_bridge_task.skills import SkillLibrary
        from agent_bridge_task.store import Store
        class Reader:
            def execute(self, step):
                return AdapterResult(True, True, {"screen": {"revision": 9, "nodes": [
                    {"token": "0", "text": "Search", "package": "other"},
                    {"token": "1", "text": "Search results", "package": "app"},
                    {"token": "2", "text": "Search again", "package": "app"}], "text": "all"}})
        store = Store(self.db)
        try:
            result = dispatch(SkillLibrary(store, {"hidden": Reader()}), {
                "operation": "observe", "package": "app", "query": "search", "offset": 1, "limit": 1})
        finally:
            store.close()
        self.assertEqual([node["token"] for node in result["screen"]["nodes"]], ["2"])
        self.assertEqual(result["screen"]["matched_nodes"], 2)


if __name__ == "__main__":
    unittest.main()
