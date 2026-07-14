"""Bounded oracle for proof-tree-independent ZRM accounting aggregation.

The model keeps two objects separate:

* an ordered, per-leaf coverage manifest recording every opened existing leaf
  row, including an all-zero row; and
* a sparse canonical finite map of material aggregate rows.

Each material row contains two monotone flows.  Resource flow is
``consumed -> created`` and authority flow is
``authorized_burn -> authorized_mint``.  Their signed projections agree iff
the ZRM conservation equation holds::

    created - consumed == authorized_mint - authorized_burn

The recursively composed carrier never stores only that signed projection.
Checked addition of fixed-width signed nets can have parenthesization-dependent
definedness, while nonnegative limbs cannot be rescued by later cancellation.

This module is non-authoritative and non-cryptographic.  In particular, a
coverage occurrence is not proof that a leaf row was derived correctly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TypeAlias


MODEL_U32_MAX = (1 << 32) - 1
MODEL_U128_MAX = (1 << 128) - 1
MODEL_U256_MAX = (1 << 256) - 1
MODEL_MAX_FRAMED_HASH_LIST_ITEMS = (MODEL_U32_MAX - 4) // 32


class AccountingModelError(ValueError):
    """Raised when an input violates an explicit accounting-model contract."""


def _require_exact_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise AccountingModelError(f"{field} must be an exact integer")
    return value


def _require_exact_ascii_text(value: object, field: str) -> str:
    if type(value) is not str or not value or not value.isascii() or "\x00" in value:
        raise AccountingModelError(
            f"{field} must be nonempty NUL-free exact ASCII text"
        )
    return value


def framed_hash_list_payload_bytes(count: int) -> int:
    """Validate and return ``4 + 32*n`` under the outer u32 frame."""

    checked = _require_exact_int(count, "framed hash-list item count")
    if not 0 <= checked <= MODEL_MAX_FRAMED_HASH_LIST_ITEMS:
        raise AccountingModelError(
            "framed hash-list item count exceeds the u32 payload capacity"
        )
    return 4 + 32 * checked


@dataclass(frozen=True, order=True)
class AccountingDimensionV1:
    """One exact ``(resource_kind_id, unit_id)`` accounting dimension."""

    resource_kind_id: str
    unit_id: str

    def __post_init__(self) -> None:
        _require_exact_ascii_text(self.resource_kind_id, "resource kind ID")
        _require_exact_ascii_text(self.unit_id, "unit ID")

    def canonical_payload(self) -> dict[str, str]:
        return {
            "resource_kind_id": self.resource_kind_id,
            "unit_id": self.unit_id,
        }


@dataclass(frozen=True)
class LeafCoverageV1:
    """Exact canonical opened row occurrences for one semantic journal leaf."""

    occurrences: tuple["OpenedLeafRowV1", ...]

    def __post_init__(self) -> None:
        if type(self.occurrences) is not tuple:
            raise AccountingModelError("leaf coverage occurrences must be a tuple")
        if any(type(value) is not OpenedLeafRowV1 for value in self.occurrences):
            raise AccountingModelError(
                "leaf coverage has an invalid occurrence runtime type"
            )
        dimensions = tuple(value.row.dimension for value in self.occurrences)
        if dimensions != tuple(sorted(dimensions)):
            raise AccountingModelError("leaf coverage occurrences must be sorted")
        if len(dimensions) != len(set(dimensions)):
            raise AccountingModelError("leaf coverage dimensions must be unique")
        provenance_ids = tuple(value.provenance_id for value in self.occurrences)
        if len(provenance_ids) != len(set(provenance_ids)):
            raise AccountingModelError("leaf coverage provenance IDs must be unique")

    @property
    def dimensions(self) -> tuple[AccountingDimensionV1, ...]:
        return tuple(value.row.dimension for value in self.occurrences)

    @classmethod
    def from_trusted_occurrences(
        cls, occurrences: Iterable["OpenedLeafRowV1"]
    ) -> "LeafCoverageV1":
        """Canonicalize authoritative occurrences, never untrusted bytes."""

        values = tuple(occurrences)
        if any(type(value) is not OpenedLeafRowV1 for value in values):
            raise AccountingModelError(
                "leaf coverage has an invalid occurrence runtime type"
            )
        dimensions = tuple(value.row.dimension for value in values)
        if len(dimensions) != len(set(dimensions)):
            raise AccountingModelError("trusted leaf coverage dimensions must be unique")
        provenance_ids = tuple(value.provenance_id for value in values)
        if len(provenance_ids) != len(set(provenance_ids)):
            raise AccountingModelError(
                "trusted leaf coverage provenance IDs must be unique"
            )
        return cls(tuple(sorted(values, key=lambda value: value.row.dimension)))


@dataclass(frozen=True)
class AccountingCoverageManifestV1:
    """Ordered leaf boundaries and complete opened dimension occurrences."""

    leaves: tuple[LeafCoverageV1, ...]

    def __post_init__(self) -> None:
        if type(self.leaves) is not tuple:
            raise AccountingModelError("coverage manifest leaves must be a tuple")
        if any(type(leaf) is not LeafCoverageV1 for leaf in self.leaves):
            raise AccountingModelError(
                "coverage manifest has an invalid leaf runtime type"
            )

    @property
    def leaf_count(self) -> int:
        return len(self.leaves)

    @property
    def occurrence_count(self) -> int:
        return sum(len(leaf.occurrences) for leaf in self.leaves)

    def append(
        self, other: "AccountingCoverageManifestV1"
    ) -> "AccountingCoverageManifestV1":
        if type(other) is not AccountingCoverageManifestV1:
            raise AccountingModelError(
                "coverage append operand has an invalid runtime type"
            )
        return AccountingCoverageManifestV1(self.leaves + other.leaves)

    def opened_dimensions(self) -> frozenset[AccountingDimensionV1]:
        return frozenset(
            dimension for leaf in self.leaves for dimension in leaf.dimensions
        )


@dataclass(frozen=True)
class AggregateBoundsV1:
    """Leaf-width, manifest-length, and aggregate-carrier limits."""

    leaf_limb_max: int
    max_leaf_count: int
    aggregate_limb_max: int
    max_dimension_count: int = MODEL_MAX_FRAMED_HASH_LIST_ITEMS
    max_coverage_entry_count: int = MODEL_MAX_FRAMED_HASH_LIST_ITEMS

    def __post_init__(self) -> None:
        leaf_max = _require_exact_int(self.leaf_limb_max, "leaf limb maximum")
        count_max = _require_exact_int(self.max_leaf_count, "maximum leaf count")
        aggregate_max = _require_exact_int(
            self.aggregate_limb_max, "aggregate limb maximum"
        )
        dimension_max = _require_exact_int(
            self.max_dimension_count, "maximum aggregate dimension count"
        )
        coverage_max = _require_exact_int(
            self.max_coverage_entry_count, "maximum coverage entry count"
        )
        if not 1 <= leaf_max <= MODEL_U128_MAX:
            raise AccountingModelError("leaf limb maximum must be in 1..u128::MAX")
        if not 1 <= count_max <= MODEL_U32_MAX:
            raise AccountingModelError("maximum leaf count must be in 1..u32::MAX")
        if not leaf_max <= aggregate_max <= MODEL_U256_MAX:
            raise AccountingModelError(
                "aggregate limb maximum must cover one leaf and fit u256"
            )
        if not 1 <= dimension_max <= MODEL_MAX_FRAMED_HASH_LIST_ITEMS:
            raise AccountingModelError(
                "maximum aggregate dimension count must be positive and fit "
                "the hash-list capacity"
            )
        if not 1 <= coverage_max <= MODEL_MAX_FRAMED_HASH_LIST_ITEMS:
            raise AccountingModelError(
                "maximum coverage entry count must be positive and fit "
                "the hash-list capacity"
            )

    @classmethod
    def protocol(cls) -> "AggregateBoundsV1":
        return cls(MODEL_U128_MAX, MODEL_U32_MAX, MODEL_U256_MAX)

    def allowed_limb_total(self, leaf_count: int) -> int:
        count = _require_exact_int(leaf_count, "aggregate leaf count")
        if not 0 <= count <= self.max_leaf_count:
            raise AccountingModelError("aggregate leaf count exceeds its bound")
        return min(self.aggregate_limb_max, count * self.leaf_limb_max)


@dataclass(frozen=True, order=True)
class MonotoneFlowV1:
    """A generic non-cancelling debit/credit pair."""

    debit_total: int
    credit_total: int

    def __post_init__(self) -> None:
        for field, value in (
            ("flow debit total", self.debit_total),
            ("flow credit total", self.credit_total),
        ):
            limb = _require_exact_int(value, field)
            if not 0 <= limb <= MODEL_U256_MAX:
                raise AccountingModelError(f"{field} must be in 0..u256::MAX")

    @property
    def net(self) -> int:
        return self.credit_total - self.debit_total

    @property
    def has_coverage(self) -> bool:
        return self.debit_total != 0 or self.credit_total != 0

    def checked_merge(
        self, other: "MonotoneFlowV1", limb_limit: int
    ) -> "MonotoneFlowV1 | None":
        if type(other) is not MonotoneFlowV1:
            raise AccountingModelError("flow merge operand has an invalid runtime type")
        limit = _require_exact_int(limb_limit, "flow merge limb limit")
        if not 0 <= limit <= MODEL_U256_MAX:
            raise AccountingModelError("flow merge limb limit must fit u256")
        debit = self.debit_total + other.debit_total
        credit = self.credit_total + other.credit_total
        if debit > limit or credit > limit:
            return None
        return MonotoneFlowV1(debit, credit)


@dataclass(frozen=True, order=True)
class AccountingAggregateRowV1:
    """One dimension's distinct resource and authority flow totals."""

    dimension: AccountingDimensionV1
    resource_flow: MonotoneFlowV1
    authority_flow: MonotoneFlowV1

    def __post_init__(self) -> None:
        if type(self.dimension) is not AccountingDimensionV1:
            raise AccountingModelError("row dimension has an invalid runtime type")
        if type(self.resource_flow) is not MonotoneFlowV1:
            raise AccountingModelError(
                "row resource flow has an invalid runtime type"
            )
        if type(self.authority_flow) is not MonotoneFlowV1:
            raise AccountingModelError(
                "row authority flow has an invalid runtime type"
            )
        if self.resource_flow.net != self.authority_flow.net:
            raise AccountingModelError(
                "row violates resource/authority signed-flow conservation"
            )

    @classmethod
    def from_columns(
        cls,
        dimension: AccountingDimensionV1,
        consumed_atoms: int,
        created_atoms: int,
        authorized_mint_atoms: int,
        authorized_burn_atoms: int,
    ) -> "AccountingAggregateRowV1":
        return cls(
            dimension,
            MonotoneFlowV1(consumed_atoms, created_atoms),
            MonotoneFlowV1(authorized_burn_atoms, authorized_mint_atoms),
        )

    @property
    def consumed_atoms(self) -> int:
        return self.resource_flow.debit_total

    @property
    def created_atoms(self) -> int:
        return self.resource_flow.credit_total

    @property
    def authorized_mint_atoms(self) -> int:
        return self.authority_flow.credit_total

    @property
    def authorized_burn_atoms(self) -> int:
        return self.authority_flow.debit_total

    @property
    def is_material(self) -> bool:
        return self.resource_flow.has_coverage or self.authority_flow.has_coverage

    def checked_merge(
        self, other: "AccountingAggregateRowV1", limb_limit: int
    ) -> "AccountingAggregateRowV1 | None":
        if type(other) is not AccountingAggregateRowV1:
            raise AccountingModelError("row merge operand has an invalid runtime type")
        if self.dimension != other.dimension:
            raise AccountingModelError("row merge dimensions differ")
        resource = self.resource_flow.checked_merge(other.resource_flow, limb_limit)
        authority = self.authority_flow.checked_merge(
            other.authority_flow, limb_limit
        )
        if resource is None or authority is None:
            return None
        return AccountingAggregateRowV1(self.dimension, resource, authority)

    def canonical_payload(self) -> dict[str, object]:
        return {
            **self.dimension.canonical_payload(),
            "consumed_atoms": self.consumed_atoms,
            "created_atoms": self.created_atoms,
            "authorized_burn_atoms": self.authorized_burn_atoms,
            "authorized_mint_atoms": self.authorized_mint_atoms,
        }


