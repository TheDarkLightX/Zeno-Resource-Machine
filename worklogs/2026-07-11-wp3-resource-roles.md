# WP3a canonical resource-role partition work log

**Date:** 2026-07-11

## Design packet

### Goal and change class

Implement only `ZRM-CBC-003`: a bounded, deterministic, in-memory partition of inert `ResourceId` values into consumed, referenced, and created roles. This is a Class C semantic change. It stops before resource construction, transition statements, roots, hashes, membership, logic verification, state, or commit.

### Typed boundary

```text
ResourceRoleListsCandidateV1 + PolicyLimitsV1
  -> CanonicalResourceRolesV1
  | ResourceRolePartitionErrorV1

CanonicalResourceRolesV1 + ResourceId
  -> ResourceRolePositionV1(resource ID, role, zero-based ordinal)
  | absent
```

Candidates and `PolicyLimitsV1` are locally validated data, not authenticated authority. Successful construction grants only structural facts: policy-bounded counts, ascending order, within-role uniqueness, pairwise role disjointness, and derived ordinals.

### Normative behavior and reject precedence

Before allocation, validate counts in this order:

1. consumed;
2. referenced;
3. created.

After all counts pass and before allocation, reject structural defects in this order:

1. duplicate consumed ID;
2. duplicate referenced ID;
3. duplicate created ID;
4. consumed/referenced collision;
5. consumed/created collision;
6. referenced/created collision.

Only structurally valid candidates reserve storage, in consumed, referenced, created order, and then sort each role by `ResourceId`. Structural precedence is deterministic and noncanonical. Whether bounded reservation succeeds is host-dependent and produces a role-local `CapacityUnavailable` diagnostic. No new stable `RejectCodeV1` number or wire tag is assigned. Ordinals are zero-based `u32` positions in each final canonical role list and restart at zero per role. Input order and input slices cannot affect or be changed by the result.

### Disaster states and obligations

- one resource occupies multiple roles (`ZRM-CBC-003`);
- duplicate occurrence changes a set into a multiset;
- a policy-disabled or over-limit role is allocated or accepted;
- a caller substitutes its own ordinal;
- input permutation changes the canonical result;
- structural success is mislabeled as resource, transition, or state authority.

### Canonical ABI and compatibility impact

No canonical bytes, role-tag parser, list root, hash, statement field, stable reject reason, or protocol vector is added. `ResourceId::Ord` supplies the current in-memory lexicographic byte order. A later Class E RFC must explicitly freeze cross-language ordering and list-root bytes before those outputs can become protocol authority.

The specification's section 9.2 displayed equation is corrected to state all three pairwise intersections already required by its prose, section 18, and `ZRM-CBC-003`.

### Technical design choice

**Design forces:** Counts must reject before allocation; capacity, duplicate, and collision errors need exact deterministic precedence; the implementation must remain `no_std` plus `alloc`; no canonical ABI is being introduced; and the production path must stay small enough for direct audit and bounded model checking.

**Pattern selected:** Use a sealed validated value object behind a staged constructor, with bounded insertion canonicalization and private role storage. No additional named design pattern is added because one would obscure the local invariants without adding an authority boundary or useful extension point.

**Invalid states prevented:** Public construction cannot produce over-limit counts, unsorted role lists, within-role duplicates, cross-role collisions, or caller-selected ordinals. The resulting type remains explicitly structural and cannot represent resource-body, transition, or state authority.

**Extension point or closed-set reason:** The three structural roles are a closed v1 set because their semantics and reject order are normative. Application-defined resource kinds and logic remain outside this crate. A future role or canonical role tag requires an explicit protocol change rather than an open plugin hook.

**Alternatives rejected:** A general-purpose sort increased bounded-model cost and exposed more library machinery. A new fixed-capacity collection dependency would enlarge the supply chain. Stack arrays of optional entries would complicate the public API and movement logic. Caller-supplied ordinals or sentinel-filled storage would make invalid states representable. Detecting duplicates during insertion would allocate malformed candidates and make structural rejection depend on reaching host allocation first.

**Pattern-specific failure modes:** Borrowed duplicate and collision scans plus insertion sorting are quadratic, but each list is capped at 256 entries. Reservation failure is a typed role-local operational error and cannot be made deterministic without allocator injection. The validated object is not `Clone`, which avoids an implicit second allocation. Structural success could still be misused as authority by a later stage, so module documentation, private fields, CBC non-claims, and the next staged type must preserve that boundary.

**Enforcement and tests:** Private fields and constructors enforce the representation invariant. Ordinary tests, two independent exhaustive boundary atlases, a structure-aware fuzz oracle, Kani harnesses, mutation analysis, line and branch coverage, Miri, strict lints, architecture checks, and dependency inventories exercise the boundary from independent directions.

**Technical AI-review status:** Complete for the implementation mechanics and pattern choice. Human review is requested only for the specified behavior, evidence, residual gaps, and future semantic changes.

### Evidence plan

- exact empty, zero-limit, at-limit, and limit-plus-one tests for every role;
- every within-role duplicate and cross-role collision family;
- a deterministic mixed-defect precedence atlas;
- ascending canonical output, input preservation, lookup, and ordinal tests;
- exhaustive small-universe role assignment and permutation properties;
- Kani over the production constructor for singleton count/collision domains and over the production duplicate validator for a two-item domain, with reachable success and reject covers;
- a structure-preserving fuzz target with committed boundary seeds and deterministic replay assertions;
- changed-crate line and branch coverage;
- zero missed mutants in the changed critical implementation;
- Miri, strict Clippy, formatting, architecture, conformance, complexity, quality, hygiene, and manifest gates.

