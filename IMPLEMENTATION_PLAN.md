# ZRM Implementation Plan

**Status:** Normative sequencing plan for the first reference implementation
**Objective:** Build a minimal, auditable semantic kernel before adding proof backends, persistence, networking, privacy, or optimizations.

Each work package has an entry gate, deliverables, required evidence, and a stop condition. Agents MUST NOT skip forward because a later feature is more visible.

---

## Work-package dependency graph

```text
WP0 repository controls
  |
  v
WP1 primitive types + canonical codec
  |
  +-----------> WP2 policy model
  |                |
  v                v
WP3 resource + statement objects
  |                |
  +--------+-------+
           v
WP4 reference accumulators/state
           |
           v
WP5 verifier capability ports
           |
           v
WP6 pure semantic kernel
           |
           v
WP7 accepted journals, reject receipts, and vectors
           |
     +-----+------+----------------+
     |            |                |
     v            v                v
WP8 formal     WP9 persistence   WP10 proof-resource adapter
     |            |                |
     +-----+------+----------------+
           v
WP11 second-domain adapter
           |
           v
WP12 proof/recursive adapters
           |
           v
WP13 release rehearsal
```

---

## WP0 — Repository bootstrap and governance

### Deliverables

- Rust workspace with pinned `rust-toolchain.toml` and `rust-version`;
- root `Cargo.toml` with shared lint policy;
- `README.md`, `SPECIFICATION.md`, `AGENTS.md`, `QUALITY_GATES.md`, `SECURITY.md`, `CONTRIBUTING.md`;
- `CONFORMANCE_MATRIX.json` checker;
- CODEOWNERS and pull-request template;
- branch protection plan;
- license decision;
- CI skeleton with no unpinned third-party actions;
- dependency policy (`deny.toml`, audit/vet plan);
- generated-code and evidence directories.

### Required checks

- repository contains no secret/private context;
- default branch protection is configured;
- private vulnerability reporting is enabled;
- CI permissions are least privilege;
- workflow actions are pinned by full commit SHA;
- release environments require approval.

### Stop condition

No semantic code until repository policy and change-class workflow are reviewable.

---

## WP1 — Primitive types and canonical codec

### Crates

```text
zrm-types
zrm-codec
zrm-crypto
```

### Types

- `MachineId`;
- `DomainId`;
- `ApplicationId`;
- `ResourceId`;
- `ResourceKindId`;
- `ResourceLogicId`;
- `LogicProfileId`;
- `CryptoSuiteId`;
- `VerifierId`;
- `PolicyId`;
- `UnitId`;
- `ControllerRoot`;
- `ProvenanceRoot`;
- `TransitionId`;
- `StatementHash`;
- `Commitment`;
- `Nullifier`;
- `ResourceFlagsV1`;
- `RejectCodeV1`;
- bounded lengths/counts;
- explicit quantity type.

All authority-bearing 32-byte values use private fields and rejecting constructors. No `From<[u8; 32]>` bypasses validation; use `TryFrom`.

### Canonical codec

Implement a simple manual normative encoding before adding convenience formats:

```text
versioned header
fixed-width integers in one documented endianness
length-prefixed bounded byte strings
count-prefixed bounded lists
explicit enum tags
no implicit defaults
no map encoding in normative bytes
```

Diagnostic JSON is a separate wire type and never the semantic hash source.

### Evidence

- exact bytes and hashes for every primitive/object fixture;
- independent Python or second-Rust implementation of vectors;
- trailing, truncation, overflow, duplicate, unknown, noncanonical rejects;
- `cargo-fuzz` decoder target;
- Kani codec harnesses;
- endian-sensitive tests under Miri where applicable.

### Stop condition

WP1 may define the syntactic `ResourceWireV1` required to exercise the codec. It MUST NOT implement validated `ResourceV1`, state, persistence, application semantics, or proof adapters until the codec, reject precedence, and independent vector policy are frozen as draft v1.

