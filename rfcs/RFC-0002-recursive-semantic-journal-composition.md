# RFC-0002: Recursive Semantic Journal Composition

**Status:** Draft
**Author:** Dana Edwards

**Drafting assistance:** GPT-5.6
**Reviewers:** Independent semantic reviewer TBD; recursive-proof reviewer TBD
**Created:** 2026-07-12
**Target version:** ZRM 0.2 draft
**Change class:** E

## Summary

This RFC defines the semantic boundary between ZRM and project-neutral recursive
proof adapters. It makes an accepted ZRM journal the native postcommit semantic
leaf, defines a bounded summary over an ordered contiguous journal segment, and
defines a partial associative composition operation over compatible summaries.

The design separates:

```text
semantic identity:
  what ordered transitions and state/effect chain are represented

proof identity:
  which programs, releases, receipts, and aggregation topology authenticate it
```

For the same ordered accepted journals under the same semantic profile, every
valid recursive tree MUST derive the same semantic segment identity. Different
proof trees MAY derive different proof-tree identities.

This RFC does not define a new canonical byte table or select a production set
accumulator. Those require follow-up Class E profiles and independent vectors.

## Motivation

Recursive proof verification can show that child guests ran and emitted
particular journals. It does not by itself establish that the child results form
one valid semantic history. Composition must additionally establish:

- exact leaf authority (`AcceptedJournal`, not arbitrary bytes);
- machine, domain, application, epoch, policy, crypto, and accumulator scope;
- ordered state-root continuity;
- no omitted, duplicated, substituted, or reordered descendant journal;
- no duplicated transition, nullifier, resource creation, or reward;
- complete accounting and transformation composition;
- explicit rejection of messages and carry state in the first profile;
- required data-availability evidence;
- tree-shape-independent semantic identity;
- proof-profile, program, release, and topology accountability without making
  them the economic identity of the transition history.

Without an explicit semantic composer, a recursive root can be cryptographically
valid while authenticating an invalid combination of individually valid
children.

## Goals

- Make postcommit `AcceptedJournal` the sole native ZRM semantic leaf.
- Keep precommit admission leaves explicitly separate.
- Define a deterministic ordered segment summary.
- Define a partial composition relation with explicit failure reasons.
- Make semantic composition associative over valid ordered segments.
- Make composition noncommutative and reject reordering.
- Bind descendant identity and state/effect coverage completely.
- Support a deliberately simple bounded reference profile before optimized
  accumulators.
- Derive first-profile leaf positions from authenticated state versions rather
  than a caller or host assignment.
- Preserve proof-system neutrality while allowing governed recursive backends
  in adapters.

## Non-goals

- Generating recursive proofs inside ZRM core.
- Hiding transition metadata or providing zero knowledge.
- Solving data availability, consensus, ordering, or finality.
- Permissionless verifier registration.
- An unbounded or production sparse-set accumulator in the first profile.
- Cross-machine atomicity or bridge semantics.
- Message-enabled or carry-enabled recursive composition in the first profile.
- Treating proof-tree shape as semantic identity.
- Retroactively authorizing an already committed transition.

## Terminology

**Admission leaf:** A precommit proof over an exact `JournalDraftHash`. It may
satisfy a policy-required admission slot but does not prove durability.

**Postcommit semantic leaf:** A proof over exact `AcceptedJournal` bytes and
hash, authenticated after durable commit.

**Semantic segment:** A nonempty, ordered, contiguous sequence of accepted
journals under one semantic scope.

**Semantic summary:** A canonical commitment to the segment endpoints, ordered
manifest, descendant identity sets, accounting/effects, fixed empty
message/carry boundaries, and DA coverage.

**Proof node:** A concrete recursive proof object and its proof-tree identity.

**Semantic node:** The tree-shape-independent semantic summary authenticated by
one or more proof nodes.

## Proposed semantics

## 1. Leaf authority

A postcommit recursive adapter accepts only a sealed or independently
authenticated `AcceptedJournal` source. Journal bytes alone are data.

The leaf verifier MUST authenticate:

- exact canonical accepted-journal payload and hash;
- trusted source of the accepted status;
- expected ZRM journal schema;
- machine, domain, application, epoch, and policy scope;
- transition and statement identity;
- pre- and post-machine-state roots and state versions;
- resource, nullifier, claim, accounting, evidence, provenance, DA, and
  semantic-effects commitments required by the active journal version;
