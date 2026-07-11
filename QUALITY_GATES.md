# ZRM Quality, Assurance, and Release Gates

**Status:** Normative gate design for the pre-alpha repository
**Rule:** A named gate is not evidence until its command, output, environment, and source revision are recorded.

This document converts the ZRM specification and `AGENTS.md` into executable engineering gates. Correctness gates are cumulative. Passing a later gate does not waive an earlier one.

---

## 1. Gate philosophy

The project uses five defense classes:

1. **Unrepresentable:** types and constructors exclude invalid state.
2. **Guarded transition:** deterministic validation rejects invalid transitions before mutation.
3. **Detected at commit:** compare-and-swap, database constraints, and atomic write sets prevent stale or duplicate commit.
4. **Detected by evidence:** tests, models, proof checks, and replay catch regressions.
5. **Bounded blast radius:** byte, depth, count, memory, time, and process-isolation limits contain failures.

No single test metric is sufficient. In particular:

- coverage is not correctness;
- formal-model success is not runtime refinement;
- proof generation is not proof verification;
- a signed artifact is not reproducible;
- a reproducible artifact is not semantically correct;
- green CI is not production authority.

---

## 2. Change classes and required gates

| Class | Description | Minimum gates |
| --- | --- | --- |
| A | prose, comments, non-normative diagrams | format, links, docs, claims review |
| B | non-authority tooling and diagnostics | A + compile, unit tests, dependency direction |
| C | semantic core, codec, policy, state, journal | B + property, mutation, fuzz corpus, Kani/model evidence, vectors |
| D | verifier, signature, proof, persistence, concurrency, or reward under a stable authority ABI | C + wrong-authority negatives, Miri/Loom as applicable, crash/replay tests, independent review |
| E | breaking canonical ABI, hash, nullifier, state root, authority identity/semantics, or release profile | D + RFC, compatibility plan, cross-language vectors, formal review, reproducible release rehearsal |

An agent or contributor MUST classify the change before implementation. Review may raise the class; it may not be lowered merely to avoid a gate.

---

## 3. Gate G0 — Repository hygiene

Required:

```bash
cargo fmt --all --check
cargo metadata --format-version 1 --locked
```

Policy checks:

- no secrets or private keys;
- no large binary artifacts without an RFC;
- no generated file modified directly;
- no absolute local paths in committed authority artifacts;
- no private project names or confidential implementation details in public documentation;
- no unresolved merge markers;
- no executable file without intentional mode;
- no hidden network fetch in tests or build scripts;
- no unreviewed Git dependency;
- no new `TODO`, `FIXME`, `HACK`, `XXX`, `unimplemented!`, or `todo!` in authority paths.

Recommended repository controls:

- protected default branch;
- required signed or verified commits for release branches;
- CODEOWNERS for core, codec, verifier, persistence, formal, and release surfaces;
- private vulnerability reporting;
- dependency update automation with review;
- OpenSSF Scorecard and CodeQL.

---

## 4. Gate G1 — Compilation and API discipline

Required command shape:

```bash
cargo check --workspace --all-targets --all-features --locked
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo test --workspace --doc --locked
```

Core crates SHOULD use:

```rust
#![forbid(unsafe_code)]
#![deny(missing_docs)]
#![deny(unused_must_use)]
```

Curated Clippy policy SHOULD deny or warn on:

- arithmetic side effects in authority code;
- lossy or sign-changing casts;
- indexing and panic-prone APIs;
- large enum variants where they hide allocation;
- needless pass-by-value;
- map-entry misuse;
- wildcard imports in critical modules;
- cognitive complexity and too-many-lines above project budgets;
- public APIs lacking `#[must_use]` where ignoring a result is unsafe;
- suspicious `Default` on authority-bearing values.

Lint suppression requires:

```rust
#[expect(clippy::lint_name, reason = "specific protocol reason")]
```

Broad `allow` attributes at crate or module level require a reviewed RFC.

---

## 5. Gate G2 — Architecture and dependency direction

The following dependency direction is enforced:

```text
primitive types / codec / crypto abstractions
                  |
                  v
policy / verifier ports / journal
                  |
                  v
pure semantic kernel / reference machine
                  |
                  v
application, proof, persistence, network, and runtime adapters
```

Forbidden:

```text
core -> application
core -> proof backend
core -> database
core -> network
core -> system time
core -> operating-system randomness
core -> process environment
```

Required evidence:

- generated dependency graph;
- denied cyclic crate dependencies;
- architecture test or script checking forbidden edges;
- review of feature-induced optional edges;
- no adapter type exposed through core public APIs.

---

## 6. Gate G3 — Complexity and auditability

Budgets are review triggers, not excuses for mechanical fragmentation.

| Metric | Preferred | Review trigger |
| --- | ---: | ---: |
| critical function logical lines | <= 40 | > 60 |
| cyclomatic complexity | <= 8 | > 12 |
| cognitive complexity | <= 10 | > 15 |
| nesting depth | <= 3 | > 4 |
| positional parameters | <= 4 | > 6 |
| public trait methods | <= 7 | > 10 |
| critical module logical lines | <= 400 | > 700 |

Unsafe blocks remain forbidden in the semantic core and require an isolated adapter safety case elsewhere.

Exceptions require:

- why splitting would reduce clarity or violate invariants;
- focused tests;
- named reviewer approval;
- an issue to remove the exception if temporary.

Auditability requirements:

- one invariant family per function;
- parsing, authentication, semantic validation, planning, commit, and journaling are separate stages;
- no boolean parameter that changes authority behavior; use an enum or profile;
- no stringly typed program, role, policy, unit, or resource-kind identifiers;
- no function named `handle`, `process`, `do_work`, or `utils` in the critical core without a narrower semantic name;
- comments explain invariants, authority, and rationale—not syntax.

---

## 7. Gate G4 — Unit, invariant, and vector tests

Every public constructor needs:

- one minimal accepted case;
- one boundary accepted case;
- one reject per invariant;
- one zero/all-zero reject where prohibited;
- overflow/maximum tests;
- canonical round trip;
- trailing-byte/noncanonical reject;
- unknown-critical-field reject for self-describing formats.

Every canonical object needs:

- exact byte fixture;
- exact digest fixture;
- independent implementation or cross-language replay;
- one-field mutation sensitivity tests;
- schema/version mutation reject.

Test names SHOULD state the rule:

```text
resource_commitment_changes_when_controller_changes
spent_resource_replay_rejects_without_state_change
wrong_logic_program_cannot_construct_verified_fact
```

Avoid test names such as `test_resource_1` or `works`.

---

## 8. Gate G5 — Property and metamorphic testing

Use deterministic seeds and commit minimized counterexamples.

Required property families:

- canonical encode/decode identity;
- noncanonical bytes reject;
- canonical ordering is permutation invariant where specified;
- order-sensitive lists remain order sensitive;
- resource role sets are disjoint;
- no accepted transition consumes the same resource twice;
- no accepted transition creates duplicate outputs;
- all accounting rows conserve or are covered by a transformation;
- reject preserves all state and external-effect counters;
- same statement and facts produce identical decisions and journals;
- disjoint transitions commute;
- stale pre-state commit rejects;
- domain/policy/program changes alter the bound statement;
- semantically equivalent proof-tree groupings preserve semantic epoch identity.

Metamorphic negative relations:

```text
change machine_id       -> statement/transition/nullifier changes
change policy_root      -> stale or mismatched facts reject
change resource role    -> logic binding changes or rejects
change unit_id          -> accounting rejects unless transformed
append trailing bytes   -> decode rejects
insert unknown critical -> decode rejects
swap verified program   -> verifier capability construction rejects
```

---

## 9. Gate G6 — BDD integration scenarios

BDD is mandatory for actor-visible workflows, not for replacing low-level invariant tests.

Each Gherkin scenario:

- names one rule;
- uses domain language rather than UI selectors;
- has deterministic fixtures;
- avoids wall clock and network;
- asserts stable decisions and committed effects;
- asserts no-op state on rejection;
- links to the corresponding CBC obligation.

Required initial features:

- exact-once resource consumption;
- stale policy rejection;
- unauthorized mint/burn/transform;
- concurrent double spend;
- proof from wrong program/profile;
- proof-task assignment, timeout, completion, challenge, and reward replay;
- crash recovery across commit boundaries;
- DA commitment without verified certificate.

---

## 10. Gate G7 — Mutation testing

The project uses two mutation layers.

### 10.1 Hand-authored critical mutants

Every critical guard gets a named mutation that:

- removes the check;
- inverts the condition;
- checks a sibling/wrong field;
- uses proposed data instead of recomputed data;
- moves commit before final validation;
- changes canonical order;
- silently wraps arithmetic;
- accepts a stale policy/program/profile;
- returns success on timeout or verifier error.

**Promotion requirement:** every critical mutant is killed by a named test.

### 10.2 General mutation testing

Command shape:

```bash
BASE_REF="${BASE_REF:-origin/main}"
mkdir -p target
git diff --binary --no-ext-diff "$BASE_REF"...HEAD > target/change.diff
cargo mutants --workspace --in-diff target/change.diff --output target/mutants
```

`--in-diff` receives a unified-diff file, not a branch name. Incremental mutation is a PR feedback gate; nightly and release gates still run the required full critical mutation set.

Targets:

- no missed mutant in critical changed code;
- >= 90% useful mutation score in authority crates;
- timeout or unviable mutants classified separately;
- exclusions reviewed and documented.

A surviving mutant is a test gap or unjustified code. It is never ignored merely because line coverage is high.

---

## 11. Gate G8 — Fuzzing and malformed grammar

Use `cargo-fuzz`/libFuzzer or a reviewed equivalent.

Initial fuzz targets:

- resource wire decoder;
- transition envelope decoder;
- accepted-journal and reject-receipt decoders;
- policy decoder;
- canonical list framing;
- accumulator proofs;
- proof/signature adapter envelopes;
- duplicate-key JSON pre-parser where JSON is accepted diagnostically;
- maximum count/depth/length edges.

Fuzz assertions:

- no panic, abort, UB, unbounded allocation, or hang;
- successful decode re-encodes to identical canonical bytes;
- invalid bytes never construct validated or authenticated types;
- parse failure never mutates state;
- error output is bounded and does not disclose secrets.

Cadence target:

| Gate | Budget |
| --- | --- |
| PR corpus replay | all committed cases |
| PR smoke | 30-60 seconds per changed target |
| nightly | >= 15 minutes per critical target |
| release rehearsal | >= 1 hour per critical target or equivalent continuous campaign |

Time budgets MAY be adjusted by hardware, but reduced coverage must be reported.

---

## 12. Gate G9 — Undefined behavior and unsafe code

Default: `unsafe` is forbidden in core crates.

An unsafe adapter requires:

- a `// SAFETY:` argument at every block;
- public safety contract;
- ownership/aliasing/threading invariants;
- Miri execution;
- Kani harness where bounded;
- structure-aware fuzz target;
- no exposed safe API that permits UB;
- independent specialist review;
- `cargo geiger` or equivalent inventory;
- a removal or isolation rationale.

Command shape:

```bash
cargo +nightly miri test --workspace
```

Miri success is not proof of soundness. It only strengthens evidence for exercised executions.

---

## 13. Gate G10 — Concurrency and atomicity

Any synchronized in-memory authority state requires Loom or equivalent exploration.

Command shape:

```bash
RUSTFLAGS="--cfg loom" cargo test --release --test loom_atomic_admission
```

Any persistent machine requires deterministic crash injection at each write boundary:

```text
before validation
between validation and plan persistence
before transaction begin
between each logical write
before commit record
between commit and acknowledgement
on recovery
```

Required invariants:

- at most one winner for conflicting commits;
- no partial application state;
- no nullifier without matching effects;
- no effects without matching nullifier/replay state;
- no duplicate reward;
- committed journal matches committed state;
- recovery is idempotent;
- stale plans fail compare-and-swap.

Database transaction success alone is insufficient if external side effects occur outside the same atomic boundary. Use outbox/inbox patterns with exact-once or explicitly at-least-once semantics.