@dataclass(frozen=True)
class OpenedLeafRowV1:
    """An exact existing leaf-row opening and its opaque provenance identity."""

    provenance_id: str
    row: AccountingAggregateRowV1

    def __post_init__(self) -> None:
        _require_exact_ascii_text(self.provenance_id, "leaf-row provenance ID")
        if type(self.row) is not AccountingAggregateRowV1:
            raise AccountingModelError(
                "opened leaf row has an invalid row runtime type"
            )


@dataclass(frozen=True)
class SignedDeltaV1:
    """A matched signed resource/authority delta convenience input."""

    dimension: AccountingDimensionV1
    delta: int

    def __post_init__(self) -> None:
        if type(self.dimension) is not AccountingDimensionV1:
            raise AccountingModelError(
                "signed-delta dimension has an invalid runtime type"
            )
        _require_exact_int(self.delta, "signed delta")


def _fold_opened_material_rows(
    coverage_manifest: AccountingCoverageManifestV1,
    limb_limit: int,
) -> tuple[AccountingAggregateRowV1, ...] | None:
    """Independently fold exact opened columns into sparse material support."""

    totals: dict[AccountingDimensionV1, AccountingAggregateRowV1] = {}
    for leaf in coverage_manifest.leaves:
        for occurrence in leaf.occurrences:
            opened = occurrence.row
            if not opened.is_material:
                continue
            previous = totals.get(opened.dimension)
            if previous is None:
                if any(
                    value > limb_limit
                    for value in (
                        opened.resource_flow.debit_total,
                        opened.resource_flow.credit_total,
                        opened.authority_flow.debit_total,
                        opened.authority_flow.credit_total,
                    )
                ):
                    return None
                totals[opened.dimension] = opened
            else:
                merged = previous.checked_merge(opened, limb_limit)
                if merged is None:
                    return None
                totals[opened.dimension] = merged
    return tuple(totals[dimension] for dimension in sorted(totals))


