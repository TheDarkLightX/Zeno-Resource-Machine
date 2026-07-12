# Agent Work Log: Security and correctness review remediation

## Task interpretation

Remediate the six findings reported against the implemented pre-alpha slice,
preserve current canonical resource bytes and identifiers, and keep every
unauthenticated policy/verifier operation outside the public authority surface.

## Scope and non-goals

In scope:

- reject zero quantity at the policy-bound dimension check;
- make the fixed lifecycle quantity policy canonical and satisfiable;
- quarantine caller-selected verifier-cost and candidate-admission operations;
- remove the public raw-byte resource-ID derivation boundary;
- redact nonce-bearing diagnostic formatting;
- strengthen counterexample and independent-review requirements.

Out of scope:

- canonical policy bytes or policy identity;
- an authenticated verifier registry, cost model, or activation path;
- proof dispatch, final `ResourceV1`, state, persistence, or commit authority;
- marker-resource semantics;
- production or release claims.

## Files and specifications inspected

- `AGENTS.md`
- `README.md`
- `SPECIFICATION.md`
- `QUALITY_GATES.md`
- `IMPLEMENTATION_PLAN.md`
- `CONFORMANCE_MATRIX.json`
- `SECURITY.md`
- `.github/CODEOWNERS`
- `docs/BRANCH_PROTECTION.md`
- affected type, codec, crypto, policy, kernel, fuzz, and formal-harness code

## Change class

Class E overall. The patch deliberately removes or narrows public pre-RFC APIs
that could otherwise be mistaken for authority. Zero-quantity enforcement is a
Class C semantic correction. Diagnostic redaction is Class B hardening.

## Affected invariants

- Version-one policy-bound resources have positive quantity.
- Lifecycle non-fungible policy candidates use the only meaningful maximum,
  one atom.
- Caller-selected cost rows cannot produce a public checked-quote value.
- Candidate policy identifiers and structural comparisons cannot authorize a
  verifier.
- Only the canonical codec exposes typed resource-ID derivation.
- Default diagnostic formatting does not disclose resource nonces.

## Affected CBC obligations

`ZRM-CBC-001`, `ZRM-CBC-015`, `ZRM-CBC-024`, `ZRM-CBC-033`,
`ZRM-CBC-035`, `ZRM-CBC-039`, `ZRM-CBC-044`, `ZRM-CBC-045`, and the new
`ZRM-CBC-046`. Every status and non-claim remains scoped in the conformance
matrix; none of these references promote the repository to production.

## Disaster states

- zero-quantity value or accounting ambiguity;
- cost-row substitution that defeats resource-exhaustion controls;
- verifier/program/policy substitution under a copied identifier;
- typed identifiers derived from malformed same-length resource bytes;
- nonce and private-resource correlation through diagnostics;
- semantic omissions surviving high structural test coverage.

## Authority boundary

All current policy and verifier candidates remain inert data. This change does
not introduce an authenticated policy, governed row, verifier fact, or commit
capability. Public access is reduced wherever a caller-selected value could be
misread as an authority-bearing result.

## Proposed design

1. Reject zero in `ResourceKindPolicyV1::validate_dimensions` for every mode,
   while preserving stable reject precedence.
2. Require a lifecycle non-fungible candidate to declare `quantity_max == 1`.
3. Keep verifier-cost arithmetic and compatibility predicates private to their
   crate for tests and formal harnesses. No public operation returns quote or
   admission-like success until governed registry construction exists.
4. Co-locate resource-wire encoding and resource-ID hashing so the raw hash
   helper is private and `ResourceWireV1::resource_id()` is the only supported
   public typed derivation.
5. Fully redact nonces from `Debug`, including raw wire and nested resource
   values. Preserve explicit byte accessors.
6. Add specification-counterexample review and record that host-side reviewer
   independence remains a release blocker until live settings and identities
   prove it.

### Design-choice review

- Design forces: fail closed, preserve vectors, prevent authority-shaped APIs,
  and avoid inventing the unresolved authority ABI.
- Pattern selected, or no additional pattern: capability/API quarantine plus
  typed policy rejection; no new extensibility pattern.
- Invalid states prevented: zero policy-bound resources, noncanonical lifecycle
  maxima, externally produced unauthenticated quotes/admission successes, raw
  same-length typed-ID derivation, and nonce-bearing default diagnostics.
- Extension point or closed-set reason: marker permission and governed verifier
  selection require a later versioned authority RFC.
- Alternatives rejected: documentation-only warnings, deprecation without
  fail-closed behavior, caller-supplied membership proofs, hashing Rust layout,
  duplicate permissive parsing, and nonce fingerprints.
