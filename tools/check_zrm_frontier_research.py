#!/usr/bin/env python3
"""Validate the revision-bound, non-authoritative ZRM frontier research packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent
PACKET = ROOT / "research/zrm_frontier_v2"
BASE_REVISION = "a4d2868d92807947cbad5f0d7fd828b74ae1368c"
MANIFEST = PACKET / "manifest.json"
EXPLICIT_PACKET_FILES = {
    "formal/lean/arm_zrm_frontier_v2/.gitignore",
    "reference_models/zrm_composition_frontier_v2.py",
    "reference_models/zrm_composition_frontier_v2_explorer.py",
    "reference_models/tests/test_zrm_composition_frontier_v2.py",
    "reference_models/deterministic_authenticated_batch_v1.py",
    "reference_models/deterministic_authenticated_batch_explorer.py",
    "reference_models/tests/test_deterministic_authenticated_batch_v1.py",
    "tools/check_zrm_frontier_research.py",
    "tools/tests/test_zrm_frontier_research.py",
}
ALLOWED_HYPOTHESIS_STATUSES = {
    "proposed",
    "source_informed",
    "source_supported",
    "supported_bounded",
    "under_test",
    "unknown",
}
EXECUTED_STATUS_PREFIXES = ("passed",)
FORBIDDEN_PUBLIC_DETAIL = {
    "src-arm-compliance",
    "src-arm-constants",
    "src-arm-transaction",
    "arm security question",
    "admits_forged_binding_signature",
    "malicious_known_scalars",
    "malicious_relation",
    "forged binding signature",
}
EXPECTED_ESSO_REVISION = "db8a3f8a782a508ada5005a2cf177f25c58f451d"
EXPECTED_ESSO_MODELS = {
    "atomic_commit_recovery",
    "commit_outcome_resolution",
    "exact_once",
    "plan_freshness",
    "policy_creation_suspension",
    "recursive_composition",
    "replay_linearization",
    "verifier_fact_freshness",
}
EXPECTED_ESSO_MUTANTS = {
    "caller_substitutes_leaf_position",
    "creation_under_wrong_policy",
    "development_fact_grants_authority",
    "nonempty_message_smuggled_as_empty",
    "partial_durable_commit",
    "policy_change_reuses_machine_root",
    "recursive_fold_omits_middle_leaf",
    "replay_lookup_outside_commit_boundary",
    "resolution_reapplies_effect",
    "retry_duplicates_effect",
    "revoked_current_remains_selected",
    "stale_plan_commits",
    "suspended_creation_allowed",
    "unknown_reported_as_rejected",
}
EXPECTED_ESSO_MISSING_FIELDS = {
    "esso_executable_sha256",
    "model_sha256",
    "property_sha256",
    "bounds",
    "seeds",
    "backend_versions",
    "counterexample_artifacts",
    "artifact_digests",
}
EXPECTED_BASE_ARTIFACT_INTEGRITY = {
    "ZRM-E01": {
        "path": "evidence/arm-zrm-frontier-exploration-v1.json",
        "base_revision": BASE_REVISION,
        "git_blob_sha1": "81b4020b37449b7a04db7690282f48d9f55c8638",
        "sha256": "ca5ab93f98832002e7ba678e98114085075dec9f41653f864a309402fd619a9f",
    }
}
EXPECTED_RESEARCH_KERNEL_RUNS = [
    {
        "id": "zrm-frontier-v2-2026-07-14",
        "purpose": "ARM and ZRM architecture seed",
        "atoms": 22,
        "edges": 13,
        "refutation_plans": 6,
        "evidence_records": 2,
        "reformulations": 5,
        "promotion_probe": "intentionally rejected because a required dependency was not satisfied",
    },
    {
        "id": "zrm-privacy-policy-v1-2026-07-14",
        "purpose": "private logic and policy receipt architecture",
        "hypotheses": 12,
        "edges": 39,
        "refutation_plans": 12,
        "evidence_records": 4,
        "reformulations": 18,
        "compounding": "retrieved prior atoms before authoring",
    },
    {
        "id": "zrm-compound-architecture-v2-2026-07-14",
        "purpose": "cross-run recursion, concurrency, privacy, and assurance synthesis",
        "retrieved_prior_atoms": 40,
        "hypotheses": 10,
        "edges": 21,
        "refutation_records": 10,
        "actual_counterexamples": 1,
        "evidence_records": 3,
        "reformulations": 6,
    },
]
EXPECTED_MANIFEST_NON_CLAIMS = [
    "The manifest authenticates packet bytes only; it does not promote research claims or protocol authority.",
    "External source availability and mutable web content are outside this local digest set.",
]


class FrontierPacketError(ValueError):
    """Raised when a packet invariant fails closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FrontierPacketError(message)


def canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise FrontierPacketError(f"value is not canonical JSON data: {error}") from error


def json_exact_equal(left: object, right: object) -> bool:
    """Compare JSON values without Python's bool/int or int/float coercions."""

    return canonical_json_bytes(left) == canonical_json_bytes(right)


def _reject_nonstandard_json_constant(value: str) -> None:
    raise ValueError(f"nonstandard JSON constant {value}")


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_nonstandard_json_constant,
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (OSError, UnicodeError, ValueError) as error:
        raise FrontierPacketError(f"cannot load {path.relative_to(ROOT)}: {error}") from error
    require(isinstance(value, dict), f"{path.relative_to(ROOT)} root must be an object")
    return value


def require_nonempty_text(value: object, field: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{field} must be nonempty text")
    return value


def safe_relative_path(value: object, field: str) -> str:
    path = require_nonempty_text(value, field)
    pure = PurePosixPath(path)
    require(not pure.is_absolute(), f"{field} must be relative")
    require(".." not in pure.parts and "." not in pure.parts, f"{field} is not normalized")
    require("\\" not in path and "\x00" not in path, f"{field} contains unsafe bytes")
    return path


def unique_ids(records: object, field: str, prefix: str) -> tuple[list[dict[str, Any]], set[str]]:
    require(isinstance(records, list), f"{field} must be a list")
    typed: list[dict[str, Any]] = []
    ids: list[str] = []
    for index, record in enumerate(records):
        require(isinstance(record, dict), f"{field}[{index}] must be an object")
        identifier = require_nonempty_text(record.get("id"), f"{field}[{index}].id")
        require(identifier.startswith(prefix), f"{field}[{index}].id has wrong prefix")
        typed.append(record)
        ids.append(identifier)
    require(len(ids) == len(set(ids)), f"{field} IDs must be unique")
    return typed, set(ids)


def validate_sources(data: dict[str, Any]) -> set[str]:
    require(data.get("schema") == "zrm/research-source-ledger/v1", "unexpected source schema")
    require(data.get("base_revision") == BASE_REVISION, "source ledger base revision mismatch")
    records, identifiers = unique_ids(data.get("sources"), "sources", "SRC-")
    require(len(records) >= 50, "source ledger is unexpectedly shallow")
    for record in records:
        source_id = record["id"]
        require_nonempty_text(record.get("kind"), f"{source_id}.kind")
        require_nonempty_text(record.get("title"), f"{source_id}.title")
        uri = require_nonempty_text(record.get("uri"), f"{source_id}.uri")
        require(uri.startswith("https://"), f"{source_id}.uri must use HTTPS")
        require_nonempty_text(record.get("revision"), f"{source_id}.revision")
        require(record.get("primary") is True, f"{source_id} must be marked primary")
    return identifiers


def validate_experiments(data: dict[str, Any]) -> tuple[set[str], dict[str, dict[str, Any]]]:
    require(data.get("schema") == "zrm/frontier-experiments/v3", "unexpected experiment schema")
    records, identifiers = unique_ids(data.get("experiments"), "experiments", "ZRM-E")
    require(len(records) >= 20, "experiment registry is unexpectedly shallow")
    by_id = {record["id"]: record for record in records}
    for record in records:
        experiment_id = record["id"]
        status = require_nonempty_text(record.get("status"), f"{experiment_id}.status")
        require_nonempty_text(record.get("title"), f"{experiment_id}.title")
        require_nonempty_text(record.get("runner"), f"{experiment_id}.runner")
        require_nonempty_text(record.get("result"), f"{experiment_id}.result")
        artifacts = record.get("artifacts", [])
        require(isinstance(artifacts, list), f"{experiment_id}.artifacts must be a list")
        for index, value in enumerate(artifacts):
            relative = safe_relative_path(value, f"{experiment_id}.artifacts[{index}]")
            if status.startswith(EXECUTED_STATUS_PREFIXES):
                require((ROOT / relative).is_file(), f"{experiment_id} artifact does not exist: {relative}")
        base_integrity = record.get("base_artifact_integrity")
        expected_base_integrity = EXPECTED_BASE_ARTIFACT_INTEGRITY.get(experiment_id)
        require(
            json_exact_equal(base_integrity, expected_base_integrity),
            f"{experiment_id} base artifact identity mismatch",
        )
        if expected_base_integrity is not None:
            relative = safe_relative_path(
                expected_base_integrity["path"],
                f"{experiment_id}.base_artifact_integrity.path",
            )
            require(relative in artifacts, f"{experiment_id} base artifact is not listed as an artifact")
            payload_path = ROOT / relative
            require(payload_path.is_file(), f"{experiment_id} base artifact does not exist: {relative}")
            payload = payload_path.read_bytes()
            git_blob = hashlib.sha1(
                b"blob " + str(len(payload)).encode("ascii") + b"\x00" + payload
            ).hexdigest()
            require(expected_base_integrity["git_blob_sha1"] == git_blob, f"{experiment_id} base artifact Git blob mismatch")
            require(expected_base_integrity["sha256"] == hashlib.sha256(payload).hexdigest(), f"{experiment_id} base artifact SHA-256 mismatch")
    return identifiers, by_id


def validate_hypotheses(
    data: dict[str, Any], source_ids: set[str], experiment_ids: set[str]
) -> tuple[set[str], dict[str, dict[str, Any]]]:
    require(data.get("schema") == "zrm/frontier-hypotheses/v3", "unexpected hypothesis schema")
    require(data.get("base_revision") == BASE_REVISION, "hypothesis base revision mismatch")
    records, identifiers = unique_ids(data.get("hypotheses"), "hypotheses", "ZRM-H")
    require(len(records) == 24, "expected exactly 24 ranked hypotheses")
    ranks = [record.get("rank") for record in records]
    require(
        all(type(rank) is int for rank in ranks),
        "hypothesis ranks must be exact integers",
    )
    require(ranks == list(range(1, len(records) + 1)), "hypothesis ranks must be ordered and contiguous")
    by_id = {record["id"]: record for record in records}
    for record in records:
        hypothesis_id = record["id"]
        require(record.get("status") in ALLOWED_HYPOTHESIS_STATUSES, f"{hypothesis_id} status is invalid")
        require("confidence" not in record, f"{hypothesis_id} must not collapse assurance into scalar confidence")
        for field in ("title", "claim", "architecture_value", "falsifier"):
            require_nonempty_text(record.get(field), f"{hypothesis_id}.{field}")
        sources = record.get("source_ids")
        experiments = record.get("experiment_ids")
        obligations = record.get("formal_obligations")
        require(isinstance(sources, list) and bool(sources), f"{hypothesis_id} needs sources")
        require(isinstance(experiments, list) and bool(experiments), f"{hypothesis_id} needs experiments")
        require(isinstance(obligations, list) and bool(obligations), f"{hypothesis_id} needs obligations")
        require(set(sources) <= source_ids, f"{hypothesis_id} has an unknown source")
        require(set(experiments) <= experiment_ids, f"{hypothesis_id} has an unknown experiment")
        require(all(isinstance(item, str) and item for item in obligations), f"{hypothesis_id} has an invalid obligation")
    return identifiers, by_id


def validate_graph(
    data: dict[str, Any], source_ids: set[str], hypothesis_ids: set[str], experiment_ids: set[str]
) -> None:
    require(data.get("schema") == "zrm/frontier-knowledge-graph/v2", "unexpected graph schema")
    require(data.get("base_revision") == BASE_REVISION, "graph base revision mismatch")
    nodes, node_ids = unique_ids(data.get("nodes"), "graph.nodes", "")
    require(len(nodes) >= 20, "knowledge graph has too few synthesis nodes")
    for node in nodes:
        require_nonempty_text(node.get("type"), f"{node['id']}.type")
        require_nonempty_text(node.get("title"), f"{node['id']}.title")
    allowed_endpoints = source_ids | hypothesis_ids | experiment_ids | node_ids
    edges, edge_ids = unique_ids(data.get("edges"), "graph.edges", "KG-E")
    require(len(edges) >= 50, "knowledge graph has too few typed edges")
    require(len(edge_ids) == len(edges), "graph edge IDs must be unique")
    for edge in edges:
        edge_id = edge["id"]
        source = require_nonempty_text(edge.get("from"), f"{edge_id}.from")
        target = require_nonempty_text(edge.get("to"), f"{edge_id}.to")
        require(source in allowed_endpoints, f"{edge_id} has unknown source endpoint {source}")
        require(target in allowed_endpoints, f"{edge_id} has unknown target endpoint {target}")
        require(source != target, f"{edge_id} cannot be a self-edge")
        require_nonempty_text(edge.get("relation"), f"{edge_id}.relation")
        require_nonempty_text(edge.get("rationale"), f"{edge_id}.rationale")
    clusters, cluster_ids = unique_ids(data.get("clusters"), "graph.clusters", "KG-C")
    require(len(cluster_ids) == len(clusters), "cluster IDs must be unique")
    for cluster in clusters:
        members = cluster.get("members")
        require(isinstance(members, list) and bool(members), f"{cluster['id']} needs members")
        require(set(members) <= hypothesis_ids, f"{cluster['id']} has an unknown member")
    frontier = data.get("ranked_frontier")
    require(isinstance(frontier, list) and len(frontier) >= 10, "ranked frontier is too short")
    require(len(frontier) == len(set(frontier)), "ranked frontier must be unique")
    require(set(frontier) <= hypothesis_ids, "ranked frontier has an unknown hypothesis")


def validate_esso_observation(esso: dict[str, Any]) -> None:
    require(
        esso.get("schema") == "zrm/esso-observational-execution-record/v1",
        "unexpected ESSO observation schema",
    )
    require(esso.get("status") == "OBSERVED_PASS_NOT_REPLAYABLE", "ESSO status overclaims replayable evidence")
    require(esso.get("evidence_class") == "observational_external_execution", "ESSO evidence class mismatch")
    require(esso.get("replayable_from_repository") is False, "ESSO observation must be non-replayable")
    require(esso.get("promotion_eligible") is False, "ESSO observation cannot be promotion eligible")
    require(esso.get("esso_revision") == EXPECTED_ESSO_REVISION, "ESSO revision mismatch")
    require(esso.get("checker_schema") == "esso-zrm-semantic-check/v2", "ESSO checker schema mismatch")
    require(esso.get("executed_at") == "2026-07-14", "ESSO observation date mismatch")
    missing = esso.get("missing_required_receipt_fields")
    require(isinstance(missing, list) and set(missing) == EXPECTED_ESSO_MISSING_FIELDS, "ESSO missing-field disclosure mismatch")

    digest_pattern = re.compile(r"^sha256:[0-9a-f]{64}$")
    models = esso.get("models")
    require(isinstance(models, dict) and set(models) == EXPECTED_ESSO_MODELS, "ESSO model identities mismatch")
    for name, item in models.items():
        require(isinstance(item, dict) and set(item) == {"inductive", "ir_hash"}, f"ESSO model {name} fields mismatch")
        require(item.get("inductive") is True, f"ESSO model {name} was not observed inductive")
        require(isinstance(item.get("ir_hash"), str) and digest_pattern.fullmatch(item["ir_hash"]), f"ESSO model {name} hash is malformed")

    mutants = esso.get("mutants")
    require(isinstance(mutants, dict) and set(mutants) == EXPECTED_ESSO_MUTANTS, "ESSO mutant identities mismatch")
    require(all(isinstance(value, str) and digest_pattern.fullmatch(value) for value in mutants.values()), "ESSO mutant hashes are malformed")
    summary = esso.get("mutant_observation_summary")
    require(
        json_exact_equal(
            summary,
            {
                "reported_code": "InvNotInductive",
                "reported_counterexample_for_each": True,
                "observed_killed": 14,
                "independently_replayable": False,
                "total": 14,
            },
        ),
        "ESSO mutant observation summary mismatch",
    )
    for field in ("execution_notes", "non_claims"):
        values = esso.get(field)
        require(isinstance(values, list) and bool(values), f"ESSO {field} must be nonempty")
        require(all(isinstance(value, str) and value for value in values), f"ESSO {field} contains invalid text")


def validate_lean_observation(lean: dict[str, Any]) -> None:
    require(lean.get("schema") == "zrm/lean-frontier-evidence/v1", "unexpected Lean evidence schema")
    require(lean.get("executed_at") == "2026-07-14", "Lean evidence date mismatch")
    require(lean.get("package") == "formal/lean/arm_zrm_frontier_v2", "Lean package mismatch")
    require(lean.get("lean_release") == "v4.32.0", "Lean release mismatch")
    require(
        lean.get("lean_commit") == "8c9756bf44da6f8c4e9b3ac40779ab939732a31d",
        "Lean commit mismatch",
    )
    require(lean.get("status") == "PASS", "Lean evidence is not PASS")
    require(type(lean.get("lake_jobs")) is int and lean["lake_jobs"] == 7, "Lean job count mismatch")
    require(
        json_exact_equal(
            lean.get("modules"),
            [
                "ArmZrmFrontier.TotalCarrier",
                "ArmZrmFrontier.ExactCoverage",
                "ArmZrmFrontier.TranscriptSeparation",
                "ArmZrmFrontier.AccountingStrongAssociativity",
            ],
        ),
        "Lean module identities mismatch",
    )
    require(
        json_exact_equal(lean.get("source_scan"), {"sorry": 0, "admit": 0, "axiom": 0}),
        "Lean source-scan summary mismatch",
    )


def validate_research_kernel_summary(summary: dict[str, Any]) -> None:
    require(
        summary.get("schema") == "zrm/research-kernel-run-summary/v1",
        "unexpected Research Kernel summary schema",
    )
    require(
        summary.get("research_kernel_revision")
        == "d9cdfceaa396dd56acfacbd042b89ce633dbc173",
        "Research Kernel revision mismatch",
    )
    require(summary.get("mcp_python_package") == "1.28.1", "Research Kernel MCP package mismatch")
    require(summary.get("executed_at") == "2026-07-14", "Research Kernel date mismatch")
    require(
        json_exact_equal(summary.get("runs"), EXPECTED_RESEARCH_KERNEL_RUNS),
        "Research Kernel run identities or counts mismatch",
    )
    limitations = summary.get("observed_kernel_limitations")
    require(
        isinstance(limitations, list)
        and len(limitations) == 7
        and all(type(item) is str and bool(item) for item in limitations),
        "Research Kernel limitations mismatch",
    )
    require_nonempty_text(summary.get("handling"), "Research Kernel handling")


def validate_evidence() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from reference_models.deterministic_authenticated_batch_explorer import explore as batch_explore
    from reference_models.zrm_composition_frontier_v2_explorer import explore as composition_explore

    composition = load_json(PACKET / "evidence/composition-frontier-v2.json")
    batch = load_json(PACKET / "evidence/deterministic-authenticated-batch-v1.json")
    require(
        json_exact_equal(composition, composition_explore()),
        "composition evidence differs from executable explorer",
    )
    require(
        json_exact_equal(batch, batch_explore()),
        "batch evidence differs from executable explorer",
    )

    validate_esso_observation(
        load_json(PACKET / "evidence/esso-zrm-semantic-check-v2.json")
    )

    lean = load_json(PACKET / "evidence/lean-frontier-v2.json")
    validate_lean_observation(lean)
    validate_research_kernel_summary(
        load_json(PACKET / "evidence/research-kernel-runs-v1.json")
    )
    lean_root = ROOT / "formal/lean/arm_zrm_frontier_v2"
    forbidden = re.compile(r"\b(sorry|admit|axiom)\b")
    violations: list[str] = []
    for path in sorted(lean_root.rglob("*.lean")):
        if forbidden.search(path.read_text(encoding="utf-8")):
            violations.append(path.relative_to(ROOT).as_posix())
    require(not violations, f"Lean source contains forbidden declarations: {violations}")


def validate_public_security_scope() -> None:
    paths: list[Path] = []
    for path in PACKET.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".md", ".py"}:
            paths.append(path)
    for relative in EXPLICIT_PACKET_FILES:
        path = ROOT / relative
        if path.suffix == ".py" and relative.startswith("reference_models/"):
            paths.append(path)
    findings: list[str] = []
    for path in sorted(set(paths)):
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_PUBLIC_DETAIL:
            if forbidden in text:
                findings.append(f"{path.relative_to(ROOT)}:{forbidden}")
    require(not findings, f"public packet contains withheld ARM detail: {findings}")


