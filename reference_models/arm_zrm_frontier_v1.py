"""Executable frontier model for ARM-style resource proofs composed with ZRM authority.

This module deliberately models algebra and composition only. Cryptographic hash,
proof-system, signature, and discrete-log assumptions are represented explicitly;
no function here creates protocol authority or claims cryptographic security.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Iterable, Mapping, Sequence


GENERATOR = "G"


class FrontierError(ValueError):
    """Raised when an abstract frontier object violates its explicit contract."""


@dataclass(frozen=True, order=True)
class LinearPoint:
    """A formal linear combination over an independent-symbol basis.

    The point is not an elliptic-curve implementation. It records symbolic
    coefficients so that assumptions such as generator independence stay visible.
    """

    coefficients: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        normalized = tuple(sorted((name, value) for name, value in self.coefficients if value != 0))
        if len({name for name, _ in normalized}) != len(normalized):
            raise FrontierError("duplicate formal-basis symbol")
        if normalized != self.coefficients:
            raise FrontierError("linear point must be normalized and sorted")

    @classmethod
    def from_mapping(cls, values: Mapping[str, int]) -> "LinearPoint":
        return cls(tuple(sorted((name, value) for name, value in values.items() if value != 0)))

    @classmethod
    def basis(cls, symbol: str, coefficient: int = 1) -> "LinearPoint":
        return cls.from_mapping({symbol: coefficient})

    @classmethod
    def zero(cls) -> "LinearPoint":
        return cls(())

    def as_mapping(self) -> dict[str, int]:
        return dict(self.coefficients)

    def add(self, other: "LinearPoint") -> "LinearPoint":
        result = self.as_mapping()
        for symbol, coefficient in other.coefficients:
            result[symbol] = result.get(symbol, 0) + coefficient
        return LinearPoint.from_mapping(result)

    def scale(self, scalar: int) -> "LinearPoint":
        return LinearPoint.from_mapping(
            {symbol: coefficient * scalar for symbol, coefficient in self.coefficients}
        )

    def coefficient(self, symbol: str) -> int:
        return self.as_mapping().get(symbol, 0)

    def is_known_generator_multiple(self) -> bool:
        """Return whether the formal point contains no unknown basis symbol."""
        return all(symbol == GENERATOR for symbol, _ in self.coefficients)

    def known_generator_scalar(self) -> int | None:
        return self.coefficient(GENERATOR) if self.is_known_generator_multiple() else None

    def canonical(self) -> list[list[object]]:
        return [[symbol, coefficient] for symbol, coefficient in self.coefficients]


@dataclass(frozen=True)
class KindBasis:
    """Candidate mapping from resource kinds to balance-commitment generators."""

    profile_id: str
    entries: tuple[tuple[str, LinearPoint], ...]
    authenticated: bool

    def __post_init__(self) -> None:
        kinds = [kind for kind, _ in self.entries]
        if not self.profile_id:
            raise FrontierError("basis profile must be nonempty")
        if kinds != sorted(kinds):
            raise FrontierError("kind-basis entries must be sorted")
        if len(kinds) != len(set(kinds)):
            raise FrontierError("kind-basis entries must be unique")

    @classmethod
    def honest(cls, kinds: Iterable[str], profile_id: str = "h2c-v1") -> "KindBasis":
        unique = sorted(set(kinds))
        return cls(
            profile_id=profile_id,
            entries=tuple((kind, LinearPoint.basis(f"K:{kind}")) for kind in unique),
            authenticated=True,
        )

    @classmethod
    def malicious_known_scalars(
        cls,
        known_scalars: Mapping[str, int],
        profile_id: str = "caller-table",
    ) -> "KindBasis":
        return cls(
            profile_id=profile_id,
            entries=tuple(
                (kind, LinearPoint.basis(GENERATOR, scalar))
                for kind, scalar in sorted(known_scalars.items())
            ),
            authenticated=False,
        )

    @classmethod
    def malicious_relation(
        cls,
        kinds: Sequence[str],
        shared_symbol: str = "K:shared",
        profile_id: str = "caller-related-table",
    ) -> "KindBasis":
        return cls(
            profile_id=profile_id,
            entries=tuple((kind, LinearPoint.basis(shared_symbol)) for kind in sorted(set(kinds))),
            authenticated=False,
        )

    def point(self, kind: str) -> LinearPoint:
        for entry_kind, point in self.entries:
            if entry_kind == kind:
                return point
        raise FrontierError(f"unknown kind: {kind}")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "entries": [[kind, point.canonical()] for kind, point in self.entries],
        }

    def root(self) -> str:
        payload = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
        return hashlib.sha256(b"ZRM-MODEL-KIND-BASIS-V1\x00" + payload).hexdigest()

    def matches_canonical_hash_to_curve(self) -> bool:
        expected = KindBasis.honest((kind for kind, _ in self.entries), self.profile_id)
        return self.authenticated and self.entries == expected.entries


@dataclass(frozen=True)
class DeltaEquation:
    """Formal transaction delta Σ quantity[k]·H(k) + blinding·G."""

    net_quantity_by_kind: tuple[tuple[str, int], ...]
    blinding: int

    @classmethod
    def from_mapping(cls, quantities: Mapping[str, int], blinding: int) -> "DeltaEquation":
        return cls(
            tuple(sorted((kind, value) for kind, value in quantities.items() if value != 0)),
            blinding,
        )

    def point(self, basis: KindBasis) -> LinearPoint:
        result = LinearPoint.basis(GENERATOR, self.blinding)
        for kind, quantity in self.net_quantity_by_kind:
            result = result.add(basis.point(kind).scale(quantity))
        return result

    def is_balanced(self) -> bool:
        return not self.net_quantity_by_kind

    def known_binding_key(self, basis: KindBasis) -> int | None:
        """Return the known scalar if the entire delta is a known multiple of G."""
        return self.point(basis).known_generator_scalar()

    def admits_forged_binding_signature(self, basis: KindBasis) -> bool:
        return not self.is_balanced() and self.known_binding_key(basis) is not None


@dataclass(frozen=True)
class KindBasisCertificate:
    """Abstract certificate that a basis root denotes canonical derivations."""

    basis_root: str
    profile_id: str
    derivation_proof_id: str


def certify_kind_basis(basis: KindBasis, proof_id: str) -> KindBasisCertificate:
    """Seal only an authenticated basis equal to the canonical abstract derivation."""
    if not proof_id:
        raise FrontierError("basis derivation proof identifier is required")
    if not basis.matches_canonical_hash_to_curve():
        raise FrontierError("untrusted or noncanonical kind basis")
    return KindBasisCertificate(basis.root(), basis.profile_id, proof_id)


class CoverageDecision(str, Enum):
    ACCEPT = "accept"
    DUPLICATE = "duplicate"
    MISSING = "missing"
    EXTRA = "extra"


@dataclass(frozen=True)
class CoverageResult:
    decision: CoverageDecision
    missing: tuple[str, ...] = ()
    extra: tuple[str, ...] = ()
    duplicates: tuple[str, ...] = ()


def exact_logic_coverage(required_tags: Sequence[str], fact_tags: Sequence[str]) -> CoverageResult:
    """Require one and only one logic fact for every required resource tag."""
    required = tuple(required_tags)
    facts = tuple(fact_tags)
    if len(required) != len(set(required)):
        raise FrontierError("required resource tags must already be unique")
    counts: dict[str, int] = {}
    for tag in facts:
        counts[tag] = counts.get(tag, 0) + 1
    duplicates = tuple(sorted(tag for tag, count in counts.items() if count > 1))
    if duplicates:
        return CoverageResult(CoverageDecision.DUPLICATE, duplicates=duplicates)
    required_set = set(required)
    fact_set = set(facts)
    missing = tuple(sorted(required_set - fact_set))
    if missing:
        return CoverageResult(CoverageDecision.MISSING, missing=missing)
    extra = tuple(sorted(fact_set - required_set))
    if extra:
        return CoverageResult(CoverageDecision.EXTRA, extra=extra)
    return CoverageResult(CoverageDecision.ACCEPT)


def compose_nonzero_scalar(left: int, right: int, modulus: int) -> int | None:
    """Model a composition carrier that refuses the additive identity."""
    if modulus <= 1:
        raise FrontierError("modulus must exceed one")
    if not (0 < left < modulus and 0 < right < modulus):
        raise FrontierError("partial carrier accepts only nonzero residues")
    result = (left + right) % modulus
    return None if result == 0 else result


def compose_total_scalar(left: int, right: int, modulus: int) -> int:
    if modulus <= 1:
        raise FrontierError("modulus must exceed one")
    if not (0 <= left < modulus and 0 <= right < modulus):
        raise FrontierError("residue out of range")
    return (left + right) % modulus


def partial_parenthesizations(a: int, b: int, c: int, modulus: int) -> tuple[int | None, int | None]:
    left_first = compose_nonzero_scalar(a, b, modulus)
    left = None if left_first is None else compose_nonzero_scalar(left_first, c, modulus)
    right_first = compose_nonzero_scalar(b, c, modulus)
    right = None if right_first is None else compose_nonzero_scalar(a, right_first, modulus)
    return left, right


def find_partial_associativity_counterexample(modulus: int) -> tuple[int, int, int, int | None, int | None]:
    for a in range(1, modulus):
        for b in range(1, modulus):
            for c in range(1, modulus):
                left, right = partial_parenthesizations(a, b, c, modulus)
                if left != right:
                    return a, b, c, left, right
    raise FrontierError("no counterexample in selected modulus")


@dataclass(frozen=True)
class SemanticSummary:
    """Canonical proof-independent summary of a shielded resource-transition shard."""

    context_hash: str
    basis_root: str
    profile_id: str
    action_ids: tuple[str, ...]
    consumed_tags: tuple[str, ...]
    created_tags: tuple[str, ...]
    fact_tags: tuple[str, ...]
    delta_rows: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        for label, values in (
            ("action_ids", self.action_ids),
            ("consumed_tags", self.consumed_tags),
            ("created_tags", self.created_tags),
            ("fact_tags", self.fact_tags),
        ):
            if values != tuple(sorted(values)):
                raise FrontierError(f"{label} must be sorted")
            if len(values) != len(set(values)):
                raise FrontierError(f"{label} must be unique")
        if self.delta_rows != tuple(sorted((kind, value) for kind, value in self.delta_rows if value != 0)):
            raise FrontierError("delta rows must be sorted, unique, and nonzero")
        if len({kind for kind, _ in self.delta_rows}) != len(self.delta_rows):
            raise FrontierError("duplicate delta row")
        if set(self.consumed_tags) & set(self.created_tags):
            raise FrontierError("consumed and created tags collide")
        required = self.consumed_tags + self.created_tags
        if exact_logic_coverage(required, self.fact_tags).decision is not CoverageDecision.ACCEPT:
            raise FrontierError("summary lacks exact logic-fact coverage")
        for field in (self.context_hash, self.basis_root, self.profile_id):
            if not field:
                raise FrontierError("summary authority bindings must be nonempty")

    @classmethod
    def singleton(
        cls,
        *,
        context_hash: str,
        basis_root: str,
        profile_id: str,
        action_id: str,
        consumed_tags: Sequence[str],
        created_tags: Sequence[str],
        delta_rows: Mapping[str, int],
    ) -> "SemanticSummary":
        consumed = tuple(sorted(consumed_tags))
        created = tuple(sorted(created_tags))
        facts = tuple(sorted(consumed + created))
        return cls(
            context_hash=context_hash,
            basis_root=basis_root,
            profile_id=profile_id,
            action_ids=(action_id,),
            consumed_tags=consumed,
            created_tags=created,
            fact_tags=facts,
            delta_rows=tuple(sorted((kind, value) for kind, value in delta_rows.items() if value != 0)),
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "context_hash": self.context_hash,
            "basis_root": self.basis_root,
            "profile_id": self.profile_id,
            "action_ids": list(self.action_ids),
            "consumed_tags": list(self.consumed_tags),
            "created_tags": list(self.created_tags),
            "fact_tags": list(self.fact_tags),
            "delta_rows": [[kind, value] for kind, value in self.delta_rows],
        }

    def semantic_root(self) -> str:
        payload = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
        return hashlib.sha256(b"ZRM-MODEL-SEMANTIC-SUMMARY-V1\x00" + payload).hexdigest()

    def compose(self, other: "SemanticSummary") -> "SemanticSummary":
        if self.context_hash != other.context_hash:
            raise FrontierError("context mismatch")
        if self.basis_root != other.basis_root:
            raise FrontierError("kind-basis mismatch")
        if self.profile_id != other.profile_id:
            raise FrontierError("profile mismatch")
        for left, right, label in (
            (self.action_ids, other.action_ids, "duplicate action"),
            (self.consumed_tags, other.consumed_tags, "duplicate consumption"),
            (self.created_tags, other.created_tags, "duplicate creation"),
            (self.fact_tags, other.fact_tags, "duplicate fact"),
        ):
            if set(left) & set(right):
                raise FrontierError(label)
        all_self_tags = set(self.consumed_tags) | set(self.created_tags)
        all_other_tags = set(other.consumed_tags) | set(other.created_tags)
        if all_self_tags & all_other_tags:
            raise FrontierError("cross-summary resource-tag collision")

        rows = dict(self.delta_rows)
        for kind, value in other.delta_rows:
            rows[kind] = rows.get(kind, 0) + value
        return SemanticSummary(
            context_hash=self.context_hash,
            basis_root=self.basis_root,
            profile_id=self.profile_id,
            action_ids=tuple(sorted(self.action_ids + other.action_ids)),
            consumed_tags=tuple(sorted(self.consumed_tags + other.consumed_tags)),
            created_tags=tuple(sorted(self.created_tags + other.created_tags)),
            fact_tags=tuple(sorted(self.fact_tags + other.fact_tags)),
            delta_rows=tuple(sorted((kind, value) for kind, value in rows.items() if value != 0)),
        )


def proof_topology_root(left_root: str, right_root: str) -> str:
    return hashlib.sha256(
        b"ZRM-MODEL-PROOF-TREE-NODE-V1\x00"
        + bytes.fromhex(left_root)
        + bytes.fromhex(right_root)
    ).hexdigest()


@dataclass(frozen=True)
class ShieldedTransitionFact:
    """Model-only sealed-fact payload required to cross into ZRM authority."""

    statement_hash: str
    validation_context_hash: str
    policy_snapshot_hash: str
    kind_basis_root: str
    verifier_policy_id: str
    verifier_release_id: str
    semantic_summary_root: str

    def matches(
        self,
        *,
        statement_hash: str,
        validation_context_hash: str,
        policy_snapshot_hash: str,
        kind_basis_root: str,
        verifier_policy_id: str,
        verifier_release_id: str,
        semantic_summary_root: str,
    ) -> bool:
        return self == ShieldedTransitionFact(
            statement_hash,
            validation_context_hash,
            policy_snapshot_hash,
            kind_basis_root,
            verifier_policy_id,
            verifier_release_id,
            semantic_summary_root,
        )


__all__ = [
    "CoverageDecision",
    "CoverageResult",
    "DeltaEquation",
    "FrontierError",
    "KindBasis",
    "KindBasisCertificate",
    "LinearPoint",
    "SemanticSummary",
    "ShieldedTransitionFact",
    "certify_kind_basis",
    "compose_nonzero_scalar",
    "compose_total_scalar",
    "exact_logic_coverage",
    "find_partial_associativity_counterexample",
    "partial_parenthesizations",
    "proof_topology_root",
]
