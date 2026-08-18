# Portfolio and interview guide

## Thirty-second explanation

> I built a synthetic reliability lab that treats an AI response as a proposal rather
> than an authority. A deterministic commit barrier validates ownership, intent,
> confirmation, and idempotency before a simulated side effect. Every decision is
> redacted, audited, and linked through a verifiable hash chain.

## What can be demonstrated live

1. Run the unit tests.
2. Execute `scenarios/demo.jsonl`.
3. Point to the blocked incomplete appointment.
4. Show the valid handoff notice followed by a blocked automated reply.
5. Verify the audit chain.
6. Change one audit value locally and show verification fail.
7. Run the PowerShell health check on a Windows machine.

## Engineering signals

- Reliability engineering: invariants, idempotency, explicit ownership.
- AI operations: model-independent validation and human-in-the-loop control.
- Observability: structured metrics, decision codes, audit replay.
- Security and privacy: data reduction and tamper evidence.
- Infrastructure operations: PowerShell health snapshot and JSON output.
- Quality engineering: deterministic tests without network or model calls.

## Honest scope statement

Use this wording when asked whether the project runs in production:

> This is a public reference lab built with synthetic data. It demonstrates the design
> and verification approach, but it is intentionally not connected to a production
> service or customer environment.
