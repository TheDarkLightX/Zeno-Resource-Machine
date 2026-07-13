# Authority ABI freeze packet

**Status:** decision-ready candidate; non-normative until the referenced RFCs and canonical byte tables are approved  
**Author:** Dana Edwards  
**Drafting assistance:** GPT-5.6  
**Date:** 2026-07-13  
**Change class if adopted:** E

## Purpose

ZRM has strong pre-authority components, semantic contracts, and assurance gates, but its authority-bearing composition is still intentionally absent. The remaining implementation cannot safely be divided among bounded implementation agents until the ownership and exact interfaces for state, policy, facts, finalization, commit, and journals are frozen.

This packet consolidates the required architectural decisions. It does not approve RFC-0001 or RFC-0002, freeze canonical bytes, promote conformance, or create production authority.

## Core decision

> Open extension points may transport bounded data or evidence. They may not mint ZRM authority.

A caller-implemented trait, callback, subprocess result, success boolean, deserialized object, copied identifier, or request-supplied coefficient must never construct any of the following:

- `TrustedValidationContextV1`;
- `GovernedPolicySnapshotV1`;
- `AuthenticatedStateSnapshotV1`;
- any `Verified*FactV1`;
- `AuthenticatedFactsV1`;
- `ValidatedTransitionV1`;
- `CommitPlanV1`;
- `CommittedTransitionV1`;
- `AcceptedJournalV1`.

Authority is created only by ZRM-owned, versioned, profile-specific verification code that rechecks exact canonical content and bindings.

## Why this must be frozen before broad implementation

The current logical policy and resource wrappers correctly distinguish local validation from authority. The missing path begins where external state, policy, verifier, or storage components could otherwise return success-shaped values. If an open downstream implementation can return a trusted type or a boolean that the kernel accepts, the type-state pipeline becomes forgeable even when every local function is well tested.

The safe composition is:

```text
open transport or storage port
  -> bounded canonical evidence
  -> ZRM-owned profile verifier
  -> opaque authenticated snapshot or fact
  -> pure semantic kernel
  -> opaque plan
  -> ZRM-owned release-selected commit implementation
  -> durable receipt
  -> accepted journal
```

## Proposed crate and authority ownership

| Component | Owns | May receive from open adapters | Must never trust directly |
| --- | --- | --- | --- |
| `zrm-codec` | canonical parsing and encoding | bounded bytes | deserialized authority types |
| `zrm-policy` | canonical logical policy values and local invariants | candidate policy bytes | activation, registry membership, trusted epoch |
| `zrm-state` | state-evidence schemas and profile verification | bounded snapshot or membership evidence | caller-provided membership booleans |
| `zrm-reference` | transparent reference accumulator/profile | bounded canonical state material | unordered maps or host iteration order |
| `zrm-verifier-api` | governed registry, dispatch plan, binding checks, sealed facts | bounded artifacts and canonical statements | backend success booleans, dynamic registration |
| `zrm-kernel` | type-state pipeline, coverage, accounting, finalization, plans | authenticated opaque types | raw bytes, policy candidates, caller effects |
| `zrm-journal` | draft and accepted journal schemas | opaque finalization and durable commit receipts | caller journal hashes or accepted flags |
| `zrm-store-api` | commit request and outcome algebra | opaque `CommitPlanV1` | reconstructed or caller-authored plans |
| release-selected runtime/store crates | durable head read and atomic commit | canonical plan bundle | a weaker fallback implementation |
| application adapters | domain policies and transition construction | public non-authority inputs and ZRM APIs | constructors for core capabilities |

The concrete crate names are candidates. The ownership direction is the requirement.

## Candidate type-state API

The signatures below freeze responsibilities, not final Rust syntax.

### 1. State evidence and authenticated snapshot

```rust
pub struct BoundedStateSnapshotEvidenceV1 {
    // private owned bytes plus explicit profile and byte/count ceilings
}

pub struct AuthenticatedStateSnapshotV1 {
    // private canonical state, roots, version, policy root, and profile
}

pub fn authenticate_reference_snapshot_v1(
    evidence: BoundedStateSnapshotEvidenceV1,
) -> Result<AuthenticatedStateSnapshotV1, StateAuthenticationErrorV1>;
```