- expected ZRM release/profile when policy requires it.

A `JournalDraft`, reject receipt, local replay result, uncommitted journal bytes,
or host Boolean cannot enter the postcommit semantic leaf path.

## 2. Admission remains separate

An admission leaf binds an exact `JournalDraftHash`, validation context,
expected verifier policy/program/release, and reserved cost slot before commit.

An admission leaf:

- may authorize the policy-selected commit attempt;
- does not prove the plan won the commit race;
- does not prove durability;
- cannot be inserted into a postcommit semantic segment.

A postcommit leaf:

- proves or authenticates an accepted journal after durability;
- cannot retroactively satisfy admission;
- cannot change committed state.

The two modes use distinct profile IDs, statement schemas, verified-fact types,
and proof domains.

## 3. Semantic scope

Every leaf and segment binds one exact scope:

```text
SemanticScopeV1 {
  machine_id
  domain_id
  application_id
  epoch
  machine_policy_root
  crypto_suite_id
  accumulator_profile_id
  semantic_profile_id
  message_profile_id
  carry_profile_id
  journal_schema_id
}
```

The first profile requires:

```text
semantic_profile_id = SerializedSemanticCompositionV1
message_profile_id  = NoMessagesV1
carry_profile_id    = NoCarryV1
```

Any other message or carry profile is unsupported by this RFC and rejects.

Cross-scope composition rejects. A future bridge profile must define source and
destination scopes, finality assumptions, replay domains, and message/asset
conservation explicitly. V0.2 does not relabel a child into its parent scope.

## 4. Ordered leaf identity

The first profile derives order from the globally serialized machine-state
version authenticated by each accepted journal:

```text
leaf.position = journal.pre_state_version
journal.post_state_version = journal.pre_state_version + 1
```

The addition is checked. No caller, host, prover, or recursive adapter supplies
the position. A future parallel or sharded profile requires an authenticated
ordering certificate and a different semantic profile ID.

Each segment has a dense position interval:

```text
SegmentRangeV1 {
  start_position: u64
  leaf_count: u32
}

end_position_exclusive = start_position + leaf_count
```

Addition is checked. `leaf_count` is nonzero and bounded. For the serialized
profile:

```text
range.start_position = first_pre_state_version
end_position_exclusive = last_post_state_version
leaf_count = last_post_state_version - first_pre_state_version
```

The subtraction is checked and converted exactly to the bounded `u32`
`leaf_count`; an unrepresentable interval rejects `RangeOverflow`.

A governance update also advances machine state but does not create an ordinary
transition `AcceptedJournal`. It therefore breaks a serialized semantic
segment. A segment cannot cross the resulting version gap or policy-scope
change. Representing governance history inside recursive semantic segments
requires a separately typed governed leaf and a follow-up Class E profile.

The leaf manifest is the ordered sequence:

```text
SemanticLeafEntryV1 {
  position
  accepted_journal_hash
  transition_id
  statement_hash
  pre_machine_state_root
  post_machine_state_root
  pre_state_version
  post_state_version
  semantic_effects_root
}
```

`position` is derived, dense, and canonical. The manifest MUST reject omission,
duplication, substitution, and reordering. Sorting an attacker-provided list is
not sufficient because order is semantic.

The ordered manifest root is distinct from all set roots.

## 5. Segment summary

The logical summary is:

```text
SemanticSegmentSummaryV1 {
  schema_version
  scope: SemanticScopeV1
  range: SegmentRangeV1

  first_pre_machine_state_root
  last_post_machine_state_root
  first_pre_state_version
  last_post_state_version

  ordered_leaf_manifest_root

  transition_id_set_root
  transition_id_count
  nullifier_set_root
  nullifier_count
  created_resource_id_set_root
  created_resource_id_count

  accounting_accumulator_root
  accounting_dimension_count
  semantic_effects_accumulator_root
  semantic_effect_count

  cross_partition_inbox_root
  cross_partition_inbox_count
  cross_partition_outbox_root
  cross_partition_outbox_count

  carry_pre_root
  carry_post_root
  carry_item_count

  da_certificate_set_root
  da_certificate_count

}

SemanticSegmentHash = H_semantic_segment_v1(
  canonical SemanticSegmentSummaryV1 bytes
)
```

