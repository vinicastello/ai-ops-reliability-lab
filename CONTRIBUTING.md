# Contributing

Contributions should preserve the project's verification-first approach.

1. Add a failing regression that demonstrates the behavior.
2. Make the smallest policy or pipeline change that resolves it.
3. Run the complete test suite.
4. Use only fictional data.
5. Do not add external API calls to tests.

Changes that weaken ownership, idempotency, confirmation, or audit integrity require an
explicit design rationale in the pull request.
