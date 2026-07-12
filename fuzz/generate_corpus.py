"""Generate deterministic non-vector seeds for the repository fuzzers."""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESOURCE_WIRE_CORPUS = ROOT / "fuzz/corpus/resource_wire_v1_decode"
POLICY_COST_CORPUS = ROOT / "fuzz/corpus/policy_cost_v1"
OVERSIZE_SEED = ROOT / "fuzz/corpus/resource_wire_v1_decode/oversize-boundary"
POLICY_SEQUENCE_SEED = ROOT / "fuzz/corpus/policy_cost_v1/sequence"
POLICY_MAX_SEED = ROOT / "fuzz/corpus/policy_cost_v1/maxima"
POLICY_SMALL_SUCCESS_SEED = ROOT / "fuzz/corpus/policy_cost_v1/small-success"
RESOURCE_ROLES_CORPUS = ROOT / "fuzz/corpus/resource_roles_v1"
INTRINSIC_RESOURCE_CORPUS = ROOT / "fuzz/corpus/intrinsic_resource_v1"
POLICY_RESOURCE_DIMENSIONS_CORPUS = (
    ROOT / "fuzz/corpus/policy_resource_dimensions_v1"
)
MAX_RESOURCE_BYTES = 16_384


def resource_id(value: int) -> bytes:
    """Return one deterministic nonzero fixed-width resource identifier."""

    return value.to_bytes(32, "big")


def resource_roles_seed(
    limits: tuple[int, int, int],
    consumed: list[int],
    referenced: list[int],
    created: list[int],
) -> bytes:
    """Encode the bounded grammar consumed by the resource-role fuzzer."""

    header = struct.pack(
        ">6H",
        *limits,
        len(consumed),
        len(referenced),
        len(created),
    )
    values = consumed + referenced + created
    return header + b"".join(resource_id(value) for value in values)


def resource_role_seeds() -> dict[str, bytes]:
    """Return boundary, duplicate, collision, and canonicalization seeds."""

    return {
        "empty": resource_roles_seed((0, 0, 0), [], [], []),
        "valid-unsorted": resource_roles_seed(
            (3, 2, 2), [3, 1, 2], [12, 11], [22, 21]
        ),
        "duplicate-consumed": resource_roles_seed((2, 1, 1), [1, 1], [2], [3]),
        "duplicate-referenced": resource_roles_seed((1, 2, 1), [1], [2, 2], [3]),
        "duplicate-created": resource_roles_seed((1, 1, 2), [1], [2], [3, 3]),
        "collision-consumed-referenced": resource_roles_seed(
            (1, 1, 1), [1], [1], [3]
        ),
        "collision-consumed-created": resource_roles_seed((1, 1, 1), [1], [2], [1]),
        "collision-referenced-created": resource_roles_seed(
            (1, 1, 1), [1], [2], [2]
        ),
        "exact-limit": resource_roles_seed(
            (256, 256, 256),
            list(range(256, 0, -1)),
            list(range(512, 256, -1)),
            list(range(768, 512, -1)),
        ),
        "over-limit": resource_roles_seed(
            (256, 0, 0), list(range(257, 0, -1)), [], []
        ),
    }


def intrinsic_resource_seeds() -> dict[str, bytes]:
    """Return parity-encoded seeds for every intrinsic defect and precedence."""

    names = [
        "zero-machine",
        "zero-domain",
        "zero-application",
        "zero-resource-kind",
        "zero-resource-logic",
        "zero-logic-profile",
        "zero-resource-kind-policy",
        "zero-unit",
        "zero-label",
        "zero-value",
        "zero-controller",
        "zero-policy-root",
        "zero-provenance",
        "zero-nonce",
        "expiry-before-creation",
        "unknown-flags",
    ]
    seeds = {"valid-zero-quantity": b"0" * 16, "all-defects": b"1" * 16}
    for index, name in enumerate(names):
        bits = bytearray(b"0" * 16)
        bits[index] = ord("1")
        seeds[name] = bytes(bits)
    return seeds


def policy_resource_dimension_seed(
    mode: int, unit_mismatch: bool, quantity: int, quantity_maximum: int
) -> bytes:
    """Encode one structured resource-dimension policy seed."""

    return bytes((mode, int(unit_mismatch))) + quantity.to_bytes(
        16, "big"
    ) + quantity_maximum.to_bytes(16, "big")


def policy_resource_dimension_seeds() -> dict[str, bytes]:
    """Return mode, precedence, lifecycle, zero, and u128 boundary seeds."""

    return {
        "zero-conserved": policy_resource_dimension_seed(0, False, 0, 1),
        "zero-mintable": policy_resource_dimension_seed(1, False, 0, 1),
        "zero-lifecycle": policy_resource_dimension_seed(2, False, 0, 1),
        "zero-transformable": policy_resource_dimension_seed(3, False, 0, 1),
        "zero-evidence": policy_resource_dimension_seed(4, False, 0, 1),
        "wrong-unit-precedes-lifecycle": policy_resource_dimension_seed(
            2, True, 0, 1
        ),
        "lifecycle-maximum-zero": policy_resource_dimension_seed(2, False, 1, 0),
        "lifecycle-maximum-one": policy_resource_dimension_seed(2, False, 1, 1),
        "lifecycle-maximum-two": policy_resource_dimension_seed(2, False, 1, 2),
        "quantity-above-maximum": policy_resource_dimension_seed(0, False, 2, 1),
        "full-width-maximum": policy_resource_dimension_seed(
            4, False, (1 << 128) - 1, (1 << 128) - 1
        ),
    }


