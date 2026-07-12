# Security remediation critical mutation map

**Scope:** ZRM-01 through ZRM-05 remediation candidate

This map separates semantic guard mutations, API-surface regressions, and
diagnostic leakage regressions. Compile-fail and architecture checks are used
where the desired property is absence of a callable public operation.

| Mutant obligation | Defect introduced | Required killer | Evidence class/result |
| --- | --- | --- | --- |
| `ZRM01-ZERO-GUARD-OMIT` | Remove the general `quantity == 0` rejection | all-mode atlas, especially `EvidenceOnly`; Kani predicate; dimension fuzzer | generated Rust mutants caught in the configured campaign; named semantic tests identify the guard |
| `ZRM01-ZERO-MODE-EXEMPT` | Exempt any one accounting mode from zero rejection | five-mode decision matrix and fuzz seeds | hand-authored sensitivity obligation; all five modes plus explicit `EvidenceOnly` regression pass, not claimed as a generated mutant |
| `ZRM01-LIFECYCLE-MAX-OMIT` | Accept lifecycle maximum 0 or greater than 1 | constructor matrix; lifecycle Kani harness | generated Rust mutants caught in focused and configured campaigns |
| `ZRM01-UNIT-PRECEDENCE` | Check quantity before unit identity | reject-precedence atlas and wrong-unit fuzz seed | generated comparison/order mutants caught where viable; exact precedence regression passes |
| `ZRM02-PUBLIC-QUOTE` | Reintroduce public caller-row quote method or quote capability type | exact architecture allowlist and compile-fail doctest | synthetic Python architecture mutation plus compile-fail evidence; this is separate from cargo-mutants |
| `ZRM02-RENAMED-QUOTE` | Reintroduce the quote under an unlisted or already-allowlisted name, async/extern function, or function-pointer constant | owner/signature/multiplicity/value source inventory plus compiler API digests | synthetic renamed, wrong-owner, qualifier, and function-pointer regressions are rejected |
| `ZRM02-FUZZ-VALUE-ESCAPE` | Make the fuzz-only bridge return a quote or integer | exact `cfg(fuzzing)` raw-input/unit-return signature | synthetic return-value and missing-cfg regressions are rejected; cargo-mutants excludes this fuzz-only module |
| `ZRM02-ZERO-ROW-FORGET` | Delete evidence that a same-backend zero row quotes zero internally | internal retained counterexample | ordinary Rust unit test documents the hazard; it grants no authority |
| `ZRM03-PUBLIC-ADMISSION` | Reintroduce public compatibility/admission success method or error/result type | exact architecture allowlist and compile-fail doctests | synthetic Python architecture mutation plus compile-fail evidence; this is separate from cargo-mutants |
| `ZRM03-CONTENT-SUBSTITUTION-FORGET` | Delete copied-policy sensitive-field counterexample | internal verifier counterexample matrix | ordinary Rust unit test retains the hazard; governed rejection remains future work |
| `ZRM04-RAW-TYPED-HASH` | Reintroduce the former public raw-byte-to-`ResourceId` function | compile-fail doctest plus API review | compile-fail evidence using the former symbol; raw identifier construction remains an explicit non-claim |
| `ZRM04-VECTOR-DRIFT` | Change resource hash domain, frame, or canonical bytes | absent/present exact vectors and independent replay | generated Rust mutants and exact vector replay constrain the framing |
| `ZRM05-OPAQUE-FULL-DEBUG` | Print complete opaque bytes | opaque formatting tests | generated Rust mutants and value-independent redaction assertions constrain formatting |
| `ZRM05-WIRE-BYTES-DEBUG` | Print any 32-byte `ResourceWireV1` array field through raw or nested `Debug` | exhaustive wire-array and intrinsic nonce non-leak tests | generated Rust mutants plus fourteen-field value-independence, redaction-count, and byte-substring assertions constrain formatting; numeric scalars intentionally remain visible |

## Automated campaigns

### Unbound implementation-track preliminary campaign

```text
202 candidates
161 caught
41 unviable
0 missed
0 timed out
```

The original implementation track recorded these counts before integration but
did not preserve the exact command, cargo-mutants version, immutable revision,
or output artifact. They are retained as historical context and are not used as
final promotion evidence.

### Independent focused resource-kind campaign

An isolated reviewer ran cargo-mutants 26.0.0 against
`crates/zrm-policy/src/resource_kind.rs`: 20 generated mutants, 15 caught, 5
unviable, zero missed, and zero timed out. This advisory result is reproduced in
the agent-review receipt; it does not approve the RFC.

### Integrated configured campaign

The first full integration run generated 419 mutants and reported 291 caught,
102 unviable, and 26 missed. Every miss was in
`crates/zrm-policy/src/cost/fuzz_assertions.rs`, which is compiled only under
`cfg(fuzzing)` while cargo-mutants runs ordinary cargo tests. The module returns
no quote, cost, decision, or capability. `.cargo/mutants.toml` now excludes that
exact path-anchored module, with the exact API allowlist, deterministic corpus
replay, and changed-target PR-smoke cargo-fuzz campaigns providing separate
evidence. Sustained nightly fuzz and mutation coverage for the fuzz-only bridge
remain non-claims.

The final configured run used cargo-mutants 26.0.0:

```text
cargo +1.87.0 mutants --workspace --timeout 10 --build-timeout 60 --jobs 2 --output target/security-remediation-mutants-c6f0381
393 mutants tested
291 caught
102 unviable
0 missed
0 timed out
```

The final immutable implementation run used output directory
`target/security-remediation-mutants-c6f0381`. The SHA-256 digest of
`mutants.out/outcomes.json` was
`614960171f98d21448d34a237cfa9af904805ff9a80e2b36d9ad0d738f0536f0`.
The final source binding and output location are also recorded in
`evidence/security-remediation-local-gates-2026-07-12.json`.

## Non-claims

- The codec compile-fail test proves only that the former raw resource-ID hash
  symbol is absent. Codec and crypto do not yet have a renamed-API inventory,
  so code review and the Class E contract remain the defenses against a future
  differently named raw typed-ID helper.
- For `zrm-policy`, the exact owner/signature source inventory, restricted
  conditional profiles, canonical compiler-derived default/fuzz API digests,
  review contract, and Class E process provide layered renamed-API defenses.
- Internal counterexamples prove why an API is quarantined. They do not prove
  rows-root membership or exact verifier-policy binding.
- Mutation success establishes test sensitivity to sampled changes. It is not
  a proof that every defect is represented by a mutant.
- Ordinary cargo-mutants provides no mutation evidence for the `cfg(fuzzing)`
  assertion bridge. Fuzz execution and API-shape checks are distinct evidence,
  not a substitute claim of mutation completeness.
