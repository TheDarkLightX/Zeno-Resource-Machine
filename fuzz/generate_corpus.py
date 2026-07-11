"""Generate deterministic non-vector seeds for the repository fuzzers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OVERSIZE_SEED = ROOT / "fuzz/corpus/resource_wire_v1_decode/oversize-boundary"
POLICY_SEQUENCE_SEED = ROOT / "fuzz/corpus/policy_cost_v1/sequence"
POLICY_MAX_SEED = ROOT / "fuzz/corpus/policy_cost_v1/maxima"
POLICY_SMALL_SUCCESS_SEED = ROOT / "fuzz/corpus/policy_cost_v1/small-success"
MAX_RESOURCE_BYTES = 16_384


def main() -> int:
    """Write or verify deterministic resource and policy-cost seeds."""

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
    if arguments.check:
        if not OVERSIZE_SEED.is_file() or OVERSIZE_SEED.read_bytes() != expected:
            print("fuzz corpus check failed: oversize-boundary is missing or stale", file=sys.stderr)
            return 1
        if not POLICY_SEQUENCE_SEED.is_file() or POLICY_SEQUENCE_SEED.read_bytes() != policy_sequence:
            print("fuzz corpus check failed: policy sequence seed is missing or stale", file=sys.stderr)
            return 1
        if not POLICY_MAX_SEED.is_file() or POLICY_MAX_SEED.read_bytes() != policy_maxima:
            print("fuzz corpus check failed: policy maxima seed is missing or stale", file=sys.stderr)
            return 1
        if (
            not POLICY_SMALL_SUCCESS_SEED.is_file()
            or POLICY_SMALL_SUCCESS_SEED.read_bytes() != policy_small_success
        ):
            print("fuzz corpus check failed: policy success seed is missing or stale", file=sys.stderr)
            return 1
        print("fuzz corpus check passed: resource boundary and three policy-cost seeds")
        return 0
    OVERSIZE_SEED.parent.mkdir(parents=True, exist_ok=True)
    OVERSIZE_SEED.write_bytes(expected)
    POLICY_SEQUENCE_SEED.parent.mkdir(parents=True, exist_ok=True)
    POLICY_SEQUENCE_SEED.write_bytes(policy_sequence)
    POLICY_MAX_SEED.write_bytes(policy_maxima)
    POLICY_SMALL_SUCCESS_SEED.write_bytes(policy_small_success)
    print("generated resource boundary and three policy-cost corpus seeds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
