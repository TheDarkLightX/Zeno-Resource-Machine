# RFC-0001 semantic design and adversarial packet

**Change or PR:** RFC-0001 semantic closure package  
**Change class:** E  
**Affected contracts:** `ZRM-SC-002`, `003`, `005`, `006`, `008`, `009`, `010`, `011`, `012`, `013`  
**Normative candidate:** `rfcs/RFC-0001-policy-context-fact-and-commit-authority.md`  
**Authoring/oracle proposer:** OpenAI GPT-5.6 Pro  
**Specification owner:** Dana Edwards  
**Independent semantic reviewer:** Required; not yet assigned  
**Authority-boundary reviewer:** Required; not yet assigned  
**Date:** 2026-07-12  
**Status:** `REQUEST_INDEPENDENT_REVIEW`

> This is an authoring and adversarial-design packet. It does not qualify as the independent approval required by `ZRM-SC-013`, because the same reasoning track proposed the RFC and ESSO models. It creates no protocol authority.

## 1. Information-flow declaration

```text
Materials received before the design pass:
  ZRM README, specification, implementation plan, semantic contracts,
  prior audit findings/remediation context, and ESSO repository/design.

Materials intentionally withheld:
  None; this was the authoring track, not an independent oracle track.

Prior involvement:
  The same model performed the prior ZRM audit and drafted the semantic
  contract suite. Correlated assumptions are therefore expected.

Model/tool:
  OpenAI GPT-5.6 Pro plus ESSO bounded state-machine checks.

Qualification:
  Corroborative semantic design and counterexample work only. A separate
  reviewer must derive or challenge the accepted-state and invalid-state
  expectations without inheriting this implementation rationale.
```

## 2. Normative inputs

| Source | Scope used | Ambiguity resolved by RFC-0001 |
| --- | --- | --- |
| `SPECIFICATION.md` | state model, policy, trusted context, facts, pipeline, commit, journal, verifier API | exact policy dispositions; fact lifetime; retry outcome; complete effect binding |
| `SEMANTIC_CONTRACTS.md` | contract registry and fail-closed hierarchy | maps the RFC to stable review boundaries |
| `ZRM-SC-002` | policy-valid resources | creation versus predecessor versus hard revocation |
| `ZRM-SC-003` | trusted context and machine policy | exact snapshot binding and no ABA rollback |
| `ZRM-SC-005` | membership, freshness, replay | exact retry versus conflicting replay |
| `ZRM-SC-006` | governed verifier facts | context/release/class freshness and Production-only authority |
| `ZRM-SC-009` | accounting and transformations | all effects must be explicit and derived |
| `ZRM-SC-010` | finalization and commit plan | complete private plan contents |
| `ZRM-SC-011` | admission, commit, journals | linearization, recovery, and accepted-journal authority |
| ESSO models | bounded design oracles | finite counterexample search for selected decisions |

## 3. Authority map

```text
Untrusted transition / policy IDs / proof artifacts / retry request
  -> bounded canonical candidates
  -> TrustedValidationContext from authenticated runtime state
  -> GovernedPolicySnapshot from expected policy root
  -> policy-valid resources and exact verifier statements
  -> governed verifier registry
  -> sealed precommit facts
  -> pure finalization
  -> private CommitPlan + exact JournalDraft
  -> optional exact VerifiedAdmissionFact
  -> replay lookup, snapshot CAS, atomic durable write
  -> NewlyCommitted or AlreadyCommitted
  -> AcceptedJournal
  -> optional postcommit recursive aggregation / anchor
```

### Authority newly defined

- exact policy disposition for each resource-kind policy;
- conservative invalidation of all uncommitted facts and plans on context change;
- one complete derived commit-effect set;
- idempotent `AlreadyCommitted` success for an exact durable replay match;
- explicit admission-versus-postcommit proof lifecycle separation.

### Authority deliberately unavailable

- creation under predecessor policies;
- use under hard-revoked policies;
- reuse of a fact or plan under a different context;
- authority from Development/Test receipts;
- hidden storage, reward, replay, audit, or outbox writes;
- idempotent success from transition ID equality alone;
- automatic migration of hard-revoked resources;
- exact-once external network delivery.

## 4. Accepted-state decision table

| Case | Preconditions | Expected result |
| --- | --- | --- |
| Create under current policy | exact current policy, active snapshot, non-revoked, resource valid | policy-valid created resource |
| Consume current-policy resource | active resource, fresh nullifier, current policy, exact logic/authority facts | transition may finalize |
| Consume predecessor resource | policy explicitly accepted as predecessor, not hard-revoked, role permits use | transition may finalize; no predecessor creation authority |
| Hard-revoke predecessor | governance authenticates update and removes predecessor disposition atomically | new context; normal use under old policy rejects |
| Use fresh production fact | exact context, policy, release, class, statement, output, validity | fact satisfies exactly one required slot |
| Local commit | exact fresh plan, LocalKernel, no admission fact, no replay record | `NewlyCommitted(AcceptedJournal)` |
| Required admission commit | exact fresh plan and exact admission fact over the draft | `NewlyCommitted(AcceptedJournal)` |
| Lost-ack retry | durable replay record exists and transition, journal, and effects hashes match | `AlreadyCommitted(existing journal)`; state unchanged |
| Crash before commit record | staged state only | recovery yields complete pre-state |
| Crash after commit record | durable record and complete effects exist | recovery yields complete post-state |
| Postcommit aggregation | accepted journal exists and aggregate profile verifies it | postcommit fact only; no retroactive admission |

## 5. Invalid-state matrix

