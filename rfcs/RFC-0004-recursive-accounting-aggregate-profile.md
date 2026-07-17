# RFC-0004: Recursive Accounting Aggregate Profile

**Status:** Draft
**Author:** Dana Edwards

**Drafting assistance:** GPT-5.6
**Reviewers:** Independent semantic reviewer TBD; accounting reviewer TBD;
recursive-proof reviewer TBD
**Created:** 2026-07-14
**Target version:** ZRM 0.2 draft
**Change class:** E

## Summary

This RFC proposes the first exact accounting-aggregation profile for the
postcommit semantic segments described by RFC-0002. It replaces an ambiguous
"checked addition of accounting rows" with a separate, proof-neutral carrier
whose arithmetic result and definedness do not depend on recursive proof-tree
shape.

For each exact `(ResourceKindId, UnitId)` dimension, the carrier retains four
nonnegative gross-flow limbs:

```text
AccountingAggregateRowV1 {
  resource_kind_id
  unit_id
  consumed_total_atoms:        U256
  created_total_atoms:         U256
  authorized_burn_total_atoms: U256
  authorized_mint_total_atoms: U256
}
```

The first two fields form the resource debit/credit pair. The final two form
the authorized debit/credit pair. Componentwise natural-number addition is the
only recursive arithmetic operation. A signed net is derived by
compare-and-subtract only at an explicitly governed boundary; it is never the
recursive carrier.

The profile also requires:

- a bounded retained opening for every accepted journal's committed
  `AccountingRowV1` list;
- exact recomputation of the leaf accounting root and count;
- an ordered per-leaf, per-dimension accounting-coverage manifest;
- a content-bound accounting-aggregation profile identity;
- U256 capacity validation derived from the existing `u32` leaf count and
  `u128` leaf-row columns;
- exact canonical byte tables and new hash domains;
- Option-level associativity, including equality of failure definedness across
  every recursive tree over the same leaves; and
- explicit separation between authenticated leaf authority, aggregate data,
  proof identity, and durable commit authority.

This RFC refines only RFC-0002's accounting subrelation. It does not modify
RFC-0002 in place, approve RFC-0002, approve this RFC, implement a recursive
adapter, or change current resource, transition, accounting-row, or journal
bytes.

## Motivation

RFC-0002 currently says that accounting rows combine by exact typed dimension
using checked arithmetic and that composition is associative when both sides
are defined. That is not sufficient to make proof-tree topology semantically
irrelevant.

For a bounded signed carrier, cancellation can make intermediate definedness
depend on grouping:

```text
signed bound = 127

(127 + 1) + (-1)  -> undefined
127 + (1 + -1)    -> 127
```

Both expressions have the same mathematical sum. A prover that selects the
tree would nevertheless select whether the segment is aggregatable. Equality
conditional on both trees succeeding does not close this gap.

The existing transition-level `AccountingRowV1` is also not itself a recursive
carrier. Its numeric columns are nonnegative, but it contains leaf-local
`authority_root` and `transformation_set_root` fields. Neither field has an
approved additive, set-union, or concatenation algebra. Applying integer
addition, XOR, bare-root set union, or an implementation-selected hash fold to
those roots would invent semantics.

Finally, an accepted journal commits an accounting root and count rather than
embedding every accounting-row body. A recursive leaf cannot derive numeric
totals from a commitment alone. It requires a bounded opening that recomputes
the exact committed root. Commitment is not data availability.

This RFC therefore separates three objects:

```text
leaf accounting validity:
  exact AccountingRowV1 plus authenticated leaf-local facts

recursive numeric projection:
  four monotone U256 totals per exact dimension

recursive audit projection:
  ordered manifest of exact leaf position, journal, row, and coverage roots
```

The aggregate authenticates and compresses accepted history. It creates no
mint, burn, transformation, reward, state change, admission, or commit
authority.

## Goals

- Give RFC-0002 one explicit accounting carrier with no hidden root algebra.
- Preserve every numeric column of `AccountingRowV1` without signed recursive
  arithmetic.
- Make success and failure independent of binary proof-tree grouping.
- Preserve equal nonzero debit and credit totals when their signed net is zero.
- Keep different resource kinds and units unconditionally separate.
- Bind every aggregate contribution to an exact accepted journal and exact
  opened accounting row.
- Provide direct accounting-provenance auditability without treating bare
  authority roots as a set.
- Make profile limits, disclosure behavior, and canonical identities governed
  rather than prover-selected.
- Bound parsing, allocation, row count, manifest count, retained bytes, and
  wide arithmetic before expensive proof work.
- Define exact byte layouts and hash domains suitable for independent vectors.
- Preserve the admission/postcommit and semantic/proof authority cuts from
  RFC-0001 and RFC-0002.

## Non-goals

- Approving RFC-0001, RFC-0002, or this RFC.
- Changing `AccountingRowV1` or its existing conservation equation.
- Defining new transition-level mint, burn, conversion, transformation, fee,
  reward, slash, or escrow authority.
- Aggregating leaf authority capabilities into a new capability.
- Making accounting-row openings permanently available.
- Defining a shielded accounting profile or claiming that SHA-256 roots hide
  low-entropy amounts or policy identities.
- Selecting a production recursive proof system, accumulator, proving
  topology, or guest release.
- Making a net-zero segment a state no-op.
- Proving market fairness, solvency, price correctness, physical conservation,
  or external truth.
- Defining cross-context, cross-policy, cross-machine, or bridge accounting.
- Replacing the ordered journal manifest, state-continuity relation, or durable
  commit boundary from RFC-0001 and RFC-0002.

## Relationship to existing objects

### Transition accounting remains authoritative at the leaf

The transition-level logical row remains:

```text
AccountingRowV1 {
  resource_kind_id
  unit_id
  consumed_atoms: u128
  created_atoms: u128
  authorized_mint_atoms: u128
  authorized_burn_atoms: u128
  authority_root
  transformation_set_root
}
```

Its existing checked equation remains:

```text
consumed_atoms + authorized_mint_atoms
  == created_atoms + authorized_burn_atoms
```

The current semantic kernel, not this aggregate profile, derives and validates
that row, exact authority coverage, exact transformation coverage, units, and
the journal commitment. A recursive adapter may consume only the result of
that accepted postcommit path.

### RFC-0002 refinement

RFC-0002's draft logical summary currently has only:

```text
accounting_accumulator_root
accounting_dimension_count
```

For a semantic profile selecting this RFC, a new semantic-summary schema
supersedes that ambiguous accumulator field with:

```text
accounting_aggregate_rows_root
accounting_dimension_count
accounting_coverage_manifest_root
accounting_coverage_entry_count
retained_accounting_opening_bytes
accounting_aggregation_profile_id
```

The content-bound semantic-profile identity MUST select the new schema and its
exact byte layout. The canonical `SemanticSegmentHash` preimage under that
schema MUST contain every listed field. An implementation MUST NOT silently
reinterpret RFC-0002's draft `accounting_accumulator_root` under an old schema
or domain.

Every other RFC-0002 rule remains outside this RFC, including accepted-journal
leaf authority, ordered positions, state continuity, descendant disjointness,
semantic-effect coverage, empty message/carry boundaries, data availability,
and separate semantic and proof identities.

### Authority roots remain leaf-local

