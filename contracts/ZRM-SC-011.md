# ZRM-SC-011 — Admission, atomic commit, journals, and rejection

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

Only a successful durable atomic commit may create:

- `CommittedTransition`;
- `AcceptedJournal`;
- durable exact-once effects inside the machine write set.

A reject receipt provides deterministic diagnostic evidence only and grants no state-transition authority.

## Inputs

### Untrusted

- admission artifact;
- retry requests;
- external side-effect responses;
- adapter-specific errors and diagnostics.

### Trusted/governed

- exact `CommitPlan` and `JournalDraft`;
- current authenticated machine-state root/version/context hash;
- policy-selected admission mode and governed admission verifier;
- storage profile's atomicity and durability mechanism.

### Derived

- verified admission fact, when required;
- committed state roots/version;
- accepted journal and audit record;
- outbox key derived from `TransitionId`;
- stable commit/reject result.

## Preconditions and invariants

1. `LocalKernel` rejects an admission fact; `RequiredVerifier` requires the exact governed `VerifiedAdmissionFact`.
2. Admission verifies the exact `JournalDraftHash` after finalization and remains within the stored reservation.
3. The commit linearization point atomically compares:

   ```text
   (machine_state_root, state_version, validation_context_hash)
   ```

   against the plan.

4. The complete write set is atomic: resource deletes/inserts, nullifiers, transition replay record, journal, state version, admission reference, rewards/escrow, outbox records, and required audit data.
5. Separate prechecks followed by unguarded writes are forbidden.
6. Stale state, stale context, missing/unexpected/mismatched admission, write failure, or durability failure returns no partial success.
7. Replay/nullifier state cannot commit separately from value or authority effects.
8. Crash consistency is specified and tested at every persistence boundary.
9. `AcceptedJournal` is returned only after the storage profile's durable-commit condition.
10. Draft and accepted journal payloads/hashes are identical, but their types and authority differ.
11. v0.1 global root/version commits are serialized. At most one conflicting plan wins.
12. External delivery is outside machine exact-once semantics. External effects use an atomically persisted outbox and idempotent receiver, or are explicitly at-least-once.
13. Reject codes and receipts are deterministic for identical inputs/state/facts. Sensitive witness or verifier internals are not exposed.
14. A reject receipt is not a proof that no other request committed and cannot be used as authority.
15. Postcommit recursive aggregation cannot retroactively authorize or alter the accepted transition.

## Required postconditions

On success:

- every write is visible together;
- state version increments exactly once;
- replay protection and value effects agree;
- returned journal is exactly the committed payload.

On failure:

- no partial write or external side effect becomes visible;
- no accepted journal is returned;
- stable bounded diagnostics may be produced.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| Plan built on stale state root | `StaleState`, no writes |
| Same state but validation context advanced | `StaleValidationContext`, no writes |
| Required admission omitted | `AdmissionRequired` |
| Local mode receives admission | `AdmissionUnexpected` |
| Admission binds another draft | `AdmissionMismatch` |
| Crash after nullifier insert but before value write | Recovery shows neither or both, never split |
| Journal returned before durable commit | Critical failure |
| Two conflicting commits both succeed | Critical failure |
| External message sent before outbox commit | Architecture failure |
| Reject message leaks witness/proof details | Security failure |
| Aggregation proof used as admission | Rejection |

## Required evidence

- transactional/CAS concurrency tests;
- crash injection around every persistence boundary;
- no-split-replay invariant model;
- admission mode and draft-binding tests;
- durable-journal retyping test;
- two-plan conflict test;
- outbox/idempotency tests and external exact-once non-claim;
- reject-code precedence vectors and disclosure tests;
- storage profile assumptions and limitations.

## Non-claims

A committed transition is not automatically consensus-final, externally delivered exactly once, private, or globally available.

## Specification anchors

Sections 24.7-24.9, 26, 27, 28, 29, and 31.
