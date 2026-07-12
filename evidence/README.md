# Evidence records

This directory stores replayable, scoped assurance records. Execution records are immutable snapshots: later review decisions use new records instead of rewriting the historical result. A record reports its source revision, dirty-tree status, exact tool and command, result, assumptions, exclusions, and non-claims. A record never grants production authority by itself.

The WP1 local gate replay is recorded in `wp1-local-gates-2026-07-10.json`. The completed Class C human review is recorded separately in `wp1-class-c-review-2026-07-11.json`. The unreviewed WP2 candidate replay is recorded in `wp2-local-gates-2026-07-11.json`; that record does not promote WP2.

WP3 evidence is staged by boundary. `wp3a-local-gates-2026-07-11.json` covers the structural role partition. `wp3b-local-gates-2026-07-11.json` covers intrinsic resource construction. `wp3c-local-gates-2026-07-12.json` covers binding one intrinsic body to its exact position in a supplied canonical partition, including three patch-bound manual authority mutants. `wp3c-ci-fuzz-remediation-2026-07-12.json` records the later hosted no-op-mutation counterexample, constructional fix, deterministic regression seed, and clean-archive replay. WP3c remains an unreviewed Class C candidate. Hosted CI, human review, merge, release, funds-safety, and production evidence remain separate requirements.