`authority_root` and `transformation_set_root` are copied into the audit
coverage entry for exact provenance. They are not added, unioned as bare roots,
deduplicated, transformed into an aggregate capability, or accepted as proof
that the corresponding facts were valid.

Repeated use of the same governed root in different accepted journals may be
legitimate. A bare set would erase that multiplicity. Exact auditability is
therefore provided by an ordered entry manifest keyed by leaf and dimension,
not by a set of roots.

## Terminology

**Accounting dimension:** The exact pair `(ResourceKindId, UnitId)`. Neither
component may be inferred, coerced, converted, wildcarded, or omitted.

**Gross-flow limb:** One nonnegative accumulated column. Gross-flow limbs do
not cancel during recursive composition.

**Resource net:** `created_total_atoms - consumed_total_atoms`, interpreted as
a mathematical integer or canonical signed magnitude at a boundary.

**Authorized net:** `authorized_mint_total_atoms -
authorized_burn_total_atoms`, interpreted in the same way.

**Retained opening:** Bounded row bodies sufficient to recompute one accepted
journal's committed accounting root and count. Retention is an assurance and
replay obligation, not an availability theorem.

**Coverage entry:** One exact association between an accepted leaf position,
journal, accounting row, dimension, authority root, and transformation-set
root.

**Internal identity:** The empty finite accounting map used to state total
algebraic laws. It is not an externally admissible semantic segment.

## Proposed semantics

### 1. Primitive aggregate quantity

`AggregateAtomsV1` is an unsigned 256-bit integer with exactly one canonical
32-byte big-endian encoding.

```text
0 <= AggregateAtomsV1 <= 2^256 - 1
```

Implementations MUST NOT:

- encode it as a variable-length integer;
- accept leading-length alternatives or negative encodings;
- reduce it modulo a proof field;
- convert it through floating point;
- narrow it to `u128`, `i128`, a host `usize`, or another smaller type;
- use wrapping or saturating arithmetic; or
- select an implementation-specific endianness.

Arithmetic in the reference profile is exact U256 checked arithmetic. A circuit
implementation must range-check every sub-limb and carry. A successful
field-element equation without integer range and carry constraints is not U256
evidence.

### 2. Aggregate row

```text
AccountingAggregateRowV1 {
  schema_version: u16 = 1
  resource_kind_id: ResourceKindId
  unit_id: UnitId
  consumed_total_atoms: AggregateAtomsV1
  created_total_atoms: AggregateAtomsV1
  authorized_burn_total_atoms: AggregateAtomsV1
  authorized_mint_total_atoms: AggregateAtomsV1
}
```

The directions are normative:

```text
resource debit       = consumed_total_atoms
resource credit      = created_total_atoms
authorized debit     = authorized_burn_total_atoms
authorized credit    = authorized_mint_total_atoms
```

The words debit and credit do not import an external accounting convention.
Only the equations in this RFC define their meaning.

An aggregate row is canonical only when:

- its schema is supported;
- both dimension identifiers are nonzero typed values;
- every limb uses the exact fixed-width encoding;
- at least one of the four limbs is nonzero; and
- the row satisfies the profile capacity and aggregate-balance invariants.

An explicit all-zero aggregate row rejects. Absence from the finite map is the
sole canonical zero representation. A row with equal nonzero debit and credit
MUST remain present.

This rule applies to the new `AccountingAggregateRowV1`, not to the existing
leaf `AccountingRowV1`. The current leaf schema does not forbid a row whose four
numeric columns are all zero. Such an authenticated leaf row remains valid,
produces a coverage entry, and projects to the internal zero contribution with
no material aggregate row. The recursive profile MUST NOT reject or rewrite an
accepted journal merely to impose the new sparse-map representation.

### 3. Governed aggregation profile

```text
AccountingAggregationProfileV1 {
  schema_version: u16 = 1
  profile_kind: u16 = 1                  // GrossFlowU256V1
  limb_encoding: u16 = 1                 // U256BeV1
  leaf_projection: u16 = 1               // AccountingRowFourColumnV1
  coverage_manifest_mode: u16 = 1         // OrderedLeafDimensionV1
  disclosure_mode: u16 = 1                // RootOnlyV1
  max_dimension_count: u32
  max_coverage_entry_count: u32
  max_retained_opening_bytes: u64
  max_segment_leaf_count: u32
}
```

Every maximum is positive and no greater than the separately reviewed protocol
ceiling for its field. The exact first deployable values remain an approval
blocker and require benchmark, memory, proof-cost, and adversarial-allocation
evidence. This RFC freezes their field widths and meaning, not an unevidenced
production value.

The hash frame below has a U32 payload-length field. Therefore the two lists of
32-byte digests have the additional non-negotiable encoding ceiling:

```text
MAX_HASHED_DIGEST_LIST_COUNT = floor((u32::MAX - 4) / 32)
                             = 134_217_727

max_dimension_count      <= MAX_HASHED_DIGEST_LIST_COUNT
max_coverage_entry_count <= MAX_HASHED_DIGEST_LIST_COUNT
```

This is an encoding-defined upper bound, not a recommended deployment value.
Reviewed resource limits will be far smaller. A profile whose declared maximum
cannot be represented by its selected hash framing rejects at profile
construction.

The profile ID is content-derived from the canonical profile bytes. Machine or
semantic policy selects the exact ID. A request, host, prover, proof tree, or
receipt cannot select a larger limit or another disclosure mode.

The selected semantic scope MUST bind `accounting_aggregation_profile_id`
directly or through a content-bound semantic-profile identity. Profiles cannot
be mixed in one segment.

`RootOnlyV1` means the semantic summary exposes roots, counts, and retained-byte
totals rather than every opened row. It does not mean that those roots are
hiding commitments or that witness size, proving time, errors, or retained
openings are private.

### 4. Retained accepted-journal opening

The first profile requires one opening per accepted journal:

```text
RetainedAccountingOpeningV1 {
  schema_version: u16 = 1
  accepted_journal_hash: JournalHash
  accounting_row_count: u32
  accounting_rows_byte_length: u64
  accounting_rows: AccountingRowV1[]
}
```

`accounting_rows` contains the exact canonical row bytes selected by the
governed authenticated journal schema, logical type, and version bound by the
semantic scope. The current `ResourceTransitionJournalV1` does not itself carry
a `journal_schema_id` field, so an adapter MUST NOT read an unbound ID from the
journal or invent one locally. Each row is length-framed by the governed
schema. Activation of this profile remains blocked until the corresponding
`AccountingRowV1` canonical bytes and independent vectors are frozen.

The wrapper and every nested row are bounded before allocation. The exact sum
of wrapper and row bytes contributes to
`retained_accounting_opening_bytes`. An implementation may stream the opening;
it may not evade the semantic byte total by avoiding an allocation.

For each opening the leaf adapter MUST:

1. accept only an authenticated `AcceptedJournal`, never a draft, Boolean, raw
   journal bytes, admission fact, or local replay assertion;
2. require exact journal-hash equality;
3. before nested allocation, require exact row-count equality with the journal
   and require the count not to exceed `max_coverage_entry_count` or
   `MAX_HASHED_DIGEST_LIST_COUNT`;
4. require the exact schema-selected row order and reject duplicate dimensions;
5. recompute every existing `AccountingRowHash` under the journal schema;
6. recompute the existing `AccountingRowsRoot` and require exact equality;
7. validate wrapper and cumulative profile bounds; and
8. derive every aggregate and coverage field rather than trusting a proposed
   projection.

