# RFC-0001: Policy, Context, Fact Freshness, and Commit Authority

**Status:** Draft
**Author:** Dana Edwards

**Drafting assistance:** GPT-5.6
**Reviewers:** Independent semantic reviewer TBD; authority-boundary reviewer TBD
**Created:** 2026-07-12
**Target version:** ZRM 0.2 draft
**Change class:** E

## Summary

This RFC closes the semantic gap between a structurally valid resource
transition and an authority-bearing durable commit. It defines:

- enabled, suspended, predecessor, and hard-revoked resource-policy behavior;
- the exact snapshot carried by `TrustedValidationContextV1`;
- the lifetime and substitution rules for sealed verifier facts;
- the fields and effects bound by a private `CommitPlan`;
- policy-selected admission over the exact `JournalDraft`;
- linearizable atomic commit, crash recovery, indeterminate outcomes, and
  idempotent retry semantics;
- the distinction between precommit admission leaves and postcommit recursive
  aggregation leaves.

The central rule is:

```text
No policy, fact, plan, proof, or journal may outlive the exact authenticated
context that gave it meaning, except an already durable transition record that
is returned idempotently without reapplying effects.
```

This RFC defines logical semantics and authority boundaries. It does not freeze
new canonical bytes or domain-separated hashes. Any new authority codec or hash
identity requires a follow-up Class E byte-table change with independent
vectors.

## Motivation

ZRM already separates untrusted bytes, intrinsic resources, structural roles,
policies, verified facts, semantic validation, commit planning, and durable
commit. The remaining open questions are compositional:

1. Can resources created under an old policy still be consumed or referenced?
2. What exactly does hard revocation invalidate?
3. Does a verified fact survive a policy, verifier-release, epoch, or ordering
   change?
4. Which snapshot components make a `CommitPlan` stale?
5. What prevents a plan from carrying hidden storage, reward, or outbox effects
   that are absent from its journal?
6. What is the linearization point of exact-once commit?
7. What should a caller receive after the commit succeeds but the response is
   lost?
8. Can an admission proof be substituted with a postcommit recursive receipt,
   or vice versa?

Without one answer to these questions, individually correct components can be
composed into an unsafe authority path.

## Goals

- Make policy rotation usable without authorizing creation under predecessor
  policies.
- Permit emergency creation suspension without requiring an unreviewed
  replacement policy.
- Preserve hard-revocation containment without silently claiming recovery or
  liveness for stranded resources.
- Make every uncommitted authority capability snapshot-bound and fail closed on
  policy, state, epoch, ordering, or release changes.
- Give semantic effects and commit metadata an explicit acyclic derivation.
- Define one linearizable commit boundary and unambiguous lost-ack recovery.
- Keep admission and postcommit recursive aggregation semantically distinct.
- Provide bounded state-machine obligations, counterexamples, and parameterized
  proof obligations for implementation.

## Non-goals

- Canonical byte tables or final hash domains for the new logical objects.
- A complete policy migration or emergency recovery protocol.
- Shielded-resource revocation or privacy-preserving nullifiers.
- Consensus, ordering, finality, or cross-machine atomicity.
- Exact-once delivery to external systems.
- Proof-system soundness or verifier-binary correctness.
- Permissionless dynamic verifier registration.

## Current behavior

The current draft specification distinguishes:

- a current creation policy from accepted predecessor resource policies;
- a sealed trusted validation context from proposer-selected time or policy;
- precommit facts, second-phase admission facts, and postcommit aggregation
  facts;
- pure finalization from atomic durable commit;
- a `JournalDraft` from an `AcceptedJournal`.

The repository does not yet implement authenticated policy activation, final
policy-valid resources, governed verifier dispatch, complete semantic
finalization, or durable commit. The current journal schema also does not carry
one explicit root over every storage, reward, replay, audit, and outbox effect.

## Proposed semantics

### 1. Resource-policy disposition and creation selection

For one active machine-policy snapshot, every recognized resource-kind policy
ID has exactly one disposition:

```text
PolicyDispositionV1 =
    CurrentCreation
  | AcceptedPredecessor
  | HardRevoked
```

Creation availability is represented separately for each resource kind:

```text
CreationSelectionV1 =
    Enabled(CurrentPolicyId)
  | Suspended
```

