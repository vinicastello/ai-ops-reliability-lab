# Security policy

## Supported scope

This repository is a synthetic lab and does not process production traffic. Security
reports should focus on weaknesses in the reference code, examples, or documentation.

## Reporting

Open a private security advisory in the repository after publication. Do not include
real credentials, personal data, customer information, or production logs in a report.

## Data handling

The committed scenarios must remain fictional. Generated audit and health artifacts are
ignored by Git. Review every artifact before sharing it publicly, even though the audit
layer performs basic email and phone redaction.

## Important limitation

Regex-based redaction is data minimization, not a complete data-loss-prevention system.
A production implementation requires a reviewed classification and retention policy.
