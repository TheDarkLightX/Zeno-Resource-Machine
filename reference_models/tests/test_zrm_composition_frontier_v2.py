"""Tests for ordered paths, context bridges, and fact-complete footprints."""

from __future__ import annotations

import itertools
import unittest

from reference_models.zrm_composition_frontier_v2 import (
    CanonicalSet,
    CompositionError,
    Footprint,
    OrderedTrace,
    Program,
    ProgramKind,
    StepKind,
    TransitionPath,
    TransitionStep,
    admit_external,
    enumerate_small_programs,
    fact_complete_parallel,
    footprint_is_exact,
    same_context_only_mutant,
    schedules_agree,
    write_only_parallel,
)
from reference_models.zrm_composition_frontier_v2_explorer import bridge_path, explore


class CanonicalContainerTests(unittest.TestCase):
    def test_canonical_set_union_is_commutative(self) -> None:
        left = CanonicalSet.from_iterable(("b", "a"))
        right = CanonicalSet.from_iterable(("c",))
        self.assertEqual(left.union(right), right.union(left))

    def test_canonical_set_rejects_unsorted_or_duplicate_items(self) -> None:
        with self.assertRaises(CompositionError):
            CanonicalSet(("b", "a"))
        with self.assertRaises(CompositionError):
            CanonicalSet(("a", "a"))
        with self.assertRaisesRegex(CompositionError, "input must be unique"):
            CanonicalSet.from_iterable(("a", "a"))

    def test_canonical_set_union_rejects_overlap(self) -> None:
        left = CanonicalSet.from_iterable(("a", "b"))
        right = CanonicalSet.from_iterable(("b", "c"))
        with self.assertRaisesRegex(CompositionError, "must be disjoint"):
            left.union(right)

    def test_ordered_trace_root_preserves_order(self) -> None:
        first = OrderedTrace(("a", "b"))
        second = OrderedTrace(("b", "a"))
        self.assertNotEqual(first.root(), second.root())
        self.assertEqual(first.incorrectly_sorted_root(), second.incorrectly_sorted_root())

    def test_ordered_trace_rejects_overlap(self) -> None:
        with self.assertRaises(CompositionError):
            OrderedTrace(("a",)).append(OrderedTrace(("a",)))


class TransitionPathTests(unittest.TestCase):
    @staticmethod
    def resource(event: str, pre: str, post: str, context: str = "ctx") -> TransitionPath:
        return TransitionPath.singleton(
            TransitionStep(event, StepKind.RESOURCE, pre, post, context, context)
        )

    def test_identity_is_total_internally_but_rejected_externally(self) -> None:
        identity = TransitionPath.identity("s0", "ctx")
        step = self.resource("a", "s0", "s1")
        self.assertEqual(identity.compose(step), step)
        self.assertFalse(admit_external(identity))
        self.assertTrue(admit_external(step))

    def test_composition_preserves_exact_order(self) -> None:
        left = self.resource("a", "s0", "s1")
        right = self.resource("b", "s1", "s2")
        self.assertEqual(left.compose(right).trace.items, ("a", "b"))
        self.assertEqual(right.trace.items, ("b",))

    def test_mismatched_endpoint_rejected(self) -> None:
        with self.assertRaises(CompositionError):
            self.resource("a", "s0", "s1").compose(self.resource("b", "s9", "s2"))

    def test_resource_step_cannot_change_context(self) -> None:
        with self.assertRaises(CompositionError):
            TransitionStep("a", StepKind.RESOURCE, "s0", "s1", "ctx-a", "ctx-b")

    def test_unknown_step_kind_cannot_bypass_context_bridge_authority(self) -> None:
        with self.assertRaisesRegex(CompositionError, "must be a StepKind"):
            TransitionStep(
                "untyped-bridge",
                "not-a-step-kind",  # type: ignore[arg-type]
                "s0",
                "s1",
                "ctx-a",
                "ctx-b",
            )

    def test_governance_bridge_requires_authority_and_context_change(self) -> None:
        with self.assertRaises(CompositionError):
            TransitionStep(
                "bridge",
                StepKind.GOVERNANCE_BRIDGE,
                "s0",
                "s1",
                "ctx-a",
                "ctx-b",
            )
        with self.assertRaises(CompositionError):
            TransitionStep(
                "bridge",
                StepKind.GOVERNANCE_BRIDGE,
                "s0",
                "s1",
                "ctx-a",
                "ctx-a",
                "authority",
            )

    def test_typed_path_composes_across_governed_context_bridge(self) -> None:
        path = bridge_path()
        pieces = tuple(TransitionPath.singleton(step) for step in path.steps)
        self.assertEqual(path.pre_context, "ctx-a")
        self.assertEqual(path.post_context, "ctx-b")
        self.assertFalse(same_context_only_mutant(pieces))
        self.assertEqual(
            path.trace.items,
            ("resource-a", "governance-a-b", "resource-b"),
        )


