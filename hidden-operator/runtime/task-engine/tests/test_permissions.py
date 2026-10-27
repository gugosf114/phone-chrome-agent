from __future__ import annotations

import unittest
import os
from pathlib import Path
from unittest.mock import patch

from agent_bridge_task.models import Authority, PermissionGrant, Scope, Step
from agent_bridge_task.permissions import (
    PermissionContext,
    agent_bridge_authority_active,
    evaluate_permission,
    permission_receipt,
)


class PermissionTests(unittest.TestCase):
    def grant(
        self,
        authority: Authority,
        targets: tuple[str, ...] = ("browser:*",),
        scope: Scope | None = None,
        denied: tuple[str, ...] = (),
    ) -> PermissionGrant:
        return PermissionGrant(
            id="g1",
            authority=authority,
            scope=scope or Scope("task", "task-1"),
            targets=targets,
            denied_actions=denied,
        )

    def step(self, target: str = "browser:example.com", verb: str = "read") -> Step:
        return Step("noop", verb, target)

    def test_read_permission_allows_read_inside_target(self) -> None:
        decision = evaluate_permission(
            self.grant(Authority.READ),
            self.step(),
            Authority.READ,
            PermissionContext("task-1"),
        )
        self.assertTrue(decision.allowed)

    def test_read_permission_blocks_local_change(self) -> None:
        decision = evaluate_permission(
            self.grant(Authority.READ),
            self.step(verb="local"),
            Authority.LOCAL,
            PermissionContext("task-1"),
        )
        self.assertFalse(decision.allowed)
        self.assertIn("needs level 3", decision.reason)

    def test_full_authority_stays_inside_named_target(self) -> None:
        decision = evaluate_permission(
            self.grant(Authority.FULL),
            self.step(target="phone:settings", verb="external"),
            Authority.EXTERNAL,
            PermissionContext("task-1"),
        )
        self.assertFalse(decision.allowed)
        self.assertIn("outside", decision.reason)

    def test_explicit_denial_wins_over_full_authority(self) -> None:
        decision = evaluate_permission(
            self.grant(Authority.FULL, denied=("noop:external",)),
            self.step(verb="external"),
            Authority.EXTERNAL,
            PermissionContext("task-1"),
        )
        self.assertFalse(decision.allowed)
        self.assertIn("explicitly denied", decision.reason)

    def test_session_permission_is_bound_to_session(self) -> None:
        decision = evaluate_permission(
            self.grant(Authority.READ, scope=Scope("session", "session-a")),
            self.step(),
            Authority.READ,
            PermissionContext("task-1", "session-b"),
        )
        self.assertFalse(decision.allowed)

    def test_unbound_session_permission_is_closed(self) -> None:
        decision = evaluate_permission(
            self.grant(Authority.READ, scope=Scope("session")),
            self.step(),
            Authority.READ,
            PermissionContext("task-1"),
        )
        self.assertFalse(decision.allowed)
        self.assertIn("another session", decision.reason)

    def test_parsed_session_permission_needs_a_session_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "concrete session ID"):
            PermissionGrant.from_dict(
                "unbound-session",
                {
                    "authority": "read",
                    "scope": {"kind": "session"},
                    "targets": ["browser:*"],
                },
            )

    def test_unbound_task_permission_is_closed(self) -> None:
        decision = evaluate_permission(
            self.grant(Authority.READ, scope=Scope("task")),
            self.step(),
            Authority.READ,
            PermissionContext("task-1"),
        )
        self.assertFalse(decision.allowed)
        self.assertIn("another task", decision.reason)

    def test_used_answer_permission_is_closed(self) -> None:
        decision = evaluate_permission(
            self.grant(Authority.READ, scope=Scope("answer", remaining_uses=0)),
            self.step(),
            Authority.READ,
            PermissionContext("task-1"),
        )
        self.assertFalse(decision.allowed)
        self.assertIn("no remaining", decision.reason)

    def test_receipt_is_plain_and_exact(self) -> None:
        receipt = permission_receipt(
            self.grant(Authority.FULL, scope=Scope("turns", remaining_uses=5))
        )
        self.assertEqual(
            receipt, "level 5 (full), scope next 5 answers, targets browser:*"
        )

    def test_target_string_cannot_turn_its_star_character_into_a_global_grant(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "targets must be a list"):
            PermissionGrant.from_dict(
                "bad-targets",
                {
                    "authority": "full",
                    "scope": {"kind": "task"},
                    "targets": "browser:*",
                },
            )

    def test_denied_actions_must_be_a_list(self) -> None:
        with self.assertRaisesRegex(ValueError, "denied_actions must be a list"):
            PermissionGrant.from_dict(
                "bad-denials",
                {
                    "authority": "full",
                    "scope": {"kind": "task"},
                    "targets": ["browser:*"],
                    "denied_actions": "browser:click",
                },
            )

    def test_agent_bridge_core_overrides_every_lower_permission_gate(self) -> None:
        core = Path(__file__).resolve().parents[3] / "scripts" / "authority_core.sh"
        with patch.dict(os.environ, {"AGENT_BRIDGE_AUTHORITY_CORE": str(core)}):
            agent_bridge_authority_active.cache_clear()
            decision = evaluate_permission(
                self.grant(Authority.TALK, targets=("nowhere:*",), denied=("*",)),
                self.step(target="phone:anything", verb="delete"),
                Authority.FULL,
                PermissionContext("wrong-task"),
            )
            self.assertTrue(decision.allowed)
            self.assertEqual(decision.reason, "Agent Bridge authority core")
            self.assertEqual(
                decision.receipt,
                "Agent Bridge full perpetual authority over everything",
            )
        agent_bridge_authority_active.cache_clear()


if __name__ == "__main__":
    unittest.main()
