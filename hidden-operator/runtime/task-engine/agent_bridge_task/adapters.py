from __future__ import annotations

import json
import http.client
import os
import re
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

from .models import BROWSER_BACKENDS, SECRET_REFERENCE_KEYS, Authority, Step


@dataclass(frozen=True)
class AdapterResult:
    ok: bool
    verified: bool
    data: dict[str, Any]


class Adapter(Protocol):
    def required_authority(self, step: Step) -> Authority: ...

    def execute(self, step: Step) -> AdapterResult: ...


LEVEL_VERBS = {
    "talk": Authority.TALK,
    "read": Authority.READ,
    "collect": Authority.COLLECT,
    "local": Authority.LOCAL,
    "external": Authority.EXTERNAL,
    "full": Authority.FULL,
}


def _field(data: Any, dotted: str) -> Any:
    value = data
    for part in dotted.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            raise KeyError(dotted)
    return value


def verify_expectation(
    data: dict[str, Any],
    expect: dict[str, Any],
    *,
    require_semantic: bool = False,
) -> tuple[bool, str]:
    if not expect:
        if require_semantic:
            return False, "mutation has no semantic postcondition"
        return True, "adapter completed"
    try:
        for dotted, wanted in expect.get("equals", {}).items():
            if _field(data, dotted) != wanted:
                return False, f"{dotted} did not equal {wanted!r}"
        for dotted, wanted in expect.get("contains", {}).items():
            if wanted == "" or wanted is None:
                return False, f"{dotted} used an empty contains expectation"
            if str(wanted) not in str(_field(data, dotted)):
                return False, f"{dotted} did not contain {wanted!r}"
    except KeyError as error:
        return False, f"result did not contain {error.args[0]!r}"
    return True, "expectation matched"


class NoopAdapter:
    """A real engine adapter used for dry runs and deterministic tests."""

    def required_authority(self, step: Step) -> Authority:
        if step.verb == "fail":
            return Authority(int(step.args.get("required_level", Authority.READ)))
        try:
            return LEVEL_VERBS[step.verb]
        except KeyError as error:
            raise ValueError(f"Unknown noop action {step.verb!r}.") from error

    def execute(self, step: Step) -> AdapterResult:
        delay_ms = int(step.args.get("delay_ms", 0))
        if delay_ms:
            time.sleep(delay_ms / 1000)
        if step.verb == "fail":
            return AdapterResult(
                False, False, {"error": step.args.get("message", "planned failure")}
            )
        data = {
            "adapter": "noop",
            "verb": step.verb,
            "target": step.target,
            "value": step.args.get("value"),
        }
        verified, reason = verify_expectation(
            data,
            step.expect,
            require_semantic=self.required_authority(step) >= Authority.LOCAL,
        )
        data["verification"] = reason
        return AdapterResult(True, verified, data)


