"""Reliability pipeline that validates proposals before committing effects."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .audit import AuditLedger
from .models import ActionKind, ConversationState, Decision, TurnProposal
from .policy import DeterministicPolicyEngine, response_fingerprint


class ReliabilityPipeline:
    """Coordinate policy, ownership, state mutation, metrics, and audit."""

    def __init__(
        self,
        policy: DeterministicPolicyEngine | None = None,
        ledger: AuditLedger | None = None,
    ) -> None:
        self.policy = policy or DeterministicPolicyEngine()
        self.ledger = ledger or AuditLedger()
        self._states: dict[str, ConversationState] = {}
        self._metrics: Counter[str] = Counter()

    def state_for(self, conversation_id: str) -> ConversationState:
        return self._states.setdefault(conversation_id, ConversationState())

    def open_handoff(self, conversation_id: str, notice: str, reason: str) -> None:
        """Give ownership to a human and authorize one integrity-bound notice."""

        state = self.state_for(conversation_id)
        state.human_owned = True
        state.handoff_open = True
        state.authorized_handoff_notice_hash = response_fingerprint(notice)
        self._metrics["handoff_opened"] += 1
        self.ledger.append(
            "handoff_opened",
            {
                "conversation_id": conversation_id,
                "reason": reason,
                "notice_hash": state.authorized_handoff_notice_hash,
                "state": state.to_dict(),
            },
        )

    def release_handoff(self, conversation_id: str, released_by: str = "human") -> None:
        """Return ownership to automation through an explicit event."""

        state = self.state_for(conversation_id)
        state.human_owned = False
        state.handoff_open = False
        state.authorized_handoff_notice_hash = None
        self._metrics["handoff_released"] += 1
        self.ledger.append(
            "handoff_released",
            {
                "conversation_id": conversation_id,
                "released_by": released_by,
                "state": state.to_dict(),
            },
        )

    def process(self, proposal: TurnProposal) -> Decision:
        """Validate a proposal, commit only if allowed, and audit the verdict."""

        state = self.state_for(proposal.conversation_id)
        decision = self.policy.evaluate(proposal, state)
        self._metrics["proposals_total"] += 1
        self._metrics["allowed" if decision.allowed else "blocked"] += 1
        self._metrics[f"decision_{decision.code.lower()}"] += 1

        if decision.allowed:
            state.handled_event_ids.add(proposal.event_id)
            state.last_intent = proposal.intent

            if decision.code == "AUTHORIZED_HANDOFF_NOTICE":
                state.authorized_handoff_notice_hash = None
                self._metrics["handoff_notices_delivered"] += 1

            if proposal.action is ActionKind.HANDOFF:
                state.human_owned = True
                state.handoff_open = True
                state.authorized_handoff_notice_hash = None

        self.ledger.append(
            "proposal_decided",
            {
                "proposal": proposal.to_dict(),
                "decision": decision.to_dict(),
                "state_after": state.to_dict(),
            },
        )
        return decision

    def metrics(self) -> dict[str, int]:
        """Return a stable snapshot suitable for health endpoints or logs."""

        keys = sorted(self._metrics)
        return {key: self._metrics[key] for key in keys}

    def health(self) -> dict[str, Any]:
        """Return operational and integrity status."""

        ledger_valid, ledger_message = self.ledger.verify()
        return {
            "status": "healthy" if ledger_valid else "degraded",
            "ledger": {"valid": ledger_valid, "message": ledger_message},
            "active_conversations": len(self._states),
            "human_owned_conversations": sum(
                1 for state in self._states.values() if state.human_owned
            ),
            "metrics": self.metrics(),
        }
