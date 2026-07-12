# ZRM semantic-closure package

**Package ID:** `zrm-semantic-closure-v1`
**Date:** 2026-07-12
**Status:** Draft Class E design package; independent review required
**Author:** Dana Edwards
**Drafting assistance:** GPT-5.6

## Purpose

This package closes selected policy, commit, retry, and recursive-composition
questions before authority-bearing implementation proceeds. It contains:

- two draft Class E RFCs;
- machine-readable semantic decisions;
- an intent-to-obligation map;
- concrete-to-abstract refinement obligations;
- counterexample-oriented authoring review packets; and
- explicit non-claims and follow-up obligations.

It does not approve its own semantics or create protocol authority.

## Draft RFCs

- [`RFC-0001`](../../../rfcs/RFC-0001-policy-context-fact-and-commit-authority.md)
  defines policy selection and suspension, trusted context, fact freshness,
  acyclic effect commitment, linearizable commit, uncertain outcomes, and
  idempotent retry resolution.
- [`RFC-0002`](../../../rfcs/RFC-0002-recursive-semantic-journal-composition.md)
  defines accepted-journal leaves, derived positions, ordered segment
  composition, descendant/effect coverage, partial associativity, and the
  deliberately empty message-and-carry first profile.

## Machine-readable decisions

- [`semantic_decisions.json`](semantic_decisions.json) records ZRM
  policy/context/fact/commit decisions.
- [`recursive_semantic_decisions.json`](recursive_semantic_decisions.json)
  records recursive semantic-composition decisions.
- [`intent_map.json`](intent_map.json) maps semantic intents to contracts,
  bounded-model obligations, counterexample mutants, and explicit deferrals.

## Refinement obligations

- [`abstraction_and_refinement_obligations.md`](abstraction_and_refinement_obligations.md)
  maps the reference policy, fact, retry, and commit models to future concrete
  ZRM state.
- [`recursive_abstraction_and_refinement_obligations.md`](recursive_abstraction_and_refinement_obligations.md)
  maps the bounded composition model to the reference composer, recursive
  verifier adapter, accumulator, and parameterized theorem obligations.

## Selected semantics

### Policy, facts, and commit

1. Creation selection is either `Enabled(CurrentPolicyId)` or `Suspended`.
2. A predecessor policy grants only the explicitly permitted existing-resource
   compatibility; it grants no creation authority.
3. Hard revocation may atomically select a replacement or suspend creation.
4. Policy updates derive a new policy root, state version, machine-state root,
   validation context, governance replay record, and audit record together.
5. Every uncommitted fact and plan binds one exact authenticated context.
6. Semantic effects are committed before journal and replay metadata, yielding
   an acyclic commitment graph.
7. Replay lookup, freshness comparison, and new commit occur inside one
   serializable or linearizable boundary.
8. Exact durable retry returns `AlreadyCommitted` without reapplying effects.
9. A retry whose durable outcome cannot be classified returns `OutcomeUnknown`
   with an inert read-only retry descriptor.
10. The same transition identity with different journal or semantic-effect
    commitments is a replay conflict.

### Recursive composition

1. An authenticated `AcceptedJournal` is the native postcommit leaf.
2. A leaf position is derived from its authenticated pre-state version.
3. Semantic identity and proof identity remain separate.
4. Parent order is exact left-then-right concatenation and is noncommutative.
5. State-root and state-version continuity are exact.
6. Descendant uniqueness requires authenticated disjoint union.
7. Aggregation combines semantic effects and creates no commit metadata.
8. The first profile requires named empty message and carry commitments and
   rejects nonempty or unsupported message/carry data.
9. Composition is partially associative for the same ordered valid leaves.
10. Recursion does not imply data availability, consensus, or finality.

## Assurance boundary

The semantic decisions have internal bounded reference models and targeted
disaster mutants. Those artifacts are corroborative design evidence. Detailed
tooling, repository metadata, run identifiers, and replay instructions are kept
outside the public package. Public readers therefore cannot independently replay
that internal evidence from this repository.

The public review oracle is the RFC text, decision files, intent map, refinement
obligations, and review packets in this package. An independent semantic reviewer
must derive and challenge expected behavior from those artifacts before any
Class E approval.

## Next implementation sequence

1. Obtain independent semantic and authority-boundary review of both RFCs.
2. Freeze canonical byte tables and independent vectors in a separate Class E
   change.
3. Implement a deliberately small reference policy/state/fact/commit machine.
4. Differential-test optimized Rust paths against the reference relation.
5. Add bounded proofs, concurrency exploration, mutation testing, stateful
   fuzzing, and deterministic crash injection.
6. Implement the bounded explicit-vector recursive composer.
7. Prove parameterized set, exact-once, recovery, associativity, and tree-shape
   independence theorems.
8. Add governed recursive verifier, release, and accumulator profiles.

## Non-claims

- The RFCs are drafts and may be changed or rejected.
- GPT-5.6's authoring pass is not independent semantic review.
- Internal bounded evidence is finite, assumption-bound, and not publicly
  replayable from this repository.
- No concrete implementation refinement has been proved.
- No new authority codec or hash ABI is frozen.
- No hard-revocation recovery protocol is provided.
- No exact-once external delivery, privacy, data availability, consensus,
  finality, or production-readiness claim is made.
