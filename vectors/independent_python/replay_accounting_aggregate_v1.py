"""Independently generate and replay proposed accounting-aggregate vectors.

This script intentionally does not import the executable reference model.  It
rederives the byte layouts, conservation checks, ordering, wide aggregation,
and framed SHA-256 hashes using only the Python standard library.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VECTOR_DIRECTORY = ROOT / "vectors"
MANIFEST_PATH = VECTOR_DIRECTORY / "accounting_aggregate_v1.json"

ROW_DOMAIN = b"zrm.accounting_aggregate_row.v1"
ROWS_DOMAIN = b"zrm.accounting_aggregate_rows.v1"
COVERAGE_ENTRY_DOMAIN = b"zrm.accounting_coverage_entry.v1"
COVERAGE_MANIFEST_DOMAIN = b"zrm.accounting_coverage_manifest.v1"

U32_MAX = (1 << 32) - 1
U64_MAX = (1 << 64) - 1
U128_MAX = (1 << 128) - 1
U256_MAX = (1 << 256) - 1
MAX_FRAMED_HASH_LIST_ITEMS = (U32_MAX - 4) // 32
ROW_PAYLOAD_BYTES = 194
COVERAGE_ENTRY_PAYLOAD_BYTES = 202
EXISTING_LEAF_ACCOUNTING_ROW_HASH_FIXTURE_LABEL = (
    b"zrm.existing_leaf.AccountingRowHash.fixture.v1"
)


class VectorError(ValueError):
    """Raised when an independently derived fixture violates the frozen ABI."""


def u16(value: int) -> bytes:
    if type(value) is not int or not 0 <= value <= 0xFFFF:
        raise VectorError("u16 value outside range")
    return struct.pack(">H", value)


def u32(value: int) -> bytes:
    if type(value) is not int or not 0 <= value <= U32_MAX:
        raise VectorError("u32 value outside range")
    return struct.pack(">I", value)


def u64(value: int) -> bytes:
    if type(value) is not int or not 0 <= value <= U64_MAX:
        raise VectorError("u64 value outside range")
    return struct.pack(">Q", value)


def u256(value: int) -> bytes:
    if type(value) is not int or not 0 <= value <= U256_MAX:
        raise VectorError("u256 value outside range")
    return value.to_bytes(32, "big")


def require_bytes32(value: bytes, field: str) -> bytes:
    if type(value) is not bytes or len(value) != 32:
        raise VectorError(f"{field} must be exactly 32 bytes")
    return value


def require_nonzero_bytes32(value: bytes, field: str) -> bytes:
    checked = require_bytes32(value, field)
    if checked == bytes(32):
        raise VectorError(f"{field} must not be the all-zero typed value")
    return checked


def framed_hash_preimage(domain: bytes, payload: bytes) -> bytes:
    """Return the repository's exact H_D SHA-256 preimage."""

    if type(domain) is not bytes or not domain or len(domain) > 0xFFFF:
        raise VectorError("hash domain must be nonempty bytes fitting u16")
    if type(payload) is not bytes or len(payload) > U32_MAX:
        raise VectorError("hash payload must be bytes fitting u32")
    return u16(len(domain)) + domain + u32(len(payload)) + payload


def framed_digest(domain: bytes, payload: bytes) -> bytes:
    return hashlib.sha256(framed_hash_preimage(domain, payload)).digest()


def framed_hash_list_payload_bytes(count: int) -> int:
    """Validate and return ``4 + 32*n`` under the outer u32 frame."""

    if type(count) is not int or not 0 <= count <= MAX_FRAMED_HASH_LIST_ITEMS:
        raise VectorError("hash-list item count exceeds the u32 payload frame")
    return 4 + 32 * count


def framed_hash_list_payload(hashes: tuple[bytes, ...]) -> bytes:
    if type(hashes) is not tuple:
        raise VectorError("hash list must be an exact tuple")
    expected_bytes = framed_hash_list_payload_bytes(len(hashes))
    for index, value in enumerate(hashes):
        require_bytes32(value, f"hash list item[{index}]")
    payload = u32(len(hashes)) + b"".join(hashes)
    if len(payload) != expected_bytes:
        raise VectorError("hash-list payload length mismatch")
    return payload


def existing_leaf_accounting_row_hash_fixture() -> bytes:
    """Return an opaque frozen existing-leaf AccountingRowHash fixture."""

    return hashlib.sha256(EXISTING_LEAF_ACCOUNTING_ROW_HASH_FIXTURE_LABEL).digest()


