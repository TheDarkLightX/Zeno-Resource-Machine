"""Independent scenario and mutant tests for the RFC-0001 commit-path model."""

from __future__ import annotations

import json
import unittest
from functools import cache
from pathlib import Path

from reference_models.bounded_explorer import replay
from reference_models.rfc0001_commit_path_explorer import (
    EVIDENCE,
    INTENT,
    explore_all,
    explore_instance,
    render,
)
from reference_models.rfc0001_commit_path_v1 import (
    Config,
    Mutant,
    PlanReading,
    Second,
    State,
    model,
    step,
)


ROOT = Path(__file__).resolve().parents[2]
INTENT_MAP = ROOT / "formal" / "state-machine" / "semantic_closure_v1" / "intent_map.json"
EVERY = tuple((second, reading) for second in Second for reading in PlanReading)


@cache
def record() -> dict[str, object]:
    """One full exploration shared by the tests that read the whole record."""

    return explore_all()


def run(config: Config, trace: tuple[str, ...]) -> tuple[State, list[str]]:
    """Execute a trace, requiring every action to be enabled."""

    state, outcomes = State(), []
    for action in trace:
        result = step(config, state, action)
        if result is None:
            raise AssertionError(f"{action} is disabled after {outcomes}")
        state, outcome = result
        outcomes.append(outcome)
    return state, outcomes


class CorrectModel(unittest.TestCase):
    def test_every_invariant_holds_in_every_instance(self) -> None:
        for second, reading in EVERY:
            with self.subTest(instance=(second.value, reading.value)):
                self.assertEqual(explore_instance(second, reading).violated(), ())

    def test_exact_retry_after_lost_acknowledgement_is_already_committed_without_a_write(self) -> None:
        config = Config(Second.CONFLICTING, PlanReading.RETAINED)
        before, _ = run(config, ("prepare_A", "commit_A_ack_lost"))
        after, outcomes = run(config, ("prepare_A", "commit_A_ack_lost", "commit_A"))
        self.assertEqual(outcomes, ["prepared", "unknown", "already_committed"])
        self.assertEqual(after.durable, before.durable)
        self.assertEqual(after.durable.effects, 1)

    def test_consumed_plan_retry_is_rejected_at_preparation_and_resolved_read_only(self) -> None:
        config = Config(Second.CONFLICTING, PlanReading.CONSUMED)
        state, outcomes = run(config, ("prepare_A", "commit_A_ack_lost", "prepare_A"))
        self.assertEqual(outcomes, ["prepared", "unknown", "invalid"])
        state, outcomes = run(config, ("prepare_A", "commit_A_ack_lost", "resolve_A"))
        self.assertEqual(outcomes[-1], "already_committed")
        self.assertEqual(state.durable.writes, 1)

    def test_conflicting_replay_is_a_conflict_not_stale(self) -> None:
        config = Config(Second.CONFLICTING, PlanReading.CONSUMED)
        before, _ = run(config, ("prepare_A", "prepare_B", "commit_A"))
        after, outcomes = run(config, ("prepare_A", "prepare_B", "commit_A", "commit_B"))
        self.assertEqual(outcomes[-1], "conflict")
        self.assertEqual(after.durable, before.durable)

    def test_stale_plan_rejects_without_state_change(self) -> None:
        config = Config(Second.DUPLICATE, PlanReading.CONSUMED)
        before, _ = run(config, ("prepare_A", "policy_update"))
        after, outcomes = run(config, ("prepare_A", "policy_update", "commit_A"))
        self.assertEqual(outcomes[-1], "stale")
        self.assertEqual(after.durable, before.durable)

    def test_crash_before_durability_is_pre_state_and_lost_ack_is_post_state(self) -> None:
        config = Config(Second.DUPLICATE, PlanReading.CONSUMED)
        crashed, outcomes = run(config, ("prepare_A", "commit_A_crash"))
        self.assertEqual((outcomes[-1], crashed.durable), ("unknown", State().durable))
        lost, outcomes = run(config, ("prepare_A", "commit_A_ack_lost"))
        delivered, _ = run(config, ("prepare_A", "commit_A"))
        self.assertEqual((outcomes[-1], lost.durable), ("unknown", delivered.durable))

    def test_read_only_observations_change_nothing(self) -> None:
        config = Config(Second.CONFLICTING, PlanReading.RETAINED)
        state, _ = run(config, ("prepare_A", "commit_A_ack_lost"))
        for action in ("resolve_A", "read_replay"):
            target, _ = step(config, state, action)  # type: ignore[misc]
            self.assertEqual(target.durable, state.durable)

    def test_durable_state_is_determined_by_its_observable_class(self) -> None:
        for report in record()["correct"]:  # type: ignore[union-attr]
            with self.subTest(instance=report["instance"]):
                loose = report["quotient"]["fields_not_determined_by_class"]
                self.assertFalse([name for name in loose if name.startswith("durable.")])
                self.assertLess(report["quotient"]["classes"], report["states"])


