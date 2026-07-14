# ARM/ZRM frontier Lean research packet v2

This non-normative Lean 4.32.0 packet checks three narrow design claims:

- `TotalCarrier` models modular accumulation with `Fin n`, proves total
  associativity and both identities, and checks that `1 + 6 = 0` remains a
  valid result modulo seven.
- `ExactCoverage` defines manifest coverage as `List.Perm`, proves preservation
  under partition composition, and includes executable missing/extra-item
  regressions.
- `TranscriptSeparation` gives order-sensitive journal traces and
  order-insensitive semantic sets different types. Set union is proved
  commutative; a concrete trace-append counterexample is proved
  noncommutative.
- `AccountingStrongAssociativity` exhibits a three-row signed checked-addition
  counterexample whose definedness depends on tree shape. It then proves that
  bounded monotone debit/credit limbs give both equal results and equal
  definedness for either parenthesization, and that the net projection respects
  limb merging.

Run from this directory:

```sh
lake build
```

## Non-claims

These theorems do not prove the ZRM implementation, ARM circuits, durable
commit protocol, cryptographic assumptions, or a refinement relation between
this model and Rust. `CanonicalSet` is an extensional semantic model, not a
canonical byte encoding. The packet deliberately contains no axioms or
`sorry`; it is design evidence only until linked to an implementation
refinement proof.
