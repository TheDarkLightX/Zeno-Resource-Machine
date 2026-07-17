"""Focused tests for sparse, exactly covered four-column accounting."""

from __future__ import annotations

import unittest

from reference_models.accounting_aggregate_v1 import (
    MODEL_MAX_FRAMED_HASH_LIST_ITEMS,
    MODEL_U128_MAX,
    MODEL_U256_MAX,
    MODEL_U32_MAX,
    AccountingAggregateRowV1,
    AccountingAggregateV1,
    AccountingBranchV1,
    AccountingCoverageManifestV1,
    AccountingDimensionV1,
    AccountingEntryV1,
    AccountingLeafV1,
    AccountingManifestV1,
    AccountingModelError,
    AggregateBoundsV1,
    LeafCoverageV1,
    MonotoneFlowV1,
    OpenedLeafRowV1,
    SignedDeltaV1,
    admit_external_manifest,
    admit_material_accounting_row,
    all_ordered_trees,
    all_tree_results_agree,
    checked_signed_add,
    fold_manifest,
    fold_tree,
    framed_hash_list_payload_bytes,
    has_nonempty_segment_carrier,
    is_actual_state_noop,
    resource_only_projection,
    signed_left_fold3,
    signed_right_fold3,
)
from reference_models.accounting_aggregate_v1_explorer import explore


DIM_A = AccountingDimensionV1("resource:a", "atoms:a")
DIM_B = AccountingDimensionV1("resource:b", "atoms:b")
DIM_C = AccountingDimensionV1("resource:c", "atoms:c")


def row(
    consumed: int,
    created: int,
    mint: int,
    burn: int,
    dimension: AccountingDimensionV1 = DIM_A,
) -> AccountingAggregateRowV1:
    return AccountingAggregateRowV1.from_columns(
        dimension,
        consumed_atoms=consumed,
        created_atoms=created,
        authorized_mint_atoms=mint,
        authorized_burn_atoms=burn,
    )


def diagonal_row(
    debit: int,
    credit: int,
    dimension: AccountingDimensionV1 = DIM_A,
) -> AccountingAggregateRowV1:
    flow = MonotoneFlowV1(debit, credit)
    return AccountingAggregateRowV1(dimension, flow, flow)


def opened(
    provenance_id: str, value: AccountingAggregateRowV1
) -> OpenedLeafRowV1:
    return OpenedLeafRowV1(provenance_id, value)


def leaf(
    bounds: AggregateBoundsV1,
    value: AccountingAggregateRowV1,
    provenance_id: str = "leaf-row:a",
) -> AccountingAggregateV1:
    return AccountingAggregateV1.leaf_from_canonical_opened_rows(
        bounds, (opened(provenance_id, value),)
    )


class StrictCanonicalBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bounds = AggregateBoundsV1(10, 4, 40)
        self.first = opened("leaf-row:a", row(2, 5, 3, 0, DIM_A))
        self.second = opened("leaf-row:b", row(7, 1, 0, 6, DIM_B))

    def test_untrusted_leaf_constructor_requires_precanonical_order(self) -> None:
        with self.assertRaisesRegex(AccountingModelError, "must be sorted"):
            AccountingAggregateV1.leaf_from_canonical_opened_rows(
                self.bounds, (self.second, self.first)
            )

    def test_trusted_leaf_builder_may_sort_authoritative_facts(self) -> None:
        value = AccountingAggregateV1.leaf_from_trusted_opened_rows(
            self.bounds, (self.second, self.first)
        )
        self.assertEqual(
            tuple(candidate.dimension for candidate in value.rows),
            (DIM_A, DIM_B),
        )
        self.assertEqual(
            value.coverage_manifest.leaves[0].dimensions,
            (DIM_A, DIM_B),
        )

    def test_strict_and_trusted_paths_both_reject_duplicate_dimensions(self) -> None:
        duplicate = opened("leaf-row:a-duplicate", row(1, 1, 0, 0, DIM_A))
        with self.assertRaisesRegex(AccountingModelError, "dimensions must be unique"):
            AccountingAggregateV1.leaf_from_canonical_opened_rows(
                self.bounds, (self.first, duplicate)
            )
        with self.assertRaisesRegex(AccountingModelError, "input must be unique"):
            AccountingAggregateV1.leaf_from_trusted_opened_rows(
                self.bounds, (duplicate, self.first)
            )

    def test_provenance_identity_is_exact_and_unique_within_a_leaf(self) -> None:
        same_provenance = opened("leaf-row:a", row(1, 1, 0, 0, DIM_B))
        with self.assertRaisesRegex(AccountingModelError, "provenance IDs"):
            AccountingAggregateV1.leaf_from_canonical_opened_rows(
                self.bounds, (self.first, same_provenance)
            )
        with self.assertRaisesRegex(AccountingModelError, "exact ASCII text"):
            OpenedLeafRowV1("", row(1, 1, 0, 0))

    def test_strict_aggregate_constructor_rejects_unsorted_material_rows(self) -> None:
        coverage = AccountingCoverageManifestV1(
            (LeafCoverageV1((self.first, self.second)),)
        )
        with self.assertRaisesRegex(AccountingModelError, "canonically sorted"):
            AccountingAggregateV1.from_canonical_material_rows(
                self.bounds,
                coverage,
                (self.second.row, self.first.row),
            )

    def test_trusted_aggregate_builder_sorts_but_does_not_change_totals(self) -> None:
        coverage = AccountingCoverageManifestV1(
            (LeafCoverageV1((self.first, self.second)),)
        )
        value = AccountingAggregateV1.from_trusted_derived_rows(
            self.bounds,
            coverage,
            (self.second.row, self.first.row),
        )
        self.assertEqual(tuple(candidate.dimension for candidate in value.rows), (DIM_A, DIM_B))

    def test_same_dimension_wrong_total_rejects_despite_valid_conservation(self) -> None:
        occurrence = opened("leaf-row:a", row(1, 1, 0, 0, DIM_A))
        coverage = AccountingCoverageManifestV1((LeafCoverageV1((occurrence,)),))
        forged = row(2, 2, 0, 0, DIM_A)
        with self.assertRaisesRegex(AccountingModelError, "exact opened leaf-column"):
            AccountingAggregateV1.from_canonical_material_rows(
                self.bounds, coverage, (forged,)
            )

    def test_material_row_without_exact_opened_columns_rejects(self) -> None:
        coverage = AccountingCoverageManifestV1((LeafCoverageV1(()),))
        with self.assertRaisesRegex(AccountingModelError, "lacks an opened"):
            AccountingAggregateV1.from_canonical_material_rows(
                self.bounds, coverage, (row(1, 1, 0, 0),)
            )


class SparseMapAndCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bounds = AggregateBoundsV1(10, 4, 40)

    def test_disjoint_support_merge_is_exact_sorted_union(self) -> None:
        left = leaf(self.bounds, row(3, 3, 0, 0, DIM_A), "leaf-row:a")
        right = leaf(self.bounds, row(5, 5, 0, 0, DIM_B), "leaf-row:b")
        merged = left.checked_merge(right)
        self.assertIsNotNone(merged)
        assert merged is not None
        self.assertEqual(tuple(candidate.dimension for candidate in merged.rows), (DIM_A, DIM_B))
        self.assertEqual(merged.row(DIM_A).consumed_atoms, 3)
        self.assertEqual(merged.row(DIM_B).consumed_atoms, 5)
        self.assertEqual(merged.coverage_manifest.leaf_count, 2)
        self.assertEqual(
            tuple(leaf.dimensions for leaf in merged.coverage_manifest.leaves),
            ((DIM_A,), (DIM_B,)),
        )

    def test_overlapping_support_adds_exact_four_columns(self) -> None:
        left = leaf(self.bounds, row(3, 5, 2, 0), "leaf-row:left")
        right = leaf(self.bounds, row(4, 1, 0, 3), "leaf-row:right")
        merged = left.checked_merge(right)
        self.assertIsNotNone(merged)
        assert merged is not None
        self.assertEqual(len(merged.rows), 1)
        self.assertEqual(
            merged.rows[0].canonical_payload(),
            row(7, 6, 2, 3).canonical_payload(),
        )

    def test_canonical_row_payload_uses_algebraic_abi_column_order(self) -> None:
        payload = row(7, 6, 2, 3).canonical_payload()
        self.assertEqual(
            tuple(payload),
            (
                "resource_kind_id",
                "unit_id",
                "consumed_atoms",
                "created_atoms",
                "authorized_burn_atoms",
                "authorized_mint_atoms",
            ),
        )

    def test_disjoint_support_all_catalan_trees_agree(self) -> None:
        values = (
            leaf(self.bounds, row(1, 1, 0, 0, DIM_A), "leaf-row:a"),
            leaf(self.bounds, row(2, 2, 0, 0, DIM_B), "leaf-row:b"),
            leaf(self.bounds, row(3, 3, 0, 0, DIM_C), "leaf-row:c"),
        )
        entries = tuple(
            AccountingEntryV1(f"entry-{index}", value)
            for index, value in enumerate(values)
        )
        manifest = AccountingManifestV1(entries)
        self.assertTrue(all_tree_results_agree(manifest))
        result = fold_manifest(manifest)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(
            tuple(candidate.dimension for candidate in result.rows),
            (DIM_A, DIM_B, DIM_C),
        )
        self.assertEqual(len(result.coverage_manifest.leaves), 3)

    def test_all_four_zero_leaf_is_coverage_only_for_compatibility(self) -> None:
        zero_occurrence = opened("existing-leaf-row:zero", row(0, 0, 0, 0))
        value = AccountingAggregateV1.leaf_from_canonical_opened_rows(
            self.bounds, (zero_occurrence,)
        )
        self.assertEqual(value.rows, ())
        self.assertEqual(value.coverage_manifest.leaf_count, 1)
        self.assertEqual(value.coverage_manifest.leaves[0].occurrences, (zero_occurrence,))
        self.assertEqual(value.coverage_manifest.leaves[0].dimensions, (DIM_A,))
        self.assertTrue(has_nonempty_segment_carrier(value))

    def test_all_zero_row_cannot_be_materialized_directly(self) -> None:
        zero_occurrence = opened("existing-leaf-row:zero", row(0, 0, 0, 0))
        coverage = AccountingCoverageManifestV1(
            (LeafCoverageV1((zero_occurrence,)),)
        )
        with self.assertRaisesRegex(AccountingModelError, "coverage occurrences"):
            AccountingAggregateV1.from_canonical_material_rows(
                self.bounds, coverage, (zero_occurrence.row,)
            )

    def test_zero_opened_row_occurrence_survives_merge_without_sparse_row(self) -> None:
        zero_leaf = AccountingAggregateV1.leaf_from_canonical_opened_rows(
            self.bounds,
            (opened("existing-leaf-row:zero", row(0, 0, 0, 0, DIM_A)),),
        )
        material_leaf = leaf(
            self.bounds,
            row(2, 2, 0, 0, DIM_B),
            "existing-leaf-row:material",
        )
        merged = zero_leaf.checked_merge(material_leaf)
        self.assertIsNotNone(merged)
        assert merged is not None
        self.assertEqual(tuple(candidate.dimension for candidate in merged.rows), (DIM_B,))
        self.assertEqual(
            tuple(leaf.dimensions for leaf in merged.coverage_manifest.leaves),
            ((DIM_A,), (DIM_B,)),
        )

    def test_internal_empty_map_identity_has_zero_leaves(self) -> None:
        identity = AccountingAggregateV1.zero(self.bounds)
        value = leaf(self.bounds, row(2, 2, 0, 0))
        self.assertEqual(identity.rows, ())
        self.assertEqual(identity.coverage_manifest.leaves, ())
        self.assertFalse(has_nonempty_segment_carrier(identity))
        self.assertEqual(identity.checked_merge(value), value)


class FourColumnRefinementTests(unittest.TestCase):
    def test_row_enforces_resource_net_equals_authority_net(self) -> None:
        with self.assertRaisesRegex(AccountingModelError, "conservation"):
            row(consumed=3, created=5, mint=1, burn=0)
        valid = row(consumed=3, created=5, mint=2, burn=0)
        self.assertEqual(valid.resource_flow.net, 2)
        self.assertEqual(valid.authority_flow.net, 2)

    def test_ordinary_transfer_has_no_authority_flow(self) -> None:
        transfer = row(consumed=7, created=7, mint=0, burn=0)
        self.assertEqual(transfer.resource_flow, MonotoneFlowV1(7, 7))
        self.assertEqual(transfer.authority_flow, MonotoneFlowV1(0, 0))

    def test_resource_only_projection_is_not_lossless(self) -> None:
        minimal = row(consumed=3, created=5, mint=2, burn=0)
        cycled = row(consumed=3, created=5, mint=3, burn=1)
        self.assertEqual(resource_only_projection(minimal), resource_only_projection(cycled))
        self.assertNotEqual(minimal, cycled)

    def test_zero_net_nonzero_row_remains_material(self) -> None:
        covered = row(consumed=2, created=2, mint=1, burn=1)
        self.assertEqual(covered.resource_flow.net, 0)
        self.assertEqual(covered.authority_flow.net, 0)
        self.assertTrue(admit_material_accounting_row(covered))


