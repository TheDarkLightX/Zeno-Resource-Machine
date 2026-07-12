# RFC-0001 semantic design and adversarial packet

**Change:** RFC-0001 semantic closure
**Change class:** E
**Affected contracts:** `ZRM-SC-002`, `003`, `005`, `006`, `008`, `009`, `010`, `011`, `012`, `013`
**Normative candidate:** `rfcs/RFC-0001-policy-context-fact-and-commit-authority.md`
**Author:** Dana Edwards
**Drafting and authoring-track review assistance:** GPT-5.6
**Independent semantic reviewer:** Required
**Authority-boundary reviewer:** Required
**Date:** 2026-07-12
**Status:** `REQUEST_INDEPENDENT_REVIEW`

This packet records the authoring track's decisions and attacks. It does not
qualify as independent approval under `ZRM-SC-013` and creates no protocol
authority.

## 1. Review independence disclosure

GPT-5.6 had access to the specification, semantic contracts, earlier audit
findings, and draft semantics while assisting with this RFC. Its adversarial
pass can find internal inconsistency, but correlated assumptions remain likely.

An independent reviewer must derive expected and forbidden behavior from the
specification and threat model before relying on this packet or the RFC's chosen
abstractions.

## 2. Authority map

```text
Untrusted transition, identifiers, proof artifacts, and retry descriptor
  -> bounded canonical candidates
  -> authenticated validation context and policy snapshot
  -> policy-valid resources and exact verifier statements
  -> governed verifier registry
  -> sealed precommit facts
  -> deterministic finalization
  -> private CommitPlan and exact JournalDraft
  -> optional exact VerifiedAdmissionFact
  -> linearizable replay lookup, freshness check, and atomic durable write
  -> NewlyCommitted, AlreadyCommitted, or explicit failure classification
  -> AcceptedJournal
```

### Authority defined by the draft

- creation is selected by `Enabled(CurrentPolicyId)` or disabled by
  `Suspended`;
- uncommitted facts and plans bind one exact authenticated context;
- semantic effects are separated from commit metadata by an acyclic commitment
  graph;
- exact durable replay returns read-only `AlreadyCommitted`;
- indeterminate durability returns `OutcomeUnknown` with an inert descriptor;
- admission and postcommit aggregation use separate capability classes.

### Authority unavailable

- creation under predecessor or suspended selection;
- use under hard-revoked policy;
- reuse of a fact or plan after context change;
- authority from Development or Test receipts;
- caller-supplied effect totals or hidden authority-bearing writes;
- idempotent success from transition identity alone;
- commit authority from `RetryDescriptorV1`;
- automatic migration of hard-revoked resources;
- exact-once external network delivery.

## 3. Accepted-state decision table

| Case | Preconditions | Expected result |
| --- | --- | --- |
| Create under enabled policy | exact selected current policy, active context, valid resource | creation may proceed |
| Suspended creation | selection is `Suspended` | creation rejects with no write |
| Consume predecessor resource | explicit predecessor disposition, permitted role, not revoked | validation may proceed; no creation authority |
| Revoke selected current policy | governed update selects authorized replacement or suspension | one new authenticated context |
| Use fresh production fact | exact lifecycle class, context, policy, release, statement, output, and window | satisfies exactly one slot |
| Local commit | exact fresh plan, local mode, no admission fact, replay absent inside transaction | `NewlyCommitted(AcceptedJournal)` |
| Required-admission commit | exact fresh plan and admission fact over exact draft | `NewlyCommitted(AcceptedJournal)` |
| Exact retry | durable replay identity, journal hash, and semantic-effects root match | `AlreadyCommitted(existing journal)`; no write |
| Conflicting retry | transition identity matches but content commitments differ | `TransitionReplayConflict`; no write |
| Indeterminate response | durable outcome cannot be authenticated | `OutcomeUnknown(RetryDescriptorV1)` |
| Resolve exact descriptor | durable exact replay record exists | read-only `AlreadyCommitted` |
| Crash before durability point | transaction did not become durable | complete pre-state |
| Crash after durability point | atomic bundle became durable | complete post-state |

## 4. Invalid-state and attack matrix