---

## 14. Gate G11 — Bounded model checking

Kani harnesses SHOULD prove bounded safety for:

- no panic/overflow in constructors and accounting;
- no out-of-bounds codec behavior;
- exact-once over bounded resource sets;
- role disjointness;
- transformation coverage;
- reject-is-no-op;
- small accumulator updates;
- commit-plan preconditions.

Command shape:

```bash
cargo kani --workspace
```

A Kani timeout, unsupported feature, or unwinding bound warning is not success. Bounds and exclusions must be recorded in the conformance matrix.

---

## 15. Gate G12 — Deductive and theorem-prover evidence

The project selects one primary Rust deductive lane by RFC—Verus or Creusot initially—to avoid duplicated proof maintenance.

Lean is used for stable abstract theorems and refinement targets.

Initial theorem obligations:

- canonical framing injectivity under explicit hash assumptions;
- exact-once state transition;
- accounting conservation;
- transformation coverage;
- reject-is-no-op;
- disjoint commutativity;
- semantic epoch root tree independence;
- proof-task reward exact-once.

Rules:

- no `sorry`, admitted theorem, or trusted axiom without a named assumption registry entry;
- solver `UNKNOWN` and timeout fail;
- theorem statements match runtime units, bounds, and role semantics;
- runtime linkage is demonstrated by extraction, shared vectors, generated constants, or a reviewed refinement argument;
- proofs are rebuilt from a pinned toolchain.

Aeneas or another Rust-to-proof-assistant translator may be explored, but generated models and handwritten external definitions remain in the TCB and require review.

---

## 16. Gate G13 — Proof and signature adapters

The governed verifier registry and its sealed adapter wrapper own the full authority boundary; only the registry constructs a verified fact:

```text
untrusted artifact
  -> bounded canonical decode
  -> cryptographic verification
  -> stage-specific statement/output/program/policy binding
  -> sealed VerifiedFact capability
```

Precommit resource facts bind the final transition statement and exact claim hash. Admission facts bind `JournalDraft`. Postcommit aggregation facts bind `AcceptedJournal`. Tests MUST reject lifecycle-stage substitution.

Mandatory negatives:

- wrong program/key/verifier;
- wrong statement or journal;
- wrong machine/domain/epoch;
- stale policy;
- unsupported proof/receipt kind;
- fake/dev/test proof in stronger profile;
- malformed artifact;
- timeout, crash, missing executable, or ambiguous output;
- metadata stronger than authenticated proof;
- valid proof for wrong resource role or ordinal.

Raw artifact bytes and caller-provided `verified=true` fields must never be accepted by the semantic kernel.

---

## 17. Gate G14 — Dependency and supply-chain assurance

Required PR checks:

```bash
cargo deny check
cargo audit
cargo vet --locked   # when a vet policy exists
```

Also require:

- dependency review for pull requests;
- build-script and proc-macro review;
- exact pinning for critical cryptographic/proof dependencies;
- minimal enabled features;
- no duplicate critical cryptographic versions without an RFC;
- license policy;
- OSV/advisory scan;
- SBOM and cryptographic bill of materials for releases.

OpenSSF Scorecard findings are risk inputs, not an automatic correctness score.

---

## 18. Gate G15 — Coverage and test adequacy

Targets:

| Scope | Line | Branch | Mutation |
| --- | ---: | ---: | ---: |
| changed critical core | 100% review target | 100% review target | all named critical mutants |
| authority crates | >= 95% | >= 90% | >= 90% useful score |
| workspace | >= 90% | >= 85% | reported |

Exclusions require a reason and reviewer approval. Generated code and defensive unreachable branches are reported separately.

Coverage never authorizes deleting meaningful edge cases to improve a percentage.

---

## 19. Gate G16 — Documentation and claims

A semantic change updates, as applicable:

- `SPECIFICATION.md`;
- public API docs;
- architecture decision records;
- threat model/disaster states;
- conformance matrix;
- vectors;
- migrations;
- README scope and non-claims.

Reserved claims such as **verified**, **private**, **available**, **final**, **reproducible**, and **production-ready** require matching evidence.

