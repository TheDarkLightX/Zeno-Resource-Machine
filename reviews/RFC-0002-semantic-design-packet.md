# RFC-0002 semantic design and adversarial packet

**Change or PR:** RFC-0002 recursive semantic composition package  
**Change class:** E  
**Affected contracts:** `ZRM-SC-006`, `ZRM-SC-010`, `ZRM-SC-011`, `ZRM-SC-013`  
**Normative candidate:** `rfcs/RFC-0002-recursive-semantic-journal-composition.md`  
**Authoring/oracle proposer:** OpenAI GPT-5.6 Pro  
**Specification owner:** Dana Edwards  
**Independent semantic reviewer:** Required; not yet assigned  
**Recursive-proof reviewer:** Required; not yet assigned  
**Accumulator/formal reviewer:** Required; not yet assigned  
**Date:** 2026-07-12  
**Status:** `REQUEST_INDEPENDENT_REVIEW`

> This packet records the authoring track's choices, bounded oracle, and attacks. It is not independent approval because the same reasoning track proposed the RFC and model.

## 1. Independent-review qualification

```text
Review type:
  Authoring and adversarial corroboration.

Information available:
  ZRM specification, semantic contracts, RFC-0001, existing ZRPF design and
  harness, and the ESSO implementation.

Prior involvement:
  The same model drafted RFC-0001 and the bounded ESSO suite.

Required separate review:
  A reviewer must independently derive the composition relation, challenge the
  summary field completeness, and inspect the proof-system/accumulator boundary
  without treating this packet as the oracle of record.
```

## 2. Authority map

```text
Durable ZRM commit
  -> authenticated AcceptedJournal
  -> deterministic semantic leaf summary
  -> bounded composition witness or authenticated accumulator operations
  -> exact left/right child semantic composition
  -> canonical SemanticSegmentSummary
  -> recursive proof verification against that exact summary
  -> sealed VerifiedPostcommitAggregationFact
  -> audit / compression / anchor use only
```

No edge points back into ZRM admission or state mutation. Recursive aggregation authenticates and compresses already accepted semantics; it does not authorize a new ZRM transition.

## 3. Principal semantic decisions

1. `AcceptedJournal`, not `JournalDraft` or bytes plus a Boolean, is the native postcommit leaf.
2. Admission and postcommit aggregation use distinct statement schemas, profiles, and sealed fact types.
3. Segment order is represented by a dense interval and exact left-then-right manifest concatenation.
4. State-root and state-version continuity are exact.
5. Descendant identity roots require an authenticated disjoint-union relation; a root alone proves neither uniqueness nor union.
6. Accounting and commit effects are exact combinations of child commitments; aggregation creates no hidden effect.
7. Message cancellation, carry continuity, and DA preservation are explicit profile operations, not inferred from child validity.
8. Semantic identity excludes recursive topology and release metadata; proof identity includes them.
9. Composition is partial associative for the same ordered valid leaves and is not commutative.
10. The first implementation uses explicit bounded witnesses before optimized accumulators.

## 4. Accepted-state decision table

| Case | Preconditions | Expected result |
| --- | --- | --- |
| Derive a leaf | Authenticated `AcceptedJournal`, supported schema/profile, governed position | Deterministic singleton `SemanticSegmentSummary` |
| Compose adjacent children | Exact scope, dense range, state continuity, disjoint descendants, valid row/effect/message/carry/DA relations | Deterministic parent summary |
| Fold three leaves left-associated | Both pairwise compositions defined | Complete summary over `a,b,c` |
| Fold three leaves right-associated | Both pairwise compositions defined | Same complete semantic summary as left fold |
| Different valid proof tree | Same ordered accepted-journal sequence and semantic profile | Same semantic hash; possibly different proof identity |
| Upgrade recursive verifier release | Semantic output unchanged and new release governed | Same semantic identity; new proof identity |
| Postcommit anchor | Exact accepted-journal/segment bytes and governed anchor profile | Anchor fact only; no admission or state authority |

## 5. Invalid-state and counterexample matrix

| Attack or defect | Required result |
| --- | --- |
| Supply `JournalDraft` as postcommit leaf | Type/profile rejection |
| Supply raw journal bytes with `accepted=true` | No authority |
| Change machine, domain, application, epoch, policy, suite, accumulator, or semantic profile | `ScopeMismatch` |
| Create a gap or overlap in child ranges | `RangeGapOrOverlap` |
| Reverse children | Normally undefined; never silently sorted |
| Child post-state differs from next pre-state | `StateRootMismatch` |
| State root matches but version does not | `StateVersionMismatch` |
| Omit, duplicate, substitute, or reorder a leaf | `ManifestMismatch` or descendant duplicate |
| Duplicate transition or nullifier across children | Reject before parent construction |
| Parent supplies a set root without union witness | No composition authority |
| Combine rows with unlike units | `AccountingDimensionMismatch` |
| Omit one child accounting or effect row | coverage rejection |
| Add aggregate-level reward not present in a ZRM journal | reject; aggregation creates no effect |
| Cancel messages by count or key without payload/source/destination match | `MessageMismatch` |
| Reuse one inbox against two outboxes | `MessageReplay` |
| Carry post/pre roots differ | `CarryMismatch` |
| Required DA verifier unavailable | fail closed; no downgrade |
| Postcommit receipt used as admission | class/profile rejection |
| Correct semantic summary under wrong recursive program or release | proof binding rejection |
| Same journals under another proof tree produce a different semantic hash | design or implementation defect |