Required properties:

1. `BoundedStateSnapshotEvidenceV1` is inert.
2. The reference authenticator recomputes the complete state root and every constituent root.
3. The authenticated snapshot is not deserializable and has no public constructor.
4. A public `StateView` trait implemented by arbitrary callers is not accepted as authority.
5. The pure kernel may read through a sealed read-only interface implemented only by authenticated snapshot types.
6. A self-consistent snapshot can produce only an inert plan; durable commit still compares the exact root, version, and validation-context hash with the current durable head.

### 2. Ordering context and validation context

```rust
pub struct AuthenticatedOrderingContextV1 {
    // private release-profile-specific ordering identity
}

pub struct TrustedValidationContextV1 {
    // RFC-0001 fields, all private, including validation_context_hash
}

pub fn derive_validation_context_v1(
    state: &AuthenticatedStateSnapshotV1,
    ordering: AuthenticatedOrderingContextV1,
) -> Result<TrustedValidationContextV1, ContextErrorV1>;
```

The context is derived from authenticated inputs. Request fields may echo the context but never select it. The validation-context hash binds:

- machine;
- domain;
- current epoch;
- expected machine-state root;
- expected state version;
- expected policy root;
- cryptographic suite;
- accumulator profile;
- ordering-context root.

Any change invalidates all uncommitted facts and plans.

### 3. Governed policy snapshot

```rust
pub struct BoundedPolicySnapshotEvidenceV1 {
    // canonical policy records and membership evidence
}

pub struct GovernedPolicySnapshotV1 {
    // private exact policy contents, dispositions, selections, registry, and cost model
}

pub fn resolve_governed_policy_snapshot_v1(
    context: &TrustedValidationContextV1,
    evidence: BoundedPolicySnapshotEvidenceV1,
) -> Result<GovernedPolicySnapshotV1, PolicyResolutionErrorV1>;
```

Resolution must recompute exact policy-content commitments and prove that the complete snapshot matches `context.expected_policy_root()`. Request-provided policy contents, release data, cost coefficients, or roots remain untrusted.

### 4. Final resources and transition statement

```rust
pub fn validate_resource_v1(
    context: &TrustedValidationContextV1,
    policies: &GovernedPolicySnapshotV1,
    role_bound: RoleBoundIntrinsicResourceV1,
) -> Result<ResourceV1, ResourceValidationErrorV1>;

pub fn build_transition_statement_v1(
    context: &TrustedValidationContextV1,
    resources: CanonicalResourceSetV1,
    claims: CanonicalClaimDescriptorsV1,
) -> Result<TransitionStatementV1, TransitionConstructionErrorV1>;
```

`ResourceV1` establishes policy validity only. It does not establish state membership, controller authority, logic validity, accounting, or commit success.

The transition statement commits every acceptance-relevant fact without a hash cycle. Claim descriptors are proof independent; proof artifacts never select the statement they are supposed to prove.

### 5. Governed verifier registry and sealed facts

No public dynamic backend registration is permitted in the authority path.

```rust
pub struct GovernedVerifierRegistryV1 {
    // private release-selected closed registry
}

pub struct DispatchPlanV1 {
    // private exact verifier slots and governed aggregate budget
}

pub fn plan_dispatch_v1(
    registry: &GovernedVerifierRegistryV1,
    context: &TrustedValidationContextV1,
    policies: &GovernedPolicySnapshotV1,
    statement: &TransitionStatementV1,
) -> Result<DispatchPlanV1, DispatchPlanErrorV1>;

pub fn authenticate_transition_v1(
    registry: &GovernedVerifierRegistryV1,
    plan: DispatchPlanV1,
    artifacts: BoundedArtifactSetV1,
) -> Result<AuthenticatedFactsV1, VerificationErrorV1>;
```

The registry must:

- resolve exact canonical policy contents from governed state;
- select an internally authenticated cost row;
- reserve the complete aggregate cost before expensive dispatch;
- call only release-selected verifier implementations;
- recheck program, key, proof mode, parameters, schema, statement, claim, context, policy snapshot, output, validity, and coverage;
- construct sealed facts only after cryptographic verification and binding checks;
- reject timeout, unsupported mode, missing verifier, revocation, stale context, and output ambiguity;
- provide no fallback to a local, development, structural, or weaker verifier.

