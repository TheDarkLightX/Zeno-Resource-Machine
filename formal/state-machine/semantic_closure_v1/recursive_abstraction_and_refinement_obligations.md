# Recursive semantic-composition refinement obligations

**Package:** `zrm-semantic-closure-v1`
**Normative candidate:** `rfcs/RFC-0002-recursive-semantic-journal-composition.md`
**Bounded oracle:** `zrm_recursive_semantic_composition_v1`
**Status:** Draft design evidence; no recursive-proof or production claim
**Author:** Dana Edwards
**Drafting assistance:** GPT-5.6

## 1. Bounded abstraction

The internal bounded model represents three ordered accepted-journal leaves.
Each leaf projects:

```text
pre-state root and version
post-state root and version
derived position range
leaf count
bounded semantic-effect total
descendant membership bits
empty message boundary
empty carry boundary
```

It constructs both associations:

```text
left  = compose(compose(a, b), c)
right = compose(a, compose(b, c))
```

and requires equality of every modeled semantic field. The model is finite and
does not establish hash collision resistance, arbitrary sets, arbitrary depth,
canonical serialization, proof-system soundness, storage correctness, or an
enabled message/carry algebra.

## 2. Concrete abstraction map

For an authenticated `AcceptedJournal` leaf `j`:

| Abstract field | Concrete projection |
| --- | --- |
| pre/post root | exact authenticated machine-state roots |
| pre/post version | exact authenticated state versions |
| start position | `j.pre_state_version` |
| end position | `j.post_state_version` |
| leaf count | exactly one |
| semantic effect | selected projection of `j.semantic_effects_root` and summary |
| descendants | membership of selected identities in authenticated child sets |
| messages | named empty inbox/outbox roots and zero counts |
| carry | named empty pre/post roots and zero count |

For an intermediate summary `s`:

```text
alpha(s) = {
  pre_root      := abstract_root(s.first_pre_machine_state_root),
  post_root     := abstract_root(s.last_post_machine_state_root),
  pre_version   := s.first_pre_state_version,
  post_version  := s.last_post_state_version,
  start         := s.start_position,
  end           := s.end_position,
  leaf_count    := s.leaf_count,
  effect        := selected_semantic_effect_projection(s),
  descendants   := selected_memberships(s),
  messages      := empty_boundary_projection(s),
  carry         := empty_carry_projection(s)
}
```

Finite abstract roots may identify different concrete roots. Concrete code must
compare complete typed roots directly.

## 3. Leaf derivation

For every authenticated accepted journal `j`:

```text
alpha(derive_postcommit_leaf(j)) = abstract_leaf(j)
```

The constructor must establish:

```text
j.post_state_version = j.pre_state_version + 1
leaf.start_position  = j.pre_state_version
leaf.end_position    = j.post_state_version
leaf.leaf_count      = 1
```

The caller supplies none of those derived values. Every remaining field is
derived from or exactly matched to authenticated journal commitments.

## 4. Composition soundness

For every concrete pair accepted by the reference composer:

```text
AbstractCompose(alpha(x), alpha(y)) is defined
alpha(ConcreteCompose(x, y)) = AbstractCompose(alpha(x), alpha(y))
```

Composition is defined only when:

```text
x.scope = y.scope
x.end_position = y.start_position
x.last_post_state_root = y.first_pre_state_root
x.last_post_state_version = y.first_pre_state_version
```

The parent covers the exact left-then-right interval:

```text
parent.start_position = left.start_position
parent.end_position   = right.end_position
parent.leaf_count     = checked_add(left.leaf_count, right.leaf_count)
parent.leaf_count     = parent.end_position - parent.start_position
```

For every security-critical abstract rejection, concrete code rejects without
creating a parent semantic capability.

## 5. No extra authority

A recursive verifier node authenticates only the summary produced by the
reference composer:

```text
VerifiedNode(artifact, expected_summary) ->
  authenticated_output(artifact) = canonical(expected_summary)
```

The host and proof adapter cannot add, omit, reorder, deduplicate, or reinterpret
a leaf, identity, accounting row, semantic effect, message boundary, carry
boundary, or availability certificate.

## 6. Associativity and order

The required parameterized theorem is:

```text
For all valid ordered summaries a, b, c under one fixed profile,
if both sides are defined:

  compose(compose(a, b), c) = compose(a, compose(b, c)).
```

Equality covers:

- derived range and state-version endpoints;
- machine-state-root endpoints;
- ordered manifest concatenation;
- exact disjoint descendant-set union;
- typed accounting combination;
- semantic-effect combination;
- fixed empty message and carry boundaries;
- availability-certificate union; and
- canonical semantic-segment hash derivation.

Composition is noncommutative. Canonicalization cannot sort children by hash,
proof size, arrival order, or any other host-selected key.

## 7. Semantic and proof identity

For valid proof trees `p1` and `p2` over the same ordered accepted-journal
sequence:

```text
semantic_summary(p1) = semantic_summary(p2)
semantic_segment_hash(p1) = semantic_segment_hash(p2)
```

Proof identities may differ because they bind different tree topology,
programs, releases, profiles, or receipt identities. Proof identity is not a
transition, accounting, or semantic-epoch identity.

The semantic segment hash is derived after the complete semantic summary. It is
not included in its own preimage.

## 8. Sets and manifests

The first profile uses bounded explicit vectors and must establish:

```text
ordered_manifest(parent) = ordered_manifest(left) || ordered_manifest(right)
set(parent) = exact_disjoint_union(set(left), set(right))
count(parent) = checked_add(count(left), count(right))
```

For every descendant set:

- inputs are canonical before hashing;
- duplicate detection precedes or accompanies sorting;
- no silent deduplication occurs;
- count equals the exact materialized set;
- set roots are domain-separated by semantic role; and
- a root without a union/disjointness witness grants no composition authority.

An optimized accumulator needs a separate refinement theorem to this relation.

## 9. Accounting and semantic effects

For each typed accounting dimension `d`:

```text
parent.row[d] = checked_add(left.row[d], right.row[d])
```

Different resource kinds and units remain separate. Absent rows are canonical
zeros only when the schema explicitly permits that representation.

The parent semantic-effect summary is the exact profile-defined combination of
child semantic-effect summaries. Recursive composition creates no new ZRM
effect and does not include replay records, accepted-journal metadata, state-head
metadata, or commit audit metadata as semantic effects.

## 10. First-profile message and carry exclusion

`SerializedSemanticCompositionV1` selects `NoMessagesV1` and `NoCarryV1`.
Every leaf and parent contains:

```text
cross_partition_inbox_root = EMPTY_CROSS_PARTITION_INBOX_ROOT_V1
cross_partition_outbox_root = EMPTY_CROSS_PARTITION_OUTBOX_ROOT_V1
cross_partition_inbox_count = 0
cross_partition_outbox_count = 0
carry_pre_root  = EMPTY_CARRY_ROOT_V1
carry_post_root = EMPTY_CARRY_ROOT_V1
carry_item_count = 0
```

Any nonempty boundary, nonzero count, or unsupported profile rejects. The
implementation cannot silently accept opaque roots and defer their meaning.

An enabled message or carry algebra requires a separate Class E RFC, model,
canonical ABI, and refinement proof.

## 11. Availability obligations

The parent preserves every child availability requirement and derives an exact
certificate union. A content commitment alone is not availability. Missing or
unverifiable required evidence rejects; recursive proof success cannot weaken
the selected availability profile.

## 12. Verifier and host refinement

For every bounded witness accepted by an optimized recursive verifier:

```text
VerifierSummary(witness) = ReferenceComposer(witness)
```

The host constructs untrusted witness bytes. The verifier independently checks:

- bounds before allocation;
- canonical child summaries;
- child proof, program/key, and release identity;
- exact scope, range, state, set, accounting, semantic-effect, empty-boundary,
  and availability conditions;
- exact parent derivation; and
- exact public-output schema.

A host-computed validity Boolean or parent root grants no authority.

## 13. Required evidence

Before promotion:

- a bounded reference model with concrete omission, position-substitution, and
  nonempty-boundary counterexamples;
- an independently written reference composer;
- exact singleton, two-leaf, and three-leaf vectors;
- permutation, omission, duplication, substitution, overlap, and overflow
  tests;
- bounded merge harnesses;
- parameterized associativity and tree-shape-independence theorems;
- verifier/reference differential tests;
- child proof and release substitution tests;
- canonical byte tables and independent vectors;
- worst-case resource-cost bounds; and
- independent semantic, proof-system, and accumulator review.

## 14. Non-claims

These obligations do not establish RFC correctness, cryptographic or proof-system
soundness, arbitrary-depth recursion, accumulator soundness, enabled message or
carry semantics, availability, consensus, finality, privacy, or production
readiness.