@dataclass(frozen=True)
class IndependentRow:
    """A four-column aggregate row in algebraic debit/credit order."""

    label: str
    resource_kind_id: bytes
    unit_id: bytes
    consumed_atoms: int
    created_atoms: int
    authorized_burn_atoms: int
    authorized_mint_atoms: int

    def __post_init__(self) -> None:
        if type(self.label) is not str or not self.label:
            raise VectorError("row label must be nonempty exact text")
        require_nonzero_bytes32(self.resource_kind_id, "resource kind ID")
        require_nonzero_bytes32(self.unit_id, "unit ID")
        for field, value in (
            ("consumed atoms", self.consumed_atoms),
            ("created atoms", self.created_atoms),
            ("authorized burn atoms", self.authorized_burn_atoms),
            ("authorized mint atoms", self.authorized_mint_atoms),
        ):
            if type(value) is not int or not 0 <= value <= U256_MAX:
                raise VectorError(f"{field} must fit u256")
        if self.created_atoms - self.consumed_atoms != (
            self.authorized_mint_atoms - self.authorized_burn_atoms
        ):
            raise VectorError("row violates two-flow conservation")
        if not any(
            (
                self.consumed_atoms,
                self.created_atoms,
                self.authorized_burn_atoms,
                self.authorized_mint_atoms,
            )
        ):
            raise VectorError("all-zero aggregate row is noncanonical")

    @property
    def dimension(self) -> tuple[bytes, bytes]:
        return self.resource_kind_id, self.unit_id

    def payload(self) -> bytes:
        payload = b"".join(
            (
                u16(1),
                self.resource_kind_id,
                self.unit_id,
                u256(self.consumed_atoms),
                u256(self.created_atoms),
                u256(self.authorized_burn_atoms),
                u256(self.authorized_mint_atoms),
            )
        )
        if len(payload) != ROW_PAYLOAD_BYTES:
            raise VectorError("accounting row payload is not exactly 194 bytes")
        return payload

    def preimage(self) -> bytes:
        return framed_hash_preimage(ROW_DOMAIN, self.payload())

    def digest(self) -> bytes:
        return hashlib.sha256(self.preimage()).digest()

    def vector_record(self) -> dict[str, object]:
        return {
            "resource_kind_id": self.resource_kind_id.hex(),
            "unit_id": self.unit_id.hex(),
            "consumed_atoms": str(self.consumed_atoms),
            "created_atoms": str(self.created_atoms),
            "authorized_burn_atoms": str(self.authorized_burn_atoms),
            "authorized_mint_atoms": str(self.authorized_mint_atoms),
            "resource_net": str(self.created_atoms - self.consumed_atoms),
            "authority_net": str(
                self.authorized_mint_atoms - self.authorized_burn_atoms
            ),
            "payload_bytes": len(self.payload()),
            "row_hash": self.digest().hex(),
        }


@dataclass(frozen=True)
class IndependentCoverageEntry:
    """One ordered accepted-journal leaf's exact accounting coverage binding."""

    label: str
    leaf_position: int
    accepted_journal_hash: bytes
    resource_kind_id: bytes
    unit_id: bytes
    accounting_row_hash: bytes
    authority_root: bytes
    transformation_set_root: bytes

    def __post_init__(self) -> None:
        if type(self.label) is not str or not self.label:
            raise VectorError("coverage label must be nonempty exact text")
        if type(self.leaf_position) is not int or not 0 <= self.leaf_position <= U64_MAX:
            raise VectorError("coverage leaf position must fit u64")
        for field, value in (
            ("accepted journal hash", self.accepted_journal_hash),
            ("coverage resource kind ID", self.resource_kind_id),
            ("coverage unit ID", self.unit_id),
            ("coverage accounting row hash", self.accounting_row_hash),
            ("coverage authority root", self.authority_root),
            ("coverage transformation-set root", self.transformation_set_root),
        ):
            require_nonzero_bytes32(value, field)

    def payload(self) -> bytes:
        payload = b"".join(
            (
                u16(1),
                u64(self.leaf_position),
                self.accepted_journal_hash,
                self.resource_kind_id,
                self.unit_id,
                self.accounting_row_hash,
                self.authority_root,
                self.transformation_set_root,
            )
        )
        if len(payload) != COVERAGE_ENTRY_PAYLOAD_BYTES:
            raise VectorError("coverage entry payload is not exactly 202 bytes")
        return payload

    def preimage(self) -> bytes:
        return framed_hash_preimage(COVERAGE_ENTRY_DOMAIN, self.payload())

    def digest(self) -> bytes:
        return hashlib.sha256(self.preimage()).digest()

    def vector_record(self) -> dict[str, object]:
        return {
            "leaf_position": self.leaf_position,
            "accepted_journal_hash": self.accepted_journal_hash.hex(),
            "resource_kind_id": self.resource_kind_id.hex(),
            "unit_id": self.unit_id.hex(),
            "accounting_row_hash": self.accounting_row_hash.hex(),
            "authority_root": self.authority_root.hex(),
            "transformation_set_root": self.transformation_set_root.hex(),
            "payload_bytes": len(self.payload()),
            "entry_hash": self.digest().hex(),
        }