An unavailable opening makes new leaf derivation unavailable. The adapter MUST
reject or report the profile's explicit unavailable-input outcome. It MUST NOT
substitute zeros, a cached host total, a weaker journal schema, or another
journal's rows.

The adapter treats opening bytes as untrusted. It MUST NOT sort, deduplicate,
merge, or otherwise repair them before root comparison. A trusted semantic
kernel constructing a new journal may construct rows in its governed canonical
order before committing them, and trusted aggregate derivation may construct
its new sparse map in canonical key order. Neither permission turns
normalization of an already committed, untrusted opening into acceptance.

The opening used for a production proof must be retained in the proof audit
bundle under the release retention policy. Future retrievability requires a
separately authenticated DA/retention profile. Successful proof generation
establishes only that the verifier consumed a valid opening at that time.

### 5. Leaf projection

For every validated opened `AccountingRowV1 row`, the singleton aggregate
contribution is exactly:

```text
dimension = (row.resource_kind_id, row.unit_id)

consumed_total_atoms        = U256(row.consumed_atoms)
created_total_atoms         = U256(row.created_atoms)
authorized_burn_total_atoms = U256(row.authorized_burn_atoms)
authorized_mint_total_atoms = U256(row.authorized_mint_atoms)
```

The widening conversion from U128 to U256 is exact. No subtraction,
cancellation, normalization, rounding, netting, or omission occurs first.

In particular:

```text
consumed=7, created=7, mint=0, burn=0
  -> aggregate row (7, 7, 0, 0)
```

It MUST NOT become an absent row merely because its resource net is zero.

The sole numeric omission is the exact internal zero:

```text
consumed=0, created=0, mint=0, burn=0
  -> no material AccountingAggregateRowV1
  -> one AccountingCoverageEntryV1 for the authenticated row occurrence
```

This omission loses no numeric support, while the mandatory coverage entry
preserves occurrence, journal, dimension, leaf-row hash, authority root, and
transformation root. It is not deduplication and does not remove the leaf from
the accepted-journal manifest.

Referenced resources contribute no quantity row unless the accepted
transition-level accounting schema independently commits an explicit effect.
The recursive adapter cannot invent a reference effect.

The leaf aggregate map's support contains exactly those opened accounting
dimensions whose four numeric columns are not all zero. Because duplicate leaf
dimensions reject, each supported dimension has exactly one leaf contribution.
The coverage manifest contains every opened row occurrence, including an
all-four-zero row. Proposed aggregate rows are non-authoritative and, if
accepted as a transport optimization, must already be strictly ordered,
duplicate-free, and equal the complete trusted derivation byte for byte; an
implementation MUST NOT sort or merge malformed proposed transport rows into
acceptance.

### 6. Coverage entry and ordered manifest

For every opened leaf row, derive:

```text
AccountingCoverageEntryV1 {
  schema_version: u16 = 1
  leaf_position: u64
  accepted_journal_hash: JournalHash
  resource_kind_id: ResourceKindId
  unit_id: UnitId
  accounting_row_hash: AccountingRowHash
  authority_root: LeafAccountingAuthorityRoot
  transformation_set_root: LeafAccountingTransformationSetRoot
}
```

`LeafAccountingAuthorityRoot` and
`LeafAccountingTransformationSetRoot` are distinct nonzero 32-byte opaque
newtypes over the correspondingly named existing leaf-row fields. They add no
new root derivation or authority. Their type separation prevents a codec or API
from swapping the two same-width values.

`leaf_position` is the RFC-0002 position derived from the authenticated
accepted journal's pre-state version. Every other field comes from the exact
opened row or its canonical hash.

`accounting_row_hash` is the existing leaf `AccountingRowHash` recomputed from
the exact canonical opened `AccountingRowV1` bytes under the accepted journal's
schema. It is never `AccountingAggregateRowHash`, a host-supplied digest, or a
hash of the widened projection. The distinct hash domains are not
interchangeable even when their payloads happen to describe equal numbers.

Coverage entries are ordered by:

```text
(leaf_position, resource_kind_id, unit_id)
```

The order is exact concatenation of leaf-local sorted rows in journal order.
Duplicate `(leaf_position, resource_kind_id, unit_id)` entries reject. Parent
composition concatenates `left.entries || right.entries`; it does not sort
children, set-union bare roots, or deduplicate repeated authority roots.

`accounting_coverage_entry_count` is the exact number of validated opened leaf
rows, including all-four-zero rows. For every dimension, the material aggregate
limbs equal the componentwise sum of the exact opened rows named by coverage
entries for that dimension; an all-four-zero occurrence contributes numeric
zero but remains in coverage. Coverage entries are an ordered positional
multiset, not a quantity oracle: the verifier recomputes quantities from the
authenticated openings and MUST NOT trust amounts inferred or supplied from
the manifest alone.

The coverage manifest is redundant with retained accepted journals in the
cryptographic sense, but it gives the accounting projection a direct,
replayable audit relation. A profile that omits it may claim only transitive
leaf authentication, not the complete directly auditable accounting provenance
defined here.

The manifest root is a commitment, not availability. Opening or querying it
requires retained entries or an independently specified authenticated-index
proof.

### 7. Canonical aggregate map

Aggregate rows are sorted strictly by:

```text
(resource_kind_id bytes ascending, unit_id bytes ascending)
```

Rules:

- duplicate dimensions in one child reject rather than merge silently;
- the same dimension in different children is combined by the normative
  parent operation;
- different units never combine, even when quantities are numerically equal;
- different resource kinds never combine;
- absence acts as a zero row only inside the pure map-merge operation;
- the output omits a dimension only when it is absent from both inputs;
- componentwise addition cannot turn a present nonzero row into zero;
- exact support is the union of nonzero child supports;
- `accounting_dimension_count` equals the exact materialized support size; and
- count and root are independently recomputed.

The accounting map is order-insensitive. The complete semantic segment remains
order-sensitive through RFC-0002's manifest, state, range, and coverage-entry
concatenation.

### 8. Parent composition

For each dimension `d` in the exact union of child supports:

```text
parent[d].consumed_total_atoms =
  checked_u256(left[d].consumed_total_atoms
             + right[d].consumed_total_atoms)

parent[d].created_total_atoms =
  checked_u256(left[d].created_total_atoms
             + right[d].created_total_atoms)

parent[d].authorized_burn_total_atoms =
  checked_u256(left[d].authorized_burn_total_atoms
             + right[d].authorized_burn_total_atoms)

parent[d].authorized_mint_total_atoms =
  checked_u256(left[d].authorized_mint_total_atoms
             + right[d].authorized_mint_total_atoms)
```

Missing child rows are internal zeroes. The parent is constructed by a linear
merge of already canonical child maps. Sorting attacker-provided rows into
canonical form is forbidden; malformed order rejects.

Also derive with checked arithmetic:

```text
parent.leaf_count = left.leaf_count + right.leaf_count
parent.coverage_entry_count =
  left.coverage_entry_count + right.coverage_entry_count
parent.retained_accounting_opening_bytes =
  left.retained_accounting_opening_bytes
    + right.retained_accounting_opening_bytes
```