## 6. Bounded ESSO oracle

**Repository:** `TheDarkLightX/ESSO`  
**Branch:** `agent/zrm-semantic-closure-v1`  
**Draft PR:** `TheDarkLightX/ESSO#1`  
**Model:** `zrpf_semantic_composition_v1`  
**IR hash:** `sha256:180d12605766063b7f97e51321be989442b4d9ae80fbfde5331c8c4255b69676`

The model represents three ordered leaves with:

- bounded pre/post endpoints;
- bounded leaf counts;
- bounded effect totals;
- two descendant-membership bits;
- pairwise descendant disjointness;
- left- and right-associated composition paths.

The positive model is canonical and 1-inductive. It also passes the recorded Z3/CVC5 multi-solver workflow. The targeted mutant changes the right fold to omit the middle leaf count. ESSO produces a concrete `InvNotInductive` witness on `finish_right` with mutant hash `sha256:3e3dacb718a0e2e929bca3ab85b5c2f4514f676ce09330f5762323d7b5843c62`.

## 7. What the bounded oracle does and does not test

### Covered

- two grouping orders over one fixed ordered three-leaf sequence;
- state endpoint continuity assumptions;
- pairwise disjointness for two selected descendant identities;
- count and effect folding;
- equality of complete modeled summaries;
- omission of a middle child contribution.

### Not covered

- cryptographic roots or canonical byte encodings;
- arbitrary-length manifests or identity sets;
- typed multi-dimensional accounting;
- message, carry, or DA algebra;
- proof receipt soundness;
- guest/host refinement;
- arbitrary-depth recursion;
- production accumulator soundness;
- release migration or data availability.

Those remain explicit formal and implementation obligations rather than silently inheriting a PASS from the bounded model.

## 8. Alternatives considered

### Proof-tree root as semantic identity

Rejected. It makes economically identical ordered journal histories depend on grouping, prover choice, or recursive implementation. It also complicates release upgrades.

### Sort child journals before aggregation

Rejected. ZRM transitions are ordered through state continuity. Sorting destroys semantic order and can create disconnected or reordered histories.

### Trust valid leaves to be globally nonconflicting

Rejected. Individually valid leaves can conflict across siblings through duplicate transitions, nullifiers, created resources, rewards, assignments, receipts, or messages.

### Set roots without authenticated operations

Rejected. Equality of opaque roots does not establish disjointness, concatenation, or exact union. The first profile recomputes from bounded witnesses; optimized profiles must prove the relation.

### Allow aggregate-level effects

Rejected. Recursive compression is not a ZRM transition and must not mint value, pay rewards, consume messages, or alter state outside accepted child journals.

### Begin with an optimized sparse accumulator

Deferred. A slow explicit-vector reference profile makes the semantics auditable and supplies a refinement target for later accumulator proofs.

### Treat composition as commutative

Rejected. State transitions, manifests, messages, and many accounting relations are order-sensitive. Associativity is the desired tree-shape law, not commutativity.

## 9. Formal obligations

A parameterized proof must cover the complete summary rather than only counts:

```text
compose(compose(a,b),c) = compose(a,compose(b,c))
```

for all valid ordered summaries under one fixed profile when both sides are defined.

Required supporting theorems include:

- exact leaf derivation;
- dense range concatenation;
- state-root and version endpoint preservation;
- ordered manifest associativity;
- exact disjoint set union and count preservation;
- accounting and effect fold associativity with checked bounds;
- message-boundary composition associativity for enabled profiles;
- carry continuity;
- DA coverage preservation;
- semantic hash tree-shape independence;
- proof identity binds semantic identity and release;
- postcommit facts cannot satisfy admission.

## 10. Implementation evidence required

- independent reference composer outside the recursive guest;
- exact leaf, two-child, and three-child vectors;
- permutation, omission, duplication, substitution, and overlap atlases;
- Kani bounded set/row merge harnesses;
- stateful fuzzing of composition witnesses;
- Lean or equivalent associativity and tree-shape-independence proofs;
- guest/reference differential tests;
- child receipt program/release substitution tests;
- explicit message, carry, and DA models;
- canonical byte tables and independent vectors;
- governed verifier cost and resource-envelope model;
- independent semantic, recursive-proof, and accumulator reviews.

## 11. Residual gaps and non-claims

- RFC-0002 is not approved protocol semantics.
- This authoring track is not independent approval.
- The bounded model does not prove arbitrary recursion or complete summary algebra.
- No canonical semantic-segment or proof-node bytes are frozen.
- No production accumulator, recursive guest, or release is selected.
- No cryptographic, DA, consensus, finality, privacy, or production-readiness claim is made.

## 12. Requested review outcome

The independent reviewers should select one:

- `APPROVE`;
- `APPROVE_WITH_TRACKED_GAPS`;
- `REQUEST_CHANGES`;
- `BLOCK_AMBIGUOUS_SPEC`;
- `BLOCK_UNSATISFIED_AUTHORITY_OBLIGATION`.

Current authoring-track outcome:

```text
REQUEST_INDEPENDENT_REVIEW
```