- Pattern-specific failure modes: test-only helpers accidentally re-exported,
  vector drift, error-precedence drift, and nested derived `Debug` leakage.
- Enforcement and tests: external compile-fail checks, exact vectors, finite
  policy oracle, Kani, fuzzing, mutation tests, and diagnostic non-leak tests.
- Technical AI-review status: independent automated reviews are advisory and
  do not replace required human semantic and authority-boundary review.

## Alternatives considered

- Leave public methods with stronger warnings: rejected because callers can
  still obtain authority-shaped success values.
- Invent governed row membership now: rejected because the policy ABI and
  activation root are not frozen.
- Treat `EvidenceOnly` as implicit marker permission: rejected because the
  specification requires explicit policy permission.
- Fingerprint nonces: rejected because fingerprints still permit correlation.

## Test-first plan

- all-mode zero rejection and lifecycle maximum matrix;
- error-precedence oracle, full-width bounded checks, fuzz, and killed mutants;
- external compile-fail checks for quarantined APIs;
- internal substitution counterexamples documenting why quarantine is needed;
- exact resource-ID vector replay and malformed same-length negatives;
- direct and nested nonce formatting non-leak tests;
- full workspace, lint, quality, conformance, package, fuzz, Kani, Miri,
  coverage, and mutation replay in proportion to the changed risk.

## Implementation summary

- `ResourceKindPolicyV1` now rejects zero quantities in every v1 accounting
  mode and enforces the RFC-0002 lifecycle maximum candidate rule with explicit
  constructor and resource error precedence.
- Caller-row quote, quote-result, request, compatibility, and admission-success
  APIs are absent from the default external surface. Internal predicates remain
  available only to tests, Kani, and one raw-byte, unit-returning
  `cfg(fuzzing)` assertion sink.
- The architecture gate records owner-qualified function signatures,
  multiplicity, qualifiers, public types, re-exports, and public const/static
  values in authority-adjacent policy modules. A separate pinned
  compiler-derived canonical span-free rustdoc JSON digest binds the complete
  package API under default and `cfg(fuzzing)` profiles without host paths.
  Conditional compilation across every policy source is restricted to reviewed
  test, Kani, and fuzz profiles. Counterexamples cover renamed, async, extern,
  wrong-owner, function-pointer, outer/inner/comment-obfuscated/raw-identifier
  `cfg` and `cfg_attr`, nested-module, unreviewed `path`-module, macro-generated,
  and value-returning fuzz escapes. Reviewed `path` attributes resolve only to
  regular files within the complete scanned policy source tree; linked source
  directories and unreviewed source inclusion fail closed.
- The canonical codec owns private resource-ID hashing. Hash frame widths are
  checked from the actual encoded bytes and actual domain length rather than
  duplicated wire-size constants.
- Default `Debug` formatting is constant-redacted for every opaque 32-byte type
  and every 32-byte array candidate in `ResourceWireV1`; numeric wire scalars
  remain visible.
- Frozen prior semantics and the RFC-0002 proposal remain separate executable
  Python models with an exact bounded differential corpus. CBC-046 records the
  positive, bounded, mode-canonical dimension obligation.

## Files changed

Production and test code:

- `crates/zrm-types/src/opaque.rs`
- `crates/zrm-codec/{Cargo.toml,src/error.rs,src/lib.rs,src/resource_wire_v1.rs}`
- `crates/zrm-codec/tests/resource_wire_v1.rs`
- `crates/zrm-crypto/{src/lib.rs,tests/vectors.rs}`
- `crates/zrm-policy/src/{cost.rs,error.rs,lib.rs,resource_kind.rs,verifier.rs}`
- `crates/zrm-policy/src/cost/{fuzz_assertions.rs,kani_harnesses.rs,tests.rs}`
- `crates/zrm-policy/src/resource_kind/kani_harnesses.rs`
- `crates/zrm-policy/src/verifier/tests.rs`
- `crates/zrm-policy/tests/{policy_model.rs,resource_dimension_atlas.rs}`
- affected codec, policy, intrinsic-resource, fuzz, and tooling regressions

Normative, assurance, and process artifacts:

- `README.md`, `SPECIFICATION.md`, `AGENTS.md`, `QUALITY_GATES.md`,
  `IMPLEMENTATION_PLAN.md`, `CONFORMANCE_MATRIX.json`, `SECURITY.md`