---

## WP2 — Policy and authority model

### Crates

```text
zrm-policy
zrm-verifier-api
```

### Define

- `MachinePolicyV1`;
- `ResourceKindPolicyV1`;
- `ValidationContextV1` plus sealed `TrustedValidationContext` construction;
- verifier registry entries;
- policy-bound `LocalKernel` versus `RequiredVerifier` admission mode;
- logic profile and program authorization;
- controller/signature policy;
- unit/accounting policy;
- transformation policy;
- validity windows and expiry semantics;
- verifier revocation and resource-policy predecessor acceptance;
- byte/count/cycle/storage limits;
- one machine-wide verifier cost model for every summed verifier budget;
- DA and privacy profile references;
- stable policy hash.

### Authority capabilities

Define private-field types such as:

```rust
VerifiedLogicFact
VerifiedControllerFact
VerifiedTransformationFact
VerifiedDaFact
VerifiedExternalAttestationFact
```

Only the owning verifier API registry can construct them after dispatch through a sealed, governed backend wrapper. Applications and arbitrary downstream trait implementations cannot mint or register authority capabilities.

### Evidence

- a specification-derived executable policy oracle developed independently of
  the production Rust implementation;
- wrong program/key/profile/policy rejects;
- stale and revoked verifier rejects;
- capability forgery compile-fail/API tests;
- policy hash vectors;
- deterministic verifier-cost row, charge, overflow, and full-dispatch-plan vectors;
- invalid-artifact tests showing that failed verification does not alter the precomputed planned charge;
- external policy activation/stale-plan model, with no v0.1 claim of complete resource migration or rollback;
- no caller-provided verification booleans.

### Construction order and stop condition

1. Freeze and independently replay canonical verifier-cost-row bytes, sort and
   uniqueness rules, row hashes, rows root, and cost-model identity.
2. Load those rows into a sealed governed model that performs internal lookup;
   no public quote accepts caller coefficients or a caller row.
3. Freeze verifier-policy content commitments and registry membership,
   activation, revocation, production-mode, program/key/release, schema, and
   resource-bound semantics.
4. Resolve a requested identifier through authenticated governed state and
   construct sealed policy/fact capabilities only inside the registry boundary.
5. Differential-test both components against independently authored reference
   models and adversarial substitution matrices.

Until steps 1-4 have an accepted Class E authority ABI, canonical vectors, and
independent review, cost arithmetic and structural candidate comparisons remain
internal assurance helpers. They MUST NOT expose checked-quote or admission-like
success to external consumers, and WP3 cannot construct final `ResourceV1` from
them.

---

## WP3 — Resource and transition statement objects

### Define `ResourceV1`

Include only fields with stable semantic meaning:

- version;
- machine/domain;
- resource kind and logic program;
- label/value commitments;
- quantity and unit;
- controller and policy roots;
- provenance;
- nonce/salt commitment;
- validity range;
- flags with explicit semantics.

### Define transition roles

```text
consumed
referenced
created
```

Role assignment and ordinal are part of every proof-independent logic claim. A proof-bound logic statement combines the final transition statement hash with one exact logic claim hash.

### Define `TransitionStatementV1`

It binds:

- machine/domain/policy;
- pre-state roots and expected post-state roots;
- canonical consumed/reference/created roots and counts;
- logic claim root;
- transformation, authority, data-availability claim, and accounting-row roots;
- evidence/provenance/DA roots;
- exact counts for every resource and claim list;
- validity/epoch/version;
- all resource bounds.

Construction order is fixed: build and hash logic, transformation, authority, and data-availability claim descriptors, place their roots and counts in `TransitionStatementV1`, derive `StatementHash`, then form proof-bound child statements. A parent root MUST NOT include a child object that embeds the parent hash.

### Evidence

