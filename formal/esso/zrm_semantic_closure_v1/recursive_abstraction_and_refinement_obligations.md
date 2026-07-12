# ZRPF semantic composition abstraction and refinement obligations

**Package:** `zrm-semantic-closure-esso-v1`  
**Normative candidate:** `rfcs/RFC-0002-recursive-semantic-journal-composition.md`  
**Bounded oracle:** `zrpf_semantic_composition_v1`  
**Status:** Draft design evidence; not a recursive-proof or production claim

## 1. Model abstraction

The ESSO model represents three ordered semantic leaves `a`, `b`, and `c`.
Each leaf projects only:

```text
pre-state endpoint
post-state endpoint
bounded leaf count
bounded effect total
two descendant-membership bits
```

The model assumes:

- `a.post = b.pre`;
- `b.post = c.pre`;
- the modeled descendant memberships are pairwise disjoint;
- integer additions remain within the declared finite domains;
- composition does not create an additional effect.

It then constructs:

```text
left  = compose(compose(a, b), c)
right = compose(a, compose(b, c))
```

and requires equality of semantic endpoints, counts, effect totals, and
descendant union.

The model does not represent hashes, canonical bytes, journal authority,
verifier releases, arbitrary sets, accounting dimensions, messages, carry,
data availability, proof receipts, or storage.

## 2. Concrete abstraction map

For an accepted journal leaf `j`:

| ESSO field | Concrete projection |
| --- | --- |
| `pre` | `j.pre_machine_state_root` |
| `post` | `j.post_machine_state_root` |
| `count` | one leaf, or a bounded child leaf count for intermediate summaries |
| `effect` | one selected additive projection of complete commit effects |
| membership bits | membership of selected descendant identities in the child set |

ESSO integers stand for typed roots or bounded quantities only through an
explicit abstraction function. Integer equality models exact typed root
equality; no arithmetic is performed on roots.

For a concrete summary `s`, define:

```text
alpha(s) = {
  pre              := abstract_root(s.first_pre_machine_state_root),
  post             := abstract_root(s.last_post_machine_state_root),
  count            := bounded_projection(s.leaf_count),
  effect           := selected_effect_projection(s.commit_effects),
  member_i         := selected_identity_i in descendants(s)
}
```

The finite abstraction may identify different concrete roots. Therefore the
ESSO proof cannot establish collision resistance or exact concrete root
continuity. Concrete verification must compare full typed roots directly.

## 3. Refinement obligations

## 3.1 Leaf derivation

For every authenticated accepted journal `j`:

```text
alpha(derive_leaf(j)) = abstract_leaf(j)
```

and every field of the concrete leaf summary must be derived from or matched to
an authenticated journal commitment. A caller-supplied summary cannot satisfy
this obligation.

## 3.2 Composition soundness

For every concrete pair `x`, `y` accepted by the reference composer:

```text
EssoCompose(alpha(x), alpha(y)) is defined
alpha(ConcreteCompose(x, y)) = EssoCompose(alpha(x), alpha(y))
```

For each security-critical abstract rejection—scope mismatch, range gap,
state discontinuity, duplicate selected identity, or arithmetic overflow—the
concrete implementation must reject or establish a stronger concrete reason
that implies no semantic parent is created.

## 3.3 No extra authority

A concrete recursive proof node may authenticate only the semantic summary
computed by the reference composer:

```text
VerifiedNode(artifact, expected_summary) ->
  authenticated_output(artifact) = canonical(expected_summary)
```

The proof adapter cannot add, omit, reorder, deduplicate, or reinterpret a leaf,
identity, accounting row, effect, message, carry value, or DA certificate.

## 3.4 Associativity

The parameterized theorem required beyond ESSO is:

```text
For all valid ordered summaries a, b, c under one fixed semantic profile,
if both sides are defined:

  compose(compose(a,b),c) = compose(a,compose(b,c)).
```

Equality is complete semantic-summary equality, not merely equality of one root
or count.

The proof must establish associativity for every field:

- range addition and dense ordering;
- state and version endpoints;
- ordered manifest concatenation;
- exact disjoint set union;
- accounting combination by typed dimension;
- complete effect combination;
- profile-defined message boundary composition;
- carry composition;
- DA certificate union;
- canonical semantic hash derivation.

A non-associative field blocks the profile rather than being excluded from the
summary.

## 3.5 Noncommutativity

