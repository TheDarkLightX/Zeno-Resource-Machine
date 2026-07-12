# WP3b intrinsic resource construction work log

**Date:** 2026-07-11

## Design packet

### Goal and change class

Implement the policy-independent semantic boundary between the frozen
`ResourceWireV1` candidate and a sealed typed resource body. This is a Class C
semantic change. It advances `ZRM-CBC-002` and `ZRM-CBC-016`, while preserving
the existing `ZRM-CBC-001` canonical body-to-ID binding and `ZRM-CBC-019`
strict-decoder boundary. It does not claim a final `ResourceV1`, active policy,
state membership, transition validity, or commit authority.

### Typed boundary

```text
ResourceWireV1
  -> IntrinsicResourceV1
  | IntrinsicResourceErrorV1
```

The exact public construction API is:

```rust
impl IntrinsicResourceV1 {
    pub fn try_from_wire(
        wire: &ResourceWireV1,
    ) -> Result<Self, IntrinsicResourceErrorV1>;
}

impl TryFrom<ResourceWireV1> for IntrinsicResourceV1;
```

The inherent constructor borrows the syntactic candidate; the standard
`TryFrom` conversion consumes it. Both use the same private implementation.
The version-specific input type fixes the v1 field set and canonical
encoder/header, regardless of whether it came from strict decoding or direct
candidate construction. It establishes no decoder provenance or
authentication. Schema version one is implicit because the type has no runtime
version selector. The public, closed local error API is:

```rust
pub enum IntrinsicResourceErrorV1 {
    ZeroField { field: IntrinsicResourceFieldV1 },
    ExpiryBeforeCreation { created_epoch: u64, expiry_epoch: u64 },
    UnknownFlags { bits: u32 },
    ResourceIdDerivation(ResourceIdDerivationError),
}
```

`IntrinsicResourceFieldV1` publicly names the thirteen nonzero identifier/root
fields plus `Nonce`. `ResourceIdDerivationError` remains the existing public
codec error. No constructor accepts a `ResourceId`.

`IntrinsicResourceV1` has private fields. Successful construction establishes
only these facts:

- every identifier, commitment, root, and the resource nonce satisfies its
  local nonzero representation invariant;
- an expiry epoch, when present, is not earlier than the creation epoch;
- version-one flags contain no unknown bits;
- quantity and epoch widths are preserved exactly;
- `ResourceId` was derived from the complete existing canonical
  `ResourceWireV1` value through the frozen resource hash framing.

The caller cannot provide the stored `ResourceId`. The input wire value remains
unauthenticated, and intrinsic success grants no policy, state, logic, role, or
transition authority.

### Local behavior and error precedence

The constructor checks deterministic semantic defects in canonical field-tag
order:

1. zero `machine_id`;
2. zero `domain_id`;
3. zero `application_id`;
4. zero `resource_kind_id`;
5. zero `resource_logic_id`;
6. zero `logic_profile_id`;
7. zero `resource_kind_policy_id`;
8. zero `unit_id`;
9. zero `label_root`;
10. zero `value_root`;
11. zero `controller_root`;
12. zero `policy_root`;
13. zero `provenance_root`;
14. zero `nonce`;
15. `expiry_epoch < created_epoch`;
16. any nonzero version-one flag bit;
17. bounded canonical encoding or resource-ID derivation failure.

These are local typed errors and local implementation precedence only. This
slice assigns no stable `RejectCodeV1`, public diagnostic envelope, canonical
error tag, or cross-stage reject number. A later final `ResourceV1` constructor
must freeze its complete quantity, epoch, flag, and policy-error precedence
before composing this stage; it must not infer normative final precedence from
the order above.
Resource-ID derivation runs only after deterministic intrinsic checks, so a
host allocation failure cannot mask an earlier semantic defect.

`quantity_atoms == 0` is preserved as unresolved data at this stage. Section
13 permits zero only when resource-kind policy explicitly permits marker
resources, but the current `ResourceKindPolicyV1` logical schema contains no
field expressing that permission. Intrinsic construction therefore neither
accepts nor rejects zero as a policy-valid quantity. A later reviewed policy
stage must resolve the schema gap before constructing final `ResourceV1`.

### Disaster states and obligations

- a caller-selected identifier is detached from the resource body;
- an all-zero semantic field reaches later authority checks in a typed object;
- an expired-before-created resource is representable as intrinsically valid;
- an unknown flag silently changes v1 semantics;
- a width conversion truncates quantity or epoch data;
- policy-dependent validation is mislabeled as complete resource validity;
- a codec or allocator failure changes the precedence of an earlier semantic
  reject.

### Canonical ABI and compatibility impact

No canonical bytes, hash domain, field tag, stable reject code, policy schema,
or `ResourceId` construction changes. The constructor reuses the reviewed
`ResourceWireV1::resource_id()` path and exact WP1 vectors. `ResourceNonce` is
an in-memory opaque nonzero type only; it introduces no separate wire form.

Adding `zrm-kernel -> zrm-codec` is an inward dependency on the existing
foundational wire layer. The architecture allowlist is updated explicitly. No
third-party dependency is added.

