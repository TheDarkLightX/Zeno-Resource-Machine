# ZRM/ZRPF ESSO semantic-closure package

**Package ID:** `zrm-semantic-closure-esso-v1`  
**Date:** 2026-07-12  
**Status:** Draft bounded design oracle; requires independent review  
**ESSO source:** `TheDarkLightX/ESSO@8a38735257cb12454e3457ee59cf28bb9f970661`  
**ESSO draft PR:** `TheDarkLightX/ESSO#1`

## Purpose

This package closes a selected set of open semantic questions before ZRM and
ZRPF implementation proceeds. It combines:

- two draft Class E RFCs;
- machine-readable semantic decisions;
- an intent-to-obligation map;
- explicit abstraction and refinement obligations;
- six bounded ESSO models;
- six targeted disaster mutants;
- Z3 and CVC5 replay evidence;
- an authoring/adversarial review packet;
- explicit non-claims and follow-up obligations.

It does not approve its own semantics and does not create protocol authority.

## Draft RFCs

- [`RFC-0001`](../../../rfcs/RFC-0001-policy-context-fact-and-commit-authority.md): policy disposition, trusted context, verifier-fact freshness, complete commit effects, atomic commit, recovery, and idempotent retry.
- [`RFC-0002`](../../../rfcs/RFC-0002-recursive-semantic-journal-composition.md): accepted-journal semantic leaves, ordered segment composition, descendant/effect coverage, partial associativity, and semantic-versus-proof identity.

## Machine-readable decisions

- [`semantic_decisions.json`](semantic_decisions.json): twelve ZRM policy/context/fact/commit decisions.
- [`recursive_semantic_decisions.json`](recursive_semantic_decisions.json): ten ZRPF composition decisions.
- [`intent_map.json`](intent_map.json): intent leaves mapped to semantic contracts, ESSO invariants, mutants, and explicit unmodeled obligations.

## Refinement obligations

- [`abstraction_and_refinement_obligations.md`](abstraction_and_refinement_obligations.md): maps five ZRM ESSO models to concrete ZRM state and implementation obligations.
- [`recursive_abstraction_and_refinement_obligations.md`](recursive_abstraction_and_refinement_obligations.md): maps the bounded composition model to the reference composer, recursive guest, accumulator, and parameterized theorem obligations.

## Evidence

- [`evidence/zrm-semantic-closure-esso-v1.json`](../../../evidence/zrm-semantic-closure-esso-v1.json): exact ESSO revision, workflow IDs, six model hashes, six mutant hashes, solver profile, discoveries, claim scope, and non-claims.
- [`reviews/RFC-0001-semantic-design-packet.md`](../../../reviews/RFC-0001-semantic-design-packet.md): accepted-state and invalid-state matrices plus information-flow disclosure.

## Bounded model results

| Model | ESSO IR hash | Result |
| --- | --- | --- |
| policy lifecycle | `sha256:9fbc36ed6fba5e7941bda6f50bb300f060ae307ede0ca9338997abbd2ad25a85` | canonical, 1-inductive, Z3/CVC5 PASS |
| plan freshness | `sha256:8536afed0692e0214fba13a4bbf379e4c96c4259a09a150b6baba073d2362147` | canonical, 1-inductive, Z3/CVC5 PASS |
| exact once | `sha256:9c97929a06272ebfaccc96e5ef1465b2cb1aaa789dfe877b57b7b7bf67b919e8` | canonical, 1-inductive, Z3/CVC5 PASS |
| verifier fact freshness | `sha256:883a5cd35185dee2ed4ba44c5f8acc576cbcd9462b28296047dc8e67949d4d83` | canonical, 1-inductive, Z3/CVC5 PASS |
| atomic commit recovery | `sha256:474c806539afb760cdb1dfb79c40e8d9fd1fd29a6dc64597a0d99f28a1cf9f16` | canonical, 1-inductive, Z3/CVC5 PASS |
| recursive composition | `sha256:180d12605766063b7f97e51321be989442b4d9ae80fbfde5331c8c4255b69676` | canonical, 1-inductive, Z3/CVC5 PASS |

Targeted mutants all produced concrete `InvNotInductive` witnesses:

- creation under the wrong policy;
- stale plan commit;
- duplicate effect on exact retry;
- Development-mode production fact;
- partial durable commit;
- recursive fold omitting the middle child.

## Semantic decisions selected for review

### ZRM

1. One exact non-revoked current creation policy per resource kind.
2. Predecessor policies authorize existing-resource compatibility only.
3. Hard revocation removes all normal use and may strand resources.
4. Every uncommitted fact and plan is exact-context-bound.
5. Production facts bind lifecycle class, snapshot, release, statement, and output.
6. Every durable effect is explicit and included in a complete effect root.
7. New commit linearizes on one root/version/context comparison plus atomic write.
8. Exact durable retry returns `AlreadyCommitted` without reapplying effects.
9. Same transition identity with different journal/effects is a replay conflict.
10. Admission and postcommit recursion are distinct authority classes.
11. External delivery remains at-least-once without receiver idempotency.
12. Policy rollback is a new version and never recreates an old snapshot tuple.

### ZRPF

1. Authenticated `AcceptedJournal` is the native postcommit semantic leaf.
2. Semantic identity is separate from proof identity.
3. Segment order is dense, explicit, and noncommutative.
4. State-root and state-version continuity are exact.
5. Descendant uniqueness requires authenticated disjoint union.
6. Aggregation creates no hidden ZRM effects.
7. Message and carry boundaries are explicit.
8. Composition is partial associative over the same ordered valid leaves.
9. The first profile uses explicit bounded witnesses before optimized accumulators.
10. Recursion does not imply DA, consensus, or finality.

## Design discoveries

The ESSO pass changed the package in three useful ways:

1. Reused enum symbols were rejected as ambiguous, so every model domain was
   namespaced before any proof result was accepted.
2. The first plan model was reachable-safe but not inductive: `PlanNone` did not
   explicitly exclude already-visible effects. `PlanNoneIsPristine` was added.
3. Mutant acceptance was tightened: only a concrete invariant witness counts;
   parser, unsupported, timeout, `unknown`, or generic solver failure does not.

## Next implementation sequence

1. Obtain independent semantic and authority-boundary review of both RFCs.
2. Freeze canonical byte tables and independent vectors in a separate Class E
   change.
3. Implement a slow reference policy/state/fact/commit machine.
4. Differential-test optimized Rust paths against the reference relation.
5. Add Kani, Loom, mutation, stateful fuzzing, and crash injection.
6. Implement the bounded explicit-vector recursive composer.
7. Prove parameterized set, exact-once, recovery, associativity, and tree-shape
   independence theorems.
8. Add governed recursive guest/release and accumulator profiles.

## Non-claims

- The RFCs are drafts and may be changed or rejected.
- The authoring track is not an independent reviewer.
- ESSO evidence is finite and assumption-bound.
- No implementation refinement has been proved.
- No new authority codec or hash ABI is frozen.
- No hard-revocation recovery protocol is provided.
- No exact-once external delivery, privacy, DA, consensus, finality, or
  production-readiness claim is made.
