"""Validate the machine-readable ZRM completion and delegation plan."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__:
    from .delegation_plan_model import (
        ROOT, DelegationPlanError, known_cbc_ids, known_sc_ids, nonempty,
        require, require_file, safe_path, string_list, validate_graph, validate_task,
    )
else:
    from delegation_plan_model import (
        ROOT, DelegationPlanError, known_cbc_ids, known_sc_ids, nonempty,
        require, require_file, safe_path, string_list, validate_graph, validate_task,
    )

PLAN_PATH = ROOT / "delegation" / "ZRM_COMPLETION_PLAN.json"

def validate_states(tasks: list[dict[str, Any]], root: Path) -> None:
    """Enforce dependency, oracle, evidence, and delegation state rules."""
    by_id = {task["id"]: task for task in tasks}
    for task in tasks:
        task_id = task["id"]
        state = task["state"]
        incomplete = [dep for dep in task["deps"] if by_id[dep]["state"] != "complete"]
        if state == "blocked":
            require(
                bool(incomplete) or task["unresolved"] is not None,
                f"{task_id} blocked state needs an incomplete dependency or unresolved decision",
            )
        elif state == "delegable":
            require(not incomplete, f"{task_id} is delegable before dependencies complete")
            require(task["unresolved"] is None, f"{task_id} is delegable with unresolved behavior")
            require(task["oracle"]["status"] == "available", f"{task_id} needs an available oracle")
            require_file(root, task["decision"], f"{task_id}.decision")
            require_file(root, task["oracle"]["path"], f"{task_id}.oracle.path")
        elif state == "complete":
            require(not incomplete, f"{task_id} is complete before dependencies complete")
            for index, reference in enumerate(task["evidence"]):
                require_file(root, reference, f"{task_id}.evidence[{index}]")

        if task["oracle"]["status"] == "available":
            require_file(root, task["oracle"]["path"], f"{task_id}.oracle.path")


def validate_summaries(data: dict[str, Any], tasks: list[dict[str, Any]]) -> None:
    """Require handoff and safe-now summaries to match task state."""
    handoff = data.get("handoff")
    require(isinstance(handoff, dict), "handoff must be an object")
    ready = handoff.get("ready")
    require(isinstance(ready, bool), "handoff.ready must be boolean")
    required = string_list(handoff.get("required"), "handoff.required")
    by_id = {task["id"]: task for task in tasks}
    unknown = set(required) - set(by_id)
    require(not unknown, f"handoff references unknown tasks: {sorted(unknown)}")
    actually_ready = all(by_id[identifier]["state"] == "complete" for identifier in required)
    require(ready == actually_ready, "handoff readiness disagrees with closure-task completion")

    posture = data.get("posture")
    require(isinstance(posture, dict), "posture must be an object")
    require(posture.get("production_ready") is False, "plan v1 cannot claim production")
    require(
        posture.get("blanket_delegation_ready") == ready,
        "blanket delegation posture disagrees with handoff",
    )
    safe_now = string_list(posture.get("safe_now"), "posture.safe_now", allow_empty=True)
    actual_safe_now = [task["id"] for task in tasks if task["state"] == "delegable"]
    require(safe_now == actual_safe_now, "safe-now list does not match delegable tasks")


def load_task_files(data: dict[str, Any], root: Path = ROOT) -> list[dict[str, Any]]:
    """Load ordered task shards named by the plan index."""
    references = string_list(data.get("task_files"), "task_files")
    tasks: list[dict[str, Any]] = []
    for index, reference in enumerate(references):
        relative = safe_path(reference, f"task_files[{index}]")
        require(
            len(relative.parts) == 3
            and relative.parts[:2] == ("delegation", "tasks")
            and relative.suffix == ".json",
            f"task_files[{index}] must be JSON directly beneath delegation/tasks/",
        )
        require_file(root, reference, f"task_files[{index}]")
        try:
            payload = json.loads((root / relative).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise DelegationPlanError(f"cannot load task shard {reference}: {error}") from error
        require(isinstance(payload, list) and bool(payload), f"{reference} must contain tasks")
        require(all(isinstance(task, dict) for task in payload), f"{reference} has invalid tasks")
        tasks.extend(task for task in payload if isinstance(task, dict))
    return tasks


def validate_plan(data: dict[str, Any], tasks: list[dict[str, Any]], root: Path = ROOT) -> None:
    """Validate the complete plan against repository contracts and evidence."""
    require(data.get("schema") == "zrm/completion-delegation-plan/v1", "unexpected plan schema")
    require(data.get("version") == 1, "unexpected plan version")
    for field in ("date", "author", "drafting_assistance", "status"):
        nonempty(data.get(field), field)

    require(
        data.get("review_policy")
        == {
            "class_c_e_merge": "human_only",
            "class_c_e_independent": True,
            "class_d_e_authority_review": True,
            "oracle": "implementation_independent",
        },
        "review policy must preserve the exact human and independent boundary",
    )
    contract = data.get("task_contract")
    require(isinstance(contract, dict), "task_contract must be an object")
    require(set(contract) == {"entry", "stop"}, "task_contract must contain entry and stop")
    string_list(contract.get("entry"), "task_contract.entry")
    string_list(contract.get("stop"), "task_contract.stop")

    require(bool(tasks), "tasks must be nonempty")

    cbc_ids = known_cbc_ids(root)
    sc_ids = known_sc_ids(root)
    for index, task in enumerate(tasks, start=1):
        validate_task(
            task,
            expected_id=f"ZRM-TASK-{index:03d}",
            cbc_ids=cbc_ids,
            sc_ids=sc_ids,
        )
    validate_graph(tasks)
    validate_states(tasks, root)
    validate_summaries(data, tasks)


def main() -> int:
    """Load and validate the repository delegation plan."""
    try:
        data = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        require(isinstance(data, dict), "delegation plan root must be an object")
        tasks = load_task_files(data, ROOT)
        validate_plan(data, tasks, ROOT)
    except (DelegationPlanError, json.JSONDecodeError, OSError) as error:
        print(f"delegation-plan check failed: {error}", file=sys.stderr)
        return 1
    safe_count = sum(task["state"] == "delegable" for task in tasks)
    print(
        "delegation-plan check passed: "
        f"{len(tasks)} tasks, acyclic dependencies, exact authority boundaries, "
        f"{safe_count} safe-now tasks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
