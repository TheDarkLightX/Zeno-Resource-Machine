"""Bounded composed model of the draft RFC-0001 commit path.

This module is deliberately small and non-authoritative.  It is an independent
public reading of draft RFC-0001 sections 8 to 12 and of the commit-path
obligations in
``formal/state-machine/semantic_closure_v1/abstraction_and_refinement_obligations.md``
(sections 4 and 6 to 10).  It is not the internal bounded models those documents
mention, it replays none of their evidence, and it approves no RFC semantics.

One transition identity ``T`` and two callers.  Caller A prepares contents
``a``, which consume input ``r1``.  Caller B either duplicates A's contents or
submits conflicting contents ``b``, which consume ``r2``, under the same ``T``.
Each commit attempt runs the logical algorithm of RFC-0001 section 10 as one
atomic step in a linearizable boundary.  The environment then chooses whether
the caller receives the result, loses the acknowledgement after durability,
crashes before durability, or sees a confirmed abort with no write.
``resolve_*`` is the read-only retry resolution of section 10.1.  One policy
update advances the commit freshness tuple as section 4 of the obligations
requires.  ``read_replay`` is a read-only snapshot lookup of the replay record,
the observation a retry-descriptor holder can make; it changes nothing and lets
the quotient see durable state after both callers finish.

The RFC leaves one point open that changes what is reachable: whether a caller
still holds its plan after ``OutcomeUnknown``.  ``PlanReading`` models both
readings.

Each named mutant reproduces one counterexample obligation from RFC-0001's
assurance plan and the review packet.  Mutant names match
``intent_map.json``.  Invariant names follow RFC-0001's formal obligations
where one fits and the intent map otherwise.

Counters are model bounds, not protocol limits.  The model abstracts roots,
hashes and contents to small integers and labels, so it assumes collision
resistance and proves nothing about bytes, storage engines or concurrency
beyond its interleavings.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from reference_models.bounded_explorer import Model


CALLERS = ("A", "B")
INPUT_OF = {"a": "r1", "b": "r2"}
OUTCOMES = (
    "prepared",
    "invalid",
    "observed",
    "newly_committed",
    "already_committed",
    "conflict",
    "stale",
    "rejected_no_write",
    "unknown",
    "not_found",
    "updated",
    "replay_absent",
    "replay_a",
    "replay_b",
)
TERMINAL = frozenset({"newly_committed", "already_committed", "conflict", "invalid"})
REJECTIONS = frozenset({"stale", "conflict", "rejected_no_write", "invalid"})
ENVIRONMENTS = ("", "_ack_lost", "_crash", "_abort")
ALPHABET = tuple(
    action
    for caller in CALLERS
    for action in (
        f"prepare_{caller}",
        f"lookup_{caller}",
        *(f"commit_{caller}{env}" for env in ENVIRONMENTS),
        f"resolve_{caller}",
    )
) + ("policy_update", "read_replay")


class Second(str, Enum):
    """What caller B submits under A's transition identity."""

    DUPLICATE = "duplicate"
    CONFLICTING = "conflicting"


class PlanReading(str, Enum):
    """Whether a caller keeps its plan after ``OutcomeUnknown``.

    ``CONSUMED``: every attempt consumes the plan, so a retry must prepare a new
    plan and pass semantic validation again.  ``RETAINED``: after
    ``OutcomeUnknown`` the caller still holds the plan and may attempt it again.
    """

    CONSUMED = "consumed"
    RETAINED = "retained"


class Mutant(str, Enum):
    """Targeted disaster mutants, named as in ``intent_map.json``."""

    NONE = "none"
    STALE_PLAN_COMMITS = "stale_plan_commits"
    POLICY_CHANGE_REUSES_MACHINE_ROOT = "policy_change_reuses_machine_root"
    REPLAY_LOOKUP_OUTSIDE_COMMIT_BOUNDARY = "replay_lookup_outside_commit_boundary"
    RETRY_DUPLICATES_EFFECT = "retry_duplicates_effect"
    UNKNOWN_REPORTED_AS_REJECTED = "unknown_reported_as_rejected"
    RESOLUTION_REAPPLIES_EFFECT = "resolution_reapplies_effect"
    PARTIAL_DURABLE_COMMIT = "partial_durable_commit"


