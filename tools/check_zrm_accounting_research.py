#!/usr/bin/env python3
"""Fail-closed validator for the ZRM accounting aggregate research packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PACKET = ROOT / "research/zrm_accounting_aggregate_v1"
MANIFEST = PACKET / "manifest.json"
BASE_REVISION = "efcaa2ba80944fc455ef9c326cd878821d23022b"
RUN_ID = "zrm_accounting_aggregate_v1_20260714"
ALLOWED_HYPOTHESIS_STATUSES = {
    "refuted",
    "source_supported",
    "supported_bounded",
    "under_test",
    "alternative",
}
EXECUTED_STATUS_PREFIXES = ("passed_",)
PACKET_FILES = {
    "README.md",
    "breakthroughs.md",
    "source_ledger.json",
    "hypotheses.json",
    "knowledge_graph.json",
    "experiments.json",
    "research_kernel_receipt.json",
    "research_kernel_plan.json",
    "morph_reformulations.json",
    "esso_campaign.json",
    "evidence/python-model.json",
    "evidence/lean.json",
    "evidence/vectors.json",
    "evidence/packet-check.json",
}
EXPLICIT_FILES = {
    ".github/workflows/ci.yml",
    "PACKAGE_MANIFEST.json",
    "README.md",
    "rfcs/README.md",
    "rfcs/RFC-0004-recursive-accounting-aggregate-profile.md",
    "reference_models/accounting_aggregate_v1.py",
    "reference_models/accounting_aggregate_v1_explorer.py",
    "reference_models/tests/test_accounting_aggregate_v1.py",
    "vectors/accounting_aggregate_v1.json",
    "vectors/independent_python/replay_accounting_aggregate_v1.py",
    "formal/lean/zrm_accounting_aggregate_v1/.gitignore",
    "formal/lean/zrm_accounting_aggregate_v1/README.md",
    "formal/lean/zrm_accounting_aggregate_v1/ZrmAccountingAggregateV1.lean",
    "formal/lean/zrm_accounting_aggregate_v1/ZrmAccountingAggregateV1/AccountingFoldTree.lean",
    "formal/lean/zrm_accounting_aggregate_v1/ZrmAccountingAggregateV1/CapacityBound.lean",
    "formal/lean/zrm_accounting_aggregate_v1/ZrmAccountingAggregateV1/FourColumnConservation.lean",
    "formal/lean/zrm_accounting_aggregate_v1/ZrmAccountingAggregateV1/TotalOverflowCarrier.lean",
    "formal/lean/zrm_accounting_aggregate_v1/lake-manifest.json",
    "formal/lean/zrm_accounting_aggregate_v1/lakefile.toml",
    "formal/lean/zrm_accounting_aggregate_v1/lean-toolchain",
    "formal/lean/arm_zrm_frontier_v2/.gitignore",
    "formal/lean/arm_zrm_frontier_v2/README.md",
    "formal/lean/arm_zrm_frontier_v2/ArmZrmFrontier.lean",
    "formal/lean/arm_zrm_frontier_v2/ArmZrmFrontier/AccountingStrongAssociativity.lean",
    "formal/lean/arm_zrm_frontier_v2/ArmZrmFrontier/ExactCoverage.lean",
    "formal/lean/arm_zrm_frontier_v2/ArmZrmFrontier/TotalCarrier.lean",
    "formal/lean/arm_zrm_frontier_v2/ArmZrmFrontier/TranscriptSeparation.lean",
    "formal/lean/arm_zrm_frontier_v2/lake-manifest.json",
    "formal/lean/arm_zrm_frontier_v2/lakefile.toml",
    "formal/lean/arm_zrm_frontier_v2/lean-toolchain",
    "tools/check_zrm_accounting_research.py",
    "tools/tests/test_zrm_accounting_research.py",
}
EXPECTED_NON_CLAIMS = [
    "The manifest authenticates packet and implementation-slice bytes only; it does not approve RFC-0004 or promote a ZRM protocol claim.",
    "Mutable external sources, Research Kernel state, and unavailable private tool repositories are outside this digest set.",
]
LEAN_PACKAGE_ROOTS = (
    "formal/lean/arm_zrm_frontier_v2",
    "formal/lean/zrm_accounting_aggregate_v1",
)
LEAN_PLACEHOLDER_RE = re.compile(r"\b(?:admit|axiom|sorry)\b")


class AccountingResearchError(ValueError):
    """Raised when a packet invariant fails closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AccountingResearchError(message)


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonstandard JSON constant {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


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
        raise AccountingResearchError(f"noncanonical JSON value: {error}") from error


def json_exact_equal(left: object, right: object) -> bool:
    return canonical_json_bytes(left) == canonical_json_bytes(right)


def lean_placeholder_tokens(source: str) -> list[str]:
    """Return proof-placeholder tokens, including any hidden in comments."""

    return [match.group(0) for match in LEAN_PLACEHOLDER_RE.finditer(source)]


def lean_package_files() -> list[str]:
    """Discover every non-build file that can influence the two Lean packages."""

    result: list[str] = []
    for root_relative in LEAN_PACKAGE_ROOTS:
        root = ROOT / root_relative
        require(root.is_dir() and not root.is_symlink(), f"Lean package root is not a regular directory: {root_relative}")
        for candidate in sorted(root.rglob("*")):
            package_relative = candidate.relative_to(root)
            if ".lake" in package_relative.parts:
                continue
            require(not candidate.is_symlink(), f"Lean package contains a symlink: {candidate.relative_to(ROOT)}")
            if candidate.is_dir():
                continue
            require(candidate.is_file(), f"Lean package contains a non-regular entry: {candidate.relative_to(ROOT)}")
            result.append(candidate.relative_to(ROOT).as_posix())
    require(result, "Lean package discovery found no files")
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, ValueError) as error:
        relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        raise AccountingResearchError(f"cannot load {relative}: {error}") from error
    require(type(value) is dict, f"{path.name} root must be an object")
    return value


