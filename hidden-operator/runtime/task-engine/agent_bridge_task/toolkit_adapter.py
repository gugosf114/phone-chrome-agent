"""Execute existing bridge tools with an exact argv and observed output."""
from __future__ import annotations

import json
import subprocess

from .adapters import AdapterResult, verify_expectation
from .hidden import project_root
from .models import Authority, Step


class ToolkitAdapter:
    TOOLS = {"web", "browser", "google", "jobs", "linkedin", "gmail", "play", "pinterest", "desktop"}

    def __init__(self, dispatcher=None):
        self.dispatcher = dispatcher

    def bind(self, step: Step) -> Step:
        if step.verb != "run" or not step.target.startswith("toolkit:") or step.target[8:] not in self.TOOLS:
            raise ValueError("unsupported toolkit target or recursive command")
        args = step.args.get("arguments")
        if not isinstance(args, list) or not args or not all(isinstance(x, str) for x in args):
            raise ValueError("toolkit arguments must be a non-empty string array")
        timeout = step.args.get("timeout_ms", 120000)
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 900000:
            raise ValueError("toolkit timeout_ms must be 1..900000")
        return step

    def required_authority(self, step: Step) -> Authority:
        self.bind(step)
        # Conservative read classification is used to avoid automatic mutation replay in evals.
        if step.target == "toolkit:jobs" and step.args["arguments"][0] in {"find", "status", "review"}:
            return Authority.READ
        return Authority.FULL

    @staticmethod
    def exclusive_resources(step: Step) -> tuple[str, ...]:
        return ("toolkit:operator",)

    def execute(self, step: Step) -> AdapterResult:
        try:
            self.bind(step)
            argv = self.dispatcher or ["bash", str(project_root() / "portable" / "toolkit-dispatch")]
            process = subprocess.run([*argv, step.target[8:], *step.args["arguments"]],
                                     text=True, capture_output=True,
                                     timeout=step.args.get("timeout_ms", 120000) / 1000)
            data = {"stdout": process.stdout, "stderr": process.stderr, "exit_code": process.returncode}
            try:
                data["payload"] = json.loads(process.stdout)
            except ValueError:
                data["payload"] = None
            matched, reason = verify_expectation(data, step.expect,
                                                 require_semantic=self.required_authority(step) >= Authority.LOCAL)
            data["verification"] = reason
            return AdapterResult(process.returncode == 0, process.returncode == 0 and matched, data)
        except (ValueError, OSError, subprocess.TimeoutExpired) as error:
            return AdapterResult(False, False, {"error": str(error), "outcome": "unknown"})