### Technical design choice

**Design forces:** The body-to-ID binding must be unforgeable through the public
API; local error order must remain visible and deterministic; the kernel must
stay `no_std`, deterministic, and side-effect free; hashing must reuse the one
frozen codec path; and unresolved policy semantics must remain outside the
validated type.

**Pattern selected:** Use a sealed validated value object behind a staged
constructor. Private grouped identity and commitment values keep the
constructor and getters auditable without creating a general service or
extension hierarchy. A closed field enum identifies the first failing local
invariant.

**Invalid states prevented:** Public construction cannot create an intrinsic
resource with a zero semantic field, invalid epoch order, unknown v1 flags, or
caller-selected resource ID. Quantity-policy validity and all authenticated
facts remain deliberately unrepresentable by this type.

**Extension point or closed-set reason:** The eighteen `ResourceWireV1` fields
and their canonical order are a closed v1 set. A new field, flag, byte layout,
or hash rule requires versioned protocol review. Application-defined resource
kinds and policy logic remain outside this module.

**Alternatives rejected:** Semantic checks in `zrm-codec` would mix parsing
with kernel policy-independent semantics. Rehashing inside `zrm-kernel` would
duplicate a canonical definition. Accepting a caller-provided ID would permit
body/identity substitution. Naming the result `ResourceV1` would overstate the
facts established. Performing local resource-kind-policy checks now would
force a decision about the missing zero-marker permission and still would not
authenticate policy membership.

**Pattern-specific failure modes:** The staged type may be mistaken for a final
resource unless documentation and names preserve the boundary. Getter drift
could expose the wrong field. Resource-ID derivation performs one bounded
allocation and can fail for host-dependent reasons. Later stages could bypass
this constructor unless their APIs obligatorily consume the sealed type.

**Enforcement and tests:** Private fields and the sole public constructor
enforce representation. Exact vector replay, every-field negatives, a complete
mixed-defect atlas, preservation and boundary tests, a structure-aware fuzz
oracle, Kani checks over the production intrinsic validator, line and branch
coverage, mutation analysis, Miri, strict lints, architecture checks, CBC
checks, dependency inventories, and independent adversarial review exercise
the boundary.

**Technical AI-review status:** Independent design and implementation reviews
are complete with no authority-boundary, semantic, or code-quality blocker.
Human attention is reserved for behavior, assurance evidence, residual
semantic gaps, and any future policy-schema decision.

### Evidence plan

- construct both committed WP1 vectors and match their exact `ResourceId`;
- reject each zero field independently and verify every pairwise mixed-defect
  precedence outcome;
- accept absent expiry and equality; reject earlier expiry; preserve `u64`
  boundaries;
- accept only zero flags and retain the exact rejected bits in local errors;
- model every nonzero `u32` flag pattern and retain the exact rejected bits;
- preserve zero, one, and `u128::MAX` quantities without granting policy
  validity;
- prove that every public getter returns the corresponding validated input;
- add a compile-fail API example showing that callers cannot initialize private
  fields or inject a `ResourceId`;
- confirm reject-is-no-op behavior: the pure borrowing constructor receives no
  mutable external capability, performs no I/O, and leaves its input unchanged
  on every reject;
- run a deterministic 65,536-case defect-mask atlas against an independent
  first-defect oracle;
- fuzz the same structure-preserving defect grammar and promote discoveries
  into ordinary regressions;
- use Kani on the production intrinsic-field validator for zero-field order,
  epoch/flag precedence, and symbolic `u128`/`u64` preservation, explicitly
  excluding SHA-256 correctness from that bounded model;
- require 100 percent line and branch coverage for the changed kernel crate and
  zero missed mutants in the changed critical implementation;
- run the full repository quality, policy, privacy, supply-chain, Miri, fuzz,
  and hosted assurance gates.

The boundary-concolic-style atlas and fuzzer are bug-discovery evidence. Kani
is limited to its stated bounded predicates. Neither establishes cryptographic
correctness, authenticated policy, or end-to-end funds safety.

### Dependencies and resource bounds

Add only the existing workspace `zrm-codec` dependency to `zrm-kernel`.
Construction performs fixed work over eighteen fields, encodes at most 603
bytes, allocates one bounded encoding buffer, and computes one SHA-256 resource
commitment. It performs no I/O, clock access, randomness, global mutation,
threading, or unbounded input traversal.

### Non-claims

- zero quantity is not established as policy-valid;
- resource-kind policy identity, content root, membership, activation,
  predecessor compatibility, and creation-policy selection are not checked;
- logic and logic-profile authorization are not checked;
- trusted epoch, role, ordinal, state membership, nonmembership, nullifier
  freshness, accounting, proofs, state roots, commit, and journals are not
  checked;
- no new stable ABI or reject taxonomy is introduced;
- `IntrinsicResourceV1` is not final `ResourceV1`, an accepted resource, or a
  production-readiness claim.

## Verification record

### Confirmed behavior

- both committed `ResourceWireV1` vectors construct the intrinsic type and
  retain their exact existing `ResourceId` values;
- all fourteen prohibited zero fields reject with the exact local field
  identity and deterministic first-error order;
