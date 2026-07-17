"""Temporary, secret-safe OpenRouter setup and free connectivity probe.

The key is held in an owner-only runtime file until `clear` or logout/reboot.
This Class B helper does not make paid requests and grants no ZRM authority.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import stat
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence


CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
FREE_MODEL = "openrouter/free"
PROBE_MARKER = "ZRM_OPENROUTER_OK"
MAX_KEY_BYTES = 512
MAX_RESPONSE_BYTES = 256_000


class AccessError(Exception):
    """A bounded setup, secret, transport, or response failure."""


class RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Reject redirects so an authorization header cannot change origins."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Mapping[str, str],
        newurl: str,
    ) -> None:
        del req, fp, code, msg, headers, newurl
        return None


def _runtime_base() -> Path:
    configured = os.environ.get("XDG_RUNTIME_DIR", "")
    if configured:
        candidate = Path(configured)
        try:
            metadata = candidate.stat()
        except OSError:
            pass
        else:
            if (
                candidate.is_absolute()
                and stat.S_ISDIR(metadata.st_mode)
                and metadata.st_uid == os.getuid()
            ):
                return candidate
    return Path(tempfile.gettempdir())


def session_dir(base: Path | None = None) -> Path:
    """Return the user-specific temporary OpenRouter directory."""

    root = _runtime_base() if base is None else base
    return root / f"zrm-openrouter-{os.getuid()}"


def key_path(base: Path | None = None) -> Path:
    """Return the fixed temporary key path."""

    return session_dir(base) / "api_key"


def _check_session_dir(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise AccessError("temporary OpenRouter session is not set up") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or metadata.st_mode & 0o077
    ):
        raise AccessError("temporary OpenRouter session directory is not owner-only")


def _ensure_session_dir(base: Path | None = None) -> Path:
    directory = session_dir(base)
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        pass
    _check_session_dir(directory)
    return directory


def _validated_key_bytes(key: str) -> bytes:
    encoded = key.encode("utf-8")
    if (
        len(encoded) < 20
        or len(encoded) > MAX_KEY_BYTES
        or any(character.isspace() for character in key)
    ):
        raise AccessError("key must be one 20-to-512-byte token")
    return encoded


def store_key(key: str, base: Path | None = None) -> Path:
    """Atomically store a validated key without printing it."""

    encoded = _validated_key_bytes(key)
    directory = _ensure_session_dir(base)
    target = directory / "api_key"
    temporary = directory / f".api_key.{os.getpid()}"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if not hasattr(os, "O_NOFOLLOW"):
        raise AccessError("this platform lacks required no-follow file support")
    flags |= os.O_NOFOLLOW
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        os.chmod(target, 0o600, follow_symlinks=False)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def load_key(base: Path | None = None) -> str:
    """Load the bounded owner-only temporary key without following symlinks."""

    directory = session_dir(base)
    _check_session_dir(directory)
    target = directory / "api_key"
    try:
        metadata = target.lstat()
    except FileNotFoundError as exc:
        raise AccessError("temporary OpenRouter key is missing; run setup") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or metadata.st_mode & 0o077
    ):
        raise AccessError("temporary OpenRouter key is not an owner-only regular file")
    flags = os.O_RDONLY
    if not hasattr(os, "O_NOFOLLOW"):
        raise AccessError("this platform lacks required no-follow file support")
    flags |= os.O_NOFOLLOW
    descriptor = os.open(target, flags)
    try:
        raw = os.read(descriptor, MAX_KEY_BYTES + 1)
    finally:
        os.close(descriptor)
    if len(raw) > MAX_KEY_BYTES:
        raise AccessError("temporary OpenRouter key exceeds its size bound")
    try:
        key = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AccessError("temporary OpenRouter key is not valid UTF-8") from exc
    _validated_key_bytes(key)
    return key


def clear_key(base: Path | None = None) -> None:
    """Remove the temporary key and its empty session directory."""

    directory = session_dir(base)
    if not directory.exists():
        return
    _check_session_dir(directory)
    (directory / "api_key").unlink(missing_ok=True)
    try:
        directory.rmdir()
    except OSError:
        pass


def probe_body() -> dict[str, Any]:
    """Return the fixed free-model marker request."""

    return {
        "model": FREE_MODEL,
        "messages": [
            {
                "role": "user",
                "content": f"Return exactly this marker and no other text: {PROBE_MARKER}",
            }
        ],
        "max_tokens": 64,
        "stream": False,
    }


def extract_probe(payload: Mapping[str, Any]) -> str:
    """Require one exact marker response."""

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AccessError("OpenRouter free probe returned no choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise AccessError("OpenRouter free probe returned an invalid choice")
    message = first.get("message")
    if not isinstance(message, dict):
        raise AccessError("OpenRouter free probe returned no message")
    content = message.get("content")
    if not isinstance(content, str) or content.strip() != PROBE_MARKER:
        raise AccessError("OpenRouter free probe marker did not match")
    return content.strip()


def run_probe(key: str) -> dict[str, Any]:
    """Make one bounded authenticated request through the free router."""

    request = urllib.request.Request(
        CHAT_URL,
        data=json.dumps(probe_body(), separators=(",", ":")).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "zrm-openrouter-temp-probe/1",
        },
        method="POST",
    )
    request.add_unredirected_header("Authorization", f"Bearer {key}")
    opener = urllib.request.build_opener(RejectRedirects)
    try:
        with opener.open(request, timeout=60) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise AccessError(f"OpenRouter returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AccessError("OpenRouter free probe transport failed") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise AccessError("OpenRouter free probe response exceeded its size bound")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AccessError("OpenRouter free probe returned malformed JSON") from exc
    if not isinstance(payload, dict):
        raise AccessError("OpenRouter free probe response was not an object")
    if key in json.dumps(payload, ensure_ascii=False):
        raise AccessError("OpenRouter response unexpectedly contained the key")
    extract_probe(payload)
    return payload


def _safe_usage(payload: Mapping[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return {}
    allowed = {"prompt_tokens", "completion_tokens", "total_tokens", "cost"}
    return {name: value for name, value in usage.items() if name in allowed}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("setup", "status", "probe", "clear"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one temporary-access command without exposing secret material."""

    command = _parser().parse_args(argv).command
    try:
        if command == "setup":
            if not sys.stdin.isatty():
                raise AccessError("run setup in your own interactive terminal")
            secret = getpass.getpass("OpenRouter key (hidden): ")
            try:
                path = store_key(secret)
            finally:
                secret = ""
            print(f"temporary OpenRouter key ready: {path}")
            print("The key value was not printed. Run 'clear' when finished.")
            return 0
        if command == "clear":
            clear_key()
            print("temporary OpenRouter key cleared")
            return 0
        key = load_key()
        if command == "status":
            print(json.dumps({"ok": True, "temporary_key_ready": True}))
            return 0
        payload = run_probe(key)
        print(
            json.dumps(
                {
                    "ok": True,
                    "authenticated_free_probe": True,
                    "requested_model": FREE_MODEL,
                    "response_model": payload.get("model", ""),
                    "usage": _safe_usage(payload),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except AccessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"error: unexpected {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
