# Delegation-readiness and authority-freeze contribution

**Date:** 2026-07-13  
**Author:** Dana Edwards  
**Drafting assistance:** GPT-5.6  
**Change class:** B process/tooling plus non-normative Class E design packet  
**Promotion impact:** none

## Goal

Create a fail-closed path from the current ZRM repository state to a point where bounded implementation agents can safely complete one frozen authority boundary at a time.

## Affected files

- `delegation/ZRM_COMPLETION_PLAN.json`;
- `delegation/tasks/*.json`;
- `docs/AUTHORITY_ABI_FREEZE_PACKET.md`;
- `docs/DELEGATION_READINESS.md`;
- `tools/delegation_plan_model.py`;
- `tools/check_delegation_plan.py`;
- `tools/tests/test_delegation_plan.py`;
- `.github/workflows/ci.yml`.

## Authority boundary

This contribution creates no runtime authority. It constrains when future authority-bearing tasks may be delegated and records a candidate architecture for later approval.

## Attacker-controlled fields

The delegation plan is repository data. A contributor could attempt to:

- mark an unresolved task delegable;
- hide incomplete dependencies;
- reference nonexistent CBC or semantic contracts;
- combine several authority boundaries in one task;
- claim completion without evidence;
- assert handoff readiness prematurely;
- weaken human or independent review requirements;
- reference paths outside the repository.

The checker rejects these states.

## Governed fields

- task-state vocabulary;
- reasoning-tier vocabulary;
- change classes;
- authority-boundary name;
- dependency graph;
- CBC and semantic-contract references;
- oracle status and artifact;
- merge authority and review flags;
- handoff threshold;
- safe-now task list.

## Invariants

1. Task identifiers are sequential and unique.
2. Dependencies are known and acyclic.
3. Every task names exactly one authority boundary.
4. Every task names existing CBC and semantic-contract IDs.
5. Delegable tasks have no unresolved decisions and no incomplete dependency.
6. Delegable tasks have an available, independent, repository-present oracle.
7. Class C-E tasks retain independent review and human merge authority.
8. Class D-E tasks retain authority-boundary review.
9. Complete tasks carry repository-present evidence.
10. Blanket handoff readiness is derived from completion of all architectural-closure tasks.
11. The safe-now summary exactly matches tasks in the `delegable` state.
12. Repository paths cannot be absolute or contain parent traversal.

## Disaster states affected

- weak agent invents missing semantics;
- locally correct modules compose across incompatible authority boundaries;
- a task self-promotes from tests or model confidence;
- a draft oracle is treated as available;
- human approval or external audit is replaced by agent output;
- a plan creates a false production-readiness claim.

## Canonical bytes and hashes

No protocol canonical bytes, domain separators, identities, roots, journals, or release digests change.

## Replay, freshness, and upgrade impact

No runtime replay or freshness semantics change. The authority-freeze packet consolidates the pending decisions already represented by RFC-0001, RFC-0002, the semantic contracts, the authority map, and the implementation plan.

## Tests written first

The negative test suite covers:

- multi-boundary task;
- dependency cycle;
- unknown CBC;
- unresolved delegable work;
- incomplete delegable dependency;
- planned or missing oracle;
- missing authority review;
- non-human merge authority for semantic code;
- premature handoff;
- completion without evidence;
- repository path traversal;
- safe-now summary mismatch.

## Independent oracle plan

The checker is deterministic standard-library Python. Its accepted state is defined by the schema and tests, not by implementation-generated output. Authority-path tasks still require their own independent semantic oracles before becoming delegable.

## Counterexamples attempted

The test suite mutates one invariant at a time and requires typed `DelegationPlanError` failure. The committed plan contains two immediately delegable non-authority tasks and keeps every authority-bearing implementation task blocked behind architectural closure.

## Resource bounds

Validation is linear in task/reference count plus a depth-first traversal of the dependency graph. The plan contains 23 tasks. No network, filesystem discovery outside named repository paths, subprocess, locale, wall clock, or randomness affects the decision.

## Validation performed

- `python3 tools/check_delegation_plan.py`;
- `python3 -m unittest tools.tests.test_delegation_plan -v`.

Local isolated result before publication:

- plan checker: pass;
- 13 negative/positive tests: pass.

Hosted repository, conformance, package, Python, Rust, fuzz, assurance, dependency, and supply-chain workflows remain authoritative for the pull request.

## Non-claims

- No RFC approval.
- No canonical authority ABI freeze.
- No semantic implementation or conformance promotion.
- No claim that all remaining work is currently delegable.
- No production authority, security audit, funds-safety, proof-system, privacy, availability, consensus, or release claim.
