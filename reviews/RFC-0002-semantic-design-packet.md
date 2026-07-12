# RFC-0002 semantic design and adversarial packet

**Change:** RFC-0002 recursive semantic composition
**Change class:** E
**Affected contracts:** `ZRM-SC-006`, `010`, `011`, `013`
**Normative candidate:** `rfcs/RFC-0002-recursive-semantic-journal-composition.md`
**Author:** Dana Edwards
**Drafting and authoring-track review assistance:** GPT-5.6
**Independent semantic reviewer:** Required
**Recursive-verifier reviewer:** Required before implementation promotion
**Accumulator/formal reviewer:** Required before optimized profile promotion
**Date:** 2026-07-12
**Status:** `REQUEST_INDEPENDENT_REVIEW`

This packet records the authoring track's choices and attacks. It is not an
independent approval.

## 1. Review independence disclosure

GPT-5.6 had access to RFC-0001, the ZRM specification and semantic contracts,
prior composition drafts, and the proposed bounded model. A separate reviewer
must independently derive the composition relation, challenge summary-field
completeness, and review the proof and accumulator boundaries.

## 2. Authority map

```text
Durable ZRM commit
  -> authenticated AcceptedJournal
  -> deterministic singleton semantic summary with derived position
  -> bounded explicit witness or authenticated accumulator operation
  -> exact left/right composition
  -> canonical SemanticSegmentSummary
  -> recursive verification against that exact summary
  -> sealed VerifiedPostcommitAggregationFact
  -> audit, compression, or governed anchor use
```

No edge authorizes ZRM admission or state mutation. Postcommit composition
authenticates already accepted semantics.

## 3. Principal decisions

1. `AcceptedJournal` is the native postcommit leaf.
2. Admission and postcommit aggregation use distinct statement schemas and
   sealed fact classes.
3. Leaf position derives from authenticated pre-state version; callers cannot
   assign it.
4. Parent order is exact left-then-right concatenation over a dense range.
5. State-root and state-version continuity are exact.
6. Descendant identity roots require authenticated disjoint union.
7. Accounting and semantic effects combine exactly; aggregation creates no
   effect or commit metadata.
8. The first profile selects named empty message and carry profiles and rejects
   any nonempty or unsupported boundary.
9. Semantic identity excludes proof topology and release metadata.
10. Composition is partially associative and noncommutative.
11. The first implementation uses explicit bounded witnesses before optimized
    accumulators.

## 4. Accepted-state decision table

| Case | Preconditions | Expected result |
| --- | --- | --- |
| Derive singleton leaf | authenticated journal, post version equals pre plus one, supported empty-boundary profile | deterministic singleton with start=`pre_version`, end=`post_version` |
| Compose adjacent children | exact scope, dense range, state continuity, disjoint descendants, valid accounting/effects, empty boundaries | deterministic parent summary |
| Fold three leaves left-associated | every pairwise composition defined | summary over exact ordered `a,b,c` |
| Fold three leaves right-associated | every pairwise composition defined | same complete semantic summary |
| Different valid proof tree | same ordered accepted-journal sequence and semantic profile | same semantic identity; proof identity may differ |
| Verifier-release upgrade | same semantic output and governed new release | same semantic identity; new proof identity |

## 5. Invalid-state and counterexample matrix

| Attack or defect | Required result |
| --- | --- |
| Supply `JournalDraft` or bytes plus `accepted=true` | no postcommit authority |
| Supply caller-selected leaf position | API rejection or value ignored and derived |
| Pre/post version does not advance by one for singleton | reject |
| Change scope or any profile identity | `ScopeMismatch` |
| Gap or overlap in child ranges | `RangeGapOrOverlap` |
| Reverse or host-sort children | reject or different semantic history |
| Child state root or version discontinuity | exact mismatch rejection |
| Omit, duplicate, substitute, or reorder a leaf | manifest or descendant rejection |
| Duplicate transition/nullifier/one-shot identity across children | reject before parent construction |
| Parent supplies set root without union witness | no composition authority |
| Combine unlike accounting units | dimension mismatch |
| Omit a child semantic-effect contribution | coverage rejection |
| Add aggregate-level reward or metadata effect | reject |
| Nonempty inbox/outbox/carry under first profile | unsupported or nonempty-boundary rejection |
| Opaque nonempty roots paired with zero counts | reject exact empty-root mismatch |
| Required availability verifier absent | fail closed |
| Postcommit fact used as admission | class/profile rejection |
| Correct summary under wrong program/key or release | proof-binding rejection |
| Same journal history yields tree-shape-dependent semantic hash | implementation defect |
| Segment hash appears in its own summary preimage | circular schema; reject design |

