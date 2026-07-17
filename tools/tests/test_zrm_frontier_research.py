"""Tests for the fail-closed ZRM frontier research packet checker."""

from __future__ import annotations

import copy
import unittest

from tools.check_zrm_frontier_research import (
    FrontierPacketError,
    _reject_duplicate_json_keys,
    json_exact_equal,
    load_json,
    PACKET,
    validate_graph,
    validate_hypotheses,
    validate_manifest,
    validate_packet,
    validate_sources,
    validate_experiments,
    validate_esso_observation,
    validate_lean_observation,
    validate_research_kernel_summary,
)


class FrontierResearchPacketTests(unittest.TestCase):
    def test_repository_packet_passes(self) -> None:
        counts = validate_packet()
        self.assertEqual(counts["hypotheses"], 24)
        self.assertGreaterEqual(counts["sources"], 50)
        self.assertGreaterEqual(counts["graph_edges"], 50)

    def test_duplicate_hypothesis_id_rejects(self) -> None:
        sources = load_json(PACKET / "source_ledger.json")
        experiments = load_json(PACKET / "experiments.json")
        hypotheses = load_json(PACKET / "hypotheses.json")
        source_ids = validate_sources(sources)
        experiment_ids, _ = validate_experiments(experiments)
        mutant = copy.deepcopy(hypotheses)
        mutant["hypotheses"][1]["id"] = mutant["hypotheses"][0]["id"]
        with self.assertRaisesRegex(FrontierPacketError, "IDs must be unique"):
            validate_hypotheses(mutant, source_ids, experiment_ids)

    def test_dangling_graph_endpoint_rejects(self) -> None:
        sources = load_json(PACKET / "source_ledger.json")
        experiments = load_json(PACKET / "experiments.json")
        hypotheses = load_json(PACKET / "hypotheses.json")
        graph = load_json(PACKET / "knowledge_graph.json")
        source_ids = validate_sources(sources)
        experiment_ids, _ = validate_experiments(experiments)
        hypothesis_ids, _ = validate_hypotheses(
            hypotheses, source_ids, experiment_ids
        )
        mutant = copy.deepcopy(graph)
        mutant["edges"][0]["to"] = "ZRM-H-DOES-NOT-EXIST"
        with self.assertRaisesRegex(FrontierPacketError, "unknown target endpoint"):
            validate_graph(mutant, source_ids, hypothesis_ids, experiment_ids)

    def test_stale_manifest_digest_rejects(self) -> None:
        manifest = load_json(PACKET / "manifest.json")
        mutant = copy.deepcopy(manifest)
        mutant["files"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(FrontierPacketError, "bytes or digests are stale"):
            validate_manifest(mutant)

    def test_scalar_hypothesis_confidence_rejects(self) -> None:
        sources = load_json(PACKET / "source_ledger.json")
        experiments = load_json(PACKET / "experiments.json")
        hypotheses = load_json(PACKET / "hypotheses.json")
        source_ids = validate_sources(sources)
        experiment_ids, _ = validate_experiments(experiments)
        mutant = copy.deepcopy(hypotheses)
        mutant["hypotheses"][0]["confidence"] = 0.99
        with self.assertRaisesRegex(FrontierPacketError, "scalar confidence"):
            validate_hypotheses(mutant, source_ids, experiment_ids)

    def test_esso_observation_cannot_claim_replayability(self) -> None:
        observation = load_json(
            PACKET / "evidence/esso-zrm-semantic-check-v2.json"
        )
        mutant = copy.deepcopy(observation)
        mutant["replayable_from_repository"] = True
        with self.assertRaisesRegex(FrontierPacketError, "non-replayable"):
            validate_esso_observation(mutant)

    def test_base_artifact_integrity_mismatch_rejects(self) -> None:
        experiments = load_json(PACKET / "experiments.json")
        mutant = copy.deepcopy(experiments)
        mutant["experiments"][0]["base_artifact_integrity"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(FrontierPacketError, "base artifact identity"):
            validate_experiments(mutant)

    def test_json_equality_is_exact_across_python_numeric_types(self) -> None:
        self.assertFalse(json_exact_equal({"value": True}, {"value": 1}))
        self.assertFalse(json_exact_equal({"value": 7}, {"value": 7.0}))

    def test_boolean_hypothesis_rank_rejects(self) -> None:
        sources = load_json(PACKET / "source_ledger.json")
        experiments = load_json(PACKET / "experiments.json")
        hypotheses = load_json(PACKET / "hypotheses.json")
        source_ids = validate_sources(sources)
        experiment_ids, _ = validate_experiments(experiments)
        mutant = copy.deepcopy(hypotheses)
        mutant["hypotheses"][0]["rank"] = True
        with self.assertRaisesRegex(FrontierPacketError, "exact integers"):
            validate_hypotheses(mutant, source_ids, experiment_ids)

    def test_float_manifest_byte_count_rejects(self) -> None:
        manifest = load_json(PACKET / "manifest.json")
        mutant = copy.deepcopy(manifest)
        mutant["files"][0]["bytes"] = float(mutant["files"][0]["bytes"])
        with self.assertRaisesRegex(FrontierPacketError, "nonnegative exact integer"):
            validate_manifest(mutant)

    def test_esso_numeric_type_substitution_rejects(self) -> None:
        observation = load_json(
            PACKET / "evidence/esso-zrm-semantic-check-v2.json"
        )
        mutant = copy.deepcopy(observation)
        mutant["mutant_observation_summary"]["observed_killed"] = 14.0
        with self.assertRaisesRegex(FrontierPacketError, "summary mismatch"):
            validate_esso_observation(mutant)

    def test_lean_job_numeric_type_substitution_rejects(self) -> None:
        observation = load_json(PACKET / "evidence/lean-frontier-v2.json")
        mutant = copy.deepcopy(observation)
        mutant["lake_jobs"] = 7.0
        with self.assertRaisesRegex(FrontierPacketError, "job count"):
            validate_lean_observation(mutant)

    def test_research_kernel_count_type_substitution_rejects(self) -> None:
        summary = load_json(
            PACKET / "evidence/research-kernel-runs-v1.json"
        )
        mutant = copy.deepcopy(summary)
        mutant["runs"][0]["atoms"] = 22.0
        with self.assertRaisesRegex(FrontierPacketError, "identities or counts"):
            validate_research_kernel_summary(mutant)

    def test_duplicate_json_object_key_rejects(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
            _reject_duplicate_json_keys([("same", 1), ("same", 2)])

    def test_unexpected_manifest_metadata_rejects(self) -> None:
        manifest = load_json(PACKET / "manifest.json")
        mutant = copy.deepcopy(manifest)
        mutant["unsigned_note"] = "not covered by the manifest"
        with self.assertRaisesRegex(FrontierPacketError, "top-level fields"):
            validate_manifest(mutant)


if __name__ == "__main__":
    unittest.main()