def decode_canonical_row(label: str, payload: bytes) -> IndependentRow:
    """Strictly decode one untrusted aggregate-row payload."""

    if type(payload) is not bytes or len(payload) != ROW_PAYLOAD_BYTES:
        raise VectorError("aggregate row payload must be exactly 194 bytes")
    if int.from_bytes(payload[0:2], "big") != 1:
        raise VectorError("unsupported aggregate row schema version")
    return IndependentRow(
        label,
        payload[2:34],
        payload[34:66],
        int.from_bytes(payload[66:98], "big"),
        int.from_bytes(payload[98:130], "big"),
        int.from_bytes(payload[130:162], "big"),
        int.from_bytes(payload[162:194], "big"),
    )


def decode_canonical_coverage_entry(
    label: str, payload: bytes
) -> IndependentCoverageEntry:
    """Strictly decode one untrusted coverage-entry payload."""

    if type(payload) is not bytes or len(payload) != COVERAGE_ENTRY_PAYLOAD_BYTES:
        raise VectorError("coverage entry payload must be exactly 202 bytes")
    if int.from_bytes(payload[0:2], "big") != 1:
        raise VectorError("unsupported coverage entry schema version")
    return IndependentCoverageEntry(
        label,
        int.from_bytes(payload[2:10], "big"),
        payload[10:42],
        payload[42:74],
        payload[74:106],
        payload[106:138],
        payload[138:170],
        payload[170:202],
    )


def fixture_id(byte: int) -> bytes:
    if type(byte) is not int or not 0 <= byte <= 0xFF:
        raise VectorError("fixture byte outside range")
    return bytes([byte]) * 32


def fixture_rows() -> dict[str, IndependentRow]:
    """Construct transfer, mint, burn/mixed, and wide-aggregate rows."""

    balanced_transfer = IndependentRow(
        "balanced_transfer",
        fixture_id(0x11),
        fixture_id(0x21),
        consumed_atoms=11,
        created_atoms=11,
        authorized_burn_atoms=0,
        authorized_mint_atoms=0,
    )
    mint = IndependentRow(
        "mint",
        fixture_id(0x12),
        fixture_id(0x22),
        consumed_atoms=0,
        created_atoms=7,
        authorized_burn_atoms=0,
        authorized_mint_atoms=7,
    )
    burn_mixed = IndependentRow(
        "burn_mixed",
        fixture_id(0x13),
        fixture_id(0x23),
        consumed_atoms=13,
        created_atoms=5,
        authorized_burn_atoms=10,
        authorized_mint_atoms=2,
    )

    # Derive the wide row from two independently valid u128-width leaves.
    leaf_columns = (U128_MAX, U128_MAX, U128_MAX, U128_MAX)
    aggregate_columns = tuple(left + right for left, right in zip(leaf_columns, leaf_columns))
    if any(value > U256_MAX for value in aggregate_columns):
        raise VectorError("two u128 leaves unexpectedly overflow u256")
    wide = IndependentRow(
        "two_u128_max_leaves",
        fixture_id(0x14),
        fixture_id(0x24),
        consumed_atoms=aggregate_columns[0],
        created_atoms=aggregate_columns[1],
        authorized_burn_atoms=aggregate_columns[2],
        authorized_mint_atoms=aggregate_columns[3],
    )
    return {row.label: row for row in (balanced_transfer, mint, burn_mixed, wide)}


