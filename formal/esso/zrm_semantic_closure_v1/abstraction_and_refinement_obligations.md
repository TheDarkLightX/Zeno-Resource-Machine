# ZRM ESSO abstraction and refinement obligations

**Package:** `zrm-semantic-closure-esso-v1`  
**Status:** Draft design evidence; not an implementation or production claim  
**ESSO models:** `TheDarkLightX/ESSO`, branch `agent/zrm-semantic-closure-v1`

## 1. Purpose

The ESSO models make selected ZRM authority and persistence questions finite,
explicit, and counterexample-generating. A passing bounded model is useful only
when the abstraction from ZRM objects to model state is stated and later
connected to implementation behavior.

This document records those connections as proof obligations. None is satisfied
merely because an ESSO model is inductive.

## 2. Common abstraction discipline

For every model `M`, define:

```text
alpha_M : ConcreteZrmState -> AbstractEssoState
classify_M : ConcreteOperation -> Option<AbstractAction>
```

The intended refinement obligation is:

```text
For every concrete state s satisfying ConcreteInvariant(s),
and every concrete operation op:

  if classify_M(op) = Some(a)
  and ConcreteStep(s, op) = Success(s', out),
  then EssoStep(alpha_M(s), a) = Success(alpha_M(s'), alpha_out(out)).

  if EssoStep(alpha_M(s), a) rejects because an authority precondition is
  false, ConcreteStep must not newly commit the corresponding authority effect.
```

The first profile may use a stronger equality relation than necessary. A later
optimized implementation may use a verified abstraction relation, but it must
not accept more authority-bearing behavior than the reference relation.

### 2.1 No-extra-authority obligation

For each modeled action:

```text
ConcreteAccept(s, op) -> AbstractAccept(alpha(s), classify(op))
```

For security-critical rejection classes:

```text
AbstractReject(alpha(s), classify(op)) ->
  ConcreteRejectOrNoNewAuthority(s, op)
```

A concrete implementation may reject additional cases only when the RFC or
active profile permits the stricter behavior and the liveness/non-claim impact
is explicit.

### 2.2 Stuttering

Concrete bookkeeping steps that do not change any modeled authority-relevant
projection may stutter:

```text
alpha(s') = alpha(s)
```

Stuttering is forbidden for hidden value movement, policy changes, verifier
release changes, replay records, accepted journals, or durable outbox effects.

### 2.3 Bounded-domain interpretation

ESSO integer ranges and finite enums are model bounds, not protocol limits.
Parameterizing beyond those bounds requires one of:

- a theorem over arbitrary finite sets, counters, or sequences;
- a checked-arithmetic proof reducing larger values to the same local relation;
- exhaustive implementation bounds that exactly match the active profile.

No claim about unbounded production behavior may cite bounded ESSO induction
alone.

## 3. Model-specific abstraction maps

## 3.1 `zrm_policy_lifecycle_v1`

### Concrete projection

| ESSO state | Concrete source |
| --- | --- |
| `creation_policy` | exact current creation-policy ID for one selected resource kind |
| `predecessor_p0` | membership of the modeled older policy in the authenticated accepted-predecessor set |
| `revoked_p0`, `revoked_p1` | hard-revocation disposition in the current authenticated policy snapshot |
| `resource_status` | absent, active, or consumed state of one selected resource identity |
| `resource_policy` | exact resource-kind policy ID committed by that resource |
| `last_event`, `last_policy` | ghost variables used only to state transition postconditions |

`last_event` and `last_policy` are specification ghosts. A production runtime
need not store them. A proof or test must instead establish the corresponding
postcondition directly for each operation.

### Obligations

1. Every resource kind has exactly one current non-revoked creation policy.
2. Created resources use the exact selected policy ID, not merely equivalent
   contents.
3. Predecessor membership authorizes only the roles named by RFC-0001.
4. Hard revocation removes normal use in the same authenticated policy update.
5. A policy update never makes a hard-revoked policy current or predecessor.
6. Existing resources may remain represented after hard revocation; the model
   makes no recovery or liveness claim.

### Generalization

The two-policy model must be generalized to arbitrary finite policy histories:

```text
CurrentCreation(kind) is a singleton.
CurrentCreation(kind) notin HardRevoked.
AcceptedPredecessor(kind) intersect HardRevoked = empty.
Creation(resource) -> resource.policy = CurrentCreation(resource.kind).
NormalUse(resource) ->
  resource.policy = CurrentCreation(resource.kind)
  or resource.policy in AcceptedPredecessor(resource.kind),
  and resource.policy notin HardRevoked.
```

## 3.2 `zrm_plan_freshness_v1`

### Concrete projection

| ESSO state | Concrete source |
| --- | --- |
| runtime snapshot counters | machine-state root/version, policy root, current epoch, ordering-context root |
| plan snapshot counters | corresponding private fields of `CommitPlan` |
| `plan_status` | no plan, private prepared plan, or already durable exact transition |
| `admission_mode` | policy-selected LocalKernel or RequiredVerifier |
| `admission_verified`, `journal_bound` | exact `VerifiedAdmissionFact` binding to the plan's journal draft |
| effect/replay/journal booleans | abstract visibility of the complete ZRM write set |

The integer generations abstract collision-resistant roots. Equality in the
model means exact typed root equality in ZRM. Inequality means at least one
security-relevant field differs.

### Obligations

1. `validation_context_hash` binds every context field named by RFC-0001.
2. Plan construction copies the exact expected snapshot, not caller echoes.
3. New commit uses one atomic comparison of root, version, and context hash.
4. Policy-required admission matches the exact draft and expected verifier.
5. Local mode rejects an unexpected admission capability.
6. Rejection exposes none of the modeled durable effects.
7. The model's idempotent state corresponds only to an exact durable replay
   match, not a stale uncommitted plan.