## 6. Bounded counterexample obligations

| Counterexample attempt | Required evidence |
| --- | --- |
| Caller substitutes leaf position | derived-position mutant |
| Parent range ignores authenticated versions | range/version invariant witness |
| Right fold omits middle leaf | associativity mutant |
| Nonempty message is represented by empty root/count | empty-boundary mutant |
| Sibling descendant overlap is silently deduplicated | disjoint-union mutant |
| Parent omits one child semantic effect | effect-coverage mutant |

Internal bounded-model artifacts are corroborative and are not publicly
replayable from this repository. A timeout, unknown result, parser failure,
unsupported feature, or checker disagreement does not count as mutation
evidence.

## 7. Design corrections captured by this revision

### Derived serialized position

A governed-but-independent position still required another ordering authority.
For the first serialized profile, position now derives from the accepted
journal's state version. The dense range and state-version chain become one
checkable relation.

### Closed message and carry profile

The earlier draft described enabled message cancellation and carry continuity
without a complete algebra. The first profile now admits only named empty roots
and zero counts. Enabled behavior requires a separate Class E profile.

### Semantic effects only

Recursive summaries combine journal-bound semantic effects. Replay records,
accepted-journal metadata, state-head metadata, and commit audit records remain
commit metadata and do not enter recursive effect algebra.

### Acyclic semantic identity

The semantic segment hash is derived from the complete summary after summary
construction and is absent from its own preimage.

## 8. Required formal obligations

For all valid ordered summaries under one fixed profile, when both sides are
defined:

```text
compose(compose(a, b), c) = compose(a, compose(b, c))
```

The proof covers derived ranges, state endpoints, ordered manifests, exact
disjoint unions, typed accounting, semantic effects, fixed empty boundaries,
availability evidence, and semantic hash tree-shape independence.

Supporting theorems must also establish exact singleton derivation,
noncommutativity, no postcommit-to-admission substitution, and refinement from
any optimized accumulator to the explicit-vector reference relation.

## 9. Required implementation evidence

- an independently written reference composer;
- exact singleton, two-child, and three-child vectors;
- permutation, omission, duplication, substitution, overlap, and overflow
  atlases;
- compile-fail or API tests for caller-position injection;
- bounded set and row merge harnesses;
- stateful composition-witness fuzzing;
- parameterized associativity and tree-shape proofs;
- verifier/reference differential tests;
- child proof program/key/release substitution tests;
- exact empty-message and empty-carry rejection tests;
- canonical bytes and independent vectors;
- worst-case resource bounds; and
- independent semantic, proof-system, and accumulator review.

## 10. Residual gaps and non-claims

- RFC-0002 remains a draft.
- GPT-5.6's authoring-track review is not independent approval.
- Internal bounded evidence is finite and not publicly replayable here.
- No canonical semantic-segment or proof-node bytes are frozen.
- No production accumulator, recursive verifier, or release is selected.
- Enabled message and carry semantics remain undefined by this profile.
- No cryptographic, availability, consensus, finality, privacy, or
  production-readiness claim is made.

## 11. Requested independent-review outcome

Reviewers should select:

- `APPROVE`;
- `APPROVE_WITH_TRACKED_GAPS`;
- `REQUEST_CHANGES`;
- `BLOCK_AMBIGUOUS_SPEC`; or
- `BLOCK_UNSATISFIED_AUTHORITY_OBLIGATION`.

Current authoring-track outcome:

```text
REQUEST_INDEPENDENT_REVIEW
```
