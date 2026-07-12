# ResourceKindPolicyV1 quantity oracle

**Status:** independent, non-authoritative executable interpretation of the
draft v0.1 specification

## Design packet

```text
Change classification:
  Class C reference-semantic artifact. It is isolated from every production
  authority path and does not promote a CBC obligation.
Goal:
  Make the ResourceKindPolicyV1 quantity and lifecycle rules executable without
  consulting an implementation.
Affected crates/modules:
  New Python-only artifacts under reference_models/. No Rust crate or authority
  path changes.
Exact typed statement or API:
  decide_policy_construction(PolicyCandidateV1) -> Decision
  decide_resource_quantity(PolicyCandidateV1, ResourceQuantityCandidateV1)
    -> Decision
Authority boundary:
  The model consumes inert values and returns a non-authoritative decision. It
  constructs no policy capability, verified fact, resource, commit plan, or
  journal.
Invariants preserved/added:
  Supported schema; ordered validity window; u128 quantity bounds; exact UnitId
  equality; zero quantity requires an explicit marker permission unavailable in
  ResourceKindPolicyV1; quantity does not exceed quantity_max; and every
  LifecycleNonFungible resource has quantity 1.
Disaster states affected:
  Unlike units treated as equivalent; lifecycle resources admitted with a
  non-unit quantity; zero markers inferred from an ambiguous mode; integer
  overflow or truncation; and divergent reference/optimized decisions.
Canonical bytes or hashes affected:
  None. ResourceKindPolicyV1 authority bytes are not frozen by the draft.
Compatibility/versioning impact:
  None. This model names its interpretation and does not define a wire ABI.
Tests to add first:
  Every accounting mode; unit mismatch; zero; quantity_max edges; u128 maximum;
  lifecycle maxima 0, 1, and greater than 1; and EvidenceOnly ambiguity.
Formal/model obligations:
  For non-lifecycle modes, structural quantity acceptance is equivalent to
  same-unit and 1 <= quantity <= quantity_max. For LifecycleNonFungible, it is
  equivalent to same-unit and quantity == 1 <= quantity_max.
Dependency impact:
  Python standard library only.
Performance/resource bounds:
  Constant time and constant space. Python integers are range-checked before
  they are interpreted as protocol u128 values.
Non-claims and known gaps:
  This model does not authenticate policy selection, decide transition
  accounting, establish evidence semantics, define canonical policy bytes, or
  prove refinement to a runtime implementation. The CBC matrix is intentionally
  unchanged and no obligation status is promoted by this independent artifact.

Design forces:
  Literal BCP 14 rules, fail-closed zero handling, transparent boundary behavior,
  and separation between policy construction and resource admission.
Pattern selected, or no additional pattern:
  No additional design pattern. Two pure decision functions keep the invariant
  families visible.
Invalid states prevented:
  Unsupported schema, reversed validity range, non-u128 values, mixed units,
  unauthorized zero quantity, quantity above the policy maximum, and lifecycle
  quantity other than 1.
Extension point or closed-set reason:
  AccountingMode is the specification's closed v1 set. Unknown modes are outside
  this typed model and must be rejected by a preceding strict decoder.
Alternatives rejected:
  Treating EvidenceOnly as implicit zero-marker permission; forcing lifecycle
  quantity_max to equal 1; and merging transition accounting authority into this
  resource-level decision.
Pattern-specific failure modes:
  None. The main residual risk is specification ambiguity, recorded below.
Enforcement and tests:
  Standard-library unittest boundary and decision-table replay.
Technical AI-review status:
  Awaiting independent review; this artifact cannot promote itself.
```

## Normative basis

The model composes these rules from `SPECIFICATION.md`:

- section 11.2: unknown schema versions reject;
- section 13.2: quantity is nonzero unless the resource-kind policy explicitly
  permits zero-quantity marker resources, quantity does not exceed the policy
  maximum, and unit equals the policy unit;
- section 14: `LifecycleNonFungible` resources have quantity `1`, while
  `EvidenceOnly` resources carry no monetary or fungible quantity semantics;
- sections 21.1 and 21.4: quantities are nonnegative `u128` values, arithmetic is
  checked, and different units are not combined without transformation;
- section 25: resource-policy validation precedes transition accounting and is
  separate from authenticated transformation or authority facts.

## Derived decisions and explicit assumptions

1. `quantity_max` is a resource upper bound, not a constructor equality rule.
   The specification does not require an admitted policy to have a nonempty
   resource set. Therefore every `u128` maximum is constructible for every mode.
2. The lifecycle rule composes with the general maximum rule. A lifecycle policy
   with maximum `0` constructs but admits no resource. Maximum `1` admits only
   quantity `1`. A maximum greater than `1` still admits only quantity `1`.
   Consequently, `LifecycleNonFungible.quantity_max == 1` is not derivable from
   the prior specification. Enforcing that equality requires an approved
   semantic amendment, including its compatibility and precedence decisions.
3. `EvidenceOnly` does not itself explicitly permit a zero-quantity marker. The
   v1 schema has no dedicated zero-marker-permission field, so zero rejects for
   every mode.
4. A positive `EvidenceOnly` quantity can pass the structural quantity checks,
   but the model cannot establish that an application will avoid monetary or
   fungible interpretation. Such acceptance carries an explicit semantic
   non-claim.
5. `schema_version == 1` and `validity_start_epoch <= validity_end_epoch` are
   construction preconditions. The model reports schema before validity when
   both fail. That reason precedence is an oracle convention; the draft fixes
   stage ordering but does not assign ResourceKindPolicyV1 reason codes.
