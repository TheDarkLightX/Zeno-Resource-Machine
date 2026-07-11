"""Unit tests for deterministic Cargo SBOM and cryptography CBOM generation."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from tools.generate_bom import (
    BomError,
    WorkspaceSnapshot,
    _decode_json_strict,
    _write_report,
    apply_build_surface_policy,
    build_cbom,
    build_sbom,
    canonical_json,
)


SHA_ID = "registry+https://github.com/rust-lang/crates.io-index#sha2@0.11.0"
BUILD_ID = "registry+https://github.com/rust-lang/crates.io-index#build-helper@1.0.0"
PROC_ID = "registry+https://github.com/rust-lang/crates.io-index#derive-helper@2.0.0"


def metadata(scope: str) -> dict[str, object]:
    """Return a small Cargo metadata v1 graph with absolute paths to discard."""

    root_name = "zrm-test" if scope == "root" else "zrm-fuzz-test"
    root_id = f"path+file:///private/repository#{root_name}@0.1.0"
    packages = [
        {
            "id": root_id,
            "name": root_name,
            "version": "0.1.0",
            "source": None,
            "license": "MIT",
            "manifest_path": f"/private/repository/{scope}/Cargo.toml",
            "targets": [
                {
                    "name": root_name,
                    "kind": ["lib"],
                    "src_path": f"/private/repository/{scope}/src/lib.rs",
                }
            ],
        },
        {
            "id": SHA_ID,
            "name": "sha2",
            "version": "0.11.0",
            "source": "registry+https://github.com/rust-lang/crates.io-index",
            "license": "MIT OR Apache-2.0",
            "manifest_path": "/cargo/registry/sha2/Cargo.toml",
            "targets": [{"name": "sha2", "kind": ["lib"], "src_path": "/cargo/sha2.rs"}],
        },
        {
            "id": BUILD_ID,
            "name": "build-helper",
            "version": "1.0.0",
            "source": "registry+https://github.com/rust-lang/crates.io-index",
            "license": "MIT",
            "manifest_path": "/cargo/registry/build-helper/Cargo.toml",
            "targets": [
                {"name": "build-script-build", "kind": ["custom-build"], "src_path": "/cargo/build.rs"}
            ],
        },
        {
            "id": PROC_ID,
            "name": "derive-helper",
            "version": "2.0.0",
            "source": "registry+https://github.com/rust-lang/crates.io-index",
            "license": "Apache-2.0",
            "manifest_path": "/cargo/registry/derive-helper/Cargo.toml",
            "targets": [
                {"name": "derive_helper", "kind": ["proc-macro"], "src_path": "/cargo/lib.rs"}
            ],
        },
    ]
    nodes = [
        {
            "id": root_id,
            "features": [],
            "deps": [
                {
                    "name": "sha2",
                    "pkg": SHA_ID,
                    "dep_kinds": [{"kind": None, "target": None}],
                },
                {
                    "name": "build_helper",
                    "pkg": BUILD_ID,
                    "dep_kinds": [{"kind": "build", "target": None}],
                },
                {
                    "name": "derive_helper",
                    "pkg": PROC_ID,
                    "dep_kinds": [{"kind": "dev", "target": "cfg(test)"}],
                },
            ],
        },
        {"id": SHA_ID, "features": ["default"], "deps": []},
        {"id": BUILD_ID, "features": [], "deps": []},
        {"id": PROC_ID, "features": [], "deps": []},
    ]
    return {
        "packages": packages,
        "workspace_members": [root_id],
        "resolve": {"nodes": nodes, "root": root_id},
    }


def lockfile() -> bytes:
    """Return matching version-four Cargo lock data."""

    return b'''version = 4

[[package]]
name = "sha2"
version = "0.11.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

[[package]]
name = "build-helper"
version = "1.0.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

[[package]]
name = "derive-helper"
version = "2.0.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
'''


def snapshot(scope: str) -> WorkspaceSnapshot:
    """Return one complete deterministic fixture snapshot."""

    prefix = "" if scope == "root" else "fuzz/"
    return WorkspaceSnapshot(
        scope=scope,
        manifest_path=f"{prefix}Cargo.toml",
        lockfile_path=f"{prefix}Cargo.lock",
        metadata=metadata(scope),
        lockfile_bytes=lockfile(),
    )


def crypto_registry() -> dict[str, object]:
    """Return a complete SHA-256 registry fixture bound to live repository files."""

    return {
        "schema": "zrm/cryptography-registry/v1",
        "components": [
            {
                "id": "ZRM-CRYPTO-001",
                "status": "implemented-reference",
                "primitive_type": "hash",
                "algorithm": "SHA-256",
                "parameter_set": "256-bit digest",
                "implementation_packages": [{"name": "sha2", "version": "0.11.0"}],
                "protocol_domains": ["zrm.resource.v1"],
                "purposes": ["Derive the canonical resource identifier."],
                "source_refs": ["crates/zrm-crypto/src/lib.rs"],
                "test_refs": ["crates/zrm-crypto/tests/vectors.rs"],
                "claimed_properties": ["Deterministic digest over explicitly framed bytes."],
                "non_claims": ["No signature, privacy, or proof-system claim."],
            }
        ],
    }


def build_surface_policy(scopes: list[str]) -> dict[str, object]:
    """Return exact review records for the fixture's executable build targets."""

    return {
        "schema": "zrm/build-surface-policy/v1",
        "components": [
            {
                "name": "build-helper",
                "version": "1.0.0",
                "target_kind": "custom-build",
                "scopes": scopes,
                "review_refs": ["docs/dependency-reviews/libfuzzer-sys-0.4.13.md"],
                "rationale": "Fixture build helper is explicit executable build surface.",
            },
            {
                "name": "derive-helper",
                "version": "2.0.0",
                "target_kind": "proc-macro",
                "scopes": scopes,
                "review_refs": ["docs/dependency-reviews/libfuzzer-sys-0.4.13.md"],
                "rationale": "Fixture derive helper is explicit compile-time code execution.",
            },
        ],
    }