@dataclass(frozen=True)
class Config:
    """One model instance and its bounds."""

    second: Second
    plan_reading: PlanReading
    mutant: Mutant = Mutant.NONE
    max_attempts: int = 3
    max_prepares: int = 2
    max_policy_updates: int = 1

    def contents(self, caller: str) -> str:
        """Transition contents a caller submits."""

        return "a" if caller == "A" or self.second is Second.DUPLICATE else "b"


@dataclass(frozen=True)
class Durable:
    """Authority-relevant durable projection.

    ``record`` is the replay record for ``T`` (its contents stand for journal
    hash and semantic-effects root).  ``effects`` counts applications of ``T``'s
    semantic effect and ``writes`` counts replay-record insertions.
    """

    record: str | None = None
    journal: str | None = None
    nullifiers: frozenset[str] = frozenset()
    effects: int = 0
    writes: int = 0
    version: int = 0
    root: int = 0
    context: int = 0
    governance_replay: int = 0
    governance_audit: int = 0

    def freshness(self) -> tuple[int, int, int]:
        """The commit freshness tuple: machine-state root, state version, context."""

        return (self.root, self.version, self.context)


@dataclass(frozen=True)
class Caller:
    """One caller: its plan's expected tuple, its knowledge and its budgets.

    ``seen`` exists only for the out-of-boundary lookup mutant.
    """

    plan: tuple[int, int, int] | None = None
    seen: str | None = None
    knows: str | None = None
    attempts: int = 0
    prepares: int = 0


@dataclass(frozen=True)
class State:
    """Durable state, both callers and the governance budget used."""

    durable: Durable = Durable()
    callers: tuple[Caller, Caller] = (Caller(), Caller())
    policy_updates: int = 0


def write(durable: Durable, contents: str) -> Durable:
    """The complete atomic bundle of one new commit of ``contents``."""

    return replace(
        durable,
        record=contents,
        journal=contents,
        nullifiers=durable.nullifiers | {INPUT_OF[contents]},
        effects=durable.effects + 1,
        writes=durable.writes + 1,
        version=durable.version + 1,
        root=durable.root + 1,
    )


def _partial_write(durable: Durable, contents: str) -> Durable:
    """Mutant only: consumption and effect durable, replay, journal and head not."""

    return replace(durable, nullifiers=durable.nullifiers | {INPUT_OF[contents]}, effects=durable.effects + 1)


def classify(config: Config, state: State, index: int) -> str:
    """In-boundary classification for one attempt (RFC-0001 section 10, steps 3 to 6).

    Returns ``write``, ``rewrite`` (mutant re-execution of an exact match),
    ``already``, ``conflict`` or ``stale``.
    """

    caller, contents = state.callers[index], config.contents(CALLERS[index])
    observed = state.durable.record
    if config.mutant is Mutant.REPLAY_LOOKUP_OUTSIDE_COMMIT_BOUNDARY:
        observed = None if caller.seen == "absent" else caller.seen
    if observed == contents:
        return "rewrite" if config.mutant is Mutant.RETRY_DUPLICATES_EFFECT else "already"
    if observed is not None:
        return "conflict"
    if caller.plan != state.durable.freshness() and config.mutant is not Mutant.STALE_PLAN_COMMITS:
        return "stale"
    return "write"


DELIVERED = {"write": "newly_committed", "rewrite": "newly_committed", "already": "already_committed"}


def _with_caller(state: State, index: int, caller: Caller, durable: Durable | None = None) -> State:
    callers = list(state.callers)
    callers[index] = caller
    return replace(state, durable=state.durable if durable is None else durable, callers=(callers[0], callers[1]))


def _prepare(config: Config, state: State, index: int) -> tuple[State, str] | None:
    caller = state.callers[index]
    if caller.plan is not None or caller.knows in TERMINAL or caller.prepares >= config.max_prepares:
        return None
    prepares = caller.prepares + 1
    if INPUT_OF[config.contents(CALLERS[index])] in state.durable.nullifiers:
        return _with_caller(state, index, replace(caller, knows="invalid", prepares=prepares)), "invalid"
    prepared = replace(caller, plan=state.durable.freshness(), knows=None, prepares=prepares)
    return _with_caller(state, index, prepared), "prepared"