This separation makes an emergency creation stop representable without
granting authority to a replacement policy that has not completed governance
review. Absence from the authenticated policy snapshot is unsupported and
fails closed. No implicit default or wildcard disposition exists.

The following construction invariants hold:

- `Enabled(policy_id)` requires exactly that policy to have disposition
  `CurrentCreation`; every other recognized policy for the kind is
  `AcceptedPredecessor` or `HardRevoked`.
- `Suspended` requires no policy for the kind to have disposition
  `CurrentCreation`.
- `CurrentCreation`, `AcceptedPredecessor`, and `HardRevoked` are pairwise
  exclusive for one policy identity.
- A policy selected for a resource kind must canonically bind that same kind.

#### 1.1 Enabled creation

A created resource is valid only when creation is `Enabled` and the resource
uses the exact selected current policy. Equality of resource kind, program,
unit, or other contents is insufficient: the selected policy identity must
match exactly.

When creation is `Suspended`, every ordinary creation attempt for that resource
kind rejects. Suspension grants no mint, migration, transformation, recovery,
or verifier-fallback authority.

#### 1.2 Accepted predecessor policy

An `AcceptedPredecessor` policy may validate an already existing resource for
consumption or reference. It MUST NOT authorize:

- creation of a new resource;
- mint, burn, reward, or transformation authority merely because the policy is
  accepted as a predecessor;
- creation under a copied or content-similar policy ID;
- verifier-policy fallback.

Predecessor acceptance is explicit per authenticated machine-policy snapshot.
It does not persist automatically across a later snapshot.

#### 1.3 Hard revocation

`HardRevoked` blocks all normal creation, reference, consumption, logic,
transformation, authority, and data-availability validation under that policy
from the effective policy snapshot onward.

Hard revocation may strand live resources. This is intentional for emergency
containment. ZRM makes no automatic recoverability or liveness claim for such
resources. A recovery or migration path requires a separately versioned,
governance-authorized rule that names the affected policy and exact resources
or state commitment.

Governance may hard-revoke the selected creation policy only by atomically doing
one of the following in the same update:

1. selecting an independently authorized, non-revoked replacement; or
2. setting the resource kind's creation selection to `Suspended`.

An ordinary suspension may reclassify the previously current policy as an
accepted predecessor when governance intends existing resources to remain
usable. Hard revocation instead classifies it as `HardRevoked` and blocks its
normal use.

### 2. Policy activation and rollback

Policy activation is a runtime governance operation outside ordinary
`TransitionStatementV1`.

A successful policy update atomically derives and persists:

```text
new_policy_root
new_state_version = old_state_version + 1
new_machine_state_root
new_validation_context_hash
governance_replay_record
governance_audit_record
```

The new machine-state root is recomputed from the unchanged or separately
governed accumulator roots plus the new policy root and version. The governance
statement binds the exact action, old and new roots, machine, domain, nonce,
validity window, and governing authority. Failure persists none of these
writes. Machine and domain identity are preserved.

Every policy update increments the monotonically increasing state version. A
rollback is represented as a new governance update and new state version. It
MUST NOT restore an earlier `(machine_state_root, policy_root, state_version,
validation_context_hash)` tuple or otherwise create an ABA-equivalent snapshot.

### 3. Trusted validation context

The runtime constructs one sealed capability from authenticated state and
ordering authority:

```text
TrustedValidationContextV1 {
  machine_id
  domain_id
  current_epoch
  expected_machine_state_root
  expected_state_version
  expected_policy_root
  expected_crypto_suite_id
  expected_accumulator_profile_id
  ordering_context_root
  validation_context_hash
}
```

`validation_context_hash` is derived from every preceding field under the
versioned validation-context schema.

The capability:

- has private fields and construction;
- is not deserializable;
- is not caller-created;
- is supplied explicitly to prevalidation and commit;
- is the sole semantic source of epoch, policy, pre-state, and ordering
  freshness.

The statement must echo and match the context. Echoed fields never select the
context.

### 4. Policy snapshot

A `GovernedPolicySnapshotV1` is resolved from
`TrustedValidationContextV1.expected_policy_root`. It supplies:

```text
GovernedPolicySnapshotV1 {
  machine_policy
  resource_kind_policy_dispositions
  creation_selection_by_kind
  governed_verifier_policies
  verifier_release_registry
  verifier_cost_model
  transformation_and_authority_policies
  data_availability_policies
  snapshot_hash
}
```

