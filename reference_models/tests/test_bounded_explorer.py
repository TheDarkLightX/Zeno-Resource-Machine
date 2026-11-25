"""Tests for the bounded explorer and its Zeno-ADP quotient port."""

from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import replace
from pathlib import Path

from reference_models.bounded_explorer import (
    BoundExceeded,
    Model,
    Quotient,
    explore,
    quotient,
    replay,
    table_line,
    undetermined_fields,
    verify,
)
from reference_models.rfc0001_commit_path_explorer import explore_instance, instance_name, instances


VECTORS = json.loads(
    (Path(__file__).resolve().parents[1] / "zeno_adp_vectors" / "vectors_0_8_0.json").read_text(encoding="utf-8")
)


def as_table(rows: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in rows)


def as_json(result: Quotient) -> dict[str, object]:
    return {
        "classes": result.classes,
        "class_of": list(result.class_of),
        "start": result.start,
        "gains": [list(row) for row in result.gains],
        "next": [list(row) for row in result.next],
        "probes": [list(probe) for probe in result.probes],
    }


def counter(limit: int, bad: int) -> Model[int]:
    """Count up by one or two below ``limit``; the invariant fails at ``bad``."""

    def step(state: int, action: str) -> tuple[int, str] | None:
        target = state + (1 if action == "inc" else 2)
        return None if target > limit else (target, "even" if target % 2 == 0 else "odd")

    return Model(
        name="counter",
        alphabet=("inc", "jump"),
        outcomes=("even", "odd"),
        initial=0,
        step=step,
        state_invariants=(("NotBad", lambda s: s != bad),),
        edge_invariants=(("NoJumpOntoBad", lambda s, a, o, t: not (a == "jump" and t == bad)),),
    )


class QuotientMatchesZenoAdp(unittest.TestCase):
    def test_port_matches_every_random_vector(self) -> None:
        for case in VECTORS["random"]:
            with self.subTest(case=case["case"]):
                result = quotient(as_table(case["next"]), as_table(case["gains"]), case["start"])
                self.assertEqual(as_json(result), case["quotient"])

    def test_port_matches_every_model_vector(self) -> None:
        expected = {entry["instance"]: entry for entry in VECTORS["models"]}
        self.assertEqual(len(expected), 2)
        for second in instances():
            name = instance_name(second)
            with self.subTest(instance=name):
                exploration = explore_instance(second)
                line = table_line(exploration.next, exploration.codes)
                self.assertEqual(hashlib.sha256(line.encode("ascii")).hexdigest(), expected[name]["table_sha256"])
                self.assertEqual(as_json(quotient(exploration.next, exploration.codes)), expected[name]["quotient"])

    def test_random_vectors_exercise_merges_unreachable_states_and_several_probes(self) -> None:
        answers = [case["quotient"] for case in VECTORS["random"]]
        self.assertGreaterEqual(sum(a["classes"] < sum(c is not None for c in a["class_of"]) for a in answers), 20)
        self.assertGreaterEqual(sum(None in a["class_of"] for a in answers), 20)
        self.assertGreaterEqual(sum(len(a["probes"]) > 1 for a in answers), 20)


class QuotientCertificate(unittest.TestCase):
    def setUp(self) -> None:
        case = VECTORS["random"][0]
        self.next, self.gains, self.start = as_table(case["next"]), as_table(case["gains"]), case["start"]
        self.result = quotient(self.next, self.gains, self.start)

    def test_tampered_gain_fails_closure(self) -> None:
        gains = list(self.result.gains)
        gains[0] = (gains[0][0] + 1,) + gains[0][1:]
        with self.assertRaises(ValueError):
            verify(replace(self.result, gains=tuple(gains)), self.next, self.gains, self.start)

    def test_dropped_probe_fails_separation(self) -> None:
        self.assertGreater(len(self.result.probes), 1)
        with self.assertRaises(ValueError):
            verify(replace(self.result, probes=self.result.probes[:-1]), self.next, self.gains, self.start)

    def test_malformed_tables_are_rejected(self) -> None:
        for next_table, gains, start in (((), (), 0), (((0,),), ((0,),), 1), (((1,),), ((0,),), 0),
                                         (((0, 0),), ((0,),), 0)):
            with self.subTest(next_table=next_table), self.assertRaises(ValueError):
                quotient(next_table, gains, start)


class Exploration(unittest.TestCase):
    def test_state_counterexample_is_shortest_then_first_in_action_order(self) -> None:
        exploration = explore(counter(limit=9, bad=5), max_states=100)
        (state, edge) = exploration.violations
        self.assertEqual((state.invariant, state.trace), ("NotBad", ("inc", "jump", "jump")))
        self.assertEqual((edge.invariant, edge.trace), ("NoJumpOntoBad", ("inc", "jump", "jump")))
        self.assertTrue(replay(exploration.model, state.trace, "NotBad"))
        self.assertTrue(replay(exploration.model, edge.trace, "NoJumpOntoBad"))

    def test_replay_refuses_traces_that_do_not_violate(self) -> None:
        model = counter(limit=9, bad=5)
        self.assertFalse(replay(model, ("inc", "inc"), "NotBad"))
        self.assertFalse(replay(model, ("jump",) * 5, "NotBad"))  # disabled past the limit
        self.assertFalse(replay(model, ("inc", "inc", "inc", "inc", "inc"), "NoJumpOntoBad"))
        with self.assertRaises(KeyError):
            replay(model, (), "Unknown")

    def test_exploration_fails_closed_above_its_bound(self) -> None:
        with self.assertRaises(BoundExceeded):
            explore(counter(limit=50, bad=-1), max_states=10)

    def test_equal_states_merge_and_disabled_actions_self_loop(self) -> None:
        exploration = explore(counter(limit=3, bad=-1), max_states=10)
        self.assertEqual(exploration.states, (0, 1, 2, 3))
        self.assertEqual(exploration.next[3], (3, 3))
        self.assertEqual(exploration.codes[3], (0, 0))
        self.assertEqual(exploration.edges, 5)

    def test_model_declarations_are_validated(self) -> None:
        base = counter(limit=3, bad=-1)
        for kwargs in ({"alphabet": ("inc", "inc")}, {"alphabet": ()}, {"outcomes": ("disabled",)},
                       {"edge_invariants": (("NotBad", lambda s, a, o, t: True),)}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(base, **kwargs)

    def test_fields_invisible_to_outcomes_are_reported(self) -> None:
        exploration = explore(counter(limit=4, bad=-1), max_states=10)
        result = quotient(exploration.next, exploration.codes)
        loose = undetermined_fields(exploration, result, lambda s: {"parity": s % 2, "value": s})
        self.assertEqual(result.classes, 5)
        self.assertEqual(loose, ())


if __name__ == "__main__":
    unittest.main()