def check_seed(path: Path, expected: bytes, label: str) -> bool:
    """Report whether one deterministic corpus entry is present and exact."""

    if path.is_file() and path.read_bytes() == expected:
        return True
    print(f"fuzz corpus check failed: {label} is missing or stale", file=sys.stderr)
    return False


def check_seed_names(directory: Path, expected_names: set[str], label: str) -> bool:
    """Reject missing, nested, linked, non-regular, or extra corpus entries."""

    if directory.is_symlink() or not directory.is_dir():
        print(f"fuzz corpus check failed: {label} corpus is missing", file=sys.stderr)
        return False
    actual_names: set[str] = set()
    invalid_entries: list[str] = []
    for path in directory.rglob("*"):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink() or not path.is_file():
            invalid_entries.append(relative)
        else:
            actual_names.add(relative)
    if actual_names == expected_names and not invalid_entries:
        return True
    print(
        f"fuzz corpus check failed: {label} corpus contains missing, extra, "
        f"nested, linked, or non-regular entries",
        file=sys.stderr,
    )
    return False


def main() -> int:
    """Write or verify deterministic resource, policy, and role seeds."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    expected = bytes(MAX_RESOURCE_BYTES + 1)
    policy_sequence = bytes(range(88))
    policy_maxima = bytes([0xFF]) * 88
    policy_small_success = b"".join(
        value.to_bytes(8, "big")
        for value in (7, 3, 5, 11, 100, 80, 40, 10_000, 10_000, 4, 5)
    )
    role_seeds = resource_role_seeds()
    intrinsic_seeds = intrinsic_resource_seeds()
    policy_dimension_seeds = policy_resource_dimension_seeds()
    if arguments.check:
        if not check_seed(OVERSIZE_SEED, expected, "oversize-boundary"):
            return 1
        if not check_seed_names(
            RESOURCE_WIRE_CORPUS,
            {"absent", "oversize-boundary", "present"},
            "resource-wire",
        ):
            return 1
        if not check_seed(POLICY_SEQUENCE_SEED, policy_sequence, "policy sequence seed"):
            return 1
        if not check_seed(POLICY_MAX_SEED, policy_maxima, "policy maxima seed"):
            return 1
        if not check_seed(
            POLICY_SMALL_SUCCESS_SEED, policy_small_success, "policy success seed"
        ):
            return 1
        if not check_seed_names(
            POLICY_COST_CORPUS,
            {"maxima", "sequence", "small-success"},
            "policy-cost",
        ):
            return 1
        for name, role_seed in role_seeds.items():
            if not check_seed(RESOURCE_ROLES_CORPUS / name, role_seed, name):
                return 1
        if not check_seed_names(RESOURCE_ROLES_CORPUS, set(role_seeds), "resource-role"):
            return 1
        for name, intrinsic_seed in intrinsic_seeds.items():
            if not check_seed(INTRINSIC_RESOURCE_CORPUS / name, intrinsic_seed, name):
                return 1
        if not check_seed_names(
            INTRINSIC_RESOURCE_CORPUS, set(intrinsic_seeds), "intrinsic-resource"
        ):
            return 1
        for name, policy_dimension_seed in policy_dimension_seeds.items():
            if not check_seed(
                POLICY_RESOURCE_DIMENSIONS_CORPUS / name,
                policy_dimension_seed,
                name,
            ):
                return 1
        if not check_seed_names(
            POLICY_RESOURCE_DIMENSIONS_CORPUS,
            set(policy_dimension_seeds),
            "policy-resource-dimensions",
        ):
            return 1
        print(
            "fuzz corpus check passed: resource boundary, three policy-cost seeds, "
            "ten resource-role seeds, eighteen intrinsic-resource seeds, and "
            "eleven policy-resource-dimension seeds"
        )
        return 0
    OVERSIZE_SEED.parent.mkdir(parents=True, exist_ok=True)
    OVERSIZE_SEED.write_bytes(expected)
    POLICY_SEQUENCE_SEED.parent.mkdir(parents=True, exist_ok=True)
    POLICY_SEQUENCE_SEED.write_bytes(policy_sequence)
    POLICY_MAX_SEED.write_bytes(policy_maxima)
    POLICY_SMALL_SUCCESS_SEED.write_bytes(policy_small_success)
    RESOURCE_ROLES_CORPUS.mkdir(parents=True, exist_ok=True)
    for name, role_seed in role_seeds.items():
        (RESOURCE_ROLES_CORPUS / name).write_bytes(role_seed)
    INTRINSIC_RESOURCE_CORPUS.mkdir(parents=True, exist_ok=True)
    for name, intrinsic_seed in intrinsic_seeds.items():
        (INTRINSIC_RESOURCE_CORPUS / name).write_bytes(intrinsic_seed)
    POLICY_RESOURCE_DIMENSIONS_CORPUS.mkdir(parents=True, exist_ok=True)
    for name, policy_dimension_seed in policy_dimension_seeds.items():
        (POLICY_RESOURCE_DIMENSIONS_CORPUS / name).write_bytes(policy_dimension_seed)
    print(
        "generated resource boundary, three policy-cost seeds, "
        "ten resource-role seeds, eighteen intrinsic-resource seeds, and "
        "eleven policy-resource-dimension seeds"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
