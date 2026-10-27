import json
import sys
import tempfile
import unittest
from pathlib import Path

from agent_bridge_task.models import Step, Authority

try:
    from agent_bridge_task.toolkit_adapter import ToolkitAdapter
except ImportError:
    ToolkitAdapter = None


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ToolkitAdapter, "toolkit task adapter is missing")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        fixture = Path(self.tmp.name) / "tool.py"
        fixture.write_text("import json,sys\nprint(json.dumps({'arguments':sys.argv[1:]}))\nsys.exit(7 if 'fail' in sys.argv else 0)\n")
        self.adapter = ToolkitAdapter(dispatcher=[sys.executable, str(fixture)])

    def test_exact_arguments_and_json_output_are_preserved(self):
        value = "quote ' and $(literal)\nnext"
        step = Step("toolkit", "run", "toolkit:jobs", {"arguments": ["find", value]},
                    {"equals": {"payload.arguments.2": value}})
        result = self.adapter.execute(step)
        self.assertTrue(result.verified)
        self.assertEqual(result.data["payload"]["arguments"], ["jobs", "find", value])

    def test_process_failure_cannot_be_verified_success(self):
        result = self.adapter.execute(Step("toolkit", "run", "toolkit:jobs", {"arguments": ["fail"]},
                                          {"contains": {"stdout": "fail"}}))
        self.assertFalse(result.ok)
        self.assertFalse(result.verified)

    def test_reads_are_classified_from_actual_tool_command(self):
        self.assertEqual(self.adapter.required_authority(Step("toolkit", "run", "toolkit:jobs", {"arguments": ["find"]})), Authority.READ)
        self.assertEqual(self.adapter.required_authority(Step("toolkit", "run", "toolkit:jobs", {"arguments": ["approve-and-submit", "x"]})), Authority.FULL)

    def test_recursive_learning_commands_and_shell_strings_are_rejected(self):
        for target, arguments in [("toolkit:learn", ["execute"]), ("toolkit:jobs", "find; anything")]:
            with self.assertRaises(ValueError):
                self.adapter.bind(Step("toolkit", "run", target, {"arguments": arguments}))


if __name__ == "__main__":
    unittest.main()