class PrimitiveBoundsAndCapacityTests(unittest.TestCase):
    def test_boolean_does_not_substitute_for_integer(self) -> None:
        with self.assertRaisesRegex(AccountingModelError, "exact integer"):
            MonotoneFlowV1(True, 0)  # type: ignore[arg-type]
        with self.assertRaisesRegex(AccountingModelError, "exact integer"):
            AggregateBoundsV1(True, 1, 1)  # type: ignore[arg-type]
        with self.assertRaisesRegex(AccountingModelError, "exact integer"):
            checked_signed_add(2, True, 0)  # type: ignore[arg-type]

    def test_u32_hash_frame_caps_list_item_count(self) -> None:
        self.assertEqual(MODEL_MAX_FRAMED_HASH_LIST_ITEMS, 134_217_727)
        self.assertEqual(
            framed_hash_list_payload_bytes(MODEL_MAX_FRAMED_HASH_LIST_ITEMS),
            4 + 32 * MODEL_MAX_FRAMED_HASH_LIST_ITEMS,
        )
        self.assertGreater(
            4 + 32 * (MODEL_MAX_FRAMED_HASH_LIST_ITEMS + 1),
            MODEL_U32_MAX,
        )
        with self.assertRaisesRegex(AccountingModelError, "payload capacity"):
            framed_hash_list_payload_bytes(MODEL_MAX_FRAMED_HASH_LIST_ITEMS + 1)
        AggregateBoundsV1(1, MODEL_U32_MAX, MODEL_U256_MAX)
        with self.assertRaisesRegex(AccountingModelError, "u32::MAX"):
            AggregateBoundsV1(1, MODEL_U32_MAX + 1, MODEL_U256_MAX)

    def test_leaf_dimension_and_coverage_counts_have_independent_bounds(self) -> None:
        protocol = AggregateBoundsV1.protocol()
        self.assertEqual(protocol.max_leaf_count, MODEL_U32_MAX)
        self.assertEqual(
            protocol.max_dimension_count, MODEL_MAX_FRAMED_HASH_LIST_ITEMS
        )
        self.assertEqual(
            protocol.max_coverage_entry_count,
            MODEL_MAX_FRAMED_HASH_LIST_ITEMS,
        )
        with self.assertRaisesRegex(AccountingModelError, "dimension count"):
            AggregateBoundsV1(
                1,
                MODEL_U32_MAX,
                MODEL_U256_MAX,
                MODEL_MAX_FRAMED_HASH_LIST_ITEMS + 1,
                MODEL_MAX_FRAMED_HASH_LIST_ITEMS,
            )
        with self.assertRaisesRegex(AccountingModelError, "coverage entry"):
            AggregateBoundsV1(
                1,
                MODEL_U32_MAX,
                MODEL_U256_MAX,
                MODEL_MAX_FRAMED_HASH_LIST_ITEMS,
                MODEL_MAX_FRAMED_HASH_LIST_ITEMS + 1,
            )

        rowless_bounds = AggregateBoundsV1(1, MODEL_U32_MAX, 1, 1, 1)
        rowless = AccountingAggregateV1.leaf_from_canonical_opened_rows(
            rowless_bounds, ()
        )
        self.assertEqual(rowless.leaf_count, 1)
        self.assertEqual(rowless.rows, ())
        with self.assertRaisesRegex(AccountingModelError, "dimension count"):
            AggregateBoundsV1(
                1,
                MODEL_U32_MAX,
                1,
                0,
                1,
            )
        with self.assertRaisesRegex(AccountingModelError, "coverage entry count"):
            AggregateBoundsV1(
                1,
                MODEL_U32_MAX,
                1,
                1,
                0,
            )

    def test_opened_leaf_and_aggregate_bounds_fail_closed(self) -> None:
        bounds = AggregateBoundsV1(2, 4, 8)
        with self.assertRaisesRegex(AccountingModelError, "per-leaf"):
            leaf(bounds, diagonal_row(3, 0))
        first = leaf(bounds, diagonal_row(2, 0), "leaf-row:first")
        second = leaf(bounds, diagonal_row(2, 0), "leaf-row:second")
        merged = first.checked_merge(second)
        self.assertIsNotNone(merged)
        assert merged is not None
        self.assertEqual(merged.rows[0].resource_flow.debit_total, 4)

    def test_checked_merge_rejects_aggregate_cap_overflow(self) -> None:
        bounds = AggregateBoundsV1(2, 2, 2)
        left = leaf(bounds, diagonal_row(2, 0), "leaf-row:left")
        right = leaf(bounds, diagonal_row(1, 0), "leaf-row:right")
        self.assertIsNone(left.checked_merge(right))

    def test_checked_merge_returns_none_for_parent_profile_caps(self) -> None:
        dimension_bounds = AggregateBoundsV1(1, 2, 2, 1, 2)
        dimension_left = leaf(
            dimension_bounds,
            diagonal_row(1, 1, DIM_A),
            "leaf-row:dimension-left",
        )
        dimension_right = leaf(
            dimension_bounds,
            diagonal_row(1, 1, DIM_B),
            "leaf-row:dimension-right",
        )
        self.assertIsNone(dimension_left.checked_merge(dimension_right))
        self.assertIsNone(dimension_right.checked_merge(dimension_left))

        coverage_bounds = AggregateBoundsV1(1, 2, 2, 1, 1)
        coverage_left = leaf(
            coverage_bounds,
            diagonal_row(1, 1),
            "leaf-row:coverage-left",
        )
        coverage_right = leaf(
            coverage_bounds,
            diagonal_row(1, 1),
            "leaf-row:coverage-right",
        )
        self.assertIsNone(coverage_left.checked_merge(coverage_right))
        self.assertIsNone(coverage_right.checked_merge(coverage_left))

    def test_two_max_u128_leaves_fit_wide_aggregate(self) -> None:
        bounds = AggregateBoundsV1.protocol()
        maximum = row(
            MODEL_U128_MAX,
            MODEL_U128_MAX,
            MODEL_U128_MAX,
            MODEL_U128_MAX,
        )
        value = leaf(bounds, maximum, "leaf-row:max")
        merged = value.checked_merge(value)
        self.assertIsNotNone(merged)
        assert merged is not None
        self.assertEqual(merged.rows[0].consumed_atoms, 2 * MODEL_U128_MAX)
        self.assertIsNone(
            maximum.resource_flow.checked_merge(maximum.resource_flow, MODEL_U128_MAX)
        )

    def test_theoretical_u32_and_framed_protocol_totals_fit_u256(self) -> None:
        theoretical = MODEL_U32_MAX * MODEL_U128_MAX
        self.assertEqual(theoretical.bit_length(), 160)
        self.assertLess(theoretical, MODEL_U256_MAX)
        self.assertEqual(
            AggregateBoundsV1.protocol().allowed_limb_total(
                MODEL_U32_MAX
            ),
            theoretical,
        )