@dataclass(frozen=True)
class AccountingAggregateV1:
    """Sparse canonical rows plus a separate complete leaf-coverage manifest."""

    bounds: AggregateBoundsV1
    coverage_manifest: AccountingCoverageManifestV1
    rows: tuple[AccountingAggregateRowV1, ...]

    def __post_init__(self) -> None:
        if type(self.bounds) is not AggregateBoundsV1:
            raise AccountingModelError("accounting bounds have an invalid runtime type")
        if type(self.coverage_manifest) is not AccountingCoverageManifestV1:
            raise AccountingModelError(
                "accounting coverage manifest has an invalid runtime type"
            )
        limit = self.bounds.allowed_limb_total(self.leaf_count)
        if type(self.rows) is not tuple:
            raise AccountingModelError("accounting rows must be a tuple")
        if len(self.rows) > self.bounds.max_dimension_count:
            raise AccountingModelError(
                "material support exceeds the profile dimension-count bound"
            )
        if (
            self.coverage_manifest.occurrence_count
            > self.bounds.max_coverage_entry_count
        ):
            raise AccountingModelError(
                "coverage occurrences exceed the profile entry-count bound"
            )
        framed_hash_list_payload_bytes(len(self.rows))
        framed_hash_list_payload_bytes(self.coverage_manifest.occurrence_count)
        if any(type(row) is not AccountingAggregateRowV1 for row in self.rows):
            raise AccountingModelError("accounting rows have an invalid runtime type")
        if self.rows != tuple(sorted(self.rows, key=lambda row: row.dimension)):
            raise AccountingModelError(
                "untrusted aggregate rows must already be canonically sorted"
            )

        dimensions = tuple(row.dimension for row in self.rows)
        if len(dimensions) != len(set(dimensions)):
            raise AccountingModelError("accounting row dimensions must be unique")
        if any(not row.is_material for row in self.rows):
            raise AccountingModelError(
                "all-zero rows are coverage occurrences, not material aggregate rows"
            )
        opened = self.coverage_manifest.opened_dimensions()
        if any(dimension not in opened for dimension in dimensions):
            raise AccountingModelError(
                "material aggregate row lacks an opened leaf coverage occurrence"
            )
        for leaf in self.coverage_manifest.leaves:
            for occurrence in leaf.occurrences:
                leaf_limbs = (
                    occurrence.row.resource_flow.debit_total,
                    occurrence.row.resource_flow.credit_total,
                    occurrence.row.authority_flow.debit_total,
                    occurrence.row.authority_flow.credit_total,
                )
                if any(value > self.bounds.leaf_limb_max for value in leaf_limbs):
                    raise AccountingModelError(
                        "opened leaf row exceeds the per-leaf limb bound"
                    )
        for row in self.rows:
            limbs = (
                row.resource_flow.debit_total,
                row.resource_flow.credit_total,
                row.authority_flow.debit_total,
                row.authority_flow.credit_total,
            )
            if any(limb > limit for limb in limbs):
                raise AccountingModelError(
                    "accounting limb exceeds leaf-count-derived aggregate bound"
                )
        expected_rows = _fold_opened_material_rows(self.coverage_manifest, limit)
        if expected_rows is None:
            raise AccountingModelError("opened leaf rows overflow aggregate bounds")
        if self.rows != expected_rows:
            raise AccountingModelError(
                "material rows do not equal the exact opened leaf-column fold"
            )

    @property
    def leaf_count(self) -> int:
        return self.coverage_manifest.leaf_count

    @classmethod
    def from_canonical_material_rows(
        cls,
        bounds: AggregateBoundsV1,
        coverage_manifest: AccountingCoverageManifestV1,
        rows: tuple[AccountingAggregateRowV1, ...],
    ) -> "AccountingAggregateV1":
        """Strict untrusted constructor: no sorting, filtering, or deduplication."""

        if type(rows) is not tuple:
            raise AccountingModelError("canonical material rows must be a tuple")
        return cls(bounds, coverage_manifest, rows)

    @classmethod
    def from_trusted_derived_rows(
        cls,
        bounds: AggregateBoundsV1,
        coverage_manifest: AccountingCoverageManifestV1,
        rows: Iterable[AccountingAggregateRowV1],
    ) -> "AccountingAggregateV1":
        """Canonicalize authoritative derived facts at an explicit trust boundary."""

        values = tuple(rows)
        if any(type(row) is not AccountingAggregateRowV1 for row in values):
            raise AccountingModelError("trusted rows have an invalid runtime type")
        dimensions = tuple(row.dimension for row in values)
        if len(dimensions) != len(set(dimensions)):
            raise AccountingModelError("trusted row input must be unique")
        material = tuple(row for row in values if row.is_material)
        return cls(
            bounds,
            coverage_manifest,
            tuple(sorted(material, key=lambda row: row.dimension)),
        )

    @classmethod
    def leaf_from_canonical_opened_rows(
        cls,
        bounds: AggregateBoundsV1,
        opened_rows: tuple[OpenedLeafRowV1, ...],
    ) -> "AccountingAggregateV1":
        """Strictly project canonical existing leaf rows into sparse material rows.

        A four-zero existing leaf row remains in coverage but is omitted from the
        sparse aggregate for compatibility with the current leaf ABI.  A later
        profile may reject such a leaf before this projection.
        """

        if type(opened_rows) is not tuple:
            raise AccountingModelError("opened leaf rows must be a tuple")
        if any(type(row) is not OpenedLeafRowV1 for row in opened_rows):
            raise AccountingModelError(
                "opened leaf rows have an invalid runtime type"
            )
        coverage = LeafCoverageV1(opened_rows)
        material = tuple(
            occurrence.row for occurrence in opened_rows if occurrence.row.is_material
        )
        return cls(
            bounds,
            AccountingCoverageManifestV1((coverage,)),
            material,
        )

    @classmethod
    def leaf_from_trusted_opened_rows(
        cls,
        bounds: AggregateBoundsV1,
        opened_rows: Iterable[OpenedLeafRowV1],
    ) -> "AccountingAggregateV1":
        """Sort authoritative opened rows before the strict leaf projection."""

        values = tuple(opened_rows)
        if any(type(row) is not OpenedLeafRowV1 for row in values):
            raise AccountingModelError(
                "trusted opened rows have an invalid runtime type"
            )
        dimensions = tuple(row.row.dimension for row in values)
        if len(dimensions) != len(set(dimensions)):
            raise AccountingModelError("trusted opened row input must be unique")
        provenance_ids = tuple(row.provenance_id for row in values)
        if len(provenance_ids) != len(set(provenance_ids)):
            raise AccountingModelError(
                "trusted opened row provenance IDs must be unique"
            )
        return cls.leaf_from_canonical_opened_rows(
            bounds, tuple(sorted(values, key=lambda row: row.row.dimension))
        )

    @classmethod
    def leaf_from_trusted_signed_deltas(
        cls,
        bounds: AggregateBoundsV1,
        deltas: Iterable[SignedDeltaV1],
    ) -> "AccountingAggregateV1":
        """Lift trusted matched mint/burn deltas into both monotone flows."""

        if type(bounds) is not AggregateBoundsV1:
            raise AccountingModelError("accounting bounds have an invalid runtime type")
        values = tuple(deltas)
        if any(type(delta) is not SignedDeltaV1 for delta in values):
            raise AccountingModelError("signed deltas have an invalid runtime type")
        dimensions = tuple(delta.dimension for delta in values)
        if len(dimensions) != len(set(dimensions)):
            raise AccountingModelError("signed-delta dimensions must be unique")

        rows = []
        for index, delta in enumerate(values):
            if not -bounds.leaf_limb_max <= delta.delta <= bounds.leaf_limb_max:
                raise AccountingModelError("signed delta exceeds the leaf limb bound")
            debit = -delta.delta if delta.delta < 0 else 0
            credit = delta.delta if delta.delta > 0 else 0
            flow = MonotoneFlowV1(debit, credit)
            rows.append(
                OpenedLeafRowV1(
                    f"trusted-signed-delta:{index}",
                    AccountingAggregateRowV1(delta.dimension, flow, flow),
                )
            )
        return cls.leaf_from_trusted_opened_rows(bounds, rows)

    @classmethod
    def zero(cls, bounds: AggregateBoundsV1) -> "AccountingAggregateV1":
        """Internal empty-map, leaf-count-zero identity."""

        return cls(bounds, AccountingCoverageManifestV1(()), ())

    @property
    def has_material_support(self) -> bool:
        return bool(self.rows)

    def row(self, dimension: AccountingDimensionV1) -> AccountingAggregateRowV1:
        if type(dimension) is not AccountingDimensionV1:
            raise AccountingModelError(
                "requested dimension has an invalid runtime type"
            )
        for row in self.rows:
            if row.dimension == dimension:
                return row
        raise AccountingModelError("requested dimension is outside material support")

    def checked_merge(
        self, other: "AccountingAggregateV1"
    ) -> "AccountingAggregateV1 | None":
        """Merge sparse supports by exact union, treating absence as internal zero."""

        if type(other) is not AccountingAggregateV1:
            raise AccountingModelError("merge operand has an invalid runtime type")
        if self.bounds != other.bounds:
            raise AccountingModelError("merge accounting bounds differ")
        parent_leaf_count = self.leaf_count + other.leaf_count
        if parent_leaf_count > self.bounds.max_leaf_count:
            return None
        parent_coverage_entry_count = (
            self.coverage_manifest.occurrence_count
            + other.coverage_manifest.occurrence_count
        )
        if parent_coverage_entry_count > self.bounds.max_coverage_entry_count:
            return None
        parent_dimensions = frozenset(row.dimension for row in self.rows) | frozenset(
            row.dimension for row in other.rows
        )
        if len(parent_dimensions) > self.bounds.max_dimension_count:
            return None

        coverage = self.coverage_manifest.append(other.coverage_manifest)
        limit = self.bounds.allowed_limb_total(parent_leaf_count)

        merged_rows: list[AccountingAggregateRowV1] = []
        left_index = 0
        right_index = 0
        while left_index < len(self.rows) or right_index < len(other.rows):
            if left_index == len(self.rows):
                merged_rows.extend(other.rows[right_index:])
                break
            if right_index == len(other.rows):
                merged_rows.extend(self.rows[left_index:])
                break
            left = self.rows[left_index]
            right = other.rows[right_index]
            if left.dimension < right.dimension:
                merged_rows.append(left)
                left_index += 1
            elif right.dimension < left.dimension:
                merged_rows.append(right)
                right_index += 1
            else:
                merged = left.checked_merge(right, limit)
                if merged is None:
                    return None
                merged_rows.append(merged)
                left_index += 1
                right_index += 1
        return AccountingAggregateV1(
            self.bounds,
            coverage,
            tuple(merged_rows),
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "leaf_count": self.leaf_count,
            "bounds": {
                "leaf_limb_max": self.bounds.leaf_limb_max,
                "max_leaf_count": self.bounds.max_leaf_count,
                "aggregate_limb_max": self.bounds.aggregate_limb_max,
                "max_dimension_count": self.bounds.max_dimension_count,
                "max_coverage_entry_count": (
                    self.bounds.max_coverage_entry_count
                ),
            },
            "coverage_manifest": [
                [
                    {
                        "provenance_id": occurrence.provenance_id,
                        "opened_row": occurrence.row.canonical_payload(),
                    }
                    for occurrence in leaf.occurrences
                ]
                for leaf in self.coverage_manifest.leaves
            ],
            "material_rows": [row.canonical_payload() for row in self.rows],
        }


