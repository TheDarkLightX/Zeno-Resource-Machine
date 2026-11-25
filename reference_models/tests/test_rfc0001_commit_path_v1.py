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
    Second,
    State,
    model,
    step,
)


ROOT = Path(__file__).resolve().parents[2]
INTENT_MAP = ROOT / "formal" / "state-machine" / "semantic_closure_v1" / "intent_map.json"


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
        for second in Second:
            with self.subTest(instance=second.value):
                self.assertEqual(explore_instance(second).violated(), ())

    def test_every_attempt_consumes_its_plan(self) -> None:
        config = Config(Second.CONFLICTING)
        for env in ("", "_ack_lost", "_crash", "_pending"):
            with self.subTest(env=env):
                state, _ = run(config, ("prepare_A", f"commit_A{env}"))
                self.assertIsNone(state.callers[0].plan)
                self.assertIsNone(step(config, state, "commit_A"))

    def test_retry_after_durable_lost_ack_is_rejected_at_preparation_and_resolved_read_only(self) -> None:
        config = Config(Second.CONFLICTING)
        _, outcomes = run(config, ("prepare_A", "commit_A_ack_lost", "prepare_A"))
        self.assertEqual(outcomes, ["prepared", "unknown", "invalid"])
        state, outcomes = run(config, ("prepare_A", "commit_A_ack_lost", "resolve_A"))
        self.assertEqual(outcomes[-1], "already_committed")
        self.assertEqual(state.durable.writes, 1)

    def test_retry_reaches_the_exact_match_when_the_original_lands_first(self) -> None:
        config = Config(Second.CONFLICTING)
        landed, _ = run(config, ("prepare_A", "commit_A_pending", "prepare_A", "land_A"))
        after, outcomes = run(config, ("prepare_A", "commit_A_pending", "prepare_A", "land_A", "commit_A"))
        self.assertEqual(outcomes, ["prepared", "unknown", "prepared", "landed", "already_committed"])
        self.assertEqual(after.durable, landed.durable)
        self.assertEqual(after.durable.effects, 1)

    def test_original_landing_after_the_retry_won_writes_nothing(self) -> None:
        config = Config(Second.CONFLICTING)
        won, outcomes = run(config, ("prepare_A", "commit_A_pending", "prepare_A", "commit_A"))
        self.assertEqual(outcomes[-1], "newly_committed")
        after, _ = run(config, ("prepare_A", "commit_A_pending", "prepare_A", "commit_A", "land_A"))
        self.assertEqual(after.durable, won.durable)

    def test_not_found_is_only_a_snapshot_observation(self) -> None:
        config = Config(Second.CONFLICTING)
        _, outcomes = run(config, ("prepare_A", "commit_A_pending", "resolve_A", "land_A", "resolve_A"))
        self.assertEqual(outcomes, ["prepared", "unknown", "not_found", "landed", "already_committed"])

    def test_conflicting_replay_is_a_conflict_not_stale(self) -> None:
        config = Config(Second.CONFLICTING)
        before, _ = run(config, ("prepare_A", "prepare_B", "commit_A"))
        after, outcomes = run(config, ("prepare_A", "prepare_B", "commit_A", "commit_B"))
        self.assertEqual(outcomes[-1], "conflict")
        self.assertEqual(after.durable, before.durable)

    def test_stale_plan_rejects_without_state_change(self) -> None:
        config = Config(Second.DUPLICATE)
        before, _ = run(config, ("prepare_A", "policy_update"))
        after, outcomes = run(config, ("prepare_A", "policy_update", "commit_A"))
        self.assertEqual(outcomes[-1], "stale")
        self.assertEqual(after.durable, before.durable)

    def test_crash_before_durability_is_pre_state_and_lost_ack_is_post_state(self) -> None:
        config = Config(Second.DUPLICATE)
        crashed, outcomes = run(config, ("prepare_A", "commit_A_crash"))
        self.assertEqual((outcomes[-1], crashed.durable), ("unknown", State().durable))
        lost, outcomes = run(config, ("prepare_A", "commit_A_ack_lost"))
        delivered, _ = run(config, ("prepare_A", "commit_A"))
        self.assertEqual((outcomes[-1], lost.durable), ("unknown", delivered.durable))

    def test_read_only_observations_change_nothing(self) -> None:
        config = Config(Second.CONFLICTING)
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
    def violation(self, second: Second, mutant: Mutant, invariant: str) -> tuple[str, ...]:
        exploration = explore_instance(second, mutant)
        traces = {v.invariant: v.trace for v in exploration.violations}
        self.assertIn(invariant, traces)
        self.assertTrue(replay(model(Config(second, mutant)), traces[invariant], invariant))
        return traces[invariant]

    def test_every_modeled_mutant_is_named_in_the_intent_map(self) -> None:
        nodes = json.loads(INTENT_MAP.read_text(encoding="utf-8"))["nodes"]
        named = {(node["id"], mutant) for node in nodes for mutant in node["mutants"]}
        for mutant, intent in INTENT.items():
            self.assertIn((intent, mutant.value), named)

    def test_single_caller_mutants_are_killed_by_their_hand_derived_trace(self) -> None:
        for mutant, (invariant, trace) in EXPECTED_SHORTEST.items():
            for second in Second:
                with self.subTest(mutant=mutant.value, instance=second.value):
                    self.assertEqual(self.violation(second, mutant, invariant), trace)

    def test_replay_lookup_outside_the_boundary_allows_two_commits(self) -> None:
        mutant = Mutant.REPLAY_LOOKUP_OUTSIDE_COMMIT_BOUNDARY
        trace = ("prepare_A", "lookup_A", "lookup_B", "commit_A", "prepare_B", "commit_B")
        got = self.violation(Second.CONFLICTING, mutant, "ConflictingPlansHaveAtMostOneNewCommit")
        self.assertEqual(got, trace)
        # A duplicate cannot prepare after the winner nullified its input, so it is misclassified as stale.
        got = self.violation(Second.DUPLICATE, mutant, "ReplayClassificationLinearizable")
        self.assertEqual(len(got), 6)
        self.assertEqual(run(Config(Second.DUPLICATE, mutant), got)[1][-1], "stale")

    def test_retry_duplicating_effects_is_killed_by_a_duplicate_or_a_delayed_original(self) -> None:
        mutant = Mutant.RETRY_DUPLICATES_EFFECT
        got = self.violation(Second.DUPLICATE, mutant, "EffectCountMatchesReplay")
        self.assertEqual(got, ("prepare_A", "prepare_B", "commit_A", "commit_B"))
        # One caller suffices once durability can land after OutcomeUnknown.
        got = self.violation(Second.CONFLICTING, mutant, "EffectCountMatchesReplay")
        self.assertEqual(got, ("prepare_A", "commit_A_pending", "prepare_A", "commit_A", "land_A"))

    def test_every_mutant_is_killed_in_every_instance(self) -> None:
        for report in record()["mutants"]:  # type: ignore[union-attr]
            with self.subTest(mutant=report["mutant"]):
                self.assertEqual(report["killed_in"], report["of"])


class EvidenceRecord(unittest.TestCase):
    def test_committed_evidence_matches_a_fresh_exploration(self) -> None:
        self.assertEqual(EVIDENCE.read_text(encoding="utf-8"), render(record(), pretty=True))


if __name__ == "__main__":
    unittest.main()
