# Policy activation v1 candidate architecture

**Status:** decision-ready candidate for `ZRM-TASK-001`; non-normative until RFC approval and independent review

**Author:** Dana Edwards  
**Drafting assistance:** GPT-5.6

## Purpose

Freeze the smallest policy-publication and activation state machine that later ZRM layers can consume without obtaining authority from caller-supplied policy objects, copied identifiers, fallback behavior, or mutable process state.

The associated executable oracle is `reference_models/policy_activation_v1.py`. It is a candidate semantic artifact, not implementation conformance evidence and not independent approval.

## Authority boundary

A future governed policy runtime may construct an authenticated snapshot only after checking governance authorization and durable state. The pure state machine in this packet receives an already-authorized command as a modeling precondition. It does not model a signature, quorum, governance proof, or trusted clock.

No application, verifier backend, open trait, deserializer, callback, subprocess exit status, or Boolean may construct a governed policy snapshot, policy activation capability, trusted validation context, policy-valid resource, verified fact, or commit plan.

## State

```text
PolicySnapshotV1Candidate {
  machine_id
  domain_id
  version
  parent_snapshot_id
  recognized_resource_kinds
  immutable_policy_contents
  policy_activation_instances
  creation_selection_by_kind
  applied_governance_operations
}
```

### Immutable content

```text
PolicyContent {
  content_id
  resource_kind_id
}
```

The reference model treats `content_id` as an opaque identity that already binds complete canonical content. Freezing those bytes is a separate Class E task.

### Activation instance

```text
PolicyActivation {
  activation_id
  content_id
  resource_kind_id
  generation
  status: Usable | HardRevoked
}
```

`activation_id` is not the policy-content identity. It identifies one activation event and binds the exact activation command digest.

### Explicit creation selection

```text
CreationSelection = Enabled(activation_id) | Suspended
```

Every recognized kind has exactly one row. Missing rows are malformed rather than implicitly suspended.

### Derived disposition

```text
if activation.status == HardRevoked:
    HardRevoked
else if selection[activation.kind] == Enabled(activation.id):
    CurrentCreation
else:
    AcceptedPredecessor
```

## Commands

### RegisterPolicyContent

Publishes inert immutable content. It does not select the policy and creates no activation capability.

### ActivatePolicy

Creates a new activation instance and selects it for creation. When another activation is current, the command must explicitly retire it as `AcceptedPredecessor` or `HardRevoked`. An absent retirement choice rejects. A retirement choice when creation is already suspended also rejects.

### SuspendCreation

Changes one kind to explicit `Suspended` and explicitly classifies the prior current activation as accepted predecessor or hard-revoked.

### HardRevokePredecessor

Hard-revokes one unselected predecessor. A current activation cannot be revoked through this command. The caller must replace or suspend it atomically.

## Resource-use matrix

| Effective disposition | Create | Consume | Reference |
| --- | --- | --- | --- |
| `CurrentCreation` | lifecycle-eligible | lifecycle-eligible | lifecycle-eligible |
| `AcceptedPredecessor` | reject | lifecycle-eligible | lifecycle-eligible |
| `HardRevoked` | reject | reject | reject |

“Lifecycle-eligible” means only that this activation stage accepts the role. Membership, freshness, resource-body validity, controller authority, logic, accounting, and commit remain separate mandatory checks.

## Identity derivation order

The candidate model uses model-only tokens:

```text
CommandDigest = H_model_command(complete command)

ActivationId = H_model_activation(
  machine_id,
  domain_id,
  parent_snapshot_id,
  CommandDigest,
  content_id,
  resource_kind_id,
  generation
)

SnapshotId = H_model_snapshot(complete successor payload)
```

Production byte tables and domain separators are deliberately not inferred from Python serialization.

## Deterministic precedence

1. malformed current snapshot;
2. malformed command;
3. exact replay or operation-ID equivocation;
4. stale parent snapshot;
5. stale scalar version;
6. unknown resource kind;
7. command-specific semantic error;
8. invalid derived successor.

Replay precedes freshness to support idempotent lost-ack recovery. For new work, the parent snapshot check precedes the scalar version because the parent commits the complete configuration rather than one counter.

## Invariants

1. Machine, domain, and recognized-kind set never change through this object.
2. Every recognized kind has exactly one explicit selection.
3. Every enabled selection points to a usable activation of the same kind.
4. Content is immutable and append-only.
5. Activation identity fields are immutable and activation records are append-only.
6. Per-kind activation generations are contiguous from one.
7. Hard revocation is terminal for an activation instance.
8. One operation ID binds one exact command digest.
9. Each success appends exactly one replay record.
10. Each success derives exactly the next version and parent link.
11. Each rejection returns the exact input snapshot.
12. Reactivating identical content creates a distinct activation identity.
13. A predecessor never authorizes creation.
14. A hard-revoked activation authorizes no role.

## Composition with later tasks

`ZRM-TASK-002` may construct a `TrustedValidationContextV1` only from an authenticated policy snapshot produced by a governed adapter. Final resources and verified facts should bind at least:

```text
policy_content_id
policy_activation_id
policy_snapshot_id or validation_context_hash
```

Content identity supports audit and deduplication. Activation identity supports revocation and non-resurrection. Snapshot/context identity supplies freshness and ordering.

The future durable implementation must linearize policy updates against the same composite machine head used by ordinary commits so a transition cannot validate under one policy snapshot and commit under another.

## Bounded reference evidence

The default deterministic explorer uses two kinds and two contents per kind. At depth three it checks:

```text
305 reached snapshots
304 applied transitions
271 rejected transitions
608 replay/equivocation probes
```

Every reached state is checked for local invariants. Every successful edge is checked for monotonicity and exact successor. Every rejection is checked as an exact no-op. This is finite evidence, not unbounded proof.

## Review decisions

The maintainer should explicitly accept, reject, or amend the three distinct identities; minimal stored status plus derived disposition; explicit selection row for every kind; inert content registration; closed command algebra; explicit retirement on replacement and suspension; atomic current revocation; terminal activation-instance revocation; exact successor versions; parent-linked snapshots; replay before freshness; command-digest-bound activation identity; lifecycle use matrix; and external anchoring requirement for any global non-equivocation claim.

## Non-claims

This packet does not define canonical protocol bytes, governance cryptography, authenticated snapshot loading, persistence, consensus, finality, complete policy migration, recovery of stranded resources, or production authority.
