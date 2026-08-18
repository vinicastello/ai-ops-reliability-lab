"""Domain models used by the reliability pipeline.

The project deliberately keeps these models small. They are not tied to a
specific LLM vendor, business domain, messaging provider, or database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class Actor(StrEnum):
    """Actor that proposed or owns a conversation turn."""

    AI = "ai"
    HUMAN = "human"
    SYSTEM = "system"


class ActionKind(StrEnum):
    """Side effect proposed by a turn."""

    NONE = "none"
    REPLY = "reply"
    CREATE_APPOINTMENT = "create_appointment"
    RESCHEDULE_APPOINTMENT = "reschedule_appointment"
    HANDOFF = "handoff"


@dataclass(slots=True)
class TurnProposal:
    """A response and optional side effect waiting for validation."""

    event_id: str
    conversation_id: str
    actor: Actor
    intent: str
    response: str
    action: ActionKind = ActionKind.REPLY
    confirmed_fields: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TurnProposal":
        """Build a proposal from JSON-compatible input."""

        return cls(
            event_id=str(payload["event_id"]),
            conversation_id=str(payload["conversation_id"]),
            actor=Actor(str(payload.get("actor", Actor.AI))),
            intent=str(payload.get("intent", "unknown")),
            response=str(payload.get("response", "")),
            action=ActionKind(str(payload.get("action", ActionKind.REPLY))),
            confirmed_fields={
                str(key): str(value)
                for key, value in dict(payload.get("confirmed_fields", {})).items()
            },
            metadata=dict(payload.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "event_id": self.event_id,
            "conversation_id": self.conversation_id,
            "actor": self.actor.value,
            "intent": self.intent,
            "response": self.response,
            "action": self.action.value,
            "confirmed_fields": dict(self.confirmed_fields),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ConversationState:
    """Minimal state needed to enforce ownership and idempotency."""

    human_owned: bool = False
    handoff_open: bool = False
    authorized_handoff_notice_hash: str | None = None
    handled_event_ids: set[str] = field(default_factory=set)
    last_intent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return non-sensitive state for audit and diagnostics."""

        return {
            "human_owned": self.human_owned,
            "handoff_open": self.handoff_open,
            "has_authorized_handoff_notice": self.authorized_handoff_notice_hash is not None,
            "handled_event_count": len(self.handled_event_ids),
            "last_intent": self.last_intent,
        }


@dataclass(frozen=True, slots=True)
class Decision:
    """Closed verdict emitted before a side effect is committed."""

    allowed: bool
    code: str
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "code": self.code,
            "reasons": list(self.reasons),
        }