def canonical_rows_payload(rows: tuple[IndependentRow, ...]) -> bytes:
    """Validate untrusted canonical order and return count-framed row hashes."""

    if type(rows) is not tuple:
        raise VectorError("rows must be an exact tuple")
    if any(type(row) is not IndependentRow for row in rows):
        raise VectorError("rows have an invalid runtime type")
    dimensions = tuple(row.dimension for row in rows)
    if dimensions != tuple(sorted(dimensions)):
        raise VectorError("untrusted rows must already be canonically sorted")
    if len(dimensions) != len(set(dimensions)):
        raise VectorError("duplicate accounting dimensions reject")
    return framed_hash_list_payload(tuple(row.digest() for row in rows))


def trusted_fixture_rows_payload(
    rows: tuple[IndependentRow, ...],
) -> tuple[bytes, tuple[IndependentRow, ...]]:
    """Sort only locally constructed authoritative fixture rows."""

    if type(rows) is not tuple or any(type(row) is not IndependentRow for row in rows):
        raise VectorError("trusted fixture rows must be an exact typed tuple")
    ordered = tuple(sorted(rows, key=lambda row: row.dimension))
    return canonical_rows_payload(ordered), ordered


def canonical_coverage_manifest_payload(
    entries: tuple[IndependentCoverageEntry, ...],
) -> bytes:
    """Validate exact positional order without sorting or deduplicating."""

    if type(entries) is not tuple:
        raise VectorError("coverage entries must be an exact tuple")
    if any(type(entry) is not IndependentCoverageEntry for entry in entries):
        raise VectorError("coverage entries have an invalid runtime type")
    keys = tuple(
        (entry.leaf_position, entry.resource_kind_id, entry.unit_id)
        for entry in entries
    )
    if keys != tuple(sorted(keys)):
        raise VectorError(
            "coverage entries must be ordered by leaf position and dimension"
        )
    if len(keys) != len(set(keys)):
        raise VectorError("duplicate leaf-position/dimension coverage entry")
    return framed_hash_list_payload(tuple(entry.digest() for entry in entries))


def raw_coverage_manifest_mutant_payload(
    entries: tuple[IndependentCoverageEntry, ...],
) -> bytes:
    """Hash a deliberately malformed order only for negative vector roots."""

    if type(entries) is not tuple or any(
        type(entry) is not IndependentCoverageEntry for entry in entries
    ):
        raise VectorError("raw mutant coverage entries must be an exact typed tuple")
    return framed_hash_list_payload(tuple(entry.digest() for entry in entries))


def fixture_coverage(
    repeated_row: IndependentRow,
) -> tuple[IndependentCoverageEntry, IndependentCoverageEntry]:
    """Bind one opaque existing leaf-row hash at two journal leaves."""

    existing_leaf_hash = existing_leaf_accounting_row_hash_fixture()
    if existing_leaf_hash == repeated_row.digest():
        raise VectorError("existing leaf row hash collided with aggregate row hash")
    common = {
        "resource_kind_id": repeated_row.resource_kind_id,
        "unit_id": repeated_row.unit_id,
        "accounting_row_hash": existing_leaf_hash,
        "authority_root": fixture_id(0xA1),
        "transformation_set_root": fixture_id(0xB1),
    }
    first = IndependentCoverageEntry(
        "coverage_0",
        leaf_position=0,
        accepted_journal_hash=hashlib.sha256(b"accepted-journal-fixture-0").digest(),
        **common,
    )
    second = IndependentCoverageEntry(
        "coverage_1",
        leaf_position=1,
        accepted_journal_hash=hashlib.sha256(b"accepted-journal-fixture-1").digest(),
        **common,
    )
    return first, second