def text(value: object, field: str) -> str:
    require(type(value) is str and bool(value.strip()), f"{field} must be nonempty text")
    return value


def exact_int(value: object, field: str, minimum: int = 0) -> int:
    require(type(value) is int and value >= minimum, f"{field} must be an exact integer >= {minimum}")
    return value


def safe_path(value: object, field: str) -> str:
    path = text(value, field)
    pure = PurePosixPath(path)
    require(not pure.is_absolute(), f"{field} must be relative")
    require("." not in pure.parts and ".." not in pure.parts, f"{field} is not normalized")
    require("\\" not in path and "\x00" not in path, f"{field} contains unsafe bytes")
    return path


def records_with_ids(value: object, field: str) -> tuple[list[dict[str, Any]], set[str]]:
    require(type(value) is list, f"{field} must be a list")
    records: list[dict[str, Any]] = []
    identifiers: list[str] = []
    for index, item in enumerate(value):
        require(type(item) is dict, f"{field}[{index}] must be an object")
        identifier = text(item.get("id"), f"{field}[{index}].id")
        records.append(item)
        identifiers.append(identifier)
    require(len(identifiers) == len(set(identifiers)), f"{field} IDs must be unique")
    return records, set(identifiers)


def validate_sources(data: dict[str, Any]) -> set[str]:
    require(data.get("schema") == "zrm/accounting-aggregate-source-ledger/v1", "source schema mismatch")
    require(data.get("run_id") == RUN_ID, "source run mismatch")
    require(data.get("base_revision") == BASE_REVISION, "source base revision mismatch")
    records, identifiers = records_with_ids(data.get("sources"), "sources")
    require(len(records) >= 20, "source ledger is unexpectedly shallow")
    for record in records:
        identifier = record["id"]
        require(identifier.startswith("AAS-"), f"bad source ID {identifier}")
        text(record.get("kind"), f"{identifier}.kind")
        text(record.get("title"), f"{identifier}.title")
        require(text(record.get("uri"), f"{identifier}.uri").startswith("https://"), f"{identifier}.uri must use HTTPS")
        text(record.get("revision"), f"{identifier}.revision")
        require(record.get("primary") is True, f"{identifier} must be primary")
        supports = record.get("supports")
        require(type(supports) is list and supports, f"{identifier}.supports must be nonempty")
        for index, item in enumerate(supports):
            text(item, f"{identifier}.supports[{index}]")
    return identifiers