- every semantic field affects resource commitment;
- role collision rejects;
- duplicate resource IDs/commitments reject;
- statement one-field mutation tests;
- missing, duplicate, extra, and reordered authority/DA claim-artifact tests;
- field-disposition matrix;
- property corpus over role permutations.

---

## WP4 — Reference state and accumulators

### Crates

```text
zrm-state
zrm-reference
```

### Initial profile

Use a deliberately simple deterministic in-memory reference profile:

```text
active resources: BTreeMap<ResourceId, Resource>
nullifiers:       BTreeSet<Nullifier>
policy root
state version
```

For the v0.1 transparent profile, the nullifier set is also the committed historical-recreation check: a created `ResourceId` must be absent from both the active set and its deterministic transparent nullifier domain. A future shielded profile requires its own committed history mechanism.

The reference state root is a documented domain-separated commitment over sorted entries. This is not necessarily the production accumulator.

### Ports

Define membership/nonmembership proof interfaces without binding core semantics to one tree implementation.

### Evidence

- root vectors;
- insertion/removal/nullifier tests;
- output historical-recreation tests;
- same semantic state gives same root regardless of insertion order;
- Kani bounded accumulator harness;
- independent root replay.

---

## WP5 — Verifier adapters and authenticated facts

### First adapters

- deterministic local test verifier;
- Ed25519 or selected signature verifier;
- optional subprocess verifier shell with strict canonical output.

### Boundary

```text
ArtifactBytes
  -> BoundedArtifact
  -> CryptographicVerification
  -> ExactBindingChecks
  -> VerifiedFact
```

### Requirements

- bounded input/output/time;
- no shell interpolation;
- fixed executable and argument vector;
- pinned executable digest for authority profiles;
- exact canonical result schema;
- timeout/crash/missing executable fail closed;
- statement, role, ordinal, policy, and validity binding;
- exact committed claim descriptor, artifact-slot, and fact coverage for logic, transformation, authority, and DA classes;
- deterministic fact-class and within-class dispatch order;
- no secret in public diagnostics.

Verified-fact constructors remain inside the verifier API authority crate. Backends are reached only through a sealed, governed registry wrapper; applications cannot register arbitrary runtime callbacks or construct facts. Development/test verifier policies cannot satisfy a production profile.

Admission verification is a separate second-phase registry call. It accepts only a bounded artifact after finalization has produced the exact `JournalDraft`, verifies that draft under the plan's governed admission policy, enforces the precomputed admission-cost reservation, and returns `VerifiedAdmissionFact`. The original transition witness does not contain an admission artifact.

### Evidence

- wrong artifact/program/key/statement/policy/role/ordinal negatives;
- malformed and timeout tests;
- fuzz envelope;
- mutation of each binding check;
- verifier result vector.

---

## WP6 — Pure semantic kernel

### Crate

```text
zrm-kernel
```

### Public operations

```rust
prevalidate_transition(
    context: &TrustedValidationContext,
    pre_state_view: &impl StateView,
    envelope: CanonicalTransitionEnvelope,
    policy: &MachinePolicyV1,
) -> Result<PrevalidatedTransition, Reject>

VerifierRegistry::authenticate_transition(
    prevalidated: &PrevalidatedTransition,
) -> Result<AuthenticatedFacts, Reject>

finalize_transition(
    prevalidated: PrevalidatedTransition,
    facts: AuthenticatedFacts,
) -> Result<(CommitPlan, JournalDraft), Reject>

VerifierRegistry::verify_admission(
    plan: &CommitPlan,
    draft: &JournalDraft,
    artifact: &BoundedArtifact,
) -> Result<VerifiedAdmissionFact, Reject>
```

Prevalidation and finalization are pure and deterministic. Registry authentication is the explicit verifier boundary. Admission verification occurs only after finalization and only for `RequiredVerifier`. `PrevalidatedTransition` and `CommitPlan` fields are private and `#[must_use]`.

### Validation sequence

