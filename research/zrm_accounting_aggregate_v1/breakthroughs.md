# Accounting aggregate breakthroughs

## 1. The leaf row is not the recursive carrier

`AccountingRowV1` combines four numeric columns with `authority_root` and
`transformation_set_root`. Addition is defined for the columns. No associative,
meaning-preserving addition is defined for the roots. Merging the entire leaf row
would either invent authority semantics or silently discard provenance.

The improvement is a split representation:

- a commutative numeric aggregate over four unsigned columns; and
- an ordered coverage commitment that retains every leaf-row occurrence and its
  authority and transformation roots.

The numeric plane answers “how much?” The coverage plane answers “which accepted
leaf rows and roots authenticate those totals?” Neither substitutes for the
accepted journal or its validation facts.

## 2. Four columns, not two

The roadmap's two resource-flow columns preserve consumed and created totals but
erase authorized mint and burn decomposition. For example, these valid rows have
the same two-column projection:

```text
(consumed=10, created=10, mint=0, burn=0)
(consumed=10, created=10, mint=7, burn=7)
```

Their authority use is different. Four monotone columns preserve every numeric
field of the existing row and make aggregate conservation independently
checkable:

```text
resource.debit + authority.credit
  = resource.credit + authority.debit
```

Equivalently, `created-consumed = mint-burn`. The recursive carrier performs no
subtraction; a signed-magnitude projection is derived only at a governed
boundary.

## 3. U256 makes composition total for the protocol cardinality

RFC-0002 bounds a segment's `leaf_count` by `u32`; every leaf column is `u128`.
Consequently:

```text
column_total <= (2^32 - 1) * (2^128 - 1) < 2^160 < 2^256
```

A U128 aggregate overflows on two legal maximum leaves. A U256 aggregate fits
every protocol-valid segment and supplies 96 unused high bits at the exact
maximum. This removes arithmetic tree-shape failure rather than merely choosing
a favorable fold order.

Every summary still checks the redundant capacity invariant
`limb <= leaf_count * (2^128 - 1)`. It detects fabricated summaries even though
the fixed carrier itself has ample width. U192 would suffice mathematically, but
U256 matches a fixed 32-byte protocol field and common circuit decompositions.

## 4. Definedness is part of associativity

Checked bounded signed addition is not strongly associative when intermediate
overflow and later cancellation are possible. At bound 127:

```text
(127 + 1) + (-1) = undefined
127 + (1 + -1)   = 127
```

The required law is equality of the partial result, not equality only when both
parenthesizations happen to succeed. Unsigned monotone addition plus a global
capacity bound makes every binary tree over the same valid leaves succeed with
the same exact total.

## 5. Zero net is evidence, not emptiness

An ordinary transfer can have equal nonzero consumed and created totals. A fold
that normalizes to net and drops zero erases gross coverage. The design therefore
distinguishes:

- the internal empty-map identity with zero leaves;
- a nonempty accepted-journal segment with no accounting rows;
- a retained nonzero row whose selected net is zero; and
- an actual state no-op, which depends on authenticated state and journal fields.

External admission never follows from aggregate emptiness or a zero net.

## 6. Exact occurrence coverage beats root set union

A set of authority roots loses multiplicity and row association. Repeated use of
one root can be legitimate, and equal numeric totals can arise under different
authorities. The first profile therefore commits an ordered sequence of coverage
entries keyed by leaf position and dimension. Parent composition is exact
concatenation, not set union or silent deduplication.

The aggregate rows are commutative, but the semantic segment is not: journal
order, state continuity, and coverage positions remain ordered.

## 7. Commitment is not availability

`AcceptedJournal` commits an accounting-row root and count, not the row bodies.
Aggregation needs a bounded untrusted opening witness. The adapter authenticates
the journal, checks bytes and count before allocation, recomputes the existing
root, and only then derives aggregate rows and coverage entries.

A valid historical commitment with unavailable openings remains a valid
commitment, but cannot be newly aggregated under the retained-opening profile.
Recursive proof compression does not manufacture data availability.

## 8. Literature synthesis and improvement

ARM supplies a useful additive balance abstraction and RISC Zero supplies proof
composition machinery, but neither defines ZRM's four-column gross accounting,
typed units, authority coverage, or accepted-journal semantics. Double-entry
bookkeeping motivates unsigned pairs and multidimensional ledgers. Fold
homomorphism work motivates tree-independent summaries. Invariant-confluence
work clarifies why componentwise addition preserves an equality invariant, while
CRDT literature is only an analogy: this carrier is not a join-semilattice and
does not imply coordination-free ZRM execution.

Zcash's value bounds illustrate the stronger engineering move adopted here:
derive aggregate range from per-item bounds and cardinality rather than hoping a
smaller checked carrier survives a particular tree. PCD, Zexe, and RISC Zero
authenticate recursive relations; they do not confer application authority.

## 9. Privacy profiles must be distinct

Four public gross totals reveal churn and mint/burn use. A SHA-256 root is binding,
not hiding. The first RFC profile is transparent or retained-opening and makes
that disclosure explicit. A future shielded profile may keep rows and coverage
private while proving a typed predicate or commitment, but it needs different
profile and statement identifiers. Bulletproof-style range proofs are relevant
to that future work, not evidence that the transparent profile is private.

## 10. Remaining high-value questions

- Which data-availability mechanism must retain accounting openings, and for how
  long?
- Should the coverage root be a flat ordered list in the first implementation or
  an append-friendly authenticated sequence with independently frozen vectors?
- Which accounting predicates, if any, may be public without unacceptable
  business-flow leakage?
- What circuit limb width minimizes constraints while retaining a simple audited
  Rust refinement?
- How should a governed context bridge relate two accounting aggregation
  profiles without reinterpreting old semantic hashes?
- Can a mechanized byte-level refinement close the remaining gap from Lean
  naturals to fixed U256 carry arithmetic and canonical encodings?