6. Unit mismatch is reported before quantity errors within this model. Only the
   accept/reject result is claimed as the derived semantic decision.

Assumptions 1, 3, and 5 require specification review before this artifact can be
treated as a normative protocol oracle. In particular, a future schema could
require inhabited policies, normalize lifecycle maxima to `1`, or add explicit
zero-marker permission.

## Decision table

`U` means the policy unit, and `V` means a different nonzero unit. `M` is
`2^128 - 1`.

| Mode | quantity_max | Resource unit | quantity | Decision | Reason |
| --- | ---: | --- | ---: | --- | --- |
| ConservedFungible | 1 | U | 0 | reject | zero needs explicit marker permission |
| ConservedFungible | 1 | U | 1 | accept | structural quantity valid |
| ConservedFungible | 1 | U | 2 | reject | exceeds maximum |
| AuthorityMintableFungible | 2 | U | 2 | accept | structural quantity valid |
| AuthorityMintableFungible | M | U | M | accept | exact u128 maximum is representable |
| AuthorityMintableFungible | M | U | M + 1 | reject | not a protocol u128 |
| LifecycleNonFungible | 0 | U | 1 | reject | exceeds maximum |
| LifecycleNonFungible | 1 | U | 1 | accept | exact lifecycle quantity |
| LifecycleNonFungible | 2 | U | 1 | accept | exact lifecycle quantity |
| LifecycleNonFungible | 2 | U | 2 | reject | lifecycle quantity must be 1 |
| LifecycleNonFungible | M | U | M | reject | lifecycle quantity must be 1 |
| Transformable | M | U | M | accept | resource shape only; transformation still required for unmatched deltas |
| EvidenceOnly | 1 | U | 0 | reject | mode is not explicit zero-marker permission |
| EvidenceOnly | 1 | U | 1 | accept | structural only; nonmonetary semantics remain unestablished |
| EvidenceOnly | M | U | M | accept | structural only; nonmonetary semantics remain unestablished |
| every mode | M | V | 1 | reject | unit mismatch |

Policy construction is independent of the resource rows above:

| Mode | quantity_max | Construction decision | Admitted quantities |
| --- | ---: | --- | --- |
| LifecycleNonFungible | 0 | accept | none |
| LifecycleNonFungible | 1 | accept | `{1}` |
| LifecycleNonFungible | 2 | accept | `{1}` |
| LifecycleNonFungible | M | accept | `{1}` |
| every other mode | 0 | accept | none under v1's no-zero rule |
| every other mode | n, where 1 <= n <= M | accept | structurally `{1, ..., n}` |

## Scope of mode-specific acceptance

- `ConservedFungible`: this model does not establish zero mint/burn or
  conservation across a transition.
- `AuthorityMintableFungible`: this model does not establish a sealed mint or
  burn authority fact.
- `LifecycleNonFungible`: this model establishes only the local exact-quantity
  shape, not lifecycle transition authorization or uniqueness.
- `Transformable`: this model does not establish exact transformation coverage.
- `EvidenceOnly`: this model establishes only the local numeric shape and makes
  no claim that downstream semantics are nonmonetary or nonfungible.

## Agent work log

```text
Summary:
  Added an implementation-independent Python oracle, boundary tests, decision
  tables, and replayable counterexample findings derived from origin/main at
  revision 794e8255ca6d63d3068c90ade3c47a24075648b9.
Files changed:
  reference_models/RESOURCE_KIND_POLICY_V1_ORACLE.md
  reference_models/resource_kind_policy_v1.py
  reference_models/resource_kind_policy_v1_counterexamples.json
  reference_models/tests/test_resource_kind_policy_v1.py
Typed statements/APIs changed:
  No protocol API changed. New inert PolicyCandidateV1,
  ResourceQuantityCandidateV1, Decision, and two pure decision functions exist
  only in the Python oracle.
Invariants added or preserved:
  Exact units, u64/u128 ranges, no implicit zero permission, policy maximum, and
  lifecycle quantity exactly one.
Disaster states addressed:
  Unit confusion, mode-specific quantity bypass, implicit marker permission,
  truncation at u128 boundaries, and cross-implementation decision drift.
Tests added:
  21 unittest cases, including exhaustive small-domain checks and replay of all
  eight machine-readable counterexamples.
Mutants killed:
  No mutation tool was run. This change adds no production guard and makes no
  mutation-evidence claim.
Formal/model evidence:
  Executable finite boundary evidence only. The small-domain test checks all five
  modes, quantity maxima 0 through 4, and quantities 0 through 5. This is not a
  proof or runtime refinement result.
Commands run and exact results:
  python3 -m unittest discover -s reference_models/tests -v
    Initial test-first run: FAILED, 1 import error because the oracle module did
    not yet exist.
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference_models/tests -v
    Final recorded semantic result: OK, 21 tests.
  python3 -m json.tool reference_models/resource_kind_policy_v1_counterexamples.json
    Exit 0; JSON parsed successfully.
  git diff --check
    Exit 0; no whitespace errors.
Canonical hashes/vectors changed:
  None.
Dependencies changed:
  None; Python standard library only.
Performance/resource-bound impact:
  Oracle decisions use constant time and space over fixed scalar inputs.
Remaining gaps and non-claims:
  No Rust source or Rust test was inspected before freezing this oracle. No
  implementation comparison was performed. The oracle is not authenticated,
  canonical, proof-backed, formally refined, release-backed, or authoritative.
  Human semantic review and any approved specification amendment remain pending.
```
