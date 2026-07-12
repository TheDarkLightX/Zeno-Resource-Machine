# WP5 bounded-artifact candidate work log

**Author:** Dana Edwards

**Drafting assistance:** GPT-5.6

**Status:** integrated local Class C candidate evidence; no production authority

## Design packet

```text
Goal:
  Establish one fallible, protocol-ceiling-bounded owned copy of untrusted
  verifier artifact bytes, including deterministic allocation-refusal mapping.

Affected crates/modules:
  zrm-verifier-api artifact boundary, workspace dependency policy, tests,
  conformance records, and evidence documentation.

Exact typed statement or API:
  BoundedArtifactV1::try_new(&[u8], u32)
    -> Result<BoundedArtifactV1, ArtifactErrorV1>

Authority boundary:
  The result remains untrusted data. It creates no policy, verifier, proof,
  statement, output, freshness, canonicality, or verified-fact authority.

Invariants preserved/added:
  The selected limit cannot exceed the protocol ceiling. Oversize input rejects
  before reservation. Reservation refusal maps to a closed typed error. A
  successful value owns the exact copied bytes. Artifact bytes have no Debug
  implementation. Diagnostics are fixed and contain no artifact bytes.

Disaster states affected:
  Excessive single-artifact allocation, allocator abort through an infallible
  copy path, and accidental artifact disclosure through Debug diagnostics.

Canonical bytes or hashes affected:
  None. BoundedArtifactV1 has no canonical codec or authority hash.

Compatibility/versioning impact:
  Pre-alpha Rust API only. No wire, hash, policy, root, journal, or release ABI
  changes.

Tests added first or with the change:
  Boundary, precedence, ownership, compile-fail Debug, deterministic injected
  reservation refusal, platform-width conversion, and diagnostic tests.

Formal/model obligations:
  Kani coverage of this WP5 boundary remains open. No formal result is claimed.

Dependency impact:
  One inward workspace edge, zrm-verifier-api -> zrm-policy. No new external
  dependency.

Performance/resource bounds:
  One attempted exact reservation and one copy, both bounded by
  PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES. Aggregate transition budgets and
  allocator metadata are outside this slice.

Non-claims and known gaps:
  No authenticated policy limit, aggregate budget, proof parsing, verifier
  dispatch, cryptographic verification, verified fact, Kani result, WP5 fuzz
  campaign, secrecy, zeroization, state transition, commit, or production claim.
```

## Design-choice review packet

```text
Design forces:
  Bound untrusted bytes before owned allocation, preserve deterministic reject
  precedence, expose allocation refusal as a typed result, and keep authority
  absent from the caller-supplied limit.

Pattern selected, or no additional pattern:
  Private-field validated value object plus a private injectable reservation
  seam used only for deterministic failure testing. No backend/registry pattern
  is introduced in this slice.

Invalid states prevented:
  An artifact larger than the selected limit, a selected limit above the
  protocol ceiling, an allocation refusal reported as success, and direct Debug
  formatting of artifact bytes.

Extension point or closed-set reason:
  ArtifactErrorV1 is closed for this v1 boundary. Verifier backends and governed
  policy resolution remain later, separately reviewed authority boundaries.

Alternatives rejected:
  Infallible to_vec/copy because allocation failure can abort; public allocator
  callbacks because callers must not control authority behavior; a generic
  verifier service because no verifier authority exists yet.

Pattern-specific failure modes:
  Test-only reservation injection could alter production behavior if exposed.
  It remains private and is exercised through module tests only.

Enforcement and tests:
  Private fields, closed errors, exact architecture allowlist, compile-fail
  Debug doctest, deterministic injected refusal tests, generated mutation, and
  two named manual refusal mutants.

Technical AI-review status:
  Local structural gates report excellent-candidate with zero advisories. This
  is technical candidate evidence and does not replace Class C human review.
```

## Files in the implementation and evidence slice

- `crates/zrm-verifier-api/Cargo.toml`
- `crates/zrm-verifier-api/src/lib.rs`
- `crates/zrm-verifier-api/src/artifact.rs`
- `crates/zrm-verifier-api/tests/artifact.rs`
- `Cargo.toml`
- `Cargo.lock`
- `tools/check_architecture.py`
- `tools/tests/test_policy_checks.py`
- `tools/design_pattern_decisions.json`
- `README.md`
- `CONFORMANCE_MATRIX.json`
- `evidence/wp5-bounded-artifact-2026-07-12.json` (historical receipt)
- `evidence/wp5-environment-policy-2026-07-12.json`
- `evidence/wp5-integrated-2026-07-12.json`
- `evidence/wp5-gates/*.json`
- `evidence/README.md`
- `worklogs/2026-07-12-wp5-bounded-artifact.md`
- `PACKAGE_MANIFEST.json`

## Observable behaviors

- a slice at or below its selected bound is copied exactly;
- the artifact owns its copy and cannot observe later source mutation;
- the exact protocol ceiling is accepted;
- a selected limit above the protocol ceiling rejects before length handling;
- an artifact longer than the selected limit rejects before reservation;
- a zero limit accepts empty bytes and rejects one byte;
- reservation refusal is deterministically mapped to
  `ArtifactErrorV1::AllocationLimitExceeded`;
- limit and length rejection precede the injected reservation seam;
- a host width unable to represent a slice length rejects as
  `ArtifactErrorV1::ArtifactTooLarge` rather than creating a platform-specific
  public error variant;