- the complete 65,536-mask defect atlas reaches all sixteen semantic rejects
  plus success and matches an independent first-error oracle;
- expiry is accepted when absent or equal to creation and rejected only when
  earlier than creation;
- every nonzero version-one flag pattern is rejected with its exact bits;
- symbolic `u128` quantities and `u64` epochs are preserved exactly;
- rejected borrowed candidates remain byte-for-byte unchanged;
- the public API cannot initialize private fields or inject a `ResourceId`;
- zero quantity remains unresolved data and grants no policy-valid marker
  authority.

### Local assurance results

- Rust tests and documentation: 97 tests plus one compile-fail doctest passed,
  with zero failures. Strict Clippy, rustfmt, and rustdoc passed with zero
  denied warnings.
- Coverage: workspace line coverage was 98.81 percent and branch coverage was
  99.12 percent. `zrm-kernel` reached 100 percent line and 100 percent branch
  coverage. `zrm-policy` retained 99.70 percent line and 100 percent branch
  coverage.
- Mutation testing: the final focused WP3b run tested 36 candidates, caught
  12, classified 24 as unviable, and had zero missed or timed-out mutants. The
  full workspace run tested 380 candidates, caught 280, classified 100 as
  unviable, and had zero missed or timed-out mutants. Production source did
  not change after that workspace run; the later test-only broadening cannot
  reduce its caught set.
- Kani 0.60.0: all 16 workspace harnesses verified with zero failures. The five
  WP3b harnesses cover exact zero-field identity, pairwise precedence,
  epoch-before-flags precedence, symbolic full-width quantity and epoch
  preservation, and every arbitrary nonzero `u32` flag pattern. Their declared
  cover properties were reached. SHA-256 and allocation behavior remain
  outside the new bounded predicates.
- Miri on the pinned nightly: all 97 workspace tests and the compile-fail
  doctest passed with zero failures. The clean command completed in 1,334.827
  wall-clock seconds. Miri reported 655.61 seconds for the 65,536-case
  intrinsic atlas and 161.20 seconds for the inherited resource-role ceiling
  atlas.
- Fuzzing: the exact 18-seed replay completed 19 runs at `cov=296`, `ft=333`.
  A separate clean 10-second campaign completed 1,265,014 executions at `cov=306`,
  `ft=353`, with no crash, assertion failure, hang, or timeout. The committed
  corpus remained exactly the generated 18 named fixtures.
- Quality controls: complexity reported 33 Rust files, 273 functions, zero
  preferred-limit warnings, and zero exceptions. Code quality remained
  `excellent-candidate` across 16 rules and five design decisions, with zero
  findings and zero advisories.
- Repository and package controls: architecture, conformance, repository
  hygiene, corpus replay, independent vectors, and all 73 Python policy-tool
  tests passed. The conformance matrix retains 45 obligations and no
  production promotion.
- Replayability: 27 separate clean-source gate records include the required
  source revision, dirty state, exact tool identity and executable hash,
  tokenized command, environment-policy root, measured duration, result root,
  assumptions, exclusions, and non-claims. Their path and file hashes are
  bound by `evidence/wp3b-local-gates-2026-07-11.json`.
- Supply chain: both locked dependency closures passed `cargo-audit` and all
  cargo-deny advisory, ban, license, and source checks. The deterministic
  inventories contain 23 source components, 65 dependency edges, and one
  cryptography component.
- Review and publication scope: independent design and implementation reviews
  found no semantic, authority-boundary, body-to-ID substitution, or
  code-quality blocker. A publication scan found no prohibited private
  context, credentials, local paths, hidden-tool references, or unintended
  generated outputs in the intended change. An isolated post-commit diff
  review found no semantic defect and identified three assurance-publication
  blockers: the sustained-fuzz timeout, a missing revision-bound evidence and
  mutation receipt, and a missing scoped agent-review receipt. This follow-up
  raises the fuzz timeout to 90 minutes and adds the canonical gate, mutation,
  and agent-review receipts. The independent remediation closure review passed
  with zero blockers. Its attestation binds revision
  `6a906de7868264f4e9864c30eb0f007a01445592`, including the corrected mutation
  provenance and workflow budgets. Hosted CI remains pending.

The nightly Miri timeout is 30 minutes so the complete intrinsic and role
atlases can run on slower hosted workers without weakening the tests. The
nightly fuzz timeout is 90 minutes so four serial 900-second campaigns retain
setup and corpus-replay headroom.

### Remaining assurance and semantic gaps

- Human Class C review and merge approval remain required for this WP3b
  behavior and evidence packet.
- Hosted CI, scheduled sustained fuzzing, and future independent release gates
  remain required. Local evidence does not substitute for those gates.
- The policy schema still cannot express explicit zero-quantity marker
  permission. A later critical schema review must resolve that gap before a
  final policy-valid `ResourceV1` can exist.
- Authenticated policy, resource membership, transition semantics, accounting,
  state, persistence, atomic commit, proof adapters, and production release
  assurance remain unimplemented.

This evidence is scoped to the implemented boundary. It establishes no
unbounded proof, end-to-end funds safety, or production readiness.