def validate_experiments(data: dict[str, Any]) -> tuple[set[str], dict[str, dict[str, Any]]]:
    require(data.get("schema") == "zrm/accounting-aggregate-experiments/v1", "experiment schema mismatch")
    require(data.get("run_id") == RUN_ID, "experiment run mismatch")
    require(data.get("base_revision") == BASE_REVISION, "experiment base revision mismatch")
    records, identifiers = records_with_ids(data.get("experiments"), "experiments")
    require(len(records) == 12, "expected exactly twelve experiments")
    by_id = {record["id"]: record for record in records}
    for record in records:
        identifier = record["id"]
        require(identifier.startswith("AAE-"), f"bad experiment ID {identifier}")
        text(record.get("title"), f"{identifier}.title")
        status = text(record.get("status"), f"{identifier}.status")
        text(record.get("runner"), f"{identifier}.runner")
        text(record.get("result"), f"{identifier}.result")
        artifacts = record.get("artifacts")
        require(type(artifacts) is list and artifacts, f"{identifier}.artifacts must be nonempty")
        for index, item in enumerate(artifacts):
            relative = safe_path(item, f"{identifier}.artifacts[{index}]")
            if status.startswith(EXECUTED_STATUS_PREFIXES):
                require((ROOT / relative).exists(), f"{identifier} executed artifact missing: {relative}")
    require(by_id["AAE-08"]["status"] == "specified_not_executed", "ESSO must remain explicitly unexecuted")
    return identifiers, by_id


def validate_hypotheses(data: dict[str, Any], source_ids: set[str], experiment_ids: set[str]) -> set[str]:
    require(data.get("schema") == "zrm/accounting-aggregate-hypotheses/v1", "hypothesis schema mismatch")
    require(data.get("run_id") == RUN_ID, "hypothesis run mismatch")
    require(data.get("base_revision") == BASE_REVISION, "hypothesis base revision mismatch")
    records, identifiers = records_with_ids(data.get("hypotheses"), "hypotheses")
    require(len(records) == 20, "expected exactly twenty hypotheses")
    ranks: list[int] = []
    refuted = 0
    for record in records:
        identifier = record["id"]
        status = text(record.get("status"), f"{identifier}.status")
        require(status in ALLOWED_HYPOTHESIS_STATUSES, f"{identifier} has unsupported status")
        if status == "refuted":
            refuted += 1
            text(record.get("counterexample"), f"{identifier}.counterexample")
        text(record.get("claim"), f"{identifier}.claim")
        ranks.append(exact_int(record.get("rank"), f"{identifier}.rank", 1))
        falsifiers = record.get("falsifiers")
        require(type(falsifiers) is list and falsifiers, f"{identifier}.falsifiers must be nonempty")
        for index, item in enumerate(falsifiers):
            text(item, f"{identifier}.falsifiers[{index}]")
        sources = record.get("source_ids")
        experiments = record.get("experiment_ids")
        require(type(sources) is list and sources, f"{identifier}.source_ids must be nonempty")
        require(type(experiments) is list and experiments, f"{identifier}.experiment_ids must be nonempty")
        require(set(sources) <= source_ids, f"{identifier} references an unknown source")
        require(set(experiments) <= experiment_ids, f"{identifier} references an unknown experiment")
    require(len(ranks) == len(set(ranks)), "hypothesis ranks must be unique")
    require(refuted == 4, "expected exactly four refuted baseline hypotheses")
    return identifiers


