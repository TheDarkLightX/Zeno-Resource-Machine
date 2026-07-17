"""Focused tests for deterministic authenticated batch refinement."""

from __future__ import annotations

from dataclasses import replace
import itertools
import unittest

from reference_models.deterministic_authenticated_batch_explorer import explore
from reference_models.deterministic_authenticated_batch_v1 import (
    BatchModelError,
    BoundedState,
    PointObservation,
    RangeObservation,
    ReadFootprint,
    TransactionSpec,
    empty_range_insert_batch,
    reserve_write_skew_batch,
    run_certified_batch,
    run_nullifier_only_mutant,
    run_sequential,
    speculate,
    state_invariants,
    validate_speculative_result,
)


def all_schedules(transaction_ids: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    return tuple(itertools.permutations(transaction_ids))


class SerialRefinementTests(unittest.TestCase):
    """Every worker schedule refines the same canonical serial execution."""

    def test_all_valid_reserve_states_and_worker_schedules_refine_serial(self) -> None:
        batch = reserve_write_skew_batch()
        schedules = all_schedules(tuple(tx.transaction_id for tx in batch))
        executions = 0
        reexecutions = 0
        for left, right in itertools.product(range(3), repeat=2):
            if left + right < 1:
                continue
            initial = BoundedState.from_mapping({0: left, 1: right})
            serial = run_sequential(initial, batch)
            schedule_roots: set[str] = set()
            for schedule in schedules:
                with self.subTest(left=left, right=right, schedule=schedule):
                    certified = run_certified_batch(initial, batch, schedule)
                    executions += 1
                    reexecutions += sum(
                        outcome.used_reexecution for outcome in certified.outcomes
                    )
                    self.assertEqual(
                        certified.semantic_payload(), serial.semantic_payload()
                    )
                    self.assertTrue(state_invariants(certified.final_state))
                    schedule_roots.add(certified.semantic_root())
            self.assertEqual(len(schedule_roots), 1)

        self.assertEqual(executions, 16)
        self.assertEqual(reexecutions, 8)

    def test_minimal_write_skew_reexecutes_second_transaction(self) -> None:
        initial = BoundedState.from_mapping({0: 1, 1: 1})
        batch = reserve_write_skew_batch()
        certified = run_certified_batch(
            initial, batch, ("reserve-right", "reserve-left")
        )

        self.assertEqual(
            [
                (outcome.transaction_id, outcome.accepted, outcome.reason)
                for outcome in certified.outcomes
            ],
            [
                ("reserve-left", True, "accepted"),
                ("reserve-right", False, "minimum_reserve_would_fail"),
            ],
        )
        self.assertEqual(
            [outcome.used_reexecution for outcome in certified.outcomes],
            [False, True],
        )
        self.assertEqual(certified.final_state.values, ((0, 0), (1, 1)))
        self.assertEqual(certified.final_state.nullifiers, ("nf-left",))
        self.assertEqual(
            certified.initial_state_root,
            "246b4363c9f5bd540fd8c44f2c5df89e997388fec8cdfc472c0f299b8091de3a",
        )
        self.assertEqual(
            certified.final_state.root(),
            "3c509c43667d81853bdd34284b83a26a8384c67d6db4665bdf4b9801bf98f65d",
        )

    def test_worker_schedule_must_be_an_exact_permutation(self) -> None:
        initial = BoundedState.from_mapping({0: 1, 1: 1})
        batch = reserve_write_skew_batch()
        for schedule in (
            ("reserve-left",),
            ("reserve-left", "reserve-left"),
            ("reserve-left", "unknown"),
        ):
            with self.subTest(schedule=schedule):
                with self.assertRaisesRegex(BatchModelError, "worker schedule"):
                    run_certified_batch(initial, batch, schedule)

    def test_preexisting_nullifier_rejects_without_a_write(self) -> None:
        transaction = reserve_write_skew_batch()[0]
        initial = BoundedState.from_mapping(
            {0: 1, 1: 1}, nullifiers=(transaction.nullifier,)
        )
        result = run_certified_batch(
            initial, (transaction,), (transaction.transaction_id,)
        )

        self.assertFalse(result.outcomes[0].accepted)
        self.assertEqual(result.outcomes[0].reason, "duplicate_nullifier")
        self.assertEqual(result.final_state, initial)

    def test_empty_external_batch_rejects(self) -> None:
        initial = BoundedState.from_mapping({0: 1, 1: 1})
        with self.assertRaisesRegex(BatchModelError, "nonempty"):
            run_sequential(initial, ())
        with self.assertRaisesRegex(BatchModelError, "nonempty"):
            run_certified_batch(initial, (), ())

    def test_invalid_initial_state_rejects_before_execution(self) -> None:
        invalid = BoundedState.from_mapping({0: 0, 1: 0})
        batch = reserve_write_skew_batch()
        with self.assertRaisesRegex(BatchModelError, "authenticated precondition"):
            run_sequential(invalid, batch)
        with self.assertRaisesRegex(BatchModelError, "authenticated precondition"):
            run_certified_batch(
                invalid, batch, tuple(tx.transaction_id for tx in batch)
            )

    def test_unknown_program_enum_rejects_at_construction(self) -> None:
        with self.assertRaisesRegex(BatchModelError, "Program enum"):
            TransactionSpec(
                position=0,
                transaction_id="unknown-program",
                nullifier="nf-unknown-program",
                program="unknown",  # type: ignore[arg-type]
                target_key=0,
            )

    def test_semantic_root_binds_exact_ordered_transaction_statement(self) -> None:
        initial = BoundedState.from_mapping({0: 1, 1: 1, 15: 1})
        first = empty_range_insert_batch()[0]
        substituted = replace(first, target_key=12)

        original_result = run_sequential(initial, (first,))
        substituted_result = run_sequential(initial, (substituted,))
        self.assertEqual(
            original_result.outcomes[0].semantic_payload(),
            substituted_result.outcomes[0].semantic_payload(),
        )
        self.assertEqual(original_result.final_state, substituted_result.final_state)
        self.assertNotEqual(
            original_result.ordered_manifest_root,
            substituted_result.ordered_manifest_root,
        )
        self.assertNotEqual(
            original_result.semantic_root(), substituted_result.semantic_root()
        )


class ExactReadFootprintTests(unittest.TestCase):
    """Substituted, missing, and extra semantic observations fail closed."""

    def setUp(self) -> None:
        self.initial = BoundedState.from_mapping({0: 1, 1: 1})

    def test_exact_point_footprint_validates(self) -> None:
        result = speculate(reserve_write_skew_batch()[0], self.initial)
        validate_speculative_result(result, self.initial)
        self.assertEqual(
            result.evaluation.footprint.points,
            (PointObservation(0, 1), PointObservation(1, 1)),
        )
        self.assertEqual(result.evaluation.footprint.ranges, ())

    def test_missing_point_observation_rejects(self) -> None:
        result = speculate(reserve_write_skew_batch()[0], self.initial)
        tampered = replace(
            result,
            evaluation=replace(
                result.evaluation,
                footprint=ReadFootprint(
                    points=result.evaluation.footprint.points[:1]
                ),
            ),
        )
        with self.assertRaisesRegex(BatchModelError, "exact read footprint"):
            validate_speculative_result(tampered, self.initial)

    def test_substituted_point_value_rejects(self) -> None:
        result = speculate(reserve_write_skew_batch()[0], self.initial)
        tampered = replace(
            result,
            evaluation=replace(
                result.evaluation,
                footprint=ReadFootprint(
                    points=(PointObservation(0, 2), PointObservation(1, 1))
                ),
            ),
        )
        with self.assertRaisesRegex(BatchModelError, "exact read footprint"):
            validate_speculative_result(tampered, self.initial)

    def test_boolean_cannot_substitute_for_integer_or_acceptance_bit(self) -> None:
        with self.assertRaisesRegex(BatchModelError, "exact integer"):
            PointObservation(0, True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(BatchModelError, "exact integer"):
            BoundedState.from_mapping({0: True, 1: 1})  # type: ignore[dict-item]

        transaction = reserve_write_skew_batch()[0]
        with self.assertRaisesRegex(BatchModelError, "exact integer"):
            replace(transaction, position=True)

        result = speculate(transaction, self.initial)
        with self.assertRaisesRegex(BatchModelError, "exact boolean"):
            replace(result.evaluation, accepted=1)  # type: ignore[arg-type]

    def test_substituted_write_rejects(self) -> None:
        result = speculate(reserve_write_skew_batch()[0], self.initial)
        tampered = replace(
            result,
            evaluation=replace(result.evaluation, writes=((0, 2),)),
        )
        with self.assertRaisesRegex(BatchModelError, "speculative result"):
            validate_speculative_result(tampered, self.initial)

    def test_exact_empty_range_footprint_validates(self) -> None:
        result = speculate(empty_range_insert_batch()[0], self.initial)
        validate_speculative_result(result, self.initial)
        self.assertEqual(result.evaluation.footprint.points, ())
        self.assertEqual(
            result.evaluation.footprint.ranges,
            (RangeObservation(10, 20, ()),),
        )

    def test_missing_range_observation_rejects(self) -> None:
        result = speculate(empty_range_insert_batch()[0], self.initial)
        tampered = replace(
            result,
            evaluation=replace(result.evaluation, footprint=ReadFootprint()),
        )
        with self.assertRaisesRegex(BatchModelError, "exact read footprint"):
            validate_speculative_result(tampered, self.initial)

    def test_substituted_range_result_rejects(self) -> None:
        result = speculate(empty_range_insert_batch()[0], self.initial)
        tampered = replace(
            result,
            evaluation=replace(
                result.evaluation,
                footprint=ReadFootprint(
                    ranges=(RangeObservation(10, 20, ((15, 1),)),)
                ),
            ),
        )
        with self.assertRaisesRegex(BatchModelError, "exact read footprint"):
            validate_speculative_result(tampered, self.initial)

    def test_snapshot_substitution_rejects(self) -> None:
        result = speculate(reserve_write_skew_batch()[0], self.initial)
        changed = BoundedState.from_mapping({0: 2, 1: 1})
        with self.assertRaisesRegex(BatchModelError, "snapshot mismatch"):
            validate_speculative_result(result, changed)

    def test_nullifier_guard_is_bound_beyond_program_reads(self) -> None:
        transaction = reserve_write_skew_batch()[0]
        fresh = BoundedState.from_mapping({0: 1, 1: 1})
        consumed = BoundedState.from_mapping(
            {0: 1, 1: 1}, nullifiers=(transaction.nullifier,)
        )

        fresh_speculation = speculate(transaction, fresh)
        consumed_speculation = speculate(transaction, consumed)
        self.assertEqual(
            fresh_speculation.evaluation.footprint.root(),
            consumed_speculation.evaluation.footprint.root(),
        )

        fresh_outcome = run_sequential(fresh, (transaction,)).outcomes[0]
        consumed_outcome = run_sequential(consumed, (transaction,)).outcomes[0]
        self.assertNotEqual(
            fresh_outcome.decision_footprint_root,
            consumed_outcome.decision_footprint_root,
        )
        self.assertEqual(consumed_outcome.reason, "duplicate_nullifier")

    def test_invariant_reads_are_bound_beyond_program_reads(self) -> None:
        transaction = empty_range_insert_batch()[0]
        reserve_one = BoundedState.from_mapping({0: 1, 1: 1})
        reserve_two = BoundedState.from_mapping({0: 2, 1: 1})

        first_speculation = speculate(transaction, reserve_one)
        second_speculation = speculate(transaction, reserve_two)
        self.assertEqual(
            first_speculation.evaluation.footprint.root(),
            second_speculation.evaluation.footprint.root(),
        )

        first_outcome = run_sequential(reserve_one, (transaction,)).outcomes[0]
        second_outcome = run_sequential(reserve_two, (transaction,)).outcomes[0]
        self.assertNotEqual(
            first_outcome.decision_footprint_root,
            second_outcome.decision_footprint_root,
        )
        self.assertTrue(first_outcome.accepted and second_outcome.accepted)


class RangeRevalidationTests(unittest.TestCase):
    """A range insertion is a dependency even when the initial result is empty."""

    def test_empty_range_insertions_are_schedule_independent(self) -> None:
        initial = BoundedState.from_mapping({0: 1, 1: 1})
        batch = empty_range_insert_batch()
        schedules = all_schedules(tuple(tx.transaction_id for tx in batch))
        results = [run_certified_batch(initial, batch, schedule) for schedule in schedules]

        self.assertEqual(len({result.semantic_root() for result in results}), 1)
        for result in results:
            self.assertEqual(
                [(outcome.accepted, outcome.reason) for outcome in result.outcomes],
                [(True, "accepted"), (False, "range_not_empty")],
            )
            self.assertEqual(
                [outcome.used_reexecution for outcome in result.outcomes],
                [False, True],
            )
            self.assertEqual(result.final_state.range_values(10, 20), ((11, 1),))
            self.assertTrue(state_invariants(result.final_state))


class NullifierOnlyMutantTests(unittest.TestCase):
    """Distinct nullifiers do not establish transaction independence."""

    def test_write_skew_mutant_accepts_distinct_nullifiers_and_breaks_invariant(self) -> None:
        initial = BoundedState.from_mapping({0: 1, 1: 1})
        mutant = run_nullifier_only_mutant(initial, reserve_write_skew_batch())

        self.assertEqual(
            [outcome.accepted for outcome in mutant.outcomes], [True, True]
        )
        self.assertEqual(mutant.final_state.nullifiers, ("nf-left", "nf-right"))
        self.assertEqual(mutant.final_state.values, ((0, 0), (1, 0)))
        self.assertFalse(state_invariants(mutant.final_state))
        self.assertEqual(
            mutant.final_state.root(),
            "9b0d56e09652e13ddfc7e66f3a6bc25fe187ad024051e27ee69eb8a393764ef4",
        )

    def test_mutant_violates_four_of_eight_valid_reserve_states(self) -> None:
        violations = 0
        for left, right in itertools.product(range(3), repeat=2):
            if left + right < 1:
                continue
            result = run_nullifier_only_mutant(
                BoundedState.from_mapping({0: left, 1: right}),
                reserve_write_skew_batch(),
            )
            violations += not state_invariants(result.final_state)
        self.assertEqual(violations, 4)

    def test_range_blind_mutant_accepts_two_phantom_insertions(self) -> None:
        initial = BoundedState.from_mapping({0: 1, 1: 1})
        result = run_nullifier_only_mutant(initial, empty_range_insert_batch())
        self.assertEqual(result.final_state.range_values(10, 20), ((11, 1), (12, 1)))
        self.assertFalse(state_invariants(result.final_state))


class EvidenceExplorerTests(unittest.TestCase):
    """The deterministic explorer pins the bounded evidence counts."""

    def test_explorer_exact_counts(self) -> None:
        evidence = explore()

        self.assertEqual(
            evidence["schema"],
            "zrm/deterministic-authenticated-batch-exploration/v1",
        )
        self.assertEqual(
            evidence["serial_refinement"],
            {
                "valid_initial_states": 8,
                "worker_schedules_per_state": 2,
                "executions": 16,
                "semantic_refinement_mismatches": 0,
                "states_with_schedule_variant_result": 0,
                "accepted_transactions_across_executions": 8,
                "reexecutions_across_executions": 8,
            },
        )
        self.assertEqual(evidence["exact_read_footprints"]["tamper_cases"], 4)
        self.assertEqual(
            evidence["exact_read_footprints"]["rejected_tamper_cases"], 4
        )
        self.assertEqual(
            evidence["decision_dependency_mutants"],
            {
                "cases": 2,
                "program_only_root_collisions": 2,
                "complete_decision_root_collisions": 0,
                "details": {
                    "nullifier_guard": {
                        "program_only_roots_collide": True,
                        "decision_roots_collide": False,
                    },
                    "candidate_invariant_reads": {
                        "program_only_roots_collide": True,
                        "decision_roots_collide": False,
                    },
                },
            },
        )
        self.assertEqual(
            evidence["range_phantom"]["distinct_certified_semantic_roots"], 1
        )
        self.assertEqual(
            evidence["nullifier_only_write_skew_mutant"]["invariant_violations"],
            4,
        )
        self.assertTrue(
            evidence["minimal_write_skew_witness"]["certified_preserves_invariants"]
        )
        self.assertFalse(
            evidence["minimal_write_skew_witness"]["mutant_preserves_invariants"]
        )


if __name__ == "__main__":
    unittest.main()