Documentation must distinguish:

```text
implemented
locally tested
formally modeled
proof-backed
release-backed
production-authoritative
```

These statuses are not synonyms.

---

## 20. Gate G17 — Reproducible build and provenance

A reproducibility claim requires independent clean builds that recreate bit-for-bit identical specified artifacts from the same declared source, build environment, and instructions.

Release inputs include:

- source archive and commit;
- dirty-tree state;
- compiler, Cargo, linker, target, libc, and system image;
- dependency and toolchain locks;
- environment allowlist;
- build paths/path remapping;
- timestamps and `SOURCE_DATE_EPOCH` policy;
- locale/timezone;
- generated sources;
- network isolation;
- commands;
- output hashes.

Release outputs include:

- binaries/libraries;
- schemas/vectors;
- SBOM/CBOM;
- test/fuzz/mutation/formal reports;
- SLSA v1.2 provenance;
- verification summary;
- signatures/transparency-log entry;
- release non-claims.

One same-host rebuild is not an independent reproducibility claim.

---

## 21. Gate G18 — Agent-generated code

All code generated or modified by an AI agent is untrusted contribution material.

Required agent evidence:

- task interpretation;
- affected invariants and disaster states;
- files inspected;
- proposed design and alternatives;
- tests written before/with code;
- commands run and exact results;
- self-review findings;
- remaining uncertainty and non-claims.

Agents MUST NOT:

- claim a command was run when it was not;
- disable tests, lints, or formal checks to obtain green output;
- weaken a postcondition or expected value without explaining the semantic change;
- bulk-refactor unrelated code;
- introduce a dependency without review metadata;
- copy code with unknown license;
- treat generated proof bytes as authority;
- edit generated files instead of the generator;
- merge or promote their own critical change.

Human review remains required for Classes C-E. Class D/E changes require at least two independent reviewers, including one reviewer focused on the authority boundary.

NIST SSDF and its AI profile are process inputs; they do not replace ordinary secure development and evidence requirements for agent-generated code.

---

## 22. Gate G19 — Release promotion

### 22.1 Pre-alpha implementation claim

Requires:

- types and constructors;
- deterministic reference semantics;
- vectors;
- invariant/negative tests;
- honest gaps.

### 22.2 Experimental proof-backed claim

Additionally requires:

- real proof/signature artifact;
- exact verifier replay;
- wrong-artifact negatives;
- source and toolchain binding;
- no stronger semantic claim than the journal proves.

### 22.3 Release-backed claim

Additionally requires:

- signed release manifest;
- reproducibility evidence;
- SLSA provenance;
- current advisory scan;
- public replay;
- governed verifier/policy roots.

### 22.4 Production-ready claim

Additionally requires:

- durable atomic commit;
- concurrency and crash evidence;
- no pending critical CBC obligations;
- formal obligations satisfied at the declared scope;
- independent security review and disposition;
- operational monitoring, rollback, incident, and key-rotation plans;
- explicit DA, privacy, oracle, and physical-attestation posture.

---

## 23. Required evidence artifact format

Every nontrivial gate emits a canonical evidence record:

```json
{
  "schema": "zrm/evidence-record/v1",
  "source_revision": "...",
  "dirty": false,
  "gate_id": "G11",
  "tool": {
    "name": "kani",
    "version": "...",
    "executable_sha256": "..."
  },
  "command": ["cargo", "kani", "--workspace"],
  "environment_policy_root": "sha256:...",
  "started_at": "informational-only",
  "duration_ms": 0,
  "status": "pass|fail|review-needed",
  "scope": [],
  "result_root": "sha256:...",
  "assumptions": [],
  "exclusions": [],
  "non_claims": []
}
```

Wall-clock fields are informational and must not affect semantic hashes.

---

## 24. Definition of done

A change is done only when:

```text
requirements traced
&& architecture preserved
&& code understandable
&& negative tests exist
&& relevant gates pass
&& vectors/docs/matrix updated
&& evidence is replayable
&& claims are honest
&& human review completed at required class
```

“Code compiles” and “the happy-path test passes” are not definitions of done.