def _lookup(config: Config, state: State, index: int) -> tuple[State, str] | None:
    caller = state.callers[index]
    if (
        config.mutant is not Mutant.REPLAY_LOOKUP_OUTSIDE_COMMIT_BOUNDARY
        or caller.seen is not None
        or caller.knows in TERMINAL
        or caller.attempts >= config.max_attempts
    ):
        return None
    seen = state.durable.record or "absent"
    return _with_caller(state, index, replace(caller, seen=seen)), "observed"


def _commit_enabled(config: Config, caller: Caller) -> bool:
    if caller.plan is None or caller.knows in TERMINAL or caller.attempts >= config.max_attempts:
        return False
    return config.mutant is not Mutant.REPLAY_LOOKUP_OUTSIDE_COMMIT_BOUNDARY or caller.seen is not None


def _attempt_result(config: Config, durable: Durable, cls: str, env: str, contents: str) -> tuple[Durable, str]:
    """Durable state and caller outcome for one attempt under one environment choice."""

    writes = cls in ("write", "rewrite")
    if env == "":
        return (write(durable, contents) if writes else durable), DELIVERED.get(cls, cls)
    if env == "_abort":
        return durable, "rejected_no_write"
    unknown = "rejected_no_write" if config.mutant is Mutant.UNKNOWN_REPORTED_AS_REJECTED else "unknown"
    if env == "_ack_lost":
        return (write(durable, contents) if writes else durable), unknown
    if writes and config.mutant is Mutant.PARTIAL_DURABLE_COMMIT:
        return _partial_write(durable, contents), unknown
    return durable, unknown


def _commit(config: Config, state: State, index: int, env: str) -> tuple[State, str] | None:
    caller = state.callers[index]
    if not _commit_enabled(config, caller):
        return None
    cls = classify(config, state, index)
    if env == "_abort" and cls not in ("write", "rewrite"):
        return None
    durable, outcome = _attempt_result(config, state.durable, cls, env, config.contents(CALLERS[index]))
    keep = config.plan_reading is PlanReading.RETAINED and outcome == "unknown"
    after = replace(caller, plan=caller.plan if keep else None, seen=None, knows=outcome, attempts=caller.attempts + 1)
    return _with_caller(state, index, after, durable), outcome


def _resolve(config: Config, state: State, index: int) -> tuple[State, str] | None:
    caller = state.callers[index]
    if caller.knows not in ("unknown", "not_found"):
        return None
    record, contents = state.durable.record, config.contents(CALLERS[index])
    outcome = "not_found" if record is None else "already_committed" if record == contents else "conflict"
    durable = state.durable
    if outcome == "already_committed" and config.mutant is Mutant.RESOLUTION_REAPPLIES_EFFECT:
        durable = replace(durable, effects=durable.effects + 1)
    plan = caller.plan if outcome == "not_found" else None
    return _with_caller(state, index, replace(caller, plan=plan, knows=outcome), durable), outcome


def _policy_update(config: Config, state: State) -> tuple[State, str] | None:
    if state.policy_updates >= config.max_policy_updates:
        return None
    d = state.durable
    reuse = config.mutant is Mutant.POLICY_CHANGE_REUSES_MACHINE_ROOT
    durable = replace(
        d,
        version=d.version + 1,
        root=d.root if reuse else d.root + 1,
        context=d.context + 1,
        governance_replay=d.governance_replay + 1,
        governance_audit=d.governance_audit + 1,
    )
    return replace(state, durable=durable, policy_updates=state.policy_updates + 1), "updated"


def step(config: Config, state: State, action: str) -> tuple[State, str] | None:
    """Apply one action; ``None`` when it is disabled."""

    if action == "policy_update":
        return _policy_update(config, state)
    if action == "read_replay":
        return state, f"replay_{state.durable.record or 'absent'}"
    verb, _, rest = action.partition("_")
    caller, _, env = rest.partition("_")
    index = CALLERS.index(caller)
    if verb == "prepare":
        return _prepare(config, state, index)
    if verb == "lookup":
        return _lookup(config, state, index)
    if verb == "resolve":
        return _resolve(config, state, index)
    return _commit(config, state, index, f"_{env}" if env else "")