- `rfcs/0002-security-review-api-quarantine.md`
- `docs/AUTHORITY_MAP.md`, `docs/SECURITY_REVIEW_REMEDIATION_2026_07.md`,
  `docs/dependency-reviews/sha2-0.11.0.md`
- the baseline and proposed resource-kind reference-model packages
- `tools/check_architecture.py`, `tools/check_conformance.py`, their tests, and
  the deterministic fuzz-corpus generator
- review templates, branch-protection guidance, workflows, this worklog, and
  the remediation evidence records

## Typed statements and APIs changed

Added public error variants:

```text
ResourceDimensionErrorV1::ZeroQuantityForbidden
PolicyValidationErrorV1::LifecycleQuantityMaximumMustBeOne
```

Removed or narrowed from the default public API:

```text
VerifierCostModelV1::compute_quote
VerifierPolicyV1::{cost_quote_request, admission_reservation_quote_request}
MachinePolicyV1::{validate_verifier_candidate_compatibility,
                  validate_admission_verifier_candidate}
VerifierCostQuoteRequestV1
VerifierCostQuoteV1
VerifierCompatibilityErrorV1
derive_resource_id_from_canonical_wire
HashConstructionError::InvalidResourceWireLength
ResourceIdDerivationError::Hash(HashConstructionError)
```

The codec replacement uses
`ResourceIdDerivationError::{Encode, HashFrameLengthOverflow, AllZeroDigest}`.
The only fuzz-only public exception is
`fuzz_assert_untrusted_candidate_cost_invariants(&[u8]) -> ()`; it returns no
quote, cost, policy decision, or capability.

## Tests added or changed

- five-mode zero and maximum decisions, lifecycle policy construction, and
  exact constructor/resource precedence;
- `EvidenceOnly` zero-marker negative and non-lifecycle empty-policy behavior;
- full-width implementation-side Rust atlas and Kani predicates;
- frozen baseline, proposed RFC, counterexample replay, and exact differential
  Python tests;
- caller-selected zero-row and copied-policy-content counterexamples retained
  behind crate-private helpers;
- external compile-fail checks plus exact architecture-allowlist mutations,
  including renamed APIs and fuzz sinks returning values;
- actual-length hash-frame conversion/overflow checks and unchanged exact
  absent/present resource vectors;
- malformed same-length strict-decoder negative;
- all-opaque, raw-wire, and nested-resource constant-redaction checks;
- maximum-width diagnostic bound checks for every numeric public error family;
- exact deterministic corpus membership so libFuzzer discoveries cannot enter
  a committed corpus silently.

## Mutants killed or surviving

The first integrated full run generated 419 mutants and reported 26 misses,
all in `cost/fuzz_assertions.rs`, because that file compiles only under
`cfg(fuzzing)` while cargo-mutants runs ordinary cargo tests. The bridge returns
no authority-shaped value. It is now narrowly excluded by module name, with
exact API allowlisting, deterministic corpus replay, and changed-target PR-smoke
cargo-fuzz as separate evidence. Mutation coverage for that fuzz-only bridge is an
explicit non-claim.

The final configured full-workspace run used cargo-mutants 26.0.0 and tested
393 mutants: 291 caught, 102 unviable, zero missed, and zero timed out. The
exact command, source binding, output digest, and the fuzz-only module
exclusion are recorded in `evidence/SECURITY_REMEDIATION_MUTATION_MAP.md` and
the local-gate receipt.

## Formal/model evidence

- Frozen prior-specification model: 21 tests.
- RFC-0002 proposed/differential model: 24 tests. The bounded delta contains
  four removed lifecycle policy maxima, three removed lifecycle resource
  states, no added accepted state, and five reason-only changes.
- Kani: the resource-kind harness ranges over all five modes and full-width
  `u128` maxima and quantities; it checks the explicit predicate and exact
  lifecycle-constructor relation. Full final-tree replay is recorded in the
  local-gate receipt.
- Miri: a full exploratory workspace run passed; the final hash-framing,
  diagnostic-maximum, and resource-dimension tests were replayed separately on
  the final working tree. Miri does not prove all executions or dependency
  soundness.
- Fuzz PR smoke: the assertion-only cost campaign completed 10,345,988 executions in 46
  seconds; the resource-dimension campaign completed 15,581,739 executions in
  46 seconds, both without a crash, timeout, or assertion failure. Their
  non-deterministic discovered corpus files were reviewed, removed, and are now
  rejected by the exact corpus-membership gate. These runs satisfy the 30-to-60
  second PR-smoke band and do not satisfy or claim the 15-minute sustained
  nightly duration.

## Canonical hashes and vectors changed

