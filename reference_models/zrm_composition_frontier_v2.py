"""Executable model for ordered composition, context bridges, and exact footprints.

The model is deliberately finite and non-cryptographic.  It distinguishes three
algebraic objects that a protocol implementation must not silently conflate:

* an order-insensitive canonical set inside one transition;
* an order-sensitive trace of accepted transition identifiers;
* a path whose endpoints are authenticated state and validation-context IDs.

It also models why write-set disjointness is insufficient for parallelism when
one transition reads authenticated state written by another transition.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Iterable, Mapping, Sequence


class CompositionError(ValueError):
    """Raised when a model object violates an explicit composition contract."""


def _require_exact_text(value: object, field: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value):
        qualifier = "exact text" if allow_empty else "nonempty exact text"
        raise CompositionError(f"{field} must be {qualifier}")
    return value


def _require_exact_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise CompositionError(f"{field} must be an exact integer")
    return value


@dataclass(frozen=True)
class CanonicalSet:
    """A sorted, unique collection; order is canonicalized, duplicates reject."""

    items: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.items) is not tuple or any(
            type(item) is not str or not item for item in self.items
        ):
            raise CompositionError("canonical set must contain nonempty exact text")
        if self.items != tuple(sorted(self.items)):
            raise CompositionError("canonical set must be sorted")
        if len(self.items) != len(set(self.items)):
            raise CompositionError("canonical set must be unique")

    @classmethod
    def from_iterable(cls, items: Iterable[str]) -> "CanonicalSet":
        """Canonicalize order without silently erasing input multiplicity."""
        values = tuple(items)
        if any(type(item) is not str or not item for item in values):
            raise CompositionError(
                "canonical set input must contain nonempty exact text"
            )
        if len(values) != len(set(values)):
            raise CompositionError("canonical set input must be unique")
        return cls(tuple(sorted(values)))

    def union(self, other: "CanonicalSet") -> "CanonicalSet":
        if self.intersects(other):
            raise CompositionError("canonical sets must be disjoint")
        return CanonicalSet.from_iterable(self.items + other.items)

    def intersects(self, other: "CanonicalSet") -> bool:
        return not set(self.items).isdisjoint(other.items)


@dataclass(frozen=True)
class OrderedTrace:
    """An order-sensitive accepted-journal trace."""

    items: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.items) is not tuple or any(
            type(item) is not str or not item for item in self.items
        ):
            raise CompositionError("trace identifiers must be nonempty exact text")
        if len(self.items) != len(set(self.items)):
            raise CompositionError("trace identifiers must be unique")

    def append(self, other: "OrderedTrace") -> "OrderedTrace":
        if set(self.items) & set(other.items):
            raise CompositionError("ordered traces overlap")
        return OrderedTrace(self.items + other.items)

    def canonical_payload(self) -> list[str]:
        return list(self.items)

    def root(self) -> str:
        payload = json.dumps(self.canonical_payload(), separators=(",", ":")).encode("ascii")
        return hashlib.sha256(b"ZRM-MODEL-ORDERED-TRACE-V1\x00" + payload).hexdigest()

    def incorrectly_sorted_root(self) -> str:
        payload = json.dumps(sorted(self.items), separators=(",", ":")).encode("ascii")
        return hashlib.sha256(b"ZRM-MODEL-SORTED-TRACE-MUTANT-V1\x00" + payload).hexdigest()


class StepKind(str, Enum):
    RESOURCE = "resource"
    GOVERNANCE_BRIDGE = "governance_bridge"


@dataclass(frozen=True)
class TransitionStep:
    """One externally meaningful state transition."""

    event_id: str
    kind: StepKind
    pre_state: str
    post_state: str
    pre_context: str
    post_context: str
    bridge_authority_id: str = ""

    def __post_init__(self) -> None:
        if type(self.kind) is not StepKind:
            raise CompositionError("step kind must be a StepKind")
        for field, value in (
            ("event ID", self.event_id),
            ("pre-state", self.pre_state),
            ("post-state", self.post_state),
            ("pre-context", self.pre_context),
            ("post-context", self.post_context),
        ):
            _require_exact_text(value, field)
        _require_exact_text(
            self.bridge_authority_id, "bridge authority ID", allow_empty=True
        )
        if self.pre_state == self.post_state and self.pre_context == self.post_context:
            raise CompositionError("external step cannot be a no-op")
        if self.kind is StepKind.RESOURCE:
            if self.pre_context != self.post_context:
                raise CompositionError("resource step cannot change validation context")
            if self.bridge_authority_id:
                raise CompositionError("resource step cannot carry bridge authority")
        elif self.kind is StepKind.GOVERNANCE_BRIDGE:
            if self.pre_context == self.post_context:
                raise CompositionError("governance bridge must change validation context")
            if not self.bridge_authority_id:
                raise CompositionError("governance bridge requires authority evidence")


@dataclass(frozen=True)
class TransitionPath:
    """A total path carrier with an internal identity and exact ordered steps."""

    pre_state: str
    post_state: str
    pre_context: str
    post_context: str
    steps: tuple[TransitionStep, ...]

    def __post_init__(self) -> None:
        for field, value in (
            ("path pre-state", self.pre_state),
            ("path post-state", self.post_state),
            ("path pre-context", self.pre_context),
            ("path post-context", self.post_context),
        ):
            _require_exact_text(value, field)
        if type(self.steps) is not tuple or any(
            type(step) is not TransitionStep for step in self.steps
        ):
            raise CompositionError("path steps have an invalid runtime type")
        if not self.steps:
            if self.pre_state != self.post_state or self.pre_context != self.post_context:
                raise CompositionError("empty path must be an endpoint identity")
            return
        first = self.steps[0]
        last = self.steps[-1]
        if (first.pre_state, first.pre_context) != (self.pre_state, self.pre_context):
            raise CompositionError("first step does not match path start")
        if (last.post_state, last.post_context) != (self.post_state, self.post_context):
            raise CompositionError("last step does not match path end")
        for left, right in zip(self.steps, self.steps[1:]):
            if (left.post_state, left.post_context) != (right.pre_state, right.pre_context):
                raise CompositionError("adjacent step endpoints do not match")
        ids = [step.event_id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise CompositionError("path event identifiers must be unique")

    @classmethod
    def identity(cls, state: str, context: str) -> "TransitionPath":
        return cls(state, state, context, context, ())

    @classmethod
    def singleton(cls, step: TransitionStep) -> "TransitionPath":
        return cls(
            step.pre_state,
            step.post_state,
            step.pre_context,
            step.post_context,
            (step,),
        )

    @property
    def trace(self) -> OrderedTrace:
        return OrderedTrace(tuple(step.event_id for step in self.steps))

    def compose(self, other: "TransitionPath") -> "TransitionPath":
        if (self.post_state, self.post_context) != (other.pre_state, other.pre_context):
            raise CompositionError("path endpoints do not compose")
        return TransitionPath(
            self.pre_state,
            other.post_state,
            self.pre_context,
            other.post_context,
            self.steps + other.steps,
        )

    def is_internal_identity(self) -> bool:
        return not self.steps


def admit_external(path: TransitionPath) -> bool:
    """Reject an internal algebraic identity as an externally authored command."""

    return bool(path.steps)


def same_context_only_mutant(paths: Sequence[TransitionPath]) -> bool:
    """Model the overly restrictive rule that one context must span a whole chain."""

    contexts = {path.pre_context for path in paths} | {path.post_context for path in paths}
    return len(contexts) == 1


@dataclass(frozen=True)
class Footprint:
    """Authenticated reads and writes for one pure semantic program."""

    reads: CanonicalSet
    writes: CanonicalSet

    def __post_init__(self) -> None:
        if type(self.reads) is not CanonicalSet or type(self.writes) is not CanonicalSet:
            raise CompositionError("footprint sets have an invalid runtime type")


class ProgramKind(str, Enum):
    SET = "set"
    COPY = "copy"


@dataclass(frozen=True)
class Program:
    """Small deterministic state program with an exact observable footprint."""

    program_id: str
    kind: ProgramKind
    target: str
    source: str = ""
    value: int = 0

    def __post_init__(self) -> None:
        if type(self.kind) is not ProgramKind:
            raise CompositionError("program kind must be a ProgramKind")
        _require_exact_text(self.program_id, "program ID")
        _require_exact_text(self.target, "program target")
        _require_exact_text(self.source, "program source", allow_empty=True)
        _require_exact_int(self.value, "program value")
        if self.kind is ProgramKind.COPY:
            if not self.source or self.source == self.target:
                raise CompositionError("copy requires a distinct source")
        elif self.source:
            raise CompositionError("set program cannot carry a source")

    def actual_footprint(self) -> Footprint:
        reads = (self.source,) if self.kind is ProgramKind.COPY else ()
        return Footprint(CanonicalSet.from_iterable(reads), CanonicalSet.from_iterable((self.target,)))

    def apply(self, state: Mapping[str, int]) -> dict[str, int]:
        for key, value in state.items():
            _require_exact_text(key, "state key")
            _require_exact_int(value, f"state value for {key}")
        if self.target not in state:
            raise CompositionError("program target is absent")
        out = dict(state)
        if self.kind is ProgramKind.SET:
            out[self.target] = self.value
        else:
            if self.source not in state:
                raise CompositionError("program source is absent")
            out[self.target] = state[self.source]
        return out


def footprint_is_exact(program: Program, declared: Footprint) -> bool:
    return program.actual_footprint() == declared


def write_only_parallel(left: Footprint, right: Footprint) -> bool:
    """Unsound mutant: ignores write/read conflicts."""

    return not left.writes.intersects(right.writes)


def fact_complete_parallel(left: Footprint, right: Footprint) -> bool:
    """Require no write/write or write/read conflict in either direction."""

    return (
        not left.writes.intersects(right.writes)
        and not left.writes.intersects(right.reads)
        and not right.writes.intersects(left.reads)
    )


def execute_order(programs: Sequence[Program], state: Mapping[str, int]) -> dict[str, int]:
    out = dict(state)
    for program in programs:
        out = program.apply(out)
    return out


def schedules_agree(left: Program, right: Program, state: Mapping[str, int]) -> bool:
    return execute_order((left, right), state) == execute_order((right, left), state)


def enumerate_small_programs(keys: Sequence[str] = ("x", "y", "z")) -> tuple[Program, ...]:
    programs: list[Program] = []
    for target in keys:
        for value in (0, 1):
            programs.append(Program(f"set-{target}-{value}", ProgramKind.SET, target, value=value))
    for source in keys:
        for target in keys:
            if source != target:
                programs.append(Program(f"copy-{source}-{target}", ProgramKind.COPY, target, source=source))
    return tuple(programs)


__all__ = [
    "CanonicalSet",
    "CompositionError",
    "Footprint",
    "OrderedTrace",
    "Program",
    "ProgramKind",
    "StepKind",
    "TransitionPath",
    "TransitionStep",
    "admit_external",
    "enumerate_small_programs",
    "execute_order",
    "fact_complete_parallel",
    "footprint_is_exact",
    "same_context_only_mutant",
    "schedules_agree",
    "write_only_parallel",
]