| Dimension | Mutation or state | Required outcome |
| --- | --- | --- |
| Policy identity | create under predecessor or same-content different policy | reject |
| Revocation | use a hard-revoked policy through normal path | reject |
| Snapshot | policy root, state version/root, epoch, or ordering changes after preparation | stale rejection; no writes |
| Release | verifier release rotates after fact creation | fact unusable |
| Mode | Development/Test policy under production path | no sealed production fact |
| Class | postcommit fact supplied as admission or logic fact | type/API rejection |
| Statement | correct verifier and policy for a different claim/draft | reject |
| Replay | same transition ID, different journal or effects | `TransitionReplayConflict` |
| Retry | exact committed retry attempts to apply effects again | forbidden; state unchanged |
| Effects | reward/outbox/audit write absent from effects root | reject or implementation defect |
| Atomicity | nullifier or journal visible without all effects | forbidden recovery state |
| Acknowledgement | success returned before durability | forbidden |
| External delivery | outbox delivered twice | receiver idempotency required; no exact-once claim |
| Rollback | old state version/context tuple reused | forbidden ABA state |

## 6. ESSO oracle package

**Repository:** `TheDarkLightX/ESSO`  
**Branch:** `agent/zrm-semantic-closure-v1`  
**Draft PR:** `TheDarkLightX/ESSO#1`

Models:

- `zrm_policy_lifecycle_v1`;
- `zrm_plan_freshness_v1`;
- `zrm_exact_once_v1`;
- `zrm_verifier_fact_freshness_v1`;
- `zrm_atomic_commit_recovery_v1`.

The models are simpler than production because they use one resource or plan,
small generation counters, Boolean effect visibility, and no cryptography,
database, networking, or arbitrary-size lists. Ghost event fields express
postconditions without prescribing production storage.

The checker requires every reference model to be 1-inductive and each targeted
disaster mutant to produce `InitNotInv` or `InvNotInductive` with a concrete
counterexample. Unsupported syntax, timeout, `unknown`, or generic solver error
does not count as a killed mutant.

## 7. Targeted counterexample log

| Attempt | Expected | Evidence status |
| --- | --- | --- |
| Create P1 resource while P0 is current | `CreationUsesExactCurrentPolicy` counterexample | ESSO mutant |
| Commit after any snapshot component changes | `FreshCommitOnly` counterexample | ESSO mutant |
| Retry increments value effect twice | exact-once invariant counterexample | ESSO mutant |
| Development-mode verifier mints a fact | Production-only counterexample | ESSO mutant |
| Durable commit omits nullifier/replay/journal | atomic durable-write counterexample | ESSO mutant |
| Predecessor resource used after hard revocation | normal use guard unavailable | positive lifecycle model plus reviewer trace required |
| Admission fact used after policy change | commit guard unavailable | positive plan model plus reviewer trace required |
| Logic fact substituted for admission | class mismatch | fact model plus compile-fail Rust test required |
| Same transition ID with mismatched effects | conflict, not idempotent success | RFC decision; fuller replay model required |
| Crash at every concrete storage boundary | complete pre/post only | implementation fault-injection required |

## 8. Design discoveries and corrections

### 8.1 ESSO enum namespace constraint

The first modeling pass reused symbols such as `None`, `Committed`, and
`Verified` across enum types. ESSO rejected the affected models as ambiguous.
The models were corrected to use globally namespaced symbols. This was a model
construction issue, not evidence for the semantic claims.

### 8.2 Mutant evidence rule

The initial checker counted any fail-closed ESSO failure as a rejected mutant.
That was too weak: parser or unsupported-feature failure could masquerade as
semantic mutation evidence. The checker now accepts only an explicit invariant
counterexample with a witness.

### 8.3 Retry semantics

Strictly rejecting every replay was rejected as operationally ambiguous after a
lost acknowledgement. The selected design returns `AlreadyCommitted` only when
transition identity, accepted-journal hash, and complete-effects root all match
the durable record. No effect is re-applied.

### 8.4 Hard revocation semantics

Creation-only revocation was rejected as too weak for a compromised policy.
Automatic migration was rejected as hidden authority. Hard revocation therefore
prioritizes containment and may strand resources until a separately governed
recovery rule exists.

### 8.5 Context equivalence

Reusing facts or plans when two policy snapshots appear semantically equivalent
was rejected for the first profile. Exact context-hash equality is simpler,
revocation-safe, and avoids a second policy-equivalence relation.

## 9. Formal and implementation obligations

- prove policy disposition set properties for arbitrary finite policy histories;
- prove exact role and fact coverage for arbitrary bounded lists;
- prove new commit requires exact context equality;
- prove exact retry preserves all state;
- prove mismatched replay cannot become idempotent success;
- prove recovery returns complete pre-state or complete post-state;
- build a simple reference runtime and differential-test optimized adapters;
- add Kani, Loom, mutation, fuzz, and crash-injection evidence;
- freeze canonical bytes and vectors in a separate Class E change;
- independently review the RFC, abstraction map, and counterexamples.

## 10. Residual gaps and non-claims

- The RFC is a draft and has no protocol authority.
- The authoring model is not an independent semantic reviewer.
- ESSO evidence is finite and assumption-bound.
- No production Rust implementation has been compared against the models.
- No new canonical ABI or journal hash has been frozen.
- No hard-revocation recovery protocol exists.
- No external exact-once-delivery claim exists.
- Recursive semantic composition remains a follow-up package.

## 11. Requested independent review outcome

An independent reviewer should select one after deriving their own oracle:

- `APPROVE`;
- `APPROVE_WITH_TRACKED_GAPS`;
- `REQUEST_CHANGES`;
- `BLOCK_AMBIGUOUS_SPEC`;
- `BLOCK_UNSATISFIED_AUTHORITY_OBLIGATION`.

The current authoring-track status is:

```text
REQUEST_INDEPENDENT_REVIEW
```
