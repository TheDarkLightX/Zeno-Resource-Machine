# RFC-0001: Policy, Context, Fact Freshness, and Commit Authority

**Status:** Draft  
**Authors:** Dana Edwards; drafting assistance by OpenAI GPT-5.6 Pro  
**Reviewers:** Independent semantic reviewer TBD; authority-boundary reviewer TBD  
**Created:** 2026-07-12  
**Target version:** ZRM 0.2 draft  
**Change class:** E

## Summary

This RFC closes the semantic gap between a structurally valid resource
transition and an authority-bearing durable commit. It defines:

- current, predecessor, and hard-revoked resource-policy behavior;
- the exact snapshot carried by `TrustedValidationContext`;
- the lifetime and substitution rules for sealed verifier facts;
- the fields and effects bound by a private `CommitPlan`;
- policy-selected admission over the exact `JournalDraft`;
- atomic commit, crash recovery, and idempotent retry semantics;
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
- Preserve an emergency hard-revocation mechanism without silently claiming
  recovery or liveness for stranded resources.
- Make every uncommitted authority capability snapshot-bound and fail closed on
  policy, state, epoch, ordering, or release changes.
- Make the complete durable effect set explicit and journal-bound.
- Define an atomic commit API with unambiguous lost-ack recovery.
- Keep admission and postcommit recursive aggregation semantically distinct.
- Provide bounded ESSO oracles, counterexamples, and parameterized proof
  obligations for implementation.

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

### 1. Resource-policy disposition

For one active machine-policy snapshot, every resource-kind policy ID has
exactly one disposition:

```text
PolicyDispositionV1 =
    CurrentCreation
  | AcceptedPredecessor
  | HardRevoked
```

Absence from the authenticated policy snapshot is equivalent to unsupported and
fails closed. No implicit default or wildcard disposition exists.

#### 1.1 Current creation policy

For each resource kind, exactly one non-revoked policy is selected as
`CurrentCreation`.

A created resource MUST use that exact policy. Equality of resource kind,
program, unit, or other contents is insufficient: the selected policy identity
must match exactly.

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

Governance MUST NOT hard-revoke the currently selected creation policy without
atomically selecting another non-revoked current creation policy in the same
policy update.

### 2. Policy activation and rollback

Policy activation is a runtime governance operation outside ordinary
`TransitionStatementV1`.

A successful policy update atomically changes:

```text
policy_root
state_version
validation_context_hash
```

and preserves the machine and domain identity.

Every policy update increments the monotonically increasing state version. A
rollback is represented as a new governance update and new state version. It
MUST NOT restore an earlier `(policy_root, state_version)` tuple or otherwise
create an ABA-equivalent snapshot.

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

A governed `PolicySnapshotV1` is resolved from
`TrustedValidationContext.expected_policy_root`. It supplies:

```text
PolicySnapshotV1 {
  machine_policy
  resource_kind_policy_dispositions
  current_creation_policy_by_kind
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

### 7. Complete commit effects

Finalization produces one canonical logical effect descriptor:

```text
CommitEffectsV1 {
  active_resource_deletes_root
  active_resource_delete_count
  active_resource_inserts_root
  active_resource_insert_count
  nullifier_inserts_root
  nullifier_insert_count
  transition_replay_inserts_root
  transition_replay_insert_count
  reward_and_escrow_effects_root
  reward_and_escrow_effect_count
  outbox_records_root
  outbox_record_count
  audit_records_root
  audit_record_count
  total_storage_write_bytes
}
```

Every field is derived. A caller-provided effect list or count is
non-authoritative and must match recomputation if accepted as an optimization.

No storage write, reward, escrow movement, replay key, outbox message, or audit
record may be hidden outside `CommitEffectsV1`.

A future canonical journal version MUST commit `commit_effects_root` and the
relevant counts. Until that version is frozen and implemented, ZRM cannot claim
that the journal completely binds all durable effects.

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
  commit_effects
  commit_effects_root
  journal_draft
  journal_draft_hash
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

The runtime commit operation returns one of two success variants:

```text
CommitSuccessV1 =
    NewlyCommitted(AcceptedJournal)
  | AlreadyCommitted(AcceptedJournal)
