# RFC-0005 paired transient resource lifecycle design

**Date:** 2026-07-16
**Change class:** E
**Status:** Product direction selected; draft design for external review
**Base:** `fa93db62e2aa30e0c9a43ffe87c2fcd949943a62`, stacked on the RFC-0004 CBC remediation

## Design packet

Goal:
Define the smallest versioned ZRM profile that lets a first-class resource be
created and consumed inside one atomic transition while preserving exact
authority, accounting, replay, state, journal, and claim boundaries.

Affected crates/modules:
The proposed future change affects `zrm-types`, `zrm-codec`, `zrm-policy`,
`zrm-kernel`, `zrm-state`, `zrm-reference`, and `zrm-verifier-api`. This design
change edits only RFC, sequencing, conformance, package metadata, and this work
log. It does not edit Rust, proof code, canonical vectors, or runtime state.

Exact typed statement or API:
RFC-0005 proposes `ResourcePlacementV2` with `Consumed`, `Referenced`,
`Created`, and `Transient`, plus `LogicUseV2` with separate `TransientBirth`
and `TransientDeath` uses. `ResourceWireV1` remains unchanged. New transition,
logic, transformation, policy, and journal schemas carry the changed meaning.

Authority boundary:
Untrusted resource bodies, placement lists, claims, artifacts, proposed graph
edges, and totals grant no authority. A governed V2 policy selects schemas and
limits. Registered verifiers produce sealed facts for exact V2 statements.
The semantic kernel derives placement, dependency, accounting, and effect
coverage. Atomic commit alone constructs an accepted journal.

Attacker-controlled versus governed inputs:
The proposer supplies canonical candidate bytes, state-proof slots, claim
descriptors, proof artifacts, and retained witness data. Governed policy fixes
resource-kind permission, transition and claim schemas, verifier identities,
profile limits, accumulator profile, current epoch, and active policy root.

New states or transitions introduced:
A V2 transition has a fourth pairwise-disjoint resource placement set. Each
transient resource has one birth use and one death use in the same transition,
never enters the active-resource set, and emits one durable nullifier only on
successful atomic commit.

Invariants preserved/added:

- `C`, `R`, `O`, and `Q` are pairwise disjoint, where `Q` is the transient set.
- Every `q` has active and historical nonmembership before validation.
- Every `q` has exactly one birth logic use, one death logic use, one producer
  transformation occurrence, and one consumer transformation occurrence.
- Transient dependency components are bounded, acyclic, and anchored between
  a persistent input and persistent output in the first profile.
- Transient quantity is derived once on each gross accounting side.
- A balanced row does not replace logic, transformation, mint, burn, or other
  authority coverage.
- Rejection is a no-op, including no transient nullifier insertion.
- Successful commit leaves `Q` absent from the active set and adds `nf(Q)` to
  permanent nullifier history.
- V1 and V2 statements, claims, facts, journals, profiles, and domains cannot
  substitute for one another.

Disaster states affected:
Membership bypass; resource recreation; hidden or duplicated value movement;
birth-only or death-only authority; producer or consumer substitution;
multiple consumers for one transient identity; cyclic self-authorization;
all-transient state spam; mixed-schema proof reuse; partial crash writes; and
privacy overclaim.

Canonical bytes or hashes affected:
No current bytes change. A future implementation requires manual V2 byte
tables and new domains for policy, transient roots, logic claims,
transformation-use claims, transition statements, transient nullifier lists,
and journals. Existing `ResourceWireV1`, `ResourceId`, transparent nullifier,
and `AccountingRowV1` identities remain byte-exact.

Replay and cross-domain separation impact:
The V2 statement domain separates statement hashes. Final transition-ID
derivation and cross-version vectors remain ABI blockers. Exact machine,
domain, application, epoch, policy, use tag, resource ID, ordinal, claim hash,
and verifier identity remain bound. A committed transient nullifier prevents
the same resource identity from being used in another transition. Cross-domain
or cross-application transients remain unsupported.