def validate_graph(data: dict[str, Any], source_ids: set[str], hypothesis_ids: set[str], experiment_ids: set[str]) -> dict[str, int]:
    require(data.get("schema") == "zrm/accounting-aggregate-knowledge-graph/v1", "graph schema mismatch")
    require(data.get("run_id") == RUN_ID, "graph run mismatch")
    node_types = data.get("node_types")
    edge_types = data.get("edge_types")
    require(type(node_types) is list and len(node_types) >= 6, "graph node types are incomplete")
    require(type(edge_types) is list and len(edge_types) >= 8, "graph edge types are incomplete")
    nodes, node_ids = records_with_ids(data.get("nodes"), "nodes")
    require(len(nodes) >= 70, "knowledge graph is unexpectedly shallow")
    for node in nodes:
        require(node.get("type") in node_types, f"node {node['id']} has unknown type")
        text(node.get("label"), f"node {node['id']}.label")
    require(source_ids <= node_ids, "graph omits a source node")
    require(hypothesis_ids <= node_ids, "graph omits a hypothesis node")
    require(experiment_ids <= node_ids, "graph omits an experiment node")
    edges = data.get("edges")
    require(type(edges) is list and len(edges) >= 80, "knowledge graph edge set is unexpectedly shallow")
    seen: set[tuple[str, str, str]] = set()
    for index, edge in enumerate(edges):
        require(type(edge) is dict, f"edges[{index}] must be an object")
        source = text(edge.get("from"), f"edges[{index}].from")
        target = text(edge.get("to"), f"edges[{index}].to")
        kind = text(edge.get("type"), f"edges[{index}].type")
        require(source in node_ids, f"edge has unknown source endpoint {source}")
        require(target in node_ids, f"edge has unknown target endpoint {target}")
        require(kind in edge_types, f"edge has unknown type {kind}")
        key = (source, target, kind)
        require(key not in seen, f"duplicate graph edge {key}")
        seen.add(key)
    return {"nodes": len(nodes), "edges": len(edges)}


def validate_morph(data: dict[str, Any]) -> None:
    require(data.get("schema") == "zrm/accounting-aggregate-morph-reformulations/v1", "Morph schema mismatch")
    require(data.get("run_id") == RUN_ID, "Morph run mismatch")
    require(data.get("status") == "candidate_search_only", "Morph outputs must remain candidates")
    records, _ = records_with_ids(data.get("reformulations"), "reformulations")
    require(len(records) == 24, "expected exactly twenty-four Morph candidates")
    for record in records:
        text(record.get("mode"), f"Morph {record['id']}.mode")
        text(record.get("relation"), f"Morph {record['id']}.relation")
        text(record.get("content"), f"Morph {record['id']}.content")


def validate_esso(data: dict[str, Any]) -> None:
    require(data.get("schema") == "zrm/accounting-aggregate-esso-campaign/v1", "ESSO schema mismatch")
    require(data.get("status") == "specified_not_executed", "ESSO status overclaims execution")
    require(data.get("esso_revision") == "db8a3f8a782a508ada5005a2cf177f25c58f451d", "ESSO revision mismatch")
    mutants, mutant_ids = records_with_ids(data.get("mutants"), "ESSO mutants")
    require(len(mutants) >= 16, "ESSO mutant plan is unexpectedly shallow")
    require(len(mutant_ids) == len(mutants), "ESSO mutant IDs must be unique")
    required = data.get("required_replay_receipt")
    require(type(required) is list and len(required) >= 7, "ESSO replay receipt is incomplete")


def hypothesis_status_map(data: dict[str, Any]) -> dict[str, str]:
    """Return the exact validated packet status for each hypothesis."""

    records = data.get("hypotheses")
    require(type(records) is list, "hypotheses must be a list")
    result: dict[str, str] = {}
    for index, record in enumerate(records):
        require(type(record) is dict, f"hypotheses[{index}] must be an object")
        identifier = text(record.get("id"), f"hypotheses[{index}].id")
        status = text(record.get("status"), f"{identifier}.status")
        require(identifier not in result, "hypothesis IDs must be unique")
        result[identifier] = status
    return result


