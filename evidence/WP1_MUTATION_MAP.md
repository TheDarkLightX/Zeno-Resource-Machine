# WP1 critical mutation map

This map names the critical WP1 guard mutations and the tests that kill them. The general campaign is also run with `cargo-mutants`. Kani-only functions are excluded from the ordinary mutation process because they are compiled and checked by Kani instead of `cargo test`.

| Mutant ID | Mutation | Killing test or evidence |
| --- | --- | --- |
| `WP1-MUT-BOUNDS-REMOVE` | remove the 16 KiB ingress ceiling | `maximum_bound_distinguishes_trailing_from_oversize` |
| `WP1-MUT-BOUNDS-OFF-BY-ONE` | reject 16,384 or accept 16,385 bytes | `maximum_bound_distinguishes_trailing_from_oversize` |
| `WP1-MUT-HEADER-BYPASS` | accept an incomplete or wrong header | `boundary_atlas_reaches_all_twelve_decoder_outcomes`, `complete_header_with_wrong_magic_reaches_magic_guard` |
| `WP1-MUT-FIELD-ORDER` | accept a duplicate, reordered, or unknown tag | `duplicate_reordered_and_unknown_tags_share_field_tag_reject` |
| `WP1-MUT-FIELD-LENGTH` | accept a noncanonical fixed-field length | `boundary_atlas_reaches_all_twelve_decoder_outcomes` |
| `WP1-MUT-OPTION-SHAPE` | accept an expiry tag/length mismatch | `expiry_length_and_tag_cross_product_is_canonical` |
| `WP1-MUT-TRAILING-BYTES` | ignore bytes after field 18 | `maximum_bound_distinguishes_trailing_from_oversize` |
| `WP1-MUT-REJECT-PRECEDENCE` | evaluate a lower-priority defect first | `error_precedence_is_stable_for_multiple_defects` |
| `WP1-MUT-ENDIANNESS` | decode or encode integers in the wrong byte order | `canonical_offsets_and_integers_are_big_endian` |
| `WP1-MUT-HASH-OMISSION` | omit or replace any resource field in `ResourceId` input | `every_wire_field_changes_resource_id` plus independent vector replay |
| `WP1-MUT-ZERO-ID` | accept an all-zero opaque identifier | `opaque_identifier_rejects_all_zero_bytes` plus Kani constructor harness |
| `WP1-MUT-DOMAIN-BINDING` | omit or substitute machine, domain, or resource binding in a transparent nullifier | `transparent_nullifier_changes_across_machine_domain_and_resource` |
| `WP1-MUT-UNKNOWN-FLAGS` | accept nonzero version-one resource flags as validated flags | `resource_flags_v1_accept_only_zero` |

Reviewed exclusions:

- replacing bitwise OR with XOR in `RejectCodeV1::value` is equivalent because the stage and reason occupy disjoint 16-bit halves;
- returning zero from `ResourceFlagsV1::bits` is equivalent because the only constructible version-one value is zero;
- Kani harness bodies are exercised through their named model-check commands and are excluded from the ordinary test runner.

The reviewed workspace campaign on 2026-07-10 evaluated 110 useful or buildable candidates: 88 were caught and 22 were unviable. No candidate was missed after the exclusions above. This is mutation evidence for WP1 only and does not prove protocol correctness.