| Dimension | Attack or state | Required outcome |
| --- | --- | --- |
| Creation selection | create under predecessor or while suspended | reject |
| Revocation | leave hard-revoked policy selected | impossible update or reject |
| Governance context | change policy root without state root/version/context/audit | impossible atomic update |
| Snapshot | any bound context field changes after plan preparation | stale; no new write |
| Verifier mode | Development or Test policy on production path | no production fact |
| Fact class | postcommit fact supplied as admission or logic fact | type or profile rejection |
| Statement | correct verifier for different claim or draft | reject |
| Replay race | two attempts observe absence before one wins | one winner; loser re-reads durable record |
| Replay identity | same transition, different journal or effects | conflict |
| Retry | exact retry applies semantic effects again | forbidden |
| Unknown outcome | timeout is mapped to confirmed rejection | forbidden misclassification |
| Descriptor | retry descriptor directly invokes a write | API design defect |
| Commitment graph | replay metadata enters semantic-effects root that its journal references | circular schema; reject design |
| Hidden effects | adapter writes authority state outside atomic bundle | implementation defect |
| Atomicity | journal, nullifier, replay, or value effect visible alone | forbidden durable state |
| Acknowledgement | success returned before stated durability point | forbidden |
| Rollback | prior context tuple reused | forbidden ABA state |

## 5. Counterexample obligations

| Counterexample attempt | Required evidence |
| --- | --- |
| Revoked current policy remains selected | bounded policy-suspension mutant |
| Create while selection is suspended | policy decision-table and bounded invariant |
| Policy update reuses machine root or context tuple | context-freshness mutant |
| Stale plan newly commits | plan-freshness mutant |
| Development fact grants production authority | fact-freshness mutant |
| Replay lookup outside transaction allows two commits | concurrency model mutant and schedule test |
| Exact retry increments effect count | exact-once mutant |
| Unknown result reported as rejection | outcome-resolution mutant |
| Retry resolution performs a write | outcome-resolution mutant and API test |
| Commit exposes partial durable state | recovery mutant and crash injection |
| Replay metadata enters its own transitive commitment | schema dependency-cycle checker |

Internal bounded-model artifacts are corroborative and are not publicly
replayable from this repository. Parser failure, unsupported syntax, timeout,
unknown solver result, or generic checker error cannot count as a killed mutant.

## 6. Design corrections captured by this revision

### Emergency policy suspension

Requiring an immediate replacement policy made containment depend on replacement
availability. `CreationSelectionV1::Suspended` permits atomic hard revocation
while granting no creation authority.

### Complete governance context update

A policy-root change alone could leave stale machine-root or validation-context
bindings. The draft now derives the policy root, state version, machine-state
root, validation context, governance replay record, and audit record together.

### Linearizable replay classification

A replay lookup before the commit transaction permits a stale absent
observation. Lookup, exact/conflicting classification, freshness comparison, and
new commit now share one serializable or linearizable boundary.

### Indeterminate outcome

Transport or durability uncertainty cannot establish rejection. The API exposes
`OutcomeUnknown` and a read-only descriptor that can query durable replay state
without carrying a commit capability.

### Acyclic effect commitments

The old complete-effect framing risked a cycle between effects root, journal
hash, and replay record. The revised graph commits semantic effects first,
journal second, and replay/commit metadata last.

## 7. Required implementation and proof evidence

- canonical bytes and independent vectors for every new committed object;
- dependency-cycle validation for hash preimage schemas;
- an independently written executable reference relation;
- differential accepted/rejected-state tests;
- compile-fail tests for sealed facts, plans, and retry descriptor authority;
- bounded arithmetic and state-machine proofs;
- concurrency interleaving exploration for replay races;
- deterministic crash injection at every persistence boundary;
- stateful fuzzing of governance, prepare, commit, timeout, resolve, and retry;
- mutation evidence tied to every semantic counterexample; and
- two independent approvals required by the Class E policy.

## 8. Residual gaps and non-claims

- RFC-0001 remains a draft.
- GPT-5.6's authoring-track review is not independent approval.
- Internal bounded evidence is finite, assumption-bound, and not publicly
  replayable here.
- No production Rust state machine refines this relation yet.
- No canonical ABI or journal hash is frozen.
- No hard-revocation recovery protocol exists.
- No external exact-once-delivery or production-readiness claim is made.

## 9. Requested independent-review outcome

After independently deriving the oracle, reviewers should select:

- `APPROVE`;
- `APPROVE_WITH_TRACKED_GAPS`;
- `REQUEST_CHANGES`;
- `BLOCK_AMBIGUOUS_SPEC`; or
- `BLOCK_UNSATISFIED_AUTHORITY_OBLIGATION`.

Current authoring-track outcome:

```text
REQUEST_INDEPENDENT_REVIEW
```
