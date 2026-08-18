"""Append-only, privacy-aware audit ledger with hash-chain verification."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d ().-]{7,}\d)(?!\d)")


def _redact_text(value: str) -> str:
    value = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", value)
    return PHONE_PATTERN.sub("[REDACTED_PHONE]", value)


def redact(value: Any) -> Any:
    """Recursively redact common contact identifiers before persistence."""

    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, Mapping):
        return {str(key): redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class AuditLedger:
    """Persist audit events as JSON Lines linked by SHA-256 hashes."""

    GENESIS_HASH = "0" * 64

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._entries: list[dict[str, Any]] = []
        if self.path and self.path.exists():
            self._entries = [
                json.loads(line)
                for line in self.path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

    @property
    def entries(self) -> list[dict[str, Any]]:
        """Return a defensive copy of ledger entries."""

        return deepcopy(self._entries)

    def append(self, event_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Redact, hash, store, and optionally persist one audit event."""

        previous_hash = self._entries[-1]["hash"] if self._entries else self.GENESIS_HASH
        body = {
            "sequence": len(self._entries) + 1,
            "recorded_at": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "payload": redact(dict(payload)),
            "previous_hash": previous_hash,
        }
        entry_hash = hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()
        entry = {**body, "hash": entry_hash}
        self._entries.append(entry)

        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

        return deepcopy(entry)

    def verify(self) -> tuple[bool, str]:
        """Verify sequence numbers, previous hashes, and record integrity."""

        expected_previous = self.GENESIS_HASH
        for expected_sequence, entry in enumerate(self._entries, start=1):
            if entry.get("sequence") != expected_sequence:
                return False, f"sequence mismatch at record {expected_sequence}"
            if entry.get("previous_hash") != expected_previous:
                return False, f"previous hash mismatch at record {expected_sequence}"

            body = {key: value for key, value in entry.items() if key != "hash"}
            expected_hash = hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()
            if entry.get("hash") != expected_hash:
                return False, f"content hash mismatch at record {expected_sequence}"
            expected_previous = expected_hash

        return True, f"verified {len(self._entries)} record(s)"

    def replay(self) -> Iterable[dict[str, Any]]:
        """Yield verified payloads in commit order."""

        valid, message = self.verify()
        if not valid:
            raise ValueError(message)
        for entry in self.entries:
            yield entry