The request may name IDs. It never supplies authoritative policy contents,
registry membership, release identity, or cost coefficients.

### 5. Sealed fact freshness

Every authority-bearing verifier fact records, through private fields:

```text
VerifiedFactBindingV1 {
  fact_class
  parent_binding_hash
  exact_claim_hash
  exact_child_statement_hash
  policy_snapshot_hash
  validation_context_hash
  verifier_policy_id
  verifier_release_id
  program_or_key_digest
  authenticated_output_root
  validity_end_epoch
}
```

`fact_class` is closed and includes at least:

```text
Logic
Transformation
Authority
DataAvailability
Admission
PostcommitAggregation
Anchor
```

Only the owning governed registry can construct the corresponding sealed fact
type.

A precommit fact is usable only when:

- its policy and context hashes exactly equal the prevalidated transition;
- its verifier policy and release remain selected by that snapshot;
- its exact claim, child statement, parent `StatementHash`, and output match;
- its fact class matches the required slot;
- the trusted current epoch is within its validity window.

No semantic-content comparison may allow a fact to survive a context-hash
change. A policy update, verifier-release rotation, epoch advance, ordering
advance, or pre-state change therefore invalidates every uncommitted fact and
plan from the old context.

This conservative rule deliberately rejects potentially reusable work rather
than implementing semantic equivalence between policy snapshots.

### 6. Fact lifecycle separation

The lifecycle classes are not substitutable:

- logic, transformation, authority, and DA facts bind the final
  `StatementHash` plus one exact claim;
- an admission fact binds the exact `JournalDraftHash` after finalization;
- a postcommit aggregation or anchor fact binds an `AcceptedJournal` and its
  ordered manifest after durable commit.

A postcommit receipt cannot authorize admission. An admission receipt does not
prove that the draft committed.

### 7. Acyclic semantic effects and commit metadata

Finalization first produces the journal-bindable semantic state delta:

```text
SemanticEffectsV1 {
  active_resource_deletes_root
  active_resource_delete_count
  active_resource_inserts_root
  active_resource_insert_count
  nullifier_inserts_root
  nullifier_insert_count
  reward_and_escrow_effects_root
  reward_and_escrow_effect_count
  outbox_records_root
  outbox_record_count
  semantic_audit_entries_root
  semantic_audit_entry_count
  total_semantic_write_bytes
}

SemanticEffectsRoot = H_semantic_effects_v1(
  canonical SemanticEffectsV1 bytes
)
```

Every field is kernel-derived. A proposed list, root, count, or byte total is
non-authoritative and must match recomputation if accepted as an optimization.
The semantic audit entries are pre-journal facts; they cannot contain a journal
hash, replay-record hash, bundle hash, or any value derived from themselves.

The next journal schema commits `SemanticEffectsRoot`, every relevant count,
and the pre/post state identities. The remaining durable metadata is derived
only after `JournalHash` exists:

```text
TransitionReplayRecordV1 {
  machine_id
  domain_id
  transition_id
  journal_hash
  semantic_effects_root
  post_machine_state_root
  post_state_version
}

CommitMetadataV1 {
  transition_replay_record
  accepted_journal_key_and_hash
  machine_state_head_update
  admission_receipt_reference
  commit_audit_record
}

AtomicCommitBundleV1 {
  semantic_effects
  commit_metadata
  total_storage_write_bytes
}
```

The dependency order is normative:

```text
SemanticEffectsV1
  -> SemanticEffectsRoot
  -> JournalPayloadV2
  -> JournalHash
  -> TransitionReplayRecordV1 and remaining CommitMetadataV1
  -> AtomicCommitBundleV1
```

No hash preimage may contain itself directly or transitively. In particular,
`SemanticEffectsRoot` excludes the replay record, accepted-journal row,
state-head row, admission receipt reference, and final commit-audit envelope.
Those records are deterministically bound by the plan and atomic bundle after
the journal hash exists. A profile may compute a postcommit audit hash over the
complete bundle, but that hash is not embedded into the bundle it hashes.

Every authority-bearing storage write belongs to exactly one field of
`AtomicCommitBundleV1`. The journal completely binds the semantic state delta;
atomic commit binds the derived metadata. Documentation MUST NOT claim that the
journal recursively commits its own storage record or the complete physical
database write representation.

Until the new logical objects receive canonical byte tables and independent
vectors, ZRM cannot claim complete journal-to-effect or bundle identity.

