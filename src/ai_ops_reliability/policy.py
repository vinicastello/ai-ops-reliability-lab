"""Deterministic safety policies evaluated before side effects."""

from __future__ import annotations

import hashlib

from .models import ActionKind, Actor, ConversationState, Decision, TurnProposal


def response_fingerprint(response: str) -> str:
    """Create a stable fingerprint for an authorized handoff notice."""

    normalized = " ".join(response.split()).strip().casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class DeterministicPolicyEngine:
    """Enforce cross-cutting invariants independently of an LLM.

    The rules model a final commit barrier. A model may interpret a message and
    propose a response, but it cannot bypass ownership, confirmation, intent,
    or idempotency constraints.
    """

    REQUIRED_APPOINTMENT_FIELDS = frozenset({"service", "date", "time"})

    def evaluate(self, proposal: TurnProposal, state: ConversationState) -> Decision:
        """Return a closed allow/block verdict for a proposed turn."""

        if not proposal.event_id.strip() or not proposal.conversation_id.strip():
            return Decision(False, "INVALID_IDENTITY", ("event and conversation IDs are required",))

        if proposal.event_id in state.handled_event_ids:
            return Decision(False, "DUPLICATE_EVENT", ("event already committed",))

        if proposal.actor is Actor.HUMAN:
            return Decision(True, "HUMAN_AUTHORITY")

        if state.human_owned:
            notice_allowed = (
                state.handoff_open
                and bool(proposal.metadata.get("authorized_handoff_notice"))
                and state.authorized_handoff_notice_hash is not None
                and response_fingerprint(proposal.response)
                == state.authorized_handoff_notice_hash
                and proposal.action is ActionKind.REPLY
            )
            if notice_allowed:
                return Decision(True, "AUTHORIZED_HANDOFF_NOTICE")
            return Decision(
                False,
                "HUMAN_OWNERSHIP_LOCK",
                ("automation is blocked while a human owns the conversation",),
            )

        if proposal.action is not ActionKind.NONE and not proposal.response.strip():
            return Decision(False, "EMPTY_RESPONSE", ("side effects require an explicit response",))

        if proposal.intent == "reschedule" and proposal.action is ActionKind.CREATE_APPOINTMENT:
            return Decision(
                False,
                "INTENT_ACTION_MISMATCH",
                ("reschedule intent cannot create a new appointment",),
            )

        if proposal.action is ActionKind.RESCHEDULE_APPOINTMENT and proposal.intent != "reschedule":
            return Decision(
                False,
                "INTENT_ACTION_MISMATCH",
                ("reschedule action requires reschedule intent",),
            )

        if proposal.action in {
            ActionKind.CREATE_APPOINTMENT,
            ActionKind.RESCHEDULE_APPOINTMENT,
        }:
            present = {
                key for key, value in proposal.confirmed_fields.items() if str(value).strip()
            }
            missing = sorted(self.REQUIRED_APPOINTMENT_FIELDS - present)
            if missing:
                return Decision(
                    False,
                    "MISSING_CONFIRMED_FIELDS",
                    (f"missing explicit confirmation: {', '.join(missing)}",),
                )

        if proposal.action is ActionKind.HANDOFF:
            return Decision(True, "HANDOFF_REQUIRED")

        return Decision(True, "POLICY_PASS")
