"""Unit tests for deterministic Rust source-complexity reporting."""

from __future__ import annotations

import contextlib
import io
import unittest
from unittest.mock import patch

from tools.check_complexity import (
    ComplexityError,
    _read_registry,
    _write_report,
    analyze_rust_source,
    build_report,
    classify_findings,
    main,
    validate_exception_registry,
)


def function_with_source_lines(name: str, source_lines: int) -> str:
    """Return a formatted function with exactly ``source_lines`` code lines."""

    if source_lines < 3:
        raise ValueError("a braced function needs at least three source lines")
    body = "\n".join(f"    let value_{index} = {index};" for index in range(source_lines - 2))
    return f"fn {name}() {{\n{body}\n}}\n"


class RustLexicalAnalysisTests(unittest.TestCase):
    """Exercise the bounded lexical contract independently of repository files."""

    def test_comments_and_strings_do_not_create_items_or_nesting(self) -> None:
        """Rust-looking text outside code cannot affect measured items."""

        source = r'''
// fn line_comment(fake: u8) { {{{
/* outer { fn block_comment() {}
   /* nested comment } */
} */
const ORDINARY: &str = "fn ordinary(a: u8) { {{{";
const RAW: &str = r###"fn raw(a: u8) { }}}"###;
fn real(value: u8) {
    let brace = "{";
    if value > 0 {
        let _copy = value;
    }
}
'''
        analysis = analyze_rust_source("crates/example/src/lib.rs", source)

        self.assertEqual([function.name for function in analysis.functions], ["real"])
        function = analysis.functions[0]
        self.assertEqual(function.positional_parameters, 1)
        self.assertEqual(function.lexical_block_depth, 1)

    def test_multiline_function_has_deterministic_source_line_count(self) -> None:
        """Blank and comment-only lines are excluded from the lexical count."""

        source = """fn add(
    first: u8,
    second: u8,
) -> u8 {
    // excluded comment

    let marker = "{";
    first + second
}
"""
        analysis = analyze_rust_source("crates/example/src/lib.rs", source)

        self.assertEqual(len(analysis.functions), 1)
        self.assertEqual(analysis.functions[0].noncomment_source_lines, 7)
        self.assertEqual(analysis.functions[0].lexical_block_depth, 0)

    def test_receiver_is_not_counted_as_positional_api_parameter(self) -> None:
        """Nested type commas do not inflate a method's explicit inputs."""

        source = """impl Example {
    fn apply(
        &mut self,
        first: u8,
        pair: (u8, u8),
        callback: fn(u8, u8),
    ) {}
}
"""
        analysis = analyze_rust_source("crates/example/src/lib.rs", source)

        self.assertEqual(analysis.functions[0].positional_parameters, 3)

    def test_multiple_lifetimes_are_not_misread_as_character_literals(self) -> None:
        """Lifetime ticks remain code while one brace character is blanked."""

        source = """fn borrow<'a, 'b>(first: &'a Value, second: &'b Value) {
    let brace = '{';
}
"""
        analysis = analyze_rust_source("crates/example/src/lib.rs", source)

        self.assertEqual(analysis.functions[0].positional_parameters, 2)
        self.assertEqual(analysis.functions[0].lexical_block_depth, 0)

    def test_const_expression_in_return_type_cannot_hide_large_body(self) -> None:
        """An array-length const block is part of the signature, not the body."""

        body = "\n".join(f"    let value_{index} = {index};" for index in range(61))
        source = f"fn array_value() -> [u8; {{ 1 }}] {{\n{body}\n    [0]\n}}\n"

        analysis = analyze_rust_source("crates/example/src/lib.rs", source)
        function = analysis.functions[0]
        findings = classify_findings([analysis])

        self.assertGreater(function.noncomment_source_lines, 60)
        self.assertEqual(function.end_line, len(source.splitlines()))
        self.assertIn(
            "review_required",
            [finding.level for finding in findings if finding.item_name == "array_value"],
        )

    def test_const_expression_in_where_clause_cannot_hide_large_body(self) -> None:
        """A const-generic bound brace cannot terminate function discovery."""

        body = "\n".join(f"    let value_{index} = {index};" for index in range(61))
        source = (
            "fn bounded<T>() -> u8\n"
            "where\n"
            "    T: Trait<{ 1 }>,\n"
            "{\n"
            f"{body}\n"
            "    0\n"
            "}\n"
        )

        analysis = analyze_rust_source("crates/example/src/lib.rs", source)
        function = analysis.functions[0]
        findings = classify_findings([analysis])

        self.assertGreater(function.noncomment_source_lines, 60)
        self.assertEqual(function.end_line, len(source.splitlines()))
        self.assertIn(
            "review_required",
            [finding.level for finding in findings if finding.item_name == "bounded"],
        )

    def test_public_trait_methods_ignore_nested_default_body_tokens(self) -> None:
        """Only direct methods of externally visible traits are counted."""

        source = """pub trait Port {
    fn first(&self);
    fn second(&self) {
        fn nested_helper() {}
        nested_helper();
    }
}

trait PrivatePort {
    fn hidden(&self);
}
"""
        analysis = analyze_rust_source("crates/example/src/lib.rs", source)

        self.assertEqual(len(analysis.public_traits), 1)
        self.assertEqual(analysis.public_traits[0].name, "Port")
        self.assertEqual(analysis.public_traits[0].method_count, 2)

    def test_unterminated_block_comment_fails_closed(self) -> None:
        """Ambiguous source cannot produce a passing complexity report."""

        with self.assertRaises(ComplexityError):
            analyze_rust_source("crates/example/src/lib.rs", "fn value() {} /*")