- artifact bytes do not implement `Debug`;
- every error diagnostic is fixed, bounded, and contains no artifact bytes;
- the workspace policy permits only the inward
  `zrm-verifier-api -> zrm-policy` dependency edge.

## Revision-bound local evidence

The integrated index is
[`evidence/wp5-integrated-2026-07-12.json`](../evidence/wp5-integrated-2026-07-12.json).
It binds the local candidate results to clean source revision
`47fb1e536e1e8f4ffc753d607d4b65e1b9bf287a` and tree
`d6371e71bc9021dc066b4b2c81fe561963c1e6b0`.

The earlier compact receipt at
[`evidence/wp5-bounded-artifact-2026-07-12.json`](../evidence/wp5-bounded-artifact-2026-07-12.json)
is preserved as a historical snapshot. Its source revision, source hashes,
coverage, mutation results, and allocator-refusal gap remain true only for that
earlier snapshot. It is not the current integrated evidence index.

Recorded local results:

```text
cargo +1.87.0 fmt --all -- --check
PASS

cargo +1.87.0 check --workspace --all-targets --all-features --locked
PASS

cargo +1.87.0 clippy --workspace --all-targets --all-features --locked -- -D warnings
PASS

cargo +1.87.0 test --workspace --all-features --locked
PASS: 116 runtime tests; 0 failed

cargo +1.87.0 test --workspace --doc --locked
PASS: 3 compile-fail doctests; 0 failed

cargo +1.87.0 doc --workspace --no-deps --locked
PASS

python3 -m unittest discover -s tools/tests -p 'test_*.py'
PASS: 75 tests; 0 failed

python3 tools/check_architecture.py
PASS

python3 tools/check_complexity.py
PASS: 38 files; 300 functions; 0 warnings; 0 exceptions

python3 tools/check_code_quality.py
PASS: excellent-candidate; 16 rules; 5 decisions; 0 advisories

python3 vectors/independent_python/replay_resource_wire_v1.py --check
PASS: 6 artifacts; 4 digests

python3 fuzz/generate_corpus.py --check
PASS

cargo +nightly-2025-03-02 llvm-cov --package zrm-verifier-api \
  --all-targets --branch --json \
  --output-path target/wp5-integrated-coverage.json --locked
PASS for artifact.rs: 69/70 lines (98.57%); 4/4 branches (100%);
14/15 functions (93.33%); 44/51 regions (86.27%)

cargo +1.87.0 mutants --in-place -p zrm-verifier-api \
  --file 'crates/zrm-verifier-api/src/*.rs' \
  --timeout 20 --build-timeout 60 --output target/wp5-mutants-integrated
PASS: 19 generated; 12 caught; 7 compiler-unviable; 0 missed; 0 timed out

manual refusal mutants
PASS: ignore-refusal and misclassify-refusal both reached test execution and
exited 101

cargo +nightly-2025-03-02 miri test -p zrm-verifier-api \
  --all-targets --locked
PASS: 4 unit and 8 integration tests

cargo +1.87.0 audit
PASS: 15 dependency records; no warning or error reported

cargo +1.87.0 deny check --hide-inclusion-graph
PASS for root policy

cargo +1.87.0 deny --manifest-path fuzz/Cargo.toml check \
  --hide-inclusion-graph
PASS for fuzz policy

python3 tools/generate_bom.py --sbom target/wp5-integrated-sbom.json \
  --cbom target/wp5-integrated-cbom.json
PASS: 24 components; 66 dependency edges; 1 cryptography component
```

No 100% line-coverage claim is made. The unexecuted source-mapped line and
function are the platform-width conversion arm that cannot be reached on the
recorded 64-bit host. Uncovered assertion-failure regions are also reported.
Branch coverage for the instrumented artifact module is 4/4.

Every integrated gate record contains the SHA-256 of its captured local command
output. Coverage and generated-mutation records additionally bind their retained
result-payload hashes; named manual mutants bind each failure output separately.

Three setup invocations were rejected before evidence collection because their
flags or output locations were invalid: `cargo audit --locked`, a misplaced
`cargo-deny --manifest-path`, and absolute BOM output paths. Their corrected
forms above passed. The rejected setup attempts are not represented as passing
evidence.

## Mutants

- generated: 19;
- caught: 12;
- compiler-unviable: 7;
- missed: 0;
- timed out: 0;
- named manual mutant `ignore_reservation_refusal`: killed, exit 101;
- named manual mutant `misclassify_reservation_refusal`: killed, exit 101.

Compiler-unviable mutants do not contribute to a behavioral mutation score.
The two manual mutants specifically protect the allocation-refusal mapping that
generated mutation does not express directly.

## Remaining gaps and non-claims

- No Kani harness covers this WP5 boundary.
- No WP5-specific fuzz target or fuzz campaign has run.
- The caller-selected bound is not an authenticated policy decision.
- The ceiling bounds logical bytes for one artifact, not allocator metadata,
  aggregate transition bytes, proof work, output bytes, time, disk, or rate.
- Empty or bounded bytes may still be malformed for every future verifier.
- Artifact presence, proof format, canonicality, secrecy, zeroization, program
  identity, statement binding, cryptographic verification, output validation,
  governed cost accounting, registry resolution, and fact construction remain
  unimplemented.
- This slice provides no verifier backend, verified fact, semantic transition,
  state mutation, persistence, atomic commit, release provenance, production
  authority, or funds-safety claim.
- Local tests, coverage, mutation, Miri, dependency checks, and structural
  quality reports are scoped candidate evidence. They do not prove unbounded
  correctness or authorize production use.