The implementation and specification must preserve order:

```text
compose(a,b) is not interchangeable with compose(b,a).
```

Canonicalization must not sort child segments by hash or proof size. Reordered
children reject unless a separate semantic profile explicitly defines and
proves commutativity for the complete relation.

## 3.6 Semantic versus proof identity

For any two valid proof trees `p1`, `p2` over the same ordered accepted-journal
sequence:

```text
semantic_summary(p1) = semantic_summary(p2)
semantic_segment_hash(p1) = semantic_segment_hash(p2)
```

Their proof identities may differ because they bind distinct topology,
recursive programs, releases, profiles, or receipt identities.

The concrete implementation must not use proof identity as the transition,
economic, or semantic epoch identity.

## 4. Set and manifest obligations

The bounded model uses two membership bits. The concrete first profile uses
bounded explicit vectors and must establish:

```text
ordered_manifest(parent) = ordered_manifest(left) || ordered_manifest(right)
set(parent) = exact_disjoint_union(set(left), set(right))
count(parent) = count(left) + count(right)
```

for every descendant set named by the profile.

Required properties:

- inputs are canonical before hashing;
- duplicate detection precedes or accompanies sorting;
- no silent deduplication;
- count matches the exact materialized or proven set;
- set roots are domain separated by semantic role;
- ordered manifests are never represented as commutative sets;
- a root without a union/disjointness witness grants no set-composition
  authority.

An optimized proof-carrying accumulator needs a separate refinement theorem to
this explicit-vector relation.

## 5. Accounting and effects obligations

The ESSO `effect` integer is only one additive projection. Concrete composition
must handle all typed rows and one-shot keys.

For each accounting dimension `d`:

```text
parent.row[d] = checked_add(left.row[d], right.row[d])
```

where absent rows are canonical zeros only when the schema explicitly permits
that representation. Different resource kinds or units remain separate.

For complete commit effects:

```text
parent.effects = exact profile-defined combination of child effects
```

A recursive node creates no new ZRM effect. Segment-level fees, rewards,
transformations, or messages require explicit accepted ZRM transitions or a new
profile with separately authorized semantics.

## 6. Message and carry obligations

For message-enabled profiles:

- internal cancellation matches exact key, payload, source, destination,
  ordering, and replay domain;
- every consumed message has exactly one producer;
- every internal producer has exactly one consumer when cancellation is
  claimed;
- unmatched messages remain on the external boundary;
- duplicate message creation or consumption rejects;
- message order is preserved when semantically relevant.

Carry composition requires exact equality:

```text
left.carry_post_root = right.carry_pre_root
```

and the parent uses the left pre-carry and right post-carry. Carry cannot hide
accounting, messages, or machine-state discontinuity.

## 7. Data-availability obligations

The parent preserves every child DA requirement and derives an exact
certificate union. A content commitment alone is not availability. A missing or
unverifiable required DA certificate rejects; recursive proof success cannot
weaken the DA profile.

## 8. Guest/host refinement

For every bounded witness accepted by an optimized recursive guest:

```text
GuestSummary(witness) = ReferenceComposer(witness)
```

The host constructs untrusted witness bytes. The guest or governed verifier
must independently check:

- bounds before allocation;
- canonical child summaries;
- child receipt/program/release identity;
- exact scope, range, state, set, accounting, effect, message, carry, and DA
  conditions;
- exact parent derivation;
- exact public output schema.

A host-computed `valid=true` or parent root is not authority.

## 9. Required evidence

Before promotion:

- bounded ESSO model and omission counterexample;
- independent reference composer outside the recursive guest;
- exact two-leaf and three-leaf vectors;
- permutation, omission, duplication, and substitution atlas;
- descendant overlap and arithmetic overflow mutants;
- message, carry, and DA failure models;
- Kani bounded merge harnesses;
- Lean associativity and tree-shape-independence theorems;
- guest/reference differential tests;
- child receipt and release substitution tests;
- canonical byte tables and independent vectors;
- resource-cost model for worst-case composition;
- independent semantic, proof-system, and accumulator review.

## 10. Non-claims

This bounded model and obligation document do not establish:

- correctness of RFC-0002;
- cryptographic hash or proof-system soundness;
- arbitrary-depth or unbounded recursion;
- concrete accumulator soundness;
- complete accounting, message, carry, or DA implementation;
- consensus, finality, availability, or privacy;
- production readiness.
