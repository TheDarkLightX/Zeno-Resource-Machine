"""Deterministic exploration of ZRM ordered paths and authenticated footprints."""

from __future__ import annotations

import argparse
import itertools
import json

from reference_models.zrm_composition_frontier_v2 import (
    Program,
    ProgramKind,
    StepKind,
    TransitionPath,
    TransitionStep,
    admit_external,
    enumerate_small_programs,
    execute_order,
    fact_complete_parallel,
    same_context_only_mutant,
    schedules_agree,
    write_only_parallel,
)


def bridge_path() -> TransitionPath:
    before = TransitionPath.singleton(
        TransitionStep("resource-a", StepKind.RESOURCE, "s0", "s1", "ctx-a", "ctx-a")
    )
    bridge = TransitionPath.singleton(
        TransitionStep(
            "governance-a-b",
            StepKind.GOVERNANCE_BRIDGE,
            "s1",
            "s2",
            "ctx-a",
            "ctx-b",
            "activation-command-7",
        )
    )
    after = TransitionPath.singleton(
        TransitionStep("resource-b", StepKind.RESOURCE, "s2", "s3", "ctx-b", "ctx-b")
    )
    return before.compose(bridge).compose(after)


def explore() -> dict[str, object]:
    actions = ("a", "b", "c")
    ordered_roots = {
        TransitionPath(
            "s0",
            "s3",
            "ctx",
            "ctx",
            tuple(
                TransitionStep(action, StepKind.RESOURCE, f"s{index}", f"s{index + 1}", "ctx", "ctx")
                for index, action in enumerate(permutation)
            ),
        ).trace.root()
        for permutation in itertools.permutations(actions)
    }
    sorted_mutant_roots = {
        TransitionPath(
            "s0",
            "s3",
            "ctx",
            "ctx",
            tuple(
                TransitionStep(action, StepKind.RESOURCE, f"s{index}", f"s{index + 1}", "ctx", "ctx")
                for index, action in enumerate(permutation)
            ),
        ).trace.incorrectly_sorted_root()
        for permutation in itertools.permutations(actions)
    }

    states = tuple(dict(zip(("x", "y", "z"), values, strict=True)) for values in itertools.product((0, 1), repeat=3))
    programs = enumerate_small_programs()
    ordered_pairs = 0
    write_only_certified = 0
    write_only_false_safe = 0
    fact_complete_certified = 0
    fact_complete_false_safe = 0
    first_write_only_counterexample: dict[str, object] | None = None
    for left, right in itertools.permutations(programs, 2):
        ordered_pairs += 1
        left_fp = left.actual_footprint()
        right_fp = right.actual_footprint()
        write_only = write_only_parallel(left_fp, right_fp)
        complete = fact_complete_parallel(left_fp, right_fp)
        if write_only:
            write_only_certified += 1
        if complete:
            fact_complete_certified += 1
        for state in states:
            agrees = schedules_agree(left, right, state)
            if write_only and not agrees:
                write_only_false_safe += 1
                if first_write_only_counterexample is None:
                    first_write_only_counterexample = {
                        "left": left.program_id,
                        "right": right.program_id,
                        "initial": state,
                        "left_then_right": execute_order((left, right), state),
                        "right_then_left": execute_order((right, left), state),
                    }
            if complete and not agrees:
                fact_complete_false_safe += 1

    bridge = bridge_path()
    identity = TransitionPath.identity("s0", "ctx-a")
    explicit_counterexample_left = Program("copy-x-y", ProgramKind.COPY, "y", source="x")
    explicit_counterexample_right = Program("set-x-1", ProgramKind.SET, "x", value=1)
    explicit_state = {"x": 0, "y": 0, "z": 0}

    return {
        "schema": "zrm/composition-frontier-exploration/v2",
        "ordered_manifest": {
            "permutations": 6,
            "distinct_ordered_roots": len(ordered_roots),
            "distinct_sorted_mutant_roots": len(sorted_mutant_roots),
        },
        "context_bridge": {
            "trace": list(bridge.trace.items),
            "pre_context": bridge.pre_context,
            "post_context": bridge.post_context,
            "typed_path_accepts": True,
            "same_context_only_mutant_accepts": same_context_only_mutant(
                tuple(TransitionPath.singleton(step) for step in bridge.steps)
            ),
        },
        "identity": {
            "internal_total_carrier_accepts": identity.is_internal_identity(),
            "external_admission_accepts": admit_external(identity),
        },
        "footprint_exploration": {
            "programs": len(programs),
            "states": len(states),
            "ordered_program_pairs": ordered_pairs,
            "schedule_checks": ordered_pairs * len(states),
            "write_only_certified_pairs": write_only_certified,
            "write_only_false_safe_schedule_checks": write_only_false_safe,
            "fact_complete_certified_pairs": fact_complete_certified,
            "fact_complete_false_safe_schedule_checks": fact_complete_false_safe,
            "first_write_only_counterexample": first_write_only_counterexample,
            "named_counterexample": {
                "left": explicit_counterexample_left.program_id,
                "right": explicit_counterexample_right.program_id,
                "initial": explicit_state,
                "write_only_certifies": write_only_parallel(
                    explicit_counterexample_left.actual_footprint(),
                    explicit_counterexample_right.actual_footprint(),
                ),
                "fact_complete_certifies": fact_complete_parallel(
                    explicit_counterexample_left.actual_footprint(),
                    explicit_counterexample_right.actual_footprint(),
                ),
                "schedules_agree": schedules_agree(
                    explicit_counterexample_left,
                    explicit_counterexample_right,
                    explicit_state,
                ),
            },
        },
        "non_claims": [
            "finite key/value programs are not a proof about arbitrary ZRM transition code",
            "declared footprints are trusted model objects until an instrumented fact resolver proves exact coverage",
            "context bridge authority is abstract and does not define governance protocol bytes",
            "hash roots are model-only domain-separated SHA-256 values",
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