def has_nonempty_segment_carrier(aggregate: AccountingAggregateV1) -> bool:
    """Distinguish a semantic leaf from the internal identity, not admit it."""

    if type(aggregate) is not AccountingAggregateV1:
        raise AccountingModelError("segment aggregate has an invalid runtime type")
    return aggregate.leaf_count > 0


def admit_material_accounting_row(row: AccountingAggregateRowV1) -> bool:
    """An emitted sparse row must be material; four-zero rows stay coverage-only."""

    if type(row) is not AccountingAggregateRowV1:
        raise AccountingModelError("material row has an invalid runtime type")
    return row.is_material


def resource_only_projection(
    row: AccountingAggregateRowV1,
) -> tuple[AccountingDimensionV1, int, int]:
    """The intentionally lossy two-column projection used as a mutant."""

    if type(row) is not AccountingAggregateRowV1:
        raise AccountingModelError("projected row has an invalid runtime type")
    return row.dimension, row.consumed_atoms, row.created_atoms


@dataclass(frozen=True)
class AccountingEntryV1:
    """One ordered semantic-manifest entry and its accounting leaf projection."""

    entry_id: str
    aggregate: AccountingAggregateV1

    def __post_init__(self) -> None:
        _require_exact_ascii_text(self.entry_id, "accounting entry ID")
        if type(self.aggregate) is not AccountingAggregateV1:
            raise AccountingModelError("entry aggregate has an invalid runtime type")
        if self.aggregate.leaf_count != 1:
            raise AccountingModelError("manifest entry must carry exactly one leaf")


