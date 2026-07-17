"""Deterministic bounded exploration of sparse four-column aggregation."""

from __future__ import annotations

import argparse
import itertools
import json

from reference_models.accounting_aggregate_v1 import (
    MODEL_MAX_FRAMED_HASH_LIST_ITEMS,
    MODEL_U128_MAX,
    MODEL_U256_MAX,
    MODEL_U32_MAX,
    AccountingAggregateRowV1,
    AccountingAggregateV1,
    AccountingBranchV1,
    AccountingDimensionV1,
    AccountingEntryV1,
    AccountingLeafV1,
    AccountingManifestV1,
    AccountingModelError,
    AggregateBoundsV1,
    MonotoneFlowV1,
    OpenedLeafRowV1,
    SignedDeltaV1,
    admit_external_manifest,
    admit_material_accounting_row,
    all_ordered_trees,
    fold_manifest,
    fold_tree,
    framed_hash_list_payload_bytes,
    has_nonempty_segment_carrier,
    is_actual_state_noop,
    resource_only_projection,
    signed_left_fold3,
    signed_right_fold3,
)


TEST_DIMENSION = AccountingDimensionV1("resource:test", "atoms:test")
OTHER_DIMENSION = AccountingDimensionV1("resource:other", "atoms:other")


def _diagonal_row(
    dimension: AccountingDimensionV1, debit: int, credit: int
) -> AccountingAggregateRowV1:
    flow = MonotoneFlowV1(debit, credit)
    return AccountingAggregateRowV1(dimension, flow, flow)


def _diagonal_leaf(
    bounds: AggregateBoundsV1,
    debit: int,
    credit: int,
    dimension: AccountingDimensionV1 = TEST_DIMENSION,
) -> AccountingAggregateV1:
    return AccountingAggregateV1.leaf_from_canonical_opened_rows(
        bounds,
        (
            OpenedLeafRowV1(
                f"opened:{dimension.resource_kind_id}:{dimension.unit_id}",
                _diagonal_row(dimension, debit, credit),
            ),
        ),
    )


def _tree_binding_rejections() -> dict[str, str]:
    bounds = AggregateBoundsV1(3, 3, 3)
    entries = tuple(
        AccountingEntryV1(f"entry-{index}", _diagonal_leaf(bounds, 1, 0))
        for index in range(3)
    )
    manifest = AccountingManifestV1(entries)
    mutants = {
        "permutation": AccountingBranchV1(
            AccountingLeafV1(entries[1]),
            AccountingBranchV1(
                AccountingLeafV1(entries[0]), AccountingLeafV1(entries[2])
            ),
        ),
        "duplicate": AccountingBranchV1(
            AccountingLeafV1(entries[0]),
            AccountingBranchV1(
                AccountingLeafV1(entries[0]), AccountingLeafV1(entries[2])
            ),
        ),
        "omission": AccountingBranchV1(
            AccountingLeafV1(entries[0]), AccountingLeafV1(entries[1])
        ),
    }
    decisions = {}
    for name, tree in mutants.items():
        try:
            fold_tree(manifest, tree)
        except AccountingModelError:
            decisions[name] = "reject"
        else:
            decisions[name] = "accept"
    return decisions


def _lifted_signed_witness(bound: int) -> dict[str, object]:
    bounds = AggregateBoundsV1(bound, 3, bound)
    entries = tuple(
        AccountingEntryV1(
            f"entry-{index}",
            AccountingAggregateV1.leaf_from_trusted_signed_deltas(
                bounds, (SignedDeltaV1(TEST_DIMENSION, delta),)
            ),
        )
        for index, delta in enumerate((127, 1, -1))
    )
    manifest = AccountingManifestV1(entries)
    results = tuple(fold_tree(manifest, tree) for tree in all_ordered_trees(entries))
    canonical = fold_manifest(manifest)
    return {
        "bound": bound,
        "ordered_binary_trees": len(results),
        "all_results_equal": all(result == canonical for result in results),
        "defined": canonical is not None,
        "result": None if canonical is None else canonical.canonical_payload(),
    }