class FindingPolicyTests(unittest.TestCase):
    """Exercise preferred warnings and mandatory review triggers."""

    def test_preferred_excess_warns_and_review_trigger_requires_approval(self) -> None:
        """The documented gap between preferred and trigger limits is retained."""

        warning_analysis = analyze_rust_source(
            "crates/example/src/warning.rs", function_with_source_lines("warning", 41)
        )
        review_analysis = analyze_rust_source(
            "crates/example/src/review.rs", function_with_source_lines("review", 61)
        )

        warning = classify_findings([warning_analysis])
        review = classify_findings([review_analysis])
        self.assertEqual([finding.level for finding in warning], ["warning"])
        self.assertEqual([finding.level for finding in review], ["review_required"])

        evaluation = validate_exception_registry(
            {"schema": "zrm/complexity-exceptions/v1", "exceptions": []}, review
        )
        self.assertEqual(evaluation.unapproved_finding_ids, (review[0].finding_id,))

    def test_exact_approved_exception_covers_one_review_finding(self) -> None:
        """Approval metadata must bind the exact measured finding."""

        analysis = analyze_rust_source(
            "crates/example/src/review.rs", function_with_source_lines("review", 61)
        )
        findings = classify_findings([analysis])
        registry = {
            "schema": "zrm/complexity-exceptions/v1",
            "exceptions": [
                {
                    "finding_id": findings[0].finding_id,
                    "status": "approved",
                    "reviewer": "maintainer",
                    "reviewed_revision": "a" * 40,
                    "rationale": "The single ordered invariant is clearer when reviewed together.",
                    "decomposition_alternatives": ["Split the ordered checks into invariant families."],
                    "focused_tests": ["tools/tests/test_complexity.py"],
                }
            ],
        }

        evaluation = validate_exception_registry(registry, findings)
        self.assertEqual(evaluation.approved_finding_ids, (findings[0].finding_id,))
        self.assertEqual(evaluation.unapproved_finding_ids, ())

    def test_finding_id_changes_when_source_changes_at_the_same_metrics(self) -> None:
        """An approval cannot survive an unreviewed same-size source edit."""

        first_source = function_with_source_lines("review", 61)
        second_source = first_source.replace("let value_0 = 0;", "let value_0 = 1;")
        first = classify_findings(
            [analyze_rust_source("crates/example/src/review.rs", first_source)]
        )[0]
        second = classify_findings(
            [analyze_rust_source("crates/example/src/review.rs", second_source)]
        )[0]

        self.assertNotEqual(first.finding_id, second.finding_id)

    def test_stale_duplicate_and_unapproved_exceptions_fail_closed(self) -> None:
        """The registry cannot silently retain an obsolete or ambiguous approval."""

        analysis = analyze_rust_source(
            "crates/example/src/review.rs", function_with_source_lines("review", 61)
        )
        finding = classify_findings([analysis])[0]
        valid = {
            "finding_id": finding.finding_id,
            "status": "approved",
            "reviewer": "maintainer",
            "reviewed_revision": "b" * 40,
            "rationale": "A focused reviewer accepted the coherent ordered check.",
            "decomposition_alternatives": ["Use two named validation phases."],
            "focused_tests": ["tools/tests/test_complexity.py"],
        }

        stale = {**valid, "finding_id": "zrm-complexity:" + "0" * 64}
        with self.assertRaises(ComplexityError):
            validate_exception_registry(
                {"schema": "zrm/complexity-exceptions/v1", "exceptions": [stale]}, [finding]
            )

        with self.assertRaises(ComplexityError):
            validate_exception_registry(
                {"schema": "zrm/complexity-exceptions/v1", "exceptions": [valid, valid]},
                [finding],
            )

        unapproved = {**valid, "status": "pending"}
        with self.assertRaises(ComplexityError):
            validate_exception_registry(
                {"schema": "zrm/complexity-exceptions/v1", "exceptions": [unapproved]},
                [finding],
            )

        missing_test = {**valid, "focused_tests": ["tools/tests/missing_complexity_test.py"]}
        with self.assertRaises(ComplexityError):
            validate_exception_registry(
                {"schema": "zrm/complexity-exceptions/v1", "exceptions": [missing_test]},
                [finding],
            )


