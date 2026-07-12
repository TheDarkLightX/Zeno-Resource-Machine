# ZRM High-Assurance Review Checklist

Use this checklist for Class C-E changes. A checkbox means the reviewer inspected evidence; it does not mean the author stated that evidence exists.

## Semantic contracts and independent review

- [ ] The pull request names every affected `ZRM-SC-*` contract and exact clause.
- [ ] The contract is traceable to `SPECIFICATION.md` or an approved RFC and does not broaden the normative accepted state space.
- [ ] Any unresolved semantic behavior fails closed or blocks the change as `BLOCK_AMBIGUOUS_SPEC`.
- [ ] An accepted-state decision table and invalid-state/counterexample matrix exist.
- [ ] The oracle reviewer derived expected behavior before receiving implementation rationale or implementation-authored tests, or the review is explicitly labeled corroborative rather than independent.
- [ ] The oracle/reference artifact has separate author/tool/model/version provenance and a stable path or digest.
- [ ] Implementation-to-oracle discrepancies are classified and dispositioned; the oracle was not edited merely to fit observed code.
- [ ] Counterexample review includes identifier/content substitution, domain/version/role substitution, downgrade, stale/revoked policy, coverage defects, overflow, replay, partial mutation, concurrent conflict, unchecked optional data, and composition failure where applicable.
- [ ] The author is not counted as the required independent approver.
- [ ] Class D/E changes have two independent approvals, including an authority-boundary reviewer.
- [ ] Integrated composition receives a distinct review after component-level review.

## Semantics

- [ ] Exact typed statement is defined.
- [ ] Consumed, referenced, and created resources are explicit.
- [ ] Resource role sets are disjoint.
- [ ] Units and accounting behavior are explicit.
- [ ] Every nonconserved delta has transformation authority.
- [ ] Policy, domain, version, and validity range are bound.
- [ ] Every child resource, policy, claim, authority, and DA identity equals the parent transition identity.
- [ ] Epoch and expiry checks use an independently trusted validation context.
- [ ] Reject behavior and precedence are stable.
- [ ] Non-goals and non-claims are explicit.

## Authority

- [ ] Raw bytes and metadata remain untrusted.
- [ ] Verified facts are sealed and cannot be caller-constructed.
- [ ] Program/key/profile/statement/policy bindings are exact.
- [ ] Identifier equality cannot substitute for authenticated content binding.
- [ ] Governed registries, not requests, supply authoritative policy and verifier contents.
- [ ] Revocation and rotation are handled.
- [ ] No host boolean is the sole authority for a safety property.
- [ ] Generated proof/artifact is reverified before use.
- [ ] Precommit facts, admission facts, and postcommit aggregation facts bind the correct lifecycle object.

## Canonical data

- [ ] Encoding is versioned, bounded, and canonical.
- [ ] Duplicate keys/IDs and trailing bytes reject.
- [ ] Unknown critical fields reject.
- [ ] Domain separators and field order are documented.
- [ ] Independent vectors exist.
- [ ] One-field mutations change the correct commitments.
- [ ] Raw bytes cannot impersonate sealed canonical-byte provenance at an authority API.
- [ ] Default diagnostics redact full nonces and sensitive opaque values.

## State and accounting

- [ ] Membership/existence checks use expected pre-state.
- [ ] Nullifiers are domain separated and exact once.
- [ ] Output uniqueness includes historical recreation policy.
- [ ] Arithmetic is checked, explicit-width, and unit-safe.
- [ ] No floating point enters semantic authority.
- [ ] State root and journal are derived deterministically.
- [ ] Resource-kind policy constructors reject unsatisfiable combinations.
- [ ] Current v1 rejects zero quantity unless a versioned policy explicitly grants marker semantics.
- [ ] Verifier cost rows are selected from the authenticated model rather than supplied by the caller.

## Atomicity and concurrency

- [ ] Validation produces a private commit plan; it does not mutate.
- [ ] Commit binds expected pre-state version/root.
- [ ] Replay state, effects, rewards, journal, and outbox are atomic.
- [ ] Journal drafts become accepted journals only through successful durable commit.
- [ ] Crash injection covers every persistence boundary.
- [ ] Conflicting commits have at most one winner.
- [ ] Disjoint transitions commute or deterministic ordering is defined.
- [ ] v0.1 durable commits remain serialized by the global root/version CAS.

## Defensive coding

- [ ] Dependency direction remains inward.
- [ ] Critical functions satisfy complexity budgets or have justified exceptions.
- [ ] Code-smell and antipattern findings are absent or exactly dispositioned.
- [ ] The selected design pattern, or no additional pattern, fits the stated forces and failure modes.
- [ ] AI design-choice evidence records alternatives, enforcement, tests, and review status.
- [ ] No panic-prone API in authority paths.
- [ ] Unsafe code is absent or isolated with a safety case.
- [ ] Untrusted collections, recursion, and allocations are bounded.
- [ ] Errors/logs do not disclose secrets.
- [ ] Comments explain invariants and rationale.

## Evidence

- [ ] Accepted, boundary, and negative tests exist.
- [ ] Every critical reject asserts state no-op.
- [ ] Relevant critical mutant is killed.
- [ ] Property/metamorphic tests cover the input family.
- [ ] Parser/proof envelopes have fuzz coverage.
- [ ] Optimized code is differential-tested against reference semantics.
- [ ] Miri/Loom/Kani/formal tools are routed appropriately.
- [ ] Tool bounds, assumptions, exclusions, and versions are recorded.

## Supply chain and release

- [ ] Dependency TCB delta is reviewed.
- [ ] Lockfile and features are intentional.
- [ ] Advisory/license policies pass.
- [ ] Build scripts/proc macros/native code are reviewed.
- [ ] Generated sources are reproducible.
- [ ] Provenance, SBOM/CBOM, signatures, and replay requirements are updated.
- [ ] Reproducibility language matches actual independent evidence.

## Claims

- [ ] README/docs/UI claims match the active conformance status.
- [ ] “verified,” “private,” “available,” “final,” and “production-ready” are scoped.
- [ ] No private project name or confidential context is exposed publicly.
- [ ] CBC matrix refs and status are accurate.
- [ ] Remaining disaster states and non-claims are preserved.

## Final review outcome

Select exactly one:

- [ ] `APPROVE`
- [ ] `APPROVE_WITH_TRACKED_GAPS`
- [ ] `REQUEST_CHANGES`
- [ ] `BLOCK_AMBIGUOUS_SPEC`
- [ ] `BLOCK_UNSATISFIED_AUTHORITY_OBLIGATION`

Reviewer rationale:
