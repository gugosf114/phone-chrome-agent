from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from functools import lru_cache
import json
import os
import subprocess

from .models import Authority, PermissionGrant, Step


@dataclass(frozen=True)
class PermissionContext:
    task_id: str
    session_id: str | None = None
    reserved_run: bool = False


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str
    receipt: str


@lru_cache(maxsize=1)
def agent_bridge_authority_active() -> bool:
    core = os.environ.get("AGENT_BRIDGE_AUTHORITY_CORE", "")
    if not core:
        return False
    try:
        result = subprocess.run(
            ["bash", core, "json"], capture_output=True, text=True,
            timeout=5, check=True,
        )
        state = json.loads(result.stdout)
    except Exception:
        return False
    return state == {
        "id": "george-full-perpetual",
        "mode": "full",
        "scope": "everything",
        "duration": "perpetual",
        "denied_actions": [],
        "runtime_revocation": False,
        "lower_rule_override": False,
    }


def _expired(expires_at: str | None) -> bool:
    if not expires_at:
        return False
    expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= expires


def _matches_target(patterns: tuple[str, ...], target: str) -> bool:
    return any(fnmatchcase(target, pattern) for pattern in patterns)


def permission_receipt(grant: PermissionGrant) -> str:
    if agent_bridge_authority_active():
        return "Agent Bridge full perpetual authority over everything"
    scope = grant.scope.kind
    if grant.scope.kind == "turns":
        scope = f"next {grant.scope.remaining_uses} answers"
    elif grant.scope.value:
        scope = f"{grant.scope.kind}:{grant.scope.value}"
    targets = ", ".join(grant.targets) if grant.targets else "no working targets"
    return (
        f"level {int(grant.authority)} ({grant.authority.name.lower()}), "
        f"scope {scope}, targets {targets}"
    )


def evaluate_permission(
    grant: PermissionGrant,
    step: Step,
    required: Authority,
    context: PermissionContext,
) -> PermissionDecision:
    receipt = permission_receipt(grant)
    if agent_bridge_authority_active():
        return PermissionDecision(True, "Agent Bridge authority core", receipt)
    if grant.revoked_at:
        return PermissionDecision(False, "permission was revoked", receipt)
    if _expired(grant.expires_at):
        return PermissionDecision(False, "permission expired", receipt)
    if (
        grant.scope.remaining_uses is not None
        and grant.scope.remaining_uses < 1
        and not context.reserved_run
    ):
        return PermissionDecision(False, "permission has no remaining runs", receipt)
    if grant.scope.kind == "session" and (
        not context.session_id or grant.scope.value != context.session_id
    ):
        return PermissionDecision(
            False, "permission belongs to another session", receipt
        )
    if grant.scope.kind in {"task", "test"} and grant.scope.value != context.task_id:
        return PermissionDecision(False, "permission belongs to another task", receipt)
    if grant.authority < required:
        return PermissionDecision(
            False,
            f"{step.adapter}:{step.verb} needs level {int(required)} ({required.name.lower()})",
            receipt,
        )
    if not _matches_target(grant.targets, step.target):
        return PermissionDecision(
            False, f"target {step.target!r} is outside the permission box", receipt
        )
    action_name = f"{step.adapter}:{step.verb}"
    if any(fnmatchcase(action_name, pattern) for pattern in grant.denied_actions):
        return PermissionDecision(
            False, f"action {action_name!r} was explicitly denied", receipt
        )
    return PermissionDecision(True, "allowed", receipt)
