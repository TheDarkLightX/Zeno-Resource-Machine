"""Generate deterministic non-vector seeds for the ResourceWireV1 fuzzer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OVERSIZE_SEED = ROOT / "fuzz/corpus/resource_wire_v1_decode/oversize-boundary"
MAX_RESOURCE_BYTES = 16_384


def main() -> int:
    """Write or verify the one-byte-over-limit regression seed."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    expected = bytes(MAX_RESOURCE_BYTES + 1)
    if arguments.check:
        if not OVERSIZE_SEED.is_file() or OVERSIZE_SEED.read_bytes() != expected:
            print("fuzz corpus check failed: oversize-boundary is missing or stale", file=sys.stderr)
            return 1
        print("fuzz corpus check passed: explicit 16,385-byte boundary seed")
        return 0
    OVERSIZE_SEED.parent.mkdir(parents=True, exist_ok=True)
    OVERSIZE_SEED.write_bytes(expected)
    print("generated fuzz/corpus/resource_wire_v1_decode/oversize-boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
