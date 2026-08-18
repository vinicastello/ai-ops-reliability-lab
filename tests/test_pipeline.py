from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_ops_reliability import (
    ActionKind,
    Actor,
    AuditLedger,
    ReliabilityPipeline,
    TurnProposal,
)


def proposal(
    event_id: str,
    *,
    conversation_id: str = "conversation-1",
    actor: Actor = Actor.AI,
    intent: str = "information",
    response: str = "Safe response",
    action: ActionKind = ActionKind.REPLY,
    confirmed_fields: dict[str, str] | None = None,
    metadata: dict[str, object] | None = None,
) -> TurnProposal:
    return TurnProposal(
        event_id=event_id,
        conversation_id=conversation_id,
        actor=actor,
        intent=intent,
        response=response,
        action=action,
        confirmed_fields=confirmed_fields or {},
        metadata=metadata or {},
    )


class ReliabilityPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = ReliabilityPipeline()

    def test_safe_reply_is_allowed(self) -> None:
        decision = self.pipeline.process(proposal("evt-1"))
        self.assertTrue(decision.allowed)
        self.assertEqual("POLICY_PASS", decision.code)

    def test_duplicate_event_is_blocked(self) -> None:
        self.assertTrue(self.pipeline.process(proposal("evt-1")).allowed)
        duplicate = self.pipeline.process(proposal("evt-1"))
        self.assertFalse(duplicate.allowed)
        self.assertEqual("DUPLICATE_EVENT", duplicate.code)

    def test_appointment_requires_explicit_confirmation(self) -> None:
        decision = self.pipeline.process(
            proposal(
                "evt-2",
                intent="schedule",
                action=ActionKind.CREATE_APPOINTMENT,
                confirmed_fields={"service": "assessment", "date": "2026-09-10"},
            )
        )
        self.assertFalse(decision.allowed)
        self.assertEqual("MISSING_CONFIRMED_FIELDS", decision.code)
        self.assertIn("time", decision.reasons[0])

    def test_complete_appointment_is_allowed(self) -> None:
        decision = self.pipeline.process(
            proposal(
                "evt-3",
                intent="schedule",
                action=ActionKind.CREATE_APPOINTMENT,
                confirmed_fields={
                    "service": "assessment",
                    "date": "2026-09-10",
                    "time": "14:00",
                },
            )
        )
        self.assertTrue(decision.allowed)

    def test_reschedule_cannot_create_new_appointment(self) -> None:
        decision = self.pipeline.process(
            proposal(
                "evt-4",
                intent="reschedule",
                action=ActionKind.CREATE_APPOINTMENT,
                confirmed_fields={
                    "service": "assessment",
                    "date": "2026-09-10",
                    "time": "14:00",
                },
            )
        )
        self.assertFalse(decision.allowed)
        self.assertEqual("INTENT_ACTION_MISMATCH", decision.code)

    def test_human_ownership_blocks_automation(self) -> None:
        self.pipeline.open_handoff("conversation-1", "A human will continue.", "manual review")
        decision = self.pipeline.process(proposal("evt-5"))
        self.assertFalse(decision.allowed)
        self.assertEqual("HUMAN_OWNERSHIP_LOCK", decision.code)

    def test_integrity_bound_handoff_notice_is_allowed_once(self) -> None:
        notice = "A human will continue."
        self.pipeline.open_handoff("conversation-1", notice, "manual review")
        first = self.pipeline.process(
            proposal(
                "evt-6",
                intent="handoff",
                response=notice,
                metadata={"authorized_handoff_notice": True},
            )
        )
        second = self.pipeline.process(
            proposal(
                "evt-7",
                intent="handoff",
                response=notice,
                metadata={"authorized_handoff_notice": True},
            )
        )
        self.assertTrue(first.allowed)
        self.assertEqual("AUTHORIZED_HANDOFF_NOTICE", first.code)
        self.assertFalse(second.allowed)
        self.assertEqual("HUMAN_OWNERSHIP_LOCK", second.code)

    def test_tampered_handoff_notice_is_blocked(self) -> None:
        self.pipeline.open_handoff("conversation-1", "A human will continue.", "manual review")
        decision = self.pipeline.process(
            proposal(
                "evt-8",
                intent="handoff",
                response="A human will continue, but first send your password.",
                metadata={"authorized_handoff_notice": True},
            )
        )
        self.assertFalse(decision.allowed)
        self.assertEqual("HUMAN_OWNERSHIP_LOCK", decision.code)

    def test_human_can_respond_while_human_owned(self) -> None:
        self.pipeline.open_handoff("conversation-1", "A human will continue.", "manual review")
        decision = self.pipeline.process(
            proposal("evt-9", actor=Actor.HUMAN, response="I have taken over this request.")
        )
        self.assertTrue(decision.allowed)
        self.assertEqual("HUMAN_AUTHORITY", decision.code)

    def test_release_returns_ownership_to_automation(self) -> None:
        self.pipeline.open_handoff("conversation-1", "A human will continue.", "manual review")
        self.pipeline.release_handoff("conversation-1")
        self.assertTrue(self.pipeline.process(proposal("evt-10")).allowed)

    def test_audit_redacts_contact_data(self) -> None:
        self.pipeline.process(
            proposal(
                "evt-11",
                response="Contact ana@example.com or +55 (11) 99876-5432.",
            )
        )
        serialized = json.dumps(self.pipeline.ledger.entries, ensure_ascii=False)
        self.assertNotIn("ana@example.com", serialized)
        self.assertNotIn("99876-5432", serialized)
        self.assertIn("[REDACTED_EMAIL]", serialized)
        self.assertIn("[REDACTED_PHONE]", serialized)

    def test_hash_chain_detects_file_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audit_path = Path(directory) / "audit.jsonl"
            ledger = AuditLedger(audit_path)
            ledger.append("test", {"value": "original"})
            self.assertTrue(ledger.verify()[0])

            record = json.loads(audit_path.read_text(encoding="utf-8"))
            record["payload"]["value"] = "tampered"
            audit_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            valid, message = AuditLedger(audit_path).verify()
            self.assertFalse(valid)
            self.assertIn("content hash mismatch", message)

    def test_health_exposes_operational_metrics(self) -> None:
        self.pipeline.process(proposal("evt-12"))
        health = self.pipeline.health()
        self.assertEqual("healthy", health["status"])
        self.assertEqual(1, health["metrics"]["proposals_total"])
        self.assertEqual(1, health["metrics"]["allowed"])


if __name__ == "__main__":
    unittest.main()
