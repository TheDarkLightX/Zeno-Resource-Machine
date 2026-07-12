# Evidence records

This directory stores replayable, scoped assurance records. Execution records are immutable snapshots: later review decisions use new records instead of rewriting the historical result. A record reports its source revision, dirty-tree status, exact tool and command, result, assumptions, exclusions, and non-claims. A record never grants production authority by itself.

The WP1 local gate replay is recorded in `wp1-local-gates-2026-07-10.json`. The completed Class C human review is recorded separately in `wp1-class-c-review-2026-07-11.json`. The unreviewed WP2 candidate replay is recorded in `wp2-local-gates-2026-07-11.json`; that record does not promote WP2.

WP3 evidence is staged by boundary. `wp3a-local-gates-2026-07-11.json` covers the structural role partition. `wp3b-local-gates-2026-07-11.json` covers intrinsic resource construction. `wp3c-local-gates-2026-07-12.json` covers binding one intrinsic body to its exact position in a supplied canonical partition, including three patch-bound manual authority mutants. `wp3c-ci-fuzz-remediation-2026-07-12.json` records the later hosted no-op-mutation counterexample, constructional fix, deterministic regression seed, and clean-archive replay. WP3c remains an unreviewed Class C candidate. Hosted CI, human review, merge, release, funds-safety, and production evidence remain separate requirements.

WP5 bounded-artifact evidence is split between the historical pre-reconciliation
receipt `wp5-bounded-artifact-2026-07-12.json` and the current integrated index
`wp5-integrated-2026-07-12.json`. The integrated index binds the clean replayed
source, environment policy, per-gate records, deterministic reservation-refusal
tests, generated and manual mutation results, Miri, coverage, and explicit
gaps. It remains local Class C candidate evidence. It grants no authenticated
policy limit, verifier fact, dispatch, state, commit, merge, release, or
production authority.

`wp5-main-integration-2026-07-12.json` records the later merge onto the
semantic-closure default-branch history. It proves ancestry and unchanged WP5
source hashes and records combined-tree gates; it does not promote the prior
coverage, mutation, or Miri results beyond their exact source revision.
