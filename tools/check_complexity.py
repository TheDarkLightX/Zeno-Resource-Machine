"""Enforce complexity findings, approvals, and deterministic report output."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

if __package__:
    from .rust_complexity import (
        METRIC_POLICIES,
        UNMEASURED_BUDGETS,
        ComplexityError,
        Finding,
        FunctionMetric,
        PublicTraitMetric,
        SourceAnalysis,
        _validate_relative_path,
        analyze_rust_source,
        classify_findings,
    )
else:
    from rust_complexity import (
        METRIC_POLICIES,
        UNMEASURED_BUDGETS,
        ComplexityError,
        Finding,
        FunctionMetric,
        PublicTraitMetric,
        SourceAnalysis,
        _validate_relative_path,
        analyze_rust_source,
        classify_findings,
    )


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXCEPTIONS_PATH = "tools/complexity_exceptions.json"
MAX_SOURCE_FILE_BYTES = 1_048_576
REPORT_SCHEMA = "zrm/complexity-report/v1"
EXCEPTION_SCHEMA = "zrm/complexity-exceptions/v1"
REVISION_PATTERN = re.compile(r"[0-9a-f]{40}")
FINDING_ID_PATTERN = re.compile(r"zrm-complexity:[0-9a-f]{64}")


@dataclass(frozen=True)
class ExceptionEvaluation:
    """Exact approved and still-unapproved review-trigger finding IDs."""

    approved_finding_ids: tuple[str, ...]
    unapproved_finding_ids: tuple[str, ...]


def _require_nonempty_string(value: object, field: str) -> str:
    """Return a nonempty string field or reject the registry."""

    if not isinstance(value, str) or not value.strip():
        raise ComplexityError(f"exception field {field} must be a nonempty string")
    return value


def _require_string_list(value: object, field: str) -> tuple[str, ...]:
    """Return a nonempty tuple of nonempty strings."""

    if not isinstance(value, list) or not value:
        raise ComplexityError(f"exception field {field} must be a nonempty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ComplexityError(f"exception field {field} contains an empty or non-string value")
    return tuple(value)


def validate_exception_registry(
    registry: object, findings: Sequence[Finding]
) -> ExceptionEvaluation:
    """Validate exact approved exception coverage for review-trigger findings."""

    if not isinstance(registry, dict) or set(registry) != {"schema", "exceptions"}:
        raise ComplexityError("exception registry must contain exactly schema and exceptions")
    if registry.get("schema") != EXCEPTION_SCHEMA:
        raise ComplexityError("unexpected complexity exception schema")
    exceptions = registry.get("exceptions")
    if not isinstance(exceptions, list):
        raise ComplexityError("complexity exceptions must be a list")
    review_ids = {
        finding.finding_id for finding in findings if finding.level == "review_required"
    }
    approved: set[str] = set()
    required_fields = {
        "finding_id",
        "status",
        "reviewer",
        "reviewed_revision",
        "rationale",
        "decomposition_alternatives",
        "focused_tests",
    }
    for exception in exceptions:
        if not isinstance(exception, dict) or set(exception) != required_fields:
            raise ComplexityError("each complexity exception must contain the exact v1 fields")
        finding_id = _require_nonempty_string(exception.get("finding_id"), "finding_id")
        if FINDING_ID_PATTERN.fullmatch(finding_id) is None:
            raise ComplexityError(f"invalid complexity finding ID: {finding_id!r}")
        if finding_id in approved:
            raise ComplexityError(f"duplicate complexity exception: {finding_id}")
        if finding_id not in review_ids:
            raise ComplexityError(f"stale complexity exception: {finding_id}")
        if exception.get("status") != "approved":
            raise ComplexityError(f"complexity exception is not approved: {finding_id}")
        _require_nonempty_string(exception.get("reviewer"), "reviewer")
        revision = _require_nonempty_string(exception.get("reviewed_revision"), "reviewed_revision")
        if REVISION_PATTERN.fullmatch(revision) is None:
            raise ComplexityError("reviewed_revision must be a lowercase forty-hex Git revision")
        _require_nonempty_string(exception.get("rationale"), "rationale")
        _require_string_list(exception.get("decomposition_alternatives"), "decomposition_alternatives")
        focused_tests = _require_string_list(exception.get("focused_tests"), "focused_tests")
        for test_path in focused_tests:
            normalized_test_path = _validate_relative_path(test_path)
            if not (ROOT / normalized_test_path).is_file():
                raise ComplexityError(
                    f"complexity exception references missing focused test: {normalized_test_path}"
                )
        approved.add(finding_id)
    return ExceptionEvaluation(
        approved_finding_ids=tuple(sorted(approved)),
        unapproved_finding_ids=tuple(sorted(review_ids - approved)),
    )


def _source_fingerprint(sources: Mapping[str, str]) -> str:
    """Hash a tooling-only length-framed snapshot of sorted paths and bytes."""

    digest = hashlib.sha256()
    for path, source in sorted(sources.items()):
        path_bytes = path.encode("utf-8")
        source_bytes = source.encode("utf-8")
        digest.update(len(path_bytes).to_bytes(4, "big"))
        digest.update(path_bytes)
        digest.update(len(source_bytes).to_bytes(8, "big"))
        digest.update(source_bytes)
    return digest.hexdigest()


def _function_report(function: FunctionMetric) -> dict[str, object]:
    """Return one stable function-report object."""

    return {
        "end_line": function.end_line,
        "lexical_block_depth": function.lexical_block_depth,
        "name": function.name,
        "noncomment_source_lines": function.noncomment_source_lines,
        "positional_parameters": function.positional_parameters,
        "start_line": function.start_line,
    }


def _trait_report(trait: PublicTraitMetric) -> dict[str, object]:
    """Return one stable public-trait report object."""

    return {
        "end_line": trait.end_line,
        "method_count": trait.method_count,
        "name": trait.name,
        "start_line": trait.start_line,
    }


def _finding_report(finding: Finding) -> dict[str, object]:
    """Return one stable finding object."""

    return {
        "finding_id": finding.finding_id,
        "item_kind": finding.item_kind,
        "item_name": finding.item_name,
        "level": finding.level,
        "measured": finding.measured,
        "metric": finding.metric,
        "path": finding.path,
        "preferred_max": finding.preferred_max,
        "review_trigger": finding.review_trigger,
        "source_sha256": finding.source_sha256,
        "start_line": finding.start_line,
    }


def build_report(sources: Mapping[str, str], registry: object) -> dict[str, Any]:
    """Build a deterministic report and canonical JSON convenience value."""

    normalized_sources: dict[str, str] = {}
    for path, source in sources.items():
        normalized = _validate_relative_path(path)
        if normalized in normalized_sources:
            raise ComplexityError(f"duplicate source path: {normalized}")
        normalized_sources[normalized] = source
    if not normalized_sources:
        raise ComplexityError("complexity report requires at least one Rust source")
    analyses = tuple(
        analyze_rust_source(path, normalized_sources[path]) for path in sorted(normalized_sources)
    )
    findings = classify_findings(analyses)
    evaluation = validate_exception_registry(registry, findings)
    payload: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "status": "pass" if not evaluation.unapproved_finding_ids else "review-needed",
        "source_fingerprint_sha256": _source_fingerprint(normalized_sources),
        "metric_contract": METRIC_POLICIES,
        "unmeasured_budgets": list(UNMEASURED_BUDGETS),
        "files": [
            {
                "functions": [_function_report(function) for function in analysis.functions],
                "noncomment_source_lines": analysis.noncomment_source_lines,
                "path": analysis.path,
                "public_traits": [_trait_report(trait) for trait in analysis.public_traits],
                "source_sha256": analysis.source_sha256,
            }
            for analysis in analyses
        ],
        "findings": [_finding_report(finding) for finding in findings],
        "exceptions": {
            "approved_finding_ids": list(evaluation.approved_finding_ids),
            "unapproved_finding_ids": list(evaluation.unapproved_finding_ids),
        },
        "summary": {
            "approved_exception_count": len(evaluation.approved_finding_ids),
            "file_count": len(analyses),
            "function_count": sum(len(analysis.functions) for analysis in analyses),
            "public_trait_count": sum(len(analysis.public_traits) for analysis in analyses),
            "review_required_count": sum(
                finding.level == "review_required" for finding in findings
            ),
            "unapproved_review_count": len(evaluation.unapproved_finding_ids),
            "warning_count": sum(finding.level == "warning" for finding in findings),
        },
        "non_claims": [
            "lexical metrics are not compiler AST or macro-expanded metrics",
            "lexical block depth is not cognitive complexity",
            "cyclomatic and cognitive complexity are unmeasured",
            "the checker does not classify semantic criticality",
            "exception metadata does not authenticate reviewer identity",
            "a passing report is not formal proof, human review, or production authority",
        ],
    }
    payload["canonical_json"] = json.dumps(
        payload, ensure_ascii=True, indent=2, sort_keys=True
    ) + "\n"
    return payload


def _read_repository_sources() -> dict[str, str]:
    """Read every current crate source file under the fixed review ceiling."""

    sources: dict[str, str] = {}
    for path in sorted(ROOT.glob("crates/*/src/**/*.rs")):
        if path.is_symlink():
            raise ComplexityError(f"Rust source symlink requires review: {path.relative_to(ROOT)}")
        source_bytes = path.read_bytes()
        if len(source_bytes) > MAX_SOURCE_FILE_BYTES:
            raise ComplexityError(
                f"Rust source exceeds one-megabyte review ceiling: {path.relative_to(ROOT)}"
            )
        try:
            source = source_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ComplexityError(f"Rust source is not UTF-8: {path.relative_to(ROOT)}") from error
        relative = path.relative_to(ROOT).as_posix()
        sources[relative] = source
    if not sources:
        raise ComplexityError("no Rust crate source files were discovered")
    return sources


def _read_registry(path_text: str) -> object:
    """Read one repository-relative exception registry."""

    normalized = _validate_relative_path(path_text)
    path = ROOT / normalized
    try:
        return _decode_registry_json(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ComplexityError(f"cannot read complexity exception registry: {normalized}") from error


def _decode_registry_json(source: str) -> object:
    """Decode JSON while rejecting duplicate object keys at every depth."""

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        decoded: dict[str, object] = {}
        for key, value in pairs:
            if key in decoded:
                raise ComplexityError(f"duplicate JSON object key in exception registry: {key!r}")
            decoded[key] = value
        return decoded

    return json.loads(source, object_pairs_hook=unique_object)


def _write_report(path_text: str, canonical_json: str) -> None:
    """Write a report only to a normalized repository-relative tooling path."""

    normalized = _validate_relative_path(path_text)
    relative_path = PurePosixPath(normalized)
    if (
        len(relative_path.parts) < 2
        or relative_path.parts[0] != "target"
        or relative_path.suffix != ".json"
    ):
        raise ComplexityError("complexity reports may be written only as JSON beneath target/")
    path = ROOT / normalized
    target_root = ROOT / "target"
    for parent in path.parents:
        if parent == ROOT:
            break
        if parent.exists() and parent.is_symlink():
            raise ComplexityError(f"complexity report parent is a symlink: {parent.relative_to(ROOT)}")
    if path.exists() and path.is_symlink():
        raise ComplexityError(f"complexity report path is a symlink: {normalized}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.resolve().is_relative_to(target_root.resolve()):
        raise ComplexityError("complexity report path resolves outside target/")
    path.write_text(canonical_json, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Measure repository Rust source and enforce exact exception coverage."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exceptions",
        default=DEFAULT_EXCEPTIONS_PATH,
        help="repository-relative approved-exception registry",
    )
    parser.add_argument(
        "--report",
        help="optional repository-relative path for canonical JSON output",
    )
    arguments = parser.parse_args(argv)
    try:
        report = build_report(_read_repository_sources(), _read_registry(arguments.exceptions))
        if arguments.report:
            _write_report(arguments.report, report["canonical_json"])
    except ComplexityError as error:
        print(f"complexity check failed: {error}", file=sys.stderr)
        return 1
    summary = report["summary"]
    for finding in report["findings"]:
        if finding["level"] == "warning":
            print(
                "complexity preferred limit exceeded: "
                f"{finding['path']}:{finding['start_line']} "
                f"{finding['item_name']} {finding['metric']}={finding['measured']} "
                f"> {finding['preferred_max']} (review trigger > {finding['review_trigger']})",
                file=sys.stderr,
            )
    if report["status"] != "pass":
        print(
            "complexity check requires review: "
            f"{summary['unapproved_review_count']} unapproved trigger(s); "
            f"report fingerprint {report['source_fingerprint_sha256']}",
            file=sys.stderr,
        )
        for finding in report["findings"]:
            if finding["level"] == "review_required" and finding["finding_id"] in report[
                "exceptions"
            ]["unapproved_finding_ids"]:
                print(
                    "complexity review required: "
                    f"{finding['path']}:{finding['start_line']} "
                    f"{finding['item_name']} {finding['metric']}={finding['measured']} "
                    f"> {finding['review_trigger']} ({finding['finding_id']})",
                    file=sys.stderr,
                )
        return 1
    print(
        "complexity check passed: "
        f"{summary['file_count']} files, {summary['function_count']} functions, "
        f"{summary['warning_count']} preferred-limit warning(s), "
        f"{summary['approved_exception_count']} approved exception(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
