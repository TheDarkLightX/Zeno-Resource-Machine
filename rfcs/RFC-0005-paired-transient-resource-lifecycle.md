# RFC-0005: Paired Transient Resource Lifecycle

**Status:** Draft for external review; product direction selected by maintainer
**Author:** TBD

**Drafting assistance:** Codex
**Reviewers:** Independent semantic reviewer TBD; authority-boundary reviewer
TBD; accounting reviewer TBD
**Created:** 2026-07-16
**Target version:** ZRM transition profile V2 draft
**Change class:** E

## Summary

This RFC proposes a versioned ZRM transition profile for a first-class
resource to be created and consumed inside the same atomic transition. The
protocol term is **paired transient resource**.

A paired transient resource:

- occupies one fourth canonical placement, separate from consumed,
  referenced, and persistent-created resources;
- has exactly one `TransientBirth` logic use and one `TransientDeath` logic
  use;
- has exactly one producer transformation occurrence and one consumer
  transformation occurrence;
- is absent from the active-resource set before and after the transition;
- uses the current creation policy and an explicit resource-kind permission;
- contributes its quantity once to each gross accounting side;
- emits one durable nullifier on successful commit; and
- is committed in the transition statement and accepted journal.

The selected state projection is:

```text
A' = (A \ C) union O
N' = N union nullifier(C) union nullifier(Q)
```

where `Q` is the transient resource set. The symbol `Q` avoids collision with
the existing transition symbol `T` and evidence component `E`.

`ResourceWireV1`, `ResourceId`, transparent nullifier derivation,
`MachineStateRootV1`, and `AccountingRowV1` remain unchanged. The changed
placement, logic, transformation, policy, statement, semantic-effect, and
journal meanings use new schemas and domains.

This is an atomic lifecycle and composition feature. It does not provide
privacy. Under the transparent profile, durable nullifiers, roots, counts,
journals, timing, and related metadata may remain linkable.

## Motivation

The current ZRM role law requires consumed, referenced, and created resource
IDs to be pairwise disjoint. That law gives strong canonical structure, but it
cannot express one resource produced by one independently governed action and
consumed by another action inside the same transition.

Current ZRM can already express a direct atomic transition:

```text
consume A -> create C
```

It cannot represent the following as two reusable resource-logic boundaries:

```text
consume A -> create transient B -> consume transient B -> create C
```

Without a transient placement, a designer must choose one of two weaker user
experiences:

1. commit `B` in one transition and consume it in another, exposing the user
   to an intermediate holding and a second confirmation; or
2. fuse both independently governed steps into one application-specific
   predicate, losing the reusable resource boundary between producer and
   consumer.

The feature is valuable for routed settlement, exact transient receipts,
proof-market challenge receipts, and other workflows
where an intermediate object has its own logic but should never become a
spendable user holding.

The timing matters. Placement tags, claim schemas, state-proof slots,
accounting derivation, semantic effects, and journal fields are not frozen for
the complete kernel. Deciding the feature before those interfaces freeze is
materially cheaper and safer than retrofitting it after WP6 or WP7.

## Relationship to ARM ephemerality

This proposal is ARM-informed and deliberately stricter.