Then require every selected profile maximum, exact coverage concatenation, and
every aggregate capacity and balance invariant. A proposed parent root, count,
row, or retained-byte total has no authority and must match exact derivation.

### 9. Capacity theorem and invariant

Each accepted leaf accounting column is a U128 and RFC-0002's segment leaf
count is U32. For every aggregate column in every dimension:

```text
column_total
  <= leaf_count * (2^128 - 1)
  <= (2^32 - 1) * (2^128 - 1)
  < 2^160
  < 2^256
```

The first inequality also relies on the existing rejection of duplicate
accounting dimensions inside one leaf journal: a given dimension contributes at
most one U128 value per accepted leaf. A future leaf schema that permits
multiple same-dimension occurrences cannot reuse this theorem unless it adds a
separate authenticated occurrence bound or proves an equivalent canonical
pre-aggregation bound.

Therefore U256 addition cannot overflow for two authentic child aggregates
whose checked leaf-count sum remains a U32. The implementation nevertheless
uses checked operations because child summaries and proof inputs are untrusted
until validated.

Every row MUST satisfy the redundant capacity invariant:

```text
each_limb <= U256(leaf_count) * U256(u128::MAX)
```

Violation rejects `AccountingAggregateCapacityViolation`. A U256 overflow from
two already sealed, profile-valid child summaries is an internal invariant
failure and blocks promotion; it cannot be normalized into another public
value.

Dimension count, coverage-entry count, retained-opening bytes, and leaf count
remain separately bounded. U256 quantity capacity does not make witnesses or
maps unbounded.

### 10. Aggregate balance

For every leaf row, existing validation establishes:

```text
consumed + authorized_mint = created + authorized_burn
```

Exact widening and componentwise addition therefore require, for every parent
row:

```text
consumed_total_atoms + authorized_mint_total_atoms
  == created_total_atoms + authorized_burn_total_atoms
```

Both additions fit U256 because each side is less than `2^161` under the
capacity theorem.

Equivalently over mathematical integers:

```text
created_total_atoms - consumed_total_atoms
  == authorized_mint_total_atoms - authorized_burn_total_atoms
```

The aggregate verifier recomputes and checks this invariant. Aggregate balance
does not replace exact leaf validation: different invalid rows can sum to a
balanced parent, so acceptance still requires every exact authenticated leaf
and coverage entry.

### 11. Strong associativity and definedness

Let `checkedMerge` validate exact support union, U32/U64 counts, profile limits,
U256 capacity, aggregate balance, and coverage concatenation. For individually
validated aggregates `a`, `b`, and `c` under the same governed profile and
semantic scope, whose flattened accepted leaves occur in contiguous left-to-
right RFC-0002 order, the normative three-child property is unconditional
Option-level equality:

```text
checkedMerge(checkedMerge(a, b), c)
  == checkedMerge(a, checkedMerge(b, c))
```

Here the operation is lifted over the inner `Option`: an inner rejection makes
that side reject. The statement does not quantify over arbitrary raw rows,
unvalidated summaries, mismatched profiles, or discontinuous leaf sequences.
Invalid leaf imbalance cannot be hidden by cancellation in another child.

This equality includes:

- equal success values;
- equal rejection definedness; and
- the same complete aggregate rows, counts, roots, retained-byte total, and
  coverage manifest when successful.

The arbitrary-tree property is stronger:

```text
For every full binary tree whose leaves flatten to the same ordered sequence of
individually authenticated, same-scope accepted journals under one governed
accounting profile, evaluation succeeds iff the complete global leaf count,
dimension support, coverage-entry count, retained-opening bytes, and canonical
openings satisfy the profile. Every successful tree derives identical
accounting summary fields. If a monotone global bound fails, every tree fails.
```

The proof relies on monotonicity:

- every component total only increases;
- support is exact union and never shrinks through cancellation;
- entry and byte counts only increase;
- U256 capacity is closed under authentic U32 child counts; and
- coverage order is exact associative concatenation.

The accounting map merge is commutative as a standalone typed effect algebra.
Coverage concatenation and the complete semantic-segment relation are not
commutative.

### 12. Net projection and boundary predicates

A recursive node MUST NOT store or recursively add a bounded signed net.

When an explicitly governed consumer needs a net, it derives canonical signed
magnitude by compare-and-subtract:

```text
SignedAggregateAtomsV1 =
    Negative(nonzero AggregateAtomsV1)
  | Zero
  | Positive(nonzero AggregateAtomsV1)

net(debit, credit) =
  if credit > debit then Positive(credit - debit)
  else if debit > credit then Negative(debit - credit)
  else Zero
```

Negative zero and positive zero are noncanonical. No I256 cast is required or
permitted.

A profile may require a typed predicate such as:

```text
NetZeroForSelectedDimensionsV1 {
  selected_dimension_set_root
  expected_accounting_aggregation_profile_id
}
```

It succeeds only when every selected row has
`consumed_total_atoms == created_total_atoms` and exact selected-set coverage
is authenticated. It cannot be supplied as a host Boolean.

Net zero is not a semantic no-op. A segment can have equal nonzero gross flow
while changing ownership, active resources, nullifiers, journals, evidence,
or application state. Lifecycle and evidence-resource quantities also do not
become market value merely because they are numeric.

The empty accounting map is an internal monoid identity. RFC-0002 semantic
segments remain nonempty and require an authenticated accepted-journal
manifest. An aggregate, empty map, or net-zero result alone cannot enter the
external leaf path.

## Canonical encoding and hashing

### Hash framing

All hashes introduced here use the existing closed reference framing:

```text
H_D(payload) = SHA-256(
  u16_be(domain_byte_length) ||
  domain_utf8_bytes ||
  u32_be(payload_byte_length) ||
  payload
)
```

Domains are schema-fixed. Callers cannot supply them. Length conversion or
addition overflow rejects before hashing.

### Domain strings

```text
zrm.accounting_aggregate_profile.v1
zrm.accounting_aggregate_row.v1
zrm.accounting_aggregate_rows.v1
zrm.accounting_coverage_entry.v1
zrm.accounting_coverage_manifest.v1
```

No existing accounting, journal, list, evidence, or proof-tree domain may be
reused for these objects.

### Profile bytes

`AccountingAggregationProfileV1` is exactly 32 bytes:

| Offset | Width | Field |
| ---: | ---: | --- |
| 0 | 2 | `schema_version`, U16 big-endian |
| 2 | 2 | `profile_kind`, U16 big-endian |
| 4 | 2 | `limb_encoding`, U16 big-endian |
| 6 | 2 | `leaf_projection`, U16 big-endian |
| 8 | 2 | `coverage_manifest_mode`, U16 big-endian |
| 10 | 2 | `disclosure_mode`, U16 big-endian |
| 12 | 4 | `max_dimension_count`, U32 big-endian |
| 16 | 4 | `max_coverage_entry_count`, U32 big-endian |
| 20 | 8 | `max_retained_opening_bytes`, U64 big-endian |
| 28 | 4 | `max_segment_leaf_count`, U32 big-endian |

```text
AccountingAggregationProfileId =
  H_"zrm.accounting_aggregate_profile.v1"(profile_bytes)
```

An all-zero digest rejects at typed construction.

### Aggregate-row bytes

`AccountingAggregateRowV1` is exactly 194 bytes:

| Offset | Width | Field |
| ---: | ---: | --- |
| 0 | 2 | `schema_version = 1`, U16 big-endian |
| 2 | 32 | `resource_kind_id` |
| 34 | 32 | `unit_id` |
| 66 | 32 | `consumed_total_atoms`, U256 big-endian |
| 98 | 32 | `created_total_atoms`, U256 big-endian |
| 130 | 32 | `authorized_burn_total_atoms`, U256 big-endian |
| 162 | 32 | `authorized_mint_total_atoms`, U256 big-endian |

```text
AccountingAggregateRowHash =
  H_"zrm.accounting_aggregate_row.v1"(row_bytes)
```

Wrong length, unsupported schema, all-zero dimension identifiers, trailing
bytes, and noncanonical all-zero aggregate rows reject.

### Aggregate-rows root

For rows in exact canonical dimension order:

```text
payload =
  u32_be(accounting_dimension_count) ||
  AccountingAggregateRowHash_0 || ... || AccountingAggregateRowHash_n

AccountingAggregateRowsRoot =
  H_"zrm.accounting_aggregate_rows.v1"(payload)
```

The canonical empty root is the hash of `u32_be(0)` under the aggregate-rows
domain. It is not all-zero bytes. This list root intentionally commits only
the canonical row sequence. It does not identify the governed aggregation
profile by itself. Cross-profile substitution is rejected because the enclosing
semantic scope selects the profile and the canonical `SemanticSegmentHash`
preimage commits `accounting_aggregation_profile_id` together with this root
and count.

### Coverage-entry bytes

`AccountingCoverageEntryV1` is exactly 202 bytes:

| Offset | Width | Field |
| ---: | ---: | --- |
| 0 | 2 | `schema_version = 1`, U16 big-endian |
| 2 | 8 | `leaf_position`, U64 big-endian |
| 10 | 32 | `accepted_journal_hash` |
| 42 | 32 | `resource_kind_id` |
| 74 | 32 | `unit_id` |
| 106 | 32 | `accounting_row_hash: AccountingRowHash` |
| 138 | 32 | `authority_root: LeafAccountingAuthorityRoot` |
| 170 | 32 | `transformation_set_root: LeafAccountingTransformationSetRoot` |

```text
AccountingCoverageEntryHash =
  H_"zrm.accounting_coverage_entry.v1"(entry_bytes)
```

Wrong length, unsupported schema, an all-zero typed digest or dimension
identifier, trailing bytes, and any entry inconsistent with its authenticated
leaf opening reject. `leaf_position = 0` is valid.

### Coverage-manifest root

For entries in exact `(leaf_position, resource_kind_id, unit_id)` order:

```text
payload =
  u32_be(accounting_coverage_entry_count) ||
  AccountingCoverageEntryHash_0 || ... || AccountingCoverageEntryHash_n

AccountingCoverageManifestRoot =
  H_"zrm.accounting_coverage_manifest.v1"(payload)
```

The canonical empty root is the hash of `u32_be(0)` under the coverage-manifest
domain. As with the aggregate-rows root, the root is profile-independent data;
the enclosing semantic scope and canonical `SemanticSegmentHash` provide the
exact profile binding. A nonempty semantic segment may have an empty coverage
manifest only when every exact accepted leaf commits an accounting-row count of
zero. Empty coverage does not make the segment an identity.

### Retained-opening wrapper

The retained wrapper begins with:

| Offset | Width | Field |
| ---: | ---: | --- |
| 0 | 2 | `schema_version = 1`, U16 big-endian |
| 2 | 32 | `accepted_journal_hash` |
| 34 | 4 | `accounting_row_count`, U32 big-endian |
| 38 | 8 | `accounting_rows_byte_length`, U64 big-endian |

It is followed by exactly `accounting_row_count` entries:

```text
u32_be(row_byte_length) || canonical AccountingRowV1 bytes
```

`accounting_rows_byte_length` equals the complete suffix length, including every
four-byte `row_byte_length` frame and every row body, but excluding the 46-byte
wrapper header. The enclosing wrapper length is therefore exactly
`46 + accounting_rows_byte_length`. Trailing bytes, truncation, count mismatch,
length overflow, or a row length inconsistent with the selected journal schema
rejects. The wrapper is retained evidence rather than a new semantic identity;
accepted-journal and coverage roots provide its semantic bindings.

The byte accounting is exact and checked:

```text
opening_total_bytes = 46 + accounting_rows_byte_length
leaf.retained_accounting_opening_bytes = opening_total_bytes
segment.retained_accounting_opening_bytes =
  sum(opening_total_bytes for every accepted leaf)
```

Both additions and the segment sum reject on U64 overflow or profile-limit
violation. Streaming or chunking does not change these semantic totals.

### Required vectors before approval

Independent implementations must agree on at least:

- profile bytes and profile ID;
- canonical domain-specific empty aggregate and coverage roots;
- singleton transfer, mint, burn, and mixed-flow rows;
- equal nonzero zero-net row retention;
- two dimensions supplied in reverse order rejecting rather than sorting;
- duplicate dimension rejection;
- two-child componentwise merge;
- U128 maximum widened to U256;
- capacity-bound edge values;
- coverage entry and two-leaf concatenated manifest;
- one-bit mutation of every field; and
- cross-domain substitution of every 32-byte digest.

Candidate, proposed, non-authoritative vectors now exist in
`vectors/accounting_aggregate_v1.json`, with binary preimages and an independent
replay script in `vectors/independent_python/replay_accounting_aggregate_v1.py`.
They cover the 194-byte aggregate row, sorted-row list root, 202-byte coverage
entry, ordered coverage-manifest root, multiplicity/order and row-hash-type
separation mutants, selected U128-to-U256 capacity cases, and the U32 hash-frame
digest-list ceiling. They do not yet cover profile bytes and profile ID,
canonical empty roots, retained-opening bytes, an existing frozen
`AccountingRowV1` opening, every field mutation, or cross-language agreement.
The coverage vector deliberately uses an opaque existing-leaf
`AccountingRowHash` fixture distinct from the aggregate-row digest. Until
canonical leaf bytes and an opening are frozen, it is codec, type-separation,
order, and multiplicity evidence only, not semantic leaf-binding evidence.
Their `proposed_non_authoritative` status neither freezes this ABI nor approves
this RFC. Approval requires complete independently reviewed vectors and the
ordinary release gates.

## Reject taxonomy and precedence

The accounting stage uses stable logical reasons:

```text
UnsupportedAccountingAggregateSchema
UnsupportedAccountingAggregationProfile
AccountingAggregationProfileMismatch
AccountingOpeningBytesExceeded
AccountingOpeningCountMismatch
AccountingOpeningRowOrder
DuplicateAccountingOpeningDimension
AccountingOpeningRootMismatch
AccountingAggregateRowCountExceeded
AccountingAggregateRowOrder
DuplicateAccountingDimension
ZeroAccountingAggregateRow
AccountingCoverageEntryCountExceeded
AccountingCoverageEntryOrder
DuplicateAccountingCoverageKey
AccountingAggregateLimbOutOfRange
AccountingAggregateCapacityViolation
AccountingAggregateProjectionMismatch
AccountingAggregateCoverageMismatch
AccountingAggregateConservationMismatch
AccountingCoverageManifestMismatch
AccountingAggregateRootMismatch
AccountingBoundaryPredicateMismatch
ResourceLimitExceeded
Internal
```

