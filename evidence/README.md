# Evidence records

This directory stores replayable, scoped assurance records. Execution records are immutable snapshots: later review decisions use new records instead of rewriting the historical result. A record reports its source revision, dirty-tree status, exact tool and command, result, assumptions, exclusions, and non-claims. A record never grants production authority by itself.

Before a candidate record first reaches the default branch, a prohibited
generic local-context string may be replaced only through a recorded privacy
correction. The original bytes remain identified by commit and SHA-256; the
exact gate is rerun from the same source revision using a repository-relative
ignored output; a separately named correction record binds every old and new
record, result, index, and worklog hash; a successor index names that correction;
and independent privacy plus evidence review is required. The correction may
change only nonsemantic execution-location data and the hashes necessarily
derived from the rerun. It cannot change pass/fail status, source, scope,
assumptions, exclusions, or non-claims silently. After default-branch merge,
release, or promotion, records are never replaced; later work adds a new record.
This procedure never applies to secrets, credentials, confidential project
names, or private repository context, which require immediate disclosure
containment and history remediation under the security policy.

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

`wp5-path-correction-2026-07-12.json` binds the pre-merge privacy correction
for two generic execution-output locations, their exact-source reruns, the
successor index, and the unchanged behavioral results.

`security-remediation-main-integration-2026-07-12.json` binds PR #9's merge
onto the WP3c, semantic-closure, and WP5 default-branch history. It preserves
the original security receipts byte-for-byte, records the branch-local
RFC-0002 to integrated RFC-0003 identity correction, binds every renamed oracle
artifact, and reports the combined-tree replay. It does not approve RFC-0003 or
promote the security remediation.

`rfc-0003-maintainer-approval-2026-07-12.json` records Dana Edwards's explicit
semantic approval after review and merge of PR #9. It accepts the positive v1
quantity and lifecycle-maximum-one rules while retaining CBC-046 as partial and
preserving every policy, verifier, state, commit, release, and production
non-claim.
