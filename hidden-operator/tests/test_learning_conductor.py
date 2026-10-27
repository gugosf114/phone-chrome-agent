import base64
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import conductor_brain


class LearningConductorTests(unittest.TestCase):
    def test_learning_request_reaches_phone_as_exact_json_data(self):
        request = {"operation": "catalog", "query": "record\nGeorge's data"}
        result = subprocess.CompletedProcess([], 0, stdout='[{"id":"record-reader"}]', stderr="")
        with patch.object(conductor_brain.subprocess, "run", return_value=result) as run:
            text, done, _ = conductor_brain.exec_tool("learn", {"request": request})
        self.assertFalse(done)
        self.assertIn("record-reader", text)
        self.assertEqual(json.loads(text)[0]["id"], "record-reader")
        remote = run.call_args.args[0][-1]
        payload = json.loads(base64.b64decode(remote.rsplit(" ", 1)[-1]))
        self.assertEqual(payload["tool"], "learn")
        self.assertEqual(json.loads(payload["arguments"][-1]), request)

    def test_learning_json_is_not_cut_at_the_old_screen_limit(self):
        output = json.dumps({"evidence": "x" * 8000, "complete": True})
        result = subprocess.CompletedProcess([], 0, stdout=output, stderr="")
        with patch.object(conductor_brain.subprocess, "run", return_value=result):
            text = conductor_brain.run_toolkit("learn", ["schema"])
        self.assertEqual(text, output)


if __name__ == "__main__":
    unittest.main()
