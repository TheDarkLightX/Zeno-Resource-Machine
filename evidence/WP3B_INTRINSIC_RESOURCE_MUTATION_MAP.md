# WP3b intrinsic-resource critical mutation map

This map names the critical policy-independent resource-construction guards and
the evidence that detects representative mutations. It covers
`ResourceWireV1 -> IntrinsicResourceV1` only. It grants no policy, state,
transition, proof, or commit authority.

Evidence binding:

```text
source_revision = 73a8612e00c8b9583a1d1d5ef3f3e6a853b09808
source_tree = f929d77a2322ec0770f146e7efa6e14b1b4fb058
dirty = false
tool = cargo-mutants 26.0.0
tool_executable_sha256 = 0c01b08444b65d20be9a0dbe9786ae1c4844898de8872b457426397a24f0a771
environment_policy_root = sha256:8276e3c5f61fa9d37849c0245070362895669a67298996553df3c07f81eee8cf
focused_duration_ms = 20441
focused_resource_output_sha256 = 82374e8d534b829c9dfac8151ae787d9c5a619b5917d032164caffd404bce4c4
focused_error_output_sha256 = 408cde6f42f448e566378072534573feb126855f57fc4c03517be6a78c37050d
workspace_duration_ms = 121686
workspace_output_sha256 = bd6fa7335019ef7be03215b4f949e4bf0c9ac42d51fd35de69db6c2fd70cb68c
```

The commands below were replayed in a detached clean worktree at the bound
revision. Ignored build and report outputs did not change `git status`.

| Mutant ID | Mutation | Killing test or evidence |
| --- | --- | --- |
| `WP3B-MUT-ID-INJECT` | allow a caller to initialize the sealed resource or provide its `ResourceId` | compile-fail example on `IntrinsicResourceV1`; private fields; sole public constructor |
| `WP3B-MUT-ID-BODY-BYPASS` | return a default or detached resource identity | `exact_absent_vector_constructs_and_preserves_every_field`, `exact_present_vector_constructs_through_try_from`; constructor-bypass cargo mutants are unviable |
| `WP3B-MUT-ID-FIELD-OMIT` | omit or replace any one of the 18 wire fields in resource-ID derivation | WP1 `every_wire_field_changes_resource_id`; both exact WP1 vector replays through WP3b |
| `WP3B-MUT-ZERO-GUARD` | skip a prohibited zero identifier, root, or nonce check | `each_zero_field_rejects_with_exact_local_identity`; the 65,536-mask atlas; Kani exact-field and pairwise-order harnesses |
| `WP3B-MUT-ZERO-ORDER` | report a later zero field before an earlier field | the 65,536-mask atlas; Kani pairwise canonical-order harness |
| `WP3B-MUT-EPOCH-REMOVE` | accept expiry earlier than creation | caught cargo mutant replacing `validate_epoch_order` with success; `expiry_boundaries_are_exact` |
| `WP3B-MUT-EPOCH-COMPARATOR` | replace `<` with `==`, `>`, or `<=` | all four generated comparator mutants caught by `expiry_boundaries_are_exact` and the atlas |
| `WP3B-MUT-EPOCH-FLAG-ORDER` | report unknown flags before invalid epoch order | atlas plus Kani epoch-before-flags harness |
| `WP3B-MUT-FLAG-BYPASS` | accept any nonzero version-one flag pattern | `representative_nonzero_flag_patterns_reject_with_exact_bits`; symbolic Kani arbitrary-nonzero-`u32` harness; structure-aware fuzzer |
| `WP3B-MUT-WIDTH-TRUNCATE` | narrow or replace `u128` quantity or `u64` epochs | `quantity_values_remain_exact_unresolved_candidates`; exact getter tests; symbolic full-width Kani harness |
| `WP3B-MUT-GETTER-SUBSTITUTE` | return a default or wrong stored field | generated quantity, creation-epoch, and expiry getter mutants were caught; exact all-field vector replay covers every getter |
| `WP3B-MUT-REJECT-MUTATE` | mutate a borrowed wire candidate before returning an error | `every_public_semantic_reject_family_leaves_borrowed_wire_unchanged`; every atlas mask compares the retained input snapshot |
| `WP3B-MUT-DERIVATION-PRECEDENCE` | attempt allocation or hashing before an earlier semantic reject | `deterministic_semantic_reject_precedes_injected_derivation_failure` |
| `WP3B-MUT-DIAGNOSTIC-EMPTY` | erase field or error diagnostic labels | all three generated error-label/display mutants caught by `every_local_error_has_a_bounded_diagnostic` |

The final focused campaigns ran:

```text
cargo +1.87.0 mutants -p zrm-kernel -f crates/zrm-kernel/src/resource.rs --timeout 10 --build-timeout 60 --jobs 2 --output target/mutants-wp3b-final
cargo +1.87.0 mutants -p zrm-kernel -f crates/zrm-kernel/src/resource/error.rs --timeout 10 --build-timeout 60 --jobs 2 --output target/mutants-wp3b-error-final
```

They tested 36 candidates: 12 were caught, 24 were unviable, zero were
missed, and zero timed out. Unviable constructor-bypass and getter mutants did
not compile because sealed opaque fields have no authority-erasing default
substitution. The unmutated baselines passed.

The full workspace campaign ran:

```text
cargo +1.87.0 mutants --workspace --timeout 10 --build-timeout 60 --jobs 2 --output target/mutants-wp3b-workspace
```

It tested 380 candidates: 280 were caught, 100 were unviable, zero were
missed, and zero timed out. Production source did not change after that run;
later changes only broadened no-op tests and Kani predicates. The exact final
WP3b source was then replayed by the focused campaigns above.

Kani harness bodies are routed to Kani and excluded from ordinary mutation
execution. The no-op and caller-forgery properties are enforced structurally
and by hand-authored tests because general mutation operators do not directly
model visibility changes or external state capabilities.

These results measure test sensitivity on the bounded candidate set. Unviable
mutants are compile-time rejections, not killed runtime mutants. This map does
not prove unbounded correctness, SHA-256 correctness, policy validity,
end-to-end funds safety, or production readiness.
