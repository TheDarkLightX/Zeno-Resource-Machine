# ResourceKindPolicyV1 RFC-0002 proposed quantity oracle

**Status:** proposed semantic amendment; non-normative unless RFC-0002 is
accepted through the repository's governed RFC process

This artifact is separate from the frozen prior-specification oracle. It does
not reinterpret or replace that baseline. It makes the RFC-0002 review proposal
executable so reviewers can inspect the exact state-space delta before deciding
whether to accept the amendment.

## Design packet

```text
Change classification:
  Class C proposed reference-semantic artifact. It changes no production or
  authority path and cannot make its own proposal normative.
Goal:
  Encode the supplied RFC-0002 quantity, lifecycle, and reason-precedence
  amendment beside the frozen baseline, then prove the bounded differential
  corpus contains exactly the intended delta.
Affected crates/modules:
  New Python-only RFC-0002 artifacts under reference_models/. Existing baseline
  oracle files remain byte-for-byte unchanged.
Exact typed statement or API:
  decide_rfc0002_policy_construction(PolicyCandidateV1) -> ProposedDecision
  decide_rfc0002_resource_quantity(
    PolicyCandidateV1,
    ResourceQuantityCandidateV1,
  ) -> ProposedDecision
Authority boundary:
  Inert candidates enter two pure functions. Results are non-authoritative and
  construct no policy capability, resource, verified fact, plan, or journal.
Invariants preserved/added:
  Supported v1 schema; ordered validity window; bounded u64/u128 values; every
  policy-bound resource quantity is positive; exact UnitId equality;
  LifecycleNonFungible policy quantity_max is exactly 1; lifecycle resource
  quantity is exactly 1; general quantities do not exceed quantity_max.
Disaster states affected:
  Divergent lifecycle-policy construction, zero-marker ambiguity, mixed units,
  incorrect reject precedence, integer truncation, and reference/runtime drift.
Canonical bytes or hashes affected:
  None. The proposal defines logical decisions only and does not freeze policy
  authority bytes.
Compatibility/versioning impact:
  If accepted, lifecycle policies with quantity_max 0 or greater than 1 move
  from baseline construction acceptance to rejection. RFC-0002 proposes an
  in-place pre-alpha amendment because no canonical policy bytes, durable policy
  identity, or activation path exists; reviewers must approve that precondition.
Tests to add first:
  All accounting modes; maximum 0/1/>1/u128::MAX; unit mismatch; positive
  quantities; EvidenceOnly zero; exact constructor and resource precedence; and
  exhaustive bounded differential checks against the frozen baseline.
Formal/model obligations:
  Proposed policy acceptance equals baseline acceptance intersected with
  (mode != LifecycleNonFungible or quantity_max == 1). Proposed resource
  acceptance equals the baseline relation except that baseline lifecycle states
  with quantity_max > 1 and quantity 1 are removed.
Dependency impact:
  Python standard library and the frozen repository-local baseline oracle only.
Performance/resource bounds:
  Constant time and space per decision. Differential tests enumerate a fixed
  bounded domain.
Non-claims and known gaps:
  RFC-0002 is not accepted by this artifact. No policy codec/hash, migration,
  authenticated activation, transition accounting, proof, or runtime refinement
  is established. CBC status remains unchanged.

Design forces:
  Preserve the historical oracle, isolate the proposal, expose semantic versus
  reason-only deltas, and fail closed at typed boundaries.
Pattern selected, or no additional pattern:
  No additional pattern. A separate module and two pure functions make proposal
  status and decision order locally visible.
Invalid states prevented:
  Lifecycle maxima other than 1, lifecycle resource quantities other than 1,
  zero policy-bound quantities, unlike units, over-maximum quantities, reversed
  windows, and out-of-width integers.
Extension point or closed-set reason:
  AccountingMode remains the closed v1 set. RFC-0002 changes one mode's
  construction invariant and does not add an enum variant.
Alternatives rejected:
  Editing the frozen baseline; deriving behavior from production code; treating
  EvidenceOnly as marker permission; and mixing migration policy into the local
  decision relation.
Pattern-specific failure modes:
  Callers may mistake a proposed decision for current normative behavior. File,
  type, function, reason, and documentation names therefore carry RFC0002 or
  Proposed labels.
Enforcement and tests:
  Standard-library unit tests, machine-readable counterexample replay, baseline
  hash checks, and exhaustive bounded differential assertions.
Technical AI-review status:
  Proposed and awaiting independent semantic review and governed RFC decision.
```

## RFC-0002 candidate amendment

