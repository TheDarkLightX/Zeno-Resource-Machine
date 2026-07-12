# ZRM-SC-009 — Accounting and authorized transformation

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

Successful accounting validation establishes that the explicit resource delta is unit-safe and either conserved or covered exactly by governed mint, burn, or transformation authority.

## Inputs

### Untrusted

- proposed accounting rows or totals;
- resource quantities and units;
- claim descriptors;
- purported authority/transformation outputs.

### Governed

- policy-valid canonical resource lists;
- accounting modes;
- sealed authority and transformation facts;
- allowed transformation sets and subject-root profiles.

### Derived

- one accounting row per `(ResourceKindId, UnitId)`;
- consumed/created totals;
- authorized mint/burn totals;
- transformation coverage;
- canonical accounting root.

## Preconditions and invariants

1. The kernel derives accounting rows from canonical resources and authenticated facts. Proposed rows are non-authoritative and, if accepted for efficiency, must equal recomputation exactly.
2. Rows are sorted and unique by `(resource_kind_id, unit_id)`. Duplicate dimensions reject rather than merge implicitly.
3. Quantities are nonnegative explicit-width integers. Summation and all conversions use checked arithmetic.
4. Floating point is forbidden.
5. Values with different `UnitId` values are never added, compared as fungible amounts, or silently converted.
6. For each row:

   ```text
   consumed + authorized_mint = created + authorized_burn
   ```

7. `ConservedFungible` has zero authorized mint and burn.
8. `AuthorityMintableFungible` mint/burn is covered by exact authority facts.
9. `Transformable` unmatched deltas are covered exactly once by allowed transformation facts.
10. Every transformation-authorized delta appears in accounting, and every unmatched accounting delta is covered. Extra, overlapping, partial, or unused authorization rejects.
11. Lifecycle/evidence semantics do not smuggle fungible value through numeric fields.
12. Rewards, fees, slashes, escrow movement, issuance, destruction, and residuals are explicit resources and rows; no verifier output creates hidden balances.
13. The recomputed accounting root equals the statement commitment.

## Required postconditions

- The accepted transition has one deterministic, unit-safe accounting interpretation.
- No value effect exists outside explicit resources, rows, and authenticated authority/transformation coverage.
- Failure creates no `ValidatedTransition` and mutates no state.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| Same numeric amount under different units | Never combined; mismatch/conversion requires transformation |
| Duplicate row dimensions | Rejection |
| Overflow during aggregate | Rejection |
| Caller totals differ from derived totals | Rejection |
| Conserved mode includes mint | Rejection |
| Transformation covers only part of unmatched delta | Rejection |
| Two facts cover same non-shareable delta | Rejection |
| Valid transformation authorizes extra unused output | Rejection |
| Fee or reward exists only in verifier metadata | Rejection |
| Floating-point conversion | Architectural review failure |

## Required evidence

- independent accounting reference model;
- property tests over resource permutations;
- unit-substitution and duplicate-row tests;
- arithmetic boundary/overflow model;
- exact transformation coverage matrix;
- mint/burn authority negatives;
- no-hidden-value tests;
- accounting-root vectors once canonical bytes are frozen.

## Non-claims

Accounting validity does not establish market fairness, economic value, price correctness, solvency outside the committed state, or physical-resource conservation.

## Specification anchors

Sections 9.6, 14, 20.2, 21, 22, and 25.