class SbomTests(unittest.TestCase):
    """Exercise deterministic dependency and executable-build-surface inventory."""

    def test_order_independence_checksums_scopes_edges_and_surfaces(self) -> None:
        """All review-critical Cargo facts survive deterministic normalization."""

        first = build_sbom([snapshot("root"), snapshot("fuzz")])
        second = build_sbom([snapshot("fuzz"), snapshot("root")])

        self.assertEqual(first, second)
        sha = next(component for component in first["components"] if component["name"] == "sha2")
        self.assertEqual(sha["checksum_sha256"], "a" * 64)
        self.assertEqual(sha["scopes"], ["fuzz", "root"])
        self.assertTrue(any(edge["dependency_kind"] == "build" for edge in first["dependencies"]))
        self.assertEqual(len(first["build_script_components"]), 1)
        self.assertEqual(len(first["proc_macro_components"]), 1)
        self.assertNotIn("/private/", canonical_json(first))
        self.assertNotIn("/cargo/", canonical_json(first))

    def test_missing_or_malformed_registry_checksum_rejects(self) -> None:
        """A registry component cannot enter an SBOM without exact lock binding."""

        for replacement in ('checksum = "short"', ""):
            damaged = lockfile().replace(
                b'checksum = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"',
                replacement.encode("utf-8"),
            )
            candidate = snapshot("root")
            candidate = WorkspaceSnapshot(
                candidate.scope,
                candidate.manifest_path,
                candidate.lockfile_path,
                candidate.metadata,
                damaged,
            )
            with self.subTest(replacement=replacement), self.assertRaises(BomError):
                build_sbom([candidate])

    def test_empty_workspace_or_missing_resolve_graph_rejects(self) -> None:
        """Absent dependency coverage cannot produce a passing inventory."""

        with self.assertRaises(BomError):
            build_sbom([])
        candidate = snapshot("root")
        broken_metadata = {**candidate.metadata, "resolve": None}
        with self.assertRaises(BomError):
            build_sbom(
                [
                    WorkspaceSnapshot(
                        candidate.scope,
                        candidate.manifest_path,
                        candidate.lockfile_path,
                        broken_metadata,
                        candidate.lockfile_bytes,
                    )
                ]
            )

    def test_duplicate_lock_component_rejects(self) -> None:
        """Two checksum records for one package identity are ambiguous."""

        candidate = snapshot("root")
        duplicate = candidate.lockfile_bytes + lockfile().split(b"[[package]]", 1)[1]
        with self.assertRaises(BomError):
            build_sbom(
                [
                    WorkspaceSnapshot(
                        candidate.scope,
                        candidate.manifest_path,
                        candidate.lockfile_path,
                        candidate.metadata,
                        duplicate,
                    )
                ]
            )

    def test_distinct_local_packages_cannot_collapse_after_path_sanitization(self) -> None:
        """Omitting host paths cannot merge two different Cargo package identities."""

        candidate = snapshot("root")
        metadata_value = candidate.metadata
        packages = metadata_value["packages"]
        resolve = metadata_value["resolve"]
        self.assertIsInstance(packages, list)
        self.assertIsInstance(resolve, dict)
        if not isinstance(packages, list) or not isinstance(resolve, dict):
            self.fail("fixture metadata shape is invalid")
        duplicate = {
            **packages[0],
            "id": "path+file:///second/private/repository#zrm-test@0.1.0",
            "manifest_path": "/second/private/repository/Cargo.toml",
        }
        nodes = resolve["nodes"]
        self.assertIsInstance(nodes, list)
        if not isinstance(nodes, list):
            self.fail("fixture nodes must be a list")
        duplicate_node = {**nodes[0], "id": duplicate["id"], "deps": []}
        collapsed = {
            **metadata_value,
            "packages": [*packages, duplicate],
            "resolve": {**resolve, "nodes": [*nodes, duplicate_node]},
        }
        with self.assertRaises(BomError):
            build_sbom(
                [
                    WorkspaceSnapshot(
                        candidate.scope,
                        candidate.manifest_path,
                        candidate.lockfile_path,
                        collapsed,
                        candidate.lockfile_bytes,
                    )
                ]
            )

    def test_build_surface_policy_must_match_exact_components_and_scopes(self) -> None:
        """Every build script and proc macro has a live explicit review record."""

        sbom = build_sbom([snapshot("root"), snapshot("fuzz")])
        reviewed = apply_build_surface_policy(
            sbom, build_surface_policy(["fuzz", "root"])
        )
        self.assertEqual(len(reviewed["reviewed_build_surface"]), 2)
        self.assertIn("build_surface_policy_sha256", reviewed)

        policy = build_surface_policy(["fuzz", "root"])
        components = policy["components"]
        self.assertIsInstance(components, list)
        if not isinstance(components, list):
            self.fail("fixture build-surface components must be a list")
        invalid_policies = (
            {**policy, "components": components[1:]},
            {
                **policy,
                "components": [{**components[0], "scopes": ["root"]}, components[1]],
            },
            {
                **policy,
                "components": [
                    {
                        **components[0],
                        "review_refs": ["docs/dependency-reviews/missing.md"],
                    },
                    components[1],
                ],
            },
        )
        for invalid in invalid_policies:
            with self.subTest(invalid=invalid), self.assertRaises(BomError):
                apply_build_surface_policy(sbom, invalid)


