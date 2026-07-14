"""Mutation tests for the ZRM accounting aggregate research packet checker."""

from __future__ import annotations

import copy
import unittest

from tools.check_zrm_accounting_research import (
    AccountingResearchError,
    PACKET,
    _reject_duplicate_keys,
    json_exact_equal,
    lean_placeholder_tokens,
    load_json,
    validate_esso,
    validate_evidence,
    validate_experiments,
    validate_graph,
    validate_hypotheses,
    validate_manifest,
    validate_morph,
    validate_packet,
    validate_receipt,
    validate_sources,
)


class AccountingResearchPacketTests(unittest.TestCase):
    def dependencies(self) -> tuple[set[str], set[str], set[str]]:
        source_ids = validate_sources(load_json(PACKET / "source_ledger.json"))
        experiment_ids, _ = validate_experiments(load_json(PACKET / "experiments.json"))
        hypothesis_ids = validate_hypotheses(
            load_json(PACKET / "hypotheses.json"), source_ids, experiment_ids
        )
        return source_ids, experiment_ids, hypothesis_ids

    def test_repository_packet_passes(self) -> None:
        counts = validate_packet()
        self.assertEqual(counts["sources"], 22)
        self.assertEqual(counts["hypotheses"], 20)
        self.assertEqual(counts["graph_nodes"], 74)
        self.assertEqual(counts["graph_edges"], 85)

    def test_duplicate_json_key_rejects(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
            _reject_duplicate_keys([("same", 1), ("same", 2)])

    def test_exact_json_equality_rejects_bool_integer_substitution(self) -> None:
        self.assertFalse(json_exact_equal({"value": True}, {"value": 1}))
        self.assertFalse(json_exact_equal({"value": 7.0}, {"value": 7}))

    def test_lean_placeholder_scanner_is_token_exact_and_comment_strict(self) -> None:
        source = "theorem sound : True := by trivial\n-- sorry\naxiomatic admitThing"
        self.assertEqual(lean_placeholder_tokens(source), ["sorry"])

    def test_unknown_hypothesis_source_rejects(self) -> None:
        source_ids, experiment_ids, _ = self.dependencies()
        mutant = copy.deepcopy(load_json(PACKET / "hypotheses.json"))
        mutant["hypotheses"][0]["source_ids"] = ["AAS-NOT-REAL"]
        with self.assertRaisesRegex(AccountingResearchError, "unknown source"):
            validate_hypotheses(mutant, source_ids, experiment_ids)

    def test_float_hypothesis_rank_rejects(self) -> None:
        source_ids, experiment_ids, _ = self.dependencies()
        mutant = copy.deepcopy(load_json(PACKET / "hypotheses.json"))
        mutant["hypotheses"][0]["rank"] = 20.0
        with self.assertRaisesRegex(AccountingResearchError, "exact integer"):
            validate_hypotheses(mutant, source_ids, experiment_ids)

    def test_dangling_graph_endpoint_rejects(self) -> None:
        source_ids, experiment_ids, hypothesis_ids = self.dependencies()
        mutant = copy.deepcopy(load_json(PACKET / "knowledge_graph.json"))
        mutant["edges"][0]["to"] = "c_not_real"
        with self.assertRaisesRegex(AccountingResearchError, "unknown target"):
            validate_graph(mutant, source_ids, hypothesis_ids, experiment_ids)

    def test_duplicate_graph_edge_rejects(self) -> None:
        source_ids, experiment_ids, hypothesis_ids = self.dependencies()
        mutant = copy.deepcopy(load_json(PACKET / "knowledge_graph.json"))
        mutant["edges"].append(copy.deepcopy(mutant["edges"][0]))
        with self.assertRaisesRegex(AccountingResearchError, "duplicate graph edge"):
            validate_graph(mutant, source_ids, hypothesis_ids, experiment_ids)

    def test_esso_cannot_claim_execution(self) -> None:
        mutant = copy.deepcopy(load_json(PACKET / "esso_campaign.json"))
        mutant["status"] = "passed"
        with self.assertRaisesRegex(AccountingResearchError, "overclaims"):
            validate_esso(mutant)

    def test_morph_cannot_claim_equivalence_validation(self) -> None:
        mutant = copy.deepcopy(load_json(PACKET / "morph_reformulations.json"))
        mutant["status"] = "validated_equivalences"
        with self.assertRaisesRegex(AccountingResearchError, "remain candidates"):
            validate_morph(mutant)

    def test_research_kernel_float_count_rejects(self) -> None:
        mutant = copy.deepcopy(load_json(PACKET / "research_kernel_receipt.json"))
        mutant["first_pass"]["mcp_calls"] = 78.0
        with self.assertRaisesRegex(AccountingResearchError, "exact integer"):
            validate_receipt(mutant, load_json(PACKET / "hypotheses.json"))

    def test_research_kernel_wrong_base_revision_rejects(self) -> None:
        mutant = copy.deepcopy(load_json(PACKET / "research_kernel_receipt.json"))
        mutant["base_revision"] = "0" * 40
        with self.assertRaisesRegex(AccountingResearchError, "base revision mismatch"):
            validate_receipt(mutant, load_json(PACKET / "hypotheses.json"))

    def test_research_kernel_too_few_promotions_rejects(self) -> None:
        mutant = copy.deepcopy(load_json(PACKET / "research_kernel_receipt.json"))
        mutant["evidence_pass"]["promoted_claim_ids"] = ["c_four_limb"]
        with self.assertRaisesRegex(AccountingResearchError, "too few"):
            validate_receipt(mutant, load_json(PACKET / "hypotheses.json"))

    def test_research_kernel_unknown_promotion_id_rejects(self) -> None:
        mutant = copy.deepcopy(load_json(PACKET / "research_kernel_receipt.json"))
        mutant["evidence_pass"]["promoted_claim_ids"][0] = "c_not_real"
        with self.assertRaisesRegex(AccountingResearchError, "unknown hypothesis"):
            validate_receipt(mutant, load_json(PACKET / "hypotheses.json"))

    def test_python_evidence_count_mutation_rejects(self) -> None:
        python_evidence = copy.deepcopy(load_json(PACKET / "evidence/python-model.json"))
        python_evidence["results"]["monotone_tree_evaluations"] = 32804
        graph = load_json(PACKET / "knowledge_graph.json")
        with self.assertRaisesRegex(AccountingResearchError, "exploration count"):
            validate_evidence(
                python_evidence,
                load_json(PACKET / "evidence/lean.json"),
                load_json(PACKET / "evidence/vectors.json"),
                load_json(PACKET / "evidence/packet-check.json"),
                {"nodes": len(graph["nodes"]), "edges": len(graph["edges"])},
            )

    def test_executed_missing_artifact_rejects(self) -> None:
        mutant = copy.deepcopy(load_json(PACKET / "experiments.json"))
        mutant["experiments"][0]["artifacts"] = ["not/a/real/file"]
        with self.assertRaisesRegex(AccountingResearchError, "artifact missing"):
            validate_experiments(mutant)

    def test_stale_manifest_digest_rejects(self) -> None:
        mutant = copy.deepcopy(load_json(PACKET / "manifest.json"))
        mutant["files"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(AccountingResearchError, "digests are stale"):
            validate_manifest(mutant)

    def test_manifest_metadata_injection_rejects(self) -> None:
        mutant = copy.deepcopy(load_json(PACKET / "manifest.json"))
        mutant["unsigned_note"] = "outside the digest set"
        with self.assertRaisesRegex(AccountingResearchError, "unexpected top-level"):
            validate_manifest(mutant)


if __name__ == "__main__":
    unittest.main()
