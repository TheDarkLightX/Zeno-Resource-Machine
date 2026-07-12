# ZRM abstraction and refinement obligations

**Package:** `zrm-semantic-closure-v1`
**Status:** Draft design evidence; no implementation or production claim
**Author:** Dana Edwards
**Drafting assistance:** GPT-5.6

## 1. Purpose

Internal bounded reference models make selected ZRM authority and persistence
questions finite and counterexample-generating. A bounded model supports a claim
only when its abstraction from concrete objects is explicit and the concrete
implementation is later shown to refine the modeled relation.

Detailed internal model artifacts are not part of the public repository. This
document preserves the public proof obligations without exposing internal
tooling or repository metadata.

## 2. Common refinement relation

For each model `M`, define:

```text
alpha_M    : ConcreteZrmState -> AbstractModelState
classify_M : ConcreteOperation -> Option<AbstractAction>
```

The safety direction is:

```text
ConcreteAccept(s, op) ->
  AbstractAccept(alpha_M(s), classify_M(op))
```

For every security-critical abstract rejection:

```text
AbstractReject(alpha_M(s), classify_M(op)) ->
  ConcreteRejectOrNoNewAuthority(s, op)
```

The concrete implementation may reject additional cases only when the active
profile permits that stricter behavior and its liveness impact is explicit.

Concrete bookkeeping may stutter only when it changes no authority-relevant
projection:

```text
alpha_M(s') = alpha_M(s)
```

Policy state, verifier releases, semantic effects, replay records, accepted
journals, nullifiers, state roots, and durable outbox entries cannot stutter.

Finite enums and counters are model bounds, not protocol limits. Generalization
requires a parameterized theorem, a checked-arithmetic refinement proof, or
concrete profile bounds that exactly match the verified domain.

## 3. Policy creation and suspension

### Abstract model

`zrm_policy_creation_suspension_v1`

### Concrete projection

| Abstract field | Concrete source |
| --- | --- |
| creation selection | authenticated `CreationSelectionV1` for one resource kind |
| policy dispositions | authenticated current, predecessor, or hard-revoked entries |
| resource policy | exact policy identity committed by one resource |
| resource status | absent, active, or consumed membership |
| last action | specification ghost used to state postconditions |

### Obligations

1. Each kind has exactly one `CreationSelectionV1` value.
2. `Enabled(id)` requires `id` to have `CurrentCreation` disposition and not be
   hard revoked.
3. `Suspended` permits no creation.
4. Creation uses the exact selected identity, not content equivalence.
5. An accepted predecessor grants only explicitly enumerated existing-resource
   roles.
6. Revoking the selected current policy atomically selects an authorized
   replacement or suspends creation.
7. Hard-revoked policies grant no normal use.
8. Existing resources may remain stranded; no recovery authority is inferred.

For arbitrary finite policy histories:

```text
selection(kind) = Enabled(p) -> disposition(p) = CurrentCreation
selection(kind) = Suspended -> no Create(kind, _)
disposition(p) = HardRevoked -> not NormalUse(p)
Create(kind, p) -> selection(kind) = Enabled(p)
```

## 4. Context and plan freshness

### Abstract model

`zrm_plan_freshness_v1`

### Concrete projection

| Abstract field | Concrete source |
| --- | --- |
| runtime context generations | machine-state root/version, policy root, epoch, ordering context, profiles |
| plan context generations | private expected-context fields of `CommitPlanV1` |
| policy-update event | governed policy-root transition and its atomic metadata |
| admission fields | exact `VerifiedAdmissionFact` and journal-draft binding |
| visible effects | committed state, replay, journal, and semantic-effect projections |

### Obligations

1. `ValidationContextHashV1` binds every field named by RFC-0001.
2. Plan construction copies authenticated values rather than caller echoes.
3. A policy update derives a new policy root, incremented state version, new
   machine-state root, new validation-context hash, governance replay record,
   and governance audit record in one atomic update.
4. An old context tuple is never reused, including rollback to earlier content.
5. New commit compares the exact expected root, version, and context hash inside
   the commit linearization boundary.
6. Rejection exposes no new authority-bearing durable effect.

Context-hash collision resistance remains a cryptographic assumption and is not
proved by a finite integer abstraction.

## 5. Verifier-fact freshness

### Abstract model

`zrm_verifier_fact_freshness_v1`

### Concrete projection

| Abstract field | Concrete source |
| --- | --- |
| policy/release/context generations | authenticated policy snapshot, verifier release, and validation context |
| expected lifecycle class | exact logic, transformation, authority, availability, admission, or postcommit slot |
| statement binding | exact parent, claim, child statement, and authenticated output |
| authority granted | semantic kernel consumption of the sealed fact for that slot |

### Obligations

1. Only governed registry code constructs sealed facts.
2. Production authority rejects Development and Test policies before fact
   construction.
3. A fact binds every security-relevant policy and release field.
4. Lifecycle fact classes are non-substitutable.
5. Any context, class, statement, program/key, release, or output mismatch
   prevents authority use.
6. Remote verifier output remains untrusted until locally authenticated.

For any fact `f` and expected slot `e`:

```text
Use(f, e) -> Binding(f) = Binding(e)
```

Equality is componentwise over the complete binding declared by RFC-0001.

## 6. Exact-once transition effects

### Abstract model