### 8. Commit plan

The semantic kernel privately constructs:

```text
CommitPlanV1 {
  transition_id
  expected_pre_machine_state_root
  expected_state_version
  expected_validation_context_hash
  expected_policy_snapshot_hash
  computed_post_machine_state_root
  semantic_effects
  semantic_effects_root
  journal_draft
  journal_draft_hash
  retry_descriptor
  admission_mode
  expected_admission_verifier_policy_id
  planned_verifier_cost_units
  admission_reserved_cost_units
}
```

The plan:

- has private fields and no deserialization path;
- is non-cloneable unless a reviewed implementation proves cloning cannot
  duplicate commit authority;
- contains no callbacks, database handles, network handles, or hidden effects;
- is valid only for its exact expected snapshot;
- is safe to attempt exactly because all semantic validation completed before
  construction.

Before the plan is consumed, the runtime may expose this inert retry value:

```text
RetryDescriptorV1 {
  machine_id
  domain_id
  transition_id
  journal_hash
  semantic_effects_root
}
```

For the selected journal schema, `journal_hash` is the hash of the same payload
carried by `JournalDraft`. `RetryDescriptorV1` is bounded serializable data. It
does not authorize validation, admission, state mutation, journal acceptance,
or recreation of a `CommitPlan`. Its sole authority-safe use is exact lookup and
comparison against the durable replay table.

### 9. Admission

`LocalKernel` requires no admission fact and rejects an unexpected one.

`RequiredVerifier` requires exactly one `VerifiedAdmissionFact` that binds:

- `journal_draft_hash`;
- `validation_context_hash`;
- policy snapshot;
- exact admission verifier policy, program/key, profile, and release;
- actual admission charge no greater than the plan reservation.

Admission verification occurs after the draft exists and before the atomic
commit attempt. It does not refresh or mutate the plan.

### 10. Atomic commit algorithm

The runtime commit operation has explicit success and failure classes:

```text
CommitSuccessV1 =
    NewlyCommitted(AcceptedJournal)
  | AlreadyCommitted(AcceptedJournal)

CommitAttemptFailureV1 =
    RejectedConfirmedNoWrite(CommitRejectV1)
  | OutcomeUnknown(RetryDescriptorV1)
```

`AlreadyCommitted` is an idempotent success, not a second state transition.
`RejectedConfirmedNoWrite` asserts that the storage profile established that no
write became durable. `OutcomeUnknown` makes no pre-state or post-state claim;
the caller must resolve the retry descriptor.

The logical algorithm is:

```text
1. Validate CommitPlan capability provenance and bound input framing; defer
   policy admission classification until after replay classification.
2. Begin one serializable storage transaction or equivalent linearizable
   critical section.
3. Inside that boundary, look up transition_id in the durable replay table.
4. If a record exists:
     a. if its journal hash, semantic-effects root, and transition identity
        equal the plan, return AlreadyCommitted(existing AcceptedJournal);
     b. otherwise reject TransitionReplayConflict.
5. If no record exists, compare the current tuple:
     (machine_state_root, state_version, validation_context_hash)
   with the plan's expected tuple.
6. Recheck policy-selected admission against the exact plan and draft.
7. Construct and byte-bound the complete AtomicCommitBundleV1.
8. Apply every bundle entry and no other authority-bearing write.
9. Atomically persist the replay record, accepted journal, state-head update,
   admission reference, and commit audit record with the semantic effects.
10. Reach the storage profile's durability point.
11. Retype JournalDraft as AcceptedJournal and return NewlyCommitted.
```

The replay read and replay insertion MUST participate in one serializable
conflict domain. A uniqueness, serialization, or compare-and-swap conflict
caused by another attempt requires a fresh in-boundary replay lookup before the
runtime classifies the result. An exact winner becomes `AlreadyCommitted`; a
different winner under the same transition ID becomes
`TransitionReplayConflict`. The runtime cannot return `StaleState` merely
because an earlier out-of-boundary replay read missed the winning record.

If the storage adapter proves that steps 2 through 10 aborted without a durable
write, it returns `RejectedConfirmedNoWrite`. If an I/O error, crash boundary,
remote acknowledgement loss, or storage contract leaves durability
indeterminate, it returns `OutcomeUnknown` with the precomputed descriptor.
It MUST NOT map an indeterminate result to a rejection.