An external process or service may return an artifact or signed receipt. Its exit status or boolean cannot itself mint a fact.

### 6. Pure kernel

```rust
pub fn prevalidate_transition_v1(
    context: &TrustedValidationContextV1,
    policies: &GovernedPolicySnapshotV1,
    state: &AuthenticatedStateSnapshotV1,
    envelope: CanonicalTransitionEnvelopeV1,
) -> Result<PrevalidatedTransitionV1, RejectV1>;

pub fn bind_authenticated_facts_v1(
    prevalidated: PrevalidatedTransitionV1,
    facts: AuthenticatedFactsV1,
) -> Result<FactBoundTransitionV1, RejectV1>;

pub fn finalize_transition_v1(
    transition: FactBoundTransitionV1,
) -> Result<(CommitPlanV1, JournalDraftV1), RejectV1>;
```

The kernel is pure, deterministic, bounded, and side-effect free. It derives:

- membership and freshness requirements;
- exact fact coverage;
- accounting rows;
- conservation and transformation decisions;
- semantic effects;
- post-state roots;
- journal draft;
- commit plan.

No function accepts a boolean authority parameter or caller-proposed accounting/effect row as authoritative.

### 7. Admission

When policy requires an admission verifier, admission binds the exact `JournalDraftHash` after finalization and before commit.

```rust
pub fn verify_admission_v1(
    registry: &GovernedVerifierRegistryV1,
    context: &TrustedValidationContextV1,
    policies: &GovernedPolicySnapshotV1,
    draft: &JournalDraftV1,
    artifact: BoundedArtifactV1,
) -> Result<VerifiedAdmissionFactV1, AdmissionErrorV1>;
```

A postcommit aggregation fact cannot substitute for admission. An admission fact does not prove commit.

### 8. Durable commit

```rust
pub enum CommitOutcomeV1 {
    Committed(CommittedTransitionV1),
    AlreadyCommitted(CommittedTransitionV1),
    ConflictConfirmedNoWrite(CommitConflictV1),
    Indeterminate(CommitIndeterminateV1),
}

pub fn commit_transition_v1(
    runtime: &mut ReleaseSelectedRuntimeV1,
    context: &TrustedValidationContextV1,
    plan: CommitPlanV1,
    draft: JournalDraftV1,
    admission: AdmissionAuthorizationV1,
) -> CommitOutcomeV1;
```

The linearization point atomically compares the complete expected head and writes the complete bundle. `AlreadyCommitted` is returned only when the durable replay record matches the exact transition ID, journal hash, semantic-effects root, and post-state identity. `ConflictConfirmedNoWrite` requires affirmative proof that no write from the attempted plan committed. Unknown storage outcomes remain `Indeterminate`.

The runtime is release selected. Production authority must not accept an arbitrary caller implementation of a `CommitPort` that can claim success without the required atomic semantics.

### 9. Accepted journal

```rust
pub fn accept_journal_v1(
    committed: CommittedTransitionV1,
) -> AcceptedJournalV1;
```

Only a durable commit receipt for the exact draft can produce `AcceptedJournalV1`. Neither a journal draft, verifier output, admission receipt, nor host boolean can construct it.

## Open interfaces that remain safe

Open interfaces are acceptable when their outputs remain untrusted until reverified:

- byte transport;
- artifact retrieval;
- snapshot material retrieval;
- telemetry sinks that cannot affect semantics;
- non-authority diagnostics;
- proof generation;
- application-level proposal construction.

Open interfaces are not acceptable when they can return:

- trusted context;
- authenticated state membership;
- active policy;
- verifier success;
- sealed fact;
- commit success;
- accepted journal.

## Canonical ABI freeze set

The following byte tables and domain strings must be approved before the corresponding bounded implementation tasks become delegable:

1. machine policy and resource-kind policy;
2. policy activation/disposition snapshot;
3. validation context;
4. transparent reference-state and constituent roots;
5. transition statement and claim descriptors;
6. verifier policy, release record, cost row, cost model, and registry snapshot;
7. verified-fact binding and authenticated output;
8. semantic effects;
9. journal draft;
10. transition replay record and commit metadata;
11. accepted journal;
12. recursive semantic summary and ordered manifest;
13. transition-level reject receipt.

