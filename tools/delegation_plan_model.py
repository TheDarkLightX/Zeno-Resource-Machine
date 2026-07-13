"""Validate the machine-readable ZRM completion and delegation plan."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

VALID_STATES = {"architect_required", "blocked", "delegable", "complete", "human_only"}
VALID_TIERS = {"architect", "bounded_implementer", "mechanical_evidence", "human_or_external"}
VALID_CLASSES = {"A", "B", "C", "D", "E"}
VALID_PHASES = {"architectural_closure", "bounded_implementation", "safe_now", "release_and_review"}
VALID_ORACLE_KINDS = {"executable_reference", "golden_vectors", "state_machine", "evidence_replay"}
VALID_ORACLE_STATUSES = {"planned", "available"}
TASK_ID_RE = re.compile(r"ZRM-TASK-(\d{3})")
CBC_ID_RE = re.compile(r"ZRM-CBC-\d{3}")
SC_ID_RE = re.compile(r"ZRM-SC-\d{3}")
WORK_PACKAGE_RE = re.compile(r"WP(?:[0-9]|1[0-3])")


class DelegationPlanError(ValueError):
    """Raised when the delegation plan violates its fail-closed contract."""


def require(condition: bool, message: str) -> None:
    """Raise a typed plan error when ``condition`` is false."""
    if not condition:
        raise DelegationPlanError(message)


def nonempty(value: Any, label: str) -> str:
    """Return a nonempty string or reject."""
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be a nonempty string")
    return value


def string_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    """Return a duplicate-free list of nonempty strings."""
    require(isinstance(value, list), f"{label} must be a list")
    require(
        all(isinstance(item, str) and bool(item.strip()) for item in value),
        f"{label} must contain only nonempty strings",
    )
    require(allow_empty or bool(value), f"{label} must not be empty")
    require(len(value) == len(set(value)), f"{label} must not contain duplicates")
    return value


def safe_path(value: str, label: str) -> Path:
    """Reject absolute, empty, and parent-traversing repository paths."""
    path = Path(nonempty(value, label).partition("#")[0])
    require(not path.is_absolute(), f"{label} must be repository-relative")
    require(".." not in path.parts, f"{label} must not escape the repository")
    require(bool(path.parts), f"{label} must name a repository path")
    return path


def require_file(root: Path, value: str, label: str) -> None:
    """Require one repository-relative file reference to exist."""
    path = safe_path(value, label)
    resolved_root = root.resolve()
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(resolved_root), f"{label} escapes the repository")
    require(resolved.is_file(), f"{label} references missing file {path.as_posix()}")


def known_cbc_ids(root: Path) -> set[str]:
    """Load CBC identifiers from the active conformance matrix."""
    try:
        data = json.loads((root / "CONFORMANCE_MATRIX.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DelegationPlanError(f"cannot load conformance matrix: {error}") from error
    obligations = data.get("obligations")
    require(isinstance(obligations, list), "conformance obligations must be a list")
    identifiers = {item.get("id") for item in obligations if isinstance(item, dict)}
    require(all(isinstance(item, str) for item in identifiers), "conformance matrix has invalid IDs")
    return {item for item in identifiers if isinstance(item, str)}


def known_sc_ids(root: Path) -> set[str]:
    """Load semantic-contract identifiers from canonical filenames."""
    directory = root / "contracts"
    require(directory.is_dir(), "contracts directory is missing")
    identifiers = {
        path.stem
        for path in directory.glob("ZRM-SC-*.md")
        if SC_ID_RE.fullmatch(path.stem) is not None
    }
    require(bool(identifiers), "no semantic contracts were found")
    return identifiers


def validate_graph(tasks: list[dict[str, Any]]) -> None:
    """Require known, acyclic task dependencies."""
    identifiers = {task["id"] for task in tasks}
    graph: dict[str, list[str]] = {}
    for task in tasks:
        task_id = task["id"]
        dependencies = task["deps"]
        require(task_id not in dependencies, f"{task_id} cannot depend on itself")
        unknown = set(dependencies) - identifiers
        require(not unknown, f"{task_id} has unknown dependencies: {sorted(unknown)}")
        graph[task_id] = dependencies

    visited: set[str] = set()
    active: set[str] = set()

    def visit(identifier: str) -> None:
        require(identifier not in active, f"task dependency cycle reaches {identifier}")
        if identifier in visited:
            return
        active.add(identifier)
        for dependency in graph[identifier]:
            visit(dependency)
        active.remove(identifier)
        visited.add(identifier)

    for identifier in graph:
        visit(identifier)


def validate_task(
    task: dict[str, Any],
    *,
    expected_id: str,
    cbc_ids: set[str],
    sc_ids: set[str],
) -> None:
    """Validate one task independently of dependency completion state."""
    task_id = nonempty(task.get("id"), "task.id")
    require(task_id == expected_id, f"task identifiers must be sequential; expected {expected_id}")
    nonempty(task.get("title"), f"{task_id}.title")
    require(task.get("phase") in VALID_PHASES, f"{task_id}.phase is invalid")
    state = task.get("state")
    tier = task.get("tier")
    change_class = task.get("class")
    require(state in VALID_STATES, f"{task_id}.state is invalid")
    require(tier in VALID_TIERS, f"{task_id}.tier is invalid")
    require(change_class in VALID_CLASSES, f"{task_id}.class is invalid")

    boundary = task.get("boundary")
    require(
        isinstance(boundary, str) and bool(boundary) and "," not in boundary,
        f"{task_id}.boundary must name exactly one authority boundary",
    )

    work_packages = string_list(task.get("wp"), f"{task_id}.wp")
    require(
        all(WORK_PACKAGE_RE.fullmatch(item) is not None for item in work_packages),
        f"{task_id} contains an invalid work package",
    )
    dependencies = string_list(task.get("deps"), f"{task_id}.deps", allow_empty=True)
    require(
        all(TASK_ID_RE.fullmatch(item) is not None for item in dependencies),
        f"{task_id} contains an invalid dependency ID",
    )

    task_cbc = string_list(task.get("cbc"), f"{task_id}.cbc")
    require(
        all(CBC_ID_RE.fullmatch(item) is not None for item in task_cbc),
        f"{task_id} contains an invalid CBC ID",
    )
    unknown_cbc = set(task_cbc) - cbc_ids
    require(not unknown_cbc, f"{task_id} references unknown CBC IDs: {sorted(unknown_cbc)}")

    task_sc = string_list(task.get("sc"), f"{task_id}.sc")
    require(
        all(SC_ID_RE.fullmatch(item) is not None for item in task_sc),
        f"{task_id} contains an invalid semantic-contract ID",
    )
    unknown_sc = set(task_sc) - sc_ids
    require(not unknown_sc, f"{task_id} references unknown contracts: {sorted(unknown_sc)}")

    for field in ("decision", "scope", "command", "target", "non_goal"):
        nonempty(task.get(field), f"{task_id}.{field}")
    safe_path(task["decision"], f"{task_id}.decision")
    safe_path(task["scope"], f"{task_id}.scope")

    unresolved = task.get("unresolved")
    require(
        unresolved is None or (isinstance(unresolved, str) and bool(unresolved.strip())),
        f"{task_id}.unresolved must be null or a nonempty string",
    )
    string_list(task.get("negatives"), f"{task_id}.negatives")
    evidence = string_list(task.get("evidence"), f"{task_id}.evidence", allow_empty=True)
    for index, reference in enumerate(evidence):
        safe_path(reference, f"{task_id}.evidence[{index}]")

    oracle = task.get("oracle")
    require(isinstance(oracle, dict), f"{task_id}.oracle must be an object")
    require(
        set(oracle) == {"kind", "path", "status"},
        f"{task_id}.oracle must contain exactly kind, path, and status",
    )
    require(oracle.get("kind") in VALID_ORACLE_KINDS, f"{task_id}.oracle.kind is invalid")
    require(oracle.get("status") in VALID_ORACLE_STATUSES, f"{task_id}.oracle.status is invalid")
    safe_path(nonempty(oracle.get("path"), f"{task_id}.oracle.path"), f"{task_id}.oracle.path")

    if state == "architect_required":
        require(tier == "architect", f"{task_id} architect work needs architect tier")
        require(unresolved is not None, f"{task_id} architect work needs an unresolved decision")
    elif state == "human_only":
        require(tier == "human_or_external", f"{task_id} human-only work needs human tier")
    elif state in {"blocked", "delegable"}:
        require(
            tier in {"bounded_implementer", "mechanical_evidence"},
            f"{task_id} {state} work needs bounded or mechanical tier",
        )
    elif state == "complete":
        require(unresolved is None, f"{task_id} complete work cannot retain an unresolved decision")
        require(bool(evidence), f"{task_id} complete work needs evidence")