1. prevalidate trusted context, statement, policy, identities, counts, roles, membership, freshness, and resource-policy rules;
2. authenticate bounded artifacts against exact expected statements through the sealed registry;
3. require exact logic, controller, transformation, authority, and DA fact coverage;
4. derive accounting rows and enforce conservation/transformation rules;
5. compute removals, additions, nullifiers, and expected post-state roots;
6. compare every public expected root;
7. derive the canonical journal draft;
8. construct a private commit plan bound to that exact draft.

For `RequiredVerifier`, a later registry call bounds and authenticates the separately supplied admission artifact against that draft. The initial cost plan reserves its worst-case policy-bounded charge before step 2, and the later call cannot increase the planned total.

### Requirements

- no I/O, clock, RNG, environment, global state, threads, or async;
- no panic/unsafe/float;
- checked arithmetic only;
- stable reject precedence;
- bounded collections;
- no host-proposed accounting rows.

### Evidence

- invariant tests for every step;
- reject-is-no-op property;
- mutation suite;
- differential tests;
- Kani exact-once/accounting harnesses;
- initial Verus or Creusot contracts;
- bounded SMT/Lean statements.

---

## WP7 — Journals and conformance corpus

### Crate

```text
zrm-journal
zrm-conformance
```

### Accepted journal

Bind:

- statement and transition identity;
- pre/post state and nullifier roots;
- consumed/reference/created roots;
- accounting/transformation roots;
- verifier/logic/policy roots;
- evidence/provenance/DA roots;
- stable counts and version.

### Reject receipt

Bind only safe public information:

- request digest when a complete bounded request exists;
- parsed statement hash only after that stage succeeds;
- pre-machine-state root only when the statement hash is present;
- one stable `RejectCodeV1`, from which the reject stage is derived.

Never include private witnesses, keys, undisclosed resource values, or unbounded parser text.

### Corpus

- accepted vectors;
- every reject class;
- canonical bytes/hashes;
- cross-language replay;
- mutation fixtures;
- migration fixtures.

---

## WP8 — Formal assurance baseline

### Kani

- constructors;
- codecs;
- accounting;
- exact-once bounded state;
- reject no-op;
- overflow/panic freedom.

### Deductive Rust lane

Choose Verus or Creusot by RFC. Prove stable pure components first.

### Lean

Prove abstract:

- exact-once transition;
- conservation;
- disjoint commutativity;
- framing/injectivity assumptions;
- tree-independent semantic root.

### TLA+/SMT and bounded state-machine models

Model:

- concurrent commit;
- crash/recovery;
- policy rotation;
- proof-task lifecycle;
- duplicate reward.

### Refinement

Publish an explicit mapping between formal state/operations and Rust types/functions. Do not promote theorem scope until linkage exists.

---

## WP9 — Durable atomic runtime

### Crates/adapters

```text
zrm-store-api
zrm-store-sqlite-reference (or selected reference store)
zrm-runtime
```

### Commit API

```rust
commit(
    current_context: &TrustedValidationContext,
    plan: CommitPlan,
    admission: Option<VerifiedAdmissionFact>,
) -> Result<(CommittedTransition, AcceptedJournal), CommitError>
```

For `RequiredVerifier`, callers first submit the separately produced bounded admission artifact through `VerifierRegistry::verify_admission`. Commit accepts only the sealed fact returned for the plan's exact draft and reserved cost slot. `LocalKernel` accepts no admission fact.

### Atomic write set

- remove consumed resources;
- add created resources;
- add nullifiers, which supply transparent-profile historical output protection;
- verify a policy-required admission fact against the exact journal draft;
- atomically retype and write the draft as the accepted journal;
- create reward/effect records;
- write transactional outbox;
- advance state version/root.

The v0.1 runtime serializes commits through one atomic comparison of `(state_root, state_version, validation_context_hash)`. Parallel proof verification and validation are allowed; parallel durable commits require a later MVCC/sharded profile and proof of serializability.