Compatibility/versioning impact:
This is a V2 transition-profile change. V1 decoders and artifacts retain their
meaning. Existing V1 resources may be placed in a governed V2 transition
without rewriting resource bytes. Activation and deactivation occur only by
governed policy updates. Feature rollback advances policy and state identity,
stales old plans and facts, forbids new transient birth, and retains a Q-empty
compatibility path so live persistent V2-policy outputs remain consumable.
Deactivation never deletes nullifiers or historical journals. The first
recursive profile rejects mixed V1/V2 segments.

Tests to add first:
A four-placement duplicate and collision atlas; exact birth/death and
producer/consumer coverage negatives; two-transition replay; same-ID race;
reject-is-no-op and crash cuts; gross accounting projection mutants; V1/V2
substitution; resource-kind permission; transformation graph same-identity
multiplicity, branch/merge, cycle, and anchoring; transition-ID cross-version
separation; per-claim accounting;
aggregate transformation-use bounds; rollback stale-plan and live-output
consumption; and transparent-profile affirmative disclosure.

Independent oracle:
A pure bounded state-machine oracle must derive placement, freshness,
dependency graph, accounting rows, nullifier writes, and post-state. It must
compare every accepted and rejected result with the Rust reference kernel.

Counterexample and mutation strategy:
Named counterexamples remove one state check, one phase fact, one graph
occurrence, one accounting projection, one nullifier write, one atomic write,
or one schema binding at a time. Each guard has a named mutant. The smallest
counterexamples are committed before runtime implementation.

Formal/model obligations:
Lean covers four-way disjointness, exact dual coverage, state projection,
accounting projection, and recreation prevention. Kani covers checked counts,
ordinals, partitioning, graph bounds, and update-set construction. SMT or TLA+
covers two-plan races, replay, crash cuts, and policy activation. Runtime/model
refinement remains a separate obligation.

Dependency impact:
None for this design package. A future implementation must justify any graph,
proof, accumulator, or wide-arithmetic dependency under the repository supply
chain policy.

Performance/resource bounds:
For counts `c`, `r`, `o`, and `q`, the first profile requires checked
`c + r + o + 2q <= max_logic_claims`. Each transient adds one bounded resource
body, two state nonmembership proofs, two logic uses, two gross accounting
contributions, one nullifier write, and no active-set write. Exact numeric
ceilings remain an RFC approval blocker pending envelope, verifier-cost,
accumulator, and graph benchmarks.

Non-claims and known gaps:
This design establishes no runtime implementation, canonical V2 ABI, proof,
privacy, unlinkability, zero state growth, data availability, consensus,
external-effect delivery, release, audit, or production authority. The
transparent profile permanently grows nullifier history by one item per
accepted transient resource.

Design forces:
Preserve one canonical placement per resource ID; support independently
governed producer and consumer logic; prevent accounting cancellation from
acting as authority; preserve exact replay history; keep V1 bytes stable; and
make resource work bounded before verifier dispatch.

Pattern selected, or no additional pattern:
Select a four-way placement partition plus two phase-specific uses. Derive a
bounded transformation dependency DAG from exact role-tagged occurrences. The
graph is a validation object and does not introduce an execution scheduler.

Invalid states prevented:
A resource ID cannot occupy an ordinary and transient placement, a transient
cannot be active, one logic half cannot stand in for both halves, one producer
cannot fan out through one transient ID, a pure transient cycle cannot
self-anchor, and a V1 fact cannot satisfy a V2 use.

Extension point or closed-set reason:
The first profile is closed: exactly four placements and five uses. Batch proofs
may authenticate several exact uses, but cannot collapse the obligations. A
membership-optional ARM-compatible profile, local non-resource receipt, shared
consumption of one transient identity, cycle, cross-application route, or
shielded transient requires another profile and RFC.

