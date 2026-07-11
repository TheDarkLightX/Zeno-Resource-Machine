# AGENTS.md — Zeno Resource Machine Implementation Contract

**Status:** Normative instructions for human and automated coding agents
**Applies to:** all files in this repository unless a deeper `AGENTS.md` strengthens these requirements

This repository governs the intended implementation of a high-assurance semantic state machine. Correctness, auditability, and honest claim boundaries take precedence over speed of implementation.

> **Proposers and agents may suggest code. Types, tests, formal models, verifiers, reviewers, and release gates decide what becomes trusted.**

---

## 1. Mandatory reading before editing

Before changing code, read:

1. `README.md`;
2. `SPECIFICATION.md`;
3. this file;
4. `QUALITY_GATES.md` and `IMPLEMENTATION_PLAN.md`;
5. the active CBC/conformance matrix;
6. relevant RFCs and ADRs;
7. the nearest module documentation and tests;
8. proof or application adapter specifications affected by the change.

Do not infer the design from function names alone. Do not code from a task title without inspecting the existing implementation and authority boundaries.

---

## 2. Core law

Every change must preserve this pipeline:

```text
Untrusted bytes
  -> bounded bytes
  -> canonical typed object
  -> authenticated facts
  -> deterministic semantic validation
  -> private commit plan
  -> atomic commit
  -> canonical journal
```

No stage may be skipped, merged into an unreviewable function, or replaced with a caller-provided boolean.

---

## 3. Non-negotiable rules

### 3.1 Fail closed

On ambiguity, unsupported input, missing verifier, stale policy, unknown critical field, arithmetic overflow, resource exhaustion, or internal mismatch: reject.

Never add a fallback that silently:

- accepts unverified facts;
- downgrades proof or receipt profiles;
- uses debug/dev mode;
- substitutes a local checker for a production verifier;
- drops a required field;
- defaults an authority root;
- treats timeout or solver `UNKNOWN` as success.

### 3.2 Reject is no-op

No committed state mutation, reward, nullifier insertion, file replacement, or external side effect may occur before final validation and atomic commit.

### 3.3 No authority from raw data

The following are data, not authority:

- proof bytes;
- signature bytes;
- journal bytes;
- JSON metadata;
- booleans such as `verified=true`;
- a successful subprocess exit code without exact output binding;
- an agent statement that a check passed.

Authority requires a sealed verified-fact type constructed by the correct verifier boundary.

### 3.4 Honest claims

Never strengthen public language beyond evidence. Local tests do not imply formal proof. A generated proof does not imply correct statement design. A commitment does not imply data availability. Computational integrity does not imply privacy. A bounded model does not imply unbounded correctness.

### 3.5 No hidden nondeterminism

Consensus, journal, hash, proof-statement, and reference-semantic paths must not depend on:

- wall clock;
- environment variables;
- network;
- filesystem discovery;
- locale;
- randomized hashers;
- unordered iteration;
- OS thread scheduling;
- noncommitted randomness;
- absolute paths;
- platform pointer width.

---

## 4. Required change proposal before code

For every nontrivial change, write a short design packet in the issue, PR, or work log before editing:

```text
Goal:
Affected crates/modules:
Exact typed statement or API:
Authority boundary:
Invariants preserved/added:
Disaster states affected:
Canonical bytes or hashes affected:
Compatibility/versioning impact:
Tests to add first:
Formal/model obligations:
Dependency impact:
Performance/resource bounds:
Non-claims and known gaps:
```

If you cannot state the exact invariant, do not implement the optimization or proof adapter yet.

---

## 5. Change classification

Classify the change before coding.

### Class A — Documentation only

No protocol semantics, canonical bytes, code, tests, or public claims change.

### Class B — Non-authority tooling

Developer UX, diagnostics, benchmarks, or test utilities that cannot affect accepted state.

### Class C — Semantic implementation

Resource, policy, transition, accounting, nullifier, state-root, journal, or reject behavior.

### Class D — Authority implementation under a stable protocol