def strict_untrusted_negative_decisions() -> dict[str, str]:
    """Exercise malformed inputs without canonicalizing them into acceptance."""

    rows = fixture_rows()
    coverage = fixture_coverage(rows["balanced_transfer"])
    decisions: dict[str, str] = {}

    def expect_reject(label: str, operation: object) -> None:
        try:
            assert callable(operation)
            operation()
        except VectorError:
            decisions[label] = "reject"
        else:
            decisions[label] = "accept"

    balanced_payload = rows["balanced_transfer"].payload()
    wrong_schema = b"\x00\x02" + balanced_payload[2:]
    expect_reject(
        "row_wrong_length",
        lambda: decode_canonical_row("wrong-length", balanced_payload[:-1]),
    )
    expect_reject(
        "row_wrong_schema",
        lambda: decode_canonical_row("wrong-schema", wrong_schema),
    )
    expect_reject(
        "row_zero_resource_kind_id",
        lambda: IndependentRow(
            "zero-kind",
            bytes(32),
            fixture_id(0x31),
            1,
            1,
            0,
            0,
        ),
    )
    expect_reject(
        "row_all_four_columns_zero",
        lambda: IndependentRow(
            "all-zero-row",
            fixture_id(0x32),
            fixture_id(0x33),
            0,
            0,
            0,
            0,
        ),
    )
    expect_reject(
        "rows_misordered",
        lambda: canonical_rows_payload(
            (rows["burn_mixed"], rows["mint"], rows["balanced_transfer"])
        ),
    )
    duplicate_dimension = IndependentRow(
        "duplicate-dimension",
        rows["balanced_transfer"].resource_kind_id,
        rows["balanced_transfer"].unit_id,
        2,
        2,
        0,
        0,
    )
    expect_reject(
        "rows_duplicate_dimension",
        lambda: canonical_rows_payload(
            (rows["balanced_transfer"], duplicate_dimension)
        ),
    )
    expect_reject(
        "coverage_reversed_order",
        lambda: canonical_coverage_manifest_payload(tuple(reversed(coverage))),
    )
    expect_reject(
        "coverage_duplicate_leaf_dimension",
        lambda: canonical_coverage_manifest_payload((coverage[0], coverage[0])),
    )
    expect_reject(
        "coverage_zero_authority_root",
        lambda: IndependentCoverageEntry(
            "zero-authority",
            coverage[0].leaf_position,
            coverage[0].accepted_journal_hash,
            coverage[0].resource_kind_id,
            coverage[0].unit_id,
            coverage[0].accounting_row_hash,
            bytes(32),
            coverage[0].transformation_set_root,
        ),
    )
    return decisions


def check_strict_positive_roundtrips() -> None:
    rows = fixture_rows()
    for label, value in rows.items():
        decoded = decode_canonical_row(f"decoded:{label}", value.payload())
        if decoded.payload() != value.payload():
            raise VectorError(f"strict row roundtrip failed for {label}")
    for entry in fixture_coverage(rows["balanced_transfer"]):
        decoded = decode_canonical_coverage_entry(
            f"decoded:{entry.label}", entry.payload()
        )
        if decoded.payload() != entry.payload():
            raise VectorError(f"strict coverage roundtrip failed for {entry.label}")


def artifact_bytes() -> dict[str, bytes]:
    """Return every independently generated binary vector artifact."""

    rows = fixture_rows()
    artifacts: dict[str, bytes] = {}
    for label, value in sorted(rows.items()):
        artifacts[f"accounting_aggregate_v1_{label}.bin"] = value.payload()
        artifacts[f"accounting_aggregate_v1_{label}_preimage.bin"] = value.preimage()

    input_rows = (rows["burn_mixed"], rows["mint"], rows["balanced_transfer"])
    sorted_payload, _ = trusted_fixture_rows_payload(input_rows)
    artifacts["accounting_aggregate_v1_sorted_rows_payload.bin"] = sorted_payload
    artifacts["accounting_aggregate_v1_sorted_rows_preimage.bin"] = (
        framed_hash_preimage(ROWS_DOMAIN, sorted_payload)
    )

    coverage = fixture_coverage(rows["balanced_transfer"])
    for entry in coverage:
        artifacts[f"accounting_aggregate_v1_{entry.label}.bin"] = entry.payload()
        artifacts[f"accounting_aggregate_v1_{entry.label}_preimage.bin"] = (
            entry.preimage()
        )
    coverage_payload = canonical_coverage_manifest_payload(coverage)
    artifacts["accounting_aggregate_v1_coverage_manifest_payload.bin"] = (
        coverage_payload
    )
    artifacts["accounting_aggregate_v1_coverage_manifest_preimage.bin"] = (
        framed_hash_preimage(COVERAGE_MANIFEST_DOMAIN, coverage_payload)
    )
    return artifacts