The proposed model takes the following RFC-0002 candidate rules as input rather
than deriving them from an implementation:

1. V1 has no marker permission. Every policy-bound resource quantity is
   positive.
2. `LifecycleNonFungible` policy construction requires `quantity_max == 1`.
3. A non-lifecycle `quantity_max == 0` remains constructible as an empty policy
   candidate.
4. Constructor semantic precedence is schema, validity window, then lifecycle
   maximum.
5. After a policy has constructed, resource semantic precedence is unit
   mismatch, lifecycle exact-one, general zero, then maximum.

Host-language width checks remain fail-closed boundary checks. They do not
authorize a different semantic order for typed v1 values.

## Frozen baseline integrity

The proposed artifacts import but do not edit the baseline first recorded by
the isolated oracle track at
`5ea0c1b104b40e93f3896edf0d4e095d0a9de1c7` and integrated on this branch as
`721200c`. Its tracked file hashes at proposal start are:

| Baseline artifact | SHA-256 |
| --- | --- |
| `RESOURCE_KIND_POLICY_V1_ORACLE.md` | `98e3f1950b586a48faf0a4684d1d779f18b74f911671e784af6626c2eb84d2a3` |
| `resource_kind_policy_v1.py` | `430e4260eead5d1fa88925be75f87d283b5b47eb2b8b2436765c2280dcc4c2c6` |
| `resource_kind_policy_v1_counterexamples.json` | `d5fe2b126748cccce346518310a9329b8709d678fa4bf454e5176af978fda334` |
| `tests/test_resource_kind_policy_v1.py` | `37ba70e4a1051f0a688827f507bacdf893e68c979d7d10dac0b546faf8a69a3e` |

## Proposed decision table

`U` is the policy unit, `V` is a different unit, and `M = 2^128 - 1`.

### Policy construction

| Mode | quantity_max | Proposed decision | Reason |
| --- | ---: | --- | --- |
| LifecycleNonFungible | 0 | reject | lifecycle policy maximum must equal 1 |
| LifecycleNonFungible | 1 | accept | proposed policy shape valid |
| LifecycleNonFungible | 2 | reject | lifecycle policy maximum must equal 1 |
| LifecycleNonFungible | M | reject | lifecycle policy maximum must equal 1 |
| every non-lifecycle mode | 0 | accept | constructible empty candidate |
| every non-lifecycle mode | 1 | accept | proposed policy shape valid |
| every non-lifecycle mode | M | accept | exact u128 maximum is valid |

### Resource quantity under a proposed-constructible policy

| Mode and maximum | Unit | Quantity | Proposed decision | Reason |
| --- | --- | ---: | --- | --- |
| LifecycleNonFungible, 1 | V | 0 | reject | unit mismatch precedes lifecycle and zero |
| LifecycleNonFungible, 1 | U | 0 | reject | lifecycle quantity must equal 1 |
| LifecycleNonFungible, 1 | U | 1 | accept | exact lifecycle quantity |
| LifecycleNonFungible, 1 | U | 2 | reject | lifecycle quantity must equal 1 before maximum |
| ConservedFungible, 0 | U | 0 | reject | positive quantity required before maximum |
| ConservedFungible, 0 | U | 1 | reject | exceeds maximum |
| ConservedFungible, 1 | U | 0 | reject | positive quantity required |
| ConservedFungible, 1 | U | 1 | accept | structural quantity valid |
| Transformable, M | U | M | accept | structural only; transformation remains unestablished |
| EvidenceOnly, 1 | U | 0 | reject | no v1 marker permission |
| EvidenceOnly, 1 | U | 1 | accept | structural only; evidence meaning remains unestablished |

## Exact differential contract

The comparison domain uses otherwise-valid v1 candidates and matching units.

| Surface | Frozen baseline | RFC-0002 proposal | Delta class |
| --- | --- | --- | --- |
| lifecycle policy max 0 | accept | reject lifecycle maximum | acceptance-set removal |
| lifecycle policy max 1 | accept | accept | none |
| lifecycle policy max >1 | accept | reject lifecycle maximum | acceptance-set removal |
| lifecycle resource max >1, quantity 1 | accept | reject invalid proposed policy | acceptance-set removal |
| lifecycle resource max 1, quantity 0 | reject general zero | reject lifecycle exact-one | reason only |
| lifecycle resource max 1, quantity 2 | reject maximum | reject lifecycle exact-one | reason only |
| valid policy plus unit mismatch | reject unit mismatch | reject unit mismatch | none |
| any non-lifecycle policy/resource decision | baseline decision | same decision | none |
| EvidenceOnly marker and positive cases | baseline decision | same decision | none |