This is a logical schema. The first reference profile may use bounded sorted
vectors as witnesses and derive roots. A production accumulator requires a
separate profile and proof format. `SemanticSegmentHash` is derived from the
summary and is not a field in its own preimage.

### 5.1 Ordered versus set commitments

- The leaf manifest is ordered and preserves transition order.
- Transition IDs, nullifiers, created resource IDs, and DA certificates are
  sorted unique sets within the active profile.
- Accounting and semantic effects are sorted unique rows by their typed
  dimensions or effect keys.
- The first profile requires the named empty inbox, outbox, carry-pre, and
  carry-post roots with zero message and carry counts.

A set root alone does not prove uniqueness, disjointness, or union. The verifier
must receive and authenticate a bounded witness or a proof-carrying accumulator
operation establishing those properties.

## 6. Leaf summary derivation

A leaf summary is derived only from one authenticated `AcceptedJournal`:

```text
range.start_position = journal.pre_state_version
range.leaf_count = 1
first_pre_root = journal.pre_machine_state_root
last_post_root = journal.post_machine_state_root
first_pre_version = journal.pre_state_version
last_post_version = journal.post_state_version
require last_post_version = first_pre_version + 1
ordered manifest = singleton journal entry
transition set = singleton transition_id
nullifier set = journal consumed-nullifier set
created set = journal created-resource set
accounting/semantic effects = journal committed rows/effects
messages and carry = named empty roots and zero counts
DA = journal profile commitments
```

No caller-provided summary field is authoritative. Every field is derived or
matched to a verified journal commitment.

## 7. Composition relation

Define a partial function:

```text
compose(left, right, witness) -> Result<parent, CompositionReject>
```

It is defined only when every condition below holds.

### 7.1 Scope equality

```text
left.scope == right.scope
```

Every field matches exactly. No runtime fallback, suite inference, or schema
coercion is permitted.

### 7.2 Dense range continuity

```text
left.start_position + left.leaf_count == right.start_position
left.end_position_exclusive == left.last_post_state_version
right.start_position == right.first_pre_state_version
```

Counts and positions use checked arithmetic. Empty segments are not valid
children in v0.2.

### 7.3 State continuity

```text
left.last_post_machine_state_root == right.first_pre_machine_state_root
left.last_post_state_version == right.first_pre_state_version
```

Every leaf requires `post_state_version = pre_state_version + 1`. Consequently,
dense range continuity and state-version continuity are the same authenticated
ordering fact under the first profile; neither can be independently supplied.

### 7.4 Ordered manifest concatenation

The parent manifest is exact concatenation:

```text
parent.manifest = left.manifest || right.manifest
```

The parent manifest root is recomputed or established by an authenticated
concatenation proof. Commutative set union is forbidden for the ordered
manifest.

### 7.5 Descendant disjointness and union

The following child sets are pairwise disjoint before union:

- transition IDs;
- consumed nullifiers;
- created resource IDs where historical uniqueness is claimed;
- one-shot reward, assignment, task, receipt, or message keys named by the
  active semantic profile;
- DA certificate identities when duplicate certificates are forbidden.

The parent root and count are derived from exact union. A duplicate rejects;
silent deduplication is forbidden.

### 7.6 Accounting composition

Accounting rows are combined by exact typed dimension using checked arithmetic.
Different units or resource kinds are never merged.

The parent accumulator must establish that it represents every child row once
and no extra row. Any cross-segment transformation, mint, burn, reward, slash,
or conversion must already be explicit in accepted child journals or in a
separately authorized segment-level rule named by the semantic profile.

The first profile defines no hidden segment-level value movement.

### 7.7 Complete semantic-effect composition

The semantic-effects accumulator combines every child semantic effect exactly
once. It must preserve effect keys and reject duplicate one-shot keys. Replay
records, accepted-journal storage rows, admission references, and state-head
metadata remain commit metadata under RFC-0001 and are not recursively folded
as economic or state effects.

Recursive aggregation does not create, remove, or reinterpret a child effect.
An aggregate proof is authentication and compression, not an additional ZRM
transition.

### 7.8 Message and carry exclusion

The first profile admits no cross-partition message or carry semantics:

```text
left.cross_partition_inbox_root =
  right.cross_partition_inbox_root =
  parent.cross_partition_inbox_root = EMPTY_CROSS_PARTITION_INBOX_ROOT_V1
left.cross_partition_outbox_root =
  right.cross_partition_outbox_root =
  parent.cross_partition_outbox_root = EMPTY_CROSS_PARTITION_OUTBOX_ROOT_V1
left.cross_partition_inbox_count =
  right.cross_partition_inbox_count =
  parent.cross_partition_inbox_count = 0
left.cross_partition_outbox_count =
  right.cross_partition_outbox_count =
  parent.cross_partition_outbox_count = 0

left.carry_pre_root = left.carry_post_root = EMPTY_CARRY_ROOT_V1
right.carry_pre_root = right.carry_post_root = EMPTY_CARRY_ROOT_V1
parent.carry_pre_root = parent.carry_post_root = EMPTY_CARRY_ROOT_V1
left.carry_item_count = right.carry_item_count = parent.carry_item_count = 0
```

The empty roots are distinct, named, domain-separated commitments frozen with
the future canonical summary schema. A nonempty message field, nonzero message
count, nonempty carry root, or unsupported message/carry profile rejects.

A future message-enabled profile must define exact key/payload/source/
destination/order/replay matching, boundary cancellation, duplicate handling,
and an associative composition law in a separate Class E RFC. A future carry
profile must likewise define its state relation and prove associativity. Neither
inherits authority from this empty profile.

### 7.9 Data availability

Every child DA requirement remains covered. The parent DA certificate set is an
exact authenticated union. Aggregation does not turn a content commitment into
an availability guarantee.

If the active policy requires a DA fact and verification is unavailable,
composition rejects. Runtime downgrade to a weaker DA profile is forbidden.

## 8. Parent derivation

For valid children:

```text
parent.scope = left.scope
parent.start_position = left.start_position
parent.leaf_count = left.leaf_count + right.leaf_count
parent.first_pre_root = left.first_pre_root
parent.last_post_root = right.last_post_root
parent.first_pre_version = left.first_pre_version
parent.last_post_version = right.last_post_version
parent.manifest = concat(left.manifest, right.manifest)
parent descendant sets = exact disjoint unions
parent accounting/semantic effects = exact checked combinations
parent inbox/outbox roots = named empty roots; counts = 0
parent carry roots = named empty carry root; carry item count = 0
parent DA set = exact authenticated union
```

Every field is derived. A parent-supplied summary is accepted only after exact
recomputation or proof verification under the active accumulator profile.

## 9. Semantic identity

The semantic segment hash is derived from the canonical summary fields that
describe the semantic history. It excludes proof-tree topology, receipt bytes,
aggregator image IDs, proving hardware, and proof release metadata.

Conceptually:

```text
SemanticSegmentHash = H_semantic_segment_v1(
  scope,
  range,
  state endpoints and versions,
  ordered_leaf_manifest_root,
  descendant set roots and counts,
  accounting and semantic-effect roots and counts,
  named empty message roots and zero counts,
  named empty carry roots and zero carry count,
  DA certificate root and count
)
```

For the same ordered accepted journals and profile, every valid tree derives the
same semantic segment hash.

## 10. Proof identity

A proof node separately binds:

```text
ProofNodeIdentityV1 {
  semantic_segment_hash
  wrapper_mode
  recursive_program_or_key_digest
  verifier_policy_id
  verifier_release_id
  proof_profile_id
  left_child_proof_identity
  right_child_proof_identity
  proof_tree_position_or_topology_commitment
}
```

Changing a verifier program, release, proof profile, or tree shape changes proof
identity. It does not change semantic identity when the authenticated semantic
summary remains exactly the same.

Consumers may require both identities: semantic identity for state/economic
meaning and proof identity for TCB, release, and audit accountability.

## 11. Algebraic law

Composition is a partial associative operation over valid ordered segments:

```text
compose(compose(a, b), c) == compose(a, compose(b, c))
```

when both sides are defined from the same three ordered leaves and witnesses.
Equality is equality of the complete semantic summary and semantic segment
hash.

Composition is not commutative:

```text
compose(a, b) != compose(b, a)
```

in general, and reversed state/range continuity normally makes the latter
undefined.

Associativity depends on the exact combination laws for every summary field.
Any field without an associative, order-aware, and auditable composition rule
blocks the profile.

