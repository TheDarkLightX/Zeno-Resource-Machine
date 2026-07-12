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

## Motivation

## Non-goals

## Invariants and CBC obligations

## Authority boundary

## Semantic change declaration

- Authority affected:
- Attacker-controlled fields:
- Governed fields:
- New valid states:
- New invalid states:
- Invariants preserved:
- Invariants changed:
- Cryptographic bindings added or changed:
- Replay/freshness implications:
- Resource-bound implications:
- Upgrade/revocation implications:
- Failure behavior and precedence:
- Independently derived tests/oracle:

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
- Remaining gaps and non-claims:

- [ ] unit/invariant
- [ ] BDD
- [ ] property/metamorphic
- [ ] mutation
- [ ] fuzz
- [ ] differential
- [ ] Miri/Loom
- [ ] Kani
- [ ] deductive/theorem/model
- [ ] release replay

Commands and results:

```text

```

For each unchecked conditional gate, explain why it is not applicable. Mark unavailable, timed-out, or unrun tools as gaps.

Independent specification-counterexample review:

- Reviewer:
- Normative rules sampled:
- Counterexamples proposed:
- Disposition/evidence:

## Dependency and supply-chain impact

## Performance/resource impact

## Documentation, vectors, and matrix updates

## Rollback plan

## Remaining gaps and non-claims

## Agent or generated contribution disclosure

- [ ] no agent-generated or agent-modified content
- [ ] agent assistance used; work log and provenance linked below

Work log/provenance:

## Required reviewers and sign-off

- Semantic owner:
- Independent non-author counterexample reviewer:
- Authority-boundary reviewer (Class D/E):
- Compatibility/formal reviewer (Class E):
- Release owner (Class E):
