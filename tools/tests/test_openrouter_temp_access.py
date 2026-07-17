"""Focused tests for temporary OpenRouter access."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tools.openrouter_temp_access import (
    AccessError,
    FREE_MODEL,
    PROBE_MARKER,
    RejectRedirects,
    clear_key,
    extract_probe,
    key_path,
    load_key,
    probe_body,
    store_key,
)


DUMMY_KEY = "unit-test-openrouter-secret-123456789"


class TemporarySecretTests(unittest.TestCase):
    def test_round_trip_is_owner_only_and_clear_removes_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            stored = store_key(DUMMY_KEY, base)
            self.assertEqual(load_key(base), DUMMY_KEY)
            self.assertEqual(os.stat(stored).st_mode & 0o777, 0o600)
            self.assertEqual(os.stat(stored.parent).st_mode & 0o777, 0o700)
            clear_key(base)
            self.assertFalse(key_path(base).exists())

    def test_rejects_short_or_whitespace_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            with self.assertRaises(AccessError):
                store_key("short", base)
            with self.assertRaises(AccessError):
                store_key("long-enough key with spaces", base)

    def test_rejects_symlinked_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            stored = store_key(DUMMY_KEY, base)
            target = stored.parent / "target"
            stored.replace(target)
            stored.symlink_to(target)
            with self.assertRaisesRegex(AccessError, "regular file"):
                load_key(base)


class FreeProbeTests(unittest.TestCase):
    def test_body_is_free_and_bounded(self) -> None:
        body = probe_body()
        self.assertEqual(body["model"], FREE_MODEL)
        self.assertEqual(body["max_tokens"], 64)

    def test_marker_must_match_exactly(self) -> None:
        good = {"choices": [{"message": {"content": PROBE_MARKER}}]}
        self.assertEqual(extract_probe(good), PROBE_MARKER)
        extra = {"choices": [{"message": {"content": f"ok {PROBE_MARKER}"}}]}
        with self.assertRaisesRegex(AccessError, "marker"):
            extract_probe(extra)

    def test_redirects_are_rejected(self) -> None:
        handler = RejectRedirects()
        self.assertIsNone(
            handler.redirect_request(
                object(),
                object(),
                302,
                "Found",
                {},
                "https://example.invalid/",
            )
        )


if __name__ == "__main__":
    unittest.main()