Alternatives rejected:
An in-place resource flag changes frozen V1 bytes and duplicates lifecycle
meaning between resource identity and transition placement. Allowing one ID in
both consumed and created sets weakens the existing partition. A proof-only
virtual receipt is useful for non-value conditions but cannot carry general
resource quantity or resource logic without recreating this design. Omitting a
durable nullifier permits cross-transition recreation.

Pattern-specific failure modes:
Dual-use omission, producer or consumer substitution, graph cycles,
same-identity multiple consumption, unanchored components, weighted-count
overflow, incorrect accounting projection, and incomplete atomic effects.

Enforcement and tests:
RFC-0005, CBC-056 through CBC-062, exact future codecs and vectors, reference
model, property and fuzz corpora, Kani, Lean, SMT/TLA+, mutation tests, BDD,
two independent Class E reviewers, and the release conformance gate.

Technical AI-review status:
Three independent read-only reviews covered semantics, UX/BDD, and
versioning/migration. A pinned Research Kernel MCP run supplied five locally
supported design conclusions, four concrete refutations, and an open
implementation-evidence frontier. These results are advisory design evidence.
Independent human semantic and authority-boundary review remain required.
The reviewed draft closes findings for the RFC-0001 hash dependency, exact
per-claim accounting, transformation-use bounds, feature-distinguishing BDD,
transition-ID nonclaim, non-stranding rollback, stale-plan invalidation, CBC
dependencies, and WP9 ownership. The maintainer selected the product direction
and requested additional external review before final semantic approval.

## Research Kernel receipt

The design used Research Kernel MCP revision
`d9cdfceaa396dd56acfacbd042b89ce633dbc173` through its stdio server with
`RK_MODE=safe`.

```text
run_id: zrm_paired_transient_resource_v2_20260716
base_revision: a4d2868d92807947cbad5f0d7fd828b74ae1368c
events: 82
atoms: 29
edges: 20
evidence records: 12
Morph template candidates: 8
locally supported design claims: 5
refuted alternative claims: 4
initial similar/prior-failure retrieval results: 0
```

Locally supported design conclusions:

1. preserve one fourth placement and derive separate birth/death uses;
2. keep the transient absent from both active sets and commit its nullifier;
3. require exact dual logic and producer/consumer coverage;
4. count its quantity once on each gross accounting side without granting
   authority; and
5. make no privacy or unlinkability claim.

Concrete refutations:

1. a nonzero V1 resource flag contradicts the frozen V1 flag rule and changes
   resource identity;
2. one birth fact plus balanced totals leaves the death half unauthorized;
3. omitting the historical nullifier admits the same transient ID in a later
   transition; and
4. a quantity-bearing virtual receipt needs the resource/accounting semantics
   it was proposed to avoid.

The kernel's `SUPPORTED` state means only that its local design gate passed.
The run contains no runtime replay, formal proof, canonical V2 vector,
independent review, or protocol approval. Morph output is template-based
reformulation, not execution of the separate Morph discovery runtime.

## Planned implementation slices

1. Commit routed-settlement and transient-receipt executable need fixtures.
2. Obtain external review, approve or revise semantics, and select exact limits.
3. Freeze V2 byte tables, domains, transition identity, reject precedence, and
   independent vectors.
4. Build the pure bounded oracle and commit the adversarial corpus.
5. Implement the inert four-placement partition and weighted limits.
6. Implement V2 policy and typed logic/transformation claims.
7. Implement reference-state freshness and update planning.
8. Implement dependency-DAG and exact coverage checks.
9. Implement per-claim and global gross accounting plus RFC-0004 fixtures.
10. Implement acyclic journal and semantic-effects binding.
11. Add formal, mutation, fuzz, replay, race, crash, and rollback evidence.
12. Promote the two need fixtures into governed adapters.
13. Add recursive support only after the accepted-journal schema is stable.

No authority-path implementation slice is delegable until the RFC, relevant
ABI freeze items, and reviewer requirements are satisfied.