Each freeze requires:

- manual field table;
- explicit widths and option encoding;
- domain separator;
- independent encoder;
- positive vectors;
- one-field mutation vectors;
- malformed, trailing, duplicate, unknown-critical, and substitution negatives;
- old/new compatibility and migration disposition.

## Required reject precedence families

The final error taxonomy must make the following precedence explicit:

1. unsupported schema/profile;
2. bounded-input and canonical decoding failure;
3. authenticated context and policy resolution failure;
4. structural role or claim-shape failure;
5. state membership, freshness, and replay failure;
6. verifier plan and cost failure;
7. cryptographic or binding failure;
8. semantic coverage, authority, accounting, and transformation failure;
9. finalization and admission failure;
10. commit conflict, corruption, or indeterminate outcome.

A later implementation may refine errors inside a family only after the public/private diagnostic boundary and cross-language parity are specified.

## Counterexamples that must be impossible

| Counterexample | Required prevention |
| --- | --- |
| Caller implements a trait that returns `true` for membership | kernel accepts only opaque authenticated state |
| Caller copies a policy ID onto altered contents | content commitment and governed membership are recomputed |
| Caller supplies a cheaper verifier cost row | registry selects the authenticated internal row |
| Development verifier runs under production policy | exact proof mode and release identity reject |
| Verifier returns success for wrong statement | registry rechecks exact statement and claim binding |
| Fact survives policy, state, epoch, ordering, or release change | exact validation-context and snapshot binding reject |
| Proposed accounting rows make an invalid transition balance | kernel derives rows from validated resources |
| Plan hides a reward, outbox, audit, or replay write | complete semantic-effects root and atomic bundle |
| Lost response causes effects to execute twice | exact replay record and idempotent `AlreadyCommitted` |
| Storage failure is reported as a clean conflict | separate confirmed-no-write and indeterminate outcomes |
| Journal draft is treated as committed | accepted type requires durable commit receipt |
| Recursive receipt authorizes a precommit transition | fact-class and lifecycle separation |
| Proof-tree regrouping changes economic identity | distinct canonical semantic ordering/root |

## Delegation threshold

Bounded implementation agents may receive authority-path tasks only after all of the following are true:

1. RFC-0001 and RFC-0002 are approved or superseded by accepted decisions.
2. The canonical ABI freeze set relevant to the task is approved.
3. Public opaque type ownership and constructor visibility are frozen.
4. The task names exactly one authority boundary.
5. Independent failing tests or vector targets exist before implementation.
6. An implementation-independent executable oracle is available.
7. Every semantic choice is resolved; no task asks the agent to choose behavior.
8. Counterexamples, non-goals, commands, and stop conditions are explicit.
9. Class C-E merge authority remains human, with required independent review.
10. Formal theorem statements and Rust-to-model refinement obligations are frozen for critical invariants.

Before that threshold, only evidence reconciliation, deterministic corpus expansion for already frozen behavior, and other non-authority tooling are safe for broad delegation.

## Required maintainer decisions

This packet recommends the following defaults:

1. Accept the closed-authority construction rule.
2. Prohibit public dynamic verifier registration in authority-bearing profiles.
3. Accept only opaque authenticated state views in the kernel.
4. Keep production commit implementations release selected rather than caller supplied.
5. Preserve RFC-0001's exact context invalidation and four-way commit outcome model.
6. Preserve RFC-0002's `AcceptedJournal`-only leaves and proof-tree-independent semantic identity.
7. Require a follow-up Class E canonical-byte RFC before authority implementation is promoted.
8. Treat unresolved ABI or oracle disagreements as blockers rather than implementation discretion.

## Non-claims

This packet:

- is not an accepted RFC;
- does not freeze canonical bytes or hashes;
- does not implement trusted context, governed policy, state, facts, kernel finalization, persistence, commit, journals, recursion, or a release;
- does not establish proof-system soundness, privacy, availability, consensus, physical truth, funds safety, external audit, or production readiness;
- does not replace independent semantic review, authority-boundary review, maintainer approval, or external security audit.
