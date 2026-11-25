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

The environment then picks one of four results for the attempt:

| Action suffix | Meaning | Caller receives |
| --- | --- | --- |
| none | delivered | the classification |
| `_ack_lost` | durable, then acknowledgement lost | `OutcomeUnknown` |
| `_crash` | crash before the durability point | `OutcomeUnknown` |
| `_abort` | storage proves no write; only when the attempt would write | `RejectedConfirmedNoWrite` |

The other actions:

- `prepare_*` runs semantic validation. A plan whose input is already nullified is
  `invalid`. Otherwise the plan records the current tuple.
- `resolve_*` is `resolve_retry`. It returns `AlreadyCommitted`, `TransitionReplayConflict`
  or `NotFoundAtObservedSnapshot`, and it writes nothing.
- `read_replay` is a read-only snapshot of the replay record, as a descriptor holder could
  observe it.
- `policy_update` advances every component of the tuple and both governance records.

**Bounds:**
- two callers;
- one transition identity;
- three commit attempts and two preparations per caller;
- one policy update.

These bounds are model bounds, not protocol limits. Counts are abstract integers, and
collision resistance of roots and hashes is assumed.

## An open point in the draft

Section 8 makes `CommitPlanV1` non-cloneable. Section 10.1 speaks of "a caller that no
longer owns the consumed `CommitPlan`". The text does not fix whether a caller still holds
its plan after `OutcomeUnknown`. The model explores both readings:

- **`consumed`:** every attempt consumes the plan. A retry must prepare a new plan, and
  semantic validation then rejects it once the first attempt's input is nullified. A lone
  retry after a lost acknowledgement therefore never reaches the exact-match branch of step 4.
  It must use `resolve_retry`. The exact-match branch is reached only by a second caller who
  prepared identical contents at the same snapshot.
- **`retained`:** the caller keeps the plan after `OutcomeUnknown` and may attempt it again.
  Step 4 then returns `AlreadyCommitted` to the lone retry.

The correct model satisfies every invariant under both readings. The readings differ in
which mutants are observable (see `retry_duplicates_effect` below). A maintainer decision on
which reading is intended would let the next model drop the other.

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
| duplicate / consumed | 620 | 2,354 | 0 | 184 | 10 |
| duplicate / retained | 4,246 | 20,634 | 0 | 564 | 18 |
| conflicting / consumed | 698 | 2,781 | 0 | 214 | 10 |
| conflicting / retained | 5,141 | 25,591 | 0 | 644 | 18 |

- **Observable classes.** Reachable states that give the same outcome to every future action
  sequence are merged, so this is the least number of states any implementation with the
  same observable behavior must distinguish. Every class is told apart from every other by
  one of the listed probe words, each of three or four actions at most.
- **Durable fields.** Every durable field is determined by its class. Only caller
  bookkeeping after a terminal result is invisible.
- **Model bounds.** Some probes separate states only by the remaining attempt budget. That
  budget is a model bound, not protocol behavior.

### Mutants

Mutant names and intent IDs are those of `intent_map.json`. Each shortest trace is
re-executed by `replay`, which uses no exploration data.

| Mutant | Intent | Killed in | Shortest trace |
| --- | --- | --- | --- |
| `stale_plan_commits` | I-CONTEXT-SNAPSHOT-EXACT | 4 of 4 | `prepare_A, policy_update, commit_A` violates `FreshCommitOnly` |
| `policy_change_reuses_machine_root` | I-POLICY-UPDATE-CONTEXT | 4 of 4 | `policy_update` violates `MachineRootAndStateVersionAdvanceTogether` |
| `replay_lookup_outside_commit_boundary` | I-REPLAY-LINEARIZABLE | 4 of 4 | see below |
| `retry_duplicates_effect` | I-EXACT-ONCE-COMPLETE | 3 of 4 | `prepare_A, commit_A_ack_lost, commit_A` (retained) violates `EffectCountMatchesReplay` |
| `unknown_reported_as_rejected` | I-OUTCOME-UNKNOWN | 4 of 4 | `prepare_A, commit_A_ack_lost` violates `RejectImpliesStateUnchanged` |
| `resolution_reapplies_effect` | I-OUTCOME-UNKNOWN | 4 of 4 | `prepare_A, commit_A_ack_lost, resolve_A` violates `RetryResolutionAppliesNoEffects` |
| `partial_durable_commit` | I-COMMIT-ATOMIC-DURABLE | 4 of 4 | `prepare_A, commit_A_crash` violates `CrashRecoveryIsPreOrPost` |

**`replay_lookup_outside_commit_boundary`.** With a conflicting second caller, the
shortest schedule is the review packet's "two commits":

```text
prepare_A, lookup_A, lookup_B, commit_A, prepare_B, commit_B
```

B observes absence before A commits, prepares a fresh plan afterwards and writes a second
time under `T`. With a duplicate second caller, B cannot prepare after A nullified the shared
input. Its attempt is instead misclassified as stale, which section 10 forbids. That
violates `ReplayClassificationLinearizable` in six actions.

**`retry_duplicates_effect`.** The mutant survives the conflicting / consumed instance. Under
the consumed reading only a duplicate plan prepared at the same snapshot reaches the
exact-match branch, and that instance has none. The survivor is an expected consequence of
the open point above, not a gap in the invariants.

## Cross-check of the quotient

`bounded_explorer.quotient` is a standard-library port of `state_discovery::RawModel::quotient`
from [Zeno-ADP](https://github.com/TheDarkLightX/Zeno-ADP) 0.8.0. The Rust program in
[`zeno_adp_vectors`](zeno_adp_vectors) asks Zeno-ADP for the answers on 120 seeded random
tables and on the four correct model tables, which it records by SHA-256.
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