def _projection_collision() -> dict[str, object]:
    first = AccountingAggregateRowV1.from_columns(
        TEST_DIMENSION,
        consumed_atoms=3,
        created_atoms=5,
        authorized_mint_atoms=2,
        authorized_burn_atoms=0,
    )
    second = AccountingAggregateRowV1.from_columns(
        TEST_DIMENSION,
        consumed_atoms=3,
        created_atoms=5,
        authorized_mint_atoms=3,
        authorized_burn_atoms=1,
    )
    return {
        "resource_only_projections_collide": (
            resource_only_projection(first) == resource_only_projection(second)
        ),
        "four_column_rows_differ": first != second,
        "first": first.canonical_payload(),
        "second": second.canonical_payload(),
    }


def _wide_carrier_witness() -> dict[str, object]:
    bounds = AggregateBoundsV1.protocol()
    max_row = AccountingAggregateRowV1.from_columns(
        TEST_DIMENSION,
        consumed_atoms=MODEL_U128_MAX,
        created_atoms=MODEL_U128_MAX,
        authorized_mint_atoms=MODEL_U128_MAX,
        authorized_burn_atoms=MODEL_U128_MAX,
    )
    leaf = AccountingAggregateV1.leaf_from_canonical_opened_rows(
        bounds, (OpenedLeafRowV1("opened:max-u128", max_row),)
    )
    merged = leaf.checked_merge(leaf)
    assert merged is not None
    premature = max_row.resource_flow.checked_merge(
        max_row.resource_flow, MODEL_U128_MAX
    )
    u32_theoretical_maximum = MODEL_U32_MAX * MODEL_U128_MAX
    return {
        "two_max_u128_leaves_defined": merged is not None,
        "two_leaf_limb_total": merged.rows[0].consumed_atoms,
        "premature_u128_aggregate_defined": premature is not None,
        "u32_theoretical_maximum_bit_length": u32_theoretical_maximum.bit_length(),
        "u32_theoretical_maximum_fits_u256": (
            u32_theoretical_maximum <= MODEL_U256_MAX
        ),
        "segment_leaf_count_max": bounds.max_leaf_count,
        "aggregate_dimension_count_max": bounds.max_dimension_count,
        "coverage_entry_count_max": bounds.max_coverage_entry_count,
        "framed_hash_list_max_items": MODEL_MAX_FRAMED_HASH_LIST_ITEMS,
        "framed_hash_list_max_payload_bytes": framed_hash_list_payload_bytes(
            MODEL_MAX_FRAMED_HASH_LIST_ITEMS
        ),
    }


def _sparse_union_witness() -> dict[str, object]:
    bounds = AggregateBoundsV1(3, 3, 9)
    left = _diagonal_leaf(bounds, 1, 1, TEST_DIMENSION)
    right = _diagonal_leaf(bounds, 2, 2, OTHER_DIMENSION)
    merged = left.checked_merge(right)
    assert merged is not None
    return {
        "left_support": len(left.rows),
        "right_support": len(right.rows),
        "union_support": len(merged.rows),
        "canonical_dimensions": [
            candidate.dimension.canonical_payload() for candidate in merged.rows
        ],
        "coverage_leaf_count": merged.leaf_count,
        "coverage_dimensions_per_leaf": [
            len(leaf.dimensions) for leaf in merged.coverage_manifest.leaves
        ],
    }


