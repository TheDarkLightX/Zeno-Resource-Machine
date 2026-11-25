"""Deterministic bounded exploration of small reference state machines.

This module is non-authoritative development tooling.  It explores a finite
model exhaustively and answers three questions about it:

1. **Shortest counterexamples.**  Breadth-first search from the initial state
   merges equal states, so the first violation found for an invariant has the
   fewest actions.  Ties are broken by the model's declared action order.
2. **Exact replay.**  :func:`replay` re-executes a trace from the initial state
   and re-checks the violation without using the exploration.
3. **Coarsest observable state.**  :func:`quotient` merges reachable states that
   give the same outcome to every future action sequence.  The result is the
   smallest machine with the model's observable behavior, together with probe
   words whose outcomes tell every two classes apart.

The quotient is a standard-library port of ``state_discovery::RawModel::quotient``
from Zeno-ADP 0.8.0 (Moore partition refinement with separating probes).  The
tests require it to match Zeno-ADP's answers on committed vectors.

Bounded exploration is not an unbounded proof.  A model exceeding its declared
state limit fails closed with :class:`BoundExceeded` and yields no result.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Hashable
from dataclasses import dataclass
from typing import Generic, TypeVar


S = TypeVar("S", bound=Hashable)
DISABLED = "disabled"


class BoundExceeded(RuntimeError):
    """Exploration reached more states than the declared limit."""


@dataclass(frozen=True)
class Model(Generic[S]):
    """A finite labelled transition system with named invariants.

    ``step(state, action)`` returns ``(next_state, outcome)`` or ``None`` when
    the action is disabled.  ``outcomes`` lists every outcome ``step`` may
    return.  A state invariant is a predicate on one state.  An edge invariant
    is a predicate on ``(source, action, outcome, target)``.
    """

    name: str
    alphabet: tuple[str, ...]
    outcomes: tuple[str, ...]
    initial: S
    step: Callable[[S, str], tuple[S, str] | None]
    state_invariants: tuple[tuple[str, Callable[[S], bool]], ...] = ()
    edge_invariants: tuple[tuple[str, Callable[[S, str, str, S], bool]], ...] = ()

    def __post_init__(self) -> None:
        if not self.alphabet or len(set(self.alphabet)) != len(self.alphabet):
            raise ValueError("the alphabet must be nonempty and duplicate-free")
        if DISABLED in self.outcomes or len(set(self.outcomes)) != len(self.outcomes):
            raise ValueError("outcomes must be duplicate-free and exclude 'disabled'")
        names = [name for name, _ in self.state_invariants + self.edge_invariants]
        if len(set(names)) != len(names):
            raise ValueError("invariant names must be unique")

    def code(self, outcome: str) -> int:
        """Integer code of an outcome: 0 for disabled, then declaration order."""

        if outcome == DISABLED:
            return 0
        return self.outcomes.index(outcome) + 1


@dataclass(frozen=True)
class Violation:
    """The shortest trace that violates one invariant."""

    invariant: str
    kind: str  # "state" or "edge"
    trace: tuple[str, ...]


@dataclass(frozen=True)
class Exploration(Generic[S]):
    """Every reachable state in breadth-first order and the total action table.

    ``next[i][a]`` is the successor of state ``i`` under action ``a``; a
    disabled action is a self-loop.  ``codes[i][a]`` is its outcome code.
    """

    model: Model[S]
    states: tuple[S, ...]
    access: tuple[tuple[int, ...], ...]
    next: tuple[tuple[int, ...], ...]
    codes: tuple[tuple[int, ...], ...]
    violations: tuple[Violation, ...]

    @property
    def edges(self) -> int:
        """Number of enabled transitions."""

        return sum(code != 0 for row in self.codes for code in row)

    def word(self, symbols: tuple[int, ...] | list[int]) -> tuple[str, ...]:
        """Action names of a word of symbol indices."""

        return tuple(self.model.alphabet[symbol] for symbol in symbols)

    def violated(self) -> tuple[str, ...]:
        """Names of violated invariants, in declaration order."""

        return tuple(violation.invariant for violation in self.violations)


def explore(model: Model[S], max_states: int) -> Exploration[S]:
    """Explore every reachable state, merging equal states.

    Raises :class:`BoundExceeded` instead of returning a partial result.
    """

    states: list[S] = [model.initial]
    index: dict[S, int] = {model.initial: 0}
    access: list[tuple[int, ...]] = [()]
    next_rows: list[tuple[int, ...]] = []
    code_rows: list[tuple[int, ...]] = []
    state_found: dict[str, tuple[int, ...]] = {}
    edge_found: dict[str, tuple[int, ...]] = {}
    queue: deque[int] = deque([0])
    while queue:
        current = queue.popleft()
        source = states[current]
        _check_state(model, source, access[current], state_found)
        row_next: list[int] = []
        row_codes: list[int] = []
        for symbol, action in enumerate(model.alphabet):
            result = model.step(source, action)
            if result is None:
                row_next.append(current)
                row_codes.append(0)
                continue
            target, outcome = result
            if target not in index:
                if len(states) >= max_states:
                    raise BoundExceeded(f"{model.name}: more than {max_states} states")
                index[target] = len(states)
                states.append(target)
                access.append(access[current] + (symbol,))
                queue.append(index[target])
            row_next.append(index[target])
            row_codes.append(model.code(outcome))
            _check_edge(model, (source, action, outcome, target), access[current] + (symbol,), edge_found)
        next_rows.append(tuple(row_next))
        code_rows.append(tuple(row_codes))
    violations = _ordered_violations(model, state_found, edge_found)
    return Exploration(model, tuple(states), tuple(access), tuple(next_rows), tuple(code_rows), violations)


def _check_state(model: Model[S], state: S, word: tuple[int, ...], found: dict[str, tuple[int, ...]]) -> None:
    """Record the first, hence shortest, state violating each state invariant."""

    for name, holds in model.state_invariants:
        if name not in found and not holds(state):
            found[name] = word


def _check_edge(
    model: Model[S],
    edge: tuple[S, str, str, S],
    word: tuple[int, ...],
    found: dict[str, tuple[int, ...]],
) -> None:
    """Record the first, hence shortest, edge violating each edge invariant."""

    for name, holds in model.edge_invariants:
        if name not in found and not holds(*edge):
            found[name] = word


def _ordered_violations(
    model: Model[S],
    state_found: dict[str, tuple[int, ...]],
    edge_found: dict[str, tuple[int, ...]],
) -> tuple[Violation, ...]:
    """Violations in invariant declaration order, with action-name traces."""

    out: list[Violation] = []
    for name, _ in model.state_invariants:
        if name in state_found:
            out.append(Violation(name, "state", tuple(model.alphabet[s] for s in state_found[name])))
    for name, _ in model.edge_invariants:
        if name in edge_found:
            out.append(Violation(name, "edge", tuple(model.alphabet[s] for s in edge_found[name])))
    return tuple(out)


def replay(model: Model[S], trace: tuple[str, ...], invariant: str) -> bool:
    """Re-execute ``trace`` from the initial state; return whether it violates ``invariant``.

    A state invariant must fail in the final state.  An edge invariant must fail
    on the final action.  Every action must be enabled.  This does not use any
    exploration result.
    """

    state_checks = dict(model.state_invariants)
    edge_checks = dict(model.edge_invariants)
    if invariant not in state_checks and invariant not in edge_checks:
        raise KeyError(invariant)
    state = model.initial
    for position, action in enumerate(trace):
        result = model.step(state, action)
        if result is None:
            return False
        target, outcome = result
        last = position == len(trace) - 1
        if last and invariant in edge_checks:
            return not edge_checks[invariant](state, action, outcome, target)
        state = target
    return invariant in state_checks and not state_checks[invariant](state)


@dataclass(frozen=True)
class Quotient:
    """The coarsest partition of reachable states that keeps every outcome.

    ``class_of[i]`` is the class of observer state ``i`` (``None`` when it is
    unreachable).  ``gains`` and ``next`` are the class table.  Every two classes
    give different outcome sums on at least one word in ``probes``.  The field
    names follow Zeno-ADP, where ``gains`` are score changes.
    """

    class_of: tuple[int | None, ...]
    start: int
    gains: tuple[tuple[int, ...], ...]
    next: tuple[tuple[int, ...], ...]
    probes: tuple[tuple[int, ...], ...]

    @property
    def classes(self) -> int:
        """Number of classes."""

        return len(self.gains)

    def gain_from(self, cls: int, word: tuple[int, ...] | list[int]) -> int:
        """Sum of outcome codes along ``word`` read from class ``cls``."""

        total = 0
        for symbol in word:
            total += self.gains[cls][symbol]
            cls = self.next[cls][symbol]
        return total

    def signature(self, cls: int) -> tuple[int, ...]:
        """Outcome sums of every probe from ``cls``."""

        return tuple(self.gain_from(cls, probe) for probe in self.probes)


def reachable_access(
    next_table: tuple[tuple[int, ...], ...], start: int
) -> list[tuple[int, ...] | None]:
    """Shortest access word of every state, first in symbol order; ``None`` if unreachable."""

    access: list[tuple[int, ...] | None] = [None] * len(next_table)
    access[start] = ()
    queue: deque[int] = deque([start])
    while queue:
        state = queue.popleft()
        for symbol, target in enumerate(next_table[state]):
            if access[target] is None:
                access[target] = access[state] + (symbol,)  # type: ignore[operator]
                queue.append(target)
    return access


def quotient(next_table: tuple[tuple[int, ...], ...], gains: tuple[tuple[int, ...], ...], start: int = 0) -> Quotient:
    """Coarsest congruence keeping outcome codes and successor classes, with probes.

    Port of Zeno-ADP 0.8.0 ``RawModel::quotient``: partition refinement until
    stable, classes numbered by the shortlex-first access word of a member, and
    probes added until every class has a distinct signature.  Verified before
    return.
    """

    _validate_table(next_table, gains, start)
    access = reachable_access(next_table, start)
    reachable = [state for state, word in enumerate(access) if word is not None]
    levels: list[list[int]] = []
    blocks = _number(reachable, len(next_table), lambda s: tuple(gains[s]))
    while True:
        count = len({blocks[s] for s in reachable})
        levels.append(blocks)
        refined = _number(
            reachable, len(next_table), lambda s, b=blocks: (b[s],) + tuple(b[t] for t in next_table[s])
        )
        if len({refined[s] for s in reachable}) == count:
            break
        blocks = refined
    result = _build(next_table, gains, start, access, reachable, blocks, levels)
    verify(result, next_table, gains, start)
    return result


def _validate_table(next_table: tuple[tuple[int, ...], ...], gains: tuple[tuple[int, ...], ...], start: int) -> None:
    """Reject malformed tables, as Zeno-ADP's ``Observer::new`` does."""

    if not next_table or not next_table[0] or not 0 <= start < len(next_table):
        raise ValueError("the table needs a state, a symbol and an existing start state")
    symbols = len(next_table[0])
    if len(gains) != len(next_table):
        raise ValueError("gains and successors must have one row per state")
    for row, gain_row in zip(next_table, gains, strict=True):
        if len(row) != symbols or len(gain_row) != symbols:
            raise ValueError("a row is malformed")
        if any(not 0 <= target < len(next_table) for target in row):
            raise ValueError("a successor is out of range")


