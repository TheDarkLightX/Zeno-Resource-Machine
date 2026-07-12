# Requests for comments

Breaking protocol, authority, or release changes require an approved RFC based
on the repository template. No RFC in this directory is approved merely because
an implementation branch exists.

## Drafts

- [`RFC-0001: Policy, Context, Fact Freshness, and Commit Authority`](RFC-0001-policy-context-fact-and-commit-authority.md) — Class E; authored by Dana Edwards with drafting assistance from GPT-5.6; defines creation suspension, context-bound facts and plans, acyclic semantic-effect commitment, linearizable commit, uncertain outcomes, idempotent retry, and admission/postcommit separation.
- [`RFC-0002: Recursive Semantic Journal Composition`](RFC-0002-recursive-semantic-journal-composition.md) — Class E; authored by Dana Edwards with drafting assistance from GPT-5.6; defines accepted-journal leaves, derived serialized positions, ordered state-continuous summaries, exact descendant/semantic-effect composition, an empty message-and-carry first profile, partial associativity, and separate semantic versus proof identity.
- [`RFC-0003: Pre-authority API Quarantine and Boundary Hardening`](RFC-0003-security-review-api-quarantine.md) — Class E review candidate; authored by Dana Edwards with drafting assistance from GPT-5.6; records the zero-quantity, canonical lifecycle, resource-ID derivation, diagnostic redaction, and unauthenticated policy-API quarantine decisions exercised by PR #9.

No RFC is approved until the maintainer records a decision after the required independent review.
