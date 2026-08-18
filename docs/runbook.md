# Operational runbook

## Purpose

This runbook describes how to execute the synthetic scenario, verify the audit chain,
and investigate a blocked proposal. It does not operate any external system.

## Pre-flight

1. Use Python 3.11 or newer.
2. Confirm that `artifacts/` contains no file you need to preserve.
3. Run the regression suite before interpreting demo output.

```bash
python -m unittest discover -s tests -v
```

## Execute the scenario

```bash
ai-ops-lab demo \
  --scenario scenarios/demo.jsonl \
  --audit artifacts/demo-audit.jsonl
```

The final JSON object contains health, ledger integrity, active ownership, and counters.

## Verify the ledger

```bash
ai-ops-lab verify --audit artifacts/demo-audit.jsonl
```

Expected result:

```json
{"valid": true, "message": "verified 10 record(s)"}
```

The exact record count can change as scenarios evolve.

## Triage a blocked proposal

1. Locate the `event_id` in the CLI output.
2. Find its `proposal_decided` entry in the audit JSONL.
3. Read `decision.code` and `decision.reasons`.
4. Confirm `state_after` did not commit the forbidden transition.
5. Reproduce the case as a deterministic unit test before changing policy.

## Decision codes

| Code | Meaning |
|---|---|
| `POLICY_PASS` | Proposal satisfied all active rules |
| `DUPLICATE_EVENT` | Event was already committed |
| `HUMAN_OWNERSHIP_LOCK` | Automation attempted to act during human ownership |
| `AUTHORIZED_HANDOFF_NOTICE` | Exact one-time handoff notice was allowed |
| `INTENT_ACTION_MISMATCH` | Proposed action conflicts with interpreted intent |
| `MISSING_CONFIRMED_FIELDS` | Sensitive action lacks explicit evidence |
| `EMPTY_RESPONSE` | A side effect was proposed without an explicit response |

## Incident rule

Do not weaken a global invariant to make a single scenario pass. First determine whether
the proposal, state, or policy is incorrect; then add a regression that proves the full
failure and expected behavior.