```

`AlreadyCommitted` is an idempotent success, not a second state transition.

The logical algorithm is:

```text
1. Validate CommitPlan capability provenance and admission shape.
2. Look up transition_id in the durable replay table.
3. If a record exists:
     a. if its journal hash, effects root, and transition identity equal the
        plan, return AlreadyCommitted(existing AcceptedJournal);
     b. otherwise reject TransitionReplayConflict.
4. If no record exists, begin one atomic storage transaction or equivalent
   linearizable critical section.
5. Compare the current tuple:
     (machine_state_root, state_version, validation_context_hash)
   with the plan's expected tuple.
6. Recheck policy-selected admission against the exact plan and draft.
7. Apply every CommitEffectsV1 entry and no other authority-bearing write.
8. Persist the transition replay record and accepted journal in the same atomic
   write set.
9. Advance the state root and state version.
10. Reach the storage profile's durability point.
11. Retype JournalDraft as AcceptedJournal and return NewlyCommitted.
```

If steps 4 through 10 fail, no partial state may become visible.

The transition-record comparison in step 3 permits safe retry after a lost
acknowledgement. It does not revalidate or reapply the old transition. A
privacy-sensitive profile may suppress or authenticate the returned journal,
but it must preserve the same no-reapplication semantics.

### 11. Error precedence at commit

For a commit attempt, precedence is:

1. invalid or foreign `CommitPlan` capability;
2. existing transition record:
   - exact match -> `AlreadyCommitted` success;
   - mismatch -> `TransitionReplayConflict`;
3. stale state root/version;
4. stale validation context;
5. admission required, unexpected, or mismatched;
6. atomic write failure;
7. durability failure;
8. fail-closed internal error.

Replay lookup occurs before stale-plan rejection only to recover an already
committed identical result. It never authorizes a new write under a stale
context.

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
retry.

### 13. External effects

External delivery is outside ZRM's atomic state boundary. ZRM may atomically
persist an outbox record derived from the transition ID. Delivery is
at-least-once unless the receiver supplies an idempotency contract. ZRM MUST NOT
claim exact-once external delivery merely because outbox persistence is atomic.

### 14. ZRPF integration

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

pub fn validate_resource_for_role(
    resource: IntrinsicResourceV1,
    role: ResourceRoleV1,
    context: &TrustedValidationContext,
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
) -> Result<CommitSuccessV1, CommitError>;
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
- **Revocation/rotation:** policy-root and state-version update; every old
  uncommitted capability becomes stale.
- **Trusted computing base:** hash and proof assumptions, governed policy root,
  verifier binaries/releases, compiler/toolchain, and storage atomicity and
  durability mechanism.

## Canonical encoding and hashing

This RFC defines logical fields only.

Before implementation of new authority identities:

- exact byte tables must be added for `PolicyDispositionV1`,
  `CommitEffectsV1`, the revised journal, and any plan-binding descriptor;
- domains must be unique and versioned;
- independent vectors must cover empty and nonempty forms;
- all list roots must be sorted, unique, count-framed, and domain-separated;
- unknown variants, duplicates, malformed options, and trailing bytes reject;
- migration and cross-version replay behavior must be specified.

`CommitPlan` itself remains non-serializable. A canonical descriptor may be
hashed for binding and evidence, but serialized bytes do not recreate the
capability.

## Accounting and resource effects

- Created resources use the current creation policy.
- Consumed and referenced resources use the current or an explicitly accepted
  predecessor policy.
- Hard-revoked policies authorize no normal role.
- Accounting rows are kernel-derived.
- Every nonconserved delta has exactly one allowed transformation or authority
  fact.
- Reward, escrow, mint, burn, slash, and outbox effects appear in the explicit
  commit effect set and journal commitment.

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
- `CommitEffectsV1.total_storage_write_bytes` must not exceed the machine-policy
  and protocol ceilings.
- Verifier costs are fully planned before transition-fact dispatch, including
  admission reservation.
- Replay lookup and exact-match comparison are bounded by fixed-size identities
  and journal/effects hashes.
- No unbounded recursion or graph traversal enters the semantic or commit path.

## Security analysis

| Disaster state | Defense | Residual risk | Evidence |
| --- | --- | --- | --- |
| Creation under predecessor policy | Exact current-policy map lookup | Policy-map implementation bug | ESSO policy lifecycle model; negative mutant |
| Old resource unusable after ordinary rotation | Explicit predecessor acceptance | Governance may omit predecessor | Policy update review and live-resource analysis |
| Compromised policy remains usable | Hard revocation plus context invalidation | Live resources may be stranded | ESSO lifecycle model; explicit non-claim |
| Old fact survives policy/release/epoch change | Exact context and snapshot hashes | Incorrect runtime context construction | ESSO fact model; registry negatives |
| Fact-class substitution | Closed sealed types and class binding | Adapter implementation defect | ESSO fact model; compile-fail tests |
| Stale plan commits | CAS over root/version/context | Storage adapter violates atomicity | ESSO plan model; Loom/crash model |
| Hidden durable effect | Complete CommitEffects root in journal | Codec or derivation defect | Differential effect derivation and mutation tests |
| Double application after lost ack | Exact replay-record lookup returns prior result | Replay table corruption | ESSO exact-once model; persistent recovery tests |
| Partial commit after crash | One atomic write set and durability protocol | Database/OS/storage assumptions | ESSO recovery model; crash injection |
| Admission/postcommit confusion | Distinct lifecycle types and profiles | Misregistered backend | Registry substitution negatives |
| External duplicate delivery | Atomic outbox plus receiver idempotency | Receiver lacks idempotency | Explicit at-least-once non-claim |

## Alternatives considered

### Current policy only for every resource role

Rejected. Ordinary policy rotation would immediately strand all resources
created under the predecessor.

### Allow predecessor creation

Rejected. It permits indefinite downgrade and makes selecting a current
creation policy ineffective.

### Let facts survive policy changes when contents appear equivalent

Rejected for the first profile. It creates a second semantic-equivalence system
for policy snapshots and introduces ABA, revocation, and release-binding risk.
Reverification under the new context is simpler and fail closed.

### Reject every replay, including retry after lost acknowledgement

Rejected. It leaves callers unable to distinguish committed-with-lost-response
from rejected-with-no-effect. Exact matching against the durable replay record
provides idempotent recovery without another state transition.

### Return idempotent success for any matching transition ID

Rejected. The durable journal hash and effects root must also match. An ID with
different contents is a replay conflict.

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
- Adding `commit_effects_root` requires a new journal schema version rather than
  reinterpretation of existing journal bytes.
- Old and new journal versions cannot substitute in admission or recursive
  profiles.
- Policy rollback is a new versioned governance update, never state-version
  decrement or tuple reuse.
- Outstanding plans and facts from a prior context are intentionally invalid.

## Test and assurance plan

### Bounded ESSO models

The semantic closure package includes:

- `zrm_policy_lifecycle_v1`;
- `zrm_plan_freshness_v1`;
- `zrm_exact_once_v1`;
- `zrm_verifier_fact_freshness_v1`;
- `zrm_atomic_commit_recovery_v1`.

Each model must be 1-inductive under ESSO. Targeted mutants must produce
counterexamples for wrong-policy creation, stale-plan commit, duplicate retry
effect, Development-mode fact minting, and partial durable commit.

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
HardRevocationExcludesNormalUse
FactUseImpliesExactCurrentContext
FactClassNonSubstitution
CommitSuccessImpliesCompleteEffects
RejectImpliesStateUnchanged
ConflictingPlansHaveAtMostOneNewCommit
ExactRetryDoesNotChangeState
CrashRecoveryIsPreOrPost
AcceptedJournalImpliesDurableCommit
```

ESSO establishes bounded finite instances. Parameterized proofs and Rust
refinement evidence remain separate obligations.

## Supply-chain and release impact

ESSO is a development and assurance tool only. ZRM core and runtime crates do
not depend on ESSO, Python, Z3, or CVC5.

Release evidence records exact ESSO source revision, model hashes, solver
versions, queries/results, counterexample corpus, and explicit finite bounds.
An ESSO pass does not promote production authority.

## Claim changes

After this RFC is accepted, implemented, and evidenced, ZRM may claim for the
active profile that:

- resources use only current or explicitly accepted policy versions according
  to role;
- uncommitted facts and plans are exact-context-bound;
- durable commit is all-or-nothing within the ZRM write set;
- exact retry after lost acknowledgement does not duplicate effects;
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
5. Introduce a new journal schema carrying `commit_effects_root`.
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
