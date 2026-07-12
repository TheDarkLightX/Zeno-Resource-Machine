# WP5 bounded-artifact candidate work log

**Author:** Dana Edwards

**Drafting assistance:** GPT-5.6

**Status:** unreviewed Class C candidate

## Goal and authority boundary

Add one inert input type that owns a fallibly allocated copy of untrusted
verifier bytes under an explicit limit no greater than the protocol ceiling.
The type must not grant proof, policy, program, statement, output, freshness,
canonicality, or verification authority.

The numeric limit remains caller supplied. A future governed verifier registry
must recheck the retained byte length against authenticated machine and verifier
policies before dispatch.

## Files

- `crates/zrm-verifier-api/Cargo.toml`
- `crates/zrm-verifier-api/src/lib.rs`
- `crates/zrm-verifier-api/src/artifact.rs`
- `crates/zrm-verifier-api/tests/artifact.rs`
- `Cargo.toml`
- `Cargo.lock`
- `tools/check_architecture.py`
- `tools/tests/test_policy_checks.py`
- `README.md`
- `CONFORMANCE_MATRIX.json`
- `PACKAGE_MANIFEST.json`

Local design drafts and the blocked state/root experiment are excluded from the
commit and public evidence.

## Behaviors under test

- a slice at or below its selected bound is copied exactly;
- the artifact owns its copy and cannot observe later source mutation;
- the exact protocol ceiling is accepted;
- a selected limit above the protocol ceiling rejects before length handling;
- an artifact longer than the selected limit rejects before allocation;
- a zero limit accepts empty bytes and rejects one byte;
- artifact bytes do not implement `Debug`;
- every error diagnostic is fixed, bounded, and contains no artifact bytes;
- the workspace dependency policy permits only the inward
  `zrm-verifier-api -> zrm-policy` edge.

## Design and code-quality decision

`BoundedArtifactV1` is a private-field validated value object at an untrusted
input boundary. It has no clone, serialization, default, or debug surface. The
implementation uses a closed error enum, checks protocol and selected limits
before allocation, calls `try_reserve_exact`, then copies only into the reserved
capacity. No backend interface, callback registry, broad manager trait, or
verified-fact constructor is introduced.

## Verification record

The earlier local draft reported a compile-failing red phase but retained no
complete command output. That report is not counted as repository evidence.

The retained compact receipt is
[`evidence/wp5-bounded-artifact-2026-07-12.json`](../evidence/wp5-bounded-artifact-2026-07-12.json).
It binds the following results to source revision
`cc570d151cdef0ebb13a1783fbacb25c16bdc3f5` and tree
`e9f27d795f9ef614557ba51c593a4cda1bbab0c3`. The later evidence-only commit
does not change Rust source, tests, dependencies, or repository checkers.

Revision-bound results:

```text
cargo fmt --all --check
PASS

cargo check --workspace --all-targets --all-features --locked
PASS

cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
PASS

cargo test --workspace --all-features --locked
PASS: 112 runtime tests; 0 failed

cargo test --workspace --doc --locked
PASS: 3 compile-fail documentation tests; 0 failed

python3 tools/check_package_manifest.py
PASS: all listed bytes and SHA-256 digests match

python3 tools/check_conformance.py
PASS: 45 obligations, live anchors, valid promotion states, acyclic dependencies

python3 tools/check_architecture.py
PASS: exact internal and external dependency allowlists match

python3 tools/check_complexity.py
PASS: 38 files, 293 functions, 0 warnings, 0 exceptions

python3 tools/check_code_quality.py
PASS: excellent-candidate, 16 rules, 5 reviewed decisions, 0 advisories

python3 -m unittest discover -s tools/tests -v
PASS: 75 tests

cargo +nightly llvm-cov --package zrm-verifier-api --all-targets --branch --summary-only --locked
PASS: 31/31 lines, 4/4 branches, 46/48 regions

cargo mutants --in-place -p zrm-verifier-api \
  --file 'crates/zrm-verifier-api/src/*.rs' \
  --timeout 20 --build-timeout 60
PASS: 15 generated; 12 caught; 3 unviable; 0 missed; 0 timed out

```

Mutation results cover every viable generated source mutant. The three unviable
mutants did not compile and therefore granted no surviving behavior claim.

## Remaining uncertainty and non-claims

- Deterministic allocator-refusal injection is not implemented. The fallible
  reservation mapping is code-reviewed but not directly exercised.
- The ceiling bounds logical artifact bytes, not allocator overhead or aggregate
  bytes across a transition.
- Empty bytes prove only bounded copying; a verifier may later reject them as a
  malformed proof.
- Artifact presence, proof format, canonicality, secrecy, zeroization, program
  identity, statement binding, cryptographic verification, output validation,
  cost accounting, and fact construction remain unimplemented.
- This slice provides no verifier backend, verified fact, semantic transition,
  state mutation, persistence, commit, or production authority.
- Human Class C review and hosted CI are required before merge.
