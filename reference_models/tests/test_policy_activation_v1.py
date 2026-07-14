"""Independent tests for the candidate policy-activation reference model."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest

from reference_models.policy_activation_v1 import (
    Activate,
    ActivationStatus,
    AppliedOperation,
    CommandOutcome,
    Disposition,
    HardRevokePredecessor,
    PolicyContent,
    Reason,
    RegisterContent,
    ResourceUse,
    Retirement,
    Suspend,
    UseOutcome,
    altered_same_operation,
    apply,
    command_digest,
    decide_use,
    derive_activation_id,
    derive_snapshot_id,
    disposition,
    genesis,
    invariant_violations,
    selected_activation,
    transition_violations,
)
from reference_models.policy_activation_v1_explorer import explore


KIND_A = "kind-a"
KIND_B = "kind-b"
CONTENT_A1 = "content-a1"
CONTENT_A2 = "content-a2"
CONTENT_B1 = "content-b1"
CONTENT_B2 = "content-b2"
COUNTEREXAMPLES = (
    Path(__file__).resolve().parents[1]
    / "policy_activation_v1_counterexamples.json"
)


def initial(*, with_contents: bool = True):
    contents = (
        PolicyContent(CONTENT_A1, KIND_A),
        PolicyContent(CONTENT_A2, KIND_A),
        PolicyContent(CONTENT_B1, KIND_B),
        PolicyContent(CONTENT_B2, KIND_B),
    ) if with_contents else ()
    return genesis("machine-a", "domain-a", (KIND_A, KIND_B), contents)


def activate(snapshot, operation_id, kind, content, retirement):
    command = Activate(
        operation_id,
        snapshot.snapshot_id,
        snapshot.version,
        content,
        kind,
        retirement,
    )
    decision = apply(snapshot, command)
    if decision.outcome is not CommandOutcome.APPLIED:
        raise AssertionError(decision)
    if decision.created_activation_id is None:
        raise AssertionError("activation did not return an identity")
    return decision.snapshot, decision.created_activation_id, command


def suspend(snapshot, operation_id, kind, retirement):
    command = Suspend(
        operation_id,
        snapshot.snapshot_id,
        snapshot.version,
        kind,
        retirement,
    )
    decision = apply(snapshot, command)
    if decision.outcome is not CommandOutcome.APPLIED:
        raise AssertionError(decision)
    return decision.snapshot, command


class RepresentationTests(unittest.TestCase):
    def test_genesis_explicitly_suspends_every_kind(self) -> None:
        snapshot = initial()
        self.assertFalse(invariant_violations(snapshot))
        self.assertIsNone(selected_activation(snapshot, KIND_A))
        self.assertIsNone(selected_activation(snapshot, KIND_B))

    def test_registering_content_creates_no_activation(self) -> None:
        snapshot = initial(with_contents=False)
        command = RegisterContent(
            "register-a1",
            snapshot.snapshot_id,
            snapshot.version,
            CONTENT_A1,
            KIND_A,
        )
        decision = apply(snapshot, command)
        self.assertIs(decision.outcome, CommandOutcome.APPLIED)
        self.assertEqual(
            decision.snapshot.contents,
            (PolicyContent(CONTENT_A1, KIND_A),),
        )
        self.assertFalse(decision.snapshot.activations)
        self.assertIsNone(selected_activation(decision.snapshot, KIND_A))

    def test_current_and_predecessor_are_derived_from_minimal_state(self) -> None:
        first, a1, _ = activate(initial(), "a1", KIND_A, CONTENT_A1, None)
        second, a2, _ = activate(
            first,
            "a2",
            KIND_A,
            CONTENT_A2,
            Retirement.ACCEPTED_PREDECESSOR,
        )
        self.assertIs(disposition(second, a1), Disposition.ACCEPTED_PREDECESSOR)
        self.assertIs(disposition(second, a2), Disposition.CURRENT_CREATION)
        statuses = {
            value.activation_id: value.status for value in second.activations
        }
        self.assertIs(statuses[a1], ActivationStatus.USABLE)
        self.assertIs(statuses[a2], ActivationStatus.USABLE)

    def test_reactivation_of_identical_content_gets_fresh_identity(self) -> None:
        first, a1, _ = activate(initial(), "a1", KIND_A, CONTENT_A1, None)
        stopped, _ = suspend(
            first, "s1", KIND_A, Retirement.HARD_REVOKED
        )
        current, a2, _ = activate(
            stopped, "a2", KIND_A, CONTENT_A1, None
        )
        self.assertNotEqual(a1, a2)
        self.assertIs(disposition(current, a1), Disposition.HARD_REVOKED)
        self.assertIs(disposition(current, a2), Disposition.CURRENT_CREATION)

    def test_activation_identity_binds_exact_command_digest(self) -> None:
        snapshot, _, _ = activate(initial(), "a1", KIND_A, CONTENT_A1, None)
        predecessor = Activate(
            "a2",
            snapshot.snapshot_id,
            snapshot.version,
            CONTENT_A2,
            KIND_A,
            Retirement.ACCEPTED_PREDECESSOR,
        )
        revoked = replace(
            predecessor, retire_current_as=Retirement.HARD_REVOKED
        )
        self.assertNotEqual(command_digest(predecessor), command_digest(revoked))
        self.assertNotEqual(
            derive_activation_id(snapshot, predecessor, 2),
            derive_activation_id(snapshot, revoked, 2),
        )

    def test_content_identifier_cannot_change_bound_kind(self) -> None:
        snapshot = initial(with_contents=False)
        first = RegisterContent(
            "c1", snapshot.snapshot_id, snapshot.version, "shared", KIND_A
        )
        registered = apply(snapshot, first).snapshot
        copied = RegisterContent(
            "c2", registered.snapshot_id, registered.version, "shared", KIND_B
        )
        decision = apply(registered, copied)
        self.assertIs(decision.reason, Reason.CONTENT_ID_COLLISION)
        self.assertIs(decision.snapshot, registered)


class DispositionTests(unittest.TestCase):
    def test_current_allows_all_lifecycle_roles(self) -> None:
        snapshot, activation_id, _ = activate(
            initial(), "a1", KIND_A, CONTENT_A1, None
        )
        for use in ResourceUse:
            with self.subTest(use=use):
                decision = decide_use(snapshot, KIND_A, activation_id, use)
                self.assertIs(decision.outcome, UseOutcome.ACCEPT)
                self.assertIs(
                    decision.disposition, Disposition.CURRENT_CREATION
                )

    def test_predecessor_cannot_create_but_can_be_consumed_or_referenced(self) -> None:
        first, predecessor, _ = activate(
            initial(), "a1", KIND_A, CONTENT_A1, None
        )
        second, _, _ = activate(
            first,
            "a2",
            KIND_A,
            CONTENT_A2,
            Retirement.ACCEPTED_PREDECESSOR,
        )
        create = decide_use(second, KIND_A, predecessor, ResourceUse.CREATE)
        self.assertIs(create.outcome, UseOutcome.REJECT)
        self.assertIs(create.reason, Reason.USE_PREDECESSOR_CANNOT_CREATE)
        for use in (ResourceUse.CONSUME, ResourceUse.REFERENCE):
            with self.subTest(use=use):
                self.assertIs(
                    decide_use(second, KIND_A, predecessor, use).outcome,
                    UseOutcome.ACCEPT,
                )

    def test_hard_revocation_blocks_every_role(self) -> None:
        first, old, _ = activate(initial(), "a1", KIND_A, CONTENT_A1, None)
        second, _, _ = activate(
            first, "a2", KIND_A, CONTENT_A2, Retirement.HARD_REVOKED
        )
        for use in ResourceUse:
            with self.subTest(use=use):
                decision = decide_use(second, KIND_A, old, use)
                self.assertIs(decision.outcome, UseOutcome.REJECT)
                self.assertIs(decision.reason, Reason.USE_HARD_REVOKED)

    def test_suspension_has_no_creation_fallback(self) -> None:
        first, old, _ = activate(initial(), "a1", KIND_A, CONTENT_A1, None)
        stopped, _ = suspend(
            first, "s1", KIND_A, Retirement.ACCEPTED_PREDECESSOR
        )
        self.assertIsNone(selected_activation(stopped, KIND_A))
        self.assertIs(
            decide_use(stopped, KIND_A, old, ResourceUse.CREATE).reason,
            Reason.USE_PREDECESSOR_CANNOT_CREATE,
        )
        self.assertIs(
            decide_use(stopped, KIND_A, old, ResourceUse.CONSUME).outcome,
            UseOutcome.ACCEPT,
        )

    def test_current_revocation_requires_atomic_replacement_or_suspension(self) -> None:
        snapshot, current, _ = activate(
            initial(), "a1", KIND_A, CONTENT_A1, None
        )
        command = HardRevokePredecessor(
            "r1",
            snapshot.snapshot_id,
            snapshot.version,
            KIND_A,
            current,
        )
        decision = apply(snapshot, command)
        self.assertIs(
            decision.reason,
            Reason.CURRENT_REVOCATION_REQUIRES_ATOMIC_SELECTION_CHANGE,
        )
        self.assertIs(decision.snapshot, snapshot)

    def test_replacement_requires_explicit_retirement(self) -> None:
        snapshot, _, _ = activate(initial(), "a1", KIND_A, CONTENT_A1, None)
        ambiguous = Activate(
            "a2",
            snapshot.snapshot_id,
            snapshot.version,
            CONTENT_A2,
            KIND_A,
            None,
        )
        decision = apply(snapshot, ambiguous)
        self.assertIs(decision.reason, Reason.RETIREMENT_REQUIRED)
        self.assertIs(decision.snapshot, snapshot)

    def test_hard_revocation_is_terminal(self) -> None:
        first, old, _ = activate(initial(), "a1", KIND_A, CONTENT_A1, None)
        second, _, _ = activate(
            first,
            "a2",
            KIND_A,
            CONTENT_A2,
            Retirement.ACCEPTED_PREDECESSOR,
        )
        revoke = HardRevokePredecessor(
            "r1", second.snapshot_id, second.version, KIND_A, old
        )
        revoked = apply(second, revoke)
        self.assertIs(revoked.outcome, CommandOutcome.APPLIED)
        again = HardRevokePredecessor(
            "r2",
            revoked.snapshot.snapshot_id,
            revoked.snapshot.version,
            KIND_A,
            old,
        )
        decision = apply(revoked.snapshot, again)
        self.assertIs(
            decision.reason, Reason.ACTIVATION_ALREADY_HARD_REVOKED
        )
        self.assertIs(decision.snapshot, revoked.snapshot)


class ReplayAndHistoryTests(unittest.TestCase):
    def test_success_is_exact_successor_and_parent_linked(self) -> None:
        previous = initial()
        current, _, _ = activate(
            previous, "a1", KIND_A, CONTENT_A1, None
        )
        self.assertEqual(current.version, previous.version + 1)
        self.assertEqual(current.parent_snapshot_id, previous.snapshot_id)
        self.assertFalse(transition_violations(previous, current))

    def test_reject_returns_exact_input_snapshot(self) -> None:
        snapshot = initial()
        command = Activate(
            "stale", "f" * 64, snapshot.version, CONTENT_A1, KIND_A, None
        )
        decision = apply(snapshot, command)
        self.assertIs(decision.reason, Reason.STALE_SNAPSHOT)
        self.assertIs(decision.snapshot, snapshot)

    def test_snapshot_freshness_precedes_scalar_version(self) -> None:
        snapshot = initial()
        command = Activate(
            "stale",
            "f" * 64,
            snapshot.version + 1,
            CONTENT_A1,
            KIND_A,
            None,
        )
        self.assertIs(apply(snapshot, command).reason, Reason.STALE_SNAPSHOT)

    def test_exact_replay_is_classified_before_freshness_after_progress(self) -> None:
        first, _, original = activate(
            initial(), "a1", KIND_A, CONTENT_A1, None
        )
        later, _, _ = activate(first, "b1", KIND_B, CONTENT_B1, None)
        replay = apply(later, original)
        self.assertIs(replay.outcome, CommandOutcome.ALREADY_APPLIED)
        self.assertIs(replay.snapshot, later)
        self.assertEqual(replay.applied_version, 1)

    def test_operation_id_equivocation_rejects(self) -> None:
        snapshot, _, original = activate(
            initial(), "a1", KIND_A, CONTENT_A1, None
        )
        decision = apply(snapshot, altered_same_operation(original))
        self.assertIs(decision.reason, Reason.OPERATION_ID_REUSE)
        self.assertIs(decision.snapshot, snapshot)

    def test_next_version_is_not_a_command_field(self) -> None:
        snapshot = initial()
        command = Activate(
            "a1", snapshot.snapshot_id, snapshot.version, CONTENT_A1, KIND_A, None
        )
        self.assertNotIn("next_version", command.__dataclass_fields__)
        self.assertEqual(apply(snapshot, command).snapshot.version, 1)


class InvariantMutationTests(unittest.TestCase):
    def test_snapshot_identity_mutation_is_detected(self) -> None:
        snapshot = initial()
        self.assertIn(
            "snapshot_id mismatch",
            invariant_violations(replace(snapshot, snapshot_id="f" * 64)),
        )

    def test_selected_hard_revoked_activation_is_detected(self) -> None:
        snapshot, activation_id, _ = activate(
            initial(), "a1", KIND_A, CONTENT_A1, None
        )
        activations = tuple(
            replace(value, status=ActivationStatus.HARD_REVOKED)
            if value.activation_id == activation_id
            else value
            for value in snapshot.activations
        )
        candidate = replace(snapshot, activations=activations, snapshot_id="")
        candidate = replace(candidate, snapshot_id=derive_snapshot_id(candidate))
        self.assertIn(
            "hard-revoked activation selected",
            invariant_violations(candidate),
        )

    def test_generation_gap_is_detected(self) -> None:
        snapshot, activation_id, _ = activate(
            initial(), "a1", KIND_A, CONTENT_A1, None
        )
        activations = tuple(
            replace(value, generation=2)
            if value.activation_id == activation_id
            else value
            for value in snapshot.activations
        )
        candidate = replace(snapshot, activations=activations, snapshot_id="")
        candidate = replace(candidate, snapshot_id=derive_snapshot_id(candidate))
        self.assertTrue(
            any(
                "non-contiguous generations" in value
                for value in invariant_violations(candidate)
            )
        )

    def test_hard_revocation_reversal_is_detected(self) -> None:
        first, activation_id, _ = activate(
            initial(), "a1", KIND_A, CONTENT_A1, None
        )
        revoked, _ = suspend(
            first, "s1", KIND_A, Retirement.HARD_REVOKED
        )
        activations = tuple(
            replace(value, status=ActivationStatus.USABLE)
            if value.activation_id == activation_id
            else value
            for value in revoked.activations
        )
        tampered = replace(revoked, activations=activations, snapshot_id="")
        tampered = replace(tampered, snapshot_id=derive_snapshot_id(tampered))
        self.assertIn(
            "hard revocation reversed",
            transition_violations(revoked, tampered),
        )

    def test_applied_version_gap_is_detected(self) -> None:
        snapshot, _, _ = activate(
            initial(), "a1", KIND_A, CONTENT_A1, None
        )
        operation = snapshot.applied_operations[0]
        broken = AppliedOperation(
            operation.operation_id, operation.command_digest, 2
        )
        candidate = replace(
            snapshot,
            applied_operations=(broken,),
            snapshot_id="",
        )
        candidate = replace(candidate, snapshot_id=derive_snapshot_id(candidate))
        self.assertIn(
            "applied versions are not exact successors",
            invariant_violations(candidate),
        )


class ExplorerTests(unittest.TestCase):
    def test_depth_three_has_exact_deterministic_state_counts(self) -> None:
        first = explore(3)
        second = explore(3)
        self.assertEqual(first, second)
        self.assertEqual(first.states, 305)
        self.assertEqual(first.applied, 304)
        self.assertEqual(first.rejected, 271)
        self.assertEqual(first.replay_checks, 608)

    def test_state_bound_fails_closed(self) -> None:
        with self.assertRaises(RuntimeError):
            explore(3, max_states=10)


class CounterexampleTests(unittest.TestCase):
    @staticmethod
    def _retirement(value):
        return None if value is None else Retirement(value)

    def _step(self, snapshot, step, activations, commands):
        operation = step["op"]
        if operation == "register":
            command = RegisterContent(
                step["id"],
                snapshot.snapshot_id,
                snapshot.version,
                step["content"],
                step["kind"],
            )
        elif operation == "activate":
            command = Activate(
                step["id"],
                snapshot.snapshot_id,
                snapshot.version,
                step["content"],
                step["kind"],
                self._retirement(step.get("retire")),
            )
        elif operation == "suspend":
            command = Suspend(
                step["id"],
                snapshot.snapshot_id,
                snapshot.version,
                step["kind"],
                Retirement(step["retire"]),
            )
        else:
            self.fail(f"unknown step {operation}")
        decision = apply(snapshot, command)
        self.assertIs(decision.outcome, CommandOutcome.APPLIED)
        if "save" in step:
            self.assertIsNotNone(decision.created_activation_id)
            activations[step["save"]] = decision.created_activation_id
        if "save_command" in step:
            commands[step["save_command"]] = command
        return decision.snapshot

    def _probe(self, snapshot, probe, activations, commands):
        probe_type = probe["type"]
        if probe_type == "use":
            decision = decide_use(
                snapshot,
                probe["kind"],
                activations[probe["activation"]],
                ResourceUse(probe["use"]),
            )
            return decision.outcome.value, (
                None if decision.reason is None else decision.reason.value
            )
        if probe_type == "tokens_differ":
            self.assertNotEqual(
                activations[probe["left"]], activations[probe["right"]]
            )
            return "accept", None
        if probe_type == "replay":
            decision = apply(snapshot, commands[probe["command"]])
            return decision.outcome.value, (
                None if decision.reason is None else decision.reason.value
            )
        if probe_type == "equivocate":
            decision = apply(
                snapshot, altered_same_operation(commands[probe["command"]])
            )
            return decision.outcome.value, decision.reason.value
        expected_snapshot_id = snapshot.snapshot_id
        if probe_type == "stale_activate":
            expected_snapshot_id = "f" * 64
            command = Activate(
                probe["id"],
                expected_snapshot_id,
                snapshot.version,
                probe["content"],
                probe["kind"],
                self._retirement(probe.get("retire")),
            )
        elif probe_type == "command" and probe["op"] == "register":
            command = RegisterContent(
                probe["id"],
                expected_snapshot_id,
                snapshot.version,
                probe["content"],
                probe["kind"],
            )
        elif probe_type == "command" and probe["op"] == "activate":
            command = Activate(
                probe["id"],
                expected_snapshot_id,
                snapshot.version,
                probe["content"],
                probe["kind"],
                self._retirement(probe.get("retire")),
            )
        elif probe_type == "command" and probe["op"] == "hard_revoke":
            command = HardRevokePredecessor(
                probe["id"],
                expected_snapshot_id,
                snapshot.version,
                probe["kind"],
                activations[probe["activation"]],
            )
        else:
            self.fail(f"unknown probe {probe}")
        decision = apply(snapshot, command)
        self.assertIs(decision.snapshot, snapshot)
        return decision.outcome.value, decision.reason.value

    def test_machine_readable_findings_are_complete_and_sorted(self) -> None:
        document = json.loads(COUNTEREXAMPLES.read_text(encoding="utf-8"))
        required = {
            "boundary",
            "attacker_capabilities",
            "preconditions",
            "invariant",
            "minimal_counterexample",
            "expected_result",
            "formal_or_property_obligation",
            "residual_risk",
        }
        identifiers = []
        for finding in document["findings"]:
            identifiers.append(finding["id"])
            self.assertTrue(required.issubset(finding))
        self.assertEqual(identifiers, sorted(identifiers))
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_every_counterexample_replays_against_reference_model(self) -> None:
        document = json.loads(COUNTEREXAMPLES.read_text(encoding="utf-8"))
        for finding in document["findings"]:
            with self.subTest(finding=finding["id"]):
                snapshot = initial()
                activations = {}
                commands = {}
                scenario = finding["minimal_counterexample"]
                for step in scenario["steps"]:
                    snapshot = self._step(
                        snapshot, step, activations, commands
                    )
                actual = self._probe(
                    snapshot, scenario["probe"], activations, commands
                )
                expected = finding["expected_result"]
                self.assertEqual(actual, (expected["outcome"], expected["reason"]))


if __name__ == "__main__":
    unittest.main()
