# WP2 policy-model critical mutation map

This map names the critical guards in the pre-RFC WP2 in-memory policy slice and the tests that kill representative mutations. The implementation defines no canonical policy bytes, hashes, registry, trusted context, verifier dispatch, or authority fact.

| Mutant ID | Mutation | Killing test or evidence |
| --- | --- | --- |
| `WP2-MUT-SCHEMA` | accept a non-v1 machine, resource-kind, context, verifier, or cost-model schema | `every_policy_object_rejects_wrong_schema_and_inverted_validity`, `model_candidate_accepts_only_schema_version_one` |
| `WP2-MUT-SUITE` | admit a machine policy under a non-schema-fixed resource suite | `machine_policy_reject_precedence_is_schema_then_suite_then_limits` |
| `WP2-MUT-LIMIT-OMIT` | remove any one of the sixteen protocol ceilings | `limit_boundary_atlas_flips_every_governed_ceiling` |
| `WP2-MUT-LIMIT-CONSTANT` | change a protocol ceiling or strict-default byte value | `every_machine_limit_accepts_its_ceiling_and_rejects_ceiling_plus_one` |
| `WP2-MUT-RESOURCE-MIN` | reject 603 or admit 602 resource bytes | `resource_wire_complete_form_must_fit_policy_limit` |
| `WP2-MUT-ADMISSION-FALLBACK` | pair `LocalKernel` with a verifier or allow `RequiredVerifier` without one | `machine_policy_rejects_both_invalid_admission_pairings`, Kani admission matrix |
| `WP2-MUT-ADMISSION-ID` | accept a local admission verifier or a required verifier under a different policy ID | `admission_verifier_candidate_requires_mode_and_exact_policy_id` |
| `WP2-MUT-WINDOW` | admit an inverted window, reject a zero-length window, or make an endpoint exclusive | `every_policy_object_rejects_wrong_schema_and_inverted_validity`, `zero_length_window_preserves_both_inclusive_endpoints`, Kani validity harness |
| `WP2-MUT-LIFECYCLE-QUANTITY` | accept a lifecycle non-fungible resource whose quantity is not exactly one | `resource_kind_policy_enforces_unit_quantity_and_lifecycle_bounds` |
| `WP2-MUT-UNIT` | accept a resource dimension under a different `UnitId` | `resource_kind_policy_enforces_unit_quantity_and_lifecycle_bounds` |
| `WP2-MUT-QUANTITY-MAX` | accept a quantity above the resource-kind maximum | `resource_kind_policy_enforces_unit_quantity_and_lifecycle_bounds` |
| `WP2-MUT-VERIFIER-IDENTITY` | compare the wrong machine, domain, or cost-model field | `verifier_compatibility_rejects_every_mismatch_before_authority` |
| `WP2-MUT-VERIFIER-WINDOW` | accept an inactive machine or verifier policy | `verifier_compatibility_binds_machine_domain_cost_model_window_and_limits`, `verifier_compatibility_rejects_every_mismatch_before_authority` |
| `WP2-MUT-VERIFIER-CAPS` | reject an exact artifact/cost cap or accept cap plus one | `verifier_compatibility_accepts_exact_machine_caps_and_rejects_one_more` |
| `WP2-MUT-COST-BACKEND` | use a cost row from another backend family | `backend_mismatch_precedes_byte_bounds_and_arithmetic` |
| `WP2-MUT-COST-BOUNDS` | perform cost arithmetic before artifact or statement bounds, or fail to copy a policy-selected bound into a quote request | `artifact_bound_precedes_statement_bound_and_arithmetic`, `public_input_bound_precedes_arithmetic`, `policy_derived_cost_quotes_preserve_every_hidden_bound` |
| `WP2-MUT-COST-TERM` | omit or replace the base, artifact, statement, or reserved-output term | `charge_includes_each_of_the_four_terms` |
| `WP2-MUT-COST-WRAP` | wrap `u128` arithmetic or narrow a charge that does not fit `u64` | `checked_sum_rejects_u128_overflow`, `charge_must_fit_u64`, Kani capped-charge harness |
| `WP2-MUT-COST-CAP` | skip or reorder model and verifier charge caps | `model_charge_cap_is_enforced_before_verifier_cap`, `verifier_policy_charge_cap_is_enforced` |
| `WP2-MUT-RESERVATION` | allow a bounded actual charge to exceed its maximum-based reservation | `reservation_dominates_every_sampled_bounded_actual_charge`, Kani reservation harness, `policy_cost_v1` fuzzer |

Documented exclusions:

- returning schema version one from `VerifierCostModelV1::schema_version` is mechanically equivalent because its constructor rejects every other version;
- returning schema version one from `MachinePolicyV1::schema_version` is mechanically equivalent for the same reason;
- Kani harness bodies are a separate tool-routing exclusion from ordinary mutation execution and are checked by Kani.

The final hardened-tree local campaign ran:

```text
cargo +1.87.0 mutants -p zrm-policy --timeout 10 --build-timeout 60 --jobs 4 --output target/mutants-wp2-final-tree
```

It tested 188 mutants after the documented exclusions: 147 were caught, 41 were unviable, zero were missed, and zero timed out. The unmutated baseline also passed. This is test-sensitivity evidence for the implemented local policy slice. It does not prove correctness or extend to the deferred canonical ABI, registry, authority, kernel, state, or commit surfaces.