## 12. Bounded reference profile

The first reference profile uses deliberately small bounded witnesses:

- binary composition;
- a bounded leaf count per node;
- explicit ordered leaf entries;
- sorted unique vectors for descendant identities;
- sorted accounting and semantic-effect rows;
- checked `u128` intermediate arithmetic;
- fixed named empty message and carry roots;
- no hidden segment-level transformation;
- no arbitrary-depth production claim.

The verifier recomputes all roots from the bounded witness. This is slower than
a proof-carrying set accumulator but easier to audit.

An optimized accumulator profile must define:

- profile ID and canonical proof format;
- membership, disjointness, union, and concatenation relations;
- independent vectors;
- soundness assumptions;
- refinement evidence against the bounded reference profile;
- resource bounds and worst-case verifier costs.

## 13. Composition reject taxonomy

Stable logical reasons include:

```text
ScopeMismatch
RangeOverflow
RangeGapOrOverlap
StateRootMismatch
StateVersionMismatch
ManifestMismatch
DuplicateTransition
DuplicateNullifier
DuplicateCreatedResource
DuplicateProfileKey
AccountingOverflow
AccountingDimensionMismatch
AccountingCoverageMismatch
EffectCoverageMismatch
UnsupportedMessageProfile
UnsupportedCarryProfile
NonEmptyMessageBoundary
NonEmptyCarryBoundary
DataAvailabilityMismatch
UnsupportedAccumulatorProfile
UnsupportedSemanticProfile
ProofBindingMismatch
ResourceLimitExceeded
Internal
```

Deterministic precedence follows the order above after bounded canonical decode.
Parallel checking may not change the public reject result.

## 14. Security analysis

| Disaster state | Primary defense | Required evidence |
| --- | --- | --- |
| Draft treated as committed | distinct admission/postcommit types and profiles | compile-fail/API tests |
| Wrong machine/domain/policy combined | exact scope equality | negative vectors |
| Same journal assigned another position | derive position from authenticated pre-state version | position-substitution mutant |
| Child order changed | dense positions and ordered concatenation root | permutation atlas |
| State history disconnected | exact state-root/version continuity | mutation and formal proof |
| Leaf omitted or duplicated | ordered manifest count/root | missing/duplicate mutants |
| Transition replay hidden by aggregation | disjoint transition set | set-union proof and mutants |
| Nullifier duplicated across children | disjoint nullifier set | bounded atlas and accumulator proof |
| Created identity recreated | historical profile set check | profile-specific evidence |
| Value row omitted or merged across units | exact typed accounting fold | differential accounting model |
| Hidden aggregate effect | aggregate creates no effects; exact child union | effect coverage tests |
| Message or carry smuggled into first profile | exact empty-profile IDs, roots, and counts | nonempty-boundary negatives |
| DA silently downgraded | policy-bound exact DA union | unavailable-verifier negatives |
| Tree shape changes economic identity | separate semantic/proof identities | associativity theorem and vectors |
| Wrong recursive program/release accepted | proof identity and governed registry | release-substitution negatives |

## 15. Bounded state-machine oracles

`zrm_recursive_semantic_composition_v1` models three ordered leaf summaries with:

- bounded state endpoints;
- singleton leaves and checked bounded leaf counts;
- positions derived from pre-state versions;
- consecutive pre/post versions and dense segment ranges;
- bounded effect totals;
- two descendant-membership bits;
- pairwise disjointness;
- left-associated and right-associated folds.

It requires both groupings to produce equal endpoints, ranges, counts, effects,
and member union. Targeted mutants assign a position independently of the
pre-state version and omit the middle leaf count from the right-associated fold;
both must produce invariant counterexamples.

The model does not represent cryptographic roots, arbitrary set sizes, DA, or
proof systems. Messages and carry are represented only by the first profile's
closed empty state. It is a small algebraic design oracle, not the complete
proof.

## 16. Formal obligations

At minimum:

```text
LeafSummaryDeterministic
ComposePreservesScope
ComposePreservesOrderedManifest
ComposeStateContinuous
ComposeDescendantsExactDisjointUnion
ComposeAccountingExact
ComposeEffectsExact
FirstProfileMessagesAreEmpty
FirstProfileCarryIsEmpty
PositionDerivedFromStateVersion
ComposeDaCoverage
ComposeAssociative
ComposeNotCommutativeInGeneral
SemanticHashTreeShapeIndependent
ProofIdentityBindsSemanticIdentityAndRelease
PostcommitCannotAuthorizeAdmission
```