class DefinednessAndManifestTests(unittest.TestCase):
    def test_signed_checked_add_definedness_depends_on_parenthesization(self) -> None:
        self.assertIsNone(signed_left_fold3(127, 127, 1, -1))
        self.assertEqual(signed_right_fold3(127, 127, 1, -1), 127)

    def test_lifted_counterexample_has_tree_independent_result(self) -> None:
        def lifted(bound: int) -> AccountingManifestV1:
            bounds = AggregateBoundsV1(bound, 3, bound)
            entries = tuple(
                AccountingEntryV1(
                    f"entry-{index}",
                    AccountingAggregateV1.leaf_from_trusted_signed_deltas(
                        bounds, (SignedDeltaV1(DIM_A, delta),)
                    ),
                )
                for index, delta in enumerate((127, 1, -1))
            )
            return AccountingManifestV1(entries)

        bounded_127 = lifted(127)
        self.assertTrue(all_tree_results_agree(bounded_127))
        self.assertIsNone(fold_manifest(bounded_127))
        bounded_128 = lifted(128)
        self.assertTrue(all_tree_results_agree(bounded_128))
        result = fold_manifest(bounded_128)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.row(DIM_A).resource_flow, MonotoneFlowV1(1, 128))

    def test_profile_caps_reject_uniformly_for_every_ordered_tree(self) -> None:
        dimension_bounds = AggregateBoundsV1(1, 3, 3, 2, 3)
        dimension_entries = tuple(
            AccountingEntryV1(
                f"dimension-entry-{index}",
                leaf(
                    dimension_bounds,
                    diagonal_row(1, 1, dimension),
                    f"leaf-row:dimension-{index}",
                ),
            )
            for index, dimension in enumerate((DIM_A, DIM_B, DIM_C))
        )
        coverage_bounds = AggregateBoundsV1(1, 3, 3, 1, 2)
        coverage_entries = tuple(
            AccountingEntryV1(
                f"coverage-entry-{index}",
                leaf(
                    coverage_bounds,
                    diagonal_row(1, 1),
                    f"leaf-row:coverage-{index}",
                ),
            )
            for index in range(3)
        )

        for entries in (dimension_entries, coverage_entries):
            manifest = AccountingManifestV1(entries)
            self.assertIsNone(fold_manifest(manifest))
            results = tuple(
                fold_tree(manifest, tree) for tree in all_ordered_trees(entries)
            )
            self.assertEqual(results, (None, None))
            self.assertTrue(all_tree_results_agree(manifest))

    def test_tree_permutation_omission_and_duplicate_reject(self) -> None:
        bounds = AggregateBoundsV1(3, 3, 9)
        entries = tuple(
            AccountingEntryV1(
                f"entry-{index}",
                leaf(bounds, diagonal_row(1, 0), f"leaf-row:{index}"),
            )
            for index in range(3)
        )
        manifest = AccountingManifestV1(entries)
        mutants = (
            AccountingBranchV1(
                AccountingLeafV1(entries[1]),
                AccountingBranchV1(AccountingLeafV1(entries[0]), AccountingLeafV1(entries[2])),
            ),
            AccountingBranchV1(AccountingLeafV1(entries[0]), AccountingLeafV1(entries[0])),
            AccountingBranchV1(AccountingLeafV1(entries[0]), AccountingLeafV1(entries[1])),
        )
        for mutant in mutants:
            with self.assertRaisesRegex(AccountingModelError, "ordered manifest"):
                fold_tree(manifest, mutant)

    def test_nonempty_empty_accounting_segment_is_not_a_state_noop_claim(self) -> None:
        bounds = AggregateBoundsV1(2, 1, 2)
        empty_support = AccountingAggregateV1.leaf_from_canonical_opened_rows(
            bounds, ()
        )
        manifest = AccountingManifestV1(
            (AccountingEntryV1("empty-support", empty_support),)
        )
        self.assertTrue(admit_external_manifest(manifest))
        self.assertFalse(is_actual_state_noop("state:before", "state:after"))
        self.assertTrue(is_actual_state_noop("state:same", "state:same"))