class ProcessAdapter:
    """Runs an exact argv list without a shell inside an explicit process target."""

    def bind(self, step: Step) -> Step:
        argv = step.args.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or not isinstance(argv[0], str)
            or not all(
                isinstance(item, str)
                or (
                    isinstance(item, dict)
                    and len(item) == 1
                    and next(iter(item)) in SECRET_REFERENCE_KEYS
                )
                for item in argv[1:]
            )
        ):
            raise ValueError("process argv must be a non-empty string list")
        executable = shutil.which(argv[0])
        if executable is None:
            candidate = Path(argv[0]).expanduser()
            if not candidate.is_absolute():
                raise ValueError(f"process executable {argv[0]!r} was not found")
            executable = str(candidate)
        invoked_path = Path(os.path.abspath(executable))
        bound_args = dict(step.args)
        bound_args["argv"] = [str(invoked_path), *argv[1:]]
        return replace(step, target=f"process:{invoked_path}", args=bound_args)

    def required_authority(self, step: Step) -> Authority:
        if step.verb not in LEVEL_VERBS:
            raise ValueError(
                "Process actions must be talk, read, collect, local, external, or full."
            )
        # An arbitrary executable can read, write, send, or delete regardless of
        # its label. Treat it as full authority instead of trusting self-declared
        # command semantics.
        return Authority.FULL

    def execute(self, step: Step) -> AdapterResult:
        argv = step.args.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(item, str) for item in argv)
        ):
            return AdapterResult(
                False, False, {"error": "process argv must be a non-empty string list"}
            )
        timeout_ms = int(step.args.get("timeout_ms", 60_000))
        cwd = step.args.get("cwd")
        env = os.environ.copy()
        extra_env = step.args.get("env", {})
        if not isinstance(extra_env, dict):
            return AdapterResult(
                False, False, {"error": "process env must be an object"}
            )
        env.update({str(key): str(value) for key, value in extra_env.items()})
        try:
            result = subprocess.run(
                argv,
                cwd=Path(cwd) if cwd else None,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_ms / 1000,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return AdapterResult(False, False, {"error": str(error)})
        data: dict[str, Any] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        expected_exit = int(step.expect.get("exit_code", 0))
        ok = result.returncode == expected_exit
        verified, reason = verify_expectation(
            data,
            {key: value for key, value in step.expect.items() if key != "exit_code"},
            require_semantic=True,
        )
        data["verification"] = reason
        return AdapterResult(ok, ok and verified, data)


class GoogleConsoleAdapter:
    """Routes existing signed-in Google browser commands through the phone launcher."""

    @staticmethod
    def exclusive_resources(step: Step) -> tuple[str, ...]:
        return ("google-console:george",)

    @staticmethod
    def validate_postcondition(step: Step) -> None:
        raise ValueError(
            "google-console mutations are disabled until the runtime returns "
            "intrinsic post-action proof"
        )

    LEVELS = {
        "status": Authority.READ,
        "read": Authority.READ,
        "controls": Authority.READ,
        "frames": Authority.READ,
        "frame-controls": Authority.READ,
        "screenshot": Authority.COLLECT,
        "tabs": Authority.READ,
        "analytics-home": Authority.READ,
        "analytics-reports": Authority.READ,
        "analytics-explore": Authority.READ,
        "analytics-advertising": Authority.READ,
        "analytics-admin": Authority.READ,
        "search-overview": Authority.READ,
        "search-performance": Authority.READ,
        "search-pages": Authority.READ,
        "search-sitemaps": Authority.READ,
        "search-removals": Authority.READ,
        "search-links": Authority.READ,
        "search-settings": Authority.READ,
        "search-inspect": Authority.READ,
        "download": Authority.COLLECT,
        "open": Authority.LOCAL,
        "click": Authority.EXTERNAL,
        "fill": Authority.EXTERNAL,
        "select": Authority.EXTERNAL,
        "check": Authority.EXTERNAL,
        "uncheck": Authority.EXTERNAL,
        "press": Authority.EXTERNAL,
        "upload": Authority.EXTERNAL,
        "wait": Authority.READ,
        "reload": Authority.LOCAL,
        "back": Authority.LOCAL,
        "new-tab": Authority.LOCAL,
        "use-tab": Authority.LOCAL,
        "close-tab": Authority.LOCAL,
        "frame-click": Authority.EXTERNAL,
        "frame-fill": Authority.EXTERNAL,
        "search-request-indexing": Authority.EXTERNAL,
        "search-submit-sitemap": Authority.EXTERNAL,
        "eval": Authority.FULL,
        "frame-eval": Authority.FULL,
        "start": Authority.LOCAL,
        "stop": Authority.LOCAL,
    }

    def __init__(self, binary: str | None = None):
        self.binary = binary or os.environ.get(
            "GOOGLE_CONSOLE_BINARY", "google-console"
        )

    def bind(self, step: Step) -> Step:
        return replace(step, target="google-console:george")

    def required_authority(self, step: Step) -> Authority:
        try:
            return self.LEVELS[step.verb]
        except KeyError as error:
            raise ValueError(f"Unknown google-console action {step.verb!r}.") from error

    def execute(self, step: Step) -> AdapterResult:
        raw_arguments = step.args.get("arguments", [])
        if not isinstance(raw_arguments, list) or not all(
            isinstance(item, str) for item in raw_arguments
        ):
            return AdapterResult(
                False, False, {"error": "arguments must be a string list"}
            )
        timeout_ms = int(step.args.get("timeout_ms", 120_000))
        try:
            result = subprocess.run(
                [self.binary, step.verb, *raw_arguments],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_ms / 1000,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return AdapterResult(False, False, {"error": str(error)})
        try:
            payload: Any = json.loads(result.stdout) if result.stdout.strip() else {}
        except json.JSONDecodeError:
            payload = {"stdout": result.stdout}
        data = {
            "exit_code": result.returncode,
            "payload": payload,
            "stderr": result.stderr,
        }
        ok = result.returncode == int(step.expect.get("exit_code", 0))
        verified, reason = verify_expectation(
            data,
            {key: value for key, value in step.expect.items() if key != "exit_code"},
            require_semantic=self.required_authority(step) >= Authority.LOCAL,
        )
        data["verification"] = reason
        return AdapterResult(ok, ok and verified, data)


class McpHttpClient:
    """Small persistent Streamable HTTP MCP client for the phone control server."""

    def __init__(self, url: str, token: str, timeout_seconds: float = 30.0):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError(f"Invalid MCP URL: {url}")
        connection_type = (
            http.client.HTTPSConnection
            if parsed.scheme == "https"
            else http.client.HTTPConnection
        )
        self.connection = connection_type(
            parsed.hostname, parsed.port, timeout=timeout_seconds
        )
        self.path = parsed.path or "/"
        self.token = token
        self.session_id: str | None = None
        self.next_id = 1

    def _post(
        self, payload: dict[str, Any], include_session: bool = True
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if include_session and self.session_id:
            headers["mcp-session-id"] = self.session_id
        self.connection.request(
            "POST",
            self.path,
            body=json.dumps(payload, separators=(",", ":")),
            headers=headers,
        )
        response = self.connection.getresponse()
        body = response.read().decode("utf-8")
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"MCP HTTP {response.status}: {body[:500]}")
        received_session = response.getheader("mcp-session-id")
        if received_session:
            self.session_id = received_session
        if not body:
            return {}
        return json.loads(body)

    def initialize(self) -> None:
        if self.session_id:
            return
        request_id = self.next_id
        self.next_id += 1
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "agent-bridge", "version": "0.1.0"},
                },
            },
            include_session=False,
        )
        if "error" in response:
            raise RuntimeError(f"MCP initialize failed: {response['error']}")
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.initialize()
        request_id = self.next_id
        self.next_id += 1
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }
        )
        if "error" in response:
            return {"isError": True, "error": response["error"]}
        return response.get("result", {})