The general Anoma Resource Machine resource schema defines `isEphemeral` as a
property that skips existence checking when a resource is consumed. The
shielded RISC Zero profile further states that such a resource may be consumed
without ever being created, while its commitment and nullifier are still added
to global accumulators. See the official [ARM resource
schema](https://specs.anoma.net/v1.0.0/arch/system/state/resource_machine/data_structures/resource/index.html)
and [shielded resource profile](https://specs.anoma.net/v1.0.0/arch/system/state/shielded_resource_machine/resource.html).

RFC-0005 does not import that membership-optional rule. Its first profile
requires a paired birth and death in one transition and never inserts the
resource into ZRM's active-resource set. The name `Transient` keeps that
semantic distinction visible.

An ARM-compatible membership-optional profile, if desired later, requires a
separate RFC, profile identity, state law, proof relation, compatibility plan,
and privacy analysis.

## Goals

- Make a first-class intermediate resource composable inside one atomic
  transition.
- Preserve one canonical placement for every resource ID.
- Preserve the current three-role V1 API and all frozen ResourceWireV1 bytes.
- Bind birth and death as separate exact logic obligations.
- Bind one exact producer and one exact consumer transformation occurrence.
- Prevent reuse of one transient by multiple consumers, cycles, unanchored
  transient components, and historical recreation in the first profile.
- Derive gross accounting without treating cancellation as authority.
- Keep rejection as a complete no-op.
- Make replay, concurrency, crash, journal, recursion, and resource bounds
  explicit before implementation.
- Give adapters a user-visible one-authorization, one-commit, one-journal
  workflow while they orchestrate any required verifier-admission phase.
- Keep privacy and state-growth claims scoped to evidence.

## Non-goals

- ARM-compatible unpaired or membership-optional resource consumption.
- Privacy, shielding, unlinkability, or hiding from a temporary lifecycle.
- A cross-application, cross-domain, or cross-machine transaction.
- A general execution VM, scheduler, or mutable intra-transition store.
- Multiple consumers for one transient identity or cyclic dependency components.
- Cross-transaction transient resources.
- Zero persistent growth; each accepted transient adds a nullifier.
- Zero-quantity marker resources under ResourceWireV1 or policy V1.
- Automatic flash-loan solvency, pricing, fee, or market-fairness semantics.
- Exact-once delivery to external systems.
- Approving RFC-0001, RFC-0002, RFC-0004, or this RFC.
- Freezing V2 bytes before independent encoders, vectors, and review exist.
- Implementing a proof guest, accumulator, persistence adapter, or runtime.

## Terminology

**Persistent consumed set `C`:** Active resources removed by a successful
transition.

**Referenced set `R`:** Active resources read without removal.

**Persistent created set `O`:** New resources inserted into the active set.

**Transient set `Q`:** New resources born and retired in one transition. They
are never members of the active set.

**Placement:** The one canonical list containing a resource ID.

**Use:** A logic or transformation occurrence derived from a placement. One
transient placement derives two uses: birth and death.

**Producer:** The unique transformation claim containing a transient birth as
an output use.

**Consumer:** The unique transformation claim containing the matching
transient death as an input use.

**Persistent boundary input:** A consumed or referenced resource use in a
transient transformation component.

**Persistent boundary output:** A persistent-created resource use in a
transient transformation component.

**Transient dependency graph:** The bounded directed graph from a transient's
producer claim to its consumer claim. It is a validation relation, not an
execution schedule.

## Current behavior

ZRM V1 defines exactly three resource roles:

```text
Consumed   = 0x00
Referenced = 0x01
Created    = 0x02
```

Each resource ID occurs in exactly one list. Consumption and reference require
active membership. Creation requires active and historical nonmembership.
Successful commit removes `C`, inserts `O`, and writes nullifiers for `C`.

The implemented slice constructs the three-way partition and role-bound
intrinsic resources. It does not yet implement the complete state
accumulator, semantic kernel, accepted journal, persistence runtime, or
governed verifier registry. No migration of accepted V1 transient behavior is
therefore required because no such behavior exists.

## Selected semantics

### 1. Four-way placement partition

Introduce a new closed placement type:

```text
ResourcePlacementV2 =
    Consumed   = 0x00
  | Referenced = 0x01
  | Created    = 0x02
  | Transient  = 0x03
```

The sets are pairwise disjoint:

```text
C intersect R = empty
C intersect O = empty
C intersect Q = empty
R intersect O = empty
R intersect Q = empty
O intersect Q = empty
```

Duplicates within any list reject. Lists are sorted by `ResourceId`. Each
placement has its own zero-based `u32` ordinal.

`ResourceRoleV1` remains unchanged and exhaustive. A V2 implementation uses a
new type and cannot reinterpret a V1 enum value or serialized role.

### 2. Five logic uses

Introduce a separate closed use type:

```text
LogicUseV2 =
    Consumed       = 0x00
  | Referenced     = 0x01
  | Created        = 0x02
  | TransientBirth = 0x03
  | TransientDeath = 0x04
```

Ordinary placements derive one matching logic use. Every transient placement
derives exactly two logic uses:

```text
Transient(q, ordinal i)
  -> TransientBirth(q, ordinal i)
  -> TransientDeath(q, ordinal i)
```

The two arrows mean required derivation, not time-ordered execution. Both
claims bind the same `ResourceId`, placement ordinal, resource body,
resource-kind policy, final transition statement hash, validation context,
verifier policy, program or key identity, expected output, and validity
window. Their distinct use tags prevent substitution.

The first profile requires exactly:

```text
logic_claim_count = |C| + |R| + |O| + 2|Q|
```

A batch proof may authenticate several exact claim statements. It cannot
collapse, omit, or weaken either logical obligation.

### 3. Membership, freshness, and epoch

For authenticated pre-state `(A, N)`:

```text
C union R is a subset of dom(A)
(O union Q) intersect dom(A) = empty
```

Require historical freshness:

```text
nullifier(c) not in N for every c in C
nullifier(o) not in N for every o in O
nullifier(q) not in N for every q in Q
```

Consequently:

- `C` and `R` require active-membership evidence;
- `O` and `Q` require active-nonmembership evidence;
- `C`, `O`, and `Q` require nullifier-nonmembership evidence; and
- `Q` never uses an active-membership proof.

Every `q` must have:

```text
created_epoch = TrustedValidationContext.current_epoch
expiry_epoch absent or >= current_epoch
```

It must match the parent machine, domain, and application and satisfy all
ordinary ResourceV1 invariants.

An already-active resource cannot be relabeled transient. A resource whose
nullifier appears in history cannot be recreated as transient.

### 4. Resource-kind policy

Introduce a new closed policy field:

```text
TransientUseV2 =
    Forbidden        = 0x00
  | PairedBirthDeath = 0x01
```

`ResourceKindPolicyV2` adds `transient_use`. There is no default, wildcard,
feature-root inference, or caller-selected override.

A transient must use the current creation policy for its exact resource kind.
An accepted predecessor policy may authorize reading or consuming an existing
persistent resource. It cannot authorize transient birth.

Suspended creation, hard revocation, invalid epoch, disallowed logic, wrong
unit, zero quantity, excess quantity, or `Forbidden` transient use rejects.

### 5. Transformation resource uses

Bare resource-ID roots are insufficient for a V2 transformation because one
transient ID has distinct input and output meanings. Define:

```text
TransformationResourceUseV2 {
  resource_id
  logic_use: LogicUseV2
  resource_ordinal: u32
}
```

Allowed input uses are:

```text
Consumed
Referenced
TransientDeath
```

Allowed output uses are:

```text
Created
TransientBirth
```

`TransformationClaimV2` replaces bare input/output resource-ID roots with
canonical roots over `TransformationResourceUseV2`. Unknown uses, wrong sides,
duplicate uses, wrong IDs, wrong ordinals, or a root not equal to the complete
opened list reject.

For each `q`:

```text
producer(q) = the unique claim containing TransientBirth(q) as output
consumer(q) = the unique claim containing TransientDeath(q) as input
```

The producer and consumer must be different claims. The first profile rejects
missing occurrences, duplicate producers, duplicate consumers for the same
transient identity, and a claim that contains both phases of the same
transient.

Different transient identities may share a producer claim or a consumer claim.
Claim-graph out-degree or in-degree greater than one is therefore allowed and
represents a bounded branch or merge. In this RFC, transient fanout means one
transient identity appearing in more than one consumer input occurrence. It
does not mean one claim producing several distinct linear transients.

### 6. Bounded dependency graph

Derive a directed edge for each transient:

```text
producer(q) -> consumer(q)
```

The resulting claim graph must be acyclic. Every connected component
containing a transient must contain:

- at least one persistent boundary input from `C` or `R`; and
- at least one persistent boundary output from `O`.

This first-profile rule rejects pure transient cycles, unanchored nullifier
spam, and components with no user-visible persistent result. It also keeps the
feature focused on composition between persistent boundaries.

The graph is derived from exact claims and checked with a deterministic
bounded algorithm. It creates no hidden mutable intermediate state and does
not prescribe verifier execution order. Independent proof jobs may still run
in parallel when their inputs permit it.

Future profiles may consider terminal burn, pure authorized mint,
multiple consumers for one transient identity, or cycles only after specifying
their authority, accounting, bounds, graph semantics, and user need.

### 7. Accounting projection

For every exact accounting dimension `d = (ResourceKindId, UnitId)`, derive:

```text
consumed_atoms_d =
    sum(quantity(c) for c in C_d)
  + sum(quantity(q) for q in Q_d)

created_atoms_d =
    sum(quantity(o) for o in O_d)
  + sum(quantity(q) for q in Q_d)
```

Then apply the existing equation:

```text
consumed_atoms_d + authorized_mint_atoms_d
  = created_atoms_d + authorized_burn_atoms_d
```

All sums use checked arithmetic. The semantic kernel derives both transient
contributions from the canonical `Q` list. A proposer-supplied total is not
authority.

The equal transient quantities cancel in net projection. They remain present
in gross accounting. This is compatible with RFC-0004's proposed four-column
aggregate, which deliberately retains equal nonzero consumed and created
totals.

Accounting equality does not establish birth logic, death logic, producer
coverage, consumer coverage, transformation permission, mint authority, burn
authority, policy validity, replay freshness, or state correctness. Every
guard remains independent.

### 8. State update

The transparent first profile derives:

```text
active_deletes     = C
active_inserts     = O
nullifier_inserts  = nullifier(C) union nullifier(Q)
```

After successful atomic commit:

```text
A' = (A \ C) union O
N' = N union nullifier(C) union nullifier(Q)
P' = P
V' = V + 1
```

Therefore:

```text
Q intersect dom(A)  = empty
Q intersect dom(A') = empty
nullifier(Q) is a subset of N'
```

The active-resource accumulator algorithm and `MachineStateRootV1` shape do
not change. The post-state root changes through the existing active and
nullifier constituent roots.

If any validation, verification, finalization, admission, or commit check
fails:

```text
S' = S
```

No transient nullifier, reward, journal, replay row, state version, outbox
record, or external effect may commit on rejection.

### 9. Replay and concurrency

Replay protection has two independent identities, subject to the canonical
identity blocker below:

1. the governed V2 transition identity prevents reapplying the same statement;
2. `nullifier(q)` prevents the same transient `ResourceId` from appearing in a
   different accepted transition.

The final `TransitionIdV2` derivation is not selected by this logical schema.
It must be a domain-separated function of the exact canonical
`TransitionStatementV2` bytes or their exact statement hash, with independent
cross-version vectors. Until that derivation is frozen, this RFC claims
statement-hash domain separation and does not claim final V1/V2 transition-ID
noncollision.

A new resource nonce creates a new resource identity and may be used if every
other rule passes.

The V2 conflict footprint includes:

```text
active membership reads       C union R
active nonmembership reads    O union Q
nullifier nonmembership reads nullifier(C union O union Q)
active deletes                C
active inserts                O
nullifier writes              nullifier(C union Q)
```

Two plans using the same transient ID conflict even though neither inserts it
into the active set. Under the initial global compare-and-swap, at most one can
commit. Any later sharded or rebasing profile must include transient
nullifiers in its serializability proof.

### 10. Transition witness

`TransitionWitnessV2` adds:

```text
transient_resources[]
transient_active_nonmembership_proofs[]
transient_nullifier_nonmembership_proofs[]
```

It also carries the complete opened transformation-use lists needed to
recompute V2 input and output roots and derive the dependency graph.

All counts and byte lengths are bounded before allocation. Resource lists,
state-proof lists, logic claims, transformation claims, artifacts, and sealed
facts must have exact cardinality. Omission, duplication, extra slots,
permutation, or repair-by-sorting of untrusted committed lists rejects.

## Typed interfaces

Conceptually:

```rust
pub enum ResourcePlacementV2 {
    Consumed,
    Referenced,
    Created,
    Transient,
}

pub enum LogicUseV2 {
    Consumed,
    Referenced,
    Created,
    TransientBirth,
    TransientDeath,
}

pub enum TransientUseV2 {
    Forbidden,
    PairedBirthDeath,
}

pub struct CanonicalResourcePartitionV2 {
    // private sorted, duplicate-free, pairwise-disjoint lists
}

pub struct ValidatedTransientGraphV2 {
    // private exact producer/consumer map and validated DAG
}

pub struct TransientSemanticEffectsV2 {
    // private kernel-derived nullifier writes and journal fields
}
```

Validated fields remain private. Wire enums are distinct from validated enums.
No public constructor accepts a Boolean such as `is_transient`, `is_valid`, or
`verified`. No `Deserialize`, `Default`, or unchecked conversion constructs an
authority-bearing partition, graph, fact, plan, or accepted journal.

## Proposed logical schemas

### Transition statement V2

`TransitionStatementV2` preserves V1 fields and adds the transient root and
count in the placement section:

```text
TransitionStatementV2 {
  schema_version
  machine_id
  domain_id
  application_id
  epoch
  validity_start_epoch
  validity_end_epoch

  machine_policy_root
  crypto_suite_id
  accumulator_profile_id
  execution_context_root
  ordering_context_root

  pre_machine_state_root
  claimed_post_machine_state_root

  consumed_resources_root
  referenced_resources_root
  created_resources_root
  transient_resources_root
  logic_claims_root
  transformation_claims_root
  authority_claims_root
  data_availability_claims_root
  accounting_rows_root

  evidence_root
  provenance_root
  data_availability_root
  data_availability_certificate_root

  consumed_count
  referenced_count
  created_count
  transient_count
  logic_claim_count
  transformation_claim_count
  authority_claim_count
  data_availability_claim_count
  accounting_row_count

  transition_nonce
}
```

The exact V2 byte table, field tags, lengths, and rejection precedence remain
an approval blocker. No implementation may hash an ad hoc struct layout from
this logical schema.

### Logic claim V2

```text
LogicClaimV2 {
  schema_version
  machine_id
  domain_id
  application_id
  epoch

  resource_id
  resource_use: LogicUseV2
  resource_ordinal

  resource_logic_id
  logic_profile_id
  resource_kind_policy_id
  verifier_id
  verifier_policy_id
  controller_root
  policy_root

  input_root
  expected_output_root
  validity_start_epoch
  validity_end_epoch
}
```

`LogicStatementV2` binds the final `TransitionStatementV2` hash and exact
`LogicClaimV2` hash. V1 claim or statement facts cannot satisfy V2 slots.

### Transformation claim V2

```text
TransformationClaimV2 {
  schema_version
  machine_id
  domain_id
  application_id
  epoch

  transformation_rule_id
  transformation_profile_id
  transformation_policy_root
  verifier_id
  verifier_policy_id
  authority_root

  input_resource_uses_root
  output_resource_uses_root
  delta_rows_root
  parameter_root
  evidence_root
  validity_start_epoch
  validity_end_epoch
}
```

`TransformationStatementV2` binds the final transition hash and exact claim
hash. The verifier authenticates the claim relation. The kernel separately
recomputes use roots, exact coverage, graph structure, and accounting linkage.
For every claim, the opened uses derive an exact per-claim gross projection:
`Consumed` and `TransientDeath` input uses contribute their resource quantity
and dimension to the consumed side; `Created` and `TransientBirth` output uses
contribute to the created side; `Referenced` contributes no value delta. Every
claimed delta row must equal that canonical use-derived projection plus exact
separately authorized mint or burn rows. No extra or omitted row is permitted.
The checked sum of all per-claim projections, preserving multiplicity, must
equal the kernel's global accounting projection.

### Policy schemas

`ResourceKindPolicyV2` adds `transient_use`. `MachinePolicyV2` adds:

```text
max_transient_resources: u32
max_transformation_input_uses_per_claim: u32
max_transformation_output_uses_per_claim: u32
max_total_transformation_uses: u32
```

It also binds supported V2 resource-placement, logic, transformation,
transition, semantic-effect, and journal schemas through its existing
versioned support roots or their approved successor fields.

The numeric maximum must be positive if any resource kind permits transients,
must not exceed a protocol ceiling selected from evidence, and must satisfy
all relational count and byte constraints.

### Journal schema

The coordinated next journal schema adds:

```text
transient_resources_root
transient_nullifiers_root
transient_count
transient_nullifier_count
```

Persistent `created_resources_root` remains scoped to `O`. The journal also
commits the V2 logic, transformation, accounting, semantic-effect, context,
policy, verifier, pre-state, and post-state roots required by RFC-0001's final
accepted-journal design.

The exact journal version number is coordinated with RFC-0001. This RFC does
not preemptively name an accepted `ResourceTransitionJournalV2` if RFC-0001
selects a different successor schema.

## Canonical encoding and hashing

### Proposed new domains

At minimum, the final V2 domain registry needs distinct domains for:

```text
zrm.resource_kind_policy.v2
zrm.machine_policy.v2
zrm.transient_resources.v2
zrm.transient_nullifiers.v2
zrm.logic_claim.v2
zrm.logic_statement.v2
zrm.logic_claim_list.v2
zrm.transformation_resource_use.v2
zrm.transformation_resource_use_list.v2
zrm.transformation_claim.v2
zrm.transformation_statement.v2
zrm.transformation_claim_list.v2
zrm.transition_statement.v2
zrm.transition_journal.v2
```

The exact journal suffix may change only through the coordinated successor
schema described above. Existing consumed, referenced, and persistent-created
list roots may be embedded unchanged because their list meanings remain
unchanged, but the V2 parent statement and journal domains prevent container
substitution.

Every new object requires:

- a manual field table;
- fixed widths and explicit enum tags;
- exact field order and list framing;
- strict decode and no trailing bytes;
- canonical re-encoding equality;
- independent empty, singleton, and multi-entry vectors;
- all-field and cross-domain mutation vectors; and
- two independent implementation replays before approval.

The V2 canonical packet must also freeze `TransitionIdV2` derivation and prove
by independent vectors that a V1 and V2 statement cannot substitute for or
replay as one another. A distinct statement domain alone is insufficient to
make that final identity claim.

`ResourceWireV1`, `ResourceId`, `zrm.resource.v1`, and
`zrm.nullifier.transparent.v1` do not change.

## Authority and trust boundary

The proposer cannot grant transient authority by:

- setting a flag;
- placing an ID in `Q`;
- supplying two claim descriptors;
- balancing quantities;
- supplying graph edges;
- returning `verified=true`;
- presenting proof bytes;
- obtaining a successful subprocess exit code; or
- providing journal-shaped bytes.

Authority requires all of the following:

1. a governed V2 machine and resource-kind policy;
2. canonical typed resource, placement, claim, and witness construction;
3. authenticated state membership or nonmembership facts;
4. governed verifier dispatch and exact sealed logic and transformation facts;
5. deterministic kernel coverage, graph, accounting, and effect derivation;
6. a private commit plan bound to the authenticated context; and
7. successful atomic commit returning an accepted journal.

Birth and death facts are precommit facts and bind the final transition
statement. They do not bind an accepted journal that does not yet exist.
Postcommit recursive facts cannot retroactively authorize a transition.

## Accounting and RFC-0004 interaction

This RFC reuses `AccountingRowV1`. It does not change column order, widths,
units, authority roots, transformation roots, or the conservation equation.

RFC-0004's proposed recursive carrier retains equal nonzero gross consumed and
created totals. A transient row such as:

```text
consumed=7, created=7, burn=0, mint=0
```

therefore remains visible in its aggregate rather than disappearing as net
zero.

Before either RFC is approved, the RFC-0004 corpus must add:

- an accepted-journal opening containing a transient gross-flow row;
- exact coverage entries for its birth and death transformation provenance;
- a mutant that nets the transient away before leaf projection;
- a mutant that omits one transient accounting side; and
- a recursive omission test showing that zero net is not semantic no-op.

RFC-0004 remains postcommit and grants no transition authority. RFC-0005 does
not make its draft aggregate profile approved or implemented.

## State, concurrency, and atomicity

The pre-journal semantic-effect commitment includes every kernel-derived
transient nullifier write together with active deletes, active inserts, and
the other pre-journal semantic effects defined by RFC-0001. It excludes journal
bytes, replay rows, state-head metadata, admission metadata, and commit-audit
metadata whose identities depend on the finalized journal. After the journal
is finalized, those derived records join the semantic effects in one atomic
commit bundle. This split preserves RFC-0001's acyclic hash dependency.

Crash outcomes must be observationally either:

- confirmed pre-state with none of those effects; or
- confirmed post-state with all of those effects and the accepted journal.

An indeterminate storage outcome remains indeterminate until read-only retry
resolution authenticates the exact replay record and accepted journal. It
cannot be reported as a clean rejection.

The initial global state/version/context compare-and-swap remains the
linearization point. A future sharded profile must prove that transient
nonmembership reads and nullifier writes participate in conflict detection.

## Privacy and disclosure

The first profile is transparent. A transient lifecycle may reduce the time an
intermediate exists as a spendable active resource. It does not establish:

- data privacy;
- function privacy;
- resource-kind hiding;
- amount hiding;
- controller hiding;
- unlinkable nullifiers;
- hidden timing;
- hidden verifier or policy identity; or
- hidden journal structure.

The accepted journal commits transient roots and counts. The transparent
nullifier is derived from public machine, domain, and resource identity and is
linkable by design. Proof generation or a root commitment alone does not add
privacy.

User interfaces and adapter documentation use **temporary** or **transient**
for this feature. They must not use **private**, **shielded**, or **unlinkable**
unless a separate approved privacy profile supplies that evidence.

Pairing ZRM with a shielded ARM or another privacy system remains an adapter
architecture question. This RFC neither replaces nor embeds ARM privacy.

## Data availability and external effects

The transition witness and any proof witness containing transient resource
bodies remain subject to the selected DA policy. A root commits bytes; it does
not prove future retrieval.

Transient logic cannot hide an external side effect. Every effect must be
explicit in the semantic-effect root, commit plan, accepted journal, and
outbox profile. A later consumer failure prevents the entire transition from
committing, including earlier-producer effects.

Exact-once commit does not imply exact-once delivery by an external system.

## Resource and performance bounds

Let:

```text
c = consumed_count
r = referenced_count
o = created_count
q = transient_count
```

Machine policy must enforce with checked arithmetic:

```text
c <= max_consumed_resources
r <= max_referenced_resources
o <= max_created_resources
q <= max_transient_resources

c + r + o + 2q <= max_logic_claims
```

For every transformation claim `j`, before allocating or opening use lists:

```text
input_uses(j)  <= max_transformation_input_uses_per_claim
output_uses(j) <= max_transformation_output_uses_per_claim
sum_j(input_uses(j) + output_uses(j)) <= max_total_transformation_uses
```

Every sum and per-claim comparison uses checked arithmetic.

The base state-proof slot count is:

```text
2c + r + 2o + 2q
```

The nullifier insert count is:

```text
c + q
```

Gross accounting processes:

```text
c + o + 2q
```

resource contributions.

Each transient therefore adds:

- one bounded resource body;
- one active-nonmembership proof;
- one nullifier-nonmembership proof;
- two logic claims and verifier slots;
- two transformation-use occurrences;
- two accounting additions;
- one graph edge;
- one nullifier insertion; and
- no active-resource insertion or deletion.

Placement sorting and intersection should be `O(n log n)` or better after
bounding counts. Exact producer/consumer mapping and graph validation should
be linear in bounded claim and transient occurrences after canonical maps are
constructed. An implementation may use a deliberately smaller ceiling to
justify a simpler bounded reference algorithm, but it must record that choice
and its measured worst case.

The current strict V1 maxima already allow ordinary role maxima to saturate
`max_logic_claims`. A V2 policy cannot simply add a transient maximum without
checking relational coherence. Persistent uses repeated across transformation
claims also consume the aggregate transformation-use budget. Exact protocol
ceilings and the strict default remain approval blockers pending envelope,
state-proof, verifier-cost, graph, memory, journal, and storage benchmarks.

## Reject taxonomy and precedence

The final stable error table must refine this family order:

```text
unsupported V2 schema or profile
  -> bounded input and canonical decode
  -> placement duplicate or collision
  -> active and historical freshness
  -> policy and current-creation permission
  -> logic-use shape and exact fact binding
  -> transformation-use root and exact producer/consumer coverage
  -> graph same-identity multiplicity, anchoring, and cycle checks
  -> accounting and authority coverage
  -> final state and journal derivation
  -> admission and atomic commit
```

The precise code values and within-family precedence require an approved
canonical ABI table and cross-language negative corpus. No implementation may
select error order from hash-map iteration, verifier scheduling, or adapter
failure timing.

## Security analysis

| Disaster state | Required defense | Residual risk |
| --- | --- | --- |
| Active resource relabeled transient | Pairwise placement plus active nonmembership | State-proof system remains in the TCB |
| Historical transient recreated | Nullifier nonmembership and atomic insertion | Nullifier history grows permanently |
| Birth authority stands in for death | Distinct exact logic uses and facts | Verifier/program correctness remains assumed |
| One transient feeds several consumers | Unique consumer occurrence and same-identity multiplicity rejection | Shared consumption needs a new profile |
| Pure transient cycle self-authorizes | Acyclic, boundary-anchored derived graph | Graph schema and implementation need refinement evidence |
| Cancellation grants authority | Independent logic, transformation, and authority coverage | Application logic may still be economically wrong |
| Transient omitted from accounting | Kernel-derived dual gross projection | Checked-arithmetic implementation needs evidence |
| Transient nullifier commits on reject | Private plan and atomic commit | Storage adapter and recovery remain unimplemented |
| V1 proof satisfies V2 use | Distinct schemas, domains, policy selection, and fact types | Registry implementation remains in the TCB |
| Net-zero row treated as no-op | Journal and RFC-0004 gross-flow retention | Recursive profile remains Draft |
| Temporary marketed as private | Explicit nonclaim and UI acceptance test | Metadata may reveal more than expected |
| Excess transient work causes DoS | Independent counts, bytes, cost, graph, and write bounds | Exact deployable limits need benchmarks |

## Alternatives considered

### Candidate ranking

| Rank | Candidate | Feature coverage | Main disposition |
| ---: | --- | --- | --- |
| 1 | Fourth placement plus dual uses | Complete | Selected for RFC review |
| 2 | Resource flag plus consumed/created overlap | Complete | Reject for the first profile |
| 3 | Transition-local virtual receipt fact | Partial | Keep as a future non-value capability |

### Resource flag and role overlap

A favorable form would put one ID in both consumed and created lists and mark
the resource ephemeral. That naturally yields two logic claims.

It also makes flagged-only-consumed, flagged-only-created, unflagged overlap,
flagged reference, and persistent flagged output representable invalid states.
It weakens the simple V1 partition, makes proof-slot shape conditional on body
flags, and requires ResourceWireV2 plus new resource identity vectors. A
derived transient root is still needed for audit.

This RFC keeps lifecycle placement outside immutable ResourceWireV1 bytes.

### One combined transient logic fact

A combined proof could verify both relations, but one combined semantic slot
makes omission and substitution harder to audit and couples independently
governed producer and consumer logic. The first profile preserves two exact
logical obligations. A governed batch verifier may prove both without changing
their typed identities.

### No durable nullifier

If a transient never enters `A` and leaves no history in `N`, two different
transition statements can reuse the same resource ID. Both pass active
nonmembership. This violates global immutable-resource recreation protection.

The transparent first profile therefore writes one durable nullifier. A truly
statement-local receipt with no global identity is a different non-resource
object and cannot carry general resource quantity or ownership.

### Virtual receipt fact

A safe local receipt can bind a producer and consumer to one statement and
carry no quantity, mint, burn, transformation delta, ownership, or reusable
global authority. That object is useful for condition chaining.

Once it carries general resource quantity, resource logic, policy, or
accounting semantics, it needs the guards defined by this RFC. It is no longer
an equivalent simpler feature.

### ARM-compatible unpaired ephemerality

Skipping consumed membership without a paired birth supports a broader design
space. It also changes ZRM's existence law, proof slots, accounting scope,
creation history, and application expectations. The requested UX is a paired
intermediate. The broader profile remains out of scope.

### Two persistent transitions

This needs no new schema, but it leaves a user-visible intermediate, adds one
commit and confirmation, and permits the second leg to fail after the first
commits. It remains appropriate when the intermediate is intentionally
holdable or transferable.

## Compatibility and migration

### ABI disposition

| Object | Disposition |
| --- | --- |
| `ResourceWireV1`, `ResourceId`, flags | unchanged; flags remain zero |
| Transparent nullifier derivation | unchanged |
| `MachineStateRootV1` constituent meaning | unchanged |
| `AccountingRowV1` | unchanged |
| `ResourceRoleV1` and three-list APIs | preserved exactly |
| `ResourcePlacementV2` | new closed enum |
| `LogicUseV2` | new closed enum |
| `LogicClaimV2` and statement | new schema and domains |
| `TransformationClaimV2` and use lists | new schema and domains |
| `ResourceKindPolicyV2` | new explicit transient permission |
| `MachinePolicyV2` | new transient limit and schema support |
| `TransitionStatementV2` and witness | new schema and domains |
| Accepted journal successor | coordinated new schema |
| First recursive transient segment | V2-only; mixed segments reject |

### Activation

1. Keep all V1 decoders, hashes, active resources, journals, and readers
   byte-exact.
2. Add V2 parsing and verification disabled by governed policy.
3. Freeze V2 bytes, domains, vectors, limits, and verifier identities.
4. Complete reference, mutation, fuzz, formal, race, and crash evidence.
5. Activate an approved MachinePolicyV2 through authenticated governance.
6. Advance policy root and state version, intentionally staling old plans and
   facts.
7. Permit V1 or V2 statements only when their exact schemas are selected by
   policy.
8. Allow existing ResourceWireV1 active resources to participate under V2
   placement without rewriting them.

### Historical replay

Historical V1 and V2 journals retain their original meanings. Readers remain
versioned. V1 logic, admission, journal, or recursive artifacts cannot satisfy
V2 slots, and V2 artifacts cannot satisfy V1 slots.

`TransitionStatementV2` has a distinct statement-hash domain. The final
transition-ID noncollision claim remains blocked until `TransitionIdV2`
derivation and cross-version vectors are approved.

### Rollback

Feature rollback is a new governed policy update that forbids every new
transient birth and advances both the policy root and state version. Every
pre-rollback plan and verifier fact becomes stale. The first rollback profile
retains V2 readers, exact policy interpretation, and a Q-empty compatibility
path needed to consume or reference live persistent `ResourceWireV1` outputs
created under V2 policy. New outputs use the governed successor creation
policy.

Full V2 schema deactivation is permitted only after governed evidence shows
that no live persistent resource requires V2-only policy interpretation, or an
approved migration preserves its consumability. Rollback never:

- rewinds state;
- deletes transient nullifiers;
- erases V2 replay records or journals;
- reinterprets V2 bytes as V1;
- reuses a prior state version; or
- reports committed V2 history as though it never occurred; or
- strands an already-live persistent resource.

Historical V2 readers and audit support remain available according to release
and retention policy.

## BDD acceptance stories

```gherkin
Feature: Compose first-class transient resources in one atomic transition
  As a user composing independently governed actions
  I want an intermediate resource to be born and retired in one transition
  So that I receive one atomic result without holding a stranded intermediate

  Rule: A routed action may use a typed intermediate without persisting it

    Scenario: Settle through an independently governed intermediate
      Given the user authorizes resource A for final resource C
      And one action produces transient B required by another action
      When the combined route commits
      Then one accepted journal commits A consumed, C active, and one transient whose root opens to B
      And exact claim openings bind B to one producer and one consumer while B remains absent from both active sets

  Rule: A transient receipt remains a resource-native linear capability

    Scenario: Consume an exact receipt from an independently governed producer
      Given one governed action produces transient receipt R for its exact result
      And another governed action requires that exact R as its input
      When the combined transition commits
      Then the accepted journal binds R to one producer and one consumer
      And R is never presented as holdable, transferable, or reusable

  Rule: Failure of any leg rejects the whole workflow

    Scenario: A later consumer rejects
      Given an earlier producer could create transient B
      And the consumer fails its logic or output constraint
      When the combined transition is evaluated
      Then the original inputs remain active and no final output is created
      And no transient nullifier, journal, reward, or version change commits

  Rule: Both halves require exact authority

    Scenario: Only transient birth is authorized
      Given a valid producer and birth fact for transient B
      And no valid death fact covers B's exact consumer and ordinal
      When the transition is evaluated
      Then it rejects for incomplete transient coverage
      And balanced gross accounting does not authorize the missing death

  Rule: Successful transient use cannot be recreated

    Scenario: Reuse a previously accepted transient resource
      Given an earlier transition committed transient B's nullifier
      When another transition proposes the exact same B
      Then historical freshness rejects without mutation

  Rule: A transient dependency component has persistent boundaries

    Scenario: Submit an all-transient cycle
      Given every proposed resource in one component is transient
      And the component has no persistent input or persistent output
      When the transition is evaluated
      Then it rejects before verifier dispatch

  Rule: Transient work consumes governed budgets

    Scenario: Weighted logic work exceeds policy
      Given ordinary placement counts are individually in range
      And the weighted count c plus r plus o plus two q exceeds policy
      When the request is bounded
      Then it rejects before any verifier is dispatched

  Rule: Temporary lifecycle does not imply privacy

    Scenario: Review a transparent transient route
      Given a route uses a transient resource under the transparent profile
      When the user reviews the route and accepted result
      Then the interface identifies the transparent profile and describes the resource as temporary
      And the accepted result discloses its transient count, root, and durable nullifier effect without a confidentiality claim

  Rule: Feature rollback preserves live persistent outputs and stales old plans

    Scenario: Roll back after V2 created a persistent output
      Given a live persistent ResourceWireV1 output was created under V2 policy
      And governance activates the transient-disabled compatibility policy
      When an authorized transition consumes that output
      Then the output remains consumable under exact predecessor-policy rules
      And every plan or fact from before rollback rejects as stale without mutation
```

## Test and assurance plan

### Structural and codec evidence

- four-placement permutation, duplicate, and collision atlas;
- unknown placement and use tags;
- exact transient ordinal derivation;
- V2 statement, policy, claim, use-list, and journal vectors;
- two independent encoders;
- every-field, list-order, cross-domain, and V1/V2 substitution mutations;
- bounded parser fuzzing with truncation, trailing data, duplicate fields, and
  allocation refusal.

### State and atomicity evidence

- active transient relabeling rejection;
- historical transient recreation rejection;
- successful transient absent from pre- and post-active sets;
- exact nullifier insertion on success;
- no nullifier insertion on rejection;
- same-ID concurrent plans yield at most one success;
- crash at every write boundary yields only authenticated pre or post state;
- idempotent lost-ack replay returns the original accepted journal without
  reapplying effects.

### Logic and transformation evidence

- missing, duplicate, extra, swapped, and wrong-ordinal birth/death claims;
- wrong program, policy, statement, use, and output bindings;
- missing, duplicate, or substituted producer and consumer occurrences;
- same-transient multiple-consumer and same-claim birth/death rejection;
- bounded branch and merge with distinct transient identities;
- per-claim and aggregate transformation-use allocation refusal;
- pure transient component, unanchored component, and directed cycle
  rejection;
- graph result invariant under untrusted list permutations that canonical
  decoding rejects or normalizes only before commitment as specified.

### Accounting evidence

- transient quantity appears exactly once in each gross side;
- omission from either side rejects;
- checked sum overflow rejects;
- transient cancellation cannot mask unauthorized persistent mint or output;
- every per-claim use projection matches its exact delta rows;
- per-claim projections compose exactly to global gross accounting;
- RFC-0004 retains the equal nonzero row and exact coverage occurrence;
- reference, optimized, proof, and recursive projections match the same
  accepted corpus.

### Named mutants

At minimum:

```text
allow_transient_active_membership
omit_transient_active_nonmembership
omit_transient_historical_freshness
omit_transient_birth_fact
omit_transient_death_fact
swap_transient_logic_use
reuse_transient_wrong_ordinal
allow_duplicate_transient_producer
allow_duplicate_transient_consumer
allow_same_transient_multiple_consumers
allow_transient_cycle
allow_unanchored_transient_component
omit_transient_consumed_accounting
omit_transient_created_accounting
net_transient_away_before_row
omit_transient_nullifier_effect
commit_transient_nullifier_on_reject
accept_v1_fact_in_v2_slot
ignore_weighted_logic_count
omit_transient_journal_root
```

Every surviving critical mutant blocks promotion.

## Formal obligations

At minimum:

```text
FourWayPlacementPartitionDisjoint
TransientPlacementDerivesTwoUses
TransientAbsentFromPreActive
TransientAbsentFromPostActive
TransientFreshAtAdmission
TransientNullifierInsertedExactlyOnce
TransientCannotBeRecreated
TransientBirthDeathCoverageExact
TransientProducerConsumerCoverageExact
TransientDependencyGraphAcyclic
TransientComponentBoundaryAnchored
TransientGrossAccountingProjectionExact
TransientClaimAccountingProjectionExact
TransientContributionHasZeroNetDelta
TransientUseBoundsEnforced
DistinctTransientBranchMergePreservesLinearity
TransientCancellationCannotGrantAuthority
TransientPolicyRequiresCurrentCreation
RejectWithTransientIsNoOp
ConcurrentSameTransientHasAtMostOneWinner
DisjointTransitionsWithTransientsCommute
TransientCrashRecoveryIsPreOrPost
RecursiveLeafRetainsTransientGrossFlow
RecursiveCompositionPreservesTransientHistory
V1V2SemanticNonSubstitution
FeatureRollbackPreservesPersistentConsumability
```

Use:

- Kani for checked counts, partitioning, ordinals, graph bounds, arithmetic,
  and update-set construction;
- Lean for set, graph, state, accounting, and replay theorems;
- SMT or TLA+ for replay, concurrency, activation, crash, and recovery models;
- property tests for deterministic bounded spaces;
- mutation tests for every critical guard; and
- fuzzing for V2 parsers, envelopes, lists, and proof slots.

Tool acceptance remains scoped. `UNKNOWN`, timeout, missing tool, placeholder,
or unexecuted plan is a recorded gap.

## Research and candidate evidence

A pinned Research Kernel MCP run
`zrm_paired_transient_resource_v2_20260716` used revision
`d9cdfceaa396dd56acfacbd042b89ce633dbc173`. It recorded 82 events, 29 atoms,
20 edges, 12 evidence records, eight Morph-style reformulation templates, five
locally supported design conclusions, and four refuted shortcuts.

The supported design conclusions match the selected placement, state,
dual-coverage, accounting, and privacy rules in this RFC. Concrete bounded
witnesses refuted an in-place V1 flag, one undifferentiated logic fact, omission
of the durable nullifier, and full equivalence with a proof-only virtual
receipt.

The run is design provenance. Research Kernel `SUPPORTED` means its local gate
passed. It is not an RFC approval, formal proof, independent review, canonical
vector, runtime replay, or production claim. Its Morph output is deterministic
template generation, not execution of the separate Morph discovery runtime.

## Implementation sequence

### Phase 0: semantic approval

1. Review the paired lifecycle, graph, nullifier, and anchoring choices.
2. Commit two named, adapter-owned executable reference fixtures: routed
   settlement and transient receipt. Each fixture must expose independent
   producer and consumer policy boundaries, show why a direct transformation
   and a non-resource virtual receipt are insufficient, and compare observable
   behavior with the safe two-commit baseline.
3. Select exact protocol and strict-default numeric ceilings from benchmarks.
4. Coordinate journal and semantic-effect fields with RFC-0001 and recursive
   leaf semantics with RFC-0002 and RFC-0004.
5. Obtain two independent Class E reviews, including an authority-boundary
   reviewer, and explicit maintainer semantic approval.

### Phase 1: canonical design evidence

1. Freeze every V2 byte table, enum tag, domain, transition-ID derivation, and
   reject precedence.
2. Add independent encoders and complete vectors.
3. Add the pure bounded state, graph, and accounting oracle.
4. Commit minimized counterexamples and mutation map.

### Phase 2: inert structural implementation

1. Implement the four-way placement partition without state or verifier
   authority.
2. Implement weighted policy limits and constructor rejects.
3. Add unit, property, fuzz, and Kani evidence.
4. Keep all V1 APIs and bytes exact.

### Phase 3: typed authority inputs

1. Implement ResourceKindPolicyV2 and MachinePolicyV2 behind governed
   activation.
2. Implement LogicClaimV2 and TransformationClaimV2 canonical construction.
3. Implement sealed V2 fact binding and substitution negatives.

### Phase 4: reference semantics

1. Implement state freshness and private update planning.
2. Implement exact dual logic and producer/consumer coverage.
3. Implement deterministic graph validation.
4. Implement gross accounting derivation.
5. Differential-test against the pure oracle.

### Phase 5: journal and runtime

1. Implement the coordinated accepted-journal successor and semantic effects.
2. Add atomic commit, replay, crash, and idempotent retry evidence.
3. Promote the Phase 0 routed-settlement and transient-receipt fixtures into
   governed adapters after their authority paths satisfy preceding gates.

### Phase 6: formal and recursive promotion

1. Complete Kani, Lean, SMT/TLA+, mutation, fuzz, and refinement obligations.
2. Add RFC-0004 gross-flow and coverage fixtures.
3. Add V2 recursive leaf support after the accepted-journal ABI is stable.
4. Run full release and independent review gates.

No authority-path implementation phase is delegable before its preceding
approval and ABI gates pass.

## Supply-chain and release impact

This design package adds no dependency. A future implementation should prefer
existing bounded collections and deterministic graph algorithms. Any new graph
library, proof SDK, accumulator, serialization crate, or native dependency
requires the complete dependency packet and TCB review.

Release promotion requires:

- approved RFC semantics and exact limits;
- frozen V2 codecs, domains, and independent vectors;
- reviewed V2 policy activation and rollback;
- complete CBC-056 through CBC-062 evidence;
- reference/runtime/proof differential agreement;
- mutation, fuzz, formal, race, crash, and recovery evidence;
- transparent-profile privacy review and honest UI language;
- two independent Class E reviewers;
- clean release provenance and reproducibility evidence; and
- no pending critical obligations for the selected profile.

## Claims after implementation and approval

For the exact approved bounded profile, the project may then claim:

- one first-class transient resource can be born and retired inside one atomic
  ZRM transition;
- bounded branches and merges may use several distinct linear transients;
- the transient is absent from pre- and post-active sets;
- exact birth/death and producer/consumer obligations bind the final
  transition;
- its gross accounting contribution is preserved on both sides;
- its durable nullifier prevents reuse of the same identity; and
- rejection leaves committed state unchanged.

It may not claim:

- privacy, shielding, unlinkability, or ARM privacy equivalence;
- zero persistent state growth;
- support for unpaired ARM ephemerality;
- multiple consumers for one transient, cycles, cross-application, or
  cross-domain transient composition;
- economic fairness, solvency, correct price, or safe flash lending;
- arbitrary or unbounded workloads;
- proof-system, compiler, cryptographic, storage, consensus, or finality
  correctness beyond named evidence; or
- production readiness from this draft or local gates.

## Open questions and approval blockers

The selected semantic baseline is paired, dual-use, globally nullified, linear
per transient identity, branch/merge capable across distinct identities,
acyclic, and boundary-anchored. Approval still requires answers to:

- What exact protocol ceiling and strict default follow from worst-case
  envelope, graph, state-proof, verifier-cost, journal, and storage evidence?
- What exact V2 field tags, byte tables, domains, and reject codes pass two
  independent encoder replays?
- What exact `TransitionIdV2` derivation binds the canonical V2 statement and
  passes cross-version replay vectors?
- Which successor accepted-journal schema is selected after RFC-0001 review?
- How does RFC-0002 identify V2-only semantic segments and preserve transient
  nullifier history?
- Which RFC-0004 opening and coverage fixtures bind transient gross flow?
- Which two real adapters justify the first activation profile?
- Which compatibility policy proves rollback does not strand live persistent
  outputs while every pre-rollback plan and fact becomes stale?
- Which UI fields disclose transient roots, counts, and nullifier effects?
- Which independent reviewers own semantic, authority, accounting, codec,
  graph, privacy, and persistence approval?

Discovery of an existing external dependency on the draft V1 transition,
claim, journal, or recursive meanings stops approval until its migration and
historical replay disposition are explicit.

## Decision

The maintainer selected paired transient resources as an intended V2 product
direction because they can measurably reduce user authorizations, durable
commits, stranded intermediate holdings, and partial-completion risk. The exact
semantics remain Draft pending external review. The proposed first profile is:

- four pairwise-disjoint placements;
- separate transient birth and death logic uses;
- exact unique producer and consumer transformation uses;
- bounded branch and merge across distinct linear transients;
- a bounded acyclic dependency graph;
- persistent input and output anchoring for every transient component;
- current-creation policy and explicit transient permission;
- dual gross accounting projection;
- no active-set insertion or deletion for the transient;
- one durable nullifier on successful commit; and
- no privacy claim.

Implementation beyond isolated, non-authority structural prototypes remains
blocked on exact limits, canonical V2 bytes and vectors, coordinated journal
semantics, reference and formal evidence, independent Class E reviews, and
explicit maintainer approval.