For a bounded domain with maxima `0..4` and resource quantities `0..5`, the
only policy accept/reject changes are lifecycle maxima `{0, 2, 3, 4}`. The only
resource accept/reject changes are `(LifecycleNonFungible, maximum, quantity 1)`
for maxima `{2, 3, 4}`. Differential tests assert both directions so no proposed
acceptance may appear outside the baseline relation.

## Remaining proposal ambiguities

1. RFC-0002 selects an in-place pre-alpha amendment on the recorded condition
   that no canonical or durable lifecycle policy identity exists. Review must
   verify and approve that condition; finding any durable external record
   requires a new schema/version and migration design.
2. Stable protocol reject codes are not supplied. Proposed reason names express
   the requested relative precedence and remain noncanonical.
3. The policy schema still cannot express a zero marker. `EvidenceOnly` remains
   structurally positive and semantically under-specified.
4. A non-lifecycle maximum of 0 intentionally constructs an empty candidate,
   but no authenticated activation or operational disablement semantics are
   established here.
5. The proposed in-place v1 disposition is not self-approving. Until RFC-0002
   receives the required human and independent approvals, the narrowed
   lifecycle state space remains an implementation candidate only.

## Agent work log

```text
Summary:
  Added a separate non-normative RFC-0002 proposed oracle, decision tables,
  machine-readable counterexamples, baseline-integrity checks, and exact bounded
  differential tests. The frozen baseline was not edited. The proposed artifacts
  are reachable on the integration branch through commit 9f2c2de.
Files changed:
  reference_models/RESOURCE_KIND_POLICY_V1_RFC0002_PROPOSED.md
  reference_models/resource_kind_policy_v1_rfc0002_proposed.py
  reference_models/resource_kind_policy_v1_rfc0002_proposed_counterexamples.json
  reference_models/tests/test_resource_kind_policy_v1_rfc0002_proposed.py
Typed statements/APIs changed:
  No protocol API changed. ProposedDecision, ProposedDecisionKind,
  ProposedReason, decide_rfc0002_policy_construction, and
  decide_rfc0002_resource_quantity exist only in the proposed Python model.
Invariants added or preserved:
  V1 positive quantities; exact units; u64/u128 widths; schema then validity then
  lifecycle-constructor precedence; lifecycle maximum exactly 1; unit then
  lifecycle then zero then maximum resource precedence; non-lifecycle empty
  policy candidates remain constructible.
Disaster states addressed:
  Silent baseline rewrite, unintended acceptance expansion, lifecycle-policy
  ambiguity, reject-precedence divergence, implicit EvidenceOnly marker
  permission, unit confusion, and integer truncation.
Tests added:
  24 proposed-oracle tests. Together with 21 frozen-baseline tests, discovery
  runs 45 tests. The differential corpus enumerates five modes, maxima 0 through
  4, quantities 0 through 5, and both acceptance-delta directions.
Mutants killed:
  No mutation tool was run. These artifacts alter no production guard and make
  no mutation-evidence claim.
Formal/model evidence:
  Executable bounded differential evidence only. It confirms exactly four
  removed policy states, exactly three removed resource states, no added accepted
  state, and five reason-only changes for common valid policies in the stated
  domain. This is not an unbounded proof or runtime refinement result.
Commands run and exact results:
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference_models/tests -v
    Initial test-first run: FAILED with one missing proposed-module import.
    Intermediate run: FAILED with two missing counterexample-file errors; all
    implemented model and differential tests passed.
    Final recorded semantic result: OK, 45 tests.
  python3 -m json.tool
    reference_models/resource_kind_policy_v1_rfc0002_proposed_counterexamples.json
    Exit 0; JSON parsed successfully.
  sha256sum over all four baseline oracle artifacts
    All hashes matched the frozen values recorded above.
  git diff --check
    Exit 0; no whitespace errors.
Canonical hashes/vectors changed:
  None. The JSON cases are noncanonical proposed decision records.
Dependencies changed:
  None; Python standard library plus frozen local inert input types.
Performance/resource-bound impact:
  Each oracle decision is constant time and space. Test enumeration is fixed and
  bounded.
Remaining gaps and non-claims:
  RFC-0002 is not accepted by this commit. No Rust production source, Rust test,
  implementation branch, or other worktree was inspected. No canonical policy
  codec, durable policy identity, authenticated activation, transition
  accounting, formal proof, runtime comparison, CBC promotion, or release claim
  is provided. The in-place pre-alpha disposition remains subject to human
  approval and invalidation if durable predecessor state is discovered.
```
