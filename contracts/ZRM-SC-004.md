# ZRM-SC-004 — Transition structure, witness, roles, and roots

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

Successful prevalidation may create a private `PrevalidatedTransition` that establishes structural and policy-relative consistency and carries the exact verifier statements expected for later authentication.

It does not establish that proof, signature, authority, transformation, or DA artifacts are valid.

## Inputs

### Untrusted

- transition statement and witness;
- resource bodies and membership proofs;
- claim descriptors and proof artifacts;
- proposed counts, roots, ordinals, accounting rows, and derived IDs.

### Governed

- trusted validation context;
- authenticated machine and resource-kind policies;
- pre-state view and protocol limits;
- canonical role and claim ordering rules.

### Derived

- every resource and claim ID/hash;
- role-local ordinal;
- canonical list order and roots;
- `StatementHash`/`TransitionId`;
- exact proof-bound child statements;
- expected artifact slots.

## Preconditions and invariants

1. Envelope bytes, arrays, counts, artifact totals, and nesting are bounded before allocation.
2. The statement and every child resource, policy, claim, authority, and DA descriptor have exact machine/domain/application equality.
3. `TransitionId` is derived from `StatementHash`; no independent caller-selected transition ID exists.
4. Resource roles are closed: consumed, referenced, or created.
5. Every role list is duplicate-free, sorted by `ResourceId`, and pairwise disjoint.
6. `resource_ordinal` is derived from the canonical list and cannot be caller-selected.
7. Claim lists use the exact specification ordering. Canonicalization never silently deduplicates.
8. Every public count equals the corresponding canonical list length and remains within policy and protocol ceilings.
9. Every committed root is recomputed from the exact canonical values.
10. Optional roots use their named canonical empty roots. A nonempty optional root is either validated under policy or rejected as unchecked data.
11. Claim descriptors are committed before the parent `StatementHash`; proof-bound child statements are formed afterward, preserving acyclic construction.
12. Witness artifact arrays are index-paired with canonical claim arrays. Missing, duplicate, permuted, or extra slots reject.
13. The first-phase witness contains no admission artifact. Admission authenticates the later `JournalDraft` through a separate bounded API.
14. Prevalidation performs no cryptographic trust promotion and no committed mutation.

## Required postconditions

`PrevalidatedTransition` privately binds:

- the exact canonical transition statement and hash;
- the context and pre-state snapshot;
- canonical resources, roles, ordinals, claim descriptors, and roots;
- expected verifier statements and artifact slots;
- effective limits and admission reservation requirements.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| Same `ResourceId` appears consumed and referenced | Rejection |
| Duplicate created resource | Rejection |
| Valid list with caller-chosen wrong ordinal | Rejection |
| Claim/artifact arrays are the same length but permuted | Rejection |
| Public count differs from list length | Rejection |
| Parent root includes a child statement that embeds parent hash | Construction rejected as cyclic |
| Cross-application child relabeled under parent | Rejection |
| Nonempty evidence root is ignored | Rejection |
| Admission artifact supplied in phase one | Rejection |
| Proposed accounting row accepted without recomputation | No authority |

## Required evidence

- exhaustive role-collision matrix;
- property tests over all role/list permutations;
- count/root/ordinal mutation atlas;
- missing/duplicate/extra/reordered claim-artifact tests;
- independent statement/root vectors once codecs are frozen;
- bounded parser and allocation fuzzing;
- compile-fail test for constructing `PrevalidatedTransition` outside its module.

## Non-claims

Prevalidation establishes no proof validity, controller authority, conservation, post-state correctness, or commit authority.

## Specification anchors

Sections 16, 17, 18, 19.1, 20.1, and 24.3.