class PhoneMcpAdapter:
    """Calls George's already-paired no-ADB Android control server."""

    @staticmethod
    def exclusive_resources(step: Step) -> tuple[str, ...]:
        return ("phone:george",)

    @staticmethod
    def validate_postcondition(step: Step) -> None:
        raise ValueError(
            "phone mutations are disabled until Agent Bridge returns intrinsic "
            "post-action proof"
        )

    READ_ACTIONS = {
        "android_get_screen_state",
        "android_get_device_logs",
        "android_find_nodes",
        "android_get_node_details",
        "android_get_clipboard",
        "android_wait_for_node",
        "android_wait_for_idle",
        "android_list_storage_locations",
        "android_list_files",
        "android_read_file",
        "android_list_apps",
        "android_list_cameras",
        "android_list_camera_photo_resolutions",
        "android_list_camera_video_resolutions",
        "android_notification_list",
        "android_get_location",
    }
    COLLECT_ACTIONS = {
        "android_download_from_url",
        "android_take_camera_photo",
        "android_save_camera_photo",
        "android_save_camera_video",
    }
    EXTERNAL_ACTIONS = {
        "android_notification_action",
        "android_notification_reply",
    }
    FULL_ACTIONS = {
        "android_delete_file",
        "android_send_intent",
    }

    def __init__(
        self,
        client: McpHttpClient | None = None,
        url: str | None = None,
        token: str | None = None,
    ):
        self.client = client or McpHttpClient(
            url
            or os.environ.get("AGENT_BRIDGE_TASK_PHONE_MCP_URL", "http://127.0.0.1:8080/mcp"),
            token or os.environ.get("AGENT_BRIDGE_TASK_PHONE_MCP_TOKEN", "agentbridge-mcp"),
        )

    def bind(self, step: Step) -> Step:
        return replace(step, target="phone:george")

    def required_authority(self, step: Step) -> Authority:
        if step.verb in self.READ_ACTIONS:
            base = Authority.READ
        elif step.verb in self.COLLECT_ACTIONS:
            base = Authority.COLLECT
        elif step.verb in self.EXTERNAL_ACTIONS:
            base = Authority.EXTERNAL
        elif step.verb in self.FULL_ACTIONS:
            base = Authority.FULL
        elif step.verb.startswith("android_"):
            base = Authority.EXTERNAL
        else:
            raise ValueError(f"Unknown phone action {step.verb!r}.")
        effect = step.args.get("effect")
        if effect is None:
            return base
        requested = (
            Authority(int(effect))
            if isinstance(effect, int)
            else LEVEL_VERBS.get(str(effect))
        )
        if requested is None:
            raise ValueError(f"Unknown phone effect {effect!r}.")
        return max(base, requested)

    def execute(self, step: Step) -> AdapterResult:
        arguments = step.args.get(
            "arguments",
            {key: value for key, value in step.args.items() if key != "effect"},
        )
        if not isinstance(arguments, dict):
            return AdapterResult(
                False, False, {"error": "phone arguments must be an object"}
            )
        try:
            raw = self.client.call(step.verb, arguments)
        except (OSError, RuntimeError, json.JSONDecodeError) as error:
            return AdapterResult(False, False, {"error": str(error)})
        is_error = bool(raw.get("isError"))
        structured = raw.get("structuredContent")
        if structured is not None:
            payload: Any = structured
        else:
            payload = raw.get("content", raw)
            content = raw.get("content")
            if (
                isinstance(content, list)
                and len(content) == 1
                and isinstance(content[0], dict)
            ):
                text_value = content[0].get("text")
                if isinstance(text_value, str):
                    try:
                        payload = json.loads(text_value)
                    except json.JSONDecodeError:
                        payload = {"text": text_value}
        data = {"tool": step.verb, "payload": payload}
        verified, reason = verify_expectation(
            data,
            step.expect,
            require_semantic=self.required_authority(step) >= Authority.LOCAL,
        )
        data["verification"] = reason
        return AdapterResult(not is_error, not is_error and verified, data)


def canonical_browser_target(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"browser URL {url!r} must be absolute HTTP or HTTPS")
    if parsed.username or parsed.password:
        raise ValueError("browser URLs must not contain credentials")
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    port = parsed.port
    default_port = 443 if parsed.scheme == "https" else 80
    netloc = host if port in {None, default_port} else f"{host}:{port}"
    return f"browser:{parsed.scheme.lower()}://{netloc}"


def canonical_file_target(value: str, label: str = "browser source") -> str:
    try:
        path = Path(value).expanduser().resolve(strict=True)
    except OSError as error:
        raise ValueError(f"{label} file is unavailable: {value!r}: {error}") from error
    if not path.is_file():
        raise ValueError(f"{label} must be a regular file: {str(path)!r}")
    return f"file:{path}"


