"""Measure deterministic lexical complexity review triggers in Rust source.

This dependency-free scanner deliberately measures a small auditable subset of
QUALITY_GATES.md. It does not parse a compiler AST or expand macros.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath


METRIC_POLICIES: dict[str, dict[str, object]] = {
    "function_noncomment_source_lines": {
        "item_kind": "function",
        "preferred_max": 40,
        "review_trigger": 60,
        "meaning": "nonblank, noncomment lexical source lines from fn through its terminator",
    },
    "lexical_block_depth": {
        "item_kind": "function",
        "preferred_max": 3,
        "review_trigger": 4,
        "meaning": "maximum nested code-brace depth inside the function body, excluding its outer brace",
    },
    "positional_parameters": {
        "item_kind": "function",
        "preferred_max": 4,
        "review_trigger": 6,
        "meaning": "explicit top-level function parameters, excluding a Rust self receiver",
    },
    "public_trait_methods": {
        "item_kind": "public_trait",
        "preferred_max": 7,
        "review_trigger": 10,
        "meaning": "direct fn items declared by a lexically public trait",
    },
    "module_noncomment_source_lines": {
        "item_kind": "module",
        "preferred_max": 400,
        "review_trigger": 700,
        "meaning": "nonblank, noncomment lexical source lines in one Rust source file",
    },
}

UNMEASURED_BUDGETS = (
    "cyclomatic_complexity",
    "cognitive_complexity",
    "public_generic_type_parameters",
    "semantic_criticality",
    "macro_expanded_complexity",
)

TOKEN_PATTERN = re.compile(
    r"r#[A-Za-z_][A-Za-z0-9_]*|[A-Za-z_][A-Za-z0-9_]*|"
    r"0[xob][0-9A-Fa-f_]+|[0-9][0-9_]*|::|->|=>|&&|\|\||"
    r"[{}()\[\]<>;,!:&*=+\-/?]"
)


class ComplexityError(ValueError):
    """Raised when source or exception data cannot be measured unambiguously."""


@dataclass(frozen=True)
class Token:
    """One relevant lexical Rust token with a source location."""

    value: str
    offset: int
    line: int
    is_identifier: bool


@dataclass(frozen=True)
class FunctionMetric:
    """Lexical metrics for one Rust function declaration or definition."""

    name: str
    start_line: int
    end_line: int
    noncomment_source_lines: int
    lexical_block_depth: int
    positional_parameters: int


@dataclass(frozen=True)
class PublicTraitMetric:
    """Direct method count for one lexically public Rust trait."""

    name: str
    start_line: int
    end_line: int
    method_count: int


@dataclass(frozen=True)
class SourceAnalysis:
    """Deterministic lexical metrics for one repository-relative Rust file."""

    path: str
    source_sha256: str
    noncomment_source_lines: int
    functions: tuple[FunctionMetric, ...]
    public_traits: tuple[PublicTraitMetric, ...]


@dataclass(frozen=True)
class Finding:
    """One preferred-limit warning or mandatory review trigger."""

    finding_id: str
    level: str
    path: str
    item_kind: str
    item_name: str
    start_line: int
    metric: str
    measured: int
    preferred_max: int
    review_trigger: int
    source_sha256: str


def _validate_relative_path(path_text: str) -> str:
    """Return one normalized repository-relative POSIX path or reject."""

    if not isinstance(path_text, str) or not path_text or "\\" in path_text:
        raise ComplexityError("source paths must be nonempty repository-relative POSIX paths")
    path = PurePosixPath(path_text)
    if path.is_absolute() or ".." in path.parts or str(path) != path_text:
        raise ComplexityError(f"path is not normalized and repository-relative: {path_text!r}")
    return path_text


def _blank_non_newlines(output: list[str], source: str, start: int, end: int) -> None:
    """Replace a non-code source interval with spaces while preserving lines."""

    for index in range(start, end):
        if source[index] != "\n":
            output[index] = " "


def _raw_string_end(source: str, start: int) -> int | None:
    """Return the exclusive end of a Rust raw string beginning at ``start``."""

    if start > 0 and (source[start - 1].isalnum() or source[start - 1] == "_"):
        return None
    if source.startswith(("br", "cr"), start):
        cursor = start + 2
    elif source.startswith("r", start):
        cursor = start + 1
    else:
        return None
    hash_start = cursor
    while cursor < len(source) and source[cursor] == "#":
        cursor += 1
    if cursor >= len(source) or source[cursor] != '"':
        return None
    hash_count = cursor - hash_start
    terminator = '"' + ("#" * hash_count)
    end_start = source.find(terminator, cursor + 1)
    if end_start < 0:
        raise ComplexityError("unterminated Rust raw string")
    return end_start + len(terminator)


def _quoted_string_end(source: str, start: int) -> int:
    """Return the exclusive end of an ordinary Rust string literal."""

    cursor = start + 1
    escaped = False
    while cursor < len(source):
        character = source[cursor]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == '"':
            return cursor + 1
        cursor += 1
    raise ComplexityError("unterminated Rust string literal")


def _character_literal_end(source: str, start: int) -> int | None:
    """Return a Rust character literal end, or ``None`` for a lifetime tick."""

    value_index = start + 1
    if value_index >= len(source) or source[value_index] in "\r\n'":
        return None
    if source[value_index] != "\\":
        closing_index = value_index + 1
        if closing_index < len(source) and source[closing_index] == "'":
            return closing_index + 1
        return None
    escape_index = value_index + 1
    if escape_index >= len(source):
        return None
    escape = source[escape_index]
    if escape == "x":
        closing_index = escape_index + 3
    elif escape == "u" and source.startswith("{", escape_index + 1):
        closing_brace = source.find("}", escape_index + 2)
        if closing_brace < 0 or "\n" in source[escape_index:closing_brace]:
            return None
        closing_index = closing_brace + 1
    else:
        closing_index = escape_index + 1
    if closing_index < len(source) and source[closing_index] == "'":
        return closing_index + 1
    return None


def _strip_non_code(source: str) -> str:
    """Blank comments and literals while preserving offsets and line breaks."""

    output = list(source)
    cursor = 0
    while cursor < len(source):
        if source.startswith("//", cursor):
            end = source.find("\n", cursor + 2)
            end = len(source) if end < 0 else end
            _blank_non_newlines(output, source, cursor, end)
            cursor = end
            continue
        if source.startswith("/*", cursor):
            depth = 1
            end = cursor + 2
            while end < len(source) and depth > 0:
                if source.startswith("/*", end):
                    depth += 1
                    end += 2
                elif source.startswith("*/", end):
                    depth -= 1
                    end += 2
                else:
                    end += 1
            if depth != 0:
                raise ComplexityError("unterminated Rust block comment")
            _blank_non_newlines(output, source, cursor, end)
            cursor = end
            continue
        raw_end = _raw_string_end(source, cursor)
        if raw_end is not None:
            _blank_non_newlines(output, source, cursor, raw_end)
            cursor = raw_end
            continue
        if source[cursor] == '"':
            end = _quoted_string_end(source, cursor)
            _blank_non_newlines(output, source, cursor, end)
            cursor = end
            continue
        if source[cursor] == "'":
            end = _character_literal_end(source, cursor)
            if end is not None:
                _blank_non_newlines(output, source, cursor, end)
                cursor = end
                continue
        cursor += 1
    return "".join(output)


def _tokens(cleaned_source: str) -> tuple[Token, ...]:
    """Return relevant tokens with deterministic one-based line numbers."""

    tokens: list[Token] = []
    previous_end = 0
    line = 1
    for match in TOKEN_PATTERN.finditer(cleaned_source):
        line += cleaned_source.count("\n", previous_end, match.start())
        value = match.group(0)
        tokens.append(
            Token(
                value=value,
                offset=match.start(),
                line=line,
                is_identifier=bool(re.fullmatch(r"(?:r#)?[A-Za-z_][A-Za-z0-9_]*", value)),
            )
        )
        previous_end = match.end()
    return tuple(tokens)


def _delimiter_pairs(tokens: Sequence[Token]) -> dict[int, int]:
    """Return matching delimiter token indexes or reject malformed source."""

    opening_for = {")": "(", "]": "[", "}": "{"}
    stacks: dict[str, list[int]] = {"(": [], "[": [], "{": []}
    pairs: dict[int, int] = {}
    for index, token in enumerate(tokens):
        if token.value in stacks:
            stacks[token.value].append(index)
        elif token.value in opening_for:
            opening = opening_for[token.value]
            if not stacks[opening]:
                raise ComplexityError(f"unmatched Rust delimiter {token.value!r} at line {token.line}")
            opening_index = stacks[opening].pop()
            pairs[opening_index] = index
            pairs[index] = opening_index
    unclosed = [tokens[index] for stack in stacks.values() for index in stack]
    if unclosed:
        first = min(unclosed, key=lambda token: token.offset)
        raise ComplexityError(f"unclosed Rust delimiter {first.value!r} at line {first.line}")
    return pairs


def _noncomment_line_count(cleaned_source: str) -> int:
    """Count nonblank source lines after comment and literal blanking."""

    return sum(1 for line in cleaned_source.splitlines() if line.strip())


def _parameter_segments(tokens: Sequence[Token]) -> tuple[tuple[Token, ...], ...]:
    """Split function parameters on top-level commas."""

    segments: list[tuple[Token, ...]] = []
    current: list[Token] = []
    round_depth = 0
    square_depth = 0
    brace_depth = 0
    angle_depth = 0
    for token in tokens:
        value = token.value
        if value == "(":
            round_depth += 1
        elif value == ")" and round_depth > 0:
            round_depth -= 1
        elif value == "[":
            square_depth += 1
        elif value == "]" and square_depth > 0:
            square_depth -= 1
        elif value == "{":
            brace_depth += 1
        elif value == "}" and brace_depth > 0:
            brace_depth -= 1
        elif value == "<":
            angle_depth += 1
        elif value == ">" and angle_depth > 0:
            angle_depth -= 1
        if value == "," and round_depth == square_depth == brace_depth == angle_depth == 0:
            if current:
                segments.append(tuple(current))
                current = []
        else:
            current.append(token)
    if current:
        segments.append(tuple(current))
    return tuple(segments)


def _is_receiver(segment: Sequence[Token]) -> bool:
    """Return whether a parameter segment represents a Rust ``self`` receiver."""

    values = [token.value for token in segment]
    if "self" not in values:
        return False
    self_index = values.index("self")
    return ":" not in values[:self_index]


def _positional_parameter_count(tokens: Sequence[Token]) -> int:
    """Count explicit parameters while excluding a self receiver."""

    return sum(1 for segment in _parameter_segments(tokens) if not _is_receiver(segment))


def _function_block_depth(tokens: Sequence[Token], opening: int, closing: int) -> int:
    """Return maximum nested code-brace depth inside a function body."""

    depth = 0
    maximum = 0
    for token in tokens[opening + 1 : closing]:
        if token.value == "{":
            depth += 1
            maximum = max(maximum, depth)
        elif token.value == "}":
            depth -= 1
            if depth < 0:
                raise ComplexityError(f"function brace depth underflow at line {token.line}")
    if depth != 0:
        raise ComplexityError("function body has inconsistent lexical brace depth")
    return maximum


def _extract_functions(
    cleaned_source: str, tokens: Sequence[Token], pairs: Mapping[int, int]
) -> tuple[FunctionMetric, ...]:
    """Extract lexical function metrics from one token stream."""

    functions: list[FunctionMetric] = []
    for index, token in enumerate(tokens):
        if token.value != "fn" or index + 1 >= len(tokens) or not tokens[index + 1].is_identifier:
            continue
        name_token = tokens[index + 1]
        parameter_open: int | None = None
        cursor = index + 2
        while cursor < len(tokens):
            value = tokens[cursor].value
            if value == "(":
                parameter_open = cursor
                break
            if value in {";", "{", "}"}:
                break
            cursor += 1
        if parameter_open is None:
            raise ComplexityError(f"function {name_token.value!r} lacks a parameter list")
        parameter_close = pairs[parameter_open]
        terminator_index: int | None = None
        body_open: int | None = None
        cursor = parameter_close + 1
        round_depth = 0
        square_depth = 0
        angle_depth = 0
        while cursor < len(tokens):
            value = tokens[cursor].value
            if value == "(":
                round_depth += 1
            elif value == ")":
                if round_depth == 0:
                    raise ComplexityError(
                        f"function {name_token.value!r} has an unmatched signature ')'"
                    )
                round_depth -= 1
            elif value == "[":
                square_depth += 1
            elif value == "]":
                if square_depth == 0:
                    raise ComplexityError(
                        f"function {name_token.value!r} has an unmatched signature ']'"
                    )
                square_depth -= 1
            elif value == "<":
                angle_depth += 1
            elif value == ">" and angle_depth > 0:
                angle_depth -= 1
            at_signature_top_level = round_depth == square_depth == angle_depth == 0
            if value == ";" and at_signature_top_level:
                terminator_index = cursor
                break
            if value == "{" and at_signature_top_level:
                body_open = cursor
                terminator_index = pairs[cursor]
                break
            if value == "{":
                cursor = pairs[cursor] + 1
                continue
            if value == "}" and at_signature_top_level:
                break
            cursor += 1
        if terminator_index is None:
            raise ComplexityError(f"function {name_token.value!r} lacks a body or semicolon")
        terminator = tokens[terminator_index]
        source_end = terminator.offset + len(terminator.value)
        function_source = cleaned_source[token.offset:source_end]
        block_depth = (
            0
            if body_open is None
            else _function_block_depth(tokens, body_open, terminator_index)
        )
        functions.append(
            FunctionMetric(
                name=name_token.value,
                start_line=token.line,
                end_line=terminator.line,
                noncomment_source_lines=_noncomment_line_count(function_source),
                lexical_block_depth=block_depth,
                positional_parameters=_positional_parameter_count(
                    tokens[parameter_open + 1 : parameter_close]
                ),
            )
        )
    return tuple(functions)


def _extract_public_traits(
    tokens: Sequence[Token], pairs: Mapping[int, int]
) -> tuple[PublicTraitMetric, ...]:
    """Extract direct method counts from lexically public traits."""

    traits: list[PublicTraitMetric] = []
    for index, token in enumerate(tokens):
        if token.value != "pub":
            continue
        trait_index: int | None = None
        cursor = index + 1
        while cursor < len(tokens):
            value = tokens[cursor].value
            if value == "trait":
                trait_index = cursor
                break
            if value in {";", "{", "}"}:
                break
            cursor += 1
        if trait_index is None or trait_index + 1 >= len(tokens):
            continue
        name_token = tokens[trait_index + 1]
        if not name_token.is_identifier:
            raise ComplexityError(f"public trait at line {token.line} lacks an identifier")
        body_open: int | None = None
        cursor = trait_index + 2
        while cursor < len(tokens):
            if tokens[cursor].value == "{":
                body_open = cursor
                break
            if tokens[cursor].value in {";", "}"}:
                break
            cursor += 1
        if body_open is None:
            raise ComplexityError(f"public trait {name_token.value!r} lacks a body")
        body_close = pairs[body_open]
        depth = 0
        method_count = 0
        for body_token in tokens[body_open + 1 : body_close]:
            if body_token.value == "{":
                depth += 1
            elif body_token.value == "}":
                depth -= 1
            elif body_token.value == "fn" and depth == 0:
                method_count += 1
        traits.append(
            PublicTraitMetric(
                name=name_token.value,
                start_line=token.line,
                end_line=tokens[body_close].line,
                method_count=method_count,
            )
        )
    return tuple(traits)


def analyze_rust_source(path: str, source: str) -> SourceAnalysis:
    """Measure one repository-relative Rust source string.

    Raises:
        ComplexityError: if the path, comments, literals, or delimiters are
            malformed and therefore cannot yield an unambiguous report.
    """

    normalized_path = _validate_relative_path(path)
    if not isinstance(source, str):
        raise ComplexityError("Rust source must be UTF-8 text")
    cleaned = _strip_non_code(source)
    tokens = _tokens(cleaned)
    pairs = _delimiter_pairs(tokens)
    return SourceAnalysis(
        path=normalized_path,
        source_sha256=hashlib.sha256(source.encode("utf-8")).hexdigest(),
        noncomment_source_lines=_noncomment_line_count(cleaned),
        functions=_extract_functions(cleaned, tokens, pairs),
        public_traits=_extract_public_traits(tokens, pairs),
    )


def _finding(
    *,
    path: str,
    item_kind: str,
    item_name: str,
    start_line: int,
    metric: str,
    measured: int,
    source_sha256: str,
) -> Finding | None:
    """Construct a deterministic finding when a preferred limit is exceeded."""

    policy = METRIC_POLICIES[metric]
    preferred = int(policy["preferred_max"])
    trigger = int(policy["review_trigger"])
    if measured <= preferred:
        return None
    level = "review_required" if measured > trigger else "warning"
    identity = {
        "item_kind": item_kind,
        "item_name": item_name,
        "measured": measured,
        "metric": metric,
        "path": path,
        "review_trigger": trigger,
        "source_sha256": source_sha256,
        "start_line": start_line,
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    finding_id = "zrm-complexity:" + hashlib.sha256(encoded).hexdigest()
    return Finding(
        finding_id=finding_id,
        level=level,
        path=path,
        item_kind=item_kind,
        item_name=item_name,
        start_line=start_line,
        metric=metric,
        measured=measured,
        preferred_max=preferred,
        review_trigger=trigger,
        source_sha256=source_sha256,
    )


def classify_findings(analyses: Sequence[SourceAnalysis]) -> tuple[Finding, ...]:
    """Classify all measured preferred-limit and review-trigger findings."""

    findings: list[Finding] = []
    for analysis in sorted(analyses, key=lambda item: item.path):
        candidates: list[Finding | None] = [
            _finding(
                path=analysis.path,
                item_kind="module",
                item_name=analysis.path,
                start_line=1,
                metric="module_noncomment_source_lines",
                measured=analysis.noncomment_source_lines,
                source_sha256=analysis.source_sha256,
            )
        ]
        for function in analysis.functions:
            candidates.extend(
                (
                    _finding(
                        path=analysis.path,
                        item_kind="function",
                        item_name=function.name,
                        start_line=function.start_line,
                        metric="function_noncomment_source_lines",
                        measured=function.noncomment_source_lines,
                        source_sha256=analysis.source_sha256,
                    ),
                    _finding(
                        path=analysis.path,
                        item_kind="function",
                        item_name=function.name,
                        start_line=function.start_line,
                        metric="lexical_block_depth",
                        measured=function.lexical_block_depth,
                        source_sha256=analysis.source_sha256,
                    ),
                    _finding(
                        path=analysis.path,
                        item_kind="function",
                        item_name=function.name,
                        start_line=function.start_line,
                        metric="positional_parameters",
                        measured=function.positional_parameters,
                        source_sha256=analysis.source_sha256,
                    ),
                )
            )
        for trait in analysis.public_traits:
            candidates.append(
                _finding(
                    path=analysis.path,
                    item_kind="public_trait",
                    item_name=trait.name,
                    start_line=trait.start_line,
                    metric="public_trait_methods",
                    measured=trait.method_count,
                    source_sha256=analysis.source_sha256,
                )
            )
        findings.extend(candidate for candidate in candidates if candidate is not None)
    findings.sort(
        key=lambda item: (item.path, item.start_line, item.item_kind, item.item_name, item.metric)
    )
    return tuple(findings)
