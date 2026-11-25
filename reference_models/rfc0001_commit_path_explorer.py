"""Exhaustive bounded exploration of the RFC-0001 commit-path model.

    python3 -m reference_models.rfc0001_commit_path_explorer [--pretty] [--check]

Explores the correct model and every named mutant in four instances: a
duplicate or a conflicting second caller, each under both plan readings.  For
the correct model it reports the coarsest observable quotient.  For each mutant
it reports which invariants fail and the shortest trace for each, re-checked by
replay.  ``--check`` compares the output with the committed evidence record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reference_models.bounded_explorer import Exploration, explore, quotient, replay, undetermined_fields
from reference_models.rfc0001_commit_path_v1 import Config, Mutant, PlanReading, Second, State, fields, model


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "rfc0001-commit-path-exploration-v1.json"
SOURCES = ("reference_models/bounded_explorer.py", "reference_models/rfc0001_commit_path_v1.py")
MAX_STATES = 50_000
INTENT = {
    Mutant.STALE_PLAN_COMMITS: "I-CONTEXT-SNAPSHOT-EXACT",
    Mutant.POLICY_CHANGE_REUSES_MACHINE_ROOT: "I-POLICY-UPDATE-CONTEXT",
    Mutant.REPLAY_LOOKUP_OUTSIDE_COMMIT_BOUNDARY: "I-REPLAY-LINEARIZABLE",
    Mutant.RETRY_DUPLICATES_EFFECT: "I-EXACT-ONCE-COMPLETE",
    Mutant.UNKNOWN_REPORTED_AS_REJECTED: "I-OUTCOME-UNKNOWN",
    Mutant.RESOLUTION_REAPPLIES_EFFECT: "I-OUTCOME-UNKNOWN",
    Mutant.PARTIAL_DURABLE_COMMIT: "I-COMMIT-ATOMIC-DURABLE",
}
NON_CLAIMS = (
    "bounded enumeration of two callers, one transition identity and one policy update is not an unbounded proof",
    "this is an independent public reading of draft RFC-0001; it is not the internal models"
    " and replays none of their evidence",
    "the model approves no RFC semantics and creates no protocol bytes, authority capability or implementation",
    "roots, hashes and contents are abstract labels; collision resistance is assumed",
    "storage engines, real concurrency, crash recovery code and external delivery are outside the model",
    "the quotient is minimal only for the declared actions and outcomes of this model",
)


def instances() -> tuple[tuple[Second, PlanReading], ...]:
    """The four model instances, in report order."""

    return tuple((second, reading) for second in Second for reading in PlanReading)


def instance_name(second: Second, reading: PlanReading) -> str:
    """Stable instance label."""

    return f"{second.value}/{reading.value}"


def explore_instance(second: Second, reading: PlanReading, mutant: Mutant = Mutant.NONE) -> Exploration[State]:
    """Explore one instance; fails closed above ``MAX_STATES``."""

    return explore(model(Config(second, reading, mutant)), MAX_STATES)


def _violations(exploration: Exploration[State]) -> list[dict[str, object]]:
    out = []
    for violation in exploration.violations:
        if not replay(exploration.model, violation.trace, violation.invariant):
            raise AssertionError(f"trace does not replay: {violation}")
        out.append({"invariant": violation.invariant, "kind": violation.kind,
                    "length": len(violation.trace), "trace": list(violation.trace)})
    return out


def correct_report(second: Second, reading: PlanReading) -> dict[str, object]:
    """Reachable size, invariant result and coarsest quotient of the correct model."""

    exploration = explore_instance(second, reading)
    result = quotient(exploration.next, exploration.codes)
    return {
        "instance": instance_name(second, reading),
        "states": len(exploration.states),
        "transitions": exploration.edges,
        "violations": _violations(exploration),
        "quotient": {
            "classes": result.classes,
            "probes": [list(exploration.word(probe)) for probe in result.probes],
            "fields_not_determined_by_class": list(undetermined_fields(exploration, result, fields)),
        },
    }


def mutant_report(mutant: Mutant) -> dict[str, object]:
    """Which invariants a mutant violates in each instance, with shortest traces."""

    rows = []
    for second, reading in instances():
        exploration = explore_instance(second, reading, mutant)
        rows.append({"instance": instance_name(second, reading), "states": len(exploration.states),
                     "killed": bool(exploration.violations), "violations": _violations(exploration)})
    killing = [v for row in rows for v in row["violations"]]  # type: ignore[union-attr]
    shortest = min(killing, key=lambda v: (v["length"], v["trace"]), default=None)
    return {"mutant": mutant.value, "intent": INTENT[mutant],
            "killed_in": sum(row["killed"] for row in rows), "of": len(rows),
            "shortest": shortest, "instances": rows}


def source_digests() -> dict[str, str]:
    """SHA-256 of the exact model and explorer sources this record describes."""

    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in SOURCES}


def explore_all() -> dict[str, object]:
    """The complete evidence record."""

    config = Config(Second.DUPLICATE, PlanReading.CONSUMED)
    return {
        "schema": "zrm/rfc0001-commit-path-exploration/v1",
        "status": "non-authoritative bounded design evidence for draft RFC-0001",
        "sources": source_digests(),
        "bounds": {"callers": 2, "transition_identities": 1, "max_attempts": config.max_attempts,
                   "max_prepares": config.max_prepares, "max_policy_updates": config.max_policy_updates,
                   "max_states": MAX_STATES},
        "correct": [correct_report(second, reading) for second, reading in instances()],
        "mutants": [mutant_report(mutant) for mutant in Mutant if mutant is not Mutant.NONE],
        "non_claims": list(NON_CLAIMS),
    }


def render(record: dict[str, object], pretty: bool) -> str:
    """Canonical JSON text of a record."""

    return json.dumps(record, indent=2 if pretty else None, sort_keys=True) + "\n"


def main() -> int:
    """Print the record, or compare it with the committed evidence."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render(explore_all(), pretty=True)
    if args.check:
        same = EVIDENCE.read_text(encoding="utf-8") == text
        print("evidence matches" if same else "evidence differs")
        return 0 if same else 1
    print(text if args.pretty else render(json.loads(text), pretty=False), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