After RFC-0002's bounded envelope, scope, range, state, and accepted-leaf checks,
the accounting-stage precedence is:

```text
1.  Bound retained-opening and nested row framing before allocation.
2.  Require supported aggregate schema and exact governed profile.
3.  Require authenticated AcceptedJournal source and exact journal hash.
4.  Require opening count, canonical leaf-row decoding, order, and uniqueness.
5.  Recompute exact leaf-row hashes and the existing AccountingRowsRoot.
6.  Require proposed aggregate-row and coverage-entry order, uniqueness, and
    shape before comparison, when those untrusted optimizations are present.
7.  Derive exact sparse leaf projection and complete coverage entries.
8.  Require leaf, dimension, coverage-entry, retained-byte, and capacity bounds.
9.  Derive parent rows and exact nonzero support union.
10. Require aggregate conservation.
11. Derive and require exact coverage manifest and aggregate roots/counts.
12. Evaluate an optional governed boundary predicate.
```

Parallel checking must not change the selected logical result. A privacy
adapter may expose a coarser profile-defined public error, but its internal
semantic result and proof statement remain deterministic. An adapter cannot
map unavailable retained input, proof uncertainty, or an internal invariant
failure to successful zero accounting.

## Authority and trust boundary

### Untrusted

- retained-opening bytes before complete validation;
- proposed rows, roots, counts, byte totals, nets, coverage entries, and
  profiles;
- recursive proof artifacts and host-computed proof metadata;
- bare authority and transformation roots;
- public Booleans claiming balance, coverage, or net zero.

### Governed

- authenticated `AcceptedJournal` source;
- journal and accounting-row schemas;
- semantic and accounting-aggregation profile identities;
- verifier policy, program/key, release, cost, and resource limits;
- retention and DA requirements;
- any boundary net predicate and selected dimension set.

### Derived

- every widened leaf limb;
- canonical aggregate rows, support, counts, and roots;
- coverage entries, order, count, and root;
- retained-opening byte total;
- capacity and aggregate-conservation decisions;
- boundary signed magnitude or typed net predicate result.

`AccountingAggregateRowV1`, its root, and the coverage manifest are canonical
data. They are not sealed facts and do not authorize a transition.

Only a governed recursive verifier may construct a sealed
`VerifiedPostcommitAggregationFact`, and only after it authenticates the exact
semantic summary, proof program/key/release, profile, and resolved child
evidence. That fact remains postcommit evidence. It cannot:

- satisfy precommit admission;
- recreate a consumed resource;
- authorize mint, burn, transformation, reward, or external delivery;
- mutate machine state;
- mark a journal accepted;
- make an unavailable opening available; or
- replace durable commit, consensus, ordering, or finality.

No aggregate-level authority or transformation rule exists in the first
profile. Every nonzero authorized limb and every transformation relationship
must already be valid and explicit in accepted leaf journals.

## Data availability and retention

The first profile requires the complete retained opening while deriving or
replaying a leaf. It makes three distinct claims:

```text
commitment:
  accepted journal binds accounting root and count

availability at proving time:
  recursive verifier received a complete matching opening

future availability:
  established only by a separate retained-artifact or DA profile
```

The first two do not imply the third. A production release must retain the
opening, coverage entries, exact profile, guest input manifest, and hashes
needed to reproduce the proof. If policy requires external availability, the
opening or its containing audit bundle must be covered by the journal's exact
DA certificate or a separately approved postcommit retention certificate.

Loss of retained openings does not rewrite an existing accepted journal or
valid proof. It prevents independent opening replay and may prevent proof
regeneration. Documentation must state that assurance loss rather than call the
data available.

## Privacy and disclosure

The first profile is not a shielded profile.

Four gross totals preserve more information than a signed net:

- equal debit and credit reveal churn when opened;
- separate authorized mint and burn totals reveal issuance/destruction use;
- coverage entries reveal which governed authority and transformation roots
  were associated with each leaf dimension;
- counts, retained byte lengths, proof size, timing, and errors may reveal
  additional structure; and
- SHA-256 roots are binding but not hiding against low-entropy dictionaries.

`RootOnlyV1` places row and coverage roots in the public semantic summary, but
it does not require public disclosure of every opening. Openings may be private
proof witnesses and retained under controlled audit access. Even then, a
dictionary attack or auxiliary public journal data may reveal values.

A future shielded profile requires a separate RFC defining hiding commitments,
public leakage fields, size and timing classes, error behavior, opening and
audit authority, and tree-independent blinding semantics. It cannot inherit a
privacy claim from this profile merely by placing the computation in a zkVM.

## Resource, denial-of-service, and circuit analysis

The canonical U256 representation uses four 64-bit or eight 32-bit machine
limbs. Four aggregate columns therefore require sixteen 64-bit additions plus
carry validation per merged dimension, before hashing and map work. A circuit
over a roughly 254-bit field cannot treat an unconstrained field element as a
U256 integer; it must use a reviewed multi-limb representation.

Compared with a two-column U256 projection, the proposed row:

- doubles wide arithmetic and range constraints;
- grows the fixed row payload from 130 to 194 bytes;
- adds one or more hash compression blocks per row depending on the backend;
- preserves aggregate mint/burn audit information; and
- enables direct aggregate-conservation checking.

The exact coverage manifest adds linear hashing, witness retention, and audit
storage. It is justified for the bounded reference profile, not claimed to be
the final production accumulator.

The verifier must:

- reject oversized envelopes before nested allocation;
- validate already-sorted child maps with a linear merge;
- use checked reservation and expose allocation refusal as a typed failure;
- cap dimensions, entries, bytes, leaves, proof input, output, and verifier
  work independently;
- reject duplicate and misordered rows rather than sorting them;
- avoid a general bigint dependency unless its exact release and TCB are
  separately approved; and
- retain worst-case cost evidence for the selected profile.

A closed `AggregateAtomsV1([u64; 4])` or equivalent fixed representation is
preferred to an unrestricted bigint API. U192 would be mathematically adequate
under the current U32/U128 theorem but introduces a less conventional 24-byte
primitive. U128 is simpler but is not closed over two legal maximum-valued
leaves. U256 is selected for the proposed profile because it gives a simple
capacity theorem and 32-byte canonical alignment.

## Security analysis

| Disaster state | Required defense | Residual risk |
| --- | --- | --- |
| Proof tree selects whether signed overflow occurs | Monotone U256 columns and arbitrary-tree definedness theorem | Dimension/byte caps still limit segment size |
| Balanced gross flow disappears because net is zero | Preserve every nonzero gross limb; omit only the exact numeric zero while retaining its coverage occurrence | Aggregate remains a projection, not full history |
| Unlike units cancel | Exact typed dimension map | Correctness of governed unit policy remains leaf-local |
| Mint total is treated as mint authority | Leaf-local sealed facts; aggregate data has no authority constructor | Consumers may misuse data outside reviewed APIs |
| Bare authority-root union erases repeated use | Ordered per-leaf/dimension coverage manifest | Opening availability remains separate |
| Forged row bodies match a proposed host total | Recompute accepted journal root/count from retained opening | Hash and journal-schema assumptions remain |
| U256 wraps in a proof field | Fixed limb range and carry constraints plus capacity invariant | Circuit/compiler correctness remains in TCB |
| Parent omits a balanced child row | Exact leaf projection, support union, and coverage manifest | Hash collision resistance remains assumed |
| Empty aggregate is admitted as an external segment | Nonempty authenticated RFC-0002 journal manifest | Legitimate segments may have zero accounting rows |
| Zero net is called state no-op | Typed net predicate and explicit nonclaim | Application-level interpretations require review |
| Profile limit is widened by the prover | Content-derived governed profile ID in semantic scope | Governance quality is not established |
| Opening commitment is called availability | Explicit proving-time versus future-DA distinction | Retention operator may still lose data |
| Gross-flow roots leak private amounts | No privacy claim; separate shielded profile required | Low-entropy dictionary attacks remain possible |
| Coverage witness causes memory or proof DoS | Independent count/byte/work caps and streaming merge | Selected limits require benchmark evidence |