def validate_receipt(data: dict[str, Any], hypotheses: dict[str, Any]) -> None:
    require(data.get("schema") == "zrm/accounting-aggregate-research-kernel-receipt/v1", "Research Kernel receipt schema mismatch")
    require(data.get("run_id") == RUN_ID, "Research Kernel receipt run mismatch")
    require(data.get("base_revision") == BASE_REVISION, "Research Kernel receipt base revision mismatch")
    require(data.get("kernel_revision") == "d9cdfceaa396dd56acfacbd042b89ce633dbc173", "Research Kernel revision mismatch")
    first = data.get("first_pass")
    second = data.get("evidence_pass")
    require(type(first) is dict and type(second) is dict, "Research Kernel passes must be objects")
    require(exact_int(first.get("mcp_calls"), "first_pass.mcp_calls") == 78, "first-pass call count mismatch")
    require(exact_int(first.get("atoms"), "first_pass.atoms") == 82, "first-pass atom count mismatch")
    require(exact_int(first.get("edges"), "first_pass.edges") == 65, "first-pass edge count mismatch")
    require(exact_int(first.get("actual_counterexamples"), "first_pass.actual_counterexamples") == 4, "counterexample count mismatch")
    promoted = second.get("promoted_claim_ids")
    require(type(promoted) is list and len(promoted) >= 6, "evidence pass promoted too few bounded claims")
    require(len(promoted) == len(set(promoted)), "promoted claim IDs must be unique")
    unpromoted = second.get("deliberately_unpromoted_claim_ids")
    require(type(unpromoted) is list and unpromoted, "receipt must record deliberately unpromoted claims")
    require(len(unpromoted) == len(set(unpromoted)), "unpromoted claim IDs must be unique")
    refuted = first.get("refuted_claim_ids")
    require(type(refuted) is list and refuted, "receipt must record refuted claims")
    require(len(refuted) == len(set(refuted)), "refuted claim IDs must be unique")
    status_by_id = hypothesis_status_map(hypotheses)
    require(set(promoted) <= set(status_by_id), "receipt promotes an unknown hypothesis")
    require(set(unpromoted) <= set(status_by_id), "receipt leaves an unknown hypothesis unpromoted")
    require(set(refuted) <= set(status_by_id), "receipt refutes an unknown hypothesis")
    expected_promoted = {
        identifier
        for identifier, status in status_by_id.items()
        if status == "supported_bounded"
    }
    expected_refuted = {
        identifier for identifier, status in status_by_id.items() if status == "refuted"
    }
    expected_unpromoted = set(status_by_id) - expected_promoted - expected_refuted
    require(set(promoted) == expected_promoted, "receipt promotion partition disagrees with hypothesis statuses")
    require(set(refuted) == expected_refuted, "receipt refutation partition disagrees with hypothesis statuses")
    require(set(unpromoted) == expected_unpromoted, "receipt unpromoted partition disagrees with hypothesis statuses")
    require(
        not (set(promoted) & set(unpromoted) or set(promoted) & set(refuted) or set(unpromoted) & set(refuted)),
        "receipt claim partitions overlap",
    )
    limitations = data.get("limitations")
    require(type(limitations) is list and len(limitations) >= 4, "Research Kernel limitations are incomplete")


