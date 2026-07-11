"""Fail closed on LLVM source-coverage thresholds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class CoverageError(RuntimeError):
    """Raised when a coverage report is malformed or below policy."""


def _percentage(covered: int, count: int) -> float:
    """Return a deterministic percentage for a validated nonempty metric."""

    return covered * 100.0 / count


def coverage_totals(report: dict[str, Any], scope_prefix: str | None) -> dict[str, dict[str, int]]:
    """Extract line and branch totals for the workspace or one repository prefix."""

    try:
        data = report["data"]
        if len(data) != 1:
            raise CoverageError("coverage report must contain exactly one data object")
        if scope_prefix is None:
            source = data[0]["totals"]
            return {
                metric: {
                    "count": int(source[metric]["count"]),
                    "covered": int(source[metric]["covered"]),
                }
                for metric in ("lines", "branches")
            }

        normalized = scope_prefix.strip("/") + "/"
        selected = []
        for entry in data[0]["files"]:
            filename = Path(entry["filename"]).as_posix()
            if f"/{normalized}" in filename or filename.startswith(normalized):
                selected.append(entry)
        if not selected:
            raise CoverageError(f"coverage scope has no files: {scope_prefix}")
        return {
            metric: {
                "count": sum(int(entry["summary"][metric]["count"]) for entry in selected),
                "covered": sum(int(entry["summary"][metric]["covered"]) for entry in selected),
            }
            for metric in ("lines", "branches")
        }
    except (IndexError, KeyError, TypeError, ValueError) as error:
        raise CoverageError("malformed LLVM coverage report") from error


def enforce_thresholds(
    totals: dict[str, dict[str, int]], min_lines: float, min_branches: float
) -> tuple[float, float]:
    """Return percentages after enforcing inclusive line and branch thresholds."""

    for metric in ("lines", "branches"):
        count = totals[metric]["count"]
        covered = totals[metric]["covered"]
        if count <= 0:
            raise CoverageError(f"{metric} metric must contain at least one site")
        if covered < 0 or covered > count:
            raise CoverageError(
                f"{metric} metric has invalid covered/count values: {covered}/{count}"
            )
    line_percent = _percentage(totals["lines"]["covered"], totals["lines"]["count"])
    branch_percent = _percentage(
        totals["branches"]["covered"], totals["branches"]["count"]
    )
    if line_percent < min_lines:
        raise CoverageError(f"line coverage {line_percent:.2f}% is below {min_lines:.2f}%")
    if branch_percent < min_branches:
        raise CoverageError(
            f"branch coverage {branch_percent:.2f}% is below {min_branches:.2f}%"
        )
    return line_percent, branch_percent


def main() -> int:
    """Load one LLVM JSON report and enforce requested thresholds."""

    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--scope-prefix")
    parser.add_argument("--min-lines", type=float, required=True)
    parser.add_argument("--min-branches", type=float, required=True)
    arguments = parser.parse_args()
    try:
        report = json.loads(arguments.report.read_text(encoding="utf-8"))
        totals = coverage_totals(report, arguments.scope_prefix)
        line_percent, branch_percent = enforce_thresholds(
            totals, arguments.min_lines, arguments.min_branches
        )
    except (CoverageError, OSError, json.JSONDecodeError) as error:
        print(f"coverage check failed: {error}")
        return 1
    scope = arguments.scope_prefix or "workspace"
    print(
        f"coverage check passed for {scope}: "
        f"lines={line_percent:.2f}% branches={branch_percent:.2f}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
