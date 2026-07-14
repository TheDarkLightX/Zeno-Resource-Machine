"""Bounded oracle for deterministic parallel execution at the ZRM state boundary.

This module is deliberately non-authoritative.  It models an immutable
speculation snapshot, exact point/range read footprints, canonical preset-order
validation, and deterministic re-execution when an observation becomes stale.
It is not a storage engine, accumulator, scheduler, proof system, or commit
implementation.

External batch entry points reject empty manifests and require the supplied
pre-state to satisfy the modeled invariants.  The model checks that precondition
but does not authenticate the state root; production authority must do so.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Mapping, Sequence


RESERVE_LEFT_KEY = 0
RESERVE_RIGHT_KEY = 1
BOUNDED_RANGE_LOWER = 10
BOUNDED_RANGE_UPPER = 20


class BatchModelError(ValueError):
    """Raised when model input violates an explicit bounded contract."""


def _require_exact_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise BatchModelError(f"{field} must be an exact integer")
    return value


def _require_exact_bool(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise BatchModelError(f"{field} must be an exact boolean")
    return value


def _require_exact_text(value: object, field: str) -> str:
    if type(value) is not str or not value:
        raise BatchModelError(f"{field} must be nonempty exact text")
    return value


def _require_int_pair(value: object, field: str) -> tuple[int, int]:
    if type(value) is not tuple or len(value) != 2:
        raise BatchModelError(f"{field} must be an exact integer pair")
    left, right = value
    _require_exact_int(left, f"{field}[0]")
    _require_exact_int(right, f"{field}[1]")
    return left, right


def _digest(domain: bytes, payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(domain + b"\x00" + encoded).hexdigest()


@dataclass(frozen=True)
class BoundedState:
    """Small canonical key/value state plus its consumed-nullifier set."""

    values: tuple[tuple[int, int], ...]
    nullifiers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.values) is not tuple:
            raise BatchModelError("state values must be a tuple")
        for index, item in enumerate(self.values):
            _require_int_pair(item, f"state values[{index}]")
        if type(self.nullifiers) is not tuple:
            raise BatchModelError("state nullifiers must be a tuple")
        for index, nullifier in enumerate(self.nullifiers):
            _require_exact_text(nullifier, f"state nullifiers[{index}]")
        if self.values != tuple(sorted(self.values)):
            raise BatchModelError("state values must be sorted")
        keys = [key for key, _ in self.values]
        if len(keys) != len(set(keys)):
            raise BatchModelError("state keys must be unique")
        if any(not 0 <= key <= 31 for key in keys):
            raise BatchModelError("state key outside bounded domain")
        if any(not 0 <= value <= 2 for _, value in self.values):
            raise BatchModelError("state value outside bounded domain")
        if self.nullifiers != tuple(sorted(self.nullifiers)):
            raise BatchModelError("nullifiers must be sorted")
        if len(self.nullifiers) != len(set(self.nullifiers)):
            raise BatchModelError("nullifiers must be unique")
        if any(not nullifier for nullifier in self.nullifiers):
            raise BatchModelError("nullifiers must be nonempty")

    @classmethod
    def from_mapping(
        cls, values: Mapping[int, int], nullifiers: Sequence[str] = ()
    ) -> "BoundedState":
        return cls(tuple(sorted(values.items())), tuple(sorted(nullifiers)))

    def point(self, key: int) -> int | None:
        _require_exact_int(key, "point key")
        for candidate, value in self.values:
            if candidate == key:
                return value
        return None

    def range_values(self, lower: int, upper: int) -> tuple[tuple[int, int], ...]:
        _require_exact_int(lower, "range lower")
        _require_exact_int(upper, "range upper")
        if not 0 <= lower < upper <= 32:
            raise BatchModelError("invalid bounded range")
        return tuple((key, value) for key, value in self.values if lower <= key < upper)

    def apply(self, writes: Sequence[tuple[int, int]], nullifier: str) -> "BoundedState":
        _require_exact_text(nullifier, "nullifier")
        if nullifier in self.nullifiers:
            raise BatchModelError("duplicate nullifier")
        if any(type(item) is not tuple for item in writes):
            raise BatchModelError("writes must contain exact tuples")
        for index, item in enumerate(writes):
            _require_int_pair(item, f"writes[{index}]")
        ordered_writes = tuple(sorted(writes))
        if ordered_writes != tuple(writes):
            raise BatchModelError("writes must be sorted")
        if len({key for key, _ in ordered_writes}) != len(ordered_writes):
            raise BatchModelError("write keys must be unique")
        values = dict(self.values)
        for key, value in ordered_writes:
            if not 0 <= key <= 31 or not 0 <= value <= 2:
                raise BatchModelError("write outside bounded domain")
            values[key] = value
        return BoundedState.from_mapping(values, self.nullifiers + (nullifier,))

    def canonical_payload(self) -> dict[str, object]:
        return {
            "values": [[key, value] for key, value in self.values],
            "nullifiers": list(self.nullifiers),
        }

    def root(self) -> str:
        return _digest(b"ZRM-MODEL-BOUNDED-STATE-V1", self.canonical_payload())


@dataclass(frozen=True, order=True)
class PointObservation:
    key: int
    value: int | None

    def __post_init__(self) -> None:
        _require_exact_int(self.key, "point observation key")
        if not 0 <= self.key <= 31:
            raise BatchModelError("point observation key outside bounded domain")
        if self.value is not None:
            _require_exact_int(self.value, "point observation value")
            if not 0 <= self.value <= 2:
                raise BatchModelError("point observation value outside bounded domain")


@dataclass(frozen=True, order=True)
class RangeObservation:
    lower: int
    upper: int
    values: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        _require_exact_int(self.lower, "range observation lower")
        _require_exact_int(self.upper, "range observation upper")
        if not 0 <= self.lower < self.upper <= 32:
            raise BatchModelError("invalid range observation")
        if type(self.values) is not tuple:
            raise BatchModelError("range observation values must be a tuple")
        for index, item in enumerate(self.values):
            key, value = _require_int_pair(item, f"range observation values[{index}]")
            if not 0 <= key <= 31 or not 0 <= value <= 2:
                raise BatchModelError("range observation value outside bounded domain")


@dataclass(frozen=True, order=True)
class NullifierObservation:
    nullifier: str
    consumed: bool

    def __post_init__(self) -> None:
        _require_exact_text(self.nullifier, "observed nullifier")
        _require_exact_bool(self.consumed, "observed nullifier status")


@dataclass(frozen=True)
class ReadFootprint:
    """Canonical semantic dependencies observed through the state-read port."""

    points: tuple[PointObservation, ...] = ()
    ranges: tuple[RangeObservation, ...] = ()
    nullifiers: tuple[NullifierObservation, ...] = ()

    def __post_init__(self) -> None:
        for field, values, expected_type in (
            ("point observations", self.points, PointObservation),
            ("range observations", self.ranges, RangeObservation),
            ("nullifier observations", self.nullifiers, NullifierObservation),
        ):
            if type(values) is not tuple:
                raise BatchModelError(f"{field} must be a tuple")
            if any(type(value) is not expected_type for value in values):
                raise BatchModelError(f"{field} have an invalid runtime type")
        if self.points != tuple(sorted(self.points)):
            raise BatchModelError("point observations must be sorted")
        if len({observation.key for observation in self.points}) != len(self.points):
            raise BatchModelError("point observations must have unique keys")
        if self.ranges != tuple(sorted(self.ranges)):
            raise BatchModelError("range observations must be sorted")
        range_keys = [(observation.lower, observation.upper) for observation in self.ranges]
        if len(range_keys) != len(set(range_keys)):
            raise BatchModelError("range observations must have unique bounds")
        for observation in self.ranges:
            if not 0 <= observation.lower < observation.upper <= 32:
                raise BatchModelError("invalid range observation")
            expected = tuple(
                sorted(
                    (key, value)
                    for key, value in observation.values
                    if observation.lower <= key < observation.upper
                )
            )
            if expected != observation.values:
                raise BatchModelError("range result must be exact, sorted, and in bounds")
        if self.nullifiers != tuple(sorted(self.nullifiers)):
            raise BatchModelError("nullifier observations must be sorted")
        observed_nullifiers = [item.nullifier for item in self.nullifiers]
        if len(observed_nullifiers) != len(set(observed_nullifiers)):
            raise BatchModelError("nullifier observations must be unique")

    def matches(self, state: BoundedState) -> bool:
        return all(state.point(item.key) == item.value for item in self.points) and all(
            state.range_values(item.lower, item.upper) == item.values
            for item in self.ranges
        ) and all(
            (item.nullifier in state.nullifiers) is item.consumed
            for item in self.nullifiers
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "points": [[item.key, item.value] for item in self.points],
            "ranges": [
                {
                    "lower": item.lower,
                    "upper": item.upper,
                    "values": [[key, value] for key, value in item.values],
                }
                for item in self.ranges
            ],
            "nullifiers": [
                {"nullifier": item.nullifier, "consumed": item.consumed}
                for item in self.nullifiers
            ],
        }

    def root(self) -> str:
        return _digest(b"ZRM-MODEL-READ-FOOTPRINT-V1", self.canonical_payload())


class _SnapshotReader:
    """The only model API through which a transaction program reads state."""

    def __init__(self, state: BoundedState) -> None:
        self.__state = state
        self.__points: dict[int, int | None] = {}
        self.__ranges: dict[tuple[int, int], tuple[tuple[int, int], ...]] = {}
        self.__nullifiers: dict[str, bool] = {}

    def point(self, key: int) -> int | None:
        value = self.__state.point(key)
        self.__points[key] = value
        return value

    def range_values(self, lower: int, upper: int) -> tuple[tuple[int, int], ...]:
        values = self.__state.range_values(lower, upper)
        self.__ranges[(lower, upper)] = values
        return values

    def nullifier_consumed(self, nullifier: str) -> bool:
        _require_exact_text(nullifier, "observed nullifier")
        consumed = nullifier in self.__state.nullifiers
        self.__nullifiers[nullifier] = consumed
        return consumed

    def footprint(self) -> ReadFootprint:
        return ReadFootprint(
            points=tuple(
                PointObservation(key, value)
                for key, value in sorted(self.__points.items())
            ),
            ranges=tuple(
                RangeObservation(lower, upper, values)
                for (lower, upper), values in sorted(self.__ranges.items())
            ),
            nullifiers=tuple(
                NullifierObservation(nullifier, consumed)
                for nullifier, consumed in sorted(self.__nullifiers.items())
            ),
        )


@dataclass(frozen=True)
class DecisionFootprint:
    """All state observations that determine one transaction outcome.

    Program reads and pre-state guards are over the canonical current state.
    Invariant reads are over the deterministically derived candidate state and
    are absent unless the program accepted and its nullifier was fresh.
    """

    program_reads: ReadFootprint
    pre_state_guards: ReadFootprint = ReadFootprint()
    candidate_invariant_reads: ReadFootprint | None = None
    candidate_invariants_hold: bool | None = None

    def __post_init__(self) -> None:
        if type(self.program_reads) is not ReadFootprint:
            raise BatchModelError("program reads must be a ReadFootprint")
        if type(self.pre_state_guards) is not ReadFootprint:
            raise BatchModelError("pre-state guards must be a ReadFootprint")
        if (
            self.candidate_invariant_reads is not None
            and type(self.candidate_invariant_reads) is not ReadFootprint
        ):
            raise BatchModelError("candidate invariant reads must be a ReadFootprint")
        if self.candidate_invariants_hold is not None:
            _require_exact_bool(
                self.candidate_invariants_hold, "candidate invariant result"
            )
        has_candidate_reads = self.candidate_invariant_reads is not None
        has_candidate_result = self.candidate_invariants_hold is not None
        if has_candidate_reads != has_candidate_result:
            raise BatchModelError(
                "candidate invariant reads and result must be present together"
            )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "program_reads": self.program_reads.canonical_payload(),
            "pre_state_guards": self.pre_state_guards.canonical_payload(),
            "candidate_invariant_reads": (
                None
                if self.candidate_invariant_reads is None
                else self.candidate_invariant_reads.canonical_payload()
            ),
            "candidate_invariants_hold": self.candidate_invariants_hold,
        }

    def root(self) -> str:
        return _digest(b"ZRM-MODEL-DECISION-FOOTPRINT-V1", self.canonical_payload())


class Program(str, Enum):
    RESERVE_IF_OTHER_PRESENT = "reserve_if_other_present"
    INSERT_IF_RANGE_EMPTY = "insert_if_range_empty"


@dataclass(frozen=True)
class TransactionSpec:
    position: int
    transaction_id: str
    nullifier: str
    program: Program
    target_key: int
    range_lower: int | None = None
    range_upper: int | None = None

    def __post_init__(self) -> None:
        _require_exact_int(self.position, "position")
        if self.position < 0:
            raise BatchModelError("position must be nonnegative")
        _require_exact_text(self.transaction_id, "transaction ID")
        _require_exact_text(self.nullifier, "transaction nullifier")
        if type(self.program) is not Program:
            raise BatchModelError("program must be a Program enum value")
        _require_exact_int(self.target_key, "transaction target key")
        if self.range_lower is not None:
            _require_exact_int(self.range_lower, "transaction range lower")
        if self.range_upper is not None:
            _require_exact_int(self.range_upper, "transaction range upper")
        if self.program is Program.RESERVE_IF_OTHER_PRESENT:
            if self.target_key not in (RESERVE_LEFT_KEY, RESERVE_RIGHT_KEY):
                raise BatchModelError("reserve target must be one of the two reserve keys")
            if self.range_lower is not None or self.range_upper is not None:
                raise BatchModelError("reserve program does not accept range bounds")
        elif self.program is Program.INSERT_IF_RANGE_EMPTY:
            if self.range_lower is None or self.range_upper is None:
                raise BatchModelError("range program requires bounds")
            if not 0 <= self.range_lower < self.range_upper <= 32:
                raise BatchModelError("invalid transaction range")
            if not self.range_lower <= self.target_key < self.range_upper:
                raise BatchModelError("insert target must fall inside its observed range")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "position": self.position,
            "transaction_id": self.transaction_id,
            "nullifier": self.nullifier,
            "program": self.program.value,
            "target_key": self.target_key,
            "range_lower": self.range_lower,
            "range_upper": self.range_upper,
        }


def ordered_manifest_root(transactions: Sequence[TransactionSpec]) -> str:
    ordered = _validate_batch(transactions)
    return _digest(
        b"ZRM-MODEL-ORDERED-TRANSACTION-MANIFEST-V1",
        [transaction.canonical_payload() for transaction in ordered],
    )


@dataclass(frozen=True)
class Evaluation:
    accepted: bool
    reason: str
    footprint: ReadFootprint
    writes: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        _require_exact_bool(self.accepted, "evaluation accepted")
        _require_exact_text(self.reason, "evaluation reason")
        if type(self.footprint) is not ReadFootprint:
            raise BatchModelError("evaluation footprint must be a ReadFootprint")
        if type(self.writes) is not tuple:
            raise BatchModelError("evaluation writes must be a tuple")
        for index, item in enumerate(self.writes):
            key, value = _require_int_pair(item, f"evaluation writes[{index}]")
            if not 0 <= key <= 31 or not 0 <= value <= 2:
                raise BatchModelError("evaluation write outside bounded domain")
        if self.accepted and not self.writes:
            raise BatchModelError("accepted evaluation must carry a write")
        if not self.accepted and self.writes:
            raise BatchModelError("rejected evaluation cannot carry writes")
        if self.writes != tuple(sorted(self.writes)):
            raise BatchModelError("evaluation writes must be sorted")


def evaluate(transaction: TransactionSpec, state: BoundedState) -> Evaluation:
    """Execute one closed model program while recording every semantic read."""

    if type(transaction) is not TransactionSpec:
        raise BatchModelError("evaluation transaction has an invalid runtime type")
    if type(state) is not BoundedState:
        raise BatchModelError("evaluation state has an invalid runtime type")
    reader = _SnapshotReader(state)
    if transaction.program is Program.RESERVE_IF_OTHER_PRESENT:
        target_value = reader.point(transaction.target_key) or 0
        other_key = (
            RESERVE_RIGHT_KEY
            if transaction.target_key == RESERVE_LEFT_KEY
            else RESERVE_LEFT_KEY
        )
        other_value = reader.point(other_key) or 0
        if target_value > 0 and other_value > 0:
            return Evaluation(
                accepted=True,
                reason="accepted",
                footprint=reader.footprint(),
                writes=((transaction.target_key, 0),),
            )
        return Evaluation(
            accepted=False,
            reason="minimum_reserve_would_fail",
            footprint=reader.footprint(),
            writes=(),
        )

    if transaction.program is Program.INSERT_IF_RANGE_EMPTY:
        assert transaction.range_lower is not None
        assert transaction.range_upper is not None
        values = reader.range_values(transaction.range_lower, transaction.range_upper)
        if not values:
            return Evaluation(
                accepted=True,
                reason="accepted",
                footprint=reader.footprint(),
                writes=((transaction.target_key, 1),),
            )
        return Evaluation(
            accepted=False,
            reason="range_not_empty",
            footprint=reader.footprint(),
            writes=(),
        )

    raise BatchModelError("unsupported program")


@dataclass(frozen=True)
class SpeculativeResult:
    transaction: TransactionSpec
    snapshot_root: str
    evaluation: Evaluation

    def __post_init__(self) -> None:
        if type(self.transaction) is not TransactionSpec:
            raise BatchModelError("speculative transaction has an invalid runtime type")
        _require_exact_text(self.snapshot_root, "speculation snapshot root")
        if type(self.evaluation) is not Evaluation:
            raise BatchModelError("speculative evaluation has an invalid runtime type")


def speculate(transaction: TransactionSpec, snapshot: BoundedState) -> SpeculativeResult:
    if type(transaction) is not TransactionSpec:
        raise BatchModelError("speculation transaction has an invalid runtime type")
    if type(snapshot) is not BoundedState:
        raise BatchModelError("speculation snapshot has an invalid runtime type")
    return SpeculativeResult(transaction, snapshot.root(), evaluate(transaction, snapshot))


def validate_speculative_result(
    result: SpeculativeResult, snapshot: BoundedState
) -> None:
    """Reject any substituted, omitted, or extra observation or output."""

    if type(result) is not SpeculativeResult:
        raise BatchModelError("speculative result has an invalid runtime type")
    if type(snapshot) is not BoundedState:
        raise BatchModelError("validation snapshot has an invalid runtime type")
    if result.snapshot_root != snapshot.root():
        raise BatchModelError("speculation snapshot mismatch")
    expected = speculate(result.transaction, snapshot)
    if result != expected:
        raise BatchModelError("speculative result or exact read footprint mismatch")


def _state_invariants_through(reader: _SnapshotReader) -> bool:
    left = reader.point(RESERVE_LEFT_KEY) or 0
    right = reader.point(RESERVE_RIGHT_KEY) or 0
    reserve_safe = left + right >= 1
    bounded_range_unique = (
        len(reader.range_values(BOUNDED_RANGE_LOWER, BOUNDED_RANGE_UPPER)) <= 1
    )
    return reserve_safe and bounded_range_unique


def state_invariants(state: BoundedState) -> bool:
    """Two small invariants, evaluated only through the sealed read capability."""

    if type(state) is not BoundedState:
        raise BatchModelError("invariant state has an invalid runtime type")
    return _state_invariants_through(_SnapshotReader(state))


@dataclass(frozen=True)
class TransactionOutcome:
    position: int
    transaction_id: str
    accepted: bool
    reason: str
    used_reexecution: bool
    pre_state_root: str
    post_state_root: str
    decision_footprint_root: str

    def __post_init__(self) -> None:
        _require_exact_int(self.position, "outcome position")
        _require_exact_text(self.transaction_id, "outcome transaction ID")
        _require_exact_bool(self.accepted, "outcome accepted")
        _require_exact_text(self.reason, "outcome reason")
        _require_exact_bool(self.used_reexecution, "outcome reexecution status")
        for field, value in (
            ("outcome pre-state root", self.pre_state_root),
            ("outcome post-state root", self.post_state_root),
            ("outcome decision-footprint root", self.decision_footprint_root),
        ):
            _require_exact_text(value, field)

    def semantic_payload(self) -> dict[str, object]:
        return {
            "position": self.position,
            "transaction_id": self.transaction_id,
            "accepted": self.accepted,
            "reason": self.reason,
            "pre_state_root": self.pre_state_root,
            "post_state_root": self.post_state_root,
            "decision_footprint_root": self.decision_footprint_root,
        }


@dataclass(frozen=True)
class BatchResult:
    initial_state_root: str
    ordered_manifest_root: str
    final_state: BoundedState
    outcomes: tuple[TransactionOutcome, ...]

    def __post_init__(self) -> None:
        _require_exact_text(self.initial_state_root, "batch initial-state root")
        _require_exact_text(self.ordered_manifest_root, "batch ordered-manifest root")
        if type(self.final_state) is not BoundedState:
            raise BatchModelError("batch final state has an invalid runtime type")
        if type(self.outcomes) is not tuple or any(
            type(outcome) is not TransactionOutcome for outcome in self.outcomes
        ):
            raise BatchModelError("batch outcomes have an invalid runtime type")

    def semantic_payload(self) -> dict[str, object]:
        return {
            "initial_state_root": self.initial_state_root,
            "ordered_manifest_root": self.ordered_manifest_root,
            "final_state": self.final_state.canonical_payload(),
            "final_state_root": self.final_state.root(),
            "outcomes": [outcome.semantic_payload() for outcome in self.outcomes],
        }

    def canonical_payload(self) -> dict[str, object]:
        payload = self.semantic_payload()
        payload["reexecuted_positions"] = [
            outcome.position for outcome in self.outcomes if outcome.used_reexecution
        ]
        return payload

    def semantic_root(self) -> str:
        return _digest(b"ZRM-MODEL-BATCH-SEMANTICS-V1", self.semantic_payload())


def _validate_batch(transactions: Sequence[TransactionSpec]) -> tuple[TransactionSpec, ...]:
    if any(type(transaction) is not TransactionSpec for transaction in transactions):
        raise BatchModelError("batch manifest contains an invalid transaction type")
    ordered = tuple(sorted(transactions, key=lambda transaction: transaction.position))
    if not ordered:
        raise BatchModelError("batch manifest must be nonempty")
    if tuple(transaction.position for transaction in ordered) != tuple(range(len(ordered))):
        raise BatchModelError("positions must be dense from zero")
    ids = [transaction.transaction_id for transaction in ordered]
    if len(ids) != len(set(ids)):
        raise BatchModelError("transaction IDs must be unique")
    return ordered


def _validate_initial_state(initial_state: BoundedState) -> None:
    if type(initial_state) is not BoundedState:
        raise BatchModelError("initial state has an invalid runtime type")
    if not state_invariants(initial_state):
        raise BatchModelError("initial state must satisfy the authenticated precondition")


def _apply_evaluation(
    state: BoundedState,
    transaction: TransactionSpec,
    evaluation: Evaluation,
    *,
    used_reexecution: bool,
    enforce_invariants: bool,
) -> tuple[BoundedState, TransactionOutcome]:
    pre_root = state.root()
    if not evaluation.accepted:
        decision_footprint = DecisionFootprint(evaluation.footprint)
        return state, TransactionOutcome(
            transaction.position,
            transaction.transaction_id,
            False,
            evaluation.reason,
            used_reexecution,
            pre_root,
            pre_root,
            decision_footprint.root(),
        )
    guard_reader = _SnapshotReader(state)
    nullifier_consumed = guard_reader.nullifier_consumed(transaction.nullifier)
    guard_reads = guard_reader.footprint()
    if nullifier_consumed:
        decision_footprint = DecisionFootprint(
            evaluation.footprint, pre_state_guards=guard_reads
        )
        return state, TransactionOutcome(
            transaction.position,
            transaction.transaction_id,
            False,
            "duplicate_nullifier",
            used_reexecution,
            pre_root,
            pre_root,
            decision_footprint.root(),
        )
    candidate = state.apply(evaluation.writes, transaction.nullifier)
    invariant_reader = _SnapshotReader(candidate)
    invariants_hold = _state_invariants_through(invariant_reader)
    decision_footprint = DecisionFootprint(
        evaluation.footprint,
        pre_state_guards=guard_reads,
        candidate_invariant_reads=invariant_reader.footprint(),
        candidate_invariants_hold=invariants_hold,
    )
    if enforce_invariants and not invariants_hold:
        return state, TransactionOutcome(
            transaction.position,
            transaction.transaction_id,
            False,
            "invariant_violation",
            used_reexecution,
            pre_root,
            pre_root,
            decision_footprint.root(),
        )
    return candidate, TransactionOutcome(
        transaction.position,
        transaction.transaction_id,
        True,
        "accepted",
        used_reexecution,
        pre_root,
        candidate.root(),
        decision_footprint.root(),
    )


def certify_speculations(
    initial_state: BoundedState,
    transactions: Sequence[TransactionSpec],
    speculative_results: Sequence[SpeculativeResult],
) -> BatchResult:
    """Validate a nonempty batch from a valid pre-state, then refine serially."""

    _validate_initial_state(initial_state)
    ordered = _validate_batch(transactions)
    by_id: dict[str, SpeculativeResult] = {}
    for result in speculative_results:
        if result.transaction.transaction_id in by_id:
            raise BatchModelError("duplicate speculative result")
        by_id[result.transaction.transaction_id] = result
    if set(by_id) != {transaction.transaction_id for transaction in ordered}:
        raise BatchModelError("speculative result coverage mismatch")

    current = initial_state
    outcomes: list[TransactionOutcome] = []
    for transaction in ordered:
        result = by_id[transaction.transaction_id]
        if result.transaction != transaction:
            raise BatchModelError("transaction substitution")
        validate_speculative_result(result, initial_state)

        evaluation = result.evaluation
        used_reexecution = False
        if not evaluation.footprint.matches(current):
            evaluation = evaluate(transaction, current)
            used_reexecution = True
        current, outcome = _apply_evaluation(
            current,
            transaction,
            evaluation,
            used_reexecution=used_reexecution,
            enforce_invariants=True,
        )
        outcomes.append(outcome)

    return BatchResult(
        initial_state.root(), ordered_manifest_root(ordered), current, tuple(outcomes)
    )


def run_certified_batch(
    initial_state: BoundedState,
    transactions: Sequence[TransactionSpec],
    worker_schedule: Sequence[str],
) -> BatchResult:
    """Speculate in the supplied worker order and certify in preset order."""

    _validate_initial_state(initial_state)
    ordered = _validate_batch(transactions)
    lookup = {transaction.transaction_id: transaction for transaction in ordered}
    if any(type(transaction_id) is not str for transaction_id in worker_schedule):
        raise BatchModelError("worker schedule IDs must be exact text")
    if len(worker_schedule) != len(ordered) or set(worker_schedule) != set(lookup):
        raise BatchModelError("worker schedule must be an exact transaction permutation")
    if len(worker_schedule) != len(set(worker_schedule)):
        raise BatchModelError("worker schedule must not duplicate a transaction")
    results = [
        speculate(lookup[transaction_id], initial_state)
        for transaction_id in worker_schedule
    ]
    return certify_speculations(initial_state, ordered, results)


def run_sequential(
    initial_state: BoundedState, transactions: Sequence[TransactionSpec]
) -> BatchResult:
    """Canonical nonempty serial oracle from a valid caller-authenticated pre-state."""

    _validate_initial_state(initial_state)
    ordered = _validate_batch(transactions)
    current = initial_state
    outcomes: list[TransactionOutcome] = []
    for transaction in ordered:
        evaluation = evaluate(transaction, current)
        current, outcome = _apply_evaluation(
            current,
            transaction,
            evaluation,
            used_reexecution=False,
            enforce_invariants=True,
        )
        outcomes.append(outcome)
    return BatchResult(
        initial_state.root(), ordered_manifest_root(ordered), current, tuple(outcomes)
    )


def run_nullifier_only_mutant(
    initial_state: BoundedState, transactions: Sequence[TransactionSpec]
) -> BatchResult:
    """Intentionally broken: trust snapshot results if nullifiers are distinct."""

    _validate_initial_state(initial_state)
    ordered = _validate_batch(transactions)
    current = initial_state
    outcomes: list[TransactionOutcome] = []
    for transaction in ordered:
        evaluation = speculate(transaction, initial_state).evaluation
        current, outcome = _apply_evaluation(
            current,
            transaction,
            evaluation,
            used_reexecution=False,
            enforce_invariants=False,
        )
        outcomes.append(outcome)
    return BatchResult(
        initial_state.root(), ordered_manifest_root(ordered), current, tuple(outcomes)
    )


def reserve_write_skew_batch() -> tuple[TransactionSpec, TransactionSpec]:
    return (
        TransactionSpec(
            position=0,
            transaction_id="reserve-left",
            nullifier="nf-left",
            program=Program.RESERVE_IF_OTHER_PRESENT,
            target_key=RESERVE_LEFT_KEY,
        ),
        TransactionSpec(
            position=1,
            transaction_id="reserve-right",
            nullifier="nf-right",
            program=Program.RESERVE_IF_OTHER_PRESENT,
            target_key=RESERVE_RIGHT_KEY,
        ),
    )


def empty_range_insert_batch() -> tuple[TransactionSpec, TransactionSpec]:
    return (
        TransactionSpec(
            position=0,
            transaction_id="range-insert-a",
            nullifier="nf-range-a",
            program=Program.INSERT_IF_RANGE_EMPTY,
            target_key=11,
            range_lower=BOUNDED_RANGE_LOWER,
            range_upper=BOUNDED_RANGE_UPPER,
        ),
        TransactionSpec(
            position=1,
            transaction_id="range-insert-b",
            nullifier="nf-range-b",
            program=Program.INSERT_IF_RANGE_EMPTY,
            target_key=12,
            range_lower=BOUNDED_RANGE_LOWER,
            range_upper=BOUNDED_RANGE_UPPER,
        ),
    )


__all__ = [
    "BOUNDED_RANGE_LOWER",
    "BOUNDED_RANGE_UPPER",
    "BatchModelError",
    "BatchResult",
    "BoundedState",
    "Evaluation",
    "DecisionFootprint",
    "NullifierObservation",
    "PointObservation",
    "Program",
    "RangeObservation",
    "ReadFootprint",
    "SpeculativeResult",
    "TransactionOutcome",
    "TransactionSpec",
    "certify_speculations",
    "empty_range_insert_batch",
    "evaluate",
    "ordered_manifest_root",
    "reserve_write_skew_batch",
    "run_certified_batch",
    "run_nullifier_only_mutant",
    "run_sequential",
    "speculate",
    "state_invariants",
    "validate_speculative_result",
]
