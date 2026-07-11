"""Validate cryptography decisions and bind them to exact SBOM packages."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

if __package__:
    from .bom_common import (
        CBOM_SCHEMA,
        CRYPTOGRAPHY_REGISTRY_SCHEMA,
        ROOT,
        SBOM_SCHEMA,
        BomError,
        canonical_json,
        require_string,
        require_string_list,
        validate_references,
    )
else:
    from bom_common import (
        CBOM_SCHEMA,
        CRYPTOGRAPHY_REGISTRY_SCHEMA,
        ROOT,
        SBOM_SCHEMA,
        BomError,
        canonical_json,
        require_string,
        require_string_list,
        validate_references,
    )


CRYPTO_COMPONENT_ID = re.compile(r"ZRM-CRYPTO-[0-9]{3}")
CRYPTO_PACKAGE_NAME = re.compile(
    r"(?:^|[-_])(?:aead|blake[0-9]*|cipher|crypto|digest|ed25519|k256|keccak|"
    r"openssl|p256|ring|rustls|secp[0-9]*|sha[0-9]*|signature)(?:$|[-_])"
)


def build_cbom(
    registry: object,
    sbom: Mapping[str, object],
    repository_root: Path = ROOT,
) -> dict[str, Any]:
    """Validate the cryptography registry and bind it to exact SBOM components."""

    if not isinstance(registry, dict) or set(registry) != {"schema", "components"}:
        raise BomError("cryptography registry must contain exactly schema and components")
    if registry.get("schema") != CRYPTOGRAPHY_REGISTRY_SCHEMA:
        raise BomError("unexpected cryptography registry schema")
    if sbom.get("schema") != SBOM_SCHEMA or not isinstance(sbom.get("components"), list):
        raise BomError("CBOM generation requires a valid ZRM source SBOM")
    sbom_index = _sbom_index(sbom["components"])
    registry_components = registry.get("components")
    if not isinstance(registry_components, list) or not registry_components:
        raise BomError("cryptography registry must contain at least one component")
    seen_ids: set[str] = set()
    seen_domains: set[str] = set()
    covered_packages: set[tuple[str, str]] = set()
    normalized_components = [
        _normalize_component(
            component,
            sbom_index,
            repository_root,
            seen_ids,
            seen_domains,
            covered_packages,
        )
        for component in registry_components
    ]
    recognizable = {
        (str(component["name"]), str(component["version"]))
        for component in sbom["components"]
        if isinstance(component, dict)
        and CRYPTO_PACKAGE_NAME.search(str(component.get("name", ""))) is not None
    }
    uncovered = recognizable - covered_packages
    if uncovered:
        raise BomError(f"cryptography-named SBOM packages lack CBOM ownership: {sorted(uncovered)}")
    normalized_components.sort(key=lambda item: str(item["id"]))
    payload: dict[str, Any] = {
        "schema": CBOM_SCHEMA,
        "inventory_kind": "ZRM-native cryptographic bill of materials",
        "source_sbom_inventory_sha256": require_string(
            sbom.get("inventory_sha256"), "source SBOM inventory fingerprint"
        ),
        "components": normalized_components,
        "summary": {
            "component_count": len(normalized_components),
            "implementation_package_count": len(covered_packages),
            "protocol_domain_count": len(seen_domains),
        },
        "non_claims": [
            "registry completeness is bounded to recognizable Cargo packages and reviewed records",
            "the CBOM does not establish implementation correctness, key management, or side-channel resistance",
            "future proof systems, signatures, TLS, hardware, and operating-system cryptography need new records",
            "this report is not signed provenance, a security audit, or production authority",
        ],
    }
    payload["cryptography_registry_sha256"] = hashlib.sha256(
        canonical_json(registry).encode("utf-8")
    ).hexdigest()
    payload["inventory_sha256"] = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return payload


def _sbom_index(components: list[object]) -> dict[tuple[str, str], list[dict[str, object]]]:
    """Index SBOM package versions while retaining ambiguous matches."""

    index: dict[tuple[str, str], list[dict[str, object]]] = {}
    for component in components:
        if not isinstance(component, dict):
            raise BomError("SBOM component must be an object")
        name = require_string(component.get("name"), "SBOM component name")
        version = require_string(component.get("version"), "SBOM component version")
        require_string(component.get("bom_ref"), "SBOM component reference")
        index.setdefault((name, version), []).append(component)
    return index


def _normalize_component(
    component: object,
    sbom_index: Mapping[tuple[str, str], list[dict[str, object]]],
    repository_root: Path,
    seen_ids: set[str],
    seen_domains: set[str],
    covered_packages: set[tuple[str, str]],
) -> dict[str, object]:
    """Validate and bind one cryptography component record."""

    required_fields = {
        "id",
        "status",
        "primitive_type",
        "algorithm",
        "parameter_set",
        "implementation_packages",
        "protocol_domains",
        "purposes",
        "source_refs",
        "test_refs",
        "claimed_properties",
        "non_claims",
    }
    if not isinstance(component, dict) or set(component) != required_fields:
        raise BomError("each cryptography component must contain the exact v1 fields")
    component_id = require_string(component.get("id"), "cryptography component ID")
    if CRYPTO_COMPONENT_ID.fullmatch(component_id) is None:
        raise BomError(f"invalid cryptography component ID: {component_id!r}")
    if component_id in seen_ids:
        raise BomError(f"duplicate cryptography component ID: {component_id}")
    seen_ids.add(component_id)
    status = require_string(component.get("status"), "cryptography component status")
    if status not in {"implemented-reference", "implemented-tooling"}:
        raise BomError(f"unsupported cryptography component status: {status}")
    implementations = component.get("implementation_packages")
    if not isinstance(implementations, list) or not implementations:
        raise BomError("cryptography implementation_packages must be a nonempty list")
    normalized_implementations, implementation_refs = _bind_implementations(
        implementations, sbom_index, covered_packages
    )
    domains = require_string_list(component.get("protocol_domains"), "cryptography protocol_domains")
    for domain in domains:
        if domain in seen_domains:
            raise BomError(f"duplicate cryptography protocol domain: {domain}")
        seen_domains.add(domain)
    return {
        "id": component_id,
        "status": status,
        "primitive_type": require_string(
            component.get("primitive_type"), "cryptography primitive_type"
        ),
        "algorithm": require_string(component.get("algorithm"), "cryptography algorithm"),
        "parameter_set": require_string(
            component.get("parameter_set"), "cryptography parameter_set"
        ),
        "implementation_packages": normalized_implementations,
        "implementation_component_refs": implementation_refs,
        "protocol_domains": sorted(domains),
        "purposes": sorted(require_string_list(component.get("purposes"), "cryptography purposes")),
        "source_refs": validate_references(
            require_string_list(component.get("source_refs"), "cryptography source_refs"),
            "cryptography source_refs",
            repository_root,
        ),
        "test_refs": validate_references(
            require_string_list(component.get("test_refs"), "cryptography test_refs"),
            "cryptography test_refs",
            repository_root,
        ),
        "claimed_properties": sorted(
            require_string_list(component.get("claimed_properties"), "cryptography claimed_properties")
        ),
        "non_claims": sorted(
            require_string_list(component.get("non_claims"), "cryptography non_claims")
        ),
    }


def _bind_implementations(
    implementations: list[object],
    sbom_index: Mapping[tuple[str, str], list[dict[str, object]]],
    covered_packages: set[tuple[str, str]],
) -> tuple[list[dict[str, str]], list[str]]:
    """Bind exact implementation package records to unique SBOM references."""

    implementation_refs: list[str] = []
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for implementation in implementations:
        if not isinstance(implementation, dict) or set(implementation) != {"name", "version"}:
            raise BomError("cryptography implementation package needs exact name and version")
        name = require_string(implementation.get("name"), "implementation package name")
        version = require_string(implementation.get("version"), "implementation package version")
        key = (name, version)
        if key in seen:
            raise BomError(f"duplicate cryptography implementation package: {key}")
        seen.add(key)
        matches = sbom_index.get(key, [])
        if len(matches) != 1:
            raise BomError(f"cryptography implementation {name} {version} has {len(matches)} SBOM matches")
        covered_packages.add(key)
        implementation_refs.append(str(matches[0]["bom_ref"]))
        normalized.append({"name": name, "version": version})
    return sorted(normalized, key=lambda item: (item["name"], item["version"])), sorted(
        implementation_refs
    )
