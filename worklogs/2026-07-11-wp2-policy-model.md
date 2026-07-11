# WP2 policy-model implementation work log

## Design packet

Goal:

Record the completed Class C human review of WP0/WP1, then implement the safe pre-RFC portion of the WP2 policy model: validated in-memory policy objects, protocol limit enforcement, explicit unit checks, admission-mode consistency, validity windows, inert validation-context data, and checked verifier-cost arithmetic.

Change class:

Class C semantic implementation. This change does not define or alter canonical policy bytes, policy hashes, authority identities, state roots, nullifiers, journals, or release profiles.

Affected crates and modules:

- `zrm-types` only if an already specified primitive type is missing;
- new `zrm-policy` pure `no_std` crate;
- workspace dependency and architecture allowlists;
- focused tests, Kani harnesses, fuzz smoke, mutation map, conformance matrix, README, and evidence records.

Exact typed APIs:

```text
MachinePolicyCandidateV1 -> TryFrom -> MachinePolicyV1 | PolicyValidationErrorV1
ResourceKindPolicyCandidateV1 -> TryFrom -> ResourceKindPolicyV1 | PolicyValidationErrorV1
ValidationContextCandidateV1 -> TryFrom -> ValidationContextV1 | PolicyValidationErrorV1
PolicyLimitsCandidateV1 -> TryFrom -> PolicyLimitsV1 | PolicyValidationErrorV1
VerifierPolicyCandidateV1 -> TryFrom -> VerifierPolicyV1 | PolicyValidationErrorV1
VerifierCostRowV1 + policy-derived bounded lengths -> checked local cost quote | VerifierCostErrorV1
ResourceKindPolicyV1 + UnitId + QuantityAtoms -> dimension check | ResourceDimensionErrorV1
```

Authority boundary:

The new types validate deterministic local policy invariants only. `ValidationContextV1` remains inert data. This slice does not construct `TrustedValidationContext`, register verifier backends, dispatch artifacts, or construct any `Verified*Fact` capability. Those operations belong to a later, separately reviewed authority-boundary slice.

Invariants preserved or added:

- schema version one is explicit and checked;
- policy validity windows are non-inverted;
- every machine limit is at or below its compile-time protocol ceiling;
- a v1 machine policy admits the complete 603-byte `ResourceWireV1` form;
- the v1 machine policy uses the schema-fixed SHA-256 suite;
- `LocalKernel` has no admission verifier policy and `RequiredVerifier` has exactly one;
- lifecycle non-fungible resource quantity is exactly one;
- resource unit checks compare opaque `UnitId` values without conversion or floating point;
- resource quantities cannot exceed the policy maximum;
- verifier-policy candidates are structurally compared with machine-policy candidates at a caller-supplied epoch, with a separate exact admission-policy ID check;
- local verifier-cost quotes use policy-derived private bounds, checked `u128` intermediates, and local candidate caps;
- all operations are deterministic, allocation-free, side-effect-free, and `no_std`.

Disaster states and CBC obligations:

- zero or collapsed semantic identities: `ZRM-CBC-002`;
- unlike units treated as equivalent: `ZRM-CBC-015`;
- overflow or lossy cost arithmetic: `ZRM-CBC-016`;
- wrong program, key, profile, stale policy, or revocation: `ZRM-CBC-010` remains specified; candidate-shape checks receive no authority claim;
- unbounded byte/count/depth/storage or verifier work: `ZRM-CBC-045`;
- agent contribution without durable evidence: `ZRM-CBC-039`.

Canonical bytes or hashes affected:

None. `SPECIFICATION.md` freezes only `ResourceWireV1` authority bytes. Policy encoders, enum tags, set/map roots, reject codes, and hashes remain blocked on an approved Class E RFC with independent vectors.

Compatibility and versioning impact:

The Rust APIs are pre-alpha and implement normative logical schemas only. They do not create a stable wire ABI or migration promise.

Tests to add first or with code:

- accepted minimal and protocol-ceiling policy candidates;
- one reject for every local constructor invariant;
- deterministic cross-field reject precedence atlas;
- all machine-limit ceiling boundaries;
- local-versus-required admission pairing;
- resource unit mismatch and quantity boundary checks;
- lifecycle quantity checks;
- verifier cost-model, candidate validity-window, admission-policy ID, and proof-mode checks;
- checked cost multiplication, addition, narrowing, and budget rejects;
- arbitrary-input fuzz smoke over limit and cost candidates;
- capability-absence API check showing no trusted context or verified fact is exported.

Formal and model obligations:

Kani is scoped to exact limit-bound predicates, admission pairing, and checked verifier-cost arithmetic over bounded symbolic inputs. Boundary-concolic-style exploration is offline bug-discovery evidence and is promoted only through deterministic regression tests. Policy codec/hash proofs and verifier-registry authority proofs remain later obligations.

Dependency impact:

No new third-party dependency. `zrm-policy` depends inward on `zrm-types` and `zrm-crypto` only.

Performance and resource bounds:

All constructor and validation operations are constant-time in input size and allocate no memory. A local verifier-cost quote uses a fixed number of checked arithmetic operations.

Non-claims and known gaps:

- no canonical policy bytes, policy hash, policy set/map root, or independent policy vector;
- no policy activation, migration, rollback, or predecessor-set membership implementation;
- no authenticated `TrustedValidationContext` construction;
- no verifier registry, backend, artifact dispatch, or sealed authority fact;
- no resource, transition, accounting kernel, state, persistence, commit, journal, proof, or application implementation;
- no production, release, privacy, availability, or physical-truth claim;
- human Class C review remains required for this new slice.

## Evidence log

Final hardened-tree replay completed on 2026-07-11 from branch `agent/wp2-policy-model`, based on merged `origin/main` revision `e955175067a6588762024bd8a890b79d3da8dc8b`. The implementation commit is `04fc103a27c711c3b12f9da0dec4d0e4a93a0dc7`, with tree `58b9cc29bfb012984de90b2167010cc335d44541`. The structured record `evidence/wp2-local-gates-2026-07-11.json` binds that exact candidate revision.

Implemented scope:

- added the pure, `no_std`, non-published `zrm-policy` crate with private-field machine, resource-kind, verifier, cost-model, limits, validity-window, and inert validation-context values;
- specialized WP2 root and identifier candidates in `zrm-types` without defining policy bytes, ordering, root derivation, authentication, or activation;
- kept verifier-cost request bounds private and derived them only from a locally validated verifier-policy candidate;
- named successful cost arithmetic a local `VerifierCostQuoteV1`, which carries no governed-charge or verifier authority;
- separated general verifier-candidate shape checking from the exact admission-mode and admission-policy-ID check;
- enforced exact quantity one on each lifecycle non-fungible resource candidate;
- added the deterministic policy-cost fuzz target and three generated corpus seeds covering success, bound rejection, and arithmetic overflow;
- added a fail-closed LLVM JSON coverage checker and CI thresholds for workspace line/branch coverage and changed-policy-crate coverage;
- clarified `CbC` as correct-by-construction and `CBC` as the project-local Construction Boundary Conformance obligation family;
- recorded the maintainer's completed Class C review of merged WP0/WP1 without extending that review to WP2.

Exact local commands and results:

```text
cargo +1.87.0 fmt --all -- --check
  PASS

cargo +1.87.0 metadata --format-version 1 --locked
cargo +1.87.0 check --workspace --all-targets --all-features --locked
cargo +1.87.0 clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo +1.87.0 test --workspace --all-targets --all-features --locked
cargo +1.87.0 test --workspace --doc --locked
cargo +1.87.0 doc --workspace --all-features --no-deps --locked
  PASS; 65 ordinary tests, zero failures; documentation built

cargo +nightly-2025-03-02 llvm-cov --workspace --all-features --locked --branch --json --output-path target/llvm-cov-branch-final-tree.json
python3 tools/check_coverage.py target/llvm-cov-branch-final-tree.json --min-lines 90 --min-branches 85
python3 tools/check_coverage.py target/llvm-cov-branch-final-tree.json --scope-prefix crates/zrm-policy --min-lines 95 --min-branches 100
  PASS; workspace lines 1597/1626 = 98.22%; branches 95/98 = 96.94%
  PASS; zrm-policy lines 895/903 = 99.11%; branches 56/56 = 100.00%

cargo +1.87.0 mutants -p zrm-policy --timeout 10 --build-timeout 60 --jobs 4 --output target/mutants-wp2-final-tree
  PASS; 188 mutants tested: 147 caught, 41 unviable, 0 missed, 0 timed out

cargo kani --workspace
  PASS; 8/8 harnesses, 0 failures

cargo +nightly-2025-03-02 miri test --workspace --all-features --locked
  PASS; 65 tests, 0 failures

python3 fuzz/generate_corpus.py --check
cargo +nightly-2025-03-02 fuzz run resource_wire_v1_decode -- -seed=1 -runs=10000 -max_len=16385 -timeout=5
cargo +nightly-2025-03-02 fuzz run policy_cost_v1 -- -seed=1 -runs=10000 -max_len=88 -timeout=5
  PASS; generated corpus exact; 10,000 runs per target; no crash or timeout
  final local counters: ResourceWire cov=411 ft=443; policy cost cov=65 ft=84

cargo +1.87.0 audit --deny warnings
cargo +1.87.0 audit --deny warnings --file fuzz/Cargo.lock
cargo +1.88.0 deny check
cargo +1.88.0 deny --manifest-path fuzz/Cargo.toml check
  PASS; root 13 and fuzz 22 dependency closures had no RustSec advisory failure
  PASS; advisories, bans, licenses, and sources policies

python3 tools/check_repository_hygiene.py
python3 tools/check_conformance.py
python3 tools/check_architecture.py
python3 tools/check_package_manifest.py
python3 -m unittest discover -s tools/tests -v
python3 vectors/independent_python/replay_resource_wire_v1.py --check
  PASS after manifest regeneration; 45 CBC obligations, exact dependency allowlists,
  15 Python policy-check tests, 6 binary vector artifacts, and 4 protocol digests
```

Review findings resolved before the final replay:

- a public caller could originally construct verifier-cost requests with substituted caps; request fields are now private, policy-derived, and yield only an inert local quote;
- required admission originally failed to compare the exact selected `VerifierPolicyId`; a separate admission-candidate check now rejects local mode and mismatched IDs first;
- lifecycle dimension checks originally admitted quantity zero; each lifecycle resource now requires exactly one while the policy maximum remains a separate bound;
- the cost fuzzer originally clamped away artifact and statement bound rejects; it now preserves raw reject inputs and separately constructs the bounded reservation lane;
- the first nightly job budget could not contain two sequential 900-second campaigns; it is now 40 minutes;
- line coverage was enforced while branch coverage was only observed; LLVM branch instrumentation and fail-closed threshold parsing are now in CI;
- `CBC-010` was briefly overstated as partially implemented by unauthenticated candidate checks; it remains `specified`.

Evidence limits and remaining uncertainty:

- Kani's WP2 arithmetic harnesses use fixed coefficients and bounded `u8` lengths; all 8 reachable harnesses pass, while Kani emits target-feature, future-compatibility, and unreachable unsupported-construct warnings. This is bounded model evidence, not a universal proof.
- Miri covers exercised executions and does not prove the absence of undefined behavior in every future adapter.
- LLVM branch coverage uses the pinned nightly compiler because cargo-llvm-cov marks `--branch` unstable. Three workspace branches outside `zrm-policy` remain uncovered and visible.
- Fuzz counters are instrumentation-specific local search evidence. The committed policy corpus does not contain a dedicated statement-only bound seed, although a deterministic unit test pins that path and the fuzzer can reach it.
- The 41 unviable mutants did not compile. The two schema-version getter substitutions are mechanically equivalent under constructors that reject every other version. Kani-only bodies are routed to Kani rather than ordinary mutation execution.
- No new third-party dependency was added. Cargo-vet, SBOM, CBOM, signed provenance, independent reproducible builds, and external security audit remain incomplete.
- The local Codex peer-review helper stalled without producing output and was interrupted; it contributes no evidence. Three read-only agent reviews did find and drive the fixes above, but they are not human approval.
- WP2 remains unreviewed contribution material. Human Class C review is required before promotion or merge. No code in this slice is safe for funds or production authority.