def validate_evidence(
    python_evidence: dict[str, Any],
    lean_evidence: dict[str, Any],
    vector_evidence: dict[str, Any],
    packet_evidence: dict[str, Any],
    graph_counts: dict[str, int],
) -> None:
    """Validate the exact bounded observations used by executed experiments."""

    for label, data, schema in (
        ("Python", python_evidence, "zrm/accounting-aggregate-python-evidence/v1"),
        ("Lean", lean_evidence, "zrm/accounting-aggregate-lean-evidence/v1"),
        ("vector", vector_evidence, "zrm/accounting-aggregate-vector-evidence/v1"),
        ("packet", packet_evidence, "zrm/accounting-aggregate-packet-check-evidence/v1"),
    ):
        require(data.get("schema") == schema, f"{label} evidence schema mismatch")
        require(data.get("base_revision") == BASE_REVISION, f"{label} evidence base revision mismatch")
        commands = data.get("commands")
        if label == "Lean":
            require(type(data.get("replay")) is dict, "Lean replay evidence is missing")
        else:
            require(type(commands) is list and commands, f"{label} evidence commands must be nonempty")
        require(type(data.get("nonclaims")) is list and data["nonclaims"], f"{label} evidence nonclaims must be nonempty")

    python_results = python_evidence.get("results")
    require(type(python_results) is dict, "Python evidence results must be an object")
    require(exact_int(python_results.get("focused_tests_passed"), "Python focused tests") == 34, "focused accounting test count mismatch")
    require(exact_int(python_results.get("focused_tests_failed"), "Python focused failures") == 0, "focused accounting tests did not pass")
    require(exact_int(python_results.get("full_reference_tests_passed"), "Python full tests") == 122, "full reference test count mismatch")
    require(exact_int(python_results.get("full_reference_tests_failed"), "Python full failures") == 0, "full reference tests did not pass")
    require(exact_int(python_results.get("monotone_tree_evaluations"), "tree evaluations") == 32805, "tree exploration count mismatch")
    require(exact_int(python_results.get("monotone_tree_disagreements"), "tree disagreements") == 0, "tree exploration found a disagreement")

    lean_results = lean_evidence.get("results")
    require(type(lean_results) is dict, "Lean evidence results must be an object")
    require(exact_int(lean_results.get("dependency_lake_jobs"), "Lean dependency jobs") == 7, "Lean dependency job count mismatch")
    require(exact_int(lean_results.get("lake_jobs"), "Lean lake jobs") == 10, "Lean job count mismatch")
    require(lean_results.get("build_passed") is True, "Lean evidence does not record a passing build")
    require(exact_int(lean_results.get("kernel_checks_passed"), "Lean kernel checks") == 2, "Lean kernel check count mismatch")
    require(
        lean_results.get("kernel_checked_modules") == ["ArmZrmFrontier", "ZrmAccountingAggregateV1"],
        "Lean kernel-checked module list mismatch",
    )
    placeholder_hits: list[str] = []
    for relative in lean_package_files():
        if not relative.endswith(".lean"):
            continue
        try:
            source = (ROOT / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise AccountingResearchError(f"cannot scan Lean source {relative}: {error}") from error
        placeholder_hits.extend(f"{relative}:{token}" for token in lean_placeholder_tokens(source))
    require(not placeholder_hits, f"Lean source contains proof placeholders: {placeholder_hits}")
    require(exact_int(lean_results.get("source_scan_sorry_axiom_admit_hits"), "Lean source placeholder hits") == 0, "Lean source contains a forbidden placeholder")

    vector_results = vector_evidence.get("results")
    require(type(vector_results) is dict, "vector evidence results must be an object")
    require(vector_results.get("replay_passed") is True, "vector replay did not pass")
    require(exact_int(vector_results.get("binary_artifacts"), "vector artifacts") == 16, "vector artifact count mismatch")
    require(exact_int(vector_results.get("strict_untrusted_negatives_rejected"), "vector rejected negatives") == 9, "strict vector negative count mismatch")
    require(
        vector_results.get("strict_untrusted_negatives_rejected")
        == vector_results.get("strict_untrusted_negatives_total"),
        "not every strict vector negative rejected",
    )

    packet_results = packet_evidence.get("results")
    require(type(packet_results) is dict, "packet evidence results must be an object")
    require(packet_results.get("packet_check_passed") is True, "packet evidence does not record a pass")
    require(exact_int(packet_results.get("checker_tests_passed"), "packet checker tests") == 18, "packet checker test count mismatch")
    require(exact_int(packet_results.get("mutation_tests_failed"), "packet mutation failures") == 0, "packet mutation test failed")
    require(exact_int(packet_results.get("sources"), "packet sources") == 22, "packet evidence source count mismatch")
    require(exact_int(packet_results.get("hypotheses"), "packet hypotheses") == 20, "packet evidence hypothesis count mismatch")
    require(exact_int(packet_results.get("experiments"), "packet experiments") == 12, "packet evidence experiment count mismatch")
    require(exact_int(packet_results.get("knowledge_graph_nodes"), "packet graph nodes") == graph_counts["nodes"], "packet evidence graph-node count mismatch")
    require(exact_int(packet_results.get("knowledge_graph_edges"), "packet graph edges") == graph_counts["edges"], "packet evidence graph-edge count mismatch")
    require(exact_int(packet_results.get("morph_candidates"), "packet Morph candidates") == 24, "packet evidence Morph count mismatch")


def expected_manifest_paths() -> list[str]:
    paths = {f"research/zrm_accounting_aggregate_v1/{path}" for path in PACKET_FILES}
    paths.update(EXPLICIT_FILES)
    paths.update(lean_package_files())
    vector_manifest_path = ROOT / "vectors/accounting_aggregate_v1.json"
    if vector_manifest_path.is_file():
        vector_manifest = load_json(vector_manifest_path)
        artifacts = vector_manifest.get("artifacts")
        require(type(artifacts) is dict, "vector artifacts must be an object")
        for name in artifacts:
            relative_name = safe_path(name, f"vector artifact {name}")
            require("/" not in relative_name, "vector artifact names must be basenames")
            paths.add(f"vectors/{relative_name}")
    return sorted(paths)


def file_record(relative: str) -> dict[str, object]:
    payload = (ROOT / relative).read_bytes()
    return {
        "path": relative,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def build_manifest() -> dict[str, object]:
    paths = expected_manifest_paths()
    for relative in paths:
        require((ROOT / relative).is_file(), f"manifest input missing: {relative}")
    return {
        "schema": "zrm/accounting-aggregate-research-manifest/v1",
        "base_revision": BASE_REVISION,
        "files": [file_record(relative) for relative in paths],
        "non_claims": EXPECTED_NON_CLAIMS,
    }


def write_manifest() -> None:
    data = build_manifest()
    MANIFEST.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_manifest(data: dict[str, Any]) -> None:
    require(
        set(data) == {"schema", "base_revision", "files", "non_claims"},
        "manifest has unexpected top-level fields",
    )
    require(data.get("schema") == "zrm/accounting-aggregate-research-manifest/v1", "manifest schema mismatch")
    require(data.get("base_revision") == BASE_REVISION, "manifest base revision mismatch")
    require(json_exact_equal(data.get("non_claims"), EXPECTED_NON_CLAIMS), "manifest nonclaims mismatch")
    expected = build_manifest()
    require(json_exact_equal(data, expected), "manifest bytes or digests are stale")


def validate_packet(*, check_manifest: bool = True) -> dict[str, int]:
    missing = [path for path in sorted(PACKET_FILES) if not (PACKET / path).is_file()]
    require(not missing, f"required packet files missing: {missing}")
    source_ids = validate_sources(load_json(PACKET / "source_ledger.json"))
    experiment_ids, experiments_by_id = validate_experiments(
        load_json(PACKET / "experiments.json")
    )
    hypotheses = load_json(PACKET / "hypotheses.json")
    hypothesis_ids = validate_hypotheses(hypotheses, source_ids, experiment_ids)
    graph_counts = validate_graph(
        load_json(PACKET / "knowledge_graph.json"),
        source_ids,
        hypothesis_ids,
        experiment_ids,
    )
    validate_morph(load_json(PACKET / "morph_reformulations.json"))
    validate_esso(load_json(PACKET / "esso_campaign.json"))
    validate_receipt(load_json(PACKET / "research_kernel_receipt.json"), hypotheses)
    validate_evidence(
        load_json(PACKET / "evidence/python-model.json"),
        load_json(PACKET / "evidence/lean.json"),
        load_json(PACKET / "evidence/vectors.json"),
        load_json(PACKET / "evidence/packet-check.json"),
        graph_counts,
    )
    require("34 focused tests" in experiments_by_id["AAE-01"]["result"], "AAE-01 disagrees with Python evidence")
    require("10 jobs" in experiments_by_id["AAE-02"]["result"], "AAE-02 disagrees with Lean evidence")
    require("9/9" in experiments_by_id["AAE-03"]["result"], "AAE-03 disagrees with vector evidence")
    require("122 reference-model tests" in experiments_by_id["AAE-04"]["result"], "AAE-04 disagrees with Python evidence")
    require("18" in experiments_by_id["AAE-07"]["result"], "AAE-07 disagrees with packet-check evidence")
    plan = load_json(PACKET / "research_kernel_plan.json")
    require(plan.get("schema") == "zrm/accounting-aggregate-research-kernel-plan/v1", "Research Kernel plan schema mismatch")
    if check_manifest:
        validate_manifest(load_json(MANIFEST))
    return {
        "sources": len(source_ids),
        "hypotheses": len(hypothesis_ids),
        "experiments": len(experiment_ids),
        "graph_nodes": graph_counts["nodes"],
        "graph_edges": graph_counts["edges"],
        "morph_candidates": 24,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.write_manifest:
            validate_packet(check_manifest=False)
            write_manifest()
        counts = validate_packet()
    except AccountingResearchError as error:
        print(f"accounting research packet rejected: {error}", file=sys.stderr)
        return 1
    print(
        "accounting research packet passed: "
        + ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