def manifest(artifacts: dict[str, bytes]) -> dict[str, object]:
    """Build deterministic vector metadata and expected protocol digests."""

    rows = fixture_rows()
    input_rows = (rows["burn_mixed"], rows["mint"], rows["balanced_transfer"])
    sorted_payload, ordered_rows = trusted_fixture_rows_payload(input_rows)
    sorted_root = framed_digest(ROWS_DOMAIN, sorted_payload)
    coverage = fixture_coverage(rows["balanced_transfer"])
    coverage_payload = canonical_coverage_manifest_payload(coverage)
    coverage_root = framed_digest(COVERAGE_MANIFEST_DOMAIN, coverage_payload)
    deduplicated_payload = canonical_coverage_manifest_payload((coverage[0],))
    reversed_payload = raw_coverage_manifest_mutant_payload(
        tuple(reversed(coverage))
    )
    u32_theoretical_maximum_limb = U32_MAX * U128_MAX
    existing_leaf_hash = existing_leaf_accounting_row_hash_fixture()
    aggregate_row_hash = rows["balanced_transfer"].digest()
    strict_decisions = strict_untrusted_negative_decisions()
    return {
        "schema": "zrm/accounting-aggregate-v1-vectors/v1",
        "status": "proposed_non_authoritative",
        "generated_by": (
            "vectors/independent_python/replay_accounting_aggregate_v1.py"
        ),
        "hash_profile": {
            "function": "sha256",
            "frame": "u16_be(domain_len)||domain||u32_be(payload_len)||payload",
            "row_domain": ROW_DOMAIN.decode("ascii"),
            "rows_domain": ROWS_DOMAIN.decode("ascii"),
            "coverage_entry_domain": COVERAGE_ENTRY_DOMAIN.decode("ascii"),
            "coverage_manifest_domain": COVERAGE_MANIFEST_DOMAIN.decode("ascii"),
        },
        "row_encoding": {
            "payload_bytes": ROW_PAYLOAD_BYTES,
            "layout": (
                "u16_be(1)||resource_kind_id[32]||unit_id[32]||"
                "resource_debit_consumed_u256_be||resource_credit_created_u256_be||"
                "authority_debit_burn_u256_be||authority_credit_mint_u256_be"
            ),
        },
        "rows": {
            label: value.vector_record() for label, value in sorted(rows.items())
        },
        "sorted_rows_root": {
            "input_order": [row.label for row in input_rows],
            "canonical_order": [row.label for row in ordered_rows],
            "row_count": len(ordered_rows),
            "payload_bytes": len(sorted_payload),
            "root": sorted_root.hex(),
        },
        "coverage_manifest": {
            "entry_payload_bytes": COVERAGE_ENTRY_PAYLOAD_BYTES,
            "entry_layout": (
                "u16_be(1)||leaf_position_u64_be||accepted_journal_hash[32]||"
                "resource_kind_id[32]||unit_id[32]||accounting_row_hash[32]||"
                "authority_root[32]||transformation_set_root[32]"
            ),
            "entries": [entry.vector_record() for entry in coverage],
            "accounting_row_hash_field_type": (
                "opaque existing leaf AccountingRowHash; not AccountingAggregateRowHashV1"
            ),
            "existing_leaf_accounting_row_hash_fixture_label": (
                EXISTING_LEAF_ACCOUNTING_ROW_HASH_FIXTURE_LABEL.decode("ascii")
            ),
            "existing_leaf_accounting_row_hash_fixture": existing_leaf_hash.hex(),
            "balanced_transfer_aggregate_row_hash_for_type_separation": (
                aggregate_row_hash.hex()
            ),
            "leaf_and_aggregate_row_hashes_are_distinct": (
                existing_leaf_hash != aggregate_row_hash
            ),
            "root_payload_layout": "u32_be(count)||ordered_entry_hashes",
            "root": coverage_root.hex(),
            "repeated_existing_leaf_accounting_row_hash_occurrences": 2,
            "deduplicated_mutant_root": framed_digest(
                COVERAGE_MANIFEST_DOMAIN, deduplicated_payload
            ).hex(),
            "reversed_order_root": framed_digest(
                COVERAGE_MANIFEST_DOMAIN, reversed_payload
            ).hex(),
            "deduplication_changes_root": (
                framed_digest(COVERAGE_MANIFEST_DOMAIN, deduplicated_payload)
                != coverage_root
            ),
            "reversal_changes_root": (
                framed_digest(COVERAGE_MANIFEST_DOMAIN, reversed_payload)
                != coverage_root
            ),
        },
        "wide_capacity": {
            "leaf_column_max": str(U128_MAX),
            "two_leaf_column_total": str(2 * U128_MAX),
            "two_leaf_total_exceeds_u128": 2 * U128_MAX > U128_MAX,
            "two_leaf_total_fits_u256": 2 * U128_MAX <= U256_MAX,
            "u32_theoretical_leaf_count_times_u128_max": str(
                u32_theoretical_maximum_limb
            ),
            "u32_theoretical_maximum_bit_length": (
                u32_theoretical_maximum_limb.bit_length()
            ),
            "u32_theoretical_maximum_fits_u256": (
                u32_theoretical_maximum_limb <= U256_MAX
            ),
            "segment_leaf_count_type": "u32",
            "hash_list_ceiling_does_not_narrow_leaf_count": True,
        },
        "framed_hash_list_capacity": {
            "payload_formula": "4 + 32*n",
            "outer_payload_length_type": "u32_be",
            "maximum_items": MAX_FRAMED_HASH_LIST_ITEMS,
            "maximum_payload_bytes": framed_hash_list_payload_bytes(
                MAX_FRAMED_HASH_LIST_ITEMS
            ),
            "next_item_rejects": (
                4 + 32 * (MAX_FRAMED_HASH_LIST_ITEMS + 1) > U32_MAX
            ),
        },
        "strict_untrusted_validation": {
            "trusted_fixture_builder": "trusted_fixture_rows_payload",
            "strict_row_decoder": "decode_canonical_row",
            "strict_coverage_decoder": "decode_canonical_coverage_entry",
            "negative_cases": len(strict_decisions),
            "rejected_negative_cases": sum(
                decision == "reject" for decision in strict_decisions.values()
            ),
            "decisions": strict_decisions,
        },
        "artifacts": {
            name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(artifacts.items())
        },
        "non_claims": [
            "these proposed vectors do not amend the current normative ZRM wire profile",
            "independent replay is not a proof of cryptographic or semantic correctness",
            "u256 aggregate columns do not widen the u128 per-leaf accounting fields",
            "coverage hashes do not authenticate journal acceptance, authority, state, or commit",
            "the opaque existing-leaf AccountingRowHash fixture is not a proposed "
            "leaf-row encoding",
            "the vectors do not establish completeness of arbitrary transition "
            "read or effect coverage",
        ],
    }