No canonical resource bytes, expected resource identifiers, crypto-suite ID,
or nullifier digest changed. Independent replay passed six binary artifacts and
four protocol digests. The codec hash owner changed; the exact domain and inner
and outer length framing did not.

## Dependencies changed

No new third-party package or feature entered the lockfile closure. `zrm-codec`
now directly depends on the existing locked, feature-minimal `sha2 0.11.0` so
the canonical encoder owns the private resource-ID hash boundary.
`zrm-crypto` retains its direct `sha2` edge for suite-ID and transparent
nullifier operations. The direct-edge review is recorded in
`docs/dependency-reviews/sha2-0.11.0.md`.

## Performance and resource-bound impact

One constant-time zero comparison is added to policy-bound dimension checks.
Hashing remains bounded to the existing 595/603-byte encodings. The fuzz-only
assertion sink reads at most 88 bytes and performs fixed checked arithmetic.
No production input limit or asymptotic bound changes.

## Commands executed

| Command | Result | Evidence/artifact |
| --- | --- | --- |
| `cargo test --workspace --all-targets --locked` | PASS, 111 tests | local working-tree replay |
| `cargo test --workspace --doc --locked` | PASS, 5 compile-fail doctests | local working-tree replay |
| strict workspace Clippy and rustfmt | PASS, zero denied warnings | local working-tree replay |
| `python3 -m unittest discover -s tools/tests -v` | PASS, 96 tests | tooling regressions |
| reference-model discovery | PASS, 45 tests | frozen and proposed oracles |
| architecture, complexity, code-quality | PASS; exact allowlist; zero advisories; `excellent-candidate` | generated local reports |
| configured branch coverage | PASS; workspace 99.14%/100%, policy 99.86%/100%, kernel 100%/100% | `target/llvm-cov-branch.json` |
| independent vector replay | PASS, 6 binary artifacts and 4 digests | independent Python replay |
| deterministic corpus replay | PASS, exact named membership | `fuzz/generate_corpus.py --check` |
| changed-target fuzz PR smoke | PASS, 25,927,727 combined executions in two 46-second campaigns | local libFuzzer output; sustained nightly fuzz remains pending |
| targeted final Miri replay | PASS, codec 20 tests plus 5 policy tests | pinned nightly Miri |
| full configured mutation | PASS; cargo-mutants 26.0.0; 393 tested, 291 caught, 102 unviable, 0 missed, 0 timed out | `target/security-remediation-mutants` and final receipt |
| `cargo kani --workspace --quiet` | PASS; 18 harnesses; 0 reachable failures | Kani 0.60.0 output and final receipt |
| advisory/dependency/BOM gates | PASS; 1,159-advisory database; 14 root and 23 fuzz locked dependencies; deny checks green; 23 components, 65 edges, 1 cryptography component | audit, deny, SBOM, CBOM output and final receipt |

## Self-review

- [x] no unrelated changes
- [x] no weakened tests or claims
- [x] no raw data promoted to authority
- [x] reject-is-no-op preserved
- [x] arithmetic and bounds checked
- [x] canonical bytes/vectors replayed without change
- [x] docs/matrix updated
- [x] dependency impact reviewed
- [x] remaining uncertainty disclosed

## Remaining gaps and non-claims

The implemented repository still has no final resource, authenticated policy
activation, governed verifier registry, state machine, persistence, atomic
commit, or production authority. Live host reviewer settings cannot be proven
by static repository files.

## Human review required

- Specified behaviors for review: positive v1 policy-bound quantity; canonical
  lifecycle maximum and exact-one resource; fixed error precedence; no public
  caller-row quote or candidate-admission success; codec-owned typed resource
  hashing; constant-redacted opaque and fixed-wire diagnostics.
- Exact assurance results: summarized above and machine-readable in the final
  local-gate and agent-review receipts.
- CBC obligations covered: `ZRM-CBC-001`, `ZRM-CBC-015`, `ZRM-CBC-024`,
  `ZRM-CBC-033`, `ZRM-CBC-035`, `ZRM-CBC-039`, `ZRM-CBC-044`,
  `ZRM-CBC-045`, and new `ZRM-CBC-046`, all within their recorded partial or
  existing scoped statuses.
- Remaining gaps and non-claims: governed authority ABI and host controls.
- Required reviewers/roles: semantic reviewer plus independent
  authority-boundary reviewer; release reviewer for host-control claims.
- Review focus: reject semantics, public API absence, vector stability, and
  diagnostic non-disclosure.
- Promotion blocked until: all gates pass and required independent reviewers
  approve the Class E change.
