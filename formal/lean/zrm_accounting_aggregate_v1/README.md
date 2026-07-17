# ZRM accounting aggregate Lean package v1

This stacked, non-normative Lean 4.32.0 package imports the frozen
`arm_zrm_frontier_v2` research package and generalizes its three-input
accounting theorem to recursive aggregation.

`AccountingFoldTree` proves:

- arbitrary checked list folds succeed exactly when their complete monotone
  debit/credit total fits the bound;
- every nonempty binary merge tree has that same specification, so proof-tree
  shape cannot change success, failure, or the accepted result;
- exact multiset coverage, including multiplicity, preserves aggregation and
  checked tree evaluation;
- the canonical nonempty row wrapper's right-associated tree exactly covers
  its committed row list and agrees with the checked list fold;
- net projection commutes with arbitrary aggregation; and
- aggregate zero is equivalent to row-wise zero accounting support, while a
  nonzero debit/credit pair that cancels at the net boundary retains support.

The model explicitly separates the empty internal fold identity from external
segment semantics. `AuthenticatedSegment` requires a nonempty journal but
allows its accounting-row list to be empty. Neither zero accounting support nor
zero net is treated as a state no-op or an admission failure.

`TotalOverflowCarrier` defines a total `finite | overflow` carrier. Overflow is
absorbing, merge is associative and commutative with a finite-zero identity,
and arbitrary aggregation is finite exactly when the exact natural sum fits.
Its boundary projection rejects overflow while retaining the partial checked
fold and tree characterization above as a refinement view.

`FourColumnConservation` models the candidate aggregate row as resource
`(consumed, created)` and authority `(burned, minted)` monotone pairs. It proves
the subtraction-free conservation equation
`consumed + minted = created + burned` through arbitrary folds and trees. A
concrete pair of distinct conserved rows proves that the resource-only
projection is not injective and therefore cannot losslessly replace all four
columns.

`CapacityBound` proves from the candidate `u32` leaf-count and `u128` per-leaf
column bounds that every exact column aggregate is below `2^160`, and therefore
below `2^256`. It follows that a U256 total carrier cannot overflow for any
segment satisfying those premises. This applies independently to consumed,
created, burned, and minted columns.

Run from this directory:

```sh
lake build
```

## Assurance boundary

The package builds as ten Lake jobs on the pinned Lean 4.32.0 toolchain. Its
Lean sources contain no `axiom`, `sorry`, or `admit` declarations. A local
`#print axioms` audit reports:

- the checked list/tree and exact-coverage results use Lean's `propext`,
  `Classical.choice`, and `Quot.sound` foundations;
- the total carrier, conservation, and capacity results use `propext` and
  `Quot.sound`; and
- the concrete resource-projection noninjectivity theorem has no axiom
  dependencies.

These are proof-term dependency reports, not independent-kernel or
implementation-refinement certificates.

## Non-claims

These theorems do not establish a refinement relation to ZRM Rust or ARM guest
code, circuit correctness, canonical row-key ordering or byte encoding,
cryptographic security, durable commit safety, liveness, or adequacy of any
numeric bound beyond the stated `u32`/`u128` premises. `CanonicalRows` commits
a nonempty list order inside the model; it does not define the RFC's sparse
finite-map support union, accepted-journal row-opening/root relation, or ordered
audit-coverage concatenation, and it does not choose the protocol's
canonicalization rule. `CoversExactly` is a multiset-permutation relation used
only for the commutative numeric fold; it is not the ordered coverage-manifest
relation. The package contains
no user-declared axioms or proof placeholders, but it remains design evidence
until linked to implementation definitions and independently checked release
artifacts. Actual state no-op and external admission are intentionally not
defined by aggregate zero, zero net, or an empty accounting-row list.