def iter_visible_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part.startswith(".") or part == "__pycache__" for part in relative_parts):
            continue
        yield path


def expected_manifest_paths() -> list[str]:
    paths = {
        path.relative_to(ROOT).as_posix()
        for path in iter_visible_files(PACKET)
        if path != MANIFEST
    }
    lean_root = ROOT / "formal/lean/arm_zrm_frontier_v2"
    paths.update(path.relative_to(ROOT).as_posix() for path in iter_visible_files(lean_root))
    paths.update(EXPLICIT_PACKET_FILES)
    return sorted(paths, key=lambda value: value.encode("utf-8"))


def file_record(relative: str) -> dict[str, object]:
    path = ROOT / relative
    require(path.is_file(), f"manifest-scoped file is missing: {relative}")
    payload = path.read_bytes()
    return {
        "path": relative,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def validate_manifest(data: dict[str, Any]) -> None:
    require(
        set(data)
        == {
            "schema",
            "base_revision",
            "digest_algorithm",
            "path_order",
            "manifest_self_excluded",
            "file_count",
            "files",
            "non_claims",
        },
        "research manifest top-level fields mismatch",
    )
    require(data.get("schema") == "zrm/frontier-research-manifest/v1", "unexpected research manifest schema")
    require(data.get("base_revision") == BASE_REVISION, "research manifest base revision mismatch")
    require(data.get("digest_algorithm") == "SHA-256", "research manifest digest algorithm mismatch")
    require(
        data.get("path_order") == "UTF-8 bytewise lexicographic",
        "research manifest path order mismatch",
    )
    require(data.get("manifest_self_excluded") is True, "research manifest must exclude itself")
    records = data.get("files")
    require(isinstance(records, list), "research manifest files must be a list")
    digest_pattern = re.compile(r"^[0-9a-f]{64}$")
    for index, record in enumerate(records):
        require(isinstance(record, dict), f"manifest.files[{index}] must be an object")
        require(
            set(record) == {"path", "bytes", "sha256"},
            f"manifest.files[{index}] fields mismatch",
        )
        require(
            type(record.get("bytes")) is int and record["bytes"] >= 0,
            f"manifest.files[{index}].bytes must be a nonnegative exact integer",
        )
        require(
            isinstance(record.get("sha256"), str)
            and bool(digest_pattern.fullmatch(record["sha256"])),
            f"manifest.files[{index}].sha256 is malformed",
        )
    expected_paths = expected_manifest_paths()
    actual_paths = [safe_relative_path(record.get("path"), "manifest.files.path") for record in records if isinstance(record, dict)]
    require(len(actual_paths) == len(records), "research manifest has a non-object record")
    require(actual_paths == expected_paths, "research manifest file scope or order mismatch")
    expected_records = [file_record(relative) for relative in expected_paths]
    require(
        json_exact_equal(records, expected_records),
        "research manifest bytes or digests are stale",
    )
    require(
        type(data.get("file_count")) is int
        and data["file_count"] == len(records),
        "research manifest file count mismatch",
    )
    require(
        json_exact_equal(data.get("non_claims"), EXPECTED_MANIFEST_NON_CLAIMS),
        "research manifest nonclaims mismatch",
    )


def validate_packet(root: Path = ROOT) -> dict[str, int]:
    require(root.resolve() == ROOT.resolve(), "alternate repository roots are not supported")
    sources = load_json(PACKET / "source_ledger.json")
    experiments = load_json(PACKET / "experiments.json")
    hypotheses = load_json(PACKET / "hypotheses.json")
    graph = load_json(PACKET / "knowledge_graph.json")
    source_ids = validate_sources(sources)
    experiment_ids, _ = validate_experiments(experiments)
    hypothesis_ids, _ = validate_hypotheses(hypotheses, source_ids, experiment_ids)
    validate_graph(graph, source_ids, hypothesis_ids, experiment_ids)
    validate_evidence()
    validate_public_security_scope()
    validate_manifest(load_json(MANIFEST))
    return {
        "sources": len(source_ids),
        "hypotheses": len(hypothesis_ids),
        "experiments": len(experiment_ids),
        "graph_nodes": len(graph["nodes"]),
        "graph_edges": len(graph["edges"]),
    }


def main() -> int:
    try:
        counts = validate_packet()
    except FrontierPacketError as error:
        print(f"ZRM frontier research check failed: {error}", file=sys.stderr)
        return 1
    print(
        "ZRM frontier research check passed: "
        + ", ".join(f"{name}={value}" for name, value in counts.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
