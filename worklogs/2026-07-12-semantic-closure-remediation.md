# Work log: semantic-closure remediation

**Change class:** E
**Status:** implementation in progress; requires independent review

## Goal

Replace the rejected semantic-closure draft with a project-neutral public
package that closes the identified policy, retry, commit-effect, durability,
and recursive-position gaps without changing implemented Rust authority,
canonical bytes, or production claims.

## Scope

Affected public surfaces:

- policy disposition and emergency creation suspension;
- policy-update state-root derivation;
- replay lookup and commit linearization;
- lost-acknowledgement and indeterminate-outcome recovery;
- acyclic semantic-effect, journal, replay-record, and atomic-write binding;
- recursive leaf position authority;
- the first message-free and carry-free recursive profile;
- machine-readable semantic decisions, review packets, and refinement
  obligations.

No Rust behavior, stable codec, hash preimage, state root, verifier dispatch,
database adapter, or release profile changes in this work package.

## Typed statements and logical APIs

The draft will define these logical boundaries:

```text
CreationSelectionV1 = Enabled(CurrentPolicyId) | Suspended

SemanticEffectsV1
  -> SemanticEffectsRoot
  -> JournalPayloadV2
  -> JournalHash
  -> TransitionReplayRecordV1
  -> AtomicCommitBundleV1

RetryDescriptorV1
CommitOutcomeV1 = NewlyCommitted | AlreadyCommitted | OutcomeUnknown

SerializedGlobalPositionV1 = pre_state_version
```

Each identity remains a logical schema until a separate Class E byte-table and
independent-vector change freezes its encoding.

## Authority boundary

- Governance supplies the authenticated policy snapshot and may suspend
  creation without selecting a replacement policy.
- Only a private `CommitPlan` may authorize a new write.
- Replay resolution is a read-only classification over an untrusted exact
  retry descriptor and cannot authorize new effects.
- Replay lookup, replay comparison, snapshot comparison, and replay insertion
  share one linearizable critical section.
- Recursive position is derived from an authenticated accepted journal under
  the serialized profile; callers do not assign it.

## Invariants

1. A compromised current creation policy can be hard-revoked into a
   creation-suspended state atomically.
2. Policy update derives a new machine-state root and monotonically increasing
   state version; rollback never recreates an old authority tuple.
3. An exact replay returns the existing accepted result without a write.
4. The same transition ID with different journal/effect identity is always a
   conflict, including under races.
5. A storage result that may have committed is reported as `OutcomeUnknown`,
   never as a confirmed no-op.
6. Effect and metadata commitments form a directed acyclic dependency graph.
7. Every atomic write is either journal-bound semantic state or deterministic
   commit metadata derived after the journal hash.
8. The first recursive profile derives positions from state versions and has
   named empty message/carry commitments.
9. All public artifacts remain application- and internal-tool-neutral.

## Disaster states

- current policy cannot be revoked during an emergency;
- two replay attempts both observe absence before one commits;
- exact retry returns stale while conflicting replay escapes conflict
  classification;
- lost response consumes the only retry authority object;
- uncertain durability is reported as rejection;
- effects root depends on a replay record that depends on the effects root;
- accepted journal, admission reference, or state metadata escapes the declared
  atomic bundle;
- caller assigns two positions to the same accepted journal history;
- recursive summary claims message/carry composition before defining it;
- public history discloses internal project or tooling names.

## Compatibility and migration

- Existing v0.1 resource bytes remain unchanged.
- The complete-effect journal requires a new journal schema; v1 and v2 cannot
  substitute.
- Existing pre-alpha commit APIs remain non-authoritative.
- The rejected public draft branch is not a migration source and must not be
  merged.
- Policy suspension and retry outcomes are new v0.2 logical semantics.

## Tests and formal obligations

Before publication:

- bounded model of current-policy suspension and replacement;
- bounded two-attempt replay-linearization model with exact and conflicting
  attempts;
- bounded lost-acknowledgement/unknown-outcome resolution model;
- bounded serialized-position and recursive-fold model;
- named mutants for missing suspension, replay recheck, unknown resolution,
  and position derivation;
- two-solver, deterministic, fail-closed replay of every positive model;
- public privacy scan and repository gates;
- later Loom, crash injection, Kani, differential Rust, and parameterized proof
  obligations remain required before implementation promotion.

## Dependencies and resources

No dependency change. Models use small finite enums, booleans, and bounded
integers. New public logical objects must receive explicit byte, count, and
storage ceilings in the future canonical-schema RFC.

## Design-choice review

**Design forces:** emergency containment, exact retry classification,
indeterminate storage outcomes, acyclic identity derivation, canonical recursive
order, and public confidentiality.

**Pattern selected:** sealed commit capability plus a separate read-only retry
descriptor; explicit sum types for creation state and commit outcome; layered
acyclic commitment descriptors; derived serialized position.

**Invalid states prevented:** caller-assigned retry authority, simultaneous
enabled-and-suspended creation, confirmed rejection after uncertain durability,
self-referential effect commitments, and caller-selected recursive position.

**Extension point:** later sharded ordering and message-enabled composition use
new profile IDs. The first profile remains closed and serialized.

**Alternatives rejected:** mandatory immediate replacement on revocation,
replay lookup before the transaction, cloning or serializing `CommitPlan`,
embedding commit metadata recursively in its own effects root, arbitrary
position certificates in the first profile, and unspecified message algebra.

**Pattern-specific failure modes:** retry descriptor disclosure, transaction
isolation weaker than declared, storage adapters hiding unknown outcomes, and
future profiles reusing serialized-position semantics incorrectly.

**Enforcement and tests:** exact decision tables, bounded state-machine models,
mutants, future typestate APIs, transaction schedule tests, crash injection,
and independent Class E review.

**Technical AI-review status:** remediation design reviewed against the ZRM
authority, effect, failure, compatibility, and evidence topologies; independent
human approvals remain required.

## Non-claims

- no approved protocol decision before maintainer and independent review;
- no implemented commit, storage, policy registry, or recursive guest;
- no canonical bytes or hashes for the new objects;
- no proof of database, operating-system, hardware, or proof-system behavior;
- no arbitrary recursion, message composition, external exact-once delivery,
  privacy, finality, or production readiness.