@dataclass(frozen=True)
class AccountingManifestV1:
    """A nonempty ordered semantic manifest, independent of proof topology."""

    entries: tuple[AccountingEntryV1, ...]

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple or not self.entries:
            raise AccountingModelError("accounting manifest must be nonempty")
        if any(type(entry) is not AccountingEntryV1 for entry in self.entries):
            raise AccountingModelError(
                "accounting manifest entries have an invalid runtime type"
            )
        entry_ids = tuple(entry.entry_id for entry in self.entries)
        if len(entry_ids) != len(set(entry_ids)):
            raise AccountingModelError("accounting manifest entry IDs must be unique")
        first_bounds = self.entries[0].aggregate.bounds
        if len(self.entries) > first_bounds.max_leaf_count:
            raise AccountingModelError("accounting manifest exceeds its leaf-count bound")
        if any(
            entry.aggregate.bounds != first_bounds for entry in self.entries[1:]
        ):
            raise AccountingModelError(
                "accounting manifest entries must share aggregate bounds"
            )

    @property
    def entry_ids(self) -> tuple[str, ...]:
        return tuple(entry.entry_id for entry in self.entries)


def admit_external_manifest(manifest: AccountingManifestV1) -> bool:
    """External identity exclusion is nonempty-manifest, not nonzero accounting."""

    if type(manifest) is not AccountingManifestV1:
        raise AccountingModelError("external manifest has an invalid runtime type")
    return bool(manifest.entries)


