"""Command-line interface for running and verifying synthetic scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .audit import AuditLedger
from .models import TurnProposal
from .pipeline import ReliabilityPipeline


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def run_scenario(scenario_path: Path, audit_path: Path) -> int:
    ledger = AuditLedger(audit_path)
    pipeline = ReliabilityPipeline(ledger=ledger)

    for line_number, raw_line in enumerate(
        scenario_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        event = json.loads(raw_line)
        operation = event.get("operation", "proposal")

        if operation == "proposal":
            proposal = TurnProposal.from_mapping(event)
            decision = pipeline.process(proposal)
            _emit(
                {
                    "line": line_number,
                    "event_id": proposal.event_id,
                    "allowed": decision.allowed,
                    "code": decision.code,
                }
            )
        elif operation == "open_handoff":
            pipeline.open_handoff(
                str(event["conversation_id"]),
                str(event["notice"]),
                str(event.get("reason", "policy escalation")),
            )
            _emit({"line": line_number, "operation": operation, "status": "recorded"})
        elif operation == "release_handoff":
            pipeline.release_handoff(
                str(event["conversation_id"]), str(event.get("released_by", "human"))
            )
            _emit({"line": line_number, "operation": operation, "status": "recorded"})
        else:
            raise ValueError(f"unsupported operation at line {line_number}: {operation}")

    _emit({"health": pipeline.health()})
    return 0


def verify_audit(audit_path: Path) -> int:
    valid, message = AuditLedger(audit_path).verify()
    _emit({"valid": valid, "message": message, "path": str(audit_path)})
    return 0 if valid else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-ops-lab",
        description="Run synthetic AI reliability scenarios and verify their audit chain.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="run a JSONL scenario")
    demo.add_argument("--scenario", type=Path, required=True)
    demo.add_argument("--audit", type=Path, required=True)

    verify = subparsers.add_parser("verify", help="verify an audit JSONL hash chain")
    verify.add_argument("--audit", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "demo":
        return run_scenario(args.scenario, args.audit)
    if args.command == "verify":
        return verify_audit(args.audit)
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
