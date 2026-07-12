# WP3c role-bound intrinsic resource work log

**Date:** 2026-07-11

## Design packet

### Goal and change class

Bind the existing sealed intrinsic resource body to its exact role and ordinal
within one supplied canonical partition, without accepting those values
independently of that partition. This is a Class C semantic implementation that
advances the obligatory handoff described by `ZRM-CBC-003` while preserving the
existing body-to-identifier construction under `ZRM-CBC-001` and
`ZRM-CBC-002`.

### Affected modules

- `crates/zrm-kernel`: new role-bound staged type and binding operation;
- kernel integration tests and bounded model harnesses;
- the existing structure-aware fuzz package and deterministic corpus;
- README, conformance, code-quality inventory, workflows, and evidence.

### Exact typed boundary

```text
IntrinsicResourceV1 + CanonicalResourceRolesV1
  -> RoleBoundIntrinsicResourceV1
  | IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles
```

The public operation is:

```rust
impl CanonicalResourceRolesV1 {
    pub fn bind_intrinsic(
        &self,
        resource: &IntrinsicResourceV1,
    ) -> Result<RoleBoundIntrinsicResourceV1, IntrinsicRoleBindingErrorV1>;
}
```

The successful result has private fields and exposes the original intrinsic
resource plus its derived `ResourceId`, `ResourceRoleV1`, and zero-based
canonical ordinal. The method always looks up `resource.resource_id()` in the
private canonical partition. No public constructor accepts a different
identifier, role, or ordinal independently of that supplied partition.

### Authority boundary

Both inputs remain structural, non-authoritative staged values. The canonical
partition is still caller-proposed and unauthenticated. Success proves only
this local relationship within that supplied partition:

```text
complete intrinsic body
  -> internally derived ResourceId
  -> exact existing canonical role
  -> exact existing canonical ordinal
```

The result authenticates no policy, state membership, freshness, logic,
transition statement, proof, nullifier state, or commit authority. The local
error has no stable reject code or wire representation.

### Invariants

- the stored resource ID equals the intrinsic resource's internally derived ID;
- the role and ordinal come only from the supplied sealed canonical partition;
- an absent resource rejects instead of accepting an independently supplied
  placement;
- local role-list permutations cannot change the bound role or ordinal;
- a valid body mutation that changes `ResourceId` cannot bind to a partition
  containing only the prior ID;
- rejection mutates neither input and performs no allocation or I/O;
- lookup is deterministic and bounded by the existing three 256-entry ceilings.

### Disaster states addressed

- a proof-independent logic claim is prepared with a role or ordinal that
  differs from the supplied canonical partition;
- a resource body is substituted after a role partition was validated;
- the body-derived ID and the role-position ID silently diverge;
- a missing body is treated as though it belonged to the transition;
- a role-local input permutation changes semantic placement.

### Canonical bytes, hashes, and compatibility

No canonical byte layout, domain string, hash, list root, reject code, schema,
or existing public semantic meaning changes. The new type is an in-memory
prevalidation stage. It does not freeze role-list or transition authority ABI.

### Tests to add first

- exact WP1 vector bodies bind in consumed, referenced, and created roles;
- unsorted role candidates produce the exact canonical ordinal;
- absence returns the sole typed local error;
- each valid mutable resource field changes the ID and fails against the stale
  partition;
- role-local permutations preserve binding;
- the wrapper preserves the maximum v1 role-local ordinal of 255;
- private-field construction and independent ID/role/ordinal injection fail to
  compile;
- a bounded exhaustive assignment atlas matches an independent placement
  oracle;
- a structure-aware fuzz target covers present/absent placement, permutations,
  and stale-body substitution;
- Kani covers hit/miss and exact role/ordinal preservation over the production
  lookup path;
- changed critical code reaches the line, branch, and mutation targets.

The boundary-concolic atlas is offline discovery evidence. Any discovered case
must become an ordinary regression. It is not a correctness proof.

### Formal and model obligations

Kani models one fixed four-member canonical partition and a symbolic query over
its four present IDs plus one absent ID. It checks hit/miss behavior and exact
role/ordinal preservation through the production lookup. It does not quantify
over arbitrary partitions or 256-entry lists. SHA-256 and intrinsic
construction remain outside this harness and retain their existing scoped
vector, mutation, fuzz, and Kani evidence. Later claim construction must make
this staged type obligatory and bind its role and ordinal through the final
transition statement.

### Dependency impact

No dependency is added. The new kernel module composes two types already owned
by `zrm-kernel`.

### Performance and resource bounds