### Generalization

For any two contexts `c1` and `c2`:

```text
c1 != c2 -> validation_context_hash(c1) != validation_context_hash(c2)
```

subject to the selected hash assumptions. The runtime must not compare only a
subset of the fields.

## 3.3 `zrm_exact_once_v1`

### Concrete projection

| ESSO state | Concrete source |
| --- | --- |
| `resource_state` | active-set membership and historical nullifier/replay state for one resource |
| `nullifier_present` | deterministic transparent nullifier in the committed nullifier set |
| `replay_record` | transition identity in the durable replay table |
| `value_effect_count` | abstract number of applications of one authority/value effect |
| `accepted_journal` | durable accepted journal for the exact transition |

### Obligations

1. Consumption removes the active resource and inserts its nullifier in one
   atomic write set.
2. The replay record, journal, and every authority/value effect are in that same
   write set.
3. A created identity is absent from both active and historical domains.
4. Exact retry does not execute any transition effect.
5. A replay-table match compares transition identity, journal hash, and complete
   effects root.
6. Mismatched content under an existing identity is a conflict, not success.

### Generalization

For arbitrary finite transitions, prove:

```text
ConsumedIds are unique.
CreatedIds are unique.
ConsumedIds, ReferencedIds, CreatedIds are pairwise disjoint.
For each consumed c, nullifier(c) is fresh before commit and present after.
Each transition replay key changes from absent to present at most once.
Every effect belongs to exactly one successful new commit.
Exact retry preserves the complete machine state.
```

## 3.4 `zrm_verifier_fact_freshness_v1`

### Concrete projection

| ESSO state | Concrete source |
| --- | --- |
| policy/release/epoch generations | policy snapshot hash, governed release identity, trusted current epoch |
| expected class and statement | exact verifier slot expected by prevalidation/finalization/commit |
| fact fields | private fields of one sealed `Verified*Fact` capability |
| `authority_granted` | downstream semantic kernel consumed the fact for the modeled slot |

### Obligations

1. Only the governed registry owns constructors for sealed facts.
2. Production authority rejects Development and Test policies before fact
   construction.
3. A fact binds the exact parent, claim, child statement, output, policy
   snapshot, validation context, verifier policy, program/key, and release.
4. Lifecycle fact types are non-interchangeable at the Rust type boundary.
5. Policy, release, epoch, statement, or class mismatch prevents authority use.
6. Remote verifier output remains untrusted until locally authenticated.

### Generalization

For any sealed fact `f` and expected slot `e`:

```text
Use(f, e) -> Binding(f) = Binding(e)
```

where equality is componentwise over every field listed in RFC-0001. No
subset-based compatibility relation is sufficient.

## 3.5 `zrm_atomic_commit_recovery_v1`

### Concrete projection

| ESSO state | Concrete source |
| --- | --- |
| staged booleans | uncommitted transaction/WAL pages or adapter-private writes |
| durable booleans | externally visible committed effects, nullifiers, replay record, and journal |
| `durable_state` | committed pre-root or computed post-root |
| `txn_phase` | abstract adapter phase around the durability point and acknowledgement |

Staged values are deliberately non-authoritative. They may exist transiently but
must not become visible through the committed state API.

### Obligations

1. The storage profile identifies one linearization/durability mechanism.
2. Recovery before the commit record yields the complete pre-state.
3. Recovery after the commit record yields the complete post-state.
4. The accepted journal is unavailable before the durable post-state.
5. Success acknowledgement occurs only after the profile's durability point.
6. Retry after durability reads the replay record and returns the prior result.
7. Crash tests inject failure before and after every concrete persistence
   boundary, not merely the five abstract actions.

### Generalization

For every concrete crash point `p`:

```text
recover(run_until_crash(pre, plan, p)) in {pre, post(plan)}
```

and if it is `post(plan)`, every declared effect and no undeclared effect is
present.

## 4. Cross-model composition obligations

The models were checked separately. End-to-end ZRM requires their assumptions to
align:

1. The policy snapshot used by resource validation is the same snapshot bound by
   verifier facts and the commit plan.
2. The context used to verify admission is the context compared at commit.
3. The exact-once replay record is part of the atomic recovery model's durable
   effect set.
4. The accepted journal commits the policy/context identities and complete
   effects root used by retry matching.
5. Hard revocation changes the policy/context snapshot, invalidating old facts
   and plans before they can newly commit.
6. Postcommit recursive aggregation consumes only an accepted journal produced
   after the atomic model reaches durable post-state.

A future composed ESSO model or TLA+/PlusCal model should exercise the complete
cross-product at reduced bounds. Separate model passes do not prove these
composition obligations.

## 5. Required implementation evidence

Before promotion of the relevant CBC obligations:

- reference Rust state machine with no I/O;
- independent model-to-Rust differential corpus;
- generated counterexample regressions for each ESSO mutant;
- compile-fail tests for fact/plan construction and class substitution;
- Kani exact-once and checked-arithmetic harnesses;
- Loom conflicting-plan and replay-race exploration;
- fault-injection tests for every storage boundary;
- one persistent adapter recovery rehearsal;
- mutation tests for all context, policy, release, class, journal, and effects
  comparisons;
- parameterized theorem statements for arbitrary finite resource and policy
  sets;
- independent semantic and authority-boundary review.

## 6. Non-claims

The current ESSO work does not establish:

- correctness of the proposed RFC;
- correctness of the abstraction maps above;
- Rust implementation conformance;
- unbounded correctness;
- cryptographic soundness;
- database, filesystem, OS, or hardware correctness;
- exact-once external delivery;
- recovery of hard-revoked resources;
- recursive proof composition;
- production readiness.