def is_actual_state_noop(pre_state_root: str, post_state_root: str) -> bool:
    """State-level no-op predicate, intentionally independent of accounting net."""

    _require_exact_ascii_text(pre_state_root, "pre-state root")
    _require_exact_ascii_text(post_state_root, "post-state root")
    return pre_state_root == post_state_root


@dataclass(frozen=True)
class AccountingLeafV1:
    entry: AccountingEntryV1

    def __post_init__(self) -> None:
        if type(self.entry) is not AccountingEntryV1:
            raise AccountingModelError("tree leaf has an invalid runtime type")


@dataclass(frozen=True)
class AccountingBranchV1:
    left: "AccountingTreeV1"
    right: "AccountingTreeV1"

    def __post_init__(self) -> None:
        if type(self.left) not in (AccountingLeafV1, AccountingBranchV1):
            raise AccountingModelError("tree left child has an invalid runtime type")
        if type(self.right) not in (AccountingLeafV1, AccountingBranchV1):
            raise AccountingModelError("tree right child has an invalid runtime type")


AccountingTreeV1: TypeAlias = AccountingLeafV1 | AccountingBranchV1


def tree_entry_ids(tree: AccountingTreeV1) -> tuple[str, ...]:
    if type(tree) is AccountingLeafV1:
        return (tree.entry.entry_id,)
    if type(tree) is AccountingBranchV1:
        return tree_entry_ids(tree.left) + tree_entry_ids(tree.right)
    raise AccountingModelError("accounting tree has an invalid runtime type")


