# ZRM-SC-008 — Claim semantics and exact authenticated-fact coverage

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

Successful claim authentication establishes that every committed logic, transformation, authority, and DA claim has exactly the required governed fact and that no unaffiliated fact influences the transition.

## Inputs

### Untrusted

- claim descriptors;
- artifact arrays;
- purported facts from outside the registry;
- expected outputs.

### Governed

- resource-kind and machine policies;
- canonical claim ordering and cardinality;
- governed verifier registry;
- profile-defined subject/input/output/root derivations.

### Derived

- claim and child-statement hashes;
- exact expected output roots;
- coverage mapping;
- `VerifierSetRoot`.

## Preconditions and invariants

1. Every claim descriptor is proof-independent, canonical, identity-matched, in-window, and committed before `StatementHash`.
2. Each committed claim has exactly one artifact slot and exactly one matching sealed fact unless the policy explicitly defines another bounded cardinality.
3. Missing, duplicate, extra, reordered, or cross-class artifacts/facts reject.
4. No sealed fact may satisfy two non-shareable claims.
5. `VerifierSetRoot` contains the sorted unique policy IDs used by finalized facts plus the expected admission policy when required. Claim multiplicity remains committed by claim roots.
6. Logic facts bind resource ID, role, ordinal, logic/profile, controller/policy roots, parent statement, and exact output.
7. Logic output cannot create hidden value movement. Every effect remains explicit in resources and accounting.
8. Transformation facts bind exact input-resource root, output-resource root, delta rows, parameters, evidence, authority, parent statement, and rule/profile.
9. Two transformations cannot cover the same non-shareable role or delta unless a profile explicitly defines composition and deterministic order.
10. Authority facts bind exact action/subject, affected resources or accounting effects, signer registry, policy, nonce, epoch, and parent statement.
11. DA facts bind exact content root, expected certificate root, profile, verifier policy, parent statement, and validity window.
12. A commitment to data does not establish availability. When policy requires DA, missing or unavailable verification rejects.
13. Extra authorization is not harmless: an authenticated fact that is not exactly consumed by the transition's coverage relation rejects.

## Required postconditions

- Every committed claim is covered exactly as policy requires.
- Every accepted fact is consumed by exactly one permitted coverage relation.
- The resulting authenticated set is canonical and bound to the parent transition.
- Failure is a state no-op.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| One logic fact reused for same resource under another role | Rejection |
| Correct claims and artifacts but one artifact slot swapped | Rejection |
| Extra valid authority signature not referenced by a claim | Rejection |
| Transformation covers a delta absent from accounting | Rejection |
| DA content commitment present but certificate missing when required | Rejection |
| Logic output implicitly mints value not represented by resources | Rejection |
| Same fact appears twice | Rejection |
| Admission policy omitted from draft verifier set | Rejection |
| Postcommit verifier included in precommit set | Rejection |

## Required evidence

- exact coverage matrix by fact class;
- missing/duplicate/extra/permuted test atlas;
- role/ordinal/resource substitution tests;
- hidden-effect and extra-authorization negatives;
- verifier-set-root vectors;
- DA commitment-versus-availability tests;
- independent reference coverage model.

## Non-claims

Authenticated claims do not by themselves establish conservation, post-state correctness, durable commit, or external truth.

## Specification anchors

Sections 18.3, 19, 20, 22, 30.4, and 32.