## Mandatory counterexamples

An implementation and independent reference model must cover at least:

1. Signed `(127, 1, -1)` left/right definedness disagreement.
2. `consumed=7, created=7` retained as equal nonzero resource limbs.
3. Pure mint: `(consumed, created, burn, mint) = (0, 7, 0, 7)`.
4. Pure burn: `(7, 0, 7, 0)`.
5. Mixed balanced row: `(3, 4, 1, 2)`.
6. Two leaves whose nonzero nets cancel but all four aggregate totals remain.
7. Same kind with different unit IDs never combining.
8. Two legal U128-maximum balanced leaves fitting U256.
9. One-leaf forged limb greater than `u128::MAX` failing capacity.
10. Explicit all-zero aggregate-row transport rejection, alongside acceptance
    of an authenticated all-four-zero leaf row whose numeric projection is
    absent but whose coverage occurrence remains.
11. Duplicate dimension in one child rejection.
12. Same dimension across children merging exactly.
13. Repeated bare authority root preserving two coverage entries.
14. Same numeric aggregate under different row/authority roots yielding a
    different coverage manifest and accepted-journal history.
15. Net-zero ownership transfer not classified as state no-op.
16. Empty aggregate unable to construct a postcommit leaf.
17. Proof-field modular-wrap mutant rejection.
18. Correct row count with one changed row failing the accepted-journal root.
19. Correct rows under a substituted aggregation profile failing enclosing
    semantic-scope and semantic-summary binding.
20. Missing, extra, permuted, duplicated, or relabeled coverage entry rejection.
21. Missing retained opening failing closed rather than substituting zeros.
22. Left- and right-associated folds both rejecting when a monotone profile cap
    is globally exceeded.
23. Digest-list count `134_217_727` fitting the U32 hash-frame payload length,
    while `134_217_728` rejects without allocation or hashing.
24. A host-proposed conserving aggregate with the correct covered dimensions
    but incorrect limb totals failing exact opening projection.

## Formal obligations

At minimum:

```text
U32TimesU128MaximumFitsU256
LeafWideningExact
LeafProjectionPreservesBalance
AggregateMapCanonical
AggregateSupportExactUnion
AggregateSparseLeafProjectionExact
AllZeroLeafCoverageRetained
AggregateCoverageExactConcatenation
AggregateMergePreservesBalance
AggregateMergeStrongAssociative
AggregateArbitraryTreeDefinednessIndependent
AggregateMapMergeCommutative
CompleteSegmentCompositionNoncommutative
EqualNonzeroNetZeroRowRetained
SignedMagnitudeProjectionTotalAndCanonical
NetProjectionAdditiveOverMathematicalIntegers
ProfileBoundMonotone
ProfileSubstitutionRejected
DigestListPayloadFramingFitsU32
CoverageUsesExistingLeafAccountingRowHash
AggregateCannotConstructLeafAuthority
PostcommitAggregateCannotAuthorizeAdmission
RustU256RefinesNaturalNumberModel
CircuitLimbsRefineU256
```

The arbitrary-tree theorem quantifies over every finite full binary tree whose
leaves flatten to the same ordered journal sequence. A three-leaf example is
not sufficient.

The current `formal/lean/zrm_accounting_aggregate_v1/` package extends the
earlier bounded-signed counterexample with proofs about checked list folds and
arbitrary nonempty binary merge trees, exact multiset coverage with
multiplicity, four-column conservation, a concrete noninjectivity witness for
the resource-only projection, and the U32/U128 capacity bound below `2^160`
and `2^256`. It is design evidence only. It does not prove the protocol's
finite-map key ordering, canonical bytes or hashes, retained-opening relation,
cryptographic coverage commitment, profile binding, Rust refinement, circuit
constraints, or authority boundary.

## Typed interfaces

Conceptually:

```rust
pub fn derive_accounting_leaf(
    journal: &AuthenticatedAcceptedJournal,
    opening: &BoundedRetainedAccountingOpening,
    profile: &GovernedAccountingAggregationProfile,
) -> Result<AccountingAggregateLeafV1, AccountingAggregateRejectV1>;

pub fn compose_accounting_aggregates(
    left: &ValidatedAccountingAggregateV1,
    right: &ValidatedAccountingAggregateV1,
    profile: &GovernedAccountingAggregationProfile,
) -> Result<ValidatedAccountingAggregateV1, AccountingAggregateRejectV1>;

pub fn evaluate_accounting_boundary(
    aggregate: &ValidatedAccountingAggregateV1,
    predicate: &GovernedAccountingBoundaryPredicate,
) -> Result<VerifiedAccountingBoundaryFact, AccountingBoundaryRejectV1>;
```

The public transport types remain inert. Validated aggregate fields are
private and constructible only through complete derivation. A
`VerifiedAccountingBoundaryFact` is scoped to its exact postcommit consumer; it
is not a mint, burn, transformation, transition, admission, or commit
capability.

## Compatibility and migration

- Frozen `ResourceWireV1` bytes and resource IDs do not change.
- Existing logical `AccountingRowV1`, `AccountingRowHash`, and
  `AccountingRowsRoot` meanings do not change.
- Existing transition statements and accepted-journal payloads do not gain or
  lose authority under this draft.
- RFC-0002 is Draft, and `ZRM-CBC-027` has no implementation, canonical vectors,
  persisted aggregate, or release identity to migrate.
- A conforming implementation introduces a new semantic-summary schema or
  profile that binds this RFC's profile ID, roots, counts, and retained-byte
  total.
- Old and new accounting-aggregation profiles cannot appear in one segment.
- Changing any row field, direction, width, ordering rule, domain, coverage
  mode, disclosure mode, or capacity interpretation requires a new schema or
  profile ID.
- Changing only a verifier program or release changes proof identity and
  governance. It does not change semantic identity when the exact accounting
  profile and derived semantic summary remain unchanged.
- Changing the accounting profile changes semantic scope and semantic identity,
  even when the numeric rows happen to match.
- A governed profile update invalidates cached uncommitted facts and breaks the
  ordinary same-scope segment. Crossing it requires the separately proposed
  governed context-bridge semantics; no bridge authority is defined here.
- Historical accepted journals may be re-proved only from exact retained
  openings under a profile that explicitly accepts their journal schema. They
  are never relabeled silently.

If reviewers discover an existing durable or externally relied-upon
`accounting_accumulator_root` interpretation, the no-migration disposition is
invalid. Approval must stop until an explicit predecessor mapping, replay
analysis, and cross-version rejection matrix exist.