def _fold_tree(tree: AccountingTreeV1) -> AccountingAggregateV1 | None:
    if type(tree) is AccountingLeafV1:
        return tree.entry.aggregate
    if type(tree) is not AccountingBranchV1:
        raise AccountingModelError("accounting tree has an invalid runtime type")
    left = _fold_tree(tree.left)
    right = _fold_tree(tree.right)
    if left is None or right is None:
        return None
    return left.checked_merge(right)


def fold_tree(
    manifest: AccountingManifestV1, tree: AccountingTreeV1
) -> AccountingAggregateV1 | None:
    if type(manifest) is not AccountingManifestV1:
        raise AccountingModelError("manifest has an invalid runtime type")
    if tree_entry_ids(tree) != manifest.entry_ids:
        raise AccountingModelError("tree leaves do not equal the ordered manifest")
    return _fold_tree(tree)


def fold_manifest(manifest: AccountingManifestV1) -> AccountingAggregateV1 | None:
    if type(manifest) is not AccountingManifestV1:
        raise AccountingModelError("manifest has an invalid runtime type")
    result: AccountingAggregateV1 | None = manifest.entries[0].aggregate
    for entry in manifest.entries[1:]:
        if result is None:
            return None
        result = result.checked_merge(entry.aggregate)
    return result