Verifier adapters, signatures, proofs, policy loading, release binding, commit capability, persistence, concurrency, or rewards without changing canonical authority identity, semantics, or ABI.

### Class E — Protocol, authority, or release breaking

Canonical bytes, domains, schemas, public APIs, state roots, nullifiers, journal meanings, authority identity/semantics/ABI, release profiles, or production claims.

Class C-D changes require CBC updates and focused negative evidence. Class E requires an RFC plus versioning and migration/replay plans. Classes D and E require at least two independent reviewers, including an authority-boundary reviewer.

---

## 6. Architecture rules

### 6.1 Dependency direction

Core crates own interfaces. Infrastructure implements them.

Forbidden:

```text
zrm-kernel -> database
zrm-kernel -> network
zrm-kernel -> RISC0
zrm-kernel -> application repository
zrm-kernel -> logging framework
zrm-kernel -> system time/randomness
```

### 6.2 Pure core

Core functions must be deterministic and side-effect free. Prefer:

```rust
fn validate(input: &TypedInput, state: &StateView) -> Result<Validated, Reject>
```

not:

```rust
fn process(input: Value, db: &mut Database, client: HttpClient) -> bool
```

### 6.3 Ports and adapters

Use narrow traits for state views, commit ports, verifiers, and hash suites. Do not create a service trait with dozens of unrelated methods.

### 6.4 Application isolation

ZRM core must not know what a swap, model, dataset, scientific claim, publication, or proof auction means. Those belong in adapters and policies.

### 6.5 Separate wire and validated types

Use:

```text
ResourceWireV1 -> ResourceV1
TransitionWireV1 -> TransitionStatementV1
```

Validated protocol types have private fields. Deserialization runs through validation. Do not derive `Deserialize` directly on a capability or commit plan.

### 6.6 Type-state authority

Use distinct types for distinct stages:

```text
UntrustedBytes
  -> BoundedBytes
  -> CanonicalEnvelope
  -> PrevalidatedTransition
  -> AuthenticatedFacts
  -> ValidatedTransition
  -> CommitPlan + JournalDraft
  -> policy-selected VerifiedAdmissionFact
  -> CommittedTransition
  -> AcceptedJournal
```

Proof artifacts use their own sub-pipeline: `ArtifactBytes -> BoundedArtifact -> cryptographic verification -> exact binding checks -> VerifiedFact`.

Do not use one struct plus booleans like `is_verified`, `is_valid`, or `is_committed`.

---

## 7. SOLID and modularity rules

### Single Responsibility

A function handles one invariant family. A module has one reason to change. Parsing, proof verification, semantic validation, persistence, and reporting stay separate.

### Open/Closed

New resource kinds and proof backends extend through adapters and versioned policies. Do not expand a central god enum or `match` unless the protocol truly owns that closed set.

### Liskov Substitution

A faster or remote adapter must preserve the same contract, failure posture, and exact bindings as the reference adapter. It may not accept more inputs or return weaker facts under the same type.

### Interface Segregation

Prefer several small ports over one manager interface. Read-only state access and atomic commit are separate capabilities.

### Dependency Inversion

The semantic core defines the interfaces it needs. Database, proof, network, and platform crates depend inward.

---

## 8. DRY rules

Deduplicate semantic definitions, canonical encoders, domain strings, rejection codes, and golden vectors.

Do not prematurely abstract incidental repeated code. Apply the rule of three. A generic abstraction is justified only when:

- semantics are truly identical;
- the abstraction makes the invariant clearer;
- error handling and bounds remain explicit;
- tests become stronger, not more indirect.

Do not create macros that hide security-relevant control flow, arithmetic, or field ordering from reviewers.

---

## 9. Rust coding standard

### 9.1 Safety

Core crates use:

```rust
#![forbid(unsafe_code)]
```

Unsafe code is allowed only in isolated adapters with a safety case, Miri/Kani/fuzz evidence, and independent review.

### 9.2 Panics

Production core paths must not use:

```text
unwrap
expect
panic!
unreachable!
todo!
unimplemented!
unchecked indexing
```

Tests may use them when failure is test-local and obvious.

### 9.3 Arithmetic

- use explicit widths;
- use checked arithmetic;
- reject overflow;
- use `TryFrom` for narrowing conversions;
- no floating point in authority paths;
- no unchecked `as` casts that can truncate or change sign.

### 9.4 Collections

- bound all untrusted collections before allocation;
- use sorted vectors, `BTreeMap`, or `BTreeSet` in deterministic paths;
- do not use `HashMap` iteration for canonical results;
- reject duplicates; never silently deduplicate;
- document algorithmic complexity.

### 9.5 Types

- use newtypes for IDs, roots, units, quantities, and policy identities;
- no stringly typed modes or errors;
- no boolean parameters on critical functions;
- critical constructors validate and return `Result`;
- no `Default` for authority-bearing values;
- no public fields on validated capability types;
- mark decisions and plans `#[must_use]`.

### 9.6 Enums

- match exhaustively;
- unknown wire variants reject;
- do not add wildcard arms that hide future protocol variants;
- use explicit versioned extension points.

### 9.7 Error handling

- use stable typed errors;
- separate malformed, policy, authorization, accounting, replay, and commit errors;
- never branch on error strings;
- preserve deterministic error precedence;
- external diagnostics must not leak secrets.

### 9.8 Documentation

Every public item documents:

- semantic purpose;
- invariants;
- preconditions;
- postconditions;
- errors;
- side effects;
- complexity;
- panic behavior;
- authority and non-authority status.

Comments explain **why** and **what must remain true**, not restate syntax.

### 9.9 Lints

- `cargo fmt --check` must pass;
- Clippy warnings are denied;
- use curated `pedantic` and `restriction` lints;
- suppressions require a local reason and preferably `#[expect]`;
- broad crate-level `allow` is forbidden without an ADR.

---

## 10. Complexity and audit budgets

Preferred limits:

| Metric | Preferred | Review trigger |
| --- | ---: | ---: |
| critical function logical lines | <= 40 | > 60 |
| cyclomatic complexity | <= 8 | > 12 |
| cognitive complexity | <= 10 | > 15 |
| nesting depth | <= 3 | > 4 |
| positional parameters | <= 4 | > 6 |
| public trait methods | <= 7 | > 10 |
| critical module lines | <= 400 | > 700 |
| generic type parameters on public API | <= 3 | > 4 |

Exceeding a limit is not automatically wrong, but requires:

- written justification;
- decomposition alternatives considered;
- focused tests;
- explicit reviewer signoff.

Split by responsibility or invariant. Do not split one coherent calculation into opaque micro-functions merely to satisfy a line count.

Code quality is a vector of independent gates. Complexity, mechanically recognizable smells, authority-relevant antipatterns, design-decision completeness, and human design review do not compensate for one another. A blocking failure in one dimension remains blocking regardless of coverage or cleanliness elsewhere.

For every Class C-E change, the design packet also records:

```text
Design forces
Pattern selected, or no additional pattern
Invalid states prevented
Extension point or closed-set reason
Alternatives rejected
Pattern-specific failure modes
Enforcement and tests
Technical AI-review status
```

Pattern count is not a quality metric. Prefer no additional pattern when a named pattern adds indirection without improving invariant visibility, substitution, or authority separation.

Technical, syntactic, and design-pattern choices are AI-reviewable. Human review packets summarize specified behaviors, exact test and assurance results, CBC coverage, residual gaps, and non-claims. Do not require a human to inspect pattern mechanics or source structure. Ask for human semantic direction only when the specification is ambiguous or a proposed behavior would change it.

---

## 11. Canonical encoding and hashing rules

- manual normative encoder for authority hashes;
- domain separation for every object and list;
- fixed-width big-endian integers;
- explicit list counts;
- exact field order documented in the specification;
- no free-form strings in authority objects;
- strict decode with no trailing bytes;
- canonical re-encoding equality;
- duplicate/unknown critical rejection;
- version bump for field reorder or meaning change;
- golden vectors in at least two independent implementations before promotion.