The transition-record comparison in step 4 permits safe retry after a lost
acknowledgement. It does not revalidate or reapply the old transition. A
privacy-sensitive profile may suppress or authenticate the returned journal,
but it must preserve the same no-reapplication semantics.

### 10.1 Read-only retry resolution

A caller that no longer owns the consumed `CommitPlan` resolves an uncertain
result through a separate read-only operation:

```text
resolve_retry(RetryDescriptorV1) ->
    AlreadyCommitted(AcceptedJournal)
  | TransitionReplayConflict
  | NotFoundAtObservedSnapshot
```

The lookup uses one consistent committed snapshot. `NotFoundAtObservedSnapshot`
is a point-in-time observation, not proof that the attempt never committed or
that a concurrent attempt will not commit. The operation applies no effects and
cannot turn the descriptor into commit authority. Access to the result or
journal may be authenticated or redacted by a privacy profile.

### 11. Error precedence at commit

For a commit attempt, precedence is:

1. invalid or foreign `CommitPlan` capability;
2. inside-boundary existing transition record:
   - exact match -> `AlreadyCommitted` success;
   - mismatch -> `TransitionReplayConflict`;
3. stale state root/version;
4. stale validation context;
5. admission required, unexpected, or mismatched;
6. bundle bound or storage-write bound exceeded;
7. confirmed atomic abort with no durable write;
8. outcome unknown;
9. fail-closed internal error before any possible durable write.

Replay classification occurs before stale-plan rejection within the same
linearizable boundary only to recover or conflict with an already committed
result. It never authorizes a new write under a stale context. Once durability
may be indeterminate, `OutcomeUnknown` is a result class rather than a reject
code and takes precedence over any claim that rejection was a no-op.

### 12. Crash consistency

A conforming storage profile defines a durability point and recovery protocol.
For every injected crash boundary:

```text
recover(crash(commit(plan, pre_state)))
  in { complete_pre_state, complete_post_state }
```

The following states are forbidden:

- nullifier without value or authority effect;
- value or reward effect without nullifier/replay record;
- accepted journal without its effects;
- effects without accepted journal;
- outbox record detached from transition identity;
- acknowledged success before durable post-state.

Loss of the response after durability is resolved by `AlreadyCommitted` on
read-only retry resolution. A crash or error before the caller can know whether
the durability point was crossed returns or reconstructs `OutcomeUnknown`; only
recovery or retry resolution may classify the durable result.

### 13. External effects

External delivery is outside ZRM's atomic state boundary. ZRM may atomically
persist an outbox record derived from the transition ID. Delivery is
at-least-once unless the receiver supplies an idempotency contract. ZRM MUST NOT
claim exact-once external delivery merely because outbox persistence is atomic.

### 14. Recursive composition integration

Recursive proof profiles distinguish:

```text
AdmissionLeafV1:
  binds JournalDraftHash before commit

PostcommitLeafV1:
  binds AcceptedJournal payload/hash after commit
```

The wrapper mode, policy, program/key, release, and ordered child manifest are
proof identity. The ordered semantic journals, transition identities, state
chain, accounting, and effects determine semantic identity.

An aggregate or anchor fact over `AcceptedJournal` cannot retroactively satisfy
admission. An admission leaf cannot claim the draft became durable.

## Typed interfaces

Conceptual interfaces:

```rust
pub enum PolicyDispositionV1 {
    CurrentCreation,
    AcceptedPredecessor,
    HardRevoked,
}

pub enum CreationSelectionV1 {
    Enabled(PolicyId),
    Suspended,
}

pub fn validate_resource_for_role(
    resource: IntrinsicResourceV1,
    role: ResourceRoleV1,
    context: &TrustedValidationContextV1,
    snapshot: &GovernedPolicySnapshotV1,
) -> Result<PolicyValidResourceV1, ResourcePolicyReject>;

pub fn finalize_transition(
    prevalidated: PrevalidatedTransition,
    facts: AuthenticatedFacts,
) -> Result<(CommitPlan, JournalDraft), FinalizeReject>;

pub fn verify_admission(
    registry: &GovernedVerifierRegistry,
    plan: &CommitPlan,
    draft: &JournalDraft,
    artifact: BoundedArtifact,
) -> Result<VerifiedAdmissionFact, AdmissionReject>;

pub fn commit(
    runtime: &mut impl AtomicCommitPort,
    plan: CommitPlan,
    admission: AdmissionInput,
) -> Result<CommitSuccessV1, CommitAttemptFailureV1>;

pub fn resolve_retry(
    runtime: &impl CommitStatusView,
    descriptor: &RetryDescriptorV1,
) -> Result<RetryResolutionV1, RetryLookupError>;
```

