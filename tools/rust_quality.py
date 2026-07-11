"""Detect a conservative set of review-critical Rust quality hazards.

The rules in this module are deliberately lexical and narrow. Compiler and
Clippy checks remain the primary source for type-aware findings. This scanner
covers repository rules that those tools do not express directly, while
retaining explicit non-claims about semantic intent and macro expansion.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

if __package__:
    from .rust_complexity import (
        ComplexityError,
        _delimiter_pairs,
        _parameter_segments,
        _strip_non_code,
        _tokens,
        _validate_relative_path,
    )
else:
    from rust_complexity import (
        ComplexityError,
        _delimiter_pairs,
        _parameter_segments,
        _strip_non_code,
        _tokens,
        _validate_relative_path,
    )


QualityError = ComplexityError

RULE_CONTRACT: dict[str, dict[str, str]] = {
    "ZRM-Q001": {
        "category": "antipattern",
        "summary": "boolean control parameter",
    },
    "ZRM-Q002": {
        "category": "antipattern",
        "summary": "boolean field claims validated authority state",
    },
    "ZRM-Q003": {
        "category": "code_smell",
        "summary": "vague critical function name",
    },
    "ZRM-Q004": {
        "category": "code_smell",
        "summary": "broad lint suppression",
    },
    "ZRM-Q005": {
        "category": "antipattern",
        "summary": "stringly typed identity, mode, root, or code",
    },
    "ZRM-Q006": {
        "category": "antipattern",
        "summary": "primitive 32-byte identity outside a wire candidate",
    },
    "ZRM-Q007": {
        "category": "code_smell",
        "summary": "wildcard import",
    },
    "ZRM-Q008": {
        "category": "antipattern",
        "summary": "unordered hash collection in core source",
    },
    "ZRM-Q009": {
        "category": "antipattern",
        "summary": "floating-point type in core source",
    },
    "ZRM-Q010": {
        "category": "design_pattern",
        "summary": "generic manager, handler, service, or coordinator object",
    },
    "ZRM-Q011": {
        "category": "antipattern",
        "summary": "public field on an authority-bearing validated type",
    },
    "ZRM-Q012": {
        "category": "antipattern",
        "summary": "implicit fallback through unwrap_or",
    },
    "ZRM-Q013": {
        "category": "antipattern",
        "summary": "Default construction on a critical or authority-bearing type",
    },
    "ZRM-Q014": {
        "category": "antipattern",
        "summary": "wall-clock source in core code",
    },
    "ZRM-Q015": {
        "category": "antipattern",
        "summary": "feature-controlled verification bypass",
    },
    "ZRM-Q016": {
        "category": "antipattern",
        "summary": "test success path conditionally skips its assertions",
    },
}

# Compatibility-facing rule metadata used by the report builder. The
# ``preferred_pattern`` values describe a local corrective direction; they do
# not assert that one design pattern is universally optimal.
QUALITY_RULES: dict[str, dict[str, str]] = {
    rule_id: {
        "category": contract["category"],
        "name": contract["summary"].replace(" ", "-"),
        "meaning": contract["summary"],
        "preferred_pattern": {
            "ZRM-Q001": "semantic enum or named input type",
            "ZRM-Q002": "sealed authority stage type",
            "ZRM-Q003": "operation or invariant-specific name",
            "ZRM-Q004": "narrow expect attribute with reason and review record",
            "ZRM-Q005": "semantic value object",
            "ZRM-Q006": "32-byte identity newtype",
            "ZRM-Q007": "explicit imports",
            "ZRM-Q008": "sorted vector, BTreeMap, or BTreeSet",
            "ZRM-Q009": "fixed-width integer or governed rational representation",
            "ZRM-Q010": "single-responsibility type and narrow capability ports",
            "ZRM-Q011": "private fields with invariant-preserving getters",
            "ZRM-Q012": "typed reject or explicitly bound fallback policy",
            "ZRM-Q013": "explicit invariant-aware constructor",
            "ZRM-Q014": "typed governed time input",
            "ZRM-Q015": "fail-closed verifier boundary",
            "ZRM-Q016": "typed test error and required success construction",
        }[rule_id],
    }
    for rule_id, contract in RULE_CONTRACT.items()
}

_AUTHORITY_FIELD_NAMES = re.compile(
    r"^(?:is_)?(?:verified|validated|authenticated|authorized|committed|accepted)$"
)
_IDENTITY_FIELD_NAMES = re.compile(r".*(?:_id|_root|_digest|_mode|_code)$")
_RAW_IDENTITY_FIELD_NAMES = re.compile(r".*(?:_id|_root|_digest)$|^nonce$")
_AUTHORITY_TYPE_NAMES = re.compile(
    r"^(?:Verified|Validated|Authenticated|Trusted|Committed|Accepted|Authorized|Sealed)"
    r"|^CommitPlan|Capability"
)
_CRITICAL_DEFAULT_NAMES = re.compile(
    r"(?:Policy|Resource|Transition|Verifier|Commit|Journal|Capability|Manager|Service)"
)
_GENERIC_OBJECT_NAMES = re.compile(r"(?:Manager|Handler|Service|Coordinator|Processor)$")
_VAGUE_FUNCTION_NAMES = {"handle", "process", "do_work", "utils"}
_BYPASS_WORDS = re.compile(r"(?:bypass|skip|disable|fake|mock|insecure).*(?:verify|proof)|"
                           r"(?:verify|proof).*(?:bypass|skip|disable|fake|mock|insecure)")


@dataclass(frozen=True)
class QualityFinding:
    """One source-bound, deterministic code-quality finding."""

    finding_id: str
    rule_id: str
    category: str
    path: str
    line: int
    item: str
    message: str
    source_sha256: str


@dataclass(frozen=True)
class _StructRange:
    """One lexical braced struct and its source span."""

    name: str
    start_offset: int
    body_start_offset: int
    body_end_offset: int


def _line_at(source: str, offset: int) -> int:
    """Return the one-based source line containing ``offset``."""

    return source.count("\n", 0, offset) + 1


def _struct_ranges(cleaned: str) -> tuple[_StructRange, ...]:
    """Return conservative ranges for ordinary braced Rust structs."""

    tokens = _tokens(cleaned)
    pairs = _delimiter_pairs(tokens)
    ranges: list[_StructRange] = []
    for index, token in enumerate(tokens):
        if token.value != "struct" or index + 1 >= len(tokens):
            continue
        name = tokens[index + 1]
        if not name.is_identifier:
            continue
        cursor = index + 2
        angle_depth = 0
        square_depth = 0
        while cursor < len(tokens):
            value = tokens[cursor].value
            if value == "<":
                angle_depth += 1
            elif value == ">" and angle_depth > 0:
                angle_depth -= 1
            elif value == "[":
                square_depth += 1
            elif value == "]" and square_depth > 0:
                square_depth -= 1
            elif value == "{" and (angle_depth > 0 or square_depth > 0):
                cursor = pairs[cursor] + 1
                continue
            elif value in {"{", ";"} and angle_depth == square_depth == 0:
                break
            cursor += 1
        if cursor >= len(tokens) or tokens[cursor].value != "{":
            continue
        close = pairs[cursor]
        ranges.append(
            _StructRange(
                name=name.value,
                start_offset=token.offset,
                body_start_offset=tokens[cursor].offset + 1,
                body_end_offset=tokens[close].offset,
            )
        )
    return tuple(ranges)


def _is_wire_or_candidate(type_name: str) -> bool:
    """Return whether a type is explicitly unvalidated wire/candidate data."""

    return bool(re.search(r"(?:Wire|Candidate)(?:V\d+)?$", type_name))


def _finding(
    *,
    path: str,
    source_sha256: str,
    rule_id: str,
    line: int,
    item: str,
    message: str,
) -> QualityFinding:
    """Construct one content-bound finding."""

    contract = RULE_CONTRACT[rule_id]
    identity = "\0".join((path, source_sha256, rule_id, str(line), item, message))
    finding_id = "zrm-quality:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return QualityFinding(
        finding_id=finding_id,
        rule_id=rule_id,
        category=contract["category"],
        path=path,
        line=line,
        item=item,
        message=message,
        source_sha256=source_sha256,
    )


def _function_findings(
    path: str, cleaned: str, source_sha256: str
) -> list[QualityFinding]:
    """Find boolean parameters and vague function names."""

    tokens = _tokens(cleaned)
    pairs = _delimiter_pairs(tokens)
    findings: list[QualityFinding] = []
    for index, token in enumerate(tokens):
        if token.value != "fn" or index + 1 >= len(tokens):
            continue
        name = tokens[index + 1]
        if not name.is_identifier:
            continue
        if name.value in _VAGUE_FUNCTION_NAMES:
            findings.append(
                _finding(
                    path=path,
                    source_sha256=source_sha256,
                    rule_id="ZRM-Q003",
                    line=token.line,
                    item=name.value,
                    message=f"function {name.value!r} does not name its invariant or operation",
                )
            )
        cursor = index + 2
        angle_depth = 0
        square_depth = 0
        while cursor < len(tokens):
            value = tokens[cursor].value
            if value == "<":
                angle_depth += 1
            elif value == ">" and angle_depth > 0:
                angle_depth -= 1
            elif value == "[":
                square_depth += 1
            elif value == "]" and square_depth > 0:
                square_depth -= 1
            elif value == "{" and (angle_depth > 0 or square_depth > 0):
                cursor = pairs[cursor] + 1
                continue
            elif value == "(" and angle_depth == square_depth == 0:
                break
            elif value in {";", "{", "}"} and angle_depth == square_depth == 0:
                break
            cursor += 1
        if cursor >= len(tokens) or tokens[cursor].value != "(":
            continue
        close = pairs[cursor]
        for segment in _parameter_segments(tokens[cursor + 1 : close]):
            values = [part.value for part in segment]
            if ":" not in values:
                continue
            colon = values.index(":")
            if "bool" not in values[colon + 1 :]:
                continue
            parameter = next((value for value in values[:colon] if value not in {"mut", "ref"}), "bool")
            findings.append(
                _finding(
                    path=path,
                    source_sha256=source_sha256,
                    rule_id="ZRM-Q001",
                    line=segment[0].line,
                    item=f"{name.value}.{parameter}",
                    message="replace a boolean control parameter with a semantic enum or input type",
                )
            )
    return findings


def _struct_findings(
    path: str, cleaned: str, source_sha256: str
) -> list[QualityFinding]:
    """Find primitive authority state and suspicious object patterns."""

    findings: list[QualityFinding] = []
    for struct in _struct_ranges(cleaned):
        authority_type = bool(_AUTHORITY_TYPE_NAMES.search(struct.name))
        if _GENERIC_OBJECT_NAMES.search(struct.name):
            findings.append(
                _finding(
                    path=path,
                    source_sha256=source_sha256,
                    rule_id="ZRM-Q010",
                    line=_line_at(cleaned, struct.start_offset),
                    item=struct.name,
                    message="generic orchestration object requires a narrower responsibility boundary",
                )
            )
        body = cleaned[struct.body_start_offset : struct.body_end_offset]
        field_pattern = re.compile(
            r"(?m)^\s*(?P<visibility>pub(?:\s*\([^)]*\))?\s+)?"
            r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?P<type>[^,\n]+)"
        )
        for match in field_pattern.finditer(body):
            field_name = match.group("name")
            field_type = " ".join(match.group("type").split())
            offset = struct.body_start_offset + match.start()
            line = _line_at(cleaned, offset)
            item = f"{struct.name}.{field_name}"
            if _AUTHORITY_FIELD_NAMES.fullmatch(field_name) and re.search(r"\bbool\b", field_type):
                findings.append(
                    _finding(
                        path=path,
                        source_sha256=source_sha256,
                        rule_id="ZRM-Q002",
                        line=line,
                        item=item,
                        message="authority state must be represented by a sealed type, not a boolean field",
                    )
                )
            if _IDENTITY_FIELD_NAMES.fullmatch(field_name) and re.search(
                r"(?:\bString\b|&\s*(?:'\w+\s+)?str\b)", field_type
            ):
                findings.append(
                    _finding(
                        path=path,
                        source_sha256=source_sha256,
                        rule_id="ZRM-Q005",
                        line=line,
                        item=item,
                        message="identity, root, mode, and code fields require a semantic type",
                    )
                )
            if (
                _RAW_IDENTITY_FIELD_NAMES.fullmatch(field_name)
                and re.search(r"\[\s*u8\s*;\s*(?:32|DIGEST_BYTES)\s*\]", field_type)
                and not _is_wire_or_candidate(struct.name)
            ):
                findings.append(
                    _finding(
                        path=path,
                        source_sha256=source_sha256,
                        rule_id="ZRM-Q006",
                        line=line,
                        item=item,
                        message="32-byte semantic identities require a dedicated value type",
                    )
                )
            if authority_type and match.group("visibility") is not None:
                findings.append(
                    _finding(
                        path=path,
                        source_sha256=source_sha256,
                        rule_id="ZRM-Q011",
                        line=line,
                        item=item,
                        message="authority-bearing validated fields must remain private",
                    )
                )
    return findings


def _regex_findings(
    path: str, source: str, cleaned: str, source_sha256: str
) -> list[QualityFinding]:
    """Find high-confidence repository-wide lexical hazards."""

    findings: list[QualityFinding] = []

    rules: tuple[tuple[str, re.Pattern[str], str, str], ...] = (
        (
            "ZRM-Q004",
            re.compile(r"#!?\s*\[\s*allow\s*\([^\]]*(?:clippy::all|clippy::pedantic|warnings|unsafe_code)[^\]]*\)\s*\]"),
            "lint-suppression",
            "broad lint suppression requires a reviewed, issue-bound exception",
        ),
        (
            "ZRM-Q007",
            re.compile(r"(?m)^\s*use\s+[^;\n]*::\s*\*\s*;"),
            "wildcard-import",
            "import explicit names at the review boundary",
        ),
        (
            "ZRM-Q008",
            re.compile(r"\b(?:HashMap|HashSet)\b|std\s*::\s*collections\s*::\s*hash_(?:map|set)"),
            "unordered-collection",
            "unordered collections require an explicit noncanonical adapter boundary",
        ),
        (
            "ZRM-Q009",
            re.compile(r"\b(?:f32|f64)\b"),
            "floating-point",
            "floating point is forbidden in semantic authority source",
        ),
        (
            "ZRM-Q012",
            re.compile(r"\.\s*unwrap_or(?:_default|_else)?\s*\("),
            "implicit-fallback",
            "fallback behavior must be explicit and policy-bound",
        ),
        (
            "ZRM-Q014",
            re.compile(r"\b(?:SystemTime|Instant)\b|std\s*::\s*time\s*::"),
            "wall-clock",
            "semantic code must receive governed time as typed input",
        ),
    )
    for rule_id, pattern, item, message in rules:
        for match in pattern.finditer(cleaned):
            findings.append(
                _finding(
                    path=path,
                    source_sha256=source_sha256,
                    rule_id=rule_id,
                    line=_line_at(cleaned, match.start()),
                    item=item,
                    message=message,
                )
            )

    derive_pattern = re.compile(
        r"#\s*\[\s*derive\s*\((?P<derives>[^)]*)\)\s*\]\s*"
        r"(?:pub(?:\s*\([^)]*\))?\s+)?struct\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
    )
    for match in derive_pattern.finditer(cleaned):
        if "Default" not in match.group("derives").split(",") and not re.search(
            r"(?:^|,)\s*Default\s*(?:,|$)", match.group("derives")
        ):
            continue
        name = match.group("name")
        if _AUTHORITY_TYPE_NAMES.search(name) or _CRITICAL_DEFAULT_NAMES.search(name):
            findings.append(
                _finding(
                    path=path,
                    source_sha256=source_sha256,
                    rule_id="ZRM-Q013",
                    line=_line_at(cleaned, match.start()),
                    item=name,
                    message="critical types require explicit invariant-aware construction",
                )
            )

    feature_pattern = re.compile(
        r"(?m)^\s*(?P<attribute>#!?\[\s*cfg[^\n\]]*feature\s*=\s*[^\n\]]+\])"
    )
    for match in feature_pattern.finditer(source):
        attribute_offset = match.start("attribute")
        if cleaned[attribute_offset] != "#":
            continue
        compact = re.sub(r"\s+", "", match.group("attribute")).lower()
        if _BYPASS_WORDS.search(compact):
            findings.append(
                _finding(
                    path=path,
                    source_sha256=source_sha256,
                    rule_id="ZRM-Q015",
                    line=_line_at(cleaned, attribute_offset),
                    item="verification-feature",
                    message="verification cannot be weakened by a runtime or build feature",
                )
            )
    return findings


def _conditional_test_findings(
    path: str, cleaned: str, source_sha256: str
) -> list[QualityFinding]:
    """Find unguarded success-only assertions in explicit assurance sources."""

    parts = PurePosixPath(path).parts
    assurance_source = "tests" in parts or "kani" in PurePosixPath(path).name
    if not assurance_source:
        return []
    findings: list[QualityFinding] = []
    let_pattern = re.compile(
        r"let\s+Ok\s*\(\s*(?P<binding>[A-Za-z_][A-Za-z0-9_]*)\s*\)\s*=\s*"
        r"(?P<expression>[A-Za-z_][A-Za-z0-9_]*)\s+else\s*\{\s*"
        r"return(?:\s+Ok\s*\(\s*\(\s*\)\s*\))?\s*;?\s*\}",
        re.DOTALL,
    )
    for match in let_pattern.finditer(cleaned):
        expression = match.group("expression")
        guard = cleaned[max(0, match.start() - 300) : match.start()]
        if re.search(rf"assert!\s*\(\s*{re.escape(expression)}\.is_ok\s*\(\s*\)\s*\)", guard):
            continue
        findings.append(
            _finding(
                path=path,
                source_sha256=source_sha256,
                rule_id="ZRM-Q016",
                line=_line_at(cleaned, match.start()),
                item=match.group("binding"),
                message="constructor failure would return test success before principal assertions",
            )
        )
    return findings


def analyze_rust_quality(path: str, source: str) -> tuple[QualityFinding, ...]:
    """Return deterministic findings for one repository-relative Rust source."""

    normalized = _validate_relative_path(path)
    if not isinstance(source, str):
        raise QualityError("Rust source must be UTF-8 text")
    cleaned = _strip_non_code(source)
    source_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
    findings = [
        *_function_findings(normalized, cleaned, source_sha256),
        *_struct_findings(normalized, cleaned, source_sha256),
        *_regex_findings(normalized, source, cleaned, source_sha256),
        *_conditional_test_findings(normalized, cleaned, source_sha256),
    ]
    unique = {
        (finding.rule_id, finding.line, finding.item, finding.message): finding
        for finding in findings
    }
    return tuple(
        sorted(
            unique.values(),
            key=lambda finding: (
                finding.path,
                finding.line,
                finding.rule_id,
                finding.item,
                finding.finding_id,
            ),
        )
    )