Binding performs at most three bounded scans over already canonical lists. It
allocates no memory, performs no hashing, I/O, clock access, randomness, or
global mutation, and has `O(C + R + O)` time with each list bounded to 256.

### Design-choice review

**Design forces:** Package the body-derived identifier and the exact structural
placement within one supplied partition so later logic-claim APIs cannot
receive them as independent caller choices.

**Pattern selected:** A sealed staged value composed by a single binding
operation. No registry, service, callback, or general abstraction is added.

**Invalid states prevented:** Public code cannot construct a successful binding
whose body, identifier, role, and ordinal disagree.

**Extension point or closed-set reason:** The three v1 resource roles are a
closed semantic set. Future roles require a new version and protocol review.

**Alternatives rejected:** Returning a tuple would permit later APIs to accept
its elements independently. Accepting an ID, role, or ordinal independently of
the supplied partition would preserve the substitution vulnerability.
Completing final `ResourceV1` would invent unresolved policy and authority
semantics. Starting reference state over an intrinsic-only resource would
overclaim policy validity.

**Pattern-specific failure modes:** A later API could bypass the staged type, or
documentation could overstate structural placement as authenticated transition
authority. Conformance references, compile-fail tests, and later constructor
signatures must prevent that drift.

**Enforcement and tests:** Private fields, one binding operation, exhaustive
placement tests, mutation analysis, fuzzing, Kani, coverage, and independent
review.

**Technical AI-review status:** Design review is in progress. Human attention is
reserved for specified behavior, evidence, remaining semantic gaps, and
non-claims.

### Known gaps and non-claims

- no final policy-valid `ResourceV1`;
- no strict-decoder provenance;
- no authenticated policy or trusted validation context;
- no resource membership, nonmembership, freshness, or exact-once enforcement;
- no logic claim, statement hash, claim root, or proof binding;
- no canonical role bytes or roots;
- no authenticated transition placement because the partition is
  caller-proposed;
- no proof that SHA-256 is injective; separation of different bodies relies on
  the schema-fixed SHA-256 collision-resistance assumption, while the tests
  cover only the 17 concrete valid field mutations;
- no proof that every partition position has exactly one body, with no missing,
  duplicate, or extra bodies;
- no transition, state, commit, journal, funds-safety, or production claim;
- the zero-quantity marker-policy schema gap remains unresolved and requires
  separate Class E semantic review.

## Verification record

Candidate implementation replay before the patch-bound evidence commit:

| Check | Result |
| --- | --- |
| Rust workspace tests | 104 passed, 0 failed |
| Rust documentation tests | 2 compile-fail tests passed, 0 failed |
| Focused WP3c boundary tests | 5 integration tests plus the 256-assignment atlas passed, including ordinal 255 |
| Coverage | workspace 98.84% lines / 99.12% branches; policy 99.70% / 100%; kernel 100% / 100% |
| New production module coverage | 40/40 lines and 8/8 functions; LLVM reports zero instrumented branch sites in this file, so no changed-module branch percentage is claimed |
| Automatic focused mutation | 9 candidates: 3 caught, 6 compiler-unviable, 0 missed, 0 timed out |
| Kani workspace | 17/17 harnesses verified, 0 failures |
| Corrected WP3c Kani harness | 856 checks passed; all 4 reachability covers satisfied; 7 unreachable-code checks reported |
| Targeted Miri | 11 WP3c-relevant tests passed, 0 failed |
| Structure-aware fuzz | 667,011 executions in 31 seconds, 0 failures, final coverage 414 and feature count 450 |
| Code quality | `excellent-candidate`; 16 rules, 5 design decisions, 0 findings or advisories |
| Complexity | 36 Rust files, 288 functions, 0 warnings, 0 exceptions |
| Repository policy | formatting, compile, Clippy, rustdoc, architecture, conformance, package manifest, corpus, vector replay, BOM, hygiene, and 73 Python tool tests passed |

The first independent authority review found three blockers: an insufficiently
targeted private-field compile-fail example, potentially vacuous Kani fixture
setup, and wording that overstated authority over a caller-proposed partition.
All three were corrected. Its follow-up review then found silent fuzz-fixture
exits and insufficient evidence for two compiler-unviable authority mutants.
The fuzz harness now fails loudly on every internally generated fixture,
partition, ordinal conversion, or different-body ID collision. Patch-bound
manual compiling mutants remain required for wrong-ID lookup, absent fallback,
and corrupted placement before this candidate is ready for human Class C
review.

The external peer-review helper returned HTTP 401 and supplied no review
evidence. Human Class C review, hosted CI, merge approval, and every production
claim remain pending.
