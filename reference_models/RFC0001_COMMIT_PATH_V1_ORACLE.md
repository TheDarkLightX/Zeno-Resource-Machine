# RFC-0001 commit-path model: interpretation and results

**Status:** non-authoritative bounded design evidence for draft RFC-0001. It approves no
semantics, creates no protocol bytes or authority, and is not part of the specification
package manifest.

The model is in [`rfc0001_commit_path_v1.py`](rfc0001_commit_path_v1.py). The explorer is
[`bounded_explorer.py`](bounded_explorer.py). The committed record is
[`evidence/rfc0001-commit-path-exploration-v1.json`](../evidence/rfc0001-commit-path-exploration-v1.json).

## Why it exists

The semantic-closure package says its internal bounded models are not publicly replayable
from this repository. Its obligations document also asks for a reduced-bound **composed**
model of the commit path (section 10). This model is an independent public reading of the
draft text that anyone can replay with the Python standard library:

```sh
python3 -m reference_models.rfc0001_commit_path_explorer --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference_models/tests -v
```

It does not reproduce or replace the internal models.

## Sources read

- RFC-0001 sections 8 (commit plan), 10 (atomic commit algorithm), 10.1 (read-only retry
  resolution), 11 (error precedence), 12 (crash consistency), and its assurance plan and
  formal obligations.
- `formal/state-machine/semantic_closure_v1/abstraction_and_refinement_obligations.md`,
  sections 4 and 6 to 10.
- `formal/state-machine/semantic_closure_v1/intent_map.json` for intent IDs, invariant names
  and mutant names.
- `reviews/RFC-0001-semantic-design-packet.md` section 5 for the counterexample obligations.

## Abstraction

| Model field | RFC concept |
| --- | --- |
| `record` | durable replay record for the one transition identity `T`; its contents label stands for journal hash and semantic-effects root |
| `journal` | accepted journal |
| `nullifiers` | committed nullifier set; contents `a` consume `r1`, contents `b` consume `r2` |
| `effects` | applications of `T`'s semantic effect |
| `writes` | replay-record insertions, that is, new commits for `T` |
| `(root, version, context)` | the commit freshness tuple: machine-state root, state version, validation-context hash |
| `governance_replay`, `governance_audit` | governance replay and audit records of a policy update |
| caller `plan` | the expected freshness tuple of a prepared `CommitPlanV1` |
| caller `knows` | the last result the caller received |

Each commit attempt runs steps 3 to 10 of the section-10 algorithm as one atomic step inside
the linearization boundary. Admission is not modeled, so it corresponds to `LocalKernel`.
Classification follows the section-11 precedence: an exact match is `AlreadyCommitted`, a
different record is `TransitionReplayConflict`, a mismatched tuple is stale, and otherwise
the bundle is written.

The environment then picks one of five results for the attempt:

| Action suffix | Meaning | Caller receives |
| --- | --- | --- |
| none | delivered | the classification |
| `_ack_lost` | durable, then acknowledgement lost | `OutcomeUnknown` |
| `_crash` | crash before the durability point; the transaction never executes | `OutcomeUnknown` |
| `_abort` | storage proves no write; only when the attempt would write | `RejectedConfirmedNoWrite` |
| `_pending` | the transaction is still in flight; `land_*` executes it later against the state at that moment, or it never executes | `OutcomeUnknown` |

The other actions:

- `prepare_*` runs semantic validation. A plan whose input is already nullified is
  `invalid`. Otherwise the plan records the current tuple.
- `land_*` executes a caller's in-flight transaction inside the boundary, with the
  section-10 classification at that moment.
- `resolve_*` is `resolve_retry`. It returns `AlreadyCommitted`, `TransitionReplayConflict`
  or `NotFoundAtObservedSnapshot`, and it writes nothing.
- `read_replay` is a read-only snapshot of the replay record, as a descriptor holder could
  observe it.
- `policy_update` advances every component of the tuple and both governance records.

**Bounds:**
- two callers;
- one transition identity;
- three commit attempts and two preparations per caller;
- one in-flight transaction per caller;
- one policy update.

These bounds are model bounds, not protocol limits. Counts are abstract integers, and
collision resistance of roots and hashes is assumed.

## Plan ownership

Every attempt consumes its plan, whatever the result. The RFC's typed interface takes the
plan by value, `commit(runtime, plan: CommitPlan, admission)`, and neither failure variant
returns it. The RFC also rejects "serialize or clone the commit plan for retry" because it
"would widen commit authority". A plan is a one-shot capability, valid only for one exact
snapshot.

A caller retries by preparing a new plan, which repeats semantic validation against current
state. This has two consequences:

- **A retry after a durable write fails validation.** If the first attempt's write is
  already durable, the retry's input is nullified and preparation rejects it. The caller
  learns the outcome from `resolve_retry`.
- **Step 4 is still reached.** The exact-match branch of step 4 is reached in two ways:
  - a second caller prepared identical contents at the same snapshot;
  - the first transaction lands after the caller was told `OutcomeUnknown` and has prepared
    again. This is the realistic lost-acknowledgement race, and `_pending` with `land_*`
    models it.

An earlier revision of this model also explored a reading in which the caller keeps its
plan after `OutcomeUnknown`. The interface above rules that reading out, so it was removed.
Without `_pending`, that revision also missed `retry_duplicates_effect` with a single
conflicting caller. Adding the delayed-durability choice closes that gap.

## Invariants

State invariants hold in every reachable state:

| Invariant | Source name |
| --- | --- |
| `ReplayAndNullifierMoveTogether` | intent map, I-EXACT-ONCE-COMPLETE |
| `JournalAndReplayMoveTogether` | intent map, I-EXACT-ONCE-COMPLETE |
| `EffectCountMatchesReplay` | intent map, I-EXACT-ONCE-COMPLETE |
| `ConflictingPlansHaveAtMostOneNewCommit` | RFC-0001 formal obligations |
| `MachineRootAndStateVersionAdvanceTogether` | intent map, I-POLICY-UPDATE-CONTEXT |
| `GovernanceReplayAndAuditMoveTogether` | intent map, I-POLICY-UPDATE-CONTEXT |

Edge invariants hold on every enabled transition:

| Invariant | Statement in the model |
| --- | --- |
| `FreshCommitOnly` | a new write uses a plan whose tuple equals the pre-state tuple |
| `ReplayClassificationLinearizable` | with a durable record present, an attempt neither writes nor answers stale |
| `RejectImpliesStateUnchanged` | stale, conflict, rejected-no-write and invalid leave durable state unchanged |
| `ExactRetryDoesNotChangeState` | `AlreadyCommitted` leaves durable state unchanged |
| `AlreadyCommittedRequiresExactRecord` | `AlreadyCommitted` only when the durable record is the caller's contents |
| `RetryResolutionAppliesNoEffects` | resolution leaves durable state unchanged |
| `CommitSuccessImpliesCompleteEffects` | `NewlyCommitted` leaves exactly the complete bundle |
| `CrashRecoveryIsPreOrPost` | a crash or abort leaves the complete pre-state or the complete post-state |

## Results

### Correct model

| Instance | States | Transitions | Violations | Observable classes | Probes |
| --- | ---: | ---: | ---: | ---: | ---: |
| duplicate | 2,561 | 12,337 | 0 | 613 | 26 |
| conflicting | 3,444 | 17,167 | 0 | 709 | 20 |

- **Observable classes.** Reachable states that give the same outcome to every future action
  sequence are merged, so this is the least number of states any implementation with the
  same observable behavior must distinguish. Outcomes include the environment's actions:
  `land_*` is observable as enabled or disabled.
- **Probes.** Every class is told apart from every other by one of the listed probe words,
  each of at most three actions.
- **Durable fields.** Every durable field is determined by its class. Only caller
  bookkeeping after a terminal result is invisible.
- **Model bounds.** Some probes separate states only by the remaining attempt budget. That
  budget is a model bound, not protocol behavior.

### Mutants

Mutant names and intent IDs are those of `intent_map.json`. Each shortest trace is
re-executed by `replay`, which uses no exploration data. Every mutant is killed in both
instances.

| Mutant | Intent | Shortest trace and first violated invariant |
| --- | --- | --- |
| `stale_plan_commits` | I-CONTEXT-SNAPSHOT-EXACT | `prepare_A, policy_update, commit_A`: `FreshCommitOnly` |
| `policy_change_reuses_machine_root` | I-POLICY-UPDATE-CONTEXT | `policy_update`: `MachineRootAndStateVersionAdvanceTogether` |
| `replay_lookup_outside_commit_boundary` | I-REPLAY-LINEARIZABLE | see below |
| `retry_duplicates_effect` | I-EXACT-ONCE-COMPLETE | see below |
| `unknown_reported_as_rejected` | I-OUTCOME-UNKNOWN | `prepare_A, commit_A_ack_lost`: `RejectImpliesStateUnchanged` |
| `resolution_reapplies_effect` | I-OUTCOME-UNKNOWN | `prepare_A, commit_A_ack_lost, resolve_A`: `RetryResolutionAppliesNoEffects` |
| `partial_durable_commit` | I-COMMIT-ATOMIC-DURABLE | `prepare_A, commit_A_crash`: `CrashRecoveryIsPreOrPost` |

**`replay_lookup_outside_commit_boundary`.** With a conflicting second caller, the
shortest schedule is the review packet's "two commits":

```text
prepare_A, lookup_A, lookup_B, commit_A, prepare_B, commit_B
```

B observes absence before A commits, prepares a fresh plan afterwards and writes a second
time under `T`. With a duplicate second caller, B cannot prepare after A nullified the shared
input. Its attempt is instead misclassified as stale, which section 10 forbids. That
violates `ReplayClassificationLinearizable` in six actions.

**`retry_duplicates_effect`.** A duplicate second caller kills it in four actions:

```text
prepare_A, prepare_B, commit_A, commit_B
```

A single conflicting caller kills it in five, through the lost-acknowledgement race:

```text
prepare_A, commit_A_pending, prepare_A, commit_A, land_A
```

The retry commits, then the original transaction lands on the exact record and re-executes.

## Cross-check of the quotient

`bounded_explorer.quotient` is a standard-library port of `state_discovery::RawModel::quotient`
from [Zeno-ADP](https://github.com/TheDarkLightX/Zeno-ADP) 0.8.0. The Rust program in
[`zeno_adp_vectors`](zeno_adp_vectors) asks Zeno-ADP for the answers on 120 seeded random
tables and on the two correct model tables, which it records by SHA-256.
`test_bounded_explorer.py` requires the port to match every class, class table and probe
word. See that directory's README for how to regenerate the vectors.

## Not modeled

- **Policy creation and suspension:** `creation_under_wrong_policy` and
  `revoked_current_remains_selected`.
- **Verifier-fact freshness:** `development_fact_grants_authority`.
- **Recursive composition:** the I-RECURSIVE-* intents.
- **Admission:** facts and admission-required profiles.
- **Concurrency and external effects:** more than two callers or one transition identity,
  storage-level concurrency, and outbox delivery.

Those intents need their own models.

## Non-claims

- Bounded enumeration is not an unbounded or parameterized proof.
- The model is an independent reading of a draft. It is not independent semantic review.
- Passing here establishes nothing about a Rust implementation until a differential test
  against this model, or a refinement argument, exists.
- The quotient is minimal only for this model's declared actions and outcomes.
