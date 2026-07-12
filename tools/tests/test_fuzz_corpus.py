"""Regression tests for exact deterministic fuzz-corpus membership."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from fuzz.generate_corpus import check_seed_names


class ExactCorpusMembershipTests(unittest.TestCase):
    """Ensure recursive libFuzzer inputs cannot bypass the named corpus set."""

    def test_exact_top_level_regular_files_pass(self) -> None:
        """Only the exact reviewed top-level files are accepted."""

        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory)
            (corpus / "first").write_bytes(b"one")
            (corpus / "second").write_bytes(b"two")
            self.assertTrue(check_seed_names(corpus, {"first", "second"}, "test"))

    def test_nested_file_is_rejected(self) -> None:
        """A recursively loaded libFuzzer unit cannot hide in a subdirectory."""

        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory)
            (corpus / "first").write_bytes(b"one")
            nested = corpus / "nested"
            nested.mkdir()
            (nested / "extra").write_bytes(b"unreviewed")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertFalse(check_seed_names(corpus, {"first"}, "test"))

    def test_symlink_is_rejected(self) -> None:
        """A linked corpus entry cannot escape exact regular-file review."""

        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory)
            (corpus / "first").write_bytes(b"one")
            (corpus / "linked").symlink_to(corpus / "first")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertFalse(check_seed_names(corpus, {"first"}, "test"))


if __name__ == "__main__":
    unittest.main()