EXPECTED_SHORTEST = {
    Mutant.STALE_PLAN_COMMITS: ("FreshCommitOnly", ("prepare_A", "policy_update", "commit_A")),
    Mutant.POLICY_CHANGE_REUSES_MACHINE_ROOT: ("MachineRootAndStateVersionAdvanceTogether", ("policy_update",)),
    Mutant.UNKNOWN_REPORTED_AS_REJECTED: ("RejectImpliesStateUnchanged", ("prepare_A", "commit_A_ack_lost")),
    Mutant.RESOLUTION_REAPPLIES_EFFECT: (
        "RetryResolutionAppliesNoEffects", ("prepare_A", "commit_A_ack_lost", "resolve_A")),
    Mutant.PARTIAL_DURABLE_COMMIT: ("CrashRecoveryIsPreOrPost", ("prepare_A", "commit_A_crash")),
}


class Mutants(unittest.TestCase):
    def violation(self, second: Second, reading: PlanReading, mutant: Mutant, invariant: str) -> tuple[str, ...]:
        exploration = explore_instance(second, reading, mutant)
        traces = {v.invariant: v.trace for v in exploration.violations}
        self.assertIn(invariant, traces)
        self.assertTrue(replay(model(Config(second, reading, mutant)), traces[invariant], invariant))
        return traces[invariant]

    def test_every_modeled_mutant_is_named_in_the_intent_map(self) -> None:
        nodes = json.loads(INTENT_MAP.read_text(encoding="utf-8"))["nodes"]
        named = {(node["id"], mutant) for node in nodes for mutant in node["mutants"]}
        for mutant, intent in INTENT.items():
            self.assertIn((intent, mutant.value), named)

    def test_single_caller_mutants_are_killed_by_their_hand_derived_trace(self) -> None:
        for mutant, (invariant, trace) in EXPECTED_SHORTEST.items():
            for second, reading in EVERY:
                with self.subTest(mutant=mutant.value, instance=(second.value, reading.value)):
                    self.assertEqual(self.violation(second, reading, mutant, invariant), trace)

    def test_replay_lookup_outside_the_boundary_allows_two_commits(self) -> None:
        mutant = Mutant.REPLAY_LOOKUP_OUTSIDE_COMMIT_BOUNDARY
        trace = ("prepare_A", "lookup_A", "lookup_B", "commit_A", "prepare_B", "commit_B")
        for reading in PlanReading:
            got = self.violation(Second.CONFLICTING, reading, mutant, "ConflictingPlansHaveAtMostOneNewCommit")
            self.assertEqual(got, trace)
        # A duplicate cannot prepare after the winner nullified its input, so it is misclassified as stale.
        got = self.violation(Second.DUPLICATE, PlanReading.CONSUMED, mutant, "ReplayClassificationLinearizable")
        self.assertEqual(len(got), 6)
        self.assertEqual(run(Config(Second.DUPLICATE, PlanReading.CONSUMED, mutant), got)[1][-1], "stale")

    def test_retry_duplicating_effects_needs_an_exact_match_inside_the_boundary(self) -> None:
        mutant = Mutant.RETRY_DUPLICATES_EFFECT
        for second in Second:
            got = self.violation(second, PlanReading.RETAINED, mutant, "EffectCountMatchesReplay")
            self.assertEqual(got, ("prepare_A", "commit_A_ack_lost", "commit_A"))
        got = self.violation(Second.DUPLICATE, PlanReading.CONSUMED, mutant, "EffectCountMatchesReplay")
        self.assertEqual(got, ("prepare_A", "prepare_B", "commit_A", "commit_B"))
        # With consumed plans and no duplicate submitter, no attempt reaches the exact-match branch.
        survivor = explore_instance(Second.CONFLICTING, PlanReading.CONSUMED, mutant)
        self.assertEqual(survivor.violated(), ())

    def test_every_mutant_is_killed_in_some_instance(self) -> None:
        for report in record()["mutants"]:  # type: ignore[union-attr]
            with self.subTest(mutant=report["mutant"]):
                self.assertGreater(report["killed_in"], 0)


class EvidenceRecord(unittest.TestCase):
    def test_committed_evidence_matches_a_fresh_exploration(self) -> None:
        self.assertEqual(EVIDENCE.read_text(encoding="utf-8"), render(record(), pretty=True))


if __name__ == "__main__":
    unittest.main()