The associativity theorem must quantify over arbitrary valid finite segment
summaries under one fixed semantic profile. Bounded state-machine analysis
supplies only finite examples.

## 17. Typed interfaces

Conceptually:

```rust
pub fn derive_postcommit_leaf(
    journal: &AuthenticatedAcceptedJournal,
    profile: &GovernedSemanticProfile,
) -> Result<SemanticSegmentSummaryV1, LeafReject>;

pub fn compose_segments(
    left: &SemanticSegmentSummaryV1,
    right: &SemanticSegmentSummaryV1,
    witness: &BoundedCompositionWitnessV1,
    profile: &GovernedSemanticProfile,
) -> Result<SemanticSegmentSummaryV1, CompositionReject>;

pub fn authenticate_recursive_node(
    expected: &SemanticSegmentSummaryV1,
    artifact: &BoundedArtifact,
    verifier: &GovernedRecursiveVerifier,
) -> Result<VerifiedPostcommitAggregationFact, VerifyError>;
```

`SemanticSegmentSummaryV1` is validated canonical data. A
`VerifiedPostcommitAggregationFact` is a sealed capability created only after
proof and exact summary verification. Neither can authorize ZRM commit.

## 18. Compatibility and versioning

- Existing ZRM resource bytes are unchanged.
- RFC-0001's future accepted-journal version must expose complete semantic
  effects before RFC-0002 can claim complete semantic composition.
- Admission and postcommit profiles use different schema/profile IDs.
- A change to summary fields, ordering, set semantics, hash domain, or
  accumulator proof format requires a new version/profile.
- Old and new semantic profiles cannot be mixed in one segment.
- A recursive verifier release upgrade changes proof identity and governance,
  even if semantic identity remains unchanged.

## 19. Test and assurance plan

- bounded composition, position-substitution, and omission mutants;
- exact leaf derivation vectors;
- all two-leaf reject cases;
- all three-leaf tree-shape permutations that preserve order;
- explicit reordering negatives;
- missing, duplicate, and substituted leaf manifests;
- state-root and version discontinuity mutants;
- descendant overlap atlases;
- accounting/effect overflow and omission mutants;
- wrong message/carry profile and nonempty-boundary negatives;
- DA unavailable/downgrade negatives;
- recursive guest/host differential tests;
- child-receipt program/release substitution tests;
- Lean associativity and tree-shape-independence proofs;
- Kani bounded merge harnesses;
- fuzzing of canonical composition witnesses;
- independent semantic and recursive-proof review.

## 20. Supply-chain and release impact

State-machine checking remains development-only. ZRM core does not depend on a
model checker, solver, or recursive SDK. Recursive adapters may depend on
governed proof-system libraries under explicit TCB, release, and provenance
policies.

A production profile requires pinned source, toolchains, guest binaries,
program/image IDs, verifier releases, reproducible build evidence, complete
coverage/non-claim documents, and retained child-manifest evidence.

## 21. Claims after implementation

When implemented and independently evidenced, the active bounded profile may
claim:

- exact postcommit ZRM journal leaf authentication;
- ordered state-continuous recursive semantic segments;
- exact bounded descendant, accounting, semantic-effect, and DA composition for
  the named profile;
- enforced empty message and carry boundaries for the first profile;
- tree-shape-independent semantic segment identity;
- separate proof-tree and release identity.

It may not claim:

- consensus, finality, censorship resistance, or data availability beyond the
  named DA profile;
- privacy;
- arbitrary recursion or unbounded set correctness;
- exact-once external delivery;
- correctness of the compiler, OS, hardware, proof system, or cryptographic
  assumptions;
- production readiness outside the complete release profile.

## 22. Open questions

Follow-up work must select:

- exact canonical bytes and domains;
- first bounded list sizes and tree depth;
- the production descendant-set accumulator, if any;
- any future message-enabled or carry-enabled profile and its algebra;
- recursive guest ABI and retained audit manifest;
- parameterized proof strategy and implementation refinement;
- release migration across recursive program/image IDs.

## Decision

To be completed after independent semantic, recursive-proof, accumulator, and
release review.