def write_vectors(
    artifacts: dict[str, bytes], expected_manifest: dict[str, object]
) -> None:
    """Write generated binary vectors and their deterministic manifest."""

    VECTOR_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for name, data in artifacts.items():
        (VECTOR_DIRECTORY / name).write_bytes(data)
    MANIFEST_PATH.write_text(
        json.dumps(expected_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def check_vectors(
    artifacts: dict[str, bytes], expected_manifest: dict[str, object]
) -> bool:
    """Compare committed vectors to a fresh independent derivation."""

    failures: list[str] = []
    for name, expected in artifacts.items():
        path = VECTOR_DIRECTORY / name
        if not path.is_file() or path.read_bytes() != expected:
            failures.append(name)
    if not MANIFEST_PATH.is_file():
        failures.append(MANIFEST_PATH.name)
    else:
        actual_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if actual_manifest != expected_manifest:
            failures.append(MANIFEST_PATH.name)
    if failures:
        print("vector replay failed: " + ", ".join(sorted(failures)), file=sys.stderr)
        return False
    print(
        "vector replay passed: "
        f"{len(artifacts)} binary artifacts, 4 rows, 2 coverage entries"
    )
    return True


def main() -> int:
    """Write or verify the deterministic independent vector corpus."""

    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    check_strict_positive_roundtrips()
    strict_decisions = strict_untrusted_negative_decisions()
    if any(decision != "reject" for decision in strict_decisions.values()):
        raise VectorError("strict untrusted validation accepted a negative case")
    if framed_hash_list_payload_bytes(MAX_FRAMED_HASH_LIST_ITEMS) > U32_MAX:
        raise VectorError("maximum hash-list count does not fit the u32 frame")
    try:
        framed_hash_list_payload_bytes(MAX_FRAMED_HASH_LIST_ITEMS + 1)
    except VectorError:
        pass
    else:
        raise VectorError("over-limit hash-list count did not reject")
    artifacts = artifact_bytes()
    expected_manifest = manifest(artifacts)
    if arguments.write:
        write_vectors(artifacts, expected_manifest)
        print("wrote independent accounting-aggregate vectors")
        return 0
    return 0 if check_vectors(artifacts, expected_manifest) else 1


if __name__ == "__main__":
    raise SystemExit(main())