def _actor(action: str) -> int | None:
    parts = action.split("_")
    return CALLERS.index(parts[1]) if len(parts) > 1 and parts[1] in CALLERS else None


def _is_commit(action: str) -> bool:
    return action.startswith("commit_")


def state_invariants() -> tuple[tuple[str, object], ...]:
    """Invariants of every reachable durable state."""

    def nullifiers_match(s: State) -> bool:
        expected = frozenset() if s.durable.record is None else frozenset({INPUT_OF[s.durable.record]})
        return s.durable.nullifiers == expected

    return (
        ("ReplayAndNullifierMoveTogether", nullifiers_match),
        ("JournalAndReplayMoveTogether", lambda s: s.durable.journal == s.durable.record),
        ("EffectCountMatchesReplay", lambda s: s.durable.effects == (0 if s.durable.record is None else 1)),
        ("ConflictingPlansHaveAtMostOneNewCommit", lambda s: s.durable.writes <= 1),
        ("MachineRootAndStateVersionAdvanceTogether", lambda s: s.durable.root == s.durable.version),
        (
            "GovernanceReplayAndAuditMoveTogether",
            lambda s: s.durable.governance_replay == s.durable.governance_audit == s.policy_updates,
        ),
    )


def edge_invariants(config: Config) -> tuple[tuple[str, object], ...]:
    """Invariants of every enabled transition ``(source, action, outcome, target)``."""

    def wrote(source: State, target: State) -> bool:
        return target.durable.writes > source.durable.writes

    def unchanged(source: State, target: State) -> bool:
        return target.durable == source.durable

    def own(action: str) -> str:
        return config.contents(CALLERS[_actor(action)])  # type: ignore[index]

    def fresh_only(source: State, action: str, outcome: str, target: State) -> bool:
        if not (_is_commit(action) and wrote(source, target)):
            return True
        return source.callers[_actor(action)].plan == source.durable.freshness()  # type: ignore[index]

    def linearizable(source: State, action: str, outcome: str, target: State) -> bool:
        if not _is_commit(action) or source.durable.record is None:
            return True
        return outcome != "stale" and not wrote(source, target)

    def success_complete(source: State, action: str, outcome: str, target: State) -> bool:
        return outcome != "newly_committed" or target.durable == write(source.durable, own(action))

    def crash_pre_or_post(source: State, action: str, outcome: str, target: State) -> bool:
        if not action.endswith(("_crash", "_abort")):
            return True
        return target.durable in (source.durable, write(source.durable, own(action)))

    return (
        ("FreshCommitOnly", fresh_only),
        ("ReplayClassificationLinearizable", linearizable),
        ("RejectImpliesStateUnchanged", lambda s, a, o, t: o not in REJECTIONS or unchanged(s, t)),
        ("ExactRetryDoesNotChangeState", lambda s, a, o, t: o != "already_committed" or unchanged(s, t)),
        (
            "AlreadyCommittedRequiresExactRecord",
            lambda s, a, o, t: o != "already_committed" or s.durable.record == own(a),
        ),
        ("RetryResolutionAppliesNoEffects", lambda s, a, o, t: not a.startswith("resolve_") or unchanged(s, t)),
        ("CommitSuccessImpliesCompleteEffects", success_complete),
        ("CrashRecoveryIsPreOrPost", crash_pre_or_post),
    )


def model(config: Config) -> Model[State]:
    """The explorer model for one configuration."""

    name = f"rfc0001_commit_path_v1/{config.second.value}/{config.plan_reading.value}/{config.mutant.value}"
    return Model(
        name=name,
        alphabet=ALPHABET,
        outcomes=OUTCOMES,
        initial=State(),
        step=lambda state, action: step(config, state, action),
        state_invariants=state_invariants(),  # type: ignore[arg-type]
        edge_invariants=edge_invariants(config),  # type: ignore[arg-type]
    )


def fields(state: State) -> dict[str, object]:
    """Named state fields, for reporting which ones the quotient cannot see."""

    out: dict[str, object] = {f"durable.{k}": v for k, v in vars(state.durable).items()}
    for name, caller in zip(CALLERS, state.callers, strict=True):
        out.update({f"caller_{name}.{k}": v for k, v in vars(caller).items()})
    out["policy_updates"] = state.policy_updates
    return out