def _number(reachable: list[int], states: int, key: Callable[[int], tuple[int, ...]]) -> list[int]:
    """Block ids numbered by first occurrence in state order; unreachable states get -1."""

    ids: dict[tuple[int, ...], int] = {}
    blocks = [-1] * states
    for state in reachable:
        blocks[state] = ids.setdefault(key(state), len(ids))
    return blocks


def _separate(
    next_table: tuple[tuple[int, ...], ...],
    gains: tuple[tuple[int, ...], ...],
    levels: list[list[int]],
    s: int,
    t: int,
) -> tuple[int, ...]:
    """A word whose outcome sums differ from ``s`` and ``t``, read from the refinement levels."""

    word: list[int] = []
    symbols = range(len(next_table[0]))
    while True:
        round_ = next(r for r, level in enumerate(levels) if level[s] != level[t])
        if round_ == 0:
            word.append(next(a for a in symbols if gains[s][a] != gains[t][a]))
            return tuple(word)
        lower = levels[round_ - 1]
        symbol = next(a for a in symbols if lower[next_table[s][a]] != lower[next_table[t][a]])
        word.append(symbol)
        s, t = next_table[s][symbol], next_table[t][symbol]


def _build(
    next_table: tuple[tuple[int, ...], ...],
    gains: tuple[tuple[int, ...], ...],
    start: int,
    access: list[tuple[int, ...] | None],
    reachable: list[int],
    blocks: list[int],
    levels: list[list[int]],
) -> Quotient:
    """Number classes in shortlex access order, then add probes until signatures differ."""

    order = sorted(reachable, key=lambda s: (len(access[s]), access[s]))  # type: ignore[arg-type]
    class_id: dict[int, int] = {}
    representative: list[int] = []
    class_of: list[int | None] = [None] * len(next_table)
    for state in order:
        if blocks[state] not in class_id:
            class_id[blocks[state]] = len(representative)
            representative.append(state)
        class_of[state] = class_id[blocks[state]]
    table_next = tuple(tuple(class_of[t] for t in next_table[rep]) for rep in representative)
    result = Quotient(
        class_of=tuple(class_of),
        start=class_of[start],  # type: ignore[arg-type]
        gains=tuple(tuple(gains[rep]) for rep in representative),
        next=table_next,  # type: ignore[arg-type]
        probes=(),
    )
    probes: list[tuple[int, ...]] = []
    while True:
        clash = _first_clash(result)
        if clash is None:
            return result
        a, b = clash
        probe = _separate(next_table, gains, levels, representative[a], representative[b])
        if result.gain_from(a, probe) == result.gain_from(b, probe):
            raise ValueError(f"probe does not separate classes {a} and {b}")
        probes.append(probe)
        result = Quotient(result.class_of, result.start, result.gains, result.next, tuple(probes))


