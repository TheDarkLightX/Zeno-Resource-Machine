"""Regression tests for exact deterministic fuzz-corpus membership."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fuzz.generate_corpus import check_corpus_expectations, check_seed, check_seed_names


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

    def test_corpus_root_symlink_is_rejected(self) -> None:
        """The reviewed corpus directory itself cannot be a symlink."""

        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            corpus = parent / "actual"
            corpus.mkdir()
            (corpus / "first").write_bytes(b"one")
            linked = parent / "linked"
            linked.symlink_to(corpus, target_is_directory=True)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertFalse(check_seed_names(linked, {"first"}, "test"))

    def test_invalid_layout_precedes_every_seed_read(self) -> None:
        """A linked root rejects before any member content can be opened."""

        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            actual = parent / "actual"
            actual.mkdir()
            (actual / "first").write_bytes(b"one")
            linked = parent / "linked"
            linked.symlink_to(actual, target_is_directory=True)
            with (
                contextlib.redirect_stderr(io.StringIO()),
                mock.patch(
                    "fuzz.generate_corpus.check_seed",
                    side_effect=AssertionError("seed content was opened before layout review"),
                ) as seed_check,
            ):
                self.assertFalse(
                    check_corpus_expectations(
                        [(linked, {"first"}, "test")],
                        [(linked / "first", b"one", "first")],
                    )
                )
            seed_check.assert_not_called()

    def test_seed_reader_rejects_direct_symlink(self) -> None:
        """An expected name cannot redirect the bounded content check."""

        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            actual = parent / "actual"
            actual.write_bytes(b"one")
            linked = parent / "linked"
            linked.symlink_to(actual)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertFalse(check_seed(linked, b"one", "test"))

    def test_wrong_seed_size_rejects_before_read(self) -> None:
        """A large or stale file cannot trigger an unbounded content read."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seed"
            path.write_bytes(b"four")
            with (
                contextlib.redirect_stderr(io.StringIO()),
                mock.patch("fuzz.generate_corpus.os.read") as read,
            ):
                self.assertFalse(check_seed(path, b"one", "test"))
            read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
