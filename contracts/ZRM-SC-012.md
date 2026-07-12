# ZRM-SC-012 — Policy governance, versioning, and release claims

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

A successful governance operation may activate, revoke, or replace a machine, resource-kind, verifier, accumulator, DA, or release policy only within the exact scope authenticated by the governance profile.

Documentation and release metadata may claim only the conformance level supported by linked evidence.

## Inputs

### Untrusted

- proposed policy objects and roots;
- governance signatures/proofs before verification;
- release artifacts, build metadata, and agent-generated evidence;
- migration and rollback assertions.

### Governed

- governance authority root and verifier policy;
- current policy/state/version;
- canonical policy schema and hash;
- revocation/activation rules;
- release environment, provenance, and reviewer requirements.

### Derived

- policy IDs/roots;
- activation/revocation decision;
- new policy/state version;
- release claim set.

## Preconditions and invariants

1. Policy contents are canonical, bounded, versioned, and content-bound before activation.
2. Governance artifacts are authenticated against the exact proposed policy, action, machine/domain, current policy/state, nonce, and validity window.
3. Activation/revocation atomically changes the policy root and state version.
4. Every plan built on the predecessor policy/context becomes stale.
5. Creation policy and predecessor acceptance are separate: accepting an old policy for consumption does not authorize new creation under it.
6. Revocation semantics state whether already-created resources remain readable/consumable and preserve liveness or intentionally block with explicit governance consequences.
7. A schema field reorder, semantic reinterpretation, domain change, authority identity change, state-root change, nullifier change, or journal meaning change is Class E and requires a new version plus replay/migration analysis.
8. Unknown critical versions fail closed; no runtime downgrade.
9. Rollback cannot restore an authority state in a way that re-enables consumed resources, revoked verifier releases, or replayed nonces.
10. Production authority binds exact verifier/release digests and TCB.
11. Build/test/proof evidence is reproducible or its independence limits are stated. Agent assertions and local gates alone do not create release provenance.
12. Public terms such as “verified,” “private,” “available,” “final,” “production-ready,” and “audited” are scoped to active evidence and non-claims.
13. Promotion requires all blocking CBC obligations, semantic contracts, independent reviews, and release gates for that profile.
14. There is no production claim before an external or organizationally independent audit of the integrated authority-bearing system.

## Required postconditions

- Activated policy identity and contents are unambiguous.
- State, policy, and replay semantics remain coherent across the update.
- Release claims exactly match the evidence bundle and unresolved gaps.
- Failure leaves policy/state unchanged.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| Same policy ID with altered contents | Rejection |
| Governance signs only a root but action/domain/nonce are unbound | Rejection |
| Verifier revoked but cached policy remains usable | Rejection |
| Rollback resurrects consumed resource | Forbidden |
| New schema silently interpreted as old | Rejection |
| Old creation policy remains usable merely because it is readable | Rejection |
| Local CI described as independent audit | Claim failure |
| Production release with unresolved Class D/E contract | Promotion blocked |
| Build path differs but provenance claims reproducibility | Claim blocked |

## Required evidence

- policy hash and governance-statement vectors;
- activation/revocation/stale-plan model;
- predecessor liveness and creation-policy tests;
- downgrade/cross-version/replay tests;
- migration and rollback analysis;
- TCB, SBOM/CBOM, provenance, and reproducibility evidence;
- independent authority-boundary review;
- integrated external audit before production.

## Non-claims

Governance authentication does not imply wise policy, democratic legitimacy, physical-world truth, or complete migration safety unless separately specified and evidenced.

## Specification anchors

Sections 0, 4, 7.2, 9.7, 11.2, 15, 30, 37, and the release/conformance sections of the implementation plan.