## Authority and trust boundary

- **Untrusted inputs:** transition bytes, resource bodies, policy IDs, proof and
  signature artifacts, remote verifier responses, proposed accounting and
  effect rows, retry requests.
- **Authenticated facts:** sealed facts produced by the governed verifier
  registry under the exact context and policy snapshot.
- **Governing policy:** authenticated snapshot selected by the runtime-owned
  policy root.
- **Commit authority:** one private plan plus policy-correct admission, applied
  by an atomic runtime against the exact snapshot tuple.
- **Revocation/rotation:** atomic policy-root, machine-state-root, state-version,
  context, governance-replay, and audit update; every old uncommitted capability
  becomes stale.
- **Trusted computing base:** hash and proof assumptions, governed policy root,
  verifier binaries/releases, compiler/toolchain, and storage atomicity and
  durability mechanism.

## Canonical encoding and hashing

This RFC defines logical fields only.

Before implementation of new authority identities:

- exact byte tables must be added for `PolicyDispositionV1`,
  `CreationSelectionV1`, `SemanticEffectsV1`, `RetryDescriptorV1`, the revised
  journal, replay record, and any plan-binding descriptor;
- domains must be unique and versioned;
- independent vectors must cover empty and nonempty forms;
- all list roots must be sorted, unique, count-framed, and domain-separated;
- unknown variants, duplicates, malformed options, and trailing bytes reject;
- migration and cross-version replay behavior must be specified.

`CommitPlan` itself remains non-serializable. A canonical descriptor may be
hashed for binding and evidence, but serialized bytes do not recreate the
capability.

## Accounting and resource effects

- Created resources require `CreationSelectionV1::Enabled` and use its exact
  current creation policy. Suspended creation rejects.
- Consumed and referenced resources use the current or an explicitly accepted
  predecessor policy.
- Hard-revoked policies authorize no normal role.
- Accounting rows are kernel-derived.
- Every nonconserved delta has exactly one allowed transformation or authority
  fact.
- Reward, escrow, mint, burn, slash, and outbox effects appear in the explicit
  semantic effect set and journal commitment. Replay, accepted-journal,
  admission-reference, state-head, and commit-audit metadata appear in the
  atomic bundle after the journal hash is derived.

## State, concurrency, and atomicity

The first durable profile remains globally serialized by one machine-state root
and monotonically increasing state version. Pure validation and proof
verification may run concurrently. Only one plan built on a given tuple can
win, except an exact retry of the already committed transition, which returns
the prior result without writing.

A later sharded profile requires a new profile ID, key-range or shard versions,
serializability proof, root-composition rules, and replay analysis.

## Privacy and disclosure

The initial profile is transparent. Transition IDs, policy generations,
nullifiers, timing, and journal availability may be linkable.

Idempotent retry may disclose whether a transition is already committed. A
privacy profile may require caller authentication or suppress journal payloads,
but it must not reapply effects or misreport an uncommitted transition as
accepted.

Default diagnostics redact full nonces, private witnesses, backend internals,
and sensitive opaque identifiers beyond the active disclosure profile.

## Data availability and external attestations

A data commitment is not availability. When policy requires availability, the
precommit transition consumes an exact sealed DA fact. Hard policy or context
changes stale that fact like every other precommit fact.

An authenticated external attestation proves only that the governed issuer made
the attestation. It does not prove the physical-world proposition independently
true.

## Resource and performance bounds

- All policy maps, resource lists, claim lists, effects, outbox records, and
  audit records are bounded before allocation.
- Both `SemanticEffectsV1.total_semantic_write_bytes` and
  `AtomicCommitBundleV1.total_storage_write_bytes` must not exceed their
  machine-policy and protocol ceilings.
- Verifier costs are fully planned before transition-fact dispatch, including
  admission reservation.
- Replay lookup and exact-match comparison are bounded by fixed-size identities
  and journal/effects hashes.
- No unbounded recursion or graph traversal enters the semantic or commit path.

## Security analysis