Rollback of an implementation cannot restore a signed or ambiguous recursive
carrier while retaining this profile ID. It must disable the profile or move to
a newly governed version.

## Test and assurance plan

- independent Python or equivalent reference model over canonical finite maps;
- exhaustive small-domain comparison of every binary tree over up to a
  reviewed leaf bound;
- Lean arbitrary-tree, capacity, projection, balance, and coverage proofs;
- ESSO bounded models and mutants for signed overflow, row dropping, final-net
  bounds, limb swaps, capacity, and coverage omission;
- Rust U256 unit, property, Kani, and differential tests;
- canonical cross-language profile, row, list, entry, and manifest vectors;
- all-field and cross-domain mutation atlas;
- retained-opening parser fuzzing with malicious counts, lengths, truncation,
  order, duplicates, and allocation refusal;
- map-merge fuzzing across dimensions, units, equal nets, and maximum values;
- all-four-zero leaf-row compatibility tests proving sparse numeric omission
  and exact coverage retention;
- recursive guest/reference differential tests across every supported tree;
- proof-field wrap, missing range constraint, and dropped-carry mutants;
- authority/transformation-root multiplicity and relabeling tests;
- unavailable-opening and missing-DA negatives;
- proof program, key, release, journal schema, semantic profile, and accounting
  profile substitution negatives;
- privacy review of public roots, counts, timing, sizes, and errors;
- worst-case memory, cycle, proof-size, and retained-storage benchmarks; and
- independent semantic, accounting, codec, proof-system, and authority-boundary
  review.

Tests, model checking, and generated proofs remain scoped evidence. They do not
approve the RFC, prove the cryptographic system, or create production
authority.

## Literature and implementation lineage

The [Anoma Resource Machine
specification](https://specs.anoma.net/v1.0.0/arch/system/state/resource_machine/index.html)
defines balance as transaction completeness. Its [transaction
model](https://specs.anoma.net/v1.0.0/arch/system/state/resource_machine/data_structures/transaction/transaction.html)
adds action deltas and aggregates transaction proofs, and its [delta-proof
relation](https://specs.anoma.net/v1.0.0/arch/system/state/resource_machine/data_structures/transaction/delta_proof.html)
checks the summed delta against an expected balance. This RFC adopts the useful
additive projection while retaining gross nonnegative columns and ZRM's exact
unit, authority, journal, and state boundaries. It does not claim that Anoma's
delta representation has this RFC's bounded signed-definedness defect.

[Proof-Carrying Data from Accumulation
Schemes](https://eprint.iacr.org/2020/499) establishes foundations for recursive
proof composition. It does not define ZRM's application accounting relation,
canonical row support, authority coverage, journal acceptance, or durable
commit. Those remain semantic inputs to any PCD construction.

[Zexe](https://eprint.iacr.org/2018/962) demonstrates recursive private
computation and fungible applications. It supports feasibility of proof-backed
resource applications but does not supply this aggregate schema or its
authority claims.

[RISC Zero proof
composition](https://dev.risczero.com/api/zkvm/composition) adds assumptions
when a guest verifies child proofs and resolves those assumptions in later
proving. Conditional proof composition therefore cannot by itself create an
accepted ZRM journal or accounting authority.

At pinned ARM revision
[`1b552f17b1c94943e6f81d08e2986befc26e99e9`](https://github.com/anoma/arm-risc0/commit/1b552f17b1c94943e6f81d08e2986befc26e99e9),
the [batch aggregation
guest](https://github.com/anoma/arm-risc0/blob/1b552f17b1c94943e6f81d08e2986befc26e99e9/arm_circuits/batch_aggregation/methods/guest/src/main.rs)
verifies compliance and logic child assumptions and republishes their instance
arrays and keys. It is useful evidence for modular proof composition, but it
does not define ZRM accepted status, state continuity, typed accounting fold,
coverage manifest, or commit authority.

The local research packet `research/zrm_accounting_aggregate_v1/`, executable
reference model in `reference_models/accounting_aggregate_v1.py`, candidate
vectors cited above, and Lean package provide the immediate counterexamples,
hypothesis ledger, executable algebra, and bounded formal evidence for this
proposal. The earlier `research/zrm_frontier_v2/breakthroughs.md` packet records
the signed-carrier counterexample that motivated the change. None is independent
review, production evidence, or normative authority.

## Supply-chain and release impact

This RFC adds no dependency while it remains documentation. An implementation
SHOULD use a small closed U256 representation. Adding a general bigint,
recursive SDK, circuit library, hashing library, or authenticated-accumulator
dependency changes the TCB and requires exact lockfile, provenance, license,
advisory, reproducibility, and release review.

A production profile requires:

- approved RFC and exact profile limits;
- independent canonical vectors;
- pinned compiler, guest, recursive SDK, program/image IDs, and verifier
  release;
- reproducible guest and verifier builds;
- retained opening and coverage audit bundles;
- complete formal-assumption and nonclaim documents;
- mutation and adversarial parser evidence;
- independent integrated audit; and
- conformance-matrix promotion through the repository's normal release gates.

No local model, agent review, CI result, or draft proof can replace those
requirements.

## Claims after implementation and approval

For the exact approved bounded profile only, the repository may then claim:

- exact widening of accepted leaf accounting rows into four U256 gross-flow
  columns;
- exact typed-dimension aggregation and ordered coverage provenance;
- U32/U128-derived U256 quantity capacity;
- accounting result and definedness independent of binary proof-tree grouping;
- aggregate conservation inherited from every authenticated leaf; and
- strict separation of aggregate data from leaf and commit authority.

It may not claim:

- approval, implementation, or production readiness from this draft;
- privacy or hiding from roots or a zkVM;
- availability after proof generation without the named DA/retention evidence;
- market value, solvency, fairness, price correctness, or physical
  conservation;
- permission to mint, burn, transform, reward, or settle from an aggregate;
- arbitrary recursion, unbounded dimensions, or unbounded witnesses;
- proof-system, compiler, hardware, operating-system, or cryptographic
  correctness;
- consensus, finality, censorship resistance, or exact-once external delivery;
  or
- cross-profile or cross-context aggregation.

## Open questions and approval blockers

- What exact first-profile limits follow from worst-case benchmark and circuit
  evidence?
- Which accepted-journal version freezes canonical `AccountingRowV1` bytes and
  makes retained opening replay possible?
- Which storage and DA profile retains openings and coverage entries, and for
  how long?
- Should an optimized production profile use a concatenation proof,
  authenticated vector, or another accumulator for the coverage manifest?
- Which public accounting roots and counts are acceptable under a future
  shielded profile?
- Which exact dimension-selection language governs boundary net predicates?
- Which independent reviewers own accounting semantics, canonical encoding,
  recursive proof binding, and privacy leakage?
- Does any downstream prototype already rely on the draft RFC-0002 accounting
  root in a way that requires explicit migration?

## Decision

Undecided. This document is a Class E proposal. Approval requires exact limit
selection, canonical `AccountingRowV1` openings, independent vectors,
arbitrary-tree formal evidence, bounded counterexample and mutation evidence,
resource benchmarks, privacy and DA review, and explicit maintainer semantic
approval.

Until then, RFC-0002 remains Draft, this profile grants no authority, and no
implementation may claim its accounting aggregate is approved, canonical,
audited, private, or production-ready.
