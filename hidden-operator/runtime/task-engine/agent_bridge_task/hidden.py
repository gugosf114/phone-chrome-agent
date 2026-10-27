"""Fresh hidden-display observations and one-shot semantic accessibility actions."""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import time
import uuid
from collections import Counter
from pathlib import Path

from .adapters import AdapterResult, verify_expectation
from .models import Authority, Step

DISPLAY = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")


def project_root() -> Path:
    configured = os.environ.get("AGENT_BRIDGE_ROOT")
    if configured:
        return Path(configured)
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts" / "authority_core.sh").is_file():
            return parent
    raise ValueError("AGENT_BRIDGE_ROOT must point to the Agent Bridge checkout")


class AdbDevice:
    def __init__(self):
        self.adb = shlex.split(os.environ.get("ADB", "adb"))

    def _shell(self, command: str, payload: str | None = None, timeout: float = 8) -> str:
        result = subprocess.run([*self.adb, "shell", command], input=payload, text=True,
                                capture_output=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError("ADB command failed: " + result.stderr[:300])
        return result.stdout.replace("\r\n", "\n")

    def observe(self, name: str) -> dict:
        path = shlex.quote(f"/data/local/tmp/vd/{name}/snapshot.json")
        value = self._shell("printf '{\"now_ms\":%s,\"snapshot\":' \"$(date +%s%3N)\"; cat " + path + "; printf '}'")
        return json.loads(value)

    def action(self, name: str, request: dict) -> dict:
        request_id = uuid.uuid4().hex
        folder = f"/data/local/tmp/vd/{name}"
        temporary = shlex.quote(f"{folder}/.{request_id}.tmp")
        command = shlex.quote(f"{folder}/request-{request_id}.json")
        response = shlex.quote(f"{folder}/response-{request_id}.json")
        payload = {**request, "request_id": request_id}
        # The text travels on stdin, not inside a shell command.
        self._shell(f"cat > {temporary} && mv {temporary} {command}", json.dumps(payload, ensure_ascii=False))
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            raw = self._shell(f"if [ -f {response} ]; then cat {response}; rm -f {response}; fi")
            if raw.strip():
                return json.loads(raw)
            time.sleep(0.1)
        return {"ok": False, "dispatched": None, "error": "action reply timed out; outcome unknown"}

    def open(self, name: str, app: str) -> dict:
        script = str(project_root() / "scripts" / "hidden_display.sh")
        for arguments in (["start", "-n", name, "phone"], ["launch", "-n", name, app]):
            result = subprocess.run(["bash", script, *arguments], capture_output=True, text=True, timeout=25)
            if result.returncode:
                return {"ok": False, "dispatched": None, "error": "hidden app launch failed"}
        return {"ok": True, "dispatched": True}


class HiddenAdapter:
    VERBS = {"observe", "open", "click", "set_text", "scroll_forward", "scroll_backward"}

    def __init__(self, device=None):
        self.device = device or AdbDevice()

    @staticmethod
    def bind(step: Step) -> Step:
        if not step.target.startswith("hidden:") or not DISPLAY.fullmatch(step.target[7:]):
            raise ValueError("hidden target needs a simple named display: hidden:main")
        if step.verb not in HiddenAdapter.VERBS:
            raise ValueError("unsupported hidden-display action")
        return step

    @staticmethod
    def exclusive_resources(step: Step) -> tuple[str, ...]:
        resources = [step.target]
        if step.args.get("package"):
            resources.append("android-app:" + str(step.args["package"]))
        return tuple(resources)

    def required_authority(self, step: Step) -> Authority:
        self.bind(step)
        return Authority.READ if step.verb == "observe" else Authority.EXTERNAL

    @staticmethod
    def validate_postcondition(step: Step) -> None:
        if not step.expect or set(step.expect) - {"equals", "contains"}:
            raise ValueError("hidden action needs a screen postcondition")
        meaningful = False
        for operation, checks in step.expect.items():
            if not isinstance(checks, dict):
                raise ValueError("screen postcondition must be a field map")
            for key, wanted in checks.items():
                if not key.startswith("screen.") or key in {"screen.revision", "screen.generation", "screen.display_id", "screen.observed_at_ms"}:
                    raise ValueError("postcondition must describe actual screen content")
                if operation == "contains" and wanted in (None, ""):
                    raise ValueError("screen contains expectation cannot be empty")
                meaningful = True
        if not meaningful:
            raise ValueError("hidden action needs a screen postcondition")

    def _observe(self, name: str) -> tuple[dict, int]:
        envelope = self.device.observe(name)
        snapshot = envelope["snapshot"]
        age = int(envelope["now_ms"]) - int(snapshot["observed_at_ms"])
        if not snapshot.get("valid") or not 0 <= age <= 2500:
            raise ValueError("hidden screen is invalid or stale; refresh the reader before acting")
        if int(snapshot["display_id"]) <= 0:
            raise ValueError("hidden actions cannot target the physical display")
        if not snapshot.get("generation") or "revision" not in snapshot:
            raise ValueError("reader does not implement versioned observations; rebuild ud.dex")
        nodes = snapshot.get("nodes", [])
        packages = Counter(n.get("package", "") for n in nodes if n.get("visible") and n.get("package") not in {"android", "com.android.systemui", "com.sec.android.app.launcher"})
        snapshot["package"] = packages.most_common(1)[0][0] if packages else ""
        snapshot["text"] = "\n".join(n["text"] for n in nodes if n.get("visible") and n.get("text"))
        return snapshot, int(envelope["now_ms"])

    @staticmethod
    def _resolve(snapshot: dict, step: Step) -> dict:
        selector = step.args.get("selector")
        package = step.args.get("package")
        if not isinstance(package, str) or not package:
            raise ValueError("hidden mutation needs an exact package")
        if not isinstance(selector, dict) or not selector or set(selector) - {"text", "description", "resource_id", "token"}:
            raise ValueError("selector must name text, description, resource_id or token")
        if not all(isinstance(v, str) and v for v in selector.values()):
            raise ValueError("selector values must be non-empty strings")
        action_field = {"click": "clickable", "set_text": "editable",
                        "scroll_forward": "scrollable", "scroll_backward": "scrollable"}[step.verb]
        found = [n for n in snapshot["nodes"] if n.get("package") == package and n.get("visible")
                 and n.get("enabled") and n.get(action_field) and all(n.get(k) == v for k, v in selector.items())]
        if len(found) != 1:
            raise ValueError(f"selector matched {len(found)} enabled visible nodes; need exactly one")
        return found[0]

    def execute(self, step: Step) -> AdapterResult:
        dispatched = False
        try:
            self.bind(step)
            name = step.target[7:]
            if step.verb == "observe":
                snapshot, _ = self._observe(name)
                data = {"screen": snapshot}
                matched, reason = verify_expectation(data, step.expect)
                return AdapterResult(True, matched, {**data, "verification": reason})
            self.validate_postcondition(step)
            wait_ms = int(step.args.get("wait_ms", 4000))
            if not 0 <= wait_ms <= 15000:
                raise ValueError("wait_ms must be between 0 and 15000")
            before = None
            if step.verb == "open":
                app = step.args.get("app", "")
                if not isinstance(app, str) or not re.fullmatch(r"[A-Za-z0-9_.$]+(?:/[A-Za-z0-9_.$]+)?", app):
                    raise ValueError("open needs an exact Android package or component")
                dispatched = None
                reply = self.device.open(name, app)
            else:
                before, now = self._observe(name)
                node = self._resolve(before, step)
                request = {"action": step.verb, "token": node["token"], "package": step.args["package"],
                           "display_id": before["display_id"], "generation": before["generation"],
                           "revision": before["revision"], "deadline_ms": now + 4000}
                if step.verb == "set_text":
                    text = step.args.get("text")
                    if not isinstance(text, str) or len(text) > 100000:
                        raise ValueError("set_text needs a string of at most 100000 characters")
                    request["text"] = text
                dispatched = None
                reply = self.device.action(name, request)
            dispatched = reply.get("dispatched")
            if not reply.get("ok"):
                return AdapterResult(False, False, {**reply, "outcome": "not_dispatched" if dispatched is False else "unknown"})
            deadline = time.monotonic() + wait_ms / 1000
            data = {"dispatched": dispatched}
            while True:
                try:
                    after, _ = self._observe(name)
                    data["screen"] = after
                    if before and (after["generation"] != before["generation"] or after["display_id"] != before["display_id"]):
                        return AdapterResult(True, False, {**data, "outcome": "unknown", "error": "display changed after action"})
                    newer = before is None or after["observed_at_ms"] > before["observed_at_ms"]
                    matched, reason = verify_expectation(data, step.expect)
                    if newer and matched:
                        return AdapterResult(True, True, {**data, "verification": reason})
                except (ValueError, KeyError, OSError, RuntimeError) as error:
                    data["error"] = str(error)
                if time.monotonic() >= deadline:
                    return AdapterResult(True, False, {**data, "outcome": "unknown", "verification": "expected fresh screen result was not observed"})
                time.sleep(0.15)
        except (ValueError, KeyError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            return AdapterResult(False, False, {"error": str(error), "dispatched": dispatched,
                                                "outcome": "not_dispatched" if dispatched is False else "unknown"})
