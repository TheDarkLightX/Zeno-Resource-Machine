## Summary

## Linked issue / RFC / ADR

- Issue:
- RFC:
- ADR:

## Change class

- [ ] A — documentation
- [ ] B — non-authority tooling
- [ ] C — semantic implementation
- [ ] D — stable authority implementation
- [ ] E — protocol/authority/release breaking

## Semantic contract impact

- Affected contract IDs (`ZRM-SC-*`):
- Exact contract clauses:
- Normative specification/RFC clauses:
- [ ] No semantic contract impact; rationale is recorded below.
- [ ] Any broadened or changed accepted behavior is authorized by an approved specification/RFC change.
- [ ] Every unresolved behavior fails closed or blocks this change.

## Motivation

## Non-goals

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

## Invariants and CBC obligations

## Authority boundary

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

## Canonical ABI / migration impact

## Security and disaster-state analysis

## Design-choice review

- Design forces:
- Pattern selected, or no additional pattern:
- Invalid states prevented:
- Extension point or closed-set reason:
- Alternatives rejected:
- Pattern-specific failure modes:
- Enforcement and tests:
- Technical AI-review status:

## Test and assurance evidence

Behavior-and-evidence summary for human review:

- Specified behaviors confirmed:
- Exact assurance results:
- CBC obligations covered:
- Semantic contracts covered:
- Counterexamples attempted:
- Remaining gaps and non-claims:

- [ ] unit/invariant
- [ ] BDD
- [ ] property/metamorphic
- [ ] mutation
- [ ] fuzz
- [ ] differential
- [ ] independent oracle/vector replay
- [ ] compile-fail/API sealing
- [ ] Miri/Loom
- [ ] Kani
- [ ] deductive/theorem/model
- [ ] release replay

Commands and results:

```text

```

For each unchecked conditional gate, explain why it is not applicable. Mark unavailable, timed-out, or unrun tools as gaps.

## Dependency and supply-chain impact

## Performance/resource impact

## Documentation, contracts, vectors, and matrix updates

## Rollback plan

## Remaining gaps and non-claims

## Agent or generated contribution disclosure

- [ ] no agent-generated or agent-modified content
- [ ] agent assistance used; work log and provenance linked below

Work log/provenance:

## Required reviewers and sign-off

- Semantic owner:
- Independent oracle reviewer (Class C-E):
- Adversarial reviewer (Class C-E):
- Authority-boundary reviewer (Class D/E):
- Compatibility/formal reviewer (Class E):
- Release owner (Class E):