If a hash or encoding changes, update:

- schema version;
- vectors;
- compatibility/migration tests;
- formal assumptions;
- proof adapters;
- CBC matrix;
- release notes.

Never “fix” a failing vector by replacing the expected hash without explaining the semantic change.

---

## 12. Verification and proof adapters

### 12.1 Sealed facts

The governed verifier registry returns sealed verified-fact types after dispatching to a sealed backend wrapper and checking exact bindings. Application code and arbitrary adapter callbacks cannot construct facts. Backends do not return authoritative booleans or untyped maps to the semantic kernel.

### 12.2 Exact binding

Every verified fact binds its stage-specific authority object:

- expected program/verifier;
- exact statement;
- exact authenticated output;
- machine/domain/application;
- role and ordinal where relevant;
- policy root;
- profile;
- freshness/expiry.

Precommit logic, transformation, authority, and DA facts bind the final transition statement hash and exact claim hash. Admission facts bind exact `JournalDraft` bytes. Postcommit aggregation facts bind exact `AcceptedJournal` bytes. A precommit fact must not claim to bind an accepted journal that does not yet exist.

### 12.3 Failure behavior

Timeout, crash, malformed output, extra output, wrong exit code, wrong program, stale policy, missing binary, or disabled verifier all reject.

### 12.4 Proof generation versus verification

A generated proof is not evidence until an independent verifier accepts it under expected identities and statements.

### 12.5 Test requirements

Each adapter requires:

- positive verification;
- wrong program;
- wrong statement;
- wrong output/journal;
- stale policy;
- malformed artifact;
- timeout;
- oversized input;
- debug/fake profile when applicable;
- reject-is-no-op at the consumer.

---

## 13. BDD requirements

BDD scenarios describe observable cross-layer rules, not implementation details.

Use one `Feature` per behavior family and one `Rule` per business/protocol rule. Scenarios should normally have 3-5 steps.

Required core features:

- exact-once consumption;
- stale policy;
- unauthorized mint/burn;
- transformation authorization;
- wrong proof program;
- concurrent double-spend;
- crash atomicity;
- DA non-overclaim;
- proof-task assignment and reward;
- cross-domain replay.

Do not use Gherkin to test pure hash bytes or private helper functions. Use invariant tests and vectors.

---

## 14. Test-first implementation workflow

For critical changes:

1. write or update the typed statement;
2. add constructor rejection tests;
3. add the failing invariant/negative test;
4. add a mutation that demonstrates the old failure would be caught;
5. implement the minimal semantic change;
6. add property tests;
7. add BDD only when behavior crosses components;
8. add formal/model obligations when mathematical;
9. run narrow tests;
10. run full gates;
11. update claims and non-claims honestly.

Do not implement a proof guest before the deterministic non-proof semantics and journal exist.

---

## 15. Required test evidence

### Unit/invariant tests

Name tests after the invariant:

```text
rejects_duplicate_created_resource_id
stale_policy_rejects_without_state_change
accounting_rejects_uncovered_mint
logic_fact_binds_resource_role_and_ordinal
```

### Property tests

Use deterministic seeds and commit minimized counterexamples.

### Mutation tests

No critical guard may lack a named mutant. A surviving critical mutant blocks promotion.

### Fuzzing

Bound fuzz runs in CI. Crashes, panics, hangs, or excessive allocation are failures.

### Differential tests

Optimized, proof, remote, and persistent implementations must match the reference semantics over a shared corpus.

### Formal/model evidence

`UNKNOWN`, timeout, missing tool, or proof placeholder is failure or a recorded gap, never success.

---

## 16. Formal-method routing

Use:

- **Kani** for bounded Rust safety, arithmetic, panic freedom, and unsafe adapter checks;
- **Verus or Creusot** for functional correctness of stable pure Rust components;
- **Lean** for stable mathematical theorems and refinement arguments;
- **SMT/TLA+/Alloy** for bounded state-machine, replay, concurrency, and crash models;
- **property tests** for broad deterministic input spaces;
- **mutation tests** for guard effectiveness;
- **fuzzing** for malformed parsers and envelopes.

