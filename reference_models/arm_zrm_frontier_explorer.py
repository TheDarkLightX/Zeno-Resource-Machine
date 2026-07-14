"""Deterministic bounded exploration for the ARM/ZRM frontier hypotheses."""

from __future__ import annotations

import argparse
import itertools
import json

from reference_models.arm_zrm_frontier_v1 import (
    DeltaEquation,
    KindBasis,
    SemanticSummary,
    find_partial_associativity_counterexample,
    partial_parenthesizations,
    proof_topology_root,
)


def explore() -> dict[str, object]:
    kinds = ("asset-a", "asset-b")
    honest = KindBasis.honest(kinds)
    malicious = KindBasis.malicious_known_scalars({"asset-a": 3, "asset-b": 5})
    relation = KindBasis.malicious_relation(kinds)

    honest_cases = 0
    honest_unbalanced_known = 0
    malicious_cases = 0
    malicious_unbalanced_known = 0
    relation_conversion_cases = 0
    for qa, qb, blind in itertools.product(range(-2, 3), range(-2, 3), range(7)):
        equation = DeltaEquation.from_mapping({"asset-a": qa, "asset-b": qb}, blind)
        honest_cases += 1
        malicious_cases += 1
        if not equation.is_balanced() and equation.known_binding_key(honest) is not None:
            honest_unbalanced_known += 1
        if not equation.is_balanced() and equation.known_binding_key(malicious) is not None:
            malicious_unbalanced_known += 1
        if qa == -qb and qa != 0 and equation.known_binding_key(relation) is not None:
            relation_conversion_cases += 1

    modulus = 7
    partial_triples = 0
    parenthesization_mismatches = 0
    both_defined_mismatches = 0
    for a, b, c in itertools.product(range(1, modulus), repeat=3):
        partial_triples += 1
        left, right = partial_parenthesizations(a, b, c, modulus)
        if left != right:
            parenthesization_mismatches += 1
            if left is not None and right is not None:
                both_defined_mismatches += 1

    basis_root = honest.root()
    summaries = [
        SemanticSummary.singleton(
            context_hash="ctx",
            basis_root=basis_root,
            profile_id="shielded-v1",
            action_id=action,
            consumed_tags=[f"nf-{action}"],
            created_tags=[f"cm-{action}"],
            delta_rows=rows,
        )
        for action, rows in (
            ("a", {"asset-a": 1}),
            ("b", {"asset-a": -1, "asset-b": 2}),
            ("c", {"asset-b": -2}),
        )
    ]
    semantic_roots: set[str] = set()
    topology_roots: set[str] = set()
    for permutation in itertools.permutations(summaries):
        first, second, third = permutation
        semantic_roots.add(first.compose(second).compose(third).semantic_root())
        left_pair = proof_topology_root(first.semantic_root(), second.semantic_root())
        topology_roots.add(proof_topology_root(left_pair, third.semantic_root()))
        right_pair = proof_topology_root(second.semantic_root(), third.semantic_root())
        topology_roots.add(proof_topology_root(first.semantic_root(), right_pair))

    return {
        "schema": "zrm/arm-zrm-frontier-exploration/v1",
        "basis_attack": {
            "honest_cases": honest_cases,
            "honest_unbalanced_known_binding_keys": honest_unbalanced_known,
            "malicious_cases": malicious_cases,
            "malicious_unbalanced_known_binding_keys": malicious_unbalanced_known,
            "known_cross_kind_conversion_cases": relation_conversion_cases,
        },
        "partial_composition": {
            "modulus": modulus,
            "nonzero_triples": partial_triples,
            "parenthesization_domain_mismatches": parenthesization_mismatches,
            "both_defined_value_mismatches": both_defined_mismatches,
            "first_counterexample": list(find_partial_associativity_counterexample(modulus)),
        },
        "summary_composition": {
            "permutations": 6,
            "distinct_semantic_roots": len(semantic_roots),
            "distinct_ordered_proof_topology_roots": len(topology_roots),
            "balanced_delta_rows": list(summaries[0].compose(summaries[1]).compose(summaries[2]).delta_rows),
        },
        "non_claims": [
            "formal symbols are not elliptic-curve points",
            "bounded enumeration is not an unbounded proof",
            "cryptographic hash, signature, proof-system, and discrete-log assumptions are external",
            "no protocol bytes, authority capability, or production implementation is created",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    print(json.dumps(explore(), indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