def _first_clash(result: Quotient) -> tuple[int, int] | None:
    """The first class whose signature repeats an earlier one, with that earlier class."""

    seen: dict[tuple[int, ...], int] = {}
    for cls in range(result.classes):
        signature = result.signature(cls)
        if signature in seen:
            return seen[signature], cls
        seen[signature] = cls
    return None


def verify(
    result: Quotient, next_table: tuple[tuple[int, ...], ...], gains: tuple[tuple[int, ...], ...], start: int
) -> None:
    """Replay closure and separation against the raw table; raise ``ValueError`` on failure."""

    access = reachable_access(next_table, start)
    if len(result.class_of) != len(next_table) or result.class_of[start] != result.start:
        raise ValueError("certificate shape")
    members = [0] * result.classes
    for state, cls in enumerate(result.class_of):
        if (cls is None) != (access[state] is None):
            raise ValueError("certificate shape")
        if cls is None:
            continue
        members[cls] += 1
        for symbol, target in enumerate(next_table[state]):
            if gains[state][symbol] != result.gains[cls][symbol] or result.class_of[target] != result.next[cls][symbol]:
                raise ValueError(f"closure fails at state {state}, symbol {symbol}")
    if 0 in members:
        raise ValueError("certificate shape")
    if _first_clash(result) is not None:
        raise ValueError("probes do not separate every class")


def undetermined_fields(
    exploration: Exploration[S], result: Quotient, fields: Callable[[S], dict[str, object]]
) -> tuple[str, ...]:
    """Fields on which two states of one class differ: invisible to every future outcome."""

    seen: dict[tuple[int, str], object] = {}
    loose: set[str] = set()
    order: list[str] = []
    for state_index, state in enumerate(exploration.states):
        cls = result.class_of[state_index]
        for name, value in fields(state).items():
            if name not in order:
                order.append(name)
            key = (cls, name)  # type: ignore[assignment]
            if key in seen and seen[key] != value:
                loose.add(name)
            seen.setdefault(key, value)
    return tuple(name for name in order if name in loose)


def table_line(next_table: tuple[tuple[int, ...], ...], gains: tuple[tuple[int, ...], ...], start: int = 0) -> str:
    """One whitespace-separated line: symbols, states, start, successors, then codes.

    This is the input format of the Zeno-ADP cross-check generator.
    """

    values = [len(next_table[0]), len(next_table), start]
    values += [target for row in next_table for target in row]
    values += [code for row in gains for code in row]
    return " ".join(map(str, values))