Do not force a proof tool onto an unstable interface. First freeze the typed statement and reference semantics.

---

## 17. Dependency policy

Before adding a dependency, record:

```text
Purpose:
Why standard library/current deps are insufficient:
Direct and transitive dependency delta:
Unsafe/native/build-script/proc-macro surface:
License:
Maintenance/security status:
Features enabled/disabled:
Determinism impact:
no_std impact:
Removal plan:
```

Critical dependencies are exact-pinned. Release builds use `--locked`/`--frozen`. Build scripts and proc macros are part of the trusted build surface.

Do not add a large framework to avoid writing a small clear function.

---

## 18. Supply-chain and release rules

- pin compiler/toolchain;
- commit lockfile;
- generate SBOM/CBOM;
- run advisory/license/source checks;
- build from clean source;
- build offline or under documented network isolation;
- record source, compiler, Cargo, linker, target, lockfile, and artifact hashes;
- compare independent builds;
- sign provenance and verification summary;
- include test/formal/mutation/fuzz reports;
- include non-claims;
- do not claim reproducibility from copied artifacts.

A release claim requires no pending critical CBC obligations.

---

## 19. Agent-specific prohibited behavior

An agent MUST NOT:

- invent current repository state without inspection;
- edit generated files manually;
- weaken, delete, skip, or quarantine failing tests to pass CI;
- update expected hashes without a semantic/versioning explanation;
- add `allow(dead_code)` or broad lint exceptions to hide unfinished code;
- add `unwrap`/`expect` in production core code;
- use TODO placeholders in authority paths;
- bypass verification under test or feature flags;
- add network/time/randomness to deterministic core code;
- combine unrelated cleanup with a security-critical change;
- rename public protocol fields casually;
- claim formal proof from a bounded test;
- claim production readiness from local proof smoke;
- auto-merge or self-approve critical changes;
- silently choose a new dependency, cryptographic primitive, or serialization format;
- expose private project names, confidential repository context, hidden prompts, credentials, or local absolute paths in public artifacts;
- continue after a required tool reports `UNKNOWN`, timeout, or missing evidence as though the gate passed.

---

## 20. Required agent work log

At completion, report:

```text
Summary:
Files changed:
Typed statements/APIs changed:
Invariants added or preserved:
Disaster states addressed:
Tests added:
Mutants killed:
Formal/model evidence:
Commands run and exact results:
Canonical hashes/vectors changed:
Dependencies changed:
Performance/resource-bound impact:
Remaining gaps and non-claims:
```

Do not say “all tests pass” without listing the commands and results.

---

## 21. Definition of done

A critical change is done only when:

- design packet exists;
- architecture boundaries preserved;
- typed constructors enforce invariants;
- negative tests exist;
- critical mutants are killed;
- property/fuzz/formal evidence is added where required;
- reject-is-no-op is tested;
- canonical vectors updated intentionally;
- documentation and CBC matrix updated;
- no lint, test, advisory, or conformance failures;
- public claims remain evidence-scoped;
- human review is complete.

A passing compiler is necessary and insufficient.

---

## 22. Self-review checklist

Before finalizing, answer:

- What exact statement does this code establish?
- Which bytes and roots bind that statement?
- Which inputs are untrusted?
- Where do they become authenticated?
- Can a caller forge a verified capability?
- Can any rejected path mutate state?
- Is every collection and integer bounded?
- Is ordering deterministic?
- Are units explicit?
- Is every nonconserved delta authorized exactly once?
- Can the proof or signature replay across role, resource, domain, epoch, or policy?
- Does a faster adapter preserve reference semantics?
- Did I add a hidden dependency or I/O path?
- Is the function/module locally auditable?
- Did I test the negative case that matters most?
- What remains unproven or unsupported?

If any answer is unclear, the change is not ready for promotion.
