"""Unit tests for repository conformance and workflow policy helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from tools.check_architecture import dependency_failures
from tools.check_conformance import ConformanceError, github_anchor, require, validate_reference
from tools.check_repository_hygiene import action_pin_failures


class ConformanceHelperTests(unittest.TestCase):
    """Exercise deterministic anchor and failure behavior."""

    def test_github_anchor_removes_punctuation(self) -> None:
        """Markdown anchors retain semantic words and separators."""

        self.assertEqual(github_anchor("13.6 ResourceWireV1 canonical bytes"), "136-resourcewirev1-canonical-bytes")

    def test_require_raises_typed_error(self) -> None:
        """Failed matrix predicates use the conformance error type."""

        with self.assertRaises(ConformanceError):
            require(False, "expected failure")

    def test_reference_cannot_escape_repository(self) -> None:
        """Parent traversal cannot satisfy a matrix evidence reference."""

        with self.assertRaises(ConformanceError):
            validate_reference("../ZRM/LICENSE", "ZRM-CBC-TEST", {})


class WorkflowPinTests(unittest.TestCase):
    """Exercise exact GitHub Action pin enforcement."""

    def test_full_commit_pin_is_accepted(self) -> None:
        """A forty-hex action ref passes."""

        workflow = "uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\n"
        self.assertEqual(action_pin_failures(workflow, Path("ci.yml")), [])

    def test_tag_ref_is_rejected(self) -> None:
        """A mutable version tag fails."""

        workflow = "uses: actions/checkout@v4\n"
        self.assertEqual(len(action_pin_failures(workflow, Path("ci.yml"))), 1)

class ArchitecturePolicyTests(unittest.TestCase):
    """Exercise exact external dependency allowlisting."""

    def test_unexpected_external_dependency_is_rejected(self) -> None:
        """A network client cannot silently enter a core crate."""

        package = {
            "name": "zrm-types",
            "dependencies": [{"name": "reqwest"}],
        }
        self.assertEqual(len(dependency_failures(package)), 1)

    def test_exact_crypto_dependencies_are_accepted(self) -> None:
        """The reviewed crypto dependency set passes exactly."""

        package = {
            "name": "zrm-crypto",
            "dependencies": [{"name": "sha2"}, {"name": "zrm-types"}],
        }
        self.assertEqual(dependency_failures(package), [])


if __name__ == "__main__":
    unittest.main()