class ReportTests(unittest.TestCase):
    """Exercise deterministic, repository-relative machine output."""

    def test_report_order_fingerprint_and_json_are_deterministic(self) -> None:
        """Input mapping order cannot change the report identity or encoding."""

        first_sources = {
            "crates/zeta/src/lib.rs": "fn zeta() {}\n",
            "crates/alpha/src/lib.rs": "fn alpha() {}\n",
        }
        second_sources = dict(reversed(list(first_sources.items())))
        registry = {"schema": "zrm/complexity-exceptions/v1", "exceptions": []}

        first = build_report(first_sources, registry)
        second = build_report(second_sources, registry)
        self.assertEqual(first, second)
        self.assertEqual(
            [file_report["path"] for file_report in first["files"]],
            ["crates/alpha/src/lib.rs", "crates/zeta/src/lib.rs"],
        )
        self.assertNotIn("/" + "home" + "/", first["canonical_json"])
        self.assertEqual(first["status"], "pass")
        self.assertIn("public_generic_type_parameters", first["unmeasured_budgets"])

    def test_absolute_or_parent_paths_reject(self) -> None:
        """Reports never embed host paths or escape the repository."""

        registry = {"schema": "zrm/complexity-exceptions/v1", "exceptions": []}
        for path in ("/" + "tmp" + "/lib.rs", "../lib.rs"):
            with self.subTest(path=path), self.assertRaises(ComplexityError):
                build_report({path: "fn value() {}\n"}, registry)

    def test_empty_source_set_cannot_report_pass(self) -> None:
        """The library API shares the CLI's fail-closed discovery rule."""

        registry = {"schema": "zrm/complexity-exceptions/v1", "exceptions": []}
        with self.assertRaises(ComplexityError):
            build_report({}, registry)

    def test_exception_json_rejects_duplicate_root_key(self) -> None:
        """A later root value cannot silently replace reviewed registry data."""

        source = (
            '{"schema":"zrm/complexity-exceptions/v1",'
            '"schema":"zrm/complexity-exceptions/v1","exceptions":[]}'
        )

        with (
            patch("pathlib.Path.read_text", return_value=source),
            self.assertRaisesRegex(ComplexityError, "duplicate JSON object key"),
        ):
            _read_registry("tools/complexity_exceptions.json")

    def test_exception_json_rejects_duplicate_nested_key(self) -> None:
        """Duplicate fields inside an exception cannot be normalized away."""

        source = (
            '{"schema":"zrm/complexity-exceptions/v1","exceptions":['
            '{"status":"approved","status":"pending"}]}'
        )

        with (
            patch("pathlib.Path.read_text", return_value=source),
            self.assertRaisesRegex(ComplexityError, "duplicate JSON object key"),
        ):
            _read_registry("tools/complexity_exceptions.json")

    def test_cli_prints_each_preferred_limit_warning(self) -> None:
        """A passing CLI run still exposes each item needing preferred cleanup."""

        sources = {
            "crates/example/src/lib.rs": function_with_source_lines("warning", 41)
        }
        registry = {"schema": "zrm/complexity-exceptions/v1", "exceptions": []}
        stderr = io.StringIO()
        stdout = io.StringIO()

        with (
            patch("tools.check_complexity._read_repository_sources", return_value=sources),
            patch("tools.check_complexity._read_registry", return_value=registry),
            contextlib.redirect_stderr(stderr),
            contextlib.redirect_stdout(stdout),
        ):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        self.assertIn("complexity preferred limit exceeded", stderr.getvalue())
        self.assertIn("function_noncomment_source_lines=41", stderr.getvalue())
        self.assertIn("1 preferred-limit warning(s)", stdout.getvalue())

    def test_report_writer_cannot_target_repository_source(self) -> None:
        """A diagnostic report path cannot overwrite reviewed input files."""

        with patch("pathlib.Path.write_text") as write_text:
            with self.assertRaises(ComplexityError):
                _write_report("tools/should-not-write.json", "{}\n")
        write_text.assert_not_called()


if __name__ == "__main__":
    unittest.main()