def all_ordered_trees(
    entries: tuple[AccountingEntryV1, ...],
) -> tuple[AccountingTreeV1, ...]:
    if type(entries) is not tuple or not entries:
        raise AccountingModelError("tree entries must be a nonempty tuple")
    if any(type(entry) is not AccountingEntryV1 for entry in entries):
        raise AccountingModelError("tree entries have an invalid runtime type")
    if len(entries) == 1:
        return (AccountingLeafV1(entries[0]),)

    trees: list[AccountingTreeV1] = []
    for split in range(1, len(entries)):
        for left in all_ordered_trees(entries[:split]):
            for right in all_ordered_trees(entries[split:]):
                trees.append(AccountingBranchV1(left, right))
    return tuple(trees)


def all_tree_results_agree(manifest: AccountingManifestV1) -> bool:
    expected = fold_manifest(manifest)
    return all(
        fold_tree(manifest, tree) == expected
        for tree in all_ordered_trees(manifest.entries)
    )


def checked_signed_add(bound: int, left: int, right: int) -> int | None:
    """Symmetric checked addition used to expose the signed-net mutant."""

    checked_bound = _require_exact_int(bound, "signed bound")
    if not 1 <= checked_bound <= MODEL_U256_MAX:
        raise AccountingModelError("signed bound must be in 1..u256::MAX")
    checked_left = _require_exact_int(left, "signed left operand")
    checked_right = _require_exact_int(right, "signed right operand")
    if not -checked_bound <= checked_left <= checked_bound:
        raise AccountingModelError("signed left operand exceeds the declared bound")
    if not -checked_bound <= checked_right <= checked_bound:
        raise AccountingModelError("signed right operand exceeds the declared bound")
    total = checked_left + checked_right
    return total if -checked_bound <= total <= checked_bound else None


def _checked_signed_fold_inputs(
    bound: int, a: int, b: int, c: int
) -> tuple[int, tuple[int, int, int]]:
    checked_bound = _require_exact_int(bound, "signed bound")
    if not 1 <= checked_bound <= MODEL_U256_MAX:
        raise AccountingModelError("signed bound must be in 1..u256::MAX")
    values = tuple(
        _require_exact_int(value, field)
        for value, field in (
            (a, "signed operand a"),
            (b, "signed operand b"),
            (c, "signed operand c"),
        )
    )
    if any(not -checked_bound <= value <= checked_bound for value in values):
        raise AccountingModelError("signed fold operand exceeds the declared bound")
    return checked_bound, values


def signed_left_fold3(bound: int, a: int, b: int, c: int) -> int | None:
    checked_bound, values = _checked_signed_fold_inputs(bound, a, b, c)
    first = checked_signed_add(checked_bound, values[0], values[1])
    return (
        None
        if first is None
        else checked_signed_add(checked_bound, first, values[2])
    )


def signed_right_fold3(bound: int, a: int, b: int, c: int) -> int | None:
    checked_bound, values = _checked_signed_fold_inputs(bound, a, b, c)
    second = checked_signed_add(checked_bound, values[1], values[2])
    return (
        None
        if second is None
        else checked_signed_add(checked_bound, values[0], second)
    )
