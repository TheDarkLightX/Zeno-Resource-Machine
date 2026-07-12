## Summary and motivation

## Change class

- [ ] A, documentation
- [ ] B, non-authority tooling
- [ ] C, semantic implementation
- [ ] D, stable authority implementation
- [ ] E, breaking protocol or release change

## Semantic contract impact

- Affected contract IDs (`ZRM-SC-*`):
- Exact contract clauses:
- Normative specification/RFC clauses:
- [ ] This change does not affect a semantic contract. Rationale:
- [ ] Any changed accepted behavior is authorized by an approved specification/RFC change.
- [ ] The contract and implementation fail closed on every unresolved behavior.

## Semantic change declaration

```text
Authority created, removed, or changed:
Attacker-controlled inputs:
Governed/trusted inputs:
Derived values:
Newly accepted states:
Newly rejected states:
Invariants preserved or added:
Failure and no-op behavior:
Canonical bytes, hashes, or identity impact:
State, replay, concurrency, and atomicity impact:
Resource and verifier bounds:
Residual gaps and non-claims:
```

## Invariants and disaster states

## Typed API and authority boundary

## Independent semantic review — required for Class C-E

- Oracle reviewer and provenance:
- Oracle/review-packet path and digest:
- Information supplied before the oracle pass:
- Implementation rationale/tests withheld during the oracle pass:
- Accepted-state decision table:
- Invalid-state and counterexample matrix:
- Reference model/vector source:
- Implementation-to-oracle differential result:
- Disagreements and disposition:
- Independent review outcome:

- [ ] The author is not counted as the required independent approver.
- [ ] The oracle was not changed merely to match observed implementation behavior.
- [ ] Class D/E has two independent approvals, including an authority-boundary reviewer.

## Tests and gates

List exact commands and results.

## Canonical ABI and vectors

## Dependencies and trusted-computing-base impact

## Resource bounds

## Formal or model evidence

## Migration and rollback

## Remaining gaps and non-claims

## Required reviewers
