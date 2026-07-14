"""Candidate reference semantics for ZRM policy publication and activation.

This module is non-authoritative. It defines a small pure state machine used to
review policy lifecycle choices before Rust authority code or canonical protocol
bytes exist. All SHA-256 values below are model-only test tokens.

The model deliberately separates immutable policy content identity, one governed
activation instance of that content, and one ordered policy snapshot. It
authenticates no governance act, constructs no trusted context, performs no I/O,
and grants no ZRM authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import TypeAlias


MODEL_SCHEMA = "zrm/reference-policy-activation-v1"
GENESIS_PARENT = "0" * 64
COMMAND_DOMAIN = "zrm:model-only:policy-command:v1"
ACTIVATION_DOMAIN = "zrm:model-only:policy-activation:v1"
SNAPSHOT_DOMAIN = "zrm:model-only:policy-snapshot:v1"
U64_MAX = (1 << 64) - 1
Identifier: TypeAlias = str
Digest: TypeAlias = str


class ActivationStatus(str, Enum):
    """Minimal stored lifecycle state for one activation instance."""

    USABLE = "usable"
    HARD_REVOKED = "hard_revoked"


class Disposition(str, Enum):
    """Disposition derived from status plus the creation-selection map."""

    CURRENT_CREATION = "current_creation"
    ACCEPTED_PREDECESSOR = "accepted_predecessor"
    HARD_REVOKED = "hard_revoked"


class Retirement(str, Enum):
    """Explicit treatment of a current activation when it is deselected."""

    ACCEPTED_PREDECESSOR = "accepted_predecessor"
    HARD_REVOKED = "hard_revoked"


class SelectionMode(str, Enum):
    """Closed creation-selection state for one recognized resource kind."""

    ENABLED = "enabled"
    SUSPENDED = "suspended"


class ResourceUse(str, Enum):
    """Lifecycle query made by later resource validation."""

    CREATE = "create"
    CONSUME = "consume"
    REFERENCE = "reference"


class CommandOutcome(str, Enum):
    """Outcome of one pure governance command."""

    APPLIED = "applied"
    ALREADY_APPLIED = "already_applied"
    REJECTED = "rejected"


class UseOutcome(str, Enum):
    """Outcome of a policy-disposition query."""

    ACCEPT = "accept"
    REJECT = "reject"


class Reason(str, Enum):
    """Stable model-local reasons, not protocol reject codes."""

    INVALID_SNAPSHOT = "invalid_snapshot"
    INVALID_COMMAND = "invalid_command"
    OPERATION_ID_REUSE = "operation_id_reuse"
    STALE_SNAPSHOT = "stale_snapshot"
    STALE_VERSION = "stale_version"
    UNKNOWN_KIND = "unknown_kind"
    CONTENT_ALREADY_REGISTERED = "content_already_registered"
    CONTENT_ID_COLLISION = "content_id_collision"
    UNKNOWN_CONTENT = "unknown_content"
    CONTENT_KIND_MISMATCH = "content_kind_mismatch"
    RETIREMENT_REQUIRED = "retirement_required"
    UNEXPECTED_RETIREMENT = "unexpected_retirement"
    CREATION_ALREADY_SUSPENDED = "creation_already_suspended"
    UNKNOWN_ACTIVATION = "unknown_activation"
    ACTIVATION_KIND_MISMATCH = "activation_kind_mismatch"
    CURRENT_REVOCATION_REQUIRES_ATOMIC_SELECTION_CHANGE = (
        "current_revocation_requires_atomic_selection_change"
    )
    ACTIVATION_ALREADY_HARD_REVOKED = "activation_already_hard_revoked"
    ACTIVATION_NOT_PREDECESSOR = "activation_not_predecessor"
    DERIVED_ACTIVATION_COLLISION = "derived_activation_collision"
    DERIVED_SNAPSHOT_INVALID = "derived_snapshot_invalid"
    USE_UNKNOWN_KIND = "use_unknown_kind"
    USE_UNKNOWN_ACTIVATION = "use_unknown_activation"
    USE_KIND_MISMATCH = "use_kind_mismatch"
    USE_HARD_REVOKED = "use_hard_revoked"
    USE_PREDECESSOR_CANNOT_CREATE = "use_predecessor_cannot_create"


@dataclass(frozen=True, order=True)
class PolicyContent:
    content_id: Identifier
    resource_kind_id: Identifier


@dataclass(frozen=True, order=True)
class PolicyActivation:
    activation_id: Digest
    content_id: Identifier
    resource_kind_id: Identifier
    generation: int
    status: ActivationStatus


@dataclass(frozen=True, order=True)
class CreationSelection:
    resource_kind_id: Identifier
    mode: SelectionMode
    activation_id: Digest | None


@dataclass(frozen=True, order=True)
class AppliedOperation:
    operation_id: Identifier
    command_digest: Digest
    applied_version: int


@dataclass(frozen=True)
class PolicySnapshot:
    machine_id: Identifier
    domain_id: Identifier
    version: int
    parent_snapshot_id: Digest
    snapshot_id: Digest
    recognized_kinds: tuple[Identifier, ...]
    contents: tuple[PolicyContent, ...]
    activations: tuple[PolicyActivation, ...]
    selections: tuple[CreationSelection, ...]
    applied_operations: tuple[AppliedOperation, ...]


@dataclass(frozen=True)
class RegisterContent:
    operation_id: Identifier
    expected_snapshot_id: Digest
    expected_version: int
    content_id: Identifier
    resource_kind_id: Identifier


@dataclass(frozen=True)
class Activate:
    operation_id: Identifier
    expected_snapshot_id: Digest
    expected_version: int
    content_id: Identifier
    resource_kind_id: Identifier
    retire_current_as: Retirement | None


@dataclass(frozen=True)
class Suspend:
    operation_id: Identifier
    expected_snapshot_id: Digest
    expected_version: int
    resource_kind_id: Identifier
    retire_current_as: Retirement


@dataclass(frozen=True)
class HardRevokePredecessor:
    operation_id: Identifier
    expected_snapshot_id: Digest
    expected_version: int
    resource_kind_id: Identifier
    activation_id: Digest


Command: TypeAlias = RegisterContent | Activate | Suspend | HardRevokePredecessor


@dataclass(frozen=True)
class CommandDecision:
    outcome: CommandOutcome
    snapshot: PolicySnapshot
    reason: Reason | None = None
    applied_version: int | None = None
    created_activation_id: Digest | None = None
    violations: tuple[str, ...] = ()


@dataclass(frozen=True)
class UseDecision:
    outcome: UseOutcome
    reason: Reason | None
    disposition: Disposition | None


def _identifier(value: object) -> bool:
    return type(value) is str and bool(value)


def _u64(value: object) -> bool:
    return type(value) is int and 0 <= value <= U64_MAX


def _digest(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _hash(domain: str, payload: object) -> Digest:
    encoded = json.dumps(
        {"domain": domain, "payload": payload},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _content_payload(value: PolicyContent) -> dict[str, object]:
    return {"content_id": value.content_id, "resource_kind_id": value.resource_kind_id}


def _activation_payload(value: PolicyActivation) -> dict[str, object]:
    return {
        "activation_id": value.activation_id,
        "content_id": value.content_id,
        "generation": value.generation,
        "resource_kind_id": value.resource_kind_id,
        "status": value.status.value,
    }


def _selection_payload(value: CreationSelection) -> dict[str, object]:
    return {
        "activation_id": value.activation_id,
        "mode": value.mode.value,
        "resource_kind_id": value.resource_kind_id,
    }


def _operation_payload(value: AppliedOperation) -> dict[str, object]:
    return {
        "applied_version": value.applied_version,
        "command_digest": value.command_digest,
        "operation_id": value.operation_id,
    }


def snapshot_payload(snapshot: PolicySnapshot) -> dict[str, object]:
    """Return every field committed by the model snapshot identity."""

    return {
        "schema": MODEL_SCHEMA,
        "machine_id": snapshot.machine_id,
        "domain_id": snapshot.domain_id,
        "version": snapshot.version,
        "parent_snapshot_id": snapshot.parent_snapshot_id,
        "recognized_kinds": list(snapshot.recognized_kinds),
        "contents": [_content_payload(value) for value in snapshot.contents],
        "activations": [_activation_payload(value) for value in snapshot.activations],
        "selections": [_selection_payload(value) for value in snapshot.selections],
        "applied_operations": [
            _operation_payload(value) for value in snapshot.applied_operations
        ],
    }


def derive_snapshot_id(snapshot: PolicySnapshot) -> Digest:
    """Derive the model-only identity of one snapshot payload."""

    return _hash(SNAPSHOT_DOMAIN, snapshot_payload(snapshot))


def _command_payload(command: Command) -> dict[str, object]:
    common: dict[str, object] = {
        "operation_id": command.operation_id,
        "expected_snapshot_id": command.expected_snapshot_id,
        "expected_version": command.expected_version,
        "resource_kind_id": command.resource_kind_id,
    }
    if type(command) is RegisterContent:
        common.update({"type": "register_content", "content_id": command.content_id})
    elif type(command) is Activate:
        common.update(
            {
                "type": "activate",
                "content_id": command.content_id,
                "retire_current_as": (
                    None
                    if command.retire_current_as is None
                    else command.retire_current_as.value
                ),
            }
        )
    elif type(command) is Suspend:
        common.update(
            {
                "type": "suspend",
                "retire_current_as": command.retire_current_as.value,
            }
        )
    elif type(command) is HardRevokePredecessor:
        common.update(
            {"type": "hard_revoke_predecessor", "activation_id": command.activation_id}
        )
    else:
        raise TypeError("unsupported command")
    return common


def command_digest(command: Command) -> Digest:
    """Bind one operation ID to the exact command, including retirement choice."""

    return _hash(COMMAND_DOMAIN, _command_payload(command))


def derive_activation_id(
    snapshot: PolicySnapshot, command: Activate, generation: int
) -> Digest:
    """Derive a fresh activation identity bound to the exact command digest."""

    return _hash(
        ACTIVATION_DOMAIN,
        {
            "machine_id": snapshot.machine_id,
            "domain_id": snapshot.domain_id,
            "parent_snapshot_id": snapshot.snapshot_id,
            "command_digest": command_digest(command),
            "content_id": command.content_id,
            "resource_kind_id": command.resource_kind_id,
            "generation": generation,
        },
    )


def _sort_contents(values):
    return tuple(sorted(values, key=lambda value: value.content_id))


def _sort_activations(values):
    return tuple(sorted(values, key=lambda value: value.activation_id))


def _sort_selections(values):
    return tuple(sorted(values, key=lambda value: value.resource_kind_id))


def _sort_operations(values):
    return tuple(sorted(values, key=lambda value: value.operation_id))


def _content_map(snapshot: PolicySnapshot) -> dict[Identifier, PolicyContent]:
    return {value.content_id: value for value in snapshot.contents}


def _activation_map(snapshot: PolicySnapshot) -> dict[Digest, PolicyActivation]:
    return {value.activation_id: value for value in snapshot.activations}


def _selection_map(snapshot: PolicySnapshot) -> dict[Identifier, CreationSelection]:
    return {value.resource_kind_id: value for value in snapshot.selections}


def _operation_map(snapshot: PolicySnapshot) -> dict[Identifier, AppliedOperation]:
    return {value.operation_id: value for value in snapshot.applied_operations}


def genesis(
    machine_id: Identifier,
    domain_id: Identifier,
    recognized_kinds: tuple[Identifier, ...],
    contents: tuple[PolicyContent, ...] = (),
) -> PolicySnapshot:
    """Create a checked genesis with explicit suspension for every kind."""

    kinds = tuple(sorted(recognized_kinds))
    candidate = PolicySnapshot(
        machine_id=machine_id,
        domain_id=domain_id,
        version=0,
        parent_snapshot_id=GENESIS_PARENT,
        snapshot_id="",
        recognized_kinds=kinds,
        contents=_sort_contents(contents),
        activations=(),
        selections=tuple(
            CreationSelection(kind, SelectionMode.SUSPENDED, None) for kind in kinds
        ),
        applied_operations=(),
    )
    candidate = replace(candidate, snapshot_id=derive_snapshot_id(candidate))
    violations = invariant_violations(candidate)
    if violations:
        raise ValueError("invalid genesis: " + "; ".join(violations))
    return candidate


def selected_activation(snapshot: PolicySnapshot, kind: Identifier) -> Digest | None:
    selection = _selection_map(snapshot).get(kind)
    if selection is None or selection.mode is SelectionMode.SUSPENDED:
        return None
    return selection.activation_id


def disposition(snapshot: PolicySnapshot, activation_id: Digest) -> Disposition | None:
    """Derive disposition without storing redundant current/predecessor state."""

    activation = _activation_map(snapshot).get(activation_id)
    if activation is None:
        return None
    if activation.status is ActivationStatus.HARD_REVOKED:
        return Disposition.HARD_REVOKED
    if selected_activation(snapshot, activation.resource_kind_id) == activation_id:
        return Disposition.CURRENT_CREATION
    return Disposition.ACCEPTED_PREDECESSOR


def invariant_violations(snapshot: PolicySnapshot) -> tuple[str, ...]:
    """Return all local snapshot invariant violations deterministically."""

    errors: list[str] = []
    if not _identifier(snapshot.machine_id):
        errors.append("invalid machine_id")
    if not _identifier(snapshot.domain_id):
        errors.append("invalid domain_id")
    if not _u64(snapshot.version):
        errors.append("invalid version")
    if not _digest(snapshot.parent_snapshot_id):
        errors.append("invalid parent_snapshot_id")
    if not _digest(snapshot.snapshot_id):
        errors.append("invalid snapshot_id")

    kinds = snapshot.recognized_kinds
    if kinds != tuple(sorted(kinds)) or len(kinds) != len(set(kinds)) or not kinds:
        errors.append("recognized kinds must be nonempty, sorted, and unique")
    if any(not _identifier(kind) for kind in kinds):
        errors.append("invalid resource kind")
    known_kinds = set(kinds)

    if snapshot.contents != _sort_contents(snapshot.contents):
        errors.append("contents not sorted")
    content_ids = [value.content_id for value in snapshot.contents]
    if len(content_ids) != len(set(content_ids)):
        errors.append("duplicate content_id")
    for value in snapshot.contents:
        if not _identifier(value.content_id):
            errors.append("invalid content_id")
        if value.resource_kind_id not in known_kinds:
            errors.append("content binds unknown kind")
    contents = _content_map(snapshot)

    if snapshot.activations != _sort_activations(snapshot.activations):
        errors.append("activations not sorted")
    activation_ids = [value.activation_id for value in snapshot.activations]
    if len(activation_ids) != len(set(activation_ids)):
        errors.append("duplicate activation_id")
    generations: dict[str, list[int]] = {kind: [] for kind in kinds}
    for value in snapshot.activations:
        if not _digest(value.activation_id):
            errors.append("invalid activation_id")
        content = contents.get(value.content_id)
        if content is None:
            errors.append("activation references unknown content")
        elif content.resource_kind_id != value.resource_kind_id:
            errors.append("activation/content kind mismatch")
        if value.resource_kind_id not in known_kinds:
            errors.append("activation binds unknown kind")
        if type(value.generation) is not int or value.generation <= 0:
            errors.append("invalid activation generation")
        else:
            generations[value.resource_kind_id].append(value.generation)
        if type(value.status) is not ActivationStatus:
            errors.append("invalid activation status")
    for kind, values in generations.items():
        if sorted(values) != list(range(1, len(values) + 1)):
            errors.append(f"non-contiguous generations for {kind}")

    if snapshot.selections != _sort_selections(snapshot.selections):
        errors.append("selections not sorted")
    if tuple(value.resource_kind_id for value in snapshot.selections) != kinds:
        errors.append("selections must cover every recognized kind exactly once")
    activations = _activation_map(snapshot)
    for value in snapshot.selections:
        if type(value.mode) is not SelectionMode:
            errors.append("invalid selection mode")
            continue
        if value.mode is SelectionMode.SUSPENDED:
            if value.activation_id is not None:
                errors.append("suspended selection carries activation")
            continue
        if value.activation_id is None:
            errors.append("enabled selection missing activation")
            continue
        activation = activations.get(value.activation_id)
        if activation is None:
            errors.append("selection references unknown activation")
        elif activation.resource_kind_id != value.resource_kind_id:
            errors.append("selection/activation kind mismatch")
        elif activation.status is ActivationStatus.HARD_REVOKED:
            errors.append("hard-revoked activation selected")

    if snapshot.applied_operations != _sort_operations(snapshot.applied_operations):
        errors.append("operations not sorted")
    operation_ids = [value.operation_id for value in snapshot.applied_operations]
    if len(operation_ids) != len(set(operation_ids)):
        errors.append("duplicate operation_id")
    versions: list[int] = []
    for value in snapshot.applied_operations:
        if not _identifier(value.operation_id):
            errors.append("invalid operation_id")
        if not _digest(value.command_digest):
            errors.append("invalid command_digest")
        if not _u64(value.applied_version) or value.applied_version == 0:
            errors.append("invalid applied_version")
        else:
            versions.append(value.applied_version)
    if sorted(versions) != list(range(1, snapshot.version + 1)):
        errors.append("applied versions are not exact successors")

    if _digest(snapshot.snapshot_id) and derive_snapshot_id(snapshot) != snapshot.snapshot_id:
        errors.append("snapshot_id mismatch")
    return tuple(errors)


def transition_violations(previous: PolicySnapshot, current: PolicySnapshot) -> tuple[str, ...]:
    """Return cross-snapshot monotonicity violations."""

    errors: list[str] = []
    if current.machine_id != previous.machine_id or current.domain_id != previous.domain_id:
        errors.append("machine or domain changed")
    if current.recognized_kinds != previous.recognized_kinds:
        errors.append("recognized kinds changed")
    if current.version != previous.version + 1:
        errors.append("version not exact successor")
    if current.parent_snapshot_id != previous.snapshot_id:
        errors.append("parent does not bind previous snapshot")

    old_contents = _content_map(previous)
    new_contents = _content_map(current)
    for content_id, old in old_contents.items():
        if new_contents.get(content_id) != old:
            errors.append("content changed or disappeared")

    old_activations = _activation_map(previous)
    new_activations = _activation_map(current)
    for activation_id, old in old_activations.items():
        new = new_activations.get(activation_id)
        if new is None:
            errors.append("activation disappeared")
            continue
        if (
            new.content_id != old.content_id
            or new.resource_kind_id != old.resource_kind_id
            or new.generation != old.generation
        ):
            errors.append("activation identity fields changed")
        if old.status is ActivationStatus.HARD_REVOKED and new.status is not ActivationStatus.HARD_REVOKED:
            errors.append("hard revocation reversed")

    old_operations = _operation_map(previous)
    new_operations = _operation_map(current)
    for operation_id, old in old_operations.items():
        if new_operations.get(operation_id) != old:
            errors.append("replay record changed or disappeared")
    if len(new_operations) != len(old_operations) + 1:
        errors.append("success did not append exactly one replay record")
    errors.extend(invariant_violations(current))
    return tuple(errors)


def _command_error(command: object) -> str | None:
    supported = (RegisterContent, Activate, Suspend, HardRevokePredecessor)
    if type(command) not in supported:
        return "unsupported command type"
    if not _identifier(command.operation_id):
        return "invalid operation_id"
    if not _digest(command.expected_snapshot_id):
        return "invalid expected_snapshot_id"
    if not _u64(command.expected_version):
        return "invalid expected_version"
    if not _identifier(command.resource_kind_id):
        return "invalid resource_kind_id"
    if type(command) in (RegisterContent, Activate) and not _identifier(command.content_id):
        return "invalid content_id"
    if type(command) is Activate:
        if command.retire_current_as is not None and type(command.retire_current_as) is not Retirement:
            return "invalid retirement"
    if type(command) is Suspend and type(command.retire_current_as) is not Retirement:
        return "invalid retirement"
    if type(command) is HardRevokePredecessor and not _digest(command.activation_id):
        return "invalid activation_id"
    return None


def _reject(snapshot: PolicySnapshot, reason: Reason, *violations: str) -> CommandDecision:
    return CommandDecision(
        CommandOutcome.REJECTED,
        snapshot,
        reason=reason,
        violations=tuple(violations),
    )


def _finish(
    previous: PolicySnapshot,
    command: Command,
    *,
    contents=None,
    activations=None,
    selections=None,
    created_activation_id: Digest | None = None,
) -> CommandDecision:
    version = previous.version + 1
    operations = _sort_operations(
        list(previous.applied_operations)
        + [AppliedOperation(command.operation_id, command_digest(command), version)]
    )
    candidate = PolicySnapshot(
        machine_id=previous.machine_id,
        domain_id=previous.domain_id,
        version=version,
        parent_snapshot_id=previous.snapshot_id,
        snapshot_id="",
        recognized_kinds=previous.recognized_kinds,
        contents=previous.contents if contents is None else _sort_contents(contents),
        activations=previous.activations if activations is None else _sort_activations(activations),
        selections=previous.selections if selections is None else _sort_selections(selections),
        applied_operations=operations,
    )
    candidate = replace(candidate, snapshot_id=derive_snapshot_id(candidate))
    violations = transition_violations(previous, candidate)
    if violations:
        return _reject(previous, Reason.DERIVED_SNAPSHOT_INVALID, *violations)
    return CommandDecision(
        CommandOutcome.APPLIED,
        candidate,
        applied_version=version,
        created_activation_id=created_activation_id,
    )


def _retire(
    activations: dict[Digest, PolicyActivation],
    activation_id: Digest,
    retirement: Retirement,
) -> None:
    if retirement is Retirement.HARD_REVOKED:
        activations[activation_id] = replace(
            activations[activation_id], status=ActivationStatus.HARD_REVOKED
        )


def apply(snapshot: PolicySnapshot, command: object) -> CommandDecision:
    """Apply one command with deterministic fail-closed precedence.

    Exact replay is checked before freshness so a lost acknowledgement can be
    classified after later progress without reapplying effects.
    """

    snapshot_errors = invariant_violations(snapshot)
    if snapshot_errors:
        return _reject(snapshot, Reason.INVALID_SNAPSHOT, *snapshot_errors)
    command_error = _command_error(command)
    if command_error is not None:
        return _reject(snapshot, Reason.INVALID_COMMAND, command_error)
    if type(command) not in (RegisterContent, Activate, Suspend, HardRevokePredecessor):
        return _reject(snapshot, Reason.INVALID_COMMAND, "unreachable command type")

    digest = command_digest(command)
    prior = _operation_map(snapshot).get(command.operation_id)
    if prior is not None:
        if prior.command_digest == digest:
            return CommandDecision(
                CommandOutcome.ALREADY_APPLIED,
                snapshot,
                applied_version=prior.applied_version,
            )
        return _reject(snapshot, Reason.OPERATION_ID_REUSE)

    if command.expected_snapshot_id != snapshot.snapshot_id:
        return _reject(snapshot, Reason.STALE_SNAPSHOT)
    if command.expected_version != snapshot.version:
        return _reject(snapshot, Reason.STALE_VERSION)
    if command.resource_kind_id not in set(snapshot.recognized_kinds):
        return _reject(snapshot, Reason.UNKNOWN_KIND)

    contents = _content_map(snapshot)
    activations = _activation_map(snapshot)
    selections = _selection_map(snapshot)

    if type(command) is RegisterContent:
        existing = contents.get(command.content_id)
        if existing is not None:
            if existing.resource_kind_id != command.resource_kind_id:
                return _reject(snapshot, Reason.CONTENT_ID_COLLISION)
            return _reject(snapshot, Reason.CONTENT_ALREADY_REGISTERED)
        contents[command.content_id] = PolicyContent(
            command.content_id, command.resource_kind_id
        )
        return _finish(snapshot, command, contents=tuple(contents.values()))

    if type(command) is Activate:
        content = contents.get(command.content_id)
        if content is None:
            return _reject(snapshot, Reason.UNKNOWN_CONTENT)
        if content.resource_kind_id != command.resource_kind_id:
            return _reject(snapshot, Reason.CONTENT_KIND_MISMATCH)
        current = selected_activation(snapshot, command.resource_kind_id)
        if current is None and command.retire_current_as is not None:
            return _reject(snapshot, Reason.UNEXPECTED_RETIREMENT)
        if current is not None and command.retire_current_as is None:
            return _reject(snapshot, Reason.RETIREMENT_REQUIRED)
        if current is not None:
            retirement = command.retire_current_as
            if retirement is None:
                return _reject(snapshot, Reason.RETIREMENT_REQUIRED)
            _retire(activations, current, retirement)
        generation = 1 + max(
            (
                value.generation
                for value in activations.values()
                if value.resource_kind_id == command.resource_kind_id
            ),
            default=0,
        )
        activation_id = derive_activation_id(snapshot, command, generation)
        if activation_id in activations:
            return _reject(snapshot, Reason.DERIVED_ACTIVATION_COLLISION)
        activations[activation_id] = PolicyActivation(
            activation_id,
            command.content_id,
            command.resource_kind_id,
            generation,
            ActivationStatus.USABLE,
        )
        selections[command.resource_kind_id] = CreationSelection(
            command.resource_kind_id, SelectionMode.ENABLED, activation_id
        )
        return _finish(
            snapshot,
            command,
            activations=tuple(activations.values()),
            selections=tuple(selections.values()),
            created_activation_id=activation_id,
        )

    if type(command) is Suspend:
        current = selected_activation(snapshot, command.resource_kind_id)
        if current is None:
            return _reject(snapshot, Reason.CREATION_ALREADY_SUSPENDED)
        _retire(activations, current, command.retire_current_as)
        selections[command.resource_kind_id] = CreationSelection(
            command.resource_kind_id, SelectionMode.SUSPENDED, None
        )
        return _finish(
            snapshot,
            command,
            activations=tuple(activations.values()),
            selections=tuple(selections.values()),
        )

    if type(command) is not HardRevokePredecessor:
        return _reject(snapshot, Reason.INVALID_COMMAND, "unreachable dispatch")
    target = activations.get(command.activation_id)
    if target is None:
        return _reject(snapshot, Reason.UNKNOWN_ACTIVATION)
    if target.resource_kind_id != command.resource_kind_id:
        return _reject(snapshot, Reason.ACTIVATION_KIND_MISMATCH)
    target_disposition = disposition(snapshot, command.activation_id)
    if target_disposition is Disposition.CURRENT_CREATION:
        return _reject(
            snapshot, Reason.CURRENT_REVOCATION_REQUIRES_ATOMIC_SELECTION_CHANGE
        )
    if target_disposition is Disposition.HARD_REVOKED:
        return _reject(snapshot, Reason.ACTIVATION_ALREADY_HARD_REVOKED)
    if target_disposition is not Disposition.ACCEPTED_PREDECESSOR:
        return _reject(snapshot, Reason.ACTIVATION_NOT_PREDECESSOR)
    activations[command.activation_id] = replace(
        target, status=ActivationStatus.HARD_REVOKED
    )
    return _finish(snapshot, command, activations=tuple(activations.values()))


def decide_use(
    snapshot: PolicySnapshot,
    resource_kind_id: Identifier,
    activation_id: Digest,
    use: ResourceUse,
) -> UseDecision:
    """Decide lifecycle permission only; all other resource checks remain open."""

    if resource_kind_id not in set(snapshot.recognized_kinds):
        return UseDecision(UseOutcome.REJECT, Reason.USE_UNKNOWN_KIND, None)
    activation = _activation_map(snapshot).get(activation_id)
    if activation is None:
        return UseDecision(UseOutcome.REJECT, Reason.USE_UNKNOWN_ACTIVATION, None)
    if activation.resource_kind_id != resource_kind_id:
        return UseDecision(UseOutcome.REJECT, Reason.USE_KIND_MISMATCH, None)
    current = disposition(snapshot, activation_id)
    if current is None:
        return UseDecision(UseOutcome.REJECT, Reason.USE_UNKNOWN_ACTIVATION, None)
    if current is Disposition.HARD_REVOKED:
        return UseDecision(UseOutcome.REJECT, Reason.USE_HARD_REVOKED, current)
    if use is ResourceUse.CREATE and current is Disposition.ACCEPTED_PREDECESSOR:
        return UseDecision(
            UseOutcome.REJECT, Reason.USE_PREDECESSOR_CANNOT_CREATE, current
        )
    return UseDecision(UseOutcome.ACCEPT, None, current)


def altered_same_operation(command: Command) -> Command:
    """Return a constructionally different command with the same operation ID."""

    if type(command) is RegisterContent:
        return replace(command, content_id=command.content_id + "-different")
    if type(command) is Activate:
        return replace(command, content_id=command.content_id + "-different")
    if type(command) is Suspend:
        retirement = (
            Retirement.HARD_REVOKED
            if command.retire_current_as is Retirement.ACCEPTED_PREDECESSOR
            else Retirement.ACCEPTED_PREDECESSOR
        )
        return replace(command, retire_current_as=retirement)
    if type(command) is HardRevokePredecessor:
        first = "0" if command.activation_id[0] != "0" else "1"
        return replace(command, activation_id=first + command.activation_id[1:])
    raise TypeError("unsupported command")


__all__ = [
    "ActivationStatus",
    "Disposition",
    "Retirement",
    "SelectionMode",
    "ResourceUse",
    "CommandOutcome",
    "UseOutcome",
    "Reason",
    "PolicyContent",
    "PolicyActivation",
    "CreationSelection",
    "AppliedOperation",
    "PolicySnapshot",
    "RegisterContent",
    "Activate",
    "Suspend",
    "HardRevokePredecessor",
    "CommandDecision",
    "UseDecision",
    "snapshot_payload",
    "derive_snapshot_id",
    "command_digest",
    "derive_activation_id",
    "genesis",
    "selected_activation",
    "disposition",
    "invariant_violations",
    "transition_violations",
    "apply",
    "decide_use",
    "altered_same_operation",
]
