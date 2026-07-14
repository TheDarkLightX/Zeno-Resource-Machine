"""Deterministic evidence explorer for the bounded authenticated-batch model."""

from __future__ import annotations

import argparse
from dataclasses import replace
import itertools
import json

from reference_models.deterministic_authenticated_batch_v1 import (
    BatchModelError,
    BoundedState,
    PointObservation,
    RangeObservation,
    ReadFootprint,
    empty_range_insert_batch,
    reserve_write_skew_batch,
    run_certified_batch,
    run_nullifier_only_mutant,
    run_sequential,
    speculate,
    state_invariants,
    validate_speculative_result,
)


def _schedules(transaction_ids: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    return tuple(itertools.permutations(transaction_ids))


def explore() -> dict[str, object]:
    reserve_batch = reserve_write_skew_batch()
    reserve_schedules = _schedules(
        tuple(transaction.transaction_id for transaction in reserve_batch)
    )
    valid_reserve_states = [
        BoundedState.from_mapping({0: left, 1: right})
        for left, right in itertools.product(range(3), repeat=2)
        if left + right >= 1
    ]

    reserve_executions = 0
    reserve_reexecutions = 0
    reserve_accepted = 0
    reserve_refinement_mismatches = 0
    reserve_schedule_variant_states = 0
    for initial_state in valid_reserve_states:
        serial = run_sequential(initial_state, reserve_batch)
        schedule_roots: set[str] = set()
        for schedule in reserve_schedules:
            result = run_certified_batch(initial_state, reserve_batch, schedule)
            reserve_executions += 1
            reserve_reexecutions += sum(
                outcome.used_reexecution for outcome in result.outcomes
            )
            reserve_accepted += sum(outcome.accepted for outcome in result.outcomes)
            schedule_roots.add(result.semantic_root())
            if result.semantic_payload() != serial.semantic_payload():
                reserve_refinement_mismatches += 1
        if len(schedule_roots) != 1:
            reserve_schedule_variant_states += 1

    mutant_violations = []
    mutant_accepted = 0
    for initial_state in valid_reserve_states:
        mutant = run_nullifier_only_mutant(initial_state, reserve_batch)
        mutant_accepted += sum(outcome.accepted for outcome in mutant.outcomes)
        if not state_invariants(mutant.final_state):
            mutant_violations.append(
                {
                    "initial_state": initial_state.canonical_payload(),
                    "result": mutant.canonical_payload(),
                }
            )

    range_batch = empty_range_insert_batch()
    range_schedules = _schedules(
        tuple(transaction.transaction_id for transaction in range_batch)
    )
    empty_range_state = BoundedState.from_mapping({0: 1, 1: 1})
    range_results = [
        run_certified_batch(empty_range_state, range_batch, schedule)
        for schedule in range_schedules
    ]
    range_mutant = run_nullifier_only_mutant(empty_range_state, range_batch)

    point_result = speculate(reserve_batch[0], empty_range_state)
    point_footprint = point_result.evaluation.footprint
    point_missing = replace(
        point_result,
        evaluation=replace(
            point_result.evaluation,
            footprint=ReadFootprint(points=point_footprint.points[:1]),
        ),
    )
    substituted_points = list(point_footprint.points)
    substituted_points[0] = PointObservation(
        substituted_points[0].key, substituted_points[0].value + 1
    )
    point_substituted = replace(
        point_result,
        evaluation=replace(
            point_result.evaluation,
            footprint=ReadFootprint(points=tuple(substituted_points)),
        ),
    )

    range_result = speculate(range_batch[0], empty_range_state)
    range_missing = replace(
        range_result,
        evaluation=replace(range_result.evaluation, footprint=ReadFootprint()),
    )
    range_substituted = replace(
        range_result,
        evaluation=replace(
            range_result.evaluation,
            footprint=ReadFootprint(
                ranges=(RangeObservation(10, 20, ((15, 1),)),)
            ),
        ),
    )
    tamper_cases = {
        "point_missing": point_missing,
        "point_value_substituted": point_substituted,
        "range_missing": range_missing,
        "range_result_substituted": range_substituted,
    }
    tamper_decisions: dict[str, str] = {}
    for name, result in tamper_cases.items():
        try:
            validate_speculative_result(result, empty_range_state)
        except BatchModelError:
            tamper_decisions[name] = "reject"
        else:
            tamper_decisions[name] = "accept"

    write_skew_initial = BoundedState.from_mapping({0: 1, 1: 1})
    write_skew_certified = run_certified_batch(
        write_skew_initial,
        reserve_batch,
        ("reserve-right", "reserve-left"),
    )
    write_skew_mutant = run_nullifier_only_mutant(write_skew_initial, reserve_batch)

    # These pairs change only dependencies that a program-read-only footprint
    # omits.  The complete decision footprint must distinguish both pairs.
    guarded_transaction = reserve_batch[0]
    consumed_nullifier_state = BoundedState.from_mapping(
        {0: 1, 1: 1}, nullifiers=(guarded_transaction.nullifier,)
    )
    fresh_guard_speculation = speculate(guarded_transaction, write_skew_initial)
    consumed_guard_speculation = speculate(
        guarded_transaction, consumed_nullifier_state
    )
    fresh_guard_outcome = run_sequential(
        write_skew_initial, (guarded_transaction,)
    ).outcomes[0]
    consumed_guard_outcome = run_sequential(
        consumed_nullifier_state, (guarded_transaction,)
    ).outcomes[0]

    invariant_transaction = range_batch[0]
    changed_reserve_state = BoundedState.from_mapping({0: 2, 1: 1})
    first_invariant_speculation = speculate(invariant_transaction, empty_range_state)
    changed_invariant_speculation = speculate(
        invariant_transaction, changed_reserve_state
    )
    first_invariant_outcome = run_sequential(
        empty_range_state, (invariant_transaction,)
    ).outcomes[0]
    changed_invariant_outcome = run_sequential(
        changed_reserve_state, (invariant_transaction,)
    ).outcomes[0]

    decision_dependency_cases = {
        "nullifier_guard": {
            "program_only_roots_collide": (
                fresh_guard_speculation.evaluation.footprint.root()
                == consumed_guard_speculation.evaluation.footprint.root()
            ),
            "decision_roots_collide": (
                fresh_guard_outcome.decision_footprint_root
                == consumed_guard_outcome.decision_footprint_root
            ),
        },
        "candidate_invariant_reads": {
            "program_only_roots_collide": (
                first_invariant_speculation.evaluation.footprint.root()
                == changed_invariant_speculation.evaluation.footprint.root()
            ),
            "decision_roots_collide": (
                first_invariant_outcome.decision_footprint_root
                == changed_invariant_outcome.decision_footprint_root
            ),
        },
    }

    return {
        "schema": "zrm/deterministic-authenticated-batch-exploration/v1",
        "serial_refinement": {
            "valid_initial_states": len(valid_reserve_states),
            "worker_schedules_per_state": len(reserve_schedules),
            "executions": reserve_executions,
            "semantic_refinement_mismatches": reserve_refinement_mismatches,
            "states_with_schedule_variant_result": reserve_schedule_variant_states,
            "accepted_transactions_across_executions": reserve_accepted,
            "reexecutions_across_executions": reserve_reexecutions,
        },
        "exact_read_footprints": {
            "tamper_cases": len(tamper_decisions),
            "rejected_tamper_cases": sum(
                decision == "reject" for decision in tamper_decisions.values()
            ),
            "decisions": tamper_decisions,
        },
        "decision_dependency_mutants": {
            "cases": len(decision_dependency_cases),
            "program_only_root_collisions": sum(
                case["program_only_roots_collide"]
                for case in decision_dependency_cases.values()
            ),
            "complete_decision_root_collisions": sum(
                case["decision_roots_collide"]
                for case in decision_dependency_cases.values()
            ),
            "details": decision_dependency_cases,
        },
        "range_phantom": {
            "worker_schedules": len(range_schedules),
            "distinct_certified_semantic_roots": len(
                {result.semantic_root() for result in range_results}
            ),
            "certified_accepted_transactions_across_schedules": sum(
                outcome.accepted
                for result in range_results
                for outcome in result.outcomes
            ),
            "certified_reexecutions_across_schedules": sum(
                outcome.used_reexecution
                for result in range_results
                for outcome in result.outcomes
            ),
            "nullifier_only_mutant_range_entries": len(
                range_mutant.final_state.range_values(10, 20)
            ),
            "nullifier_only_mutant_preserves_invariants": state_invariants(
                range_mutant.final_state
            ),
        },
        "nullifier_only_write_skew_mutant": {
            "initial_states": len(valid_reserve_states),
            "accepted_transactions": mutant_accepted,
            "invariant_violations": len(mutant_violations),
            "first_violation": mutant_violations[0],
        },
        "minimal_write_skew_witness": {
            "initial_state": write_skew_initial.canonical_payload(),
            "canonical_order": [
                transaction.transaction_id for transaction in reserve_batch
            ],
            "worker_schedule": ["reserve-right", "reserve-left"],
            "certified": write_skew_certified.canonical_payload(),
            "nullifier_only_mutant": write_skew_mutant.canonical_payload(),
            "certified_preserves_invariants": state_invariants(
                write_skew_certified.final_state
            ),
            "mutant_preserves_invariants": state_invariants(
                write_skew_mutant.final_state
            ),
        },
        "non_claims": [
            "bounded enumeration is not an unbounded serializability proof",
            "model hashes are deterministic identifiers, not accumulator security proofs",
            "the model does not implement storage, durability, proofs, or production authority",
            "the nullifier-only path is an intentional mutant, not an admissible design",
            "the sealed capability is one modeled enforcement design, not proof that all production program reads are instrumented",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    print(json.dumps(explore(), indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
