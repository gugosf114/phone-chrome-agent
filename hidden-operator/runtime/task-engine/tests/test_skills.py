from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from agent_bridge_task.adapters import AdapterResult, NoopAdapter
from agent_bridge_task.store import Store

try:
    from agent_bridge_task.skills import SkillLibrary
except ImportError:
    SkillLibrary = None


def specification():
    return {
        "id": "echo-value",
        "description": "Read back a value for later composition",
        "tags": ["read", "value"],
        "inputs": {"value": {"type": "string"}},
        "plan": {
            "task": {"goal": "Read {{value}}"},
            "steps": [{"adapter": "noop", "verb": "read", "target": "fixture:record",
                       "args": {"value": {"$input": "value"}},
                       "expect": {"equals": {"value": {"$input": "value"}}}}],
        },
        "outputs": {"value": "0.value"},
    }


def cases():
    return [
        {"id": "first", "inputs": {"value": "alpha"}, "expect": {"equals": {"value": "alpha"}}},
        {"id": "second", "inputs": {"value": "beta"}, "expect": {"equals": {"value": "beta"}}},
    ]


class SkillsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(SkillLibrary, "the executable learning library is missing")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / "state.sqlite3")
        self.addCleanup(self.store.close)
        self.library = SkillLibrary(self.store, {"noop": NoopAdapter()})

    def admit(self, spec=None):
        candidate = self.library.propose(spec or specification())
        self.library.evaluate(candidate["id"], candidate["version"], cases())
        return self.library.promote(candidate["id"], candidate["version"])

    def test_new_inputs_execute_and_outputs_come_from_recorded_results(self):
        self.admit()
        result = self.library.execute("echo-value", {"value": "unseen"}, "request-1")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["outputs"], {"value": "unseen"})
        events = self.store.events(result["task_id"])
        self.assertEqual(json.loads(events[0]["result_json"])["value"], "unseen")

    def test_identical_request_returns_same_task_without_repeating_work(self):
        self.admit()
        first = self.library.execute("echo-value", {"value": "once"}, "request-1")
        second = self.library.execute("echo-value", {"value": "once"}, "request-1")
        self.assertEqual(first, second)
        self.assertEqual(len(self.store.events(first["task_id"])), 1)
        with self.assertRaisesRegex(ValueError, "different"):
            self.library.execute("echo-value", {"value": "different"}, "request-1")

    def test_candidates_cannot_be_used_as_admitted_skills(self):
        candidate = self.library.propose(specification())
        with self.assertRaisesRegex(ValueError, "admitted|active"):
            self.library.execute("echo-value", {"value": "x"}, "unproven", version=candidate["version"])

    def test_one_case_or_two_identical_inputs_cannot_establish_reuse(self):
        self.library.propose(specification())
        with self.assertRaisesRegex(ValueError, "distinct|two"):
            self.library.evaluate("echo-value", 1, cases()[:1])
        repeated = [cases()[0], {**cases()[0], "id": "duplicate"}]
        with self.assertRaisesRegex(ValueError, "distinct"):
            self.library.evaluate("echo-value", 1, repeated)

    def test_wrong_independent_outcome_prevents_promotion(self):
        self.library.propose(specification())
        wrong = cases()
        wrong[1]["expect"]["equals"]["value"] = "not beta"
        report = self.library.evaluate("echo-value", 1, wrong)
        self.assertEqual(report["passed"], 1)
        with self.assertRaisesRegex(ValueError, "evaluation|pass"):
            self.library.promote("echo-value", 1)

    def test_revision_does_not_replace_working_version_until_it_passes(self):
        self.admit()
        spec = specification()
        spec["plan"]["steps"][0]["args"]["value"] = "broken"
        candidate = self.library.propose(spec, parent=1)
        self.assertEqual(candidate["version"], 2)
        self.assertEqual(self.library.catalog()[0]["version"], 1)
        result = self.library.execute("echo-value", {"value": "works"}, "old-still-active")
        self.assertEqual(result["outputs"]["value"], "works")

    def test_revision_cannot_drop_or_rewrite_parent_regression_cases(self):
        self.admit()
        self.library.propose(specification(), parent=1)
        reduced = cases()
        reduced[0]["inputs"]["value"] = "replacement"
        with self.assertRaisesRegex(ValueError, "regression"):
            self.library.evaluate("echo-value", 2, reduced)

    def test_promotion_is_atomic_and_old_version_remains_exportable(self):
        self.admit()
        spec = specification()
        spec["description"] = "Improved description"
        self.library.propose(spec, parent=1)
        self.library.evaluate("echo-value", 2, cases())
        self.library.promote("echo-value", 2)
        self.assertEqual(self.library.catalog()[0]["version"], 2)
        self.assertEqual(self.library.export("echo-value", 1)["spec"]["description"], specification()["description"])

    def test_unknown_missing_or_wrong_typed_inputs_fail_before_execution(self):
        self.admit()
        for inputs in [{}, {"value": 4}, {"value": "x", "other": True}]:
            with self.subTest(inputs=inputs), self.assertRaises(ValueError):
                self.library.execute("echo-value", inputs, "invalid-" + str(inputs))

    def test_structured_parameter_binding_keeps_types_and_literal_shell_characters(self):
        spec = specification()
        spec["inputs"]["value"] = {"type": "array"}
        spec["plan"]["task"]["goal"] = "Read values"
        self.library.propose(spec)
        suite = [
            {"id": "a", "inputs": {"value": [1, "x"]}, "expect": {"equals": {"value": [1, "x"]}}},
            {"id": "b", "inputs": {"value": [2]}, "expect": {"equals": {"value": [2]}}},
        ]
        self.library.evaluate("echo-value", 1, suite)
        self.library.promote("echo-value", 1)
        result = self.library.execute("echo-value", {"value": [3, "$(anything); 'quoted'\nnext"]}, "array")
        self.assertEqual(result["outputs"]["value"], [3, "$(anything); 'quoted'\nnext"])

    def test_mutating_the_callers_spec_cannot_change_a_stored_version(self):
        spec = specification()
        self.library.propose(spec)
        spec["plan"]["steps"][0]["verb"] = "fail"
        self.assertEqual(self.library.export("echo-value", 1)["spec"]["plan"]["steps"][0]["verb"], "read")

    def test_source_tasks_are_validated_and_diagnosis_contains_actual_failure(self):
        with self.assertRaises(KeyError):
            self.library.propose(specification(), sources=["invented-task"])
        spec = specification()
        spec["plan"]["steps"][0]["verb"] = "fail"
        spec["plan"]["steps"][0]["args"]["message"] = "control was disabled"
        self.library.propose(spec)
        report = self.library.evaluate("echo-value", 1, cases())
        brief = self.library.diagnose(report["results"][0]["task_id"])
        self.assertIn("control was disabled", json.dumps(brief))
        self.assertEqual(brief["failed_step"], 0)

    def test_unfinished_claim_is_unknown_and_never_redispatched(self):
        self.admit()
        class PowerLoss(BaseException):
            pass
        class Interrupted(NoopAdapter):
            def execute(self, step):
                raise PowerLoss()
        self.library.adapters["noop"] = Interrupted()
        with self.assertRaises(PowerLoss):
            self.library.execute("echo-value", {"value": "x"}, "interrupted")
        self.library.adapters["noop"] = NoopAdapter()
        result = self.library.execute("echo-value", {"value": "x"}, "interrupted")
        self.assertEqual(result["status"], "outcome_unknown")
        self.assertEqual(self.store.events(result["task_id"]), [])

    def test_secret_literals_and_undeclared_parameters_are_rejected(self):
        spec = specification()
        spec["plan"]["steps"][0]["args"]["password"] = "must-not-store"
        with self.assertRaises(ValueError):
            self.library.propose(spec)
        spec = specification()
        spec["plan"]["steps"][0]["args"]["value"] = {"$input": "unknown"}
        with self.assertRaises(ValueError):
            self.library.propose(spec)

    def test_empty_outcome_assertions_cannot_admit_a_skill(self):
        self.library.propose(specification())
        bad = cases()
        for case in bad:
            case["expect"] = {"exit_code": 0}
        with self.assertRaisesRegex(ValueError, "outcome|expect"):
            self.library.evaluate("echo-value", 1, bad)

    def test_evaluation_never_repeats_mutations_and_can_use_recorded_trials(self):
        spec = specification()
        spec["plan"]["steps"][0]["verb"] = "external"
        self.library.propose(spec)
        with self.assertRaisesRegex(ValueError, "recorded|trial"):
            self.library.evaluate("echo-value", 1, cases())
        recorded = cases()
        for index, case in enumerate(recorded):
            request_id = "explicit-trial-" + str(index)
            result = self.library.trial("echo-value", 1, case["inputs"], request_id)
            self.assertEqual(result["status"], "completed")
            case["request_id"] = request_id
        report = self.library.evaluate("echo-value", 1, recorded)
        self.assertEqual(report["passed"], 2)
        self.library.promote("echo-value", 1)

    def test_recorded_evaluation_cannot_borrow_another_versions_success(self):
        self.admit()
        self.library.execute("echo-value", {"value": "alpha"}, "old-proof")
        self.library.propose(specification(), parent=1)
        recorded = cases()
        recorded[0]["request_id"] = "old-proof"
        recorded[1]["request_id"] = "invented"
        with self.assertRaisesRegex(ValueError, "recorded|version|evidence"):
            self.library.evaluate("echo-value", 2, recorded)

    def test_failed_candidate_can_be_revised_without_discarding_its_test(self):
        broken = specification()
        broken["plan"]["steps"][0]["args"]["value"] = "broken"
        self.library.propose(broken)
        self.assertEqual(self.library.evaluate("echo-value", 1, cases())["passed"], 0)
        revised = self.library.propose(specification(), parent=1)
        self.assertEqual(revised["version"], 2)
        self.assertEqual(self.library.evaluate("echo-value", 2, cases())["passed"], 2)
        self.assertEqual(self.library.promote("echo-value", 2)["status"], "active")

    def test_ambiguous_adapter_result_remains_unknown_to_the_caller(self):
        self.admit()
        class Ambiguous(NoopAdapter):
            def execute(self, step):
                return AdapterResult(False, False, {"outcome": "unknown", "dispatched": None})
        self.library.adapters["noop"] = Ambiguous()
        result = self.library.execute("echo-value", {"value": "x"}, "lost-reply")
        self.assertEqual(result["status"], "outcome_unknown")


if __name__ == "__main__":
    unittest.main()
