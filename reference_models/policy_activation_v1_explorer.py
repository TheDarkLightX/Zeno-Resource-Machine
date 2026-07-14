"""Deterministic bounded explorer for the policy-activation reference model.

This is a force multiplier, not a proof. It enumerates a closed command alphabet,
checks every reached snapshot, checks every successful edge, verifies rejection
is an exact no-op, and probes exact replay plus operation-ID equivocation.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace

from reference_models.policy_activation_v1 import (
    Activate,
    ActivationStatus,
    Command,
    CommandOutcome,
    Disposition,
    HardRevokePredecessor,
    PolicyContent,
    PolicySnapshot,
    Reason,
    Retirement,
    Suspend,
    altered_same_operation,
    apply,
    disposition,
    genesis,
    invariant_violations,
    selected_activation,
    transition_violations,
)


@dataclass(frozen=True)
class ExplorationStats:
    states: int
    applied: int
    rejected: int
    replay_checks: int
    max_depth: int


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _operation(snapshot: PolicySnapshot, index: int) -> str:
    return f"explore-{snapshot.version + 1}-{index}-{snapshot.snapshot_id[:12]}"


def candidate_commands(snapshot: PolicySnapshot) -> tuple[Command, ...]:
    """Return deterministic positive and negative commands for one snapshot."""

    commands: list[Command] = []
    index = 0
    for kind in snapshot.recognized_kinds:
        current = selected_activation(snapshot, kind)
        content_ids = tuple(
            value.content_id
            for value in snapshot.contents
            if value.resource_kind_id == kind
        )
        for content_id in content_ids:
            retirements = (
                (
                    Retirement.ACCEPTED_PREDECESSOR,
                    Retirement.HARD_REVOKED,
                    None,
                )
                if current is not None
                else (None, Retirement.ACCEPTED_PREDECESSOR)
            )
            for retirement in retirements:
                commands.append(
                    Activate(
                        _operation(snapshot, index),
                        snapshot.snapshot_id,
                        snapshot.version,
                        content_id,
                        kind,
                        retirement,
                    )
                )
                index += 1
        if current is None:
            commands.append(
                Suspend(
                    _operation(snapshot, index),
                    snapshot.snapshot_id,
                    snapshot.version,
                    kind,
                    Retirement.ACCEPTED_PREDECESSOR,
                )
            )
            index += 1
        else:
            for retirement in Retirement:
                commands.append(
                    Suspend(
                        _operation(snapshot, index),
                        snapshot.snapshot_id,
                        snapshot.version,
                        kind,
                        retirement,
                    )
                )
                index += 1
        for activation in snapshot.activations:
            if activation.resource_kind_id == kind:
                commands.append(
                    HardRevokePredecessor(
                        _operation(snapshot, index),
                        snapshot.snapshot_id,
                        snapshot.version,
                        kind,
                        activation.activation_id,
                    )
                )
                index += 1
    if commands:
        commands.append(
            replace(
                commands[0],
                operation_id=_operation(snapshot, index),
                expected_snapshot_id="f" * 64,
            )
        )
    return tuple(commands)


def explore(max_depth: int = 3, max_states: int = 20_000) -> ExplorationStats:
    """Explore two kinds and two contents per kind to a fixed depth."""

    if type(max_depth) is not int or max_depth < 0:
        raise ValueError("max_depth must be a nonnegative exact integer")
    if type(max_states) is not int or max_states <= 0:
        raise ValueError("max_states must be a positive exact integer")

    initial = genesis(
        "machine-a",
        "domain-a",
        ("kind-a", "kind-b"),
        (
            PolicyContent("content-a1", "kind-a"),
            PolicyContent("content-a2", "kind-a"),
            PolicyContent("content-b1", "kind-b"),
            PolicyContent("content-b2", "kind-b"),
        ),
    )
    queue: deque[tuple[PolicySnapshot, int]] = deque([(initial, 0)])
    reached: dict[str, PolicySnapshot] = {initial.snapshot_id: initial}
    applied_count = 0
    rejected_count = 0
    replay_count = 0

    while queue:
        snapshot, depth = queue.popleft()
        _require(not invariant_violations(snapshot), "reached invalid snapshot")
        if depth == max_depth:
            continue
        for command in candidate_commands(snapshot):
            decision = apply(snapshot, command)
            if decision.outcome is CommandOutcome.REJECTED:
                rejected_count += 1
                _require(decision.snapshot is snapshot, "rejection changed snapshot")
                continue
            _require(
                decision.outcome is CommandOutcome.APPLIED,
                "unknown command outcome",
            )
            applied_count += 1
            _require(
                not transition_violations(snapshot, decision.snapshot),
                "successful edge violates transition invariants",
            )

            replay = apply(decision.snapshot, command)
            replay_count += 1
            _require(
                replay.outcome is CommandOutcome.ALREADY_APPLIED,
                "exact replay was not idempotent",
            )
            _require(replay.snapshot is decision.snapshot, "replay changed snapshot")

            equivocation = apply(decision.snapshot, altered_same_operation(command))
            replay_count += 1
            _require(
                equivocation.outcome is CommandOutcome.REJECTED,
                "operation-ID equivocation was not rejected",
            )
            _require(
                equivocation.reason is Reason.OPERATION_ID_REUSE,
                "operation-ID equivocation used wrong reason",
            )
            _require(
                equivocation.snapshot is decision.snapshot,
                "operation-ID equivocation changed snapshot",
            )

            if decision.snapshot.snapshot_id not in reached:
                if len(reached) >= max_states:
                    raise RuntimeError(
                        f"exploration exceeded max_states={max_states}"
                    )
                reached[decision.snapshot.snapshot_id] = decision.snapshot
                queue.append((decision.snapshot, depth + 1))

    for snapshot in reached.values():
        for activation in snapshot.activations:
            if activation.status is ActivationStatus.HARD_REVOKED:
                _require(
                    disposition(snapshot, activation.activation_id)
                    is Disposition.HARD_REVOKED,
                    "hard-revoked activation lost tombstone disposition",
                )

    return ExplorationStats(
        len(reached),
        applied_count,
        rejected_count,
        replay_count,
        max_depth,
    )


def main() -> int:
    stats = explore()
    print(
        "policy-activation exploration passed: "
        f"states={stats.states}, applied={stats.applied}, "
        f"rejected={stats.rejected}, replay_checks={stats.replay_checks}, "
        f"max_depth={stats.max_depth}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