def explore() -> dict[str, object]:
    signed_bound = 2
    signed_mismatches = []
    for a, b, c in itertools.product(
        range(-signed_bound, signed_bound + 1), repeat=3
    ):
        left = signed_left_fold3(signed_bound, a, b, c)
        right = signed_right_fold3(signed_bound, a, b, c)
        if left != right:
            signed_mismatches.append(
                {"inputs": [a, b, c], "left": left, "right": right}
            )

    limb_bound = 2
    bounds = AggregateBoundsV1(limb_bound, 4, limb_bound)
    leaf_values = tuple(
        _diagonal_leaf(bounds, debit, credit)
        for debit, credit in itertools.product(range(limb_bound + 1), repeat=2)
    )
    manifests = 0
    tree_evaluations = 0
    tree_disagreements = 0
    defined_manifests = 0
    undefined_manifests = 0
    tree_count = 0
    for leaves in itertools.product(leaf_values, repeat=4):
        entries = tuple(
            AccountingEntryV1(f"entry-{index}", aggregate)
            for index, aggregate in enumerate(leaves)
        )
        manifest = AccountingManifestV1(entries)
        expected = fold_manifest(manifest)
        trees = all_ordered_trees(entries)
        manifests += 1
        tree_count = len(trees)
        defined_manifests += expected is not None
        undefined_manifests += expected is None
        for tree in trees:
            tree_evaluations += 1
            tree_disagreements += fold_tree(manifest, tree) != expected

    opened_rows = tuple(
        _diagonal_row(TEST_DIMENSION, debit, credit)
        for debit, credit in itertools.product(range(limb_bound + 1), repeat=2)
    )
    material_rows = tuple(
        candidate
        for candidate in opened_rows
        if admit_material_accounting_row(candidate)
    )
    zero_net_nonzero = tuple(
        candidate for candidate in material_rows if candidate.resource_flow.net == 0
    )
    zero_opened_leaf = AccountingAggregateV1.leaf_from_canonical_opened_rows(
        bounds, (OpenedLeafRowV1("opened:zero-row", opened_rows[0]),)
    )
    zero_manifest = AccountingManifestV1(
        (AccountingEntryV1("zero-opened-row", zero_opened_leaf),)
    )
    empty_support_leaf = AccountingAggregateV1.leaf_from_canonical_opened_rows(
        bounds, ()
    )
    empty_support_manifest = AccountingManifestV1(
        (AccountingEntryV1("empty-support", empty_support_leaf),)
    )
    internal_identity = AccountingAggregateV1.zero(bounds)

    tree_binding = _tree_binding_rejections()
    return {
        "schema": "zrm/accounting-aggregate-exploration/v1",
        "signed_checked_add_mutant": {
            "bound": signed_bound,
            "triples": (2 * signed_bound + 1) ** 3,
            "parenthesization_mismatches": len(signed_mismatches),
            "first_mismatch": signed_mismatches[0],
            "literature_seed_witness_bound_127": {
                "inputs": [127, 1, -1],
                "left": signed_left_fold3(127, 127, 1, -1),
                "right": signed_right_fold3(127, 127, 1, -1),
            },
        },
        "monotone_sparse_two_flow_trees": {
            "aggregate_cap": limb_bound,
            "leaves_per_manifest": 4,
            "diagonal_leaf_values": len(leaf_values),
            "manifests": manifests,
            "ordered_binary_trees_per_manifest": tree_count,
            "tree_evaluations": tree_evaluations,
            "defined_manifests": defined_manifests,
            "undefined_manifests": undefined_manifests,
            "value_or_definedness_disagreements": tree_disagreements,
        },
        "sparse_support_union": _sparse_union_witness(),
        "lifted_signed_witness": {
            "bound_127": _lifted_signed_witness(127),
            "bound_128": _lifted_signed_witness(128),
        },
        "four_column_projection": _projection_collision(),
        "wide_aggregate_carrier": _wide_carrier_witness(),
        "ordered_manifest_binding": {
            "mutants": len(tree_binding),
            "rejected_mutants": sum(
                decision == "reject" for decision in tree_binding.values()
            ),
            "decisions": tree_binding,
        },
        "identity_coverage_and_materiality": {
            "opened_leaf_rows": len(opened_rows),
            "material_rows": len(material_rows),
            "coverage_only_zero_rows": len(opened_rows) - len(material_rows),
            "material_zero_net_rows": len(zero_net_nonzero),
            "zero_opened_row_material_support": len(zero_opened_leaf.rows),
            "zero_opened_row_coverage_occurrences": sum(
                len(leaf.dimensions)
                for leaf in zero_opened_leaf.coverage_manifest.leaves
            ),
            "zero_opened_row_manifest_admitted": admit_external_manifest(
                zero_manifest
            ),
            "empty_support_manifest_admitted": admit_external_manifest(
                empty_support_manifest
            ),
            "empty_support_has_nonempty_carrier": has_nonempty_segment_carrier(
                empty_support_leaf
            ),
            "internal_identity_has_nonempty_carrier": (
                has_nonempty_segment_carrier(internal_identity)
            ),
            "distinct_state_roots_are_actual_noop": is_actual_state_noop(
                "state:before", "state:after"
            ),
            "equal_state_roots_are_actual_noop": is_actual_state_noop(
                "state:same", "state:same"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    if args.compact:
        print(json.dumps(explore(), sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(explore(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
