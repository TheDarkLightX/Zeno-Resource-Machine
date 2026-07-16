"""Unit tests for the ZRM completion and delegation-plan gate."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.check_delegation_plan import DelegationPlanError, load_task_files, validate_plan


class DelegationPlanTests(unittest.TestCase):
    """Exercise fail-closed task, dependency, authority, and handoff rules."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repository_root = Path(__file__).resolve().parents[2]
        plan_path = cls.repository_root / "delegation" / "ZRM_COMPLETION_PLAN.json"
        cls.plan = json.loads(plan_path.read_text(encoding="utf-8"))
        cls.tasks = load_task_files(cls.plan, cls.repository_root)

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        matrix = {"obligations": [{"id": f"ZRM-CBC-{number:03d}"} for number in range(1, 56)]}
        (self.root / "CONFORMANCE_MATRIX.json").write_text(json.dumps(matrix), encoding="utf-8")
        contracts = self.root / "contracts"
        contracts.mkdir()
        for number in range(1, 14):
            (contracts / f"ZRM-SC-{number:03d}.md").write_text(
                f"# ZRM-SC-{number:03d}\n", encoding="utf-8"
            )
        self._write("docs/AUTHORITY_MAP.md", "# authority map\n")
        self._write("vectors/resource_wire_v1.json", "{}\n")
        self._write("rfcs/RFC-0003-security-review-api-quarantine.md", "# RFC\n")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write(self, relative_path: str, content: str) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def candidate(self) -> tuple[dict[str, object], list[dict[str, object]]]:
        return copy.deepcopy(self.plan), copy.deepcopy(self.tasks)

    def reject(self, plan: dict[str, object], tasks: list[dict[str, object]]) -> None:
        with self.assertRaises(DelegationPlanError):
            validate_plan(plan, tasks, self.root)

    def test_repository_plan_is_valid(self) -> None:
        plan, tasks = self.candidate()
        validate_plan(plan, tasks, self.root)

    def test_authority_boundary_must_be_exactly_one(self) -> None:
        plan, tasks = self.candidate()
        tasks[0]["boundary"] = "policy_activation,validation_context"
        self.reject(plan, tasks)

    def test_dependency_cycle_is_rejected(self) -> None:
        plan, tasks = self.candidate()
        tasks[0]["deps"] = ["ZRM-TASK-002"]
        self.reject(plan, tasks)

    def test_unknown_cbc_is_rejected(self) -> None:
        plan, tasks = self.candidate()
        tasks[0]["cbc"] = ["ZRM-CBC-999"]
        self.reject(plan, tasks)

    def test_delegable_task_cannot_retain_unresolved_behavior(self) -> None:
        plan, tasks = self.candidate()
        tasks[21]["unresolved"] = "choose new accepted behavior"
        self.reject(plan, tasks)

    def test_delegable_task_requires_completed_dependencies(self) -> None:
        plan, tasks = self.candidate()
        tasks[21]["deps"] = ["ZRM-TASK-001"]
        self.reject(plan, tasks)

    def test_delegable_task_requires_available_oracle(self) -> None:
        plan, tasks = self.candidate()
        tasks[21]["oracle"]["status"] = "planned"
        self.reject(plan, tasks)

    def test_available_oracle_must_exist(self) -> None:
        plan, tasks = self.candidate()
        tasks[21]["oracle"]["path"] = "missing/oracle.json"
        self.reject(plan, tasks)

    def test_review_policy_cannot_be_weakened(self) -> None:
        plan, tasks = self.candidate()
        plan["review_policy"]["class_c_e_merge"] = "agent"
        self.reject(plan, tasks)

    def test_handoff_cannot_be_declared_early(self) -> None:
        plan, tasks = self.candidate()
        plan["handoff"]["ready"] = True
        plan["posture"]["blanket_delegation_ready"] = True
        self.reject(plan, tasks)

    def test_complete_task_requires_existing_evidence(self) -> None:
        plan, tasks = self.candidate()
        tasks[0]["state"] = "complete"
        tasks[0]["unresolved"] = None
        tasks[0]["evidence"] = ["missing/evidence.json"]
        self.reject(plan, tasks)

    def test_repository_path_traversal_is_rejected(self) -> None:
        plan, tasks = self.candidate()
        tasks[0]["scope"] = "../private/source.rs"
        self.reject(plan, tasks)

    def test_safe_now_list_must_match_delegable_tasks(self) -> None:
        plan, tasks = self.candidate()
        plan["posture"]["safe_now"] = []
        self.reject(plan, tasks)


if __name__ == "__main__":
    unittest.main()