| Disaster state | Defense | Residual risk | Evidence |
| --- | --- | --- | --- |
| Creation under predecessor policy | Exact enabled-policy lookup | Policy-map implementation bug | lifecycle model; negative mutant |
| Current policy cannot be stopped safely | Explicit `Suspended` creation state | Governance misuse | suspension model; decision table |
| Old resource unusable after ordinary rotation | Explicit predecessor acceptance | Governance may omit predecessor | Policy update review and live-resource analysis |
| Compromised policy remains usable | Hard revocation plus context invalidation | Live resources may be stranded | lifecycle model; explicit non-claim |
| Old fact survives policy/release/epoch change | Exact context and snapshot hashes | Incorrect runtime context construction | fact model; registry negatives |
| Fact-class substitution | Closed sealed types and class binding | Adapter implementation defect | fact model; compile-fail tests |
| Stale plan commits | CAS over root/version/context | Storage adapter violates atomicity | plan model; Loom/crash model |
| Replay read races with a winner | Lookup and insert share one serializable boundary | Isolation-level mismatch | two-attempt replay model; schedule tests |
| Self-referential commit identity | Normative acyclic derivation order | Codec or projection defect | dependency-cycle check and vectors |
| Hidden durable effect | Complete atomic bundle with disjoint semantic/metadata layers | Storage adapter adds writes | Differential bundle derivation and mutation tests |
| Double application after lost ack | Exact replay-record lookup returns prior result | Replay table corruption | exact-once model; persistent recovery tests |
| Uncertain durability reported as rejection | `OutcomeUnknown` plus retry descriptor | Adapter misclassifies I/O errors | recovery model; crash injection |
| Partial commit after crash | One atomic write set and durability protocol | Database/OS/storage assumptions | recovery model; crash injection |
| Admission/postcommit confusion | Distinct lifecycle types and profiles | Misregistered backend | Registry substitution negatives |
| External duplicate delivery | Atomic outbox plus receiver idempotency | Receiver lacks idempotency | Explicit at-least-once non-claim |

## Alternatives considered

### Current policy only for every resource role

Rejected. Ordinary policy rotation would immediately strand all resources
created under the predecessor.

### Allow predecessor creation

Rejected. It permits indefinite downgrade and makes selecting a current
creation policy ineffective.

### Require an immediate replacement before revoking the current policy

Rejected. It can force governance to keep a compromised policy active or rush
an unreviewed replacement. Explicit creation suspension preserves containment
without granting replacement authority.

### Let facts survive policy changes when contents appear equivalent

Rejected for the first profile. It creates a second semantic-equivalence system
for policy snapshots and introduces ABA, revocation, and release-binding risk.
Reverification under the new context is simpler and fail closed.

### Reject every replay, including retry after lost acknowledgement

Rejected. It leaves callers unable to distinguish committed-with-lost-response
from rejected-with-no-effect. Exact matching against the durable replay record
provides idempotent recovery without another state transition.

### Return idempotent success for any matching transition ID

Rejected. The durable journal hash and semantic-effects root must also match.
An ID with different contents is a replay conflict.

### Read replay state before entering the transaction

Rejected. Two attempts may both observe absence before one wins, causing the
loser to escape exact replay classification. Lookup, comparison, and insertion
share one serializable conflict boundary.

### Serialize or clone the commit plan for retry

Rejected. It would widen commit authority and make capability replay possible.
The serializable retry descriptor is read-only data and cannot authorize a new
write.

### Embed replay and journal storage rows in the semantic-effects root

Rejected. A replay record binds the journal and semantic-effects roots, so
including it in either preimage creates a circular dependency. Commit metadata
is derived after the journal hash and applied in the same atomic bundle.

### Keep rewards and outbox writes outside the journal commitment

Rejected. Uncommitted or hidden side effects would escape semantic review and
recursive proof binding.

### Automatically migrate resources on hard revocation

Deferred. Automatic migration is itself an authority-bearing transformation and
requires a separate rule, accounting semantics, and recovery threat model.

## Compatibility and migration

- Existing `ResourceWireV1` bytes are unchanged by this RFC.
- Existing pre-alpha policy structs remain non-authoritative until canonical
  policy schemas and authenticated snapshots are implemented.
- Adding `semantic_effects_root` requires a new journal schema version rather
  than reinterpretation of existing journal bytes.
- Old and new journal versions cannot substitute in admission or recursive
  profiles.
- Policy rollback is a new versioned governance update, never state-version
  decrement or tuple reuse.