class BrowserRunnerClient:
    """Direct client for the authenticated job-browser daemon on this phone."""

    MAX_RESPONSE_BYTES = 16 * 1024 * 1024
    EXPECTED_PROTOCOL = "agent-bridge-browser-v2"

    def __init__(
        self,
        socket_path: str | Path | None = None,
        profile: str = "job-applications",
        *,
        backend: str,
        timeout_seconds: float = 3.0,
        cdp_endpoint: str | None = None,
    ):
        if backend not in BROWSER_BACKENDS:
            choices = ", ".join(sorted(BROWSER_BACKENDS))
            raise ValueError(f"browser backend must be one of: {choices}")
        self.socket_path = Path(
            socket_path
            or os.environ.get(
                "BROWSER_RUNNER_RPC_SOCKET",
                "/data/data/com.termux/files/home/.cache/browser-headless/browser-daemon.sock",
            )
        )
        self.profile = profile
        self.backend = backend
        self.timeout_seconds = timeout_seconds
        self.cdp_endpoint = cdp_endpoint

    def _request(self, request: dict[str, Any]) -> dict[str, Any]:
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(self.timeout_seconds)
        chunks: list[bytes] = []
        size = 0
        try:
            connection.connect(str(self.socket_path))
            connection.sendall(
                json.dumps(request, separators=(",", ":")).encode("utf-8") + b"\n"
            )
            # Once the daemon accepts a command, wait for its terminal result.
            # The daemon owns the 900-second action deadline; a client timeout
            # could otherwise report failure while a submission still succeeds.
            connection.settimeout(None)
            while True:
                chunk = connection.recv(65_536)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > self.MAX_RESPONSE_BYTES:
                    raise RuntimeError("browser runner response exceeded 16 MiB")
                if b"\n" in chunk:
                    break
        finally:
            connection.close()
        raw = b"".join(chunks).split(b"\n", 1)[0]
        if not raw:
            raise RuntimeError("browser runner returned an empty response")
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError("browser runner returned invalid JSON") from error

    def _start_daemon(self) -> None:
        log_dir = Path(
            os.environ.get(
                "AGENT_BRIDGE_RUNTIME_DIR",
                "/data/data/com.termux/files/home/.cache/agent-bridge",
            )
        ).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)
        log = (log_dir / "browser-runner.log").open("ab")
        try:
            subprocess.Popen(
                [
                    "browser-runner-daemon",
                    "--profile",
                    self.profile,
                    "--backend",
                    self.backend,
                    *(["--cdp-endpoint", self.cdp_endpoint] if self.cdp_endpoint else []),
                    "serve",
                ],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        finally:
            log.close()

    def ensure_ready(self) -> dict[str, Any]:
        try:
            response = self._request({"control": "status", "profile": self.profile})
        except OSError as error:
            if error.errno not in {2, 111}:
                raise
            self._start_daemon()
            response = {}
            last_error: OSError | None = error
            for _ in range(80):
                time.sleep(0.25)
                try:
                    response = self._request(
                        {"control": "status", "profile": self.profile}
                    )
                    last_error = None
                    break
                except OSError as retry_error:
                    last_error = retry_error
            if last_error is not None:
                raise RuntimeError("job browser daemon did not start") from last_error
        if (
            response.get("code") != 0
            or response.get("status") != "ready"
            or response.get("profile") != self.profile
            or response.get("backend") != self.backend
            or response.get("protocol") != self.EXPECTED_PROTOCOL
        ):
            reason = response.get("reason")
            if response.get("backend") != self.backend:
                actual = response.get("backend") or "unknown"
                reason = f"runner is using {actual!r}; task requires {self.backend!r}"
            if not reason and response.get("protocol") != self.EXPECTED_PROTOCOL:
                reason = "installed browser runner protocol is incompatible"
            reason = reason or response.get("status") or "unavailable"
            raise RuntimeError(f"job browser is not ready: {reason}")
        return response

    def command(
        self,
        arguments: list[str],
        *,
        expected_url: str | None = None,
        expected_page_token: str | None = None,
        allowed_origin: str | None = None,
    ) -> dict[str, Any]:
        request: dict[str, Any] = {
            "profile": self.profile,
            "argv": [
                "--profile",
                self.profile,
                "--backend",
                self.backend,
                *(["--cdp-endpoint", self.cdp_endpoint] if self.cdp_endpoint else []),
                *arguments,
            ],
        }
        if expected_url:
            request["expectedUrl"] = expected_url
        if expected_page_token:
            request["expectedPageToken"] = expected_page_token
        if allowed_origin:
            request["allowedOrigin"] = allowed_origin
        response = self._request(request)
        stdout = str(response.get("stdout") or "")
        payload: Any = {}
        if stdout.strip():
            try:
                payload = json.loads(stdout)
            except json.JSONDecodeError:
                payload = {"stdout": stdout}
        response["result"] = payload
        return response

    def current_page(self) -> dict[str, Any]:
        self.ensure_ready()
        response = self.command(["status"])
        if response.get("code") != 0:
            reason = response.get("reason") or response.get("stderr") or "status failed"
            raise RuntimeError(f"job browser status failed: {str(reason).strip()}")
        payload = response.get("result")
        if (
            not isinstance(payload, dict)
            or not isinstance(payload.get("url"), str)
            or not isinstance(payload.get("pageToken"), str)
            or re.fullmatch(r"[0-9a-f]{64}", payload["pageToken"]) is None
        ):
            raise RuntimeError("job browser status did not return its page identity")
        return payload


class BrowserRunnerAdapter:
    """Task adapter for Agent Bridge's authenticated browser runtime."""

    LEVELS = {
        "status": Authority.READ,
        "read": Authority.READ,
        "controls": Authority.READ,
        "frames": Authority.READ,
        "frame-controls": Authority.READ,
        "screenshot": Authority.COLLECT,
        "tabs": Authority.READ,
        "artifact-read": Authority.READ,
        "ashby-status": Authority.READ,
        "greenhouse-status": Authority.READ,
        "download": Authority.COLLECT,
        "open": Authority.LOCAL,
        "fill": Authority.EXTERNAL,
        "frame-fill": Authority.EXTERNAL,
        "upload": Authority.EXTERNAL,
        "wait": Authority.READ,
        "reload": Authority.LOCAL,
        "back": Authority.LOCAL,
        "new-tab": Authority.LOCAL,
        "use-tab": Authority.LOCAL,
        "close-tab": Authority.LOCAL,
        "ashby-stage": Authority.EXTERNAL,
        "greenhouse-stage": Authority.EXTERNAL,
        "click": Authority.EXTERNAL,
        "frame-click": Authority.EXTERNAL,
        "press": Authority.EXTERNAL,
        "select": Authority.EXTERNAL,
        "check": Authority.EXTERNAL,
        "uncheck": Authority.EXTERNAL,
        "ashby-submit": Authority.EXTERNAL,
        "greenhouse-submit": Authority.EXTERNAL,
        "eval": Authority.FULL,
        "frame-eval": Authority.FULL,
    }
    FULL_WORDS = re.compile(
        r"\b(delete|remove account|pay|purchase|buy|place order|confirm payment)\b",
        re.IGNORECASE,
    )
    BATCH_OBSERVATIONS = {
        "status",
        "read",
        "controls",
        "frames",
        "tabs",
    }
    EFFECT_VERBS = {
        "open",
    }
    OUTCOME_EXPECTATION_VERBS = {
        "open",
    }

    def __init__(self, client: BrowserRunnerClient | None = None):
        self._injected_client = client is not None
        self.client = client
        self.backend = getattr(client, "backend", None)

    def configure_backend(self, backend: str) -> None:
        if backend not in BROWSER_BACKENDS:
            choices = ", ".join(sorted(BROWSER_BACKENDS))
            raise ValueError(f"browser backend must be one of: {choices}")
        if self._injected_client:
            actual = getattr(self.client, "backend", None)
            if actual is not None and actual != backend:
                raise ValueError(
                    f"browser client is fixed to {actual!r}; task requires {backend!r}"
                )
        else:
            self.client = BrowserRunnerClient(backend=backend)
        self.backend = backend

    def _client(self) -> BrowserRunnerClient:
        if self.client is None or self.backend is None:
            raise ValueError(
                "browser route is unset; task.browser_backend must name PHONE or LAPTOP"
            )
        return self.client

    @staticmethod
    def exclusive_resources(step: Step) -> tuple[str, ...]:
        return ("job-browser:job-applications",)

    @staticmethod
    def _has_observed_outcome(expect: dict[str, Any], prefix: str = "payload.") -> bool:
        excluded = {
            f"{prefix}action",
            f"{prefix}target",
            f"{prefix}capturedAt",
            f"{prefix}textLength",
            f"{prefix}effect.verified",
        }
        for operation in ("equals", "contains"):
            checks = expect.get(operation)
            if not isinstance(checks, dict):
                continue
            for dotted, wanted in checks.items():
                if not dotted.startswith(prefix) or dotted in excluded:
                    continue
                if dotted.startswith(f"{prefix}effect."):
                    continue
                if operation == "contains" and (wanted == "" or wanted is None):
                    continue
                return True
        return False

    def validate_postcondition(self, step: Step) -> None:
        equals = step.expect.get("equals")
        equals = equals if isinstance(equals, dict) else {}
        if step.verb in self.EFFECT_VERBS:
            if equals.get("payload.effect.verified") is not True:
                raise ValueError(
                    f"browser:{step.verb} requires equals payload.effect.verified=true"
                )
            if (
                step.verb in self.OUTCOME_EXPECTATION_VERBS
                and not self._has_observed_outcome(step.expect)
            ):
                raise ValueError(
                    f"browser:{step.verb} requires an observed post-action outcome"
                )
            return
        if step.verb == "batch":
            batch = step.args.get("steps")
            starts_with_open = bool(batch and batch[0].get("verb") == "open")
            if not starts_with_open:
                return
            if equals.get("payload.results.0.result.effect.verified") is not True:
                raise ValueError(
                    "browser batch navigation requires equals "
                    "payload.results.0.result.effect.verified=true"
                )
            if not self._has_observed_outcome(step.expect, "payload.results.0.result."):
                raise ValueError(
                    "browser batch navigation requires an observed destination outcome"
                )
            return
        if step.verb in {"ashby-stage", "greenhouse-stage"}:
            if equals.get("payload.status") not in {"ready", "needs-input"}:
                raise ValueError(
                    f"browser:{step.verb} requires an exact expected payload.status"
                )
            return
        if step.verb in {"ashby-submit", "greenhouse-submit"}:
            if equals.get("payload.status") != "submitted":
                raise ValueError(
                    f"browser:{step.verb} requires equals payload.status='submitted'"
                )
            return
        if step.verb in {
            "click",
            "frame-click",
            "press",
            "fill",
            "frame-fill",
            "select",
            "check",
            "uncheck",
            "upload",
            "reload",
            "back",
            "new-tab",
            "use-tab",
            "close-tab",
            "eval",
            "frame-eval",
        }:
            raise ValueError(
                f"browser:{step.verb} is disabled because page change cannot prove "
                "or safely replay its outside effect"
            )
        raise ValueError(f"browser:{step.verb} has no semantic mutation verifier")

    @staticmethod
    def _ashby_state(payload: Any) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        raw_path = payload.get("state")
        application_id = payload.get("application_id")
        if not isinstance(raw_path, str) or not isinstance(application_id, str):
            return None
        root = Path(
            os.environ.get(
                "BROWSER_HEADLESS_ARTIFACT_DIR",
                "/data/data/com.termux/files/home/.cache/browser-headless",
            )
        ).expanduser()
        try:
            allowed = (root / "applications").resolve()
            path = Path(raw_path).expanduser().resolve()
            path.relative_to(allowed)
            if path.name != "state.json" or path.stat().st_size > 2_000_000:
                return None
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(state, dict) or state.get("application_id") != application_id:
            return None
        return state

    def _ashby_proof(self, verb: str, payload: Any) -> bool:
        state = self._ashby_state(payload)
        if state is None or not isinstance(payload, dict):
            return False
        if (
            state.get("browser_profile") != "job-applications"
            or state.get("browser_backend") != self.backend
            or state.get("status") != payload.get("status")
        ):
            return False
        if verb == "ashby-stage":
            review_sha = payload.get("review_sha256")
            return bool(
                payload.get("status") in {"ready", "needs-input"}
                and isinstance(review_sha, str)
                and re.fullmatch(r"[0-9a-f]{64}", review_sha)
                and state.get("review_sha256") == review_sha
            )
        if verb != "ashby-submit" or payload.get("status") != "submitted":
            return False
        guard = payload.get("submission_guard")
        response = payload.get("submission_response")
        confirmation = payload.get("confirmation_screenshot")
        try:
            confirmation_path = Path(str(confirmation)).expanduser().resolve()
            state_path = Path(str(payload["state"])).expanduser().resolve()
            confirmation_path.relative_to(state_path.parent)
        except (OSError, ValueError, KeyError):
            return False
        return bool(
            isinstance(guard, dict)
            and guard.get("permit_used") is True
            and isinstance(response, dict)
            and 200 <= int(response.get("status", 0)) < 300
            and response.get("result_type") == "FormSubmitSuccess"
            and confirmation_path.is_file()
        )

    def _greenhouse_proof(self, verb: str, payload: Any) -> bool:
        state = self._ashby_state(payload)
        if state is None or not isinstance(payload, dict):
            return False
        if (
            state.get("browser_profile") != "job-applications"
            or state.get("browser_backend") != self.backend
            or state.get("status") != payload.get("status")
        ):
            return False
        fields = state.get("fields")
        resume = state.get("resume")
        if (
            not isinstance(fields, list)
            or not fields
            or not all(
                isinstance(field, dict)
                and isinstance(field.get("id"), str)
                and isinstance(field.get("value"), str)
                and field.get("value")
                and isinstance(field.get("observed"), str)
                and field.get("observed")
                for field in fields
            )
            or not isinstance(resume, dict)
            or not re.fullmatch(r"[0-9a-f]{64}", str(resume.get("sha256") or ""))
            or state.get("form_valid") is not True
        ):
            return False
        try:
            state_file = Path(str(payload["state"])).expanduser().resolve()
            proof_key = (
                "confirmation_screenshot"
                if verb == "greenhouse-submit"
                else "screenshot"
            )
            proof = Path(str(payload[proof_key])).expanduser().resolve()
            proof.relative_to(state_file.parent)
        except (OSError, ValueError, KeyError):
            return False
        if not proof.is_file():
            return False
        if verb == "greenhouse-stage":
            return payload.get("status") in {"ready", "needs-input"}
        return bool(
            payload.get("status") == "submitted"
            and isinstance(payload.get("success_text"), str)
            and payload.get("success_text")
            and isinstance(payload.get("authorized_by"), str)
            and payload.get("authorized_by")
        )

    def _runner_semantic_proof(self, step: Step, payload: Any) -> tuple[bool, str]:
        if step.verb in self.EFFECT_VERBS:
            effect = payload.get("effect") if isinstance(payload, dict) else None
            if isinstance(effect, dict) and effect.get("verified") is True:
                return True, "browser effect and expectation matched"
            return False, "browser returned no verified post-action effect"
        if step.verb == "batch":
            batch = step.args.get("steps")
            if not batch or batch[0].get("verb") != "open":
                return True, "observation batch completed"
            try:
                effect = payload["results"][0]["result"]["effect"]
            except (KeyError, IndexError, TypeError):
                effect = None
            if isinstance(effect, dict) and effect.get("verified") is True:
                return True, "browser navigation effect and expectation matched"
            return False, "browser batch returned no verified navigation effect"
        if step.verb in {"ashby-stage", "ashby-submit"}:
            if self._ashby_proof(step.verb, payload):
                return True, "Ashby durable state proof and expectation matched"
            return False, "Ashby durable state proof did not verify"
        if step.verb in {"greenhouse-stage", "greenhouse-submit"}:
            if self._greenhouse_proof(step.verb, payload):
                return True, "Greenhouse durable state proof and expectation matched"
            return False, "Greenhouse durable state proof did not verify"
        return True, "browser observation completed"

    @staticmethod
    def _arguments(raw: Any, label: str = "browser") -> list[str]:
        if not isinstance(raw, list):
            raise ValueError(f"{label} arguments must be a string list")
        safe: list[str] = []
        for item in raw:
            if isinstance(item, str):
                safe.append(item)
            elif (
                isinstance(item, dict)
                and len(item) == 1
                and next(iter(item)) in SECRET_REFERENCE_KEYS
            ):
                safe.append("[SECRET_REFERENCE]")
            else:
                raise ValueError(
                    f"{label} arguments must contain strings or secret references"
                )
        return safe

    def _single_level(
        self, verb: str, arguments: list[str], effect: Any = None
    ) -> Authority:
        base = self.LEVELS.get(verb)
        if base is None:
            raise ValueError(f"Unknown job-browser action {verb!r}.")
        declared = base
        if effect is not None:
            requested = (
                Authority(int(effect))
                if isinstance(effect, int)
                else LEVEL_VERBS.get(str(effect))
            )
            if requested is None:
                raise ValueError(f"Unknown browser effect {effect!r}.")
            declared = max(declared, requested)
        if self.FULL_WORDS.search(" ".join(arguments)):
            return max(declared, Authority.FULL)
        return declared

    def required_authority(self, step: Step) -> Authority:
        if step.verb != "batch":
            arguments = self._arguments(step.args.get("arguments", []))
            return self._single_level(step.verb, arguments, step.args.get("effect"))
        batch = step.args.get("steps")
        if not isinstance(batch, list) or not batch:
            raise ValueError("browser batch needs at least one step")
        required = Authority.TALK
        for index, item in enumerate(batch):
            if not isinstance(item, dict):
                raise ValueError("every browser batch step must be an object")
            verb = str(item.get("verb", ""))
            if verb == "open" and index == 0:
                pass
            elif verb not in self.BATCH_OBSERVATIONS:
                raise ValueError(f"browser batch cannot contain unsafe action {verb!r}")
            arguments = self._arguments(item.get("arguments", []), "browser batch")
            required = max(
                required, self._single_level(verb, arguments, item.get("effect"))
            )
        return required

    def permission_steps(self, step: Step) -> tuple[Step, ...]:
        if step.verb == "batch":
            nested_steps = []
            for item in step.args["steps"]:
                nested_args: dict[str, Any] = {"arguments": item.get("arguments", [])}
                if "effect" in item:
                    nested_args["effect"] = item["effect"]
                nested_steps.append(
                    Step(
                        adapter=step.adapter,
                        verb=str(item["verb"]),
                        target=step.target,
                        args=nested_args,
                    )
                )
            return tuple(nested_steps)
        arguments = self._arguments(step.args.get("arguments", []))
        if step.verb == "upload":
            if len(arguments) < 2:
                raise ValueError("browser upload needs a target and source file")
            return (
                replace(
                    step,
                    target=canonical_file_target(arguments[1], "browser upload source"),
                ),
            )
        if step.verb not in {
            "ashby-stage",
            "ashby-submit",
            "greenhouse-stage",
            "greenhouse-submit",
        }:
            return ()
        return tuple(
            replace(step, target=target)
            for target in self._ashby_file_targets(arguments)
        )

    @staticmethod
    def _resolved_spec_file(raw: Any, base: Path, label: str) -> str:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"Ashby spec {label} needs a file path")
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = base / path
        return canonical_file_target(str(path), f"Ashby {label}")

    @classmethod
    def _ashby_file_targets(cls, arguments: list[str]) -> tuple[str, ...]:
        if not arguments:
            raise ValueError("Ashby action needs a spec path")
        spec_path = Path(arguments[0]).expanduser().resolve(strict=True)
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(
                f"cannot read Ashby spec {str(spec_path)!r}: {error}"
            ) from error
        if not isinstance(spec, dict):
            raise ValueError("Ashby spec must be an object")
        base = spec_path.parent
        targets = [canonical_file_target(str(spec_path), "Ashby spec")]
        targets.append(
            cls._resolved_spec_file(spec.get("answer_bank"), base, "answer bank")
        )
        documents = spec.get("documents")
        if not isinstance(documents, dict):
            raise ValueError("Ashby spec documents must be an object")
        for name in ("resume", "cover_letter"):
            document = documents.get(name)
            if document is None and name == "cover_letter":
                continue
            if not isinstance(document, dict):
                raise ValueError(f"Ashby spec documents.{name} must be an object")
            targets.append(
                cls._resolved_spec_file(document.get("path"), base, f"documents.{name}")
            )
        return tuple(dict.fromkeys(targets))

    @staticmethod
    def _spec_url(arguments: list[str]) -> str:
        if not arguments:
            raise ValueError("Ashby action needs a spec path")
        path = Path(arguments[0]).expanduser()
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(
                f"cannot read Ashby spec {str(path)!r}: {error}"
            ) from error
        url = spec.get("apply_url")
        if not isinstance(url, str):
            raise ValueError("Ashby spec needs apply_url")
        return url

    def _explicit_url(self, verb: str, arguments: list[str]) -> str | None:
        if verb == "open":
            if not arguments:
                raise ValueError("open needs a URL")
            return arguments[0]
        if verb == "new-tab" and arguments:
            return arguments[0]
        if verb in {
            "ashby-stage",
            "ashby-submit",
            "greenhouse-stage",
            "greenhouse-submit",
        }:
            return self._spec_url(arguments)
        return None

    def bind(self, step: Step) -> Step:
        if step.verb.startswith("frame-"):
            raise ValueError(
                "browser frame commands are disabled until frame-origin permission is bound"
            )
        args = dict(step.args)
        if step.verb == "artifact-read":
            arguments = self._arguments(step.args.get("arguments", []))
            if not arguments:
                raise ValueError("browser artifact-read needs an exact file path")
            return replace(
                step,
                target=canonical_file_target(arguments[0], "browser artifact"),
                args=args,
            )
        explicit_urls: list[str] = []
        starts_with_navigation = False
        if step.verb == "batch":
            batch = step.args.get("steps")
            if not isinstance(batch, list) or not batch:
                raise ValueError("browser batch needs at least one step")
            for index, item in enumerate(batch):
                if not isinstance(item, dict):
                    raise ValueError("every browser batch step must be an object")
                verb = str(item.get("verb", ""))
                arguments = self._arguments(item.get("arguments", []), "browser batch")
                url = self._explicit_url(verb, arguments)
                if url:
                    explicit_urls.append(url)
                    if index == 0:
                        starts_with_navigation = True
        else:
            arguments = self._arguments(step.args.get("arguments", []))
            url = self._explicit_url(step.verb, arguments)
            if url:
                explicit_urls.append(url)
                starts_with_navigation = True
            elif step.verb in {"ashby-status", "greenhouse-status"}:
                if not arguments:
                    raise ValueError(f"{step.verb} needs an application ID")
                return replace(step, target=f"browser:{step.verb}:{arguments[0]}")

        targets = {canonical_browser_target(url) for url in explicit_urls}
        if not explicit_urls or (step.verb == "batch" and not starts_with_navigation):
            current = self._client().current_page()
            raw_url = current["url"]
            targets.add(canonical_browser_target(raw_url))
            args["_expected_page_token"] = current["pageToken"]
        if len(targets) != 1:
            raise ValueError("one browser step cannot span multiple URL targets")
        target = targets.pop()
        return replace(step, target=target, args=args)

    @staticmethod
    def _runner_arguments(step: Step) -> list[str]:
        if step.verb == "batch":
            normalized = []
            for item in step.args["steps"]:
                nested = dict(item)
                arguments = list(nested.get("arguments", []))
                if (
                    nested.get("verb") in {"read", "controls"}
                    and len(arguments) == 1
                    and arguments[0].isdigit()
                ):
                    arguments = ["--limit", arguments[0]]
                nested["arguments"] = arguments
                normalized.append(nested)
            return ["batch", json.dumps(normalized, separators=(",", ":"))]
        arguments = list(step.args.get("arguments", []))
        if (
            step.verb in {"read", "controls"}
            and len(arguments) == 1
            and arguments[0].isdigit()
        ):
            arguments = ["--limit", arguments[0]]
        return [step.verb, *arguments]

    def execute(self, step: Step) -> AdapterResult:
        client = self._client()
        try:
            client.ensure_ready()
            response = client.command(
                self._runner_arguments(step),
                expected_url=step.args.get("_expected_url"),
                expected_page_token=step.args.get("_expected_page_token"),
                allowed_origin=(
                    step.target.removeprefix("browser:")
                    if step.target.startswith("browser:http")
                    else None
                ),
            )
        except (OSError, RuntimeError, ValueError) as error:
            return AdapterResult(
                False,
                False,
                {
                    "error": str(error),
                    "transport": "job-browser",
                    "browser_backend": self.backend,
                },
            )
        data = {
            "exit_code": int(response.get("code", 5)),
            "payload": response.get("result", {}),
            "stderr": str(response.get("stderr") or ""),
            "transport": "job-browser",
            "browser_backend": self.backend,
        }
        ok = data["exit_code"] == int(step.expect.get("exit_code", 0))
        verified, reason = verify_expectation(
            data,
            {key: value for key, value in step.expect.items() if key != "exit_code"},
            require_semantic=self.required_authority(step) >= Authority.LOCAL,
        )
        semantic_verified, semantic_reason = self._runner_semantic_proof(
            step, data["payload"]
        )
        data["verification"] = (
            semantic_reason if not semantic_verified or verified else reason
        )
        return AdapterResult(ok, ok and verified and semantic_verified, data)


def default_adapters() -> dict[str, Adapter]:
    from .hidden import HiddenAdapter
    from .toolkit_adapter import ToolkitAdapter
    return {
        "google-console": GoogleConsoleAdapter(),
        "phone": PhoneMcpAdapter(),
        "browser": BrowserRunnerAdapter(),
        "hidden": HiddenAdapter(),
        "toolkit": ToolkitAdapter(),
    }