class BoundedExplorerTests(unittest.TestCase):
    def test_explorer_counts_and_mutants_are_stable(self) -> None:
        result = explore()
        signed = result["signed_checked_add_mutant"]
        self.assertEqual(signed["triples"], 125)
        self.assertEqual(signed["parenthesization_mismatches"], 20)

        trees = result["monotone_sparse_two_flow_trees"]
        self.assertEqual(trees["manifests"], 6561)
        self.assertEqual(trees["ordered_binary_trees_per_manifest"], 5)
        self.assertEqual(trees["tree_evaluations"], 32805)
        self.assertEqual(trees["defined_manifests"], 225)
        self.assertEqual(trees["undefined_manifests"], 6336)
        self.assertEqual(trees["value_or_definedness_disagreements"], 0)

        sparse = result["sparse_support_union"]
        self.assertEqual(sparse["left_support"], 1)
        self.assertEqual(sparse["right_support"], 1)
        self.assertEqual(sparse["union_support"], 2)
        self.assertEqual(sparse["coverage_leaf_count"], 2)

        binding = result["ordered_manifest_binding"]
        self.assertEqual(binding["mutants"], 3)
        self.assertEqual(binding["rejected_mutants"], 3)

        identity = result["identity_coverage_and_materiality"]
        self.assertEqual(identity["coverage_only_zero_rows"], 1)
        self.assertEqual(identity["zero_opened_row_material_support"], 0)
        self.assertEqual(identity["zero_opened_row_coverage_occurrences"], 1)
        self.assertTrue(identity["zero_opened_row_manifest_admitted"])
        self.assertFalse(identity["internal_identity_has_nonempty_carrier"])


if __name__ == "__main__":
    unittest.main()