`zrm_exact_once_v1`

### Concrete projection

| Abstract field | Concrete source |
| --- | --- |
| resource state | active-set membership and historical identity state |
| nullifier present | committed nullifier-set membership |
| semantic-effect count | applications of one modeled value/authority effect |
| replay record | durable transition replay entry |
| accepted journal | durable journal for the exact transition |

### Obligations

1. Consumption, nullifier insertion, semantic effects, replay record, accepted
   journal, and state-head update are one atomic bundle.
2. Created identities are fresh in both active and historical domains.
3. Exact retry executes no transition effect.
4. Replay equality compares transition identity, journal hash, and
   semantic-effects root.
5. Different contents under an existing transition identity are a conflict.
6. Every semantic effect belongs to exactly one newly committed transition.

## 7. Commitment graph and crash recovery

### Abstract model

`zrm_atomic_commit_recovery_v1`

### Concrete commitment graph

```text
SemanticEffectsV1
  -> SemanticEffectsRoot
  -> JournalPayloadV2
  -> JournalHash
  -> TransitionReplayRecordV1 and CommitMetadataV1
  -> AtomicCommitBundleV1
```

No node may contain itself transitively. The semantic-effects root excludes
replay records, accepted-journal metadata, state-head metadata, and commit audit
metadata that depend on the journal hash.

### Recovery obligations

1. The storage profile identifies one linearization and durability mechanism.
2. Recovery before its durable commit record yields the complete pre-state.
3. Recovery after it yields the complete post-state.
4. The accepted journal is unavailable before durable post-state.
5. Success acknowledgement occurs only after the stated durability point.
6. Crash injection covers every concrete persistence boundary.

For every concrete crash point `p`:

```text
recover(run_until_crash(pre, plan, p)) in {pre, post(plan)}
```

If recovery yields `post(plan)`, every declared effect and no undeclared
authority-bearing effect is present.

## 8. Replay linearization

### Abstract model

`zrm_replay_linearization_v1`

### Concrete projection

| Abstract field | Concrete source |
| --- | --- |
| durable replay slot | transaction-scoped replay-table lookup |
| candidate identity | transition ID, journal hash, semantic-effects root |
| freshness state | exact expected root/version/context comparison |
| commit count | number of successful new writes for the replay key |
| classification | newly committed, already committed, conflict, or rejected |

### Obligations

1. Replay lookup and classification occur inside the same serializable or
   linearizable boundary as new commit.
2. An absent observation made before entering that boundary grants no authority.
3. A uniqueness or compare-and-swap race re-reads durable replay state inside
   the boundary before classifying the result.
4. Exactly matching durable contents return read-only `AlreadyCommitted`.
5. Different contents return read-only `TransitionReplayConflict`.
6. At most one new commit wins for a replay key.

## 9. Outcome-unknown resolution

### Abstract model

`zrm_commit_outcome_resolution_v1`

### Concrete projection

| Abstract field | Concrete source |
| --- | --- |
| durable record state | absent, exact, or conflicting replay record |
| caller knowledge | newly committed, already committed, conflict, rejected-no-write, or unknown |
| retry descriptor | machine, domain, transition, journal hash, semantic-effects root |
| effect count | durable application count for the modeled transition |

### Obligations

1. Indeterminate transport, I/O, or durability failure returns
   `OutcomeUnknown`, never confirmed rejection or success.
2. `RetryDescriptorV1` is inert and read-only; it contains no commit capability.
3. Resolution reads durable state and performs no write.
4. Exact durable record resolves to `AlreadyCommitted`.
5. Mismatched durable record resolves to conflict.
6. An absent record yields only `NotFoundAtObservedSnapshot`; it does not prove
   historical absence beyond that authenticated observation.
7. Retrying a transition re-enters the normal linearizable commit algorithm and
   cannot reapply an already durable effect.

## 10. Cross-model composition

The separate model obligations align only if:

1. the policy snapshot used by resource validation is the snapshot bound by
   verifier facts and commit plans;
2. policy updates change the complete commit freshness tuple;
3. replay classification shares the storage linearization boundary;
4. the replay record commits the journal hash and semantic-effects root derived
   by the commitment graph;
5. the retry descriptor identifies that exact replay relation;
6. hard revocation invalidates old facts and plans before they can newly commit;
7. recursive aggregation consumes only an accepted journal reached after the
   durable post-state.

Passing separate bounded models does not prove this composition. A reduced-bound
composed model and concrete integration tests remain required.

## 11. Required implementation evidence

Before implementation promotion:

- canonical byte tables and independent vectors for every new committed object;
- a small executable reference relation written independently of optimized Rust;
- differential tests across the accepted and rejected state space;
- compile-fail tests for unauthorized capability construction;
- bounded arithmetic and state-transition harnesses;
- concurrency interleaving exploration for replay races;
- deterministic crash injection at every persistence boundary;
- stateful fuzzing across policy update, prepare, commit, timeout, resolve, and
  retry sequences;
- targeted mutants for each obligation in the intent map;
- parameterized theorems for exact-once and recovery properties; and
- independent semantic and authority-boundary approval.

## 12. Non-claims

These obligations do not establish RFC correctness, implementation refinement,
cryptographic soundness, storage-system correctness, arbitrary-size behavior,
hard-revocation recovery, external exactly-once delivery, or production
readiness.