class CbomTests(unittest.TestCase):
    """Exercise explicit cryptographic algorithm and implementation binding."""

    def test_complete_registry_builds_deterministic_cbom(self) -> None:
        """The primitive binds live code, tests, domains, and an SBOM component."""

        sbom = build_sbom([snapshot("root")])
        first = build_cbom(crypto_registry(), sbom)
        second = build_cbom(crypto_registry(), sbom)

        self.assertEqual(first, second)
        self.assertEqual(first["components"][0]["algorithm"], "SHA-256")
        self.assertEqual(len(first["components"][0]["implementation_component_refs"]), 1)

    def test_duplicate_id_or_domain_rejects(self) -> None:
        """Algorithm records and protocol domains cannot be ambiguous."""

        sbom = build_sbom([snapshot("root")])
        registry = crypto_registry()
        component = registry["components"][0]
        self.assertIsInstance(component, dict)
        if not isinstance(component, dict):
            self.fail("fixture component must be an object")
        for duplicate in (
            component,
            {**component, "id": "ZRM-CRYPTO-002"},
        ):
            with self.subTest(duplicate=duplicate), self.assertRaises(BomError):
                build_cbom({**registry, "components": [component, duplicate]}, sbom)

    def test_missing_implementation_or_stale_reference_rejects(self) -> None:
        """A registry label without dependency and source evidence cannot pass."""

        sbom = build_sbom([snapshot("root")])
        registry = crypto_registry()
        component = registry["components"][0]
        self.assertIsInstance(component, dict)
        if not isinstance(component, dict):
            self.fail("fixture component must be an object")
        invalid_components = (
            {**component, "implementation_packages": [{"name": "sha2", "version": "9.9.9"}]},
            {**component, "source_refs": ["crates/zrm-crypto/src/missing.rs"]},
        )
        for invalid in invalid_components:
            with self.subTest(invalid=invalid), self.assertRaises(BomError):
                build_cbom({**registry, "components": [invalid]}, sbom)

    def test_unregistered_crypto_named_package_rejects(self) -> None:
        """Recognizable cryptographic packages require an explicit CBOM owner."""

        sbom = build_sbom([snapshot("root")])
        extra = {
            **sbom["components"][0],
            "bom_ref": "registry:example.invalid/digest@1.0.0",
            "name": "digest",
            "version": "1.0.0",
        }
        modified = {**sbom, "components": [*sbom["components"], extra]}
        with self.assertRaises(BomError):
            build_cbom(crypto_registry(), modified)


class BomIoTests(unittest.TestCase):
    """Exercise strict policy decoding and confined deterministic output."""

    def test_duplicate_json_keys_reject_at_every_depth(self) -> None:
        """A later registry field cannot silently replace reviewed metadata."""

        sources = (
            '{"schema":"zrm/cryptography-registry/v1",'
            '"schema":"zrm/cryptography-registry/v1","components":[]}',
            '{"schema":"zrm/cryptography-registry/v1","components":['
            '{"id":"ZRM-CRYPTO-001","id":"ZRM-CRYPTO-002"}]}',
        )
        for source in sources:
            with self.subTest(source=source), self.assertRaisesRegex(
                BomError, "duplicate JSON object key"
            ):
                _decode_json_strict(source)

    def test_report_writer_cannot_escape_target_or_overwrite_source(self) -> None:
        """Generated evidence stays confined to target JSON paths."""

        for path in ("tools/sbom.json", "target/../sbom.json", "/tmp/sbom.json"):
            with self.subTest(path=path), patch("pathlib.Path.write_text") as write_text:
                with self.assertRaises(BomError):
                    _write_report(path, json.dumps({}))
                write_text.assert_not_called()


if __name__ == "__main__":
    unittest.main()