The boundary-concolic-style atlas is offline bug-discovery evidence. Any discovered case is promoted into an ordinary deterministic regression. It is not a correctness proof.

Canonical sorting and ordinals are exercised by exhaustive ordinary atlases, fixed ceiling cases, the independent fuzz oracle, branch coverage, and mutation analysis. They are not claimed as model-checked in this slice. Public-constructor capacity failure is not deterministically injectable; the private reservation helper has exact role-local failure tests, and the host-dependent public case remains an explicit evidence gap.

### Dependencies and resource bounds

Add the specification-planned `zrm-kernel` crate with inward dependencies only on `zrm-types` and `zrm-policy`. Add no third-party dependency. The candidate borrows caller-owned slices. Each role is bounded by its validated policy limit and the v1 protocol ceiling of 256 entries. All three counts reject before any internal allocation. Sorting is bounded by three lists of at most 256 fixed-width identifiers. Caller-side construction of the input slices remains outside this constructor's allocation claim.

### Non-claims

- supplied policy limits are not authenticated or active policy;
- supplied IDs are not rebound to canonical resource bodies;
- no transition, membership, freshness, nullifier, logic, accounting, state, or commit check occurs;
- no canonical role bytes, roots, hashes, or stable reject ABI exist;
- no production-readiness or funds-safety claim is created;
- `ZRM-CBC-003` can reach only `implemented_partial` until later kernel stages obligatorily consume this type before logic verification.

## Verification record

Final local replay on the candidate working tree produced the following evidence:

- Rust quality: formatting, locked metadata, workspace check, strict Clippy, all-target tests, doc tests, and rustdoc passed. The workspace ran 86 ordinary tests with zero failures; `zrm-kernel` contributed 16.
- Independent boundary atlases: two separate 8^3 sequence atlases each checked 512 exact outcomes. They cover count-first precedence, nonadjacent duplicates, all collision pairs, and mixed defects. Protocol boundaries at 256 and 257 entries passed for each role; the simultaneous 768-ID case passed with terminal ordinal 255 in every role.
- Python and repository policy: 73 tool tests passed. Architecture, CBC conformance, package manifest, repository hygiene, deterministic corpus, and independent protocol-vector replay passed.
- Complexity and quality: 29 Rust files and 230 functions produced zero preferred-limit warnings and zero approved exceptions. The multi-axis quality report reached `excellent-candidate` with 16 rules, five design decisions, zero findings, and zero advisories.
- Coverage: workspace line coverage was 98.67% and branch coverage was 99.09%. `zrm-kernel` reached 100.00% line and 100.00% branch coverage. The existing `zrm-policy` ratchet remained at 99.70% line and 100.00% branch coverage.
- Mutation: the final `zrm-kernel` campaign tested 36 candidates; 23 were caught, 13 did not compile, zero were missed, and zero timed out. An earlier run exposed one operator mutation equivalent only under the duplicate-free precondition; the implementation was clarified to state the ordering predicate directly and the zero-miss campaign was rerun. The first hosted full-workspace campaign then exposed six missing direct assertions for the three policy-limit getters because cargo-mutants does not rely on downstream-crate tests when mutating `zrm-policy`. Distinct policy-level assertions were added, and the complete local workspace replay passed 344 candidates: 268 caught, 76 unviable, zero missed, and zero timed out.
- Kani 0.60.0: the count-precedence constructor harness had 0/942 failed checks and 4/4 satisfied covers; the collision-precedence constructor harness had 0/930 failed checks and 4/4 covers; the direct production duplicate validator had 0/298 failed checks and 3/3 covers. The final workspace replay verified 11/11 harnesses with zero failures. Earlier whole-constructor two-item sort attempts exceeded the local 180-second budget and provide no evidence.
- Miri on `nightly-2025-03-02`: all 86 workspace tests and doc tests passed on exercised executions. The kernel's maximum-ceiling atlas completed in 161.20 seconds.
- Structure-aware fuzzing: fixed replay loaded exactly ten named seeds and completed 11 runs with `cov=392`, `ft=535`. A subsequent ten-second request completed 2,526 executions in 11 seconds with `cov=452`, `ft=1041`, no crash, assertion failure, hang, or timeout. Hash-named campaign discoveries were removed; the deterministic corpus check again confirmed exactly ten named role seeds.
- Supply chain: RustSec scans passed for 14 root and 23 fuzz dependencies; both cargo-deny graphs passed advisories, bans, licenses, and source policy. Deterministic BOM generation reported 23 source components, 63 dependency edges, and one cryptography component.
- Review: two independent AI adversarial passes reported no remaining behavioral code blocker. Technical pattern and syntax review is complete.
- Hosted CI: the first assurance run passed coverage and exposed six missing direct assertions during its full mutation campaign. After the focused regression and 344-mutant local replay, GitHub Actions run 18 passed all five jobs: quality, dependency review, fuzz smoke, assurance, and supply chain.

Kani emitted target-feature, future-compatibility, and unsupported-construct warnings. Unsupported paths were unreachable in the successful harness results. Kani evidence is restricted to the stated bounded domains. Miri and fuzzing cover exercised executions only. The configured hosted 45-second and nightly 900-second fuzz campaigns were not run locally.

The remaining assurance gaps are human review of the specified behavior and evidence, hosted CI, public-constructor allocator-failure injection, a Class E canonical role/list ABI, obligatory consumption by the later prevalidated-transition stage, and every later resource-body, membership, logic, accounting, state, atomicity, journal, proof, release, and external-audit obligation.
