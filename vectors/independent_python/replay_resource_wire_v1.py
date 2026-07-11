"""Independently generate and replay the frozen ResourceWireV1 vectors."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VECTOR_DIRECTORY = ROOT / "vectors"
MANIFEST_PATH = VECTOR_DIRECTORY / "resource_wire_v1.json"
SUITE_DOMAIN = b"zrm.crypto_suite.sha256.v1"
RESOURCE_DOMAIN = b"zrm.resource.v1"
NULLIFIER_DOMAIN = b"zrm.nullifier.transparent.v1"


def framed_hash_preimage(domain: bytes, payload: bytes) -> bytes:
    """Return the exact H_D SHA-256 preimage."""

    return struct.pack(">H", len(domain)) + domain + struct.pack(">I", len(payload)) + payload


def tagged_field(tag: int, value: bytes) -> bytes:
    """Encode one strict tagged field."""

    return struct.pack(">HI", tag, len(value)) + value


def fixture_fields(expiry_epoch: int | None) -> list[tuple[int, bytes]]:
    """Build the independent canonical fixture field values."""

    fields = [(tag, bytes([tag]) * 32) for tag in range(1, 9)]
    fields.append((0x0009, bytes.fromhex("0102030405060708090a0b0c0d0e0f10")))
    fields.extend((tag, bytes([tag]) * 32) for tag in range(0x000A, 0x0010))
    fields.append((0x0010, bytes.fromhex("0102030405060708")))
    expiry = b"\x00" if expiry_epoch is None else b"\x01" + struct.pack(">Q", expiry_epoch)
    fields.append((0x0011, expiry))
    fields.append((0x0012, struct.pack(">I", 0)))
    return fields


def encode_resource(expiry_epoch: int | None) -> bytes:
    """Encode the independent ResourceWireV1 fixture."""

    header = b"ZRM1" + struct.pack(">HHH", 1, 1, 18)
    return header + b"".join(tagged_field(tag, value) for tag, value in fixture_fields(expiry_epoch))


def resource_id_preimage(wire: bytes) -> bytes:
    """Build the two-level length-framed ResourceId preimage."""

    payload = struct.pack(">I", len(wire)) + wire
    return framed_hash_preimage(RESOURCE_DOMAIN, payload)


def artifact_bytes() -> dict[str, bytes]:
    """Return every independently generated binary vector artifact."""

    absent = encode_resource(None)
    present = encode_resource(0x1112131415161718)
    absent_preimage = resource_id_preimage(absent)
    present_preimage = resource_id_preimage(present)
    suite_preimage = framed_hash_preimage(SUITE_DOMAIN, b"")
    absent_id = hashlib.sha256(absent_preimage).digest()
    nullifier_payload = bytes([1]) * 32 + bytes([2]) * 32 + absent_id
    nullifier_preimage = framed_hash_preimage(NULLIFIER_DOMAIN, nullifier_payload)
    return {
        "resource_wire_v1_absent.bin": absent,
        "resource_wire_v1_present.bin": present,
        "resource_wire_v1_absent_preimage.bin": absent_preimage,
        "resource_wire_v1_present_preimage.bin": present_preimage,
        "sha256_reference_suite_id_preimage.bin": suite_preimage,
        "transparent_nullifier_v1_preimage.bin": nullifier_preimage,
    }


def manifest(artifacts: dict[str, bytes]) -> dict[str, object]:
    """Build deterministic vector metadata and expected digests."""

    absent_preimage = artifacts["resource_wire_v1_absent_preimage.bin"]
    present_preimage = artifacts["resource_wire_v1_present_preimage.bin"]
    suite_preimage = artifacts["sha256_reference_suite_id_preimage.bin"]
    nullifier_preimage = artifacts["transparent_nullifier_v1_preimage.bin"]
    return {
        "schema": "zrm/resource-wire-v1-vectors/v1",
        "specification_version": "0.1.0-draft.2",
        "generated_by": "vectors/independent_python/replay_resource_wire_v1.py",
        "vectors": {
            "sha256_reference_suite_id": hashlib.sha256(suite_preimage).hexdigest(),
            "resource_id_absent_expiry": hashlib.sha256(absent_preimage).hexdigest(),
            "resource_id_present_expiry": hashlib.sha256(present_preimage).hexdigest(),
            "transparent_nullifier_absent_expiry": hashlib.sha256(nullifier_preimage).hexdigest(),
        },
        "artifacts": {
            name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(artifacts.items())
        },
        "non_claims": [
            "independent vector replay is not a proof of cryptographic or semantic correctness",
            "ResourceWireV1 vectors are syntactic and do not establish ResourceV1 validity",
        ],
    }


def write_vectors(artifacts: dict[str, bytes], expected_manifest: dict[str, object]) -> None:
    """Write generated binary vectors and their deterministic manifest."""

    VECTOR_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for name, data in artifacts.items():
        (VECTOR_DIRECTORY / name).write_bytes(data)
    MANIFEST_PATH.write_text(
        json.dumps(expected_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def check_vectors(artifacts: dict[str, bytes], expected_manifest: dict[str, object]) -> bool:
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
    print("vector replay passed: 6 binary artifacts and 4 protocol digests")
    return True


def main() -> int:
    """Write or verify the deterministic independent vector corpus."""

    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    artifacts = artifact_bytes()
    expected_manifest = manifest(artifacts)
    if arguments.write:
        write_vectors(artifacts, expected_manifest)
        print("wrote independent ResourceWireV1 vectors")
        return 0
    return 0 if check_vectors(artifacts, expected_manifest) else 1


if __name__ == "__main__":
    raise SystemExit(main())
