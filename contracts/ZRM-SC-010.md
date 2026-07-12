# ZRM-SC-010 — Pure semantic kernel, finalization, and commit plan

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

Successful finalization may create:

- a private `ValidatedTransition`;
- a private `CommitPlan`;
- a canonical but non-authoritative `JournalDraft`.

`CommitPlan` authorizes only one later atomic commit attempt against its exact bound state/context and admission rule.

## Inputs

### Untrusted

No raw request data enters this stage except through previously constructed typed values. Raw artifacts remain outside the pure finalizer.

### Governed/trusted

- `PrevalidatedTransition`;
- exact `AuthenticatedFacts`;
- policy-selected admission mode and cost plan;
- deterministic state/update algorithms.

### Derived

- exact fact coverage;
- accounting rows;
- deletes, inserts, nullifiers, replay keys, conflict footprint;
- post roots and state version;
- canonical journal payload/hash;
- bound commit plan.

## Preconditions and invariants

1. The authority pipeline remains explicit:

   ```text
   UntrustedBytes
     -> BoundedBytes
     -> CanonicalEnvelope
     -> PrevalidatedTransition
     -> AuthenticatedFacts
     -> ValidatedTransition
     -> CommitPlan + JournalDraft
   ```

2. No stage is represented by a boolean field on one mutable struct.
3. Finalization requires exact fact coverage and validates authenticated outputs.
4. Accounting, transformation coverage, state delta, and post roots are recomputed deterministically.
5. Computed post-state root equals the statement's claimed post-state root.
6. `CommitPlan` binds exact pre-state root/version, `ValidationContextHash`, machine policy, transition ID, state delta, replay keys, `JournalDraftHash`, verifier cost plan, and expected admission policy.
7. `CommitPlan` and trusted intermediate types have private fields, no `Deserialize`, no unchecked constructor, and preferably no `Clone`.
8. `JournalDraft` cannot be publicly converted into `AcceptedJournal`.
9. Prevalidation and finalization are pure: no I/O, clock, environment, network, filesystem, RNG, global mutable state, async side effects, or committed mutation.
10. Core paths use no unsafe code, panics, unchecked arithmetic, floating point, nondeterministic iteration, or platform-dependent identity.
11. Rejection precedence is stable and independent of scheduling. Parallel verification may not alter the chosen result or plan.
12. Every failure before commit is a state and external-effect no-op.
13. Complexity remains reviewable; security-relevant control flow, arithmetic, and field order are not hidden by generic abstractions or macros.

## Required postconditions

The plan is safe to present to the commit adapter only if:

- its exact pre-state/context still match;
- its admission requirement is satisfied exactly;
- the adapter can atomically apply its complete write set.

The draft is deterministic data, not evidence of acceptance.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| Missing authenticated fact | Finalization rejection |
| Extra fact | Finalization rejection |
| Computed post root differs by one byte | Rejection |
| Plan can be serialized/deserialized by caller | API review failure |
| Plan can be constructed with public fields | API review failure |
| Draft converted to accepted journal without commit | Type-system/API impossibility |
| Finalizer reads wall clock or database | Architecture failure |
| Rejection after a preliminary state write | Critical failure |
| Parallel verification changes reject code | Determinism failure |
| Boolean `is_verified` substitutes for capability | Rejection/design failure |

## Required evidence

- end-to-end reference semantic model;
- reject-is-no-op property for every stage;
- exact fact coverage and post-root mutation tests;
- capability and commit-plan compile-fail tests;
- differential tests against a simpler oracle;
- mutation testing of every critical check;
- bounded Kani/SMT/Lean/Verus obligations for exact-once/accounting/state update;
- deterministic reject-precedence tests under varied execution order.

## Non-claims

A `CommitPlan` is not committed state. A `JournalDraft` is not an accepted journal or finality proof.

## Specification anchors

Sections 5, 24, 25, 26, and 27.
