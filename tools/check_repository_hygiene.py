"""Check repository-local security and workflow hygiene without dependencies."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRECTORIES = {".git", "__pycache__", "artifacts", "target"}
SKIP_FILES = {".git"}
TEXT_SUFFIXES = {"", ".json", ".lock", ".md", ".py", ".rs", ".toml", ".txt", ".yaml", ".yml"}
MAX_REPOSITORY_FILE_BYTES = 1_048_576
CONTEXT_MARKERS = (
    "/" + "home" + "/",
    "/" + "mnt" + "/" + "data" + "/",
    "/" + "tmp" + "/",
    "sand" + "box:",
    "Down" + "loads/",
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b"),
)
AUTHORITY_PLACEHOLDERS = re.compile(r"\b(?:TODO|FIXME|HACK|XXX)\b|\btodo!\s*\(|\bunimplemented!\s*\(")
MERGE_MARKERS = re.compile(r"^(?:<{7}|={7}|>{7})(?:\s|$)", re.MULTILINE)
REMOTE_ACTION = re.compile(r"^\s*uses:\s*([^\s#]+)(?:\s+#.*)?$", re.MULTILINE)
PINNED_ACTION = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def repository_files(root: Path = ROOT) -> list[Path]:
    """Return deterministic repository files while excluding build and VCS data."""

    files: list[Path] = []
    for directory, directory_names, file_names in os.walk(root):
        directory_names[:] = sorted(name for name in directory_names if name not in SKIP_DIRECTORIES)
        for file_name in sorted(name for name in file_names if name not in SKIP_FILES):
            path = Path(directory) / file_name
            if path.suffix in TEXT_SUFFIXES:
                files.append(path)
    return files


def repository_file_metadata_failures(root: Path = ROOT) -> list[str]:
    """Reject symlinks, unexpected executable modes, and oversized files."""

    failures: list[str] = []
    for directory, directory_names, file_names in os.walk(root):
        directory_names[:] = sorted(name for name in directory_names if name not in SKIP_DIRECTORIES)
        for file_name in sorted(name for name in file_names if name not in SKIP_FILES):
            path = Path(directory) / file_name
            relative_path = path.relative_to(root)
            if path.is_symlink():
                failures.append(f"{relative_path}: repository symlink requires explicit review")
                continue
            stat = path.stat()
            if stat.st_mode & 0o111:
                failures.append(f"{relative_path}: unexpected executable mode")
            if stat.st_size > MAX_REPOSITORY_FILE_BYTES:
                failures.append(f"{relative_path}: file exceeds one-megabyte review ceiling")
    return failures


def action_pin_failures(text: str, relative_path: Path) -> list[str]:
    """Return unpinned remote GitHub Action references from one workflow."""

    failures = repository_file_metadata_failures()
    for reference in REMOTE_ACTION.findall(text):
        if reference.startswith("./"):
            continue
        if PINNED_ACTION.fullmatch(reference) is None:
            failures.append(f"{relative_path}: unpinned workflow action {reference}")
    return failures


def main() -> int:
    """Run deterministic source, secret, placeholder, and action-pin checks."""

    failures: list[str] = []
    for path in repository_files():
        relative_path = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in CONTEXT_MARKERS:
            if marker in text:
                failures.append(f"{relative_path}: local-context marker {marker!r}")
        if MERGE_MARKERS.search(text) is not None:
            failures.append(f"{relative_path}: unresolved merge marker")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text) is not None:
                failures.append(f"{relative_path}: possible secret material")
        if str(relative_path).startswith("crates/") and AUTHORITY_PLACEHOLDERS.search(text) is not None:
            failures.append(f"{relative_path}: placeholder in authority-path source")
        if relative_path.parts[:2] == (".github", "workflows"):
            failures.extend(action_pin_failures(text, relative_path))
        if path.name == "Cargo.toml" and re.search(r"\bgit\s*=", text) is not None:
            failures.append(f"{relative_path}: unreviewed Git dependency")

    if failures:
        for failure in failures:
            print(f"repository hygiene failed: {failure}", file=sys.stderr)
        return 1
    print("repository hygiene passed: configured context, secret, source, mode, size, and action-pin checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
