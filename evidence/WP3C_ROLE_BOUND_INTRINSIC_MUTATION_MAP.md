# WP3c role-bound intrinsic critical mutation map

This map names the critical guards for:

```text
IntrinsicResourceV1 + CanonicalResourceRolesV1
  -> RoleBoundIntrinsicResourceV1
  | IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles
```

It grants no policy, membership, logic, transition, state, proof, commit, or
production authority.

Evidence binding:

```text
source_revision = ab346b0d3f8a659f70af7a0ab9cc25d218e4fd64
source_tree = a8ecd89a03e22fc0a40ec85ca0fa035320118bf6
dirty = false
cargo-mutants = 26.0.0
cargo-mutants executable sha256 = 0c01b08444b65d20be9a0dbe9786ae1c4844898de8872b457426397a24f0a771
environment_policy_root = sha256:0e51986ace15ac5ed231d530dad6e11401da402f42b0a4bf69e0255316e23d75
focused_outcomes_sha256 = cec68bbd3dddffe3947fefa1aa9a206c98c252b2527b952d75718073d2b75372
workspace_outcomes_sha256 = 23cfbb2f197118f3cc0941597f5771a453a1091d323c435cb47eb51bd0a86c32
manual_result_root = a71c28b23702237613c7760268ceac3a02c7f080a2ab43bcf1660acff1750e23
```

| Mutant ID | Mutation | Killing evidence |
| --- | --- | --- |
| `WP3C-MUT-FORGE` | construct a successful binding with caller-selected private body or position fields | external compile-fail example supplies both fields and fails because they are private |
| `WP3C-MUT-WRONG-PRESENT-ID` | replace the body-derived lookup key with another ID already present in the supplied partition | manual compiling mutant killed by absence, exact-vector, stale-body, and ordinal-ceiling tests |
| `WP3C-MUT-ABSENT-FALLBACK` | turn absence into success by falling back to a different present position | manual compiling mutant killed by absence and all-field stale-body tests |
| `WP3C-MUT-CORRUPT-ORDINAL` | return ordinal zero independently of the sealed position | manual compiling mutant killed by exact-vector and ordinal-255 tests; automatic ordinal mutants are also caught |
| `WP3C-MUT-CORRUPT-ROLE` | project a role different from the sealed position | exact consumed, referenced, and created binding tests compare both direct getters and the complete position |
| `WP3C-MUT-STALE-BODY-ACCEPT` | accept a body whose derived ID differs from the partition ID | all 17 valid field mutations reject; fuzz grammar and manual fallback mutant exercise this disaster state |
| `WP3C-MUT-PERMUTATION` | derive ordinal from caller list order instead of canonical order | role-local permutation test and 256-assignment atlas use independently computed canonical ordinals |
| `WP3C-MUT-MAX-ORDINAL` | truncate or replace the role-local ordinal at the v1 ceiling | public wrapper test binds a target at exact ordinal 255 |
| `WP3C-MUT-REJECT-MUTATE` | alter the intrinsic resource or canonical partition on rejection | absence test snapshots both inputs; the API accepts shared references and returns no effect capability |

The automatic focused campaign ran:

```text
cargo +1.87.0 mutants -p zrm-kernel \
  -f crates/zrm-kernel/src/role_bound_resource.rs \
  --timeout 10 --build-timeout 60 --jobs 2 \
  --output target/wp3c-mutants-focused-evidence
```

It tested nine candidates: three were caught, six were compiler-unviable, zero
were missed, and zero timed out. Because the authority-relevant function
replacement candidates were compiler-unviable, three exact source patches were
then applied one at a time to the clean recorded revision. Every patch compiled
through the test-build phase, reached tests, and was killed:

| Patch | Patch SHA-256 | Test result |
| --- | --- | --- |
| `evidence/wp3c-mutants/wrong-present-id.diff.txt` | `d5d76a15b88477366e693aa3630b37749fb660f373631f0601b15ac60b0913b9` | exit 101; four focused tests failed |
| `evidence/wp3c-mutants/absent-fallback.diff.txt` | `90b6a6a595a492ecce4bc5e247c314c01cb3b9afa826f7d5eb024a7b659f4073` | exit 101; absence and stale-body tests failed |
| `evidence/wp3c-mutants/corrupt-ordinal.diff.txt` | `86de81caf63ddd2c733fd6e61d2ff2e66b124e39f060eeee3461c236309524d4` | exit 101; exact and ceiling ordinal tests failed |

The worktree returned to the exact source tree after every mutant and the
unmutated focused tests passed afterward. The full workspace campaign tested
389 candidates: 283 were caught, 106 were compiler-unviable, zero were missed,
and zero timed out.

These results measure test sensitivity over the recorded generated and manual
fault set. Compiler-unviable mutants are compile-time outcomes. Mutation
killing does not prove complete fault detection, SHA-256 injectivity, arbitrary
partition correctness, funds safety, or production readiness.