### Evidence

- compare-and-swap races;
- epoch/order-context advance races with unchanged machine state;
- crash injection after every write;
- recovery idempotence;
- no split replay/effects;
- database corruption handling;
- backup/restore replay;
- Loom for in-process coordination;
- TLA+/state-machine model for persistent lifecycle.

---

## WP10 — Proof Resource Machine reference adapter

### Resource kinds

- proof task;
- reward escrow;
- prover capacity;
- bond;
- bid/commit/reveal if enabled;
- assignment;
- proof receipt;
- challenge;
- reward claim;
- residual budget/capacity.

### Transitions

- publish task;
- bid/assign;
- complete;
- timeout/reassign;
- challenge/slash;
- settle;
- cancel/refund under explicit policy.

### Required properties

- task and assignment exact once;
- reward conservation;
- no duplicate payment;
- late proof policy explicit;
- proof verifier fact binds exact task statement;
- challenge window and finality explicit;
- capacity cannot be double-reserved;
- bond/slash authority explicit.

### Evidence

BDD, property, mutation, SMT/TLA, and runtime replay corpus.

---

## WP11 — Second-domain adapter

Choose a materially different public reference domain by RFC, for example:

- bounded fungible-asset transfer;
- capability grant/revocation;
- evidence/challenge lifecycle;
- model checkpoint plus evaluation receipt;
- storage lease plus availability certificate.

Success criterion: no changes to core semantics are needed merely to encode domain vocabulary. If the core needs new semantics, demonstrate that they are general and version them.

---

## WP12 — Proof and recursive integration

### Proof leaf

A proof backend uses one explicitly selected mode:

- precommit admission authenticates the exact `JournalDraft` bound to a `CommitPlan`;
- postcommit aggregation authenticates an `AcceptedJournal` returned by durable commit.

The two wrappers have identical canonical payload bytes and distinct authority types.

### Semantic epoch root

Canonicalize the ordered transition/journal set independently of proof-tree grouping.

### Proof-tree root

Bind child proofs, programs, profiles, claims, journals, manifests, and topology.

### Requirements

- admission proof, when required by policy, is verified before commit and never implies that commit won;
- postcommit aggregation cannot retroactively authorize a transition;
- exact program/statement/journal/policy/release binding;
- child omission/substitution/duplicate negatives;
- semantic root remains tree-shape independent;
- DA certificate remains separate;
- proof generation and verification paths remain separate;
- local proof does not imply release authority or privacy.

---

## WP13 — Release rehearsal

### Required artifacts

- source archive;
- toolchain/dependency manifest;
- independent clean builds;
- bit-identical specified artifacts;
- SBOM/CBOM;
- all gate reports;
- formal builds;
- public conformance replay;
- signed manifest/provenance/VSA;
- security review disposition;
- claims and nonclaims;
- rollback/revocation plan.

### Promotion

No production claim while any critical conformance obligation is pending.

---

## Agent task sizing

Agents SHOULD receive one work-package slice with:

- no more than one authority boundary;
- explicit files/modules;
- named invariants/CBC IDs;
- failing tests or vector targets;
- required commands;
- non-goals.

Avoid prompts such as “implement ZRM.” Prefer:

```text
Implement canonical decoding for ResourceWireV1 under ZRM-CBC-001 and ZRM-CBC-019.
Do not implement state or proof adapters. Add exact vectors, trailing and
noncanonical rejects, a fuzz target, Kani bounds harness, and update the matrix.
```

## Global stop conditions

Stop and report rather than guessing when:

- the normative schema is ambiguous;
- a required authority source is unavailable;
- two specifications disagree;
- a tool returns `UNKNOWN`, timeout, or nondeterministic results;
- a dependency or license cannot be verified;
- a change would expose private repository context;
- a test appears wrong but the semantic intent is unclear;
- a canonical ABI change lacks version/migration approval;
- a critical invariant cannot be expressed or tested.
