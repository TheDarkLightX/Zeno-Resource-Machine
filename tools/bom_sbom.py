"""Normalize locked Cargo graphs and reviewed executable build surface."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__:
    from .bom_common import (
        BUILD_SURFACE_POLICY_SCHEMA,
        MAX_INPUT_BYTES,
        ROOT,
        SBOM_SCHEMA,
        BomError,
        WorkspaceSnapshot,
        canonical_json,
        normalize_path,
        require_string,
        require_string_list,
        validate_references,
    )
else:
    from bom_common import (
        BUILD_SURFACE_POLICY_SCHEMA,
        MAX_INPUT_BYTES,
        ROOT,
        SBOM_SCHEMA,
        BomError,
        WorkspaceSnapshot,
        canonical_json,
        normalize_path,
        require_string,
        require_string_list,
        validate_references,
    )


REGISTRY_CHECKSUM = re.compile(r"[0-9a-f]{64}")


def _lock_checksums(snapshot: WorkspaceSnapshot) -> dict[tuple[str, str, str], str]:
    """Return exact registry package checksums from one lockfile."""

    if not isinstance(snapshot.lockfile_bytes, bytes) or len(snapshot.lockfile_bytes) > MAX_INPUT_BYTES:
        raise BomError(f"{snapshot.scope} lockfile is absent or exceeds the input ceiling")
    try:
        lock = tomllib.loads(snapshot.lockfile_bytes.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise BomError(f"cannot decode {snapshot.scope} Cargo lockfile") from error
    packages = lock.get("package")
    if not isinstance(packages, list):
        raise BomError(f"{snapshot.scope} Cargo lockfile has no package list")
    checksums: dict[tuple[str, str, str], str] = {}
    for package in packages:
        if not isinstance(package, dict):
            raise BomError(f"{snapshot.scope} lock package must be an object")
        source = package.get("source")
        if source is None:
            continue
        name = require_string(package.get("name"), "lock package name")
        version = require_string(package.get("version"), "lock package version")
        source_text = require_string(source, "lock package source")
        checksum = package.get("checksum")
        if not isinstance(checksum, str) or REGISTRY_CHECKSUM.fullmatch(checksum) is None:
            raise BomError(f"locked external package {name} {version} lacks a SHA-256 checksum")
        key = (name, version, source_text)
        if key in checksums:
            raise BomError(f"duplicate locked package identity: {name} {version} {source_text}")
        checksums[key] = checksum
    return checksums


def _component_identity(package: Mapping[str, object], checksum: str | None) -> dict[str, object]:
    """Return sanitized stable package identity fields."""

    name = require_string(package.get("name"), "metadata package name")
    version = require_string(package.get("version"), "metadata package version")
    source = package.get("source")
    if source is None:
        source_kind = "repository"
        source_value = "repository"
        manifest_path = package.get("manifest_path")
        if not isinstance(manifest_path, str):
            raise BomError(f"repository package {name} {version} lacks a manifest path")
        try:
            repository_path: str | None = (
                Path(manifest_path).resolve().relative_to(ROOT.resolve()).as_posix()
            )
        except ValueError:
            repository_path = None
    else:
        source_text = require_string(source, "metadata package source")
        if not source_text.startswith("registry+"):
            raise BomError(f"unsupported unlocked external package source: {source_text}")
        source_kind = "registry"
        source_value = source_text.removeprefix("registry+")
        if checksum is None:
            raise BomError(f"registry package {name} {version} has no matching lock checksum")
        repository_path = None
    stable_identity = {
        "name": name,
        "source": source_value,
        "source_kind": source_kind,
        "version": version,
        "repository_path": repository_path,
    }
    identity_bytes = json.dumps(
        stable_identity, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        **stable_identity,
        "bom_ref": "zrm-component:" + hashlib.sha256(identity_bytes).hexdigest(),
    }


def _target_kinds(package: Mapping[str, object]) -> tuple[str, ...]:
    """Return sorted Cargo target kinds for one package."""

    targets = package.get("targets")
    if not isinstance(targets, list) or not targets:
        raise BomError("metadata package has no targets")
    kinds: set[str] = set()
    for target in targets:
        if not isinstance(target, dict) or not isinstance(target.get("kind"), list):
            raise BomError("metadata target lacks a kind list")
        for kind in target["kind"]:
            kinds.add(require_string(kind, "metadata target kind"))
    return tuple(sorted(kinds))


def _snapshot_packages(
    snapshot: WorkspaceSnapshot,
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]], set[str]]:
    """Return package-id maps, resolve nodes, and workspace member IDs."""

    if snapshot.scope not in {"root", "fuzz"}:
        raise BomError(f"unsupported workspace scope: {snapshot.scope!r}")
    normalize_path(snapshot.manifest_path)
    normalize_path(snapshot.lockfile_path)
    metadata = snapshot.metadata
    if not isinstance(metadata, Mapping):
        raise BomError(f"{snapshot.scope} Cargo metadata must be an object")
    packages = metadata.get("packages")
    members = metadata.get("workspace_members")
    resolve = metadata.get("resolve")
    if not isinstance(packages, list) or not packages:
        raise BomError(f"{snapshot.scope} Cargo metadata has no packages")
    if not isinstance(members, list) or not members:
        raise BomError(f"{snapshot.scope} Cargo metadata has no workspace members")
    if not isinstance(resolve, Mapping) or not isinstance(resolve.get("nodes"), list):
        raise BomError(f"{snapshot.scope} Cargo metadata has no resolve graph")
    package_map: dict[str, dict[str, object]] = {}
    for package in packages:
        if not isinstance(package, dict):
            raise BomError("metadata package must be an object")
        package_id = require_string(package.get("id"), "metadata package ID")
        if package_id in package_map:
            raise BomError(f"duplicate metadata package ID: {package_id}")
        package_map[package_id] = package
    node_map: dict[str, dict[str, object]] = {}
    for node in resolve["nodes"]:
        if not isinstance(node, dict):
            raise BomError("metadata resolve node must be an object")
        node_id = require_string(node.get("id"), "metadata resolve node ID")
        if node_id in node_map:
            raise BomError(f"duplicate metadata resolve node: {node_id}")
        node_map[node_id] = node
    if set(package_map) != set(node_map):
        raise BomError(f"{snapshot.scope} package and resolve-node coverage differ")
    member_set = {require_string(member, "workspace member ID") for member in members}
    if not member_set.issubset(package_map):
        raise BomError(f"{snapshot.scope} workspace member is absent from package metadata")
    return package_map, node_map, member_set


def _merge_component(
    components: dict[str, dict[str, object]],
    candidate: dict[str, object],
    scope: str,
) -> None:
    """Insert or consistently merge one component across workspace scopes."""

    bom_ref = str(candidate["bom_ref"])
    existing = components.get(bom_ref)
    if existing is None:
        components[bom_ref] = candidate
        return
    for field in (
        "name",
        "version",
        "source",
        "source_kind",
        "repository_path",
        "checksum_sha256",
        "license_declared",
    ):
        if existing[field] != candidate[field]:
            raise BomError(f"inconsistent component metadata for {bom_ref}: {field}")
    for field in ("activated_features", "target_kinds"):
        existing[field] = sorted(set(existing[field]) | set(candidate[field]))
    existing["scopes"] = sorted(set(existing["scopes"]) | {scope})
    existing["workspace_member_scopes"] = sorted(
        set(existing["workspace_member_scopes"])
        | set(candidate["workspace_member_scopes"])
    )


def build_sbom(workspaces: Sequence[WorkspaceSnapshot]) -> dict[str, Any]:
    """Build one deterministic ZRM source dependency inventory."""

    if not workspaces:
        raise BomError("SBOM generation requires at least one workspace snapshot")
    scopes = [snapshot.scope for snapshot in workspaces]
    if len(scopes) != len(set(scopes)):
        raise BomError("duplicate workspace scope")
    components: dict[str, dict[str, object]] = {}
    dependencies: set[tuple[str, str, str, str, str, str]] = set()
    workspace_reports: list[dict[str, object]] = []
    for snapshot in sorted(workspaces, key=lambda item: item.scope):
        checksums = _lock_checksums(snapshot)
        package_map, node_map, members = _snapshot_packages(snapshot)
        package_refs: dict[str, str] = {}
        package_ref_owners: dict[str, str] = {}
        for package_id, package in package_map.items():
            name = require_string(package.get("name"), "metadata package name")
            version = require_string(package.get("version"), "metadata package version")
            source = package.get("source")
            checksum: str | None = None
            if source is not None:
                source_text = require_string(source, "metadata package source")
                checksum = checksums.get((name, version, source_text))
            identity = _component_identity(package, checksum)
            bom_ref = str(identity["bom_ref"])
            prior_owner = package_ref_owners.get(bom_ref)
            if prior_owner is not None and prior_owner != package_id:
                raise BomError(
                    "distinct Cargo package IDs collapse to one sanitized component identity"
                )
            package_ref_owners[bom_ref] = package_id
            package_refs[package_id] = bom_ref
            node = node_map[package_id]
            features = node.get("features")
            if not isinstance(features, list) or not all(isinstance(item, str) for item in features):
                raise BomError(f"metadata node features are malformed: {package_id}")
            license_value = package.get("license")
            if license_value is not None and not isinstance(license_value, str):
                raise BomError(f"metadata package license is malformed: {package_id}")
            candidate = {
                **identity,
                "checksum_sha256": checksum,
                "license_declared": license_value,
                "activated_features": sorted(set(features)),
                "target_kinds": list(_target_kinds(package)),
                "scopes": [snapshot.scope],
                "workspace_member_scopes": [snapshot.scope] if package_id in members else [],
            }
            _merge_component(components, candidate, snapshot.scope)
        _add_dependency_edges(snapshot, node_map, package_refs, dependencies)
        workspace_reports.append(
            {
                "scope": snapshot.scope,
                "manifest_path": normalize_path(snapshot.manifest_path),
                "lockfile_path": normalize_path(snapshot.lockfile_path),
                "lockfile_sha256": hashlib.sha256(snapshot.lockfile_bytes).hexdigest(),
                "workspace_component_refs": sorted(package_refs[member] for member in members),
            }
        )
    return _sbom_report(components, dependencies, workspace_reports)


def _add_dependency_edges(
    snapshot: WorkspaceSnapshot,
    node_map: Mapping[str, Mapping[str, object]],
    package_refs: Mapping[str, str],
    dependencies: set[tuple[str, str, str, str, str, str]],
) -> None:
    """Add normalized dependency-kind edges for one workspace graph."""

    for node_id, node in node_map.items():
        deps = node.get("deps")
        if not isinstance(deps, list):
            raise BomError(f"metadata resolve dependencies are malformed: {node_id}")
        for dependency in deps:
            if not isinstance(dependency, dict):
                raise BomError("metadata dependency edge must be an object")
            dependency_name = require_string(dependency.get("name"), "metadata dependency name")
            dependency_id = require_string(
                dependency.get("pkg"), "metadata dependency package ID"
            )
            if dependency_id not in package_refs:
                raise BomError(f"dependency edge references unknown package: {dependency_id}")
            dependency_kinds = dependency.get("dep_kinds")
            if not isinstance(dependency_kinds, list) or not dependency_kinds:
                raise BomError("metadata dependency edge has no dependency kinds")
            for dependency_kind in dependency_kinds:
                if not isinstance(dependency_kind, dict):
                    raise BomError("metadata dependency kind must be an object")
                kind = dependency_kind.get("kind")
                normalized_kind = "normal" if kind is None else require_string(
                    kind, "metadata dependency kind"
                )
                if normalized_kind not in {"normal", "build", "dev"}:
                    raise BomError(f"unsupported Cargo dependency kind: {normalized_kind}")
                target = dependency_kind.get("target")
                if target is not None and not isinstance(target, str):
                    raise BomError("metadata dependency target condition must be a string or null")
                edge = (
                    snapshot.scope,
                    package_refs[node_id],
                    package_refs[dependency_id],
                    dependency_name,
                    normalized_kind,
                    target or "",
                )
                if edge in dependencies:
                    raise BomError(f"duplicate dependency edge: {edge}")
                dependencies.add(edge)


def _sbom_report(
    components: Mapping[str, dict[str, object]],
    dependencies: set[tuple[str, str, str, str, str, str]],
    workspace_reports: list[dict[str, object]],
) -> dict[str, Any]:
    """Assemble and fingerprint normalized SBOM components and edges."""

    component_list = sorted(components.values(), key=lambda item: str(item["bom_ref"]))
    dependency_list = [
        {
            "scope": edge[0],
            "from_component_ref": edge[1],
            "to_component_ref": edge[2],
            "dependency_name": edge[3],
            "dependency_kind": edge[4],
            "target_condition": edge[5] or None,
        }
        for edge in sorted(dependencies)
    ]
    payload: dict[str, Any] = {
        "schema": SBOM_SCHEMA,
        "inventory_kind": "ZRM-native Cargo source software bill of materials",
        "components": component_list,
        "dependencies": dependency_list,
        "workspaces": workspace_reports,
        "build_script_components": sorted(
            component["bom_ref"]
            for component in component_list
            if "custom-build" in component["target_kinds"]
        ),
        "proc_macro_components": sorted(
            component["bom_ref"]
            for component in component_list
            if "proc-macro" in component["target_kinds"]
        ),
        "summary": {
            "component_count": len(component_list),
            "dependency_edge_count": len(dependency_list),
            "workspace_count": len(workspace_reports),
        },
        "non_claims": [
            "this ZRM-native source inventory does not claim SPDX or CycloneDX conformance",
            "registry checksums do not prove source review, maintainer identity, or benign behavior",
            "compiled artifacts, linker inputs, operating-system packages, and deployment images are outside this report",
            "this report is not signed provenance, a vulnerability scan, or a reproducible-build receipt",
        ],
    }
    payload["inventory_sha256"] = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return payload


def apply_build_surface_policy(
    sbom: Mapping[str, object],
    policy: object,
    repository_root: Path = ROOT,
) -> dict[str, Any]:
    """Bind every discovered build script and proc macro to exact review records."""

    if sbom.get("schema") != SBOM_SCHEMA or not isinstance(sbom.get("components"), list):
        raise BomError("build-surface validation requires a valid ZRM source SBOM")
    if not isinstance(policy, dict) or set(policy) != {"schema", "components"}:
        raise BomError("build-surface policy must contain exactly schema and components")
    if policy.get("schema") != BUILD_SURFACE_POLICY_SCHEMA:
        raise BomError("unexpected build-surface policy schema")
    discovered = _discovered_build_surface(sbom["components"])
    declared = _declared_build_surface(policy.get("components"), repository_root)
    missing = set(discovered) - set(declared)
    stale = set(declared) - set(discovered)
    if missing:
        raise BomError(f"unreviewed executable build components: {sorted(missing)}")
    if stale:
        raise BomError(f"stale executable build component approvals: {sorted(stale)}")
    normalized: list[dict[str, object]] = []
    for key in sorted(discovered):
        bom_ref, scopes = discovered[key]
        record = declared[key]
        if record["scopes"] != scopes:
            raise BomError(
                f"build-surface scope mismatch for {key}: {record['scopes']} != {scopes}"
            )
        normalized.append({**record, "component_ref": bom_ref})
    payload = dict(sbom)
    payload.pop("inventory_sha256", None)
    payload["reviewed_build_surface"] = normalized
    payload["build_surface_policy_sha256"] = hashlib.sha256(
        canonical_json(policy).encode("utf-8")
    ).hexdigest()
    payload["inventory_sha256"] = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return payload


def _discovered_build_surface(
    components: Sequence[object],
) -> dict[tuple[str, str, str], tuple[str, list[str]]]:
    """Return exact executable target identities from SBOM components."""

    discovered: dict[tuple[str, str, str], tuple[str, list[str]]] = {}
    for component in components:
        if not isinstance(component, dict):
            raise BomError("SBOM component must be an object")
        name = require_string(component.get("name"), "SBOM component name")
        version = require_string(component.get("version"), "SBOM component version")
        bom_ref = require_string(component.get("bom_ref"), "SBOM component reference")
        scopes = component.get("scopes")
        target_kinds = component.get("target_kinds")
        if not isinstance(scopes, list) or not all(scope in {"root", "fuzz"} for scope in scopes):
            raise BomError(f"SBOM component scopes are malformed: {name} {version}")
        if not isinstance(target_kinds, list):
            raise BomError(f"SBOM component target kinds are malformed: {name} {version}")
        for target_kind in ("custom-build", "proc-macro"):
            if target_kind in target_kinds:
                key = (name, version, target_kind)
                if key in discovered:
                    raise BomError(f"ambiguous executable build component identity: {key}")
                discovered[key] = (bom_ref, sorted(set(scopes)))
    return discovered


def _declared_build_surface(
    components: object, repository_root: Path
) -> dict[tuple[str, str, str], dict[str, object]]:
    """Validate and normalize reviewed executable target records."""

    if not isinstance(components, list):
        raise BomError("build-surface policy components must be a list")
    required_fields = {
        "name",
        "version",
        "target_kind",
        "scopes",
        "review_refs",
        "rationale",
    }
    declared: dict[tuple[str, str, str], dict[str, object]] = {}
    for component in components:
        if not isinstance(component, dict) or set(component) != required_fields:
            raise BomError("each build-surface component must contain the exact v1 fields")
        name = require_string(component.get("name"), "build-surface package name")
        version = require_string(component.get("version"), "build-surface package version")
        target_kind = require_string(component.get("target_kind"), "build-surface target kind")
        if target_kind not in {"custom-build", "proc-macro"}:
            raise BomError(f"unsupported executable build target kind: {target_kind}")
        key = (name, version, target_kind)
        if key in declared:
            raise BomError(f"duplicate build-surface policy component: {key}")
        scopes = require_string_list(component.get("scopes"), "build-surface scopes")
        if any(scope not in {"root", "fuzz"} for scope in scopes) or len(scopes) != len(
            set(scopes)
        ):
            raise BomError(f"invalid or duplicate build-surface scopes: {key}")
        declared[key] = {
            "name": name,
            "version": version,
            "target_kind": target_kind,
            "scopes": sorted(scopes),
            "review_refs": validate_references(
                require_string_list(component.get("review_refs"), "build-surface review_refs"),
                "build-surface review_refs",
                repository_root,
            ),
            "rationale": require_string(component.get("rationale"), "build-surface rationale"),
        }
    return declared