- Outstanding plans and facts from a prior context are intentionally invalid.

## Test and assurance plan

### Bounded state-machine models

The semantic closure package includes:

- `zrm_plan_freshness_v1`;
- `zrm_exact_once_v1`;
- `zrm_verifier_fact_freshness_v1`;
- `zrm_atomic_commit_recovery_v1`;
- `zrm_policy_creation_suspension_v1`;
- `zrm_replay_linearization_v1`;
- `zrm_commit_outcome_resolution_v1`.

Each model must be canonical and 1-inductive under the configured fail-closed
checker. Targeted mutants must produce semantic counterexamples for
wrong-policy creation, missing suspension, stale-plan commit, replay lookup
outside the linearization boundary, duplicate retry effect, incorrect unknown
outcome resolution, Development-mode fact minting, and partial durable commit.

### Implementation evidence

- accepted, boundary, and negative unit tests;
- stateful property testing against a deliberately simple reference machine;
- mutation tests for every authority guard;
- fuzzing of bounded envelopes and operation sequences;
- Kani harnesses for exact-once and effect-set properties;
- Loom exploration for plan/commit and replay races;
- deterministic crash injection before and after every persistence boundary;
- differential storage-adapter tests against the reference runtime;
- Lean or equivalent parameterized theorems for set disjointness, exact-once
  state update, and associative semantic journal folding;
- independent semantic and authority-boundary review.

## Formal obligations

At minimum, formal work should state:

```text
PredecessorNonCreation
SuspendedCreationRejects
CurrentPolicyCanRevokeIntoSuspension
HardRevocationExcludesNormalUse
FactUseImpliesExactCurrentContext
FactClassNonSubstitution
CommitSuccessImpliesCompleteEffects
RejectImpliesStateUnchanged
ConflictingPlansHaveAtMostOneNewCommit
ExactRetryDoesNotChangeState
ReplayClassificationLinearizable
ConflictingReplayAlwaysConflicts
OutcomeUnknownMakesNoStateClaim
RetryResolutionAppliesNoEffects
CommitIdentityDependencyGraphAcyclic
CrashRecoveryIsPreOrPost
AcceptedJournalImpliesDurableCommit
```

Bounded state-machine analysis establishes finite instances only. Parameterized
proofs and Rust refinement evidence remain separate obligations.

## Supply-chain and release impact

State-machine checking is development assurance only. ZRM core and runtime
crates do not depend on a model checker or solver. Internal model results are
not public replay evidence and do not promote production authority. A release
claim requires a separately approved public or independently reproducible
evidence bundle.

## Claim changes

After this RFC is accepted, implemented, and evidenced, ZRM may claim for the
active profile that:

- resources use only current or explicitly accepted policy versions according
  to role, and creation can be suspended without selecting a replacement;
- uncommitted facts and plans are exact-context-bound;
- durable commit is all-or-nothing within the ZRM write set;
- exact retry after lost acknowledgement does not duplicate effects and a
  conflicting replay cannot be misclassified as stale;
- indeterminate durability is surfaced as unknown until resolved;
- admission and postcommit aggregation are distinct authority classes.

It still may not claim:

- automatic recovery of hard-revoked resources;
- exact-once external delivery;
- privacy;
- consensus or finality;
- proof-system, compiler, OS, or storage-hardware correctness;
- production readiness without the remaining release gates.

## Rollout and rollback

1. Approve the semantic decisions independently.
2. Freeze follow-up canonical byte tables and vectors.
3. Implement the slow reference policy/state/runtime profile.
4. Differential-test optimized implementations against it.
5. Introduce a new journal schema carrying `semantic_effects_root`.
6. Add governed verifier and admission paths.
7. Rehearse crash recovery and idempotent retry.
8. Enable authority-bearing use only under a separately approved release
   profile.

Rollback of an implementation release restores code but never rewinds machine
state or reuses a state version. Policy rollback is a new governed update.

## Open questions

The following are intentionally left for follow-up RFCs and do not alter the
semantics above:

- canonical bytes and hash domains for the new logical objects;
- emergency recovery/migration for hard-revoked resources;
- authenticated privacy-preserving retry disclosure;
- sharded/MVCC durable commit;
- the parameterized recursive journal-composition proof and accumulator choice.

## Decision

To be completed by maintainers after independent semantic, authority-boundary,
and compatibility review.