class FootprintTests(unittest.TestCase):
    def test_unknown_program_kind_rejects_at_construction(self) -> None:
        with self.assertRaisesRegex(CompositionError, "must be a ProgramKind"):
            Program(
                "untyped-program",
                "not-a-program-kind",  # type: ignore[arg-type]
                "x",
            )

    def test_boolean_cannot_substitute_for_program_or_state_integer(self) -> None:
        with self.assertRaisesRegex(CompositionError, "exact integer"):
            Program(
                "bool-value",
                ProgramKind.SET,
                "x",
                value=True,  # type: ignore[arg-type]
            )
        program = Program("set-x", ProgramKind.SET, "x", value=1)
        with self.assertRaisesRegex(CompositionError, "exact integer"):
            program.apply({"x": True})  # type: ignore[dict-item]

    def test_declared_footprint_must_include_authenticated_read(self) -> None:
        program = Program("copy-x-y", ProgramKind.COPY, "y", source="x")
        exact = program.actual_footprint()
        omitted = Footprint(CanonicalSet.from_iterable(()), exact.writes)
        self.assertTrue(footprint_is_exact(program, exact))
        self.assertFalse(footprint_is_exact(program, omitted))

    def test_write_only_disjointness_has_concrete_false_safe_case(self) -> None:
        copy = Program("copy-x-y", ProgramKind.COPY, "y", source="x")
        update = Program("set-x-1", ProgramKind.SET, "x", value=1)
        state = {"x": 0, "y": 0, "z": 0}
        self.assertTrue(write_only_parallel(copy.actual_footprint(), update.actual_footprint()))
        self.assertFalse(fact_complete_parallel(copy.actual_footprint(), update.actual_footprint()))
        self.assertFalse(schedules_agree(copy, update, state))

    def test_fact_complete_certified_pairs_agree_in_bounded_domain(self) -> None:
        states = (
            dict(zip(("x", "y", "z"), values, strict=True))
            for values in itertools.product((0, 1), repeat=3)
        )
        programs = enumerate_small_programs()
        state_list = tuple(states)
        certified = 0
        for left, right in itertools.permutations(programs, 2):
            if fact_complete_parallel(left.actual_footprint(), right.actual_footprint()):
                certified += 1
                for state in state_list:
                    self.assertTrue(schedules_agree(left, right, state))
        self.assertEqual(certified, 54)

    def test_write_only_false_safe_count_is_stable(self) -> None:
        result = explore()["footprint_exploration"]
        self.assertEqual(result["schedule_checks"], 1056)
        self.assertEqual(result["write_only_false_safe_schedule_checks"], 168)
        self.assertEqual(result["fact_complete_false_safe_schedule_checks"], 0)


class ExplorerTests(unittest.TestCase):
    def test_explorer_records_order_context_and_identity_boundaries(self) -> None:
        result = explore()
        self.assertEqual(result["ordered_manifest"]["distinct_ordered_roots"], 6)
        self.assertEqual(result["ordered_manifest"]["distinct_sorted_mutant_roots"], 1)
        self.assertTrue(result["context_bridge"]["typed_path_accepts"])
        self.assertFalse(result["context_bridge"]["same_context_only_mutant_accepts"])
        self.assertTrue(result["identity"]["internal_total_carrier_accepts"])
        self.assertFalse(result["identity"]["external_admission_accepts"])


if __name__ == "__main__":
    unittest.main()
