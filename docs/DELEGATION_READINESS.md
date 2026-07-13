# ZRM delegation readiness

**Status:** candidate engineering control; no protocol or release authority  
**Author:** Dana Edwards  
**Drafting assistance:** GPT-5.6  
**Date:** 2026-07-13

## Current verdict

ZRM is not ready for blanket delegation of the remaining implementation.

The repository has a reviewed ZRM-L0 slice, strong pre-authority candidate modules, semantic contracts, bounded artifacts, assurance tooling, and draft closure semantics. It still lacks the frozen authority ABI and executable ownership boundaries for authenticated policy, state, verified facts, semantic finalization, durable commit, and accepted journals.

A bounded implementation agent can safely execute a task only when the task contains no unresolved semantic decision and cannot create authority outside an already frozen interface.

## What is safe to delegate now

The machine-readable plan currently marks only two task classes as immediately delegable:

1. evidence reconciliation for already merged candidate slices; and
2. deterministic adversarial-corpus expansion for already frozen WP1, WP3, WP5, and RFC-0003 behavior.

These tasks cannot promote conformance, approve an RFC, mint authority, or change accepted behavior.

## What must remain in the architect lane

The following ten closure tasks require high-reasoning architectural work before broad handoff:

1. policy activation and disposition;
2. authenticated snapshot and validation context;
3. reference state, membership, nullifier, and root identity;
4. transition and exact claim-coverage ABI;
5. governed verifier registry, cost model, and sealed facts;
6. pure-kernel type state and reject precedence;
7. semantic effects, journal draft, and commit plan;
8. durable commit, retry, conflict, and indeterminate outcomes;
9. accepted-journal recursive composition; and
10. formal refinement maps and theorem statements.

The authoritative task list is `delegation/ZRM_COMPLETION_PLAN.json`.

## Handoff definition

`blanket_delegation_ready` may become true only when every architectural-closure task is marked `complete` and carries repository-verifiable evidence.

Completion requires:

- accepted decisions rather than draft prose;
- frozen canonical byte tables and domain strings for the affected task;
- private constructors and explicit authority ownership;
- an implementation-independent executable oracle;
- failing tests or exact vector targets;
- a one-boundary task packet;
- explicit counterexamples, non-goals, commands, and stop conditions;
- human merge authority for Class C-E work;
- independent semantic and authority-boundary review where required.

The gate does not infer readiness from model confidence, test count, code coverage, or an agent statement.

## Reasoning lanes

### Architect

The architect lane resolves novel semantics, canonical authority identity, constructor ownership, commit outcome algebra, recursion semantics, and theorem scope.

An architect task must not be converted to a bounded task merely by writing a more detailed prompt. The normative ambiguity must actually be removed.

### Bounded implementer

A bounded implementer receives:

- exactly one authority boundary;
- approved decision references;
- explicit source paths;
- exact CBC and semantic-contract IDs;
- preexisting failing tests or vector targets;
- an independent oracle;
- counterexamples;
- commands;
- non-goals;
- fail-closed stop conditions.

The implementer may choose local code organization that preserves the contract. It may not choose new accepted behavior, weaken a binding, change canonical bytes, add a fallback, or self-promote the result.

### Mechanical evidence

The mechanical-evidence lane may:

- replay revision-bound commands;
- reconcile matrix and evidence references;
- add deterministic seeds derived from frozen behavior;
- generate reports;
- improve non-authority test utilities;
- check documentation and package consistency.

It may not resolve semantic disagreements or convert corroborative evidence into approval.

### Human or external

Maintainer semantic approval, independent authority-boundary review, external security audit, and release authorization remain human or externally accountable gates.

## Machine-enforced rules

Run:

```text
python3 tools/check_delegation_plan.py
```

The checker fails closed when:

- task IDs are missing, duplicated, reordered, or cyclic;
- a task names more than one authority boundary;
- a CBC or semantic-contract ID is unknown;
- a delegable task has an incomplete dependency;
- a delegable task retains an unresolved decision;
- its oracle is only planned or is missing;
- the v1 human and independent review policy is weakened;
- completion lacks durable evidence;
- handoff readiness is asserted before all closure tasks complete;
- a task path escapes the repository;
- the safe-now summary differs from actual task state.

CI runs the same checker and its negative tests.

## Task-state transitions

The only normal transitions are:

```text
architect_required
  -> complete

blocked
  -> delegable
  -> complete

human_only
  -> complete
```

A task moves from `blocked` to `delegable` only after every dependency is complete, all decisions are resolved, and the oracle is available.

A task moves to `complete` only after evidence references exist. A task cannot mark itself complete by editing its own state without adding the required evidence.

## Recommended assignment policy

Use the least capable agent that can satisfy the frozen contract:

| Work | Minimum lane |
| --- | --- |
| Evidence hashes, command replay, deterministic corpus maintenance | mechanical evidence |
| One frozen codec, validator, reference module, or adapter slice | bounded implementer |
| Cross-module integration after all interfaces are frozen | bounded implementer with stronger review |
| New semantic choice, canonical ABI, authority ownership, commit semantics | architect |
| Independent approval, audit, release authorization | human or external |

Escalate immediately when a bounded agent encounters:

- an ambiguous field;
- an unlisted accepted or rejected state;
- oracle disagreement;
- a missing authority source;
- a required ABI change;
- an unexpected cross-boundary dependency;
- solver `UNKNOWN`, nondeterminism, or a counterexample not covered by the packet.

## Completion strategy

The shortest safe route is:

```text
authority decisions and ABI
  -> executable independent oracles
  -> bounded reference implementations
  -> pure kernel and finalization
  -> durable reference runtime
  -> formal/refinement closure
  -> two materially different adapters
  -> proof and recursion adapters
  -> independent release review
```

Do not parallelize implementation ahead of an unresolved predecessor merely to increase apparent throughput. That creates integration debt at precisely the boundaries where ZRM must be fail closed.

## Non-claims

The delegation plan and checker are process controls. They do not:

- approve RFC-0001 or RFC-0002;
- freeze a canonical authority ABI;
- implement a complete semantic kernel;
- establish authenticated state, policy, facts, persistence, atomic commit, recursion, or production release;
- replace semantic review, formal proof, security audit, or human release authorization.
