# Zeno Resource Machine (ZRM) Specification

**Version:** 0.1.0-draft.2
**Date:** 2026-07-10
**Status:** Pre-alpha normative design specification
**Audience:** protocol designers, implementers, formal-methods engineers, security reviewers, proof-system integrators, and coding agents

> **zkVMs prove that code ran. ZRM defines what the result is allowed to change.**

> **Promotion boundary:** This document specifies a target design. It is not evidence that the design has been implemented, verified, audited, released, or made safe for production use.

---

## 0. Document conventions

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** are normative requirement levels and are to be interpreted as described by BCP 14 (RFC 2119 and RFC 8174) when, and only when, they appear in all capitals.

A requirement is not satisfied by prose, an issue, a test name, an agent assertion, or a generated proof artifact alone. A requirement is satisfied only when the corresponding implementation and required evidence exist and are linked from the conformance matrix.

The terms **authority**, **verified**, **accepted**, **canonical**, **proof-backed**, **private**, **available**, **final**, and **production-ready** are reserved terms. Code, documentation, UI, and release artifacts MUST NOT use them more broadly than the active profile and evidence allow.

---

## 1. Abstract

Zeno Resource Machine is a deterministic, proof-system-neutral semantic kernel for typed resource transitions.

The machine models digital assets, rights, capabilities, evidence, computation, model checkpoints, proof tasks, publication authority, storage commitments, and other replay-sensitive objects as immutable resources. A transition consumes active resources, references active resources, and creates new resources. The transition is valid only when:

1. every consumed and referenced resource exists under the committed pre-state;
2. every consumed resource has a fresh nullifier;
3. every created resource is new;
4. each resource logic has been authenticated under a current verifier policy;
5. controller authority and validity windows are satisfied;
6. quantities and units are conserved or changed only through explicit authorized transformations;
7. all statement, policy, domain, evidence, provenance, and data-availability commitments match;
8. the computed post-state matches the public statement;
9. the state update, replay protection, journal, and rewards are committed atomically.

The ZRM core defines semantic validity. It does not itself provide consensus, recursive proving, privacy, data availability, oracle truth, networking, or finality.

---

## 2. Design lineage and differentiation

Resource machines are established prior art. The Anoma Resource Machine models immutable resources that can be created once and consumed once, active-resource state, nullifiers, balance proofs, compliance proofs, and resource-logic proofs. ZRM adopts the useful semantic pattern of immutable resources plus exact-once consumption, while targeting a distinct engineering objective:

> A proof-system-neutral, high-assurance, recursively composable semantic kernel that can be used by financial protocols, proof markets, verifiable-computation systems, machine-learning workflows, evidence systems, publishing systems, and other applications.

ZRM does **not** claim invention of the resource-machine paradigm and is not affiliated with Anoma.

ZRM differs from a general-purpose VM:

```text
VM or zkVM:
  Did program P execute on input X and produce output Y?

ZRM:
  Did authorized, unspent resources permit this state change; were all
  transformations valid; and may the resulting objects become canonical?
```

ZRM is separate from a recursive proof fabric:

```text
ZRM:
  semantic validity of one or more resource transitions

Recursive proof fabric:
  proof authentication and recursive aggregation of transition journals
```

ZRM is also separate from a ledger or durable runtime:

```text
ZRM:
  pure transition semantics and commit plan

Ledger or durable runtime:
  ordering, durable atomic commit, replication, finality, and history
```

---

## 3. Goals

ZRM MUST provide:

1. a deterministic semantic transition relation;
2. exact-once resource consumption;
3. typed resource kinds, units, quantities, policies, and authorities;
4. explicit conservation and transformation semantics;
5. proof-system-neutral verified-fact interfaces;
6. canonical, bounded, versioned authority objects;
7. stable typed rejection reasons;
8. reject-is-no-op semantics;
9. a canonical transition journal;
10. a reference implementation that can run without a blockchain or proof system;
11. formalizable invariants and executable conformance vectors;
12. clean application and proof-system adapter boundaries;
13. deterministic replay and auditable release evidence;
14. a code structure suitable for independent review and formal verification.

---

## 4. Non-goals and non-claims

ZRM v0.1 does not provide or claim:

- blockchain consensus;
- transaction ordering or censorship resistance;
- recursive proof generation;
- zero-knowledge or witness privacy;
- physical compute, energy, location, or legal-right verification;
- data availability without a separately verified certificate;
- external oracle truth;
- permanent storage;
- token issuance or token value;
- a universal scientific-truth mechanism;
- production-ready finance;
- arbitrary application code execution inside the core;
- unbounded inputs or unbounded recursion;
- compiler, operating-system, hardware, or cryptographic-proof-system correctness.

A ZRM proof profile MAY authenticate a claim about a signed physical-world attestation. It MUST NOT reinterpret authentication of the attestation as proof that the physical-world claim is true.

---

## 5. Architectural principles

### 5.1 Pure core, imperative shell

The semantic kernel MUST be a pure deterministic computation over explicit inputs. It MUST NOT read the clock, environment, filesystem, network, process state, random generator, locale, thread scheduler, or global mutable state.

I/O, proof verification, storage, networking, metrics, and process management MUST live in adapters outside the semantic core.

### 5.2 Make invalid states unrepresentable

Validated protocol types MUST have private fields and validating constructors. Deserialization MUST target wire types, followed by `TryFrom` or an equivalent checked constructor. Security-critical validated types MUST NOT be instantiated through unchecked struct literals outside their defining module.

### 5.3 Authority through capabilities, not booleans

A raw proof, signature, JSON object, metadata map, or field such as `proof_ok: true` carries no authority.

A proof adapter MUST authenticate the artifact and construct a non-serializable, non-forgeable verified-fact capability. Only that capability may satisfy the semantic kernel's proof precondition.

### 5.4 Typed before proved

Every transition family MUST define, in this order:

```text
Typed public statement
  -> deterministic reference semantics
  -> canonical journal
  -> malformed and negative tests
  -> proof adapter or optimized implementation
```

The proof system is not the specification.

### 5.5 Fail closed

Unknown schema versions, unknown critical fields, ambiguous encodings, unsupported profiles, stale policies, missing evidence, unavailable verifier tooling, arithmetic overflow, and resource-bound exhaustion MUST reject.

No production profile may silently downgrade to a weaker verifier, debug mode, local replay, or unverified host result.

### 5.6 One semantic definition

Protocol semantics MUST have one normative source. Equivalent implementations in Rust, Lean, SMT, Python, a zkVM guest, or another language MUST be validated by conformance vectors, refinement proofs, or explicit non-claims.

### 5.7 Proof-tree shape is not economic identity

Recursive proof topology MUST be separated from canonical semantic identity. Different valid aggregation trees over the same ordered transition set SHOULD produce the same `semantic_epoch_root`, while their `proof_tree_root` MAY differ.

---

## 6. Layering and dependency direction

The intended dependency graph is:

```text
zrm-types / zrm-codec
          |
          v
      zrm-kernel <----- application policies and logic ports
          |
          v
      zrm-journal
          |
   +------+------+-------------------+
   |             |                   |
   v             v                   v
proof adapters  storage adapters   application adapters
   |             |                   |
   +-------------+-------------------+
                 v
       recursive proof fabric
                 v
       ledger / runtime / anchors
```

Forbidden dependencies:

```text
zrm-core -> any application-specific crate
zrm-core -> any product runtime
zrm-core -> recursive proof implementation
zrm-core -> concrete zkVM SDK
zrm-core -> ledger or runtime implementation
zrm-core -> network clients
zrm-core -> database clients
zrm-core -> system clock or RNG
```

The core defines ports. Adapters implement them. This is the Dependency Inversion Principle applied to the protocol boundary.

---

## 7. Threat model

### 7.1 Adversarial actors

The design assumes that any of the following may be malicious or faulty:

- transition proposer;
- solver or scheduler;
- proof producer;
- proof-market participant;
- application adapter;
- untrusted byte stream;
- metadata producer;
- storage provider;
- data-availability provider;
- network peer;
- stale or misconfigured verifier process;
- compromised build environment;
- coding agent;
- dependency or build script.

### 7.2 Trusted or assumed components

Trust MUST be explicit and profile-bound. Potential assumptions include:

- collision resistance and preimage resistance of the selected hash suite;
- signature or proof-system soundness;
- correctness of a pinned verifier binary;
- correctness of the Rust compiler and target toolchain;
- correctness of a governed policy root;
- atomicity guarantees of the storage adapter;
- truthfulness of external attestations where policy explicitly trusts them.

Every production profile MUST publish its trusted computing base and assumptions.

### 7.3 Disaster states

At minimum, the implementation and CBC matrix MUST address:

| Disaster state | Required primary defense |
| --- | --- |
| nonexistent resource consumed | authenticated membership check |
| resource consumed twice | deterministic nullifier plus atomic uniqueness |
| previously consumed resource recreated | output nonmembership against active and nullifier domains |
| wrong resource logic accepted | logic program/profile/policy binding |
| logic proof replayed onto another transition | statement hash, role, ordinal, resource, domain binding |
| wrong controller authorized | controller root and logic statement binding |
| stale policy accepted | ledger-owned expected policy root |
| cross-domain replay | machine, domain, epoch, and policy in statement hash |
| unauthorized mint/burn | accounting mode and authority fact |
| unlike units added | `UnitId` equality and typed rows |
| nonconserved transition accepted | complete accounting and transformation coverage |
| transformation proof covers wrong resources | exact input/output set binding |
| duplicate output commitment | output uniqueness check |
| canonical bytes interpreted differently | manual normative encoding and exact decode |
| unknown critical field ignored | strict versioned wire schema |
| integer overflow | checked arithmetic and protocol bounds |
| attacker exhausts memory | byte/count bounds before allocation |
| rejection mutates state | prepare/commit typestate split |
| concurrent double spend | pre-root compare-and-swap and atomic commit |
| journal detached from transition | statement and journal hash binding |
| proof artifact trusted as a boolean | sealed verified-fact capability |
| unavailable data treated as available | DA certificate policy or explicit non-claim |
| debug proof admitted | production verifier profile and release gate |
| path-dependent build promoted | reproducible build and provenance gate |
| agent weakens tests to pass | mutation gate, review, and claims matrix |

---

## 8. Terminology

**Resource object:** the canonical typed data describing a resource.

**Resource commitment / Resource ID:** the domain-separated hash of the canonical resource object under the selected cryptographic profile.

**Active resource:** a resource commitment present in the active-resource accumulator and not consumed.

**Nullifier:** a deterministic or privacy-preserving identifier marking a resource as consumed.

**Referenced resource:** an active resource read by a transition but not consumed.

**Resource logic:** a versioned predicate authorizing consumption, reference, or creation of a resource.

**Resource-kind policy:** policy that defines unit, accounting mode, allowed logics, quantity bounds, and transformation authority for a resource kind.

**Transformation:** an explicitly authorized mapping between resource vectors or lifecycle states.

**Verified fact:** a non-forgeable in-process capability produced by an authenticated verifier adapter.

**Transition statement:** the canonical public claim that the kernel or proof system evaluates.

**Transition witness:** full resource bodies, membership proofs, proof artifacts, signatures, and other private or non-authoritative data used to establish the statement.

**Commit plan:** a non-serializable validated state delta that is safe to commit only if both the pre-state and trusted validation context still match.

**Journal:** canonical public output describing an accepted transition.

**Reject receipt:** non-authoritative diagnostic output describing why an uncommitted transition failed.

**Construction Boundary Conformance (CBC):** ZRM's machine-readable obligation family. Each `ZRM-CBC-*` record binds a disaster state to a construction rule, required evidence, current status, and explicit non-claim. `specified` means the obligation exists in the design; it does not mean the obligation is implemented or verified. This project-local acronym is distinct from the general **correct by construction (CbC)** engineering approach. A CBC identifier names an assurance obligation; it does not itself claim CbC correctness.

---

## 9. Formal state model

Let machine state at logical version `t` be:

\[
S_t = (A_t, N_t, P_t, V_t)
\]

where:

- \(A_t\) is the finite map of active resource commitments to resource records or availability references;
- \(N_t\) is the set of consumed-resource nullifiers;
- \(P_t\) is the active machine policy;
- \(V_t\) is a monotonically increasing logical state version.

The independently authenticated `TrustedValidationContext` supplies the logical `current_epoch` used to evaluate this state. The proposer cannot select that authority input.

A transition proposes:

\[
T = (C, R, O, L, X, E)
\]

where:

- \(C\) is the consumed resource set;
- \(R\) is the referenced resource set;
- \(O\) is the created resource set;
- \(L\) is the set of verified resource-logic facts;
- \(X\) is the set of verified transformation/authority facts;
- \(E\) is evidence and provenance committed by roots.

An accepted transition MUST satisfy:

### 9.1 Existence

\[
C \cup R \subseteq \operatorname{dom}(A_t)
\]

Every member of \(C \cup R\) MUST also be live at `current_epoch` under its accepted resource-kind policy.

### 9.2 Role disjointness

\[
C \cap R = C \cap O = R \cap O = \varnothing
\]

and no duplicate commitment may appear within or across role lists.

### 9.3 Fresh consumption

For every \(c \in C\):

\[
\operatorname{nullifier}(c) \notin N_t
\]

### 9.4 Fresh creation

For every \(o \in O\):

\[
o \notin \operatorname{dom}(A_t)
\]

and:

\[
\operatorname{nullifier}(o) \notin N_t
\]

The second condition prevents recreation of a previously consumed resource commitment in the v0.1 transparent profile. This global-history claim does not extend to a future shielded profile unless that profile specifies and commits an equivalent historical nonmembership mechanism.

### 9.5 Logic coverage

Every consumed, referenced, and created resource MUST have exactly one required logic fact for its role unless its resource-kind policy explicitly defines a different bounded cardinality.

### 9.6 Accounting and transformation

For each accounting dimension \(d = (resource\_kind\_id, unit\_id)\), ordinary conserved quantities satisfy:

\[
consumed_d + authorizedMint_d = created_d + authorizedBurn_d
\]

Any unmatched delta MUST be covered exactly once by a verified transformation fact allowed by the resource-kind and machine policies.

### 9.7 State update

If all checks pass:

\[
A_{t+1} = (A_t \setminus C) \cup O
\]

\[
N_{t+1} = N_t \cup \{nullifier(c) \mid c \in C\}
\]

\[
P_{t+1} = P_t
\]

\[
V_{t+1} = V_t + 1
\]

If any check fails:

\[
S_{t+1} = S_t
\]

`TransitionStatementV1` cannot change machine policy in v0.1. Policy governance is a separate runtime operation outside this transition schema. Any deployment policy activation MUST authenticate governance authority, atomically change the policy root and state version, preserve every still-live predecessor resource policy needed for consumption or reference, and invalidate stale plans through the same root/version check. ZRM v0.1 makes no complete policy-migration or rollback claim.

### 9.8 Disjoint commutativity

For accepted transitions \(T_1\) and \(T_2\) with disjoint write footprints and no read/write conflicts:

\[
apply(apply(S,T_1),T_2) = apply(apply(S,T_2),T_1)
\]

This theorem is a target for formal proof and supports parallel validation, deterministic revalidation, and future sharded execution. It does not override the v0.1 global compare-and-swap rule.

---

## 10. Cryptographic and commitment profiles

### 10.1 Cryptographic agility

Every authority object MUST bind a `CryptoSuiteId`, either as an explicit canonical field or through a versioned schema that fixes exactly one suite. The initial transparent reference profile uses SHA-256 for interoperability and auditability. A future proof-optimized profile MAY use a different hash only under a distinct suite ID and versioned compatibility rules.

No implementation may infer a suite from digest length or runtime configuration.

`ResourceWireV1` fixes the SHA-256 reference suite through its schema rather than adding a suite field to each resource. The suite ID is:

```text
SHA256_REFERENCE_V1_ID = SHA256(
  u16_be(26) || ASCII "zrm.crypto_suite.sha256.v1" || u32_be(0)
)

= 0x99f6dd0823f85ca70ed6d91bd00f50dc63fdb5dec3d9fc7212b9eff27e3b1391
```

This is the domain framing in section 10.2 with an empty payload and is unconditionally SHA-256. A machine policy admitting `ResourceWireV1` MUST set `crypto_suite_id = SHA256_REFERENCE_V1_ID`. A different resource hash suite requires a new resource schema version and distinct compatibility rules; it cannot reinterpret v1 bytes.

### 10.2 Domain-separated hash function

For the SHA-256 reference suite, define:

```text
H_D(fields...) = SHA256(
  u16_be(len(D)) || D ||
  u32_be(len(payload)) || payload
)

payload = canonical_tuple(fields...)
```

The canonical tuple is the ordered concatenation required by the object's schema. Variable-length fields inside a tuple MUST be framed as:

```text
u32_be(byte_length) || bytes
```

Lists MUST be framed as:

```text
u32_be(element_count) || canonical_element_1 || ... || canonical_element_n
```

Fixed-width integers use unsigned big-endian encoding. Negative protocol quantities are forbidden; signed deltas are represented using separate nonnegative fields.

### 10.3 Required domain strings

The initial specification reserves:

```text
zrm.resource.v1
zrm.crypto_suite.sha256.v1
zrm.consumed_resources.v1
zrm.referenced_resources.v1
zrm.created_resources.v1
zrm.nullifier.transparent.v1
zrm.active_resource_set.v1
zrm.nullifier_set.v1
zrm.machine_policy.v1
zrm.resource_kind_policy.v1
zrm.validation_context.v1
zrm.ordering_context.v1
zrm.logic_claim.v1
zrm.logic_statement.v1
zrm.logic_claim_list.v1
zrm.transformation_claim.v1
zrm.transformation_statement.v1
zrm.transformation_claim_list.v1
zrm.authority_claim.v1
zrm.authority_statement.v1
zrm.authority_claim_list.v1
zrm.data_availability_claim.v1
zrm.data_availability_statement.v1
zrm.data_availability_claim_list.v1
zrm.transition_statement.v1
zrm.transition_journal.v1
zrm.reject_receipt.v1
zrm.untrusted_request.v1
zrm.accounting_row.v1
zrm.accounting_rows.v1
zrm.machine_state.v1
zrm.verifier_policy.v1
zrm.verifier_cost_model.v1
zrm.verifier_cost_row.v1
zrm.verifier_cost_rows.v1
zrm.verifier_set.v1
zrm.semantic_epoch.v1
zrm.proof_tree.v1
zrm.evidence.v1
zrm.provenance.v1
zrm.data_availability.v1
zrm.data_availability_certificate.v1
```

A domain string MUST NOT be reused for a different encoding or semantic object.

### 10.4 Canonical list roots and empty commitments

For a list of fixed-width 32-byte identifiers or hashes, define:

```text
ListRoot_D(items) = H_D(
  u32_be(item_count) ||
  item_0 || ... || item_n
)
```

Items MUST already be in the schema's canonical order. Duplicate items reject before hashing. Each semantic list uses its own domain string. A consumed-resource list root therefore cannot be substituted for a created-resource list root even when the byte elements happen to match.

The canonical empty value for any such list is:

```text
EmptyListRoot_D = H_D(u32_be(0))
```

Optional commitment fields in v0.1 are represented by their named, domain-separated empty root. They MUST NOT use all-zero bytes. The initial empty values are:

```text
EMPTY_CONSUMED_RESOURCES_ROOT       = EmptyListRoot_"zrm.consumed_resources.v1"
EMPTY_REFERENCED_RESOURCES_ROOT     = EmptyListRoot_"zrm.referenced_resources.v1"
EMPTY_CREATED_RESOURCES_ROOT        = EmptyListRoot_"zrm.created_resources.v1"
EMPTY_LOGIC_CLAIMS_ROOT             = EmptyListRoot_"zrm.logic_claim_list.v1"
EMPTY_TRANSFORMATION_CLAIMS_ROOT    = EmptyListRoot_"zrm.transformation_claim_list.v1"
EMPTY_AUTHORITY_CLAIMS_ROOT         = EmptyListRoot_"zrm.authority_claim_list.v1"
EMPTY_DA_CLAIMS_ROOT                = EmptyListRoot_"zrm.data_availability_claim_list.v1"
EMPTY_ACCOUNTING_ROWS_ROOT          = EmptyListRoot_"zrm.accounting_rows.v1"
EMPTY_EVIDENCE_ROOT                 = EmptyListRoot_"zrm.evidence.v1"
EMPTY_PROVENANCE_ROOT               = EmptyListRoot_"zrm.provenance.v1"
EMPTY_DATA_AVAILABILITY_ROOT        = EmptyListRoot_"zrm.data_availability.v1"
EMPTY_DA_CERTIFICATE_ROOT           = EmptyListRoot_"zrm.data_availability_certificate.v1"
EMPTY_ORDERING_CONTEXT_ROOT         = EmptyListRoot_"zrm.ordering_context.v1"
```

If policy requires evidence, provenance, data availability, or a DA certificate, the corresponding field MUST differ from its canonical empty root and MUST authenticate the required object. If policy does not require it, a nonempty root remains a committed claim and MUST still be validated or rejected as an unchecked witness field.

---

## 11. Canonical encoding rules

Canonical bytes are protocol authority.

### 11.1 General rules

- Critical hashes MUST use a manual normative encoder independent of Serde.
- Transport codecs MAY use Postcard or another bounded codec, but hash identity MUST NOT depend on library-specific re-encoding.
- Authority-path JSON is forbidden in v0.1.
- Diagnostic JSON MUST reject duplicate keys and unknown critical fields and MUST never be hashed after lossy parsing.
- Every object header carries an explicit schema version before semantic fields; a fixed magic and object-type discriminator MAY precede it when the schema defines them.
- Every list has an explicit count and profile-specific maximum.
- Optional values use an explicit one-byte tag (`0` absent, `1` present) followed by the value when present.
- Maps are represented as sorted unique rows, never implementation-defined map iteration.
- Free-form strings are forbidden in authority objects. Human names and descriptions live outside authority and reference fixed IDs.
- All zero values for IDs and commitments reject unless the field specification names a domain-separated canonical empty value.
- Trailing bytes reject.
- Noncanonical encodings reject even if a decoder could interpret them.

### 11.2 Schema evolution

- Reordering a normative field is breaking.
- Changing a field's meaning is breaking.
- Changing a hash domain is breaking.
- Adding a critical field requires a new schema version.
- Append-only transport compatibility MAY be supported only when old and new authority hashes remain explicit and unambiguous.
- Unknown critical fields reject.
- Version downgrade and cross-version replay reject.

---

## 12. Primitive newtypes

The reference Rust implementation MUST use opaque newtypes for at least:

```text
MachineId
DomainId
ApplicationId
ResourceId
ResourceKindId
ResourceLogicId
LogicProfileId
TransformationRuleId
TransformationProfileId
AuthorityKindId
DataAvailabilityProfileId
PolicyId
VerifierId
VerifierPolicyId
VerifierCostModelId
VerifierCostRowHash
BackendFamilyId
ArtifactCodecId
CryptoSuiteId
AccumulatorProfileId
UnitId
ControllerRoot
Commitment
Nullifier
TransitionId
StatementHash
LogicClaimHash
LogicStatementHash
TransformationClaimHash
TransformationStatementHash
AuthorityClaimHash
AuthorityStatementHash
DataAvailabilityClaimHash
DataAvailabilityStatementHash
ValidationContextHash
RequestDigest
RejectReceiptHash
JournalDraftHash
JournalHash
EvidenceRoot
ProvenanceRoot
DataAvailabilityRoot
```

Each 32-byte ID or commitment constructor MUST reject all-zero bytes unless the type explicitly permits a canonical empty value.

Types with different semantics MUST NOT be aliases for the same raw type at public boundaries.

Security capabilities such as `TrustedValidationContext`, `PrevalidatedTransition`, `AuthenticatedFacts`, `VerifiedLogicFact`, `VerifiedTransformationFact`, `ValidatedTransition`, and `CommitPlan` MUST NOT implement `Deserialize`. They SHOULD NOT implement `Clone`. They MUST have private fields and sealed construction paths.

---

## 13. Resource object

### 13.1 Normative logical schema

```text
ResourceV1 {
  schema_version: u16
  machine_id: MachineId
  domain_id: DomainId
  application_id: ApplicationId

  resource_kind_id: ResourceKindId
  resource_logic_id: ResourceLogicId
  logic_profile_id: LogicProfileId
  resource_kind_policy_id: PolicyId

  unit_id: UnitId
  quantity_atoms: u128

  label_root: Commitment
  value_root: Commitment
  controller_root: ControllerRoot
  policy_root: Commitment
  provenance_root: ProvenanceRoot

  nonce: [u8; 32]
  created_epoch: u64
  expiry_epoch: Option<u64>
  flags: ResourceFlagsV1
}
```

### 13.2 Resource invariants

A valid resource MUST satisfy:

- schema version is supported;
- machine, domain, application, kind, logic, profile, policy, unit, controller, and roots are nonzero;
- nonce is nonzero;
- quantity is nonzero unless a versioned resource-kind policy explicitly permits zero-quantity marker resources; the v1 policy schema has no such permission, so every v1 policy-bound resource has positive quantity;
- expiry, when present, is not less than creation epoch;
- flags contain no unknown bits;
- quantity does not exceed the resource-kind policy maximum;
- unit matches resource-kind policy;
- logic and logic profile are authorized by resource-kind policy;
- resource policy ID/root is a member of the active machine policy's accepted resource-kind policy set;
- a created resource uses the currently designated creation policy for its resource kind.

### 13.3 Resource commitment

```text
wire = canonical ResourceWireV1 bytes
payload = u32_be(byte_length(wire)) || wire

ResourceId = SHA256(
  u16_be(15) || ASCII "zrm.resource.v1" ||
  u32_be(byte_length(payload)) || payload
)
```

The inner length prefix is required because `wire` is one variable-length field in the canonical tuple. For the two valid v1 forms, `(byte_length(wire), byte_length(payload))` is `(595, 599)` or `(603, 607)`. This exact preimage uses the schema-fixed `SHA256_REFERENCE_V1_ID`; an implementation MUST NOT hash raw `wire` without the inner length.

The caller MUST NOT supply an authoritative `ResourceId`. It is derived.

### 13.4 Transparent nullifier profile

The v0.1 transparent profile defines:

```text
Nullifier = H_"zrm.nullifier.transparent.v1"(
  machine_id,
  domain_id,
  resource_id
)
```

This profile provides exact-once semantics and no privacy. Shielded nullifiers require a separate profile and specification.

### 13.5 Resource flags

`ResourceFlagsV1` is encoded as a `u32`. Version 1 defines no flag bits:

```text
RESOURCE_FLAGS_V1_KNOWN_MASK = 0x00000000
```

The field MUST therefore be zero in v1. Transferability, fungibility, revocation, and evidence semantics belong to resource-kind policy and logic. A future flag requires a new resource schema version with an explicit invariant and compatibility rule. Any nonzero v1 bit rejects as `zrm.resource.unknown_flag`.

### 13.6 ResourceWireV1 canonical bytes

`ResourceWireV1` is the first frozen-draft authority codec. It is a strict tagged field sequence. Its decoded values are still untrusted until `ResourceV1::try_from` validates the semantic invariants.

Header:

```text
offset  width  value
0       4      ASCII "ZRM1"
4       2      schema_version = u16_be(1)
6       2      object_tag = u16_be(1)       // ResourceWire
8       2      field_count = u16_be(18)
```

Each field is encoded as:

```text
u16_be(field_tag) || u32_be(value_length) || value_bytes
```

The 18 fields MUST occur exactly once in strictly increasing tag order:

| Tag | Field | Value encoding | Length |
| ---: | --- | --- | ---: |
| `0x0001` | `machine_id` | raw 32-byte ID candidate | 32 |
| `0x0002` | `domain_id` | raw 32-byte ID candidate | 32 |
| `0x0003` | `application_id` | raw 32-byte ID candidate | 32 |
| `0x0004` | `resource_kind_id` | raw 32-byte ID candidate | 32 |
| `0x0005` | `resource_logic_id` | raw 32-byte ID candidate | 32 |
| `0x0006` | `logic_profile_id` | raw 32-byte ID candidate | 32 |
| `0x0007` | `resource_kind_policy_id` | raw 32-byte ID candidate | 32 |
| `0x0008` | `unit_id` | raw 32-byte ID candidate | 32 |
| `0x0009` | `quantity_atoms` | `u128_be` | 16 |
| `0x000a` | `label_root` | raw 32-byte commitment candidate | 32 |
| `0x000b` | `value_root` | raw 32-byte commitment candidate | 32 |
| `0x000c` | `controller_root` | raw 32-byte commitment candidate | 32 |
| `0x000d` | `policy_root` | raw 32-byte commitment candidate | 32 |
| `0x000e` | `provenance_root` | raw 32-byte commitment candidate | 32 |
| `0x000f` | `nonce` | raw bytes | 32 |
| `0x0010` | `created_epoch` | `u64_be` | 8 |
| `0x0011` | `expiry_epoch` | absent: `0x00`; present: `0x01 || u64_be(epoch)` | 1 or 9 |
| `0x0012` | `flags` | `u32_be`, required zero in v1 | 4 |

The only valid total encoded lengths are 595 bytes with absent expiry and 603 bytes with present expiry. A decoder MUST reject before constructing `ResourceWireV1` on:

- wrong magic, schema version, object tag, or field count;
- missing, repeated, out-of-order, or unknown field tag;
- a length that differs from the table;
- an optional tag other than `0x00` or `0x01`;
- truncation or trailing bytes.

Before reading the header, ingress MUST reject an input whose byte length exceeds the effective resource-byte limit. That limit is the lesser of `MAX_RESOURCE_BYTES` and the active policy's `max_resource_bytes` when an active policy exists. The isolated WP1 decoder uses `MAX_RESOURCE_BYTES`. A resource-byte limit MUST be at least 603 bytes for a policy to admit `ResourceWireV1`.

When multiple defects are observable, the decoder reports the first applicable v1 code in this precedence order:

| Order | Reject code | Condition |
| ---: | --- | --- |
| 1 | `zrm.bounds.resource_wire_bytes` | input exceeds the effective resource-byte limit |
| 2 | `zrm.malformed.resource_wire_header` | fewer than 10 header bytes are available |
| 3 | `zrm.malformed.resource_wire_magic` | magic differs from `ZRM1` |
| 4 | `zrm.malformed.resource_wire_version` | schema version is unsupported |
| 5 | `zrm.malformed.resource_wire_object` | object tag is not `1` |
| 6 | `zrm.malformed.resource_wire_field_count` | field count is not `18` |
| 7 | `zrm.malformed.resource_wire_field_header` | a tag/length header is truncated |
| 8 | `zrm.canonical.resource_wire_field_tag` | next tag is missing, repeated, out of order, or unknown |
| 9 | `zrm.canonical.resource_wire_field_length` | declared field length differs from the table |
| 10 | `zrm.malformed.resource_wire_field_value` | declared value bytes are truncated |
| 11 | `zrm.canonical.resource_wire_option_tag` | expiry option tag/length is invalid |
| 12 | `zrm.canonical.resource_wire_trailing` | bytes remain after field `0x0012` |

Semantic constructor rejects have their own precedence after successful wire decoding and MUST NOT be reported as codec acceptance.

The semantic constructor then rejects prohibited zero IDs/roots/nonces, invalid quantities or epochs, nonzero flags, and policy mismatches. Canonical encoding emits exactly this form, so every accepted byte string satisfies:

```text
encode(decode(bytes)) = bytes
```

`ResourceId` hashes the complete canonical `ResourceWireV1` bytes using the exact length-framed SHA-256 preimage in section 13.3. No transport codec, struct layout, Serde representation, host endianness, or runtime suite selection participates in this identity.

This draft freezes only the `ResourceWireV1` byte layout for WP1 implementation. Other schemas in this document are normative logical schemas; their authority-byte tables, enum tags, and independent vectors MUST be added by an approved specification change before their codecs or hashes are implemented. This preserves the package-wide non-claim of a stable ABI.

---

## 14. Resource-kind policy

```text
ResourceKindPolicyV1 {
  schema_version
  policy_id
  machine_id
  domain_id
  application_id
  resource_kind_id
  unit_id
  accounting_mode
  quantity_max
  allowed_logic_set_root
  allowed_logic_profile_set_root
  allowed_transformation_set_root
  controller_policy_root
  mint_authority_root
  burn_authority_root
  require_data_availability
  validity_start_epoch
  validity_end_epoch
}
```

`accounting_mode` is one of:

```text
ConservedFungible
AuthorityMintableFungible
LifecycleNonFungible
Transformable
EvidenceOnly
```

Rules:

- The v1 policy schema has no zero-quantity marker rule; every policy-bound v1
  resource MUST have quantity greater than zero. `EvidenceOnly` does not imply
  marker permission.
- `LifecycleNonFungible` resources MUST have quantity `1`.
- A v1 `LifecycleNonFungible` policy MUST declare `quantity_max = 1`; zero is
  unsatisfiable and larger maxima are noncanonical for a fixed-quantity mode.
- `EvidenceOnly` resources MUST NOT carry monetary or fungible quantity semantics.
- `ConservedFungible` resources MUST have zero authorized mint and burn.
- `AuthorityMintableFungible` mint/burn MUST bind an authorized fact.
- `Transformable` unmatched deltas MUST bind an allowed transformation rule.
- `accounting_mode` is policy, not a caller-selected transition label.

For a typed `ResourceKindPolicyV1` candidate, constructor rejection precedence
MUST be:

```text
unsupported schema
  -> invalid validity window
  -> LifecycleNonFungible quantity_max is not 1
  -> construct
```

For dimensions checked against a constructed policy, rejection precedence MUST
be:

```text
unit mismatch
  -> LifecycleNonFungible quantity is not 1
  -> zero quantity
  -> quantity exceeds quantity_max
  -> accept
```

Consequently, lifecycle quantity zero reports the lifecycle exact-one failure,
while non-lifecycle quantity zero reports the general zero failure. A
non-lifecycle policy with `quantity_max = 0` remains a constructible empty
candidate. This fixed-mode lifecycle rule is an in-place pre-alpha v1 semantic
amendment: no canonical resource-kind-policy bytes, persisted policy identity,
or governed activation path exists to migrate. RFC-0002 approval remains
required before this candidate rule can be promoted or used by an
authority-bearing path.

---

## 15. Machine policy

```text
MachinePolicyV1 {
  schema_version
  policy_id
  machine_id
  domain_id
  crypto_suite_id
  accumulator_profile_id
  verifier_cost_model_id
  supported_resource_schema_root
  supported_transition_schema_root
  resource_kind_policy_set_root
  creation_resource_kind_policy_map_root
  accepted_predecessor_resource_policy_set_root
  logic_verifier_policy_root
  transformation_verifier_policy_root
  authority_verifier_policy_root
  data_availability_policy_root
  admission_mode
  admission_verifier_policy_id: Option<VerifierPolicyId>
  governance_authority_root
  feature_suite_root

  max_envelope_bytes
  max_resource_bytes
  max_consumed_resources
  max_referenced_resources
  max_created_resources
  max_logic_claims
  max_transformation_claims
  max_authority_claims
  max_data_availability_claims
  max_accounting_rows
  max_evidence_references
  max_proof_artifact_bytes
  max_total_proof_bytes
  max_total_verifier_cost_units
  max_nesting_depth
  max_storage_write_bytes

  validity_start_epoch
  validity_end_epoch
}
```

The expected machine policy MUST come from independently trusted machine state or governed configuration. The proposer may echo the policy root but may not select it.

`resource_kind_policy_set_root` commits every policy version accepted for reading or consumption. `creation_resource_kind_policy_map_root` selects exactly one current creation policy per resource kind. `accepted_predecessor_resource_policy_set_root` identifies older policies that may be consumed or referenced during a governed compatibility window. A new resource MUST use the selected creation policy; accepting a predecessor MUST NOT authorize creation under it.

`admission_mode` is exactly one of:

```text
LocalKernel
RequiredVerifier
```

`LocalKernel` requires an absent admission verifier policy ID. `RequiredVerifier` requires one nonzero, currently authorized `VerifierPolicyId`. Because the complete machine policy is bound by `machine_policy_root`, the transition and trusted validation context commit the admission choice before evaluation. Runtime fallback from `RequiredVerifier` to `LocalKernel` is forbidden.

Critical limits MUST be bounded above by compile-time protocol ceilings. A policy may tighten but not exceed protocol ceilings.

Every verifier policy admitted by one `MachinePolicyV1` MUST use that machine policy's exact `verifier_cost_model_id`. Only costs under that one governed model may be summed against `max_total_verifier_cost_units`. Supporting heterogeneous cost units requires a new machine-policy schema with per-model budgets; implicit conversion is forbidden.

The v0.1 protocol ceilings are:

```text
MAX_ENVELOPE_BYTES          = 4 MiB
MAX_RESOURCE_BYTES          = 16 KiB
MAX_CONSUMED_RESOURCES      = 256
MAX_REFERENCED_RESOURCES    = 256
MAX_CREATED_RESOURCES       = 256
MAX_LOGIC_CLAIMS            = 768
MAX_TRANSFORMATION_CLAIMS   = 256
MAX_AUTHORITY_CLAIMS        = 768
MAX_DATA_AVAILABILITY_CLAIMS = 256
MAX_ACCOUNTING_ROWS         = 512
MAX_EVIDENCE_REFERENCES     = 512
MAX_PROOF_ARTIFACT_BYTES    = 1 MiB
MAX_TOTAL_PROOF_BYTES       = 3 MiB
MAX_TOTAL_VERIFIER_COST_UNITS = 2^48 - 1 profile-defined cost units
MAX_NESTING_DEPTH           = 16
MAX_STORAGE_WRITE_BYTES     = 8 MiB
```

The reference strict default profile is:

```text
max_envelope_bytes          = 1 MiB
max_resource_bytes          = 4 KiB
max_consumed_resources      = 64
max_referenced_resources    = 64
max_created_resources       = 64
max_logic_claims            = 192
max_transformation_claims   = 64
max_authority_claims        = 192
max_data_availability_claims = 64
max_accounting_rows         = 128
max_evidence_references     = 128
max_proof_artifact_bytes    = 256 KiB
max_total_proof_bytes       = 768 KiB
max_total_verifier_cost_units = 2^32 - 1 profile-defined cost units
max_nesting_depth           = 8
max_storage_write_bytes     = 2 MiB
```

These are DoS and auditability limits, not throughput claims.

### 15.1 Trusted validation context

Validity is evaluated against an independently authenticated logical epoch and pre-state, never against time values selected by the proposer.

```text
ValidationContextV1 {
  schema_version
  machine_id
  domain_id
  current_epoch
  expected_machine_state_root
  expected_state_version
  expected_policy_root
  expected_crypto_suite_id
  expected_accumulator_profile_id
  ordering_context_root
}
```

```text
ValidationContextHash = H_"zrm.validation_context.v1"(
  canonical ValidationContextV1 bytes
)
```

The runtime or ledger adapter authenticates these fields from committed state and ordering policy, then constructs a sealed `TrustedValidationContext`. Untrusted wire bytes MUST NOT directly deserialize into that capability. The semantic kernel receives the capability as an explicit input and requires the transition's machine, domain, epoch, pre-state root, policy root, crypto suite, accumulator profile, and ordering-context root to equal the corresponding context fields. It also requires:

```text
statement.execution_context_root = ValidationContextHash
```

At `current_epoch`, validation MUST require:

- machine policy and every selected resource-kind policy are within their validity windows;
- transition validity contains `current_epoch`, and `statement.epoch == current_epoch`;
- every consumed or referenced resource has `created_epoch <= current_epoch` and is not expired;
- every created resource has `created_epoch == current_epoch` and, when present, `expiry_epoch >= current_epoch`;
- every logic, transformation, authority, and DA fact is within its policy-bound validity window.

Wall-clock time has no semantic authority. A deployment that maps timestamps, block heights, or epochs into `current_epoch` MUST specify and authenticate that mapping in its ordering/runtime profile.

---

## 16. Transition statement

### 16.1 Public statement

```text
TransitionStatementV1 {
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
  logic_claim_count
  transformation_claim_count
  authority_claim_count
  data_availability_claim_count
  accounting_row_count

  transition_nonce
}
```

### 16.2 Statement hash

```text
StatementHash = H_"zrm.transition_statement.v1"(
  canonical TransitionStatementV1 bytes
)
```

The construction is acyclic:

```text
resources and policy
  -> LogicClaimV1[] / TransformationClaimV1[]
     / AuthorityClaimV1[] / DataAvailabilityClaimV1[] / AccountingRowV1[]
  -> canonical claim and accounting roots
  -> TransitionStatementV1
  -> StatementHash
  -> proof-bound LogicStatementV1 / TransformationStatementV1
```

The transition commits to proof-independent claim descriptors. The verifier statements created afterward bind the final `StatementHash` to one exact claim hash. A child proof statement is never included in the root from which its parent transition hash is computed.

### 16.3 Transition ID

```text
TransitionId = StatementHash
```

A later profile MAY distinguish the two, but v0.1 uses one identity to avoid redundant caller-controlled identifiers.

### 16.4 Statement requirements

The constructor MUST reject:

- invalid time range;
- epoch outside validity range or unequal to `TrustedValidationContext.current_epoch`;
- stale or mismatched machine policy;
- mismatch with the trusted pre-state, state version, policy, execution context, or ordering context;
- zero roots or IDs;
- an all-zero transition nonce;
- counts above policy or protocol ceilings;
- count/list mismatch;
- duplicate role entries;
- unsorted list roots where the profile requires sorting;
- pre-state profile mismatch;
- claimed post-state root omitted or ambiguous;
- the canonical empty DA certificate root when policy requires a certificate;
- a nonempty optional root that is not validated under policy;
- any caller-provided derived value that does not match recomputation.

---

## 17. Transition witness and envelope

The public statement does not carry full resource bodies or proof artifacts. The untrusted envelope supplies:

```text
TransitionWitnessV1 {
  consumed_resources[]
  consumed_membership_proofs[]

  referenced_resources[]
  referenced_membership_proofs[]

  created_resources[]
  created_nonmembership_proofs[]

  logic_claims[]
  logic_proof_artifacts[]
  transformation_claims[]
  transformation_proof_artifacts[]
  authority_claims[]
  authority_artifacts[]
  data_availability_claims[]
  data_availability_artifacts[]
  evidence_references[]
}
```

The witness MUST be bounded before allocation. Every array length MUST equal the corresponding public count or explicitly defined proof count. Logic, transformation, authority, and data-availability artifact arrays are index-paired with their respective claim arrays after the section 18 canonical ordering; permutation, omission, duplication, or an extra slot rejects.

An admission artifact is intentionally absent from `TransitionWitnessV1`. It authenticates the `JournalDraft`, which does not exist until transition facts have been authenticated and finalization has completed. Under `RequiredVerifier`, the caller receives the exact draft, obtains the admission artifact, submits it through the separate bounded admission-verification API, and then supplies the resulting `VerifiedAdmissionFact` to commit. This is a two-phase protocol. `LocalKernel` forbids an admission artifact.

A witness field is admissible only if one of these holds:

1. the kernel checks it directly;
2. a verifier adapter authenticates it and creates a sealed verified fact;
3. the kernel recomputes a commitment from it and matches the public statement;
4. a documented proof obligation establishes that it cannot affect the accepted public result.

All other witness fields are unconstrained and MUST be removed.

---

## 18. Resource roles and canonical order

### 18.1 Cross-object identity equality

In v0.1, every consumed, referenced, and created `ResourceV1`; every selected `ResourceKindPolicyV1`; every `LogicClaimV1`; every `TransformationClaimV1`; every `AuthorityClaimV1`; and every `DataAvailabilityClaimV1` MUST have `machine_id`, `domain_id`, and `application_id` exactly equal to its parent `TransitionStatementV1`. Zero, wildcard, inherited, or omitted identity values are forbidden. The machine and domain must also equal `TrustedValidationContext`. Proof-bound statements inherit these identities through their exact committed claim hash and parent `StatementHash`.

Cross-application or cross-domain movement requires a future bridge profile with separate source and destination statements, explicit transformation authority, replay domains, and atomicity/finality assumptions. v0.1 MUST reject it rather than relabel child objects under the parent identity.

### 18.2 Roles and ordering

Resources are assigned one role:

```text
Consumed   = role_tag 0x00
Referenced = role_tag 0x01
Created    = role_tag 0x02
```

Unknown role tags reject. Canonical lists are sorted by `ResourceId` ascending. Duplicate IDs reject. A resource ID may occur in exactly one role. `resource_ordinal` is the zero-based `u32` position within the canonical list for that role; the same resource under another role or ordinal is a different claim and MUST reject on substitution.

Logic claims are sorted by:

```text
(role_tag, resource_id, resource_logic_id, logic_profile_id, logic_claim_hash)
```

Transformation claims are sorted by:

```text
(transformation_rule_id, transformation_claim_hash)
```

Authority claims are sorted by:

```text
(authority_kind_id, subject_root, authority_claim_hash)
```

Data-availability claims are sorted by:

```text
(data_availability_profile_id, data_availability_root,
 data_availability_claim_hash)
```

Accounting rows are sorted by:

```text
(resource_kind_id, unit_id)
```

No canonicalization function may silently deduplicate. Duplicate detection precedes or accompanies sorting and rejects.

### 18.3 Authority and data-availability claim descriptors

Authority and DA artifacts have proof-independent committed descriptors, just like logic and transformation artifacts:

```text
AuthorityClaimV1 {
  schema_version
  machine_id
  domain_id
  application_id
  epoch

  authority_kind_id
  subject_root
  authority_policy_root
  signer_registry_root
  authority_nonce
  verifier_id
  verifier_policy_id
  input_root
  expected_output_root
  validity_start_epoch
  validity_end_epoch
}

AuthorityClaimHash = H_"zrm.authority_claim.v1"(
  canonical AuthorityClaimV1 bytes
)

AuthorityStatementV1 {
  schema_version
  transition_statement_hash
  authority_claim_hash
}

AuthorityStatementHash = H_"zrm.authority_statement.v1"(
  canonical AuthorityStatementV1 bytes
)

DataAvailabilityClaimV1 {
  schema_version
  machine_id
  domain_id
  application_id
  epoch

  data_availability_profile_id
  verifier_id
  verifier_policy_id
  data_availability_root
  expected_certificate_root
  parameter_root
  validity_start_epoch
  validity_end_epoch
}

DataAvailabilityClaimHash = H_"zrm.data_availability_claim.v1"(
  canonical DataAvailabilityClaimV1 bytes
)

DataAvailabilityStatementV1 {
  schema_version
  transition_statement_hash
  data_availability_claim_hash
}

DataAvailabilityStatementHash = H_"zrm.data_availability_statement.v1"(
  canonical DataAvailabilityStatementV1 bytes
)
```

The transition roots are:

```text
AuthorityClaimsRoot = ListRoot_"zrm.authority_claim_list.v1"(
  AuthorityClaimHash values ordered by
  (authority_kind_id, subject_root, authority_claim_hash)
)

DataAvailabilityClaimsRoot = ListRoot_"zrm.data_availability_claim_list.v1"(
  DataAvailabilityClaimHash values ordered by
  (data_availability_profile_id, data_availability_root,
   data_availability_claim_hash)
)

TransitionStatementV1.data_availability_root =
  ListRoot_"zrm.data_availability.v1"(
    data_availability_root values in DataAvailabilityClaimV1 order
  )

TransitionStatementV1.data_availability_certificate_root =
  ListRoot_"zrm.data_availability_certificate.v1"(
    expected_certificate_root values in DataAvailabilityClaimV1 order
  )
```

`subject_root` commits the exact resource roles, accounting effects, or other actions that the authority may authorize. Its profile MUST define a canonical, domain-separated derivation. `signer_registry_root` selects the governed signer or authority registry, and `authority_nonce` is a nonzero replay-domain value. `expected_certificate_root` is the exact DA certificate commitment expected from the verifier. V0.1 permits at most one DA claim for a given `data_availability_root`; duplicate content roots or duplicate certificate roots reject. A profile that cannot define these values canonically is not admissible.

The claim roots and counts are committed before `StatementHash` is derived. Proof-bound authority and DA statements are formed only afterward, avoiding parent/child hash cycles. Each committed claim requires exactly one artifact slot and exactly one matching sealed fact; missing, duplicate, or extra claims, artifacts, or facts reject. A verified fact binds the final `StatementHash`, its exact claim hash and statement hash, verifier policy, expected output, and validity window.

---

## 19. Resource logic contract

### 19.1 Logic claim and proof-bound statement

```text
LogicClaimV1 {
  schema_version
  machine_id
  domain_id
  application_id
  epoch

  resource_id
  resource_role
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

LogicClaimHash = H_"zrm.logic_claim.v1"(
  canonical LogicClaimV1 bytes
)

LogicStatementV1 {
  schema_version
  transition_statement_hash
  logic_claim_hash
}

LogicStatementHash = H_"zrm.logic_statement.v1"(
  canonical LogicStatementV1 bytes
)
```

`TransitionStatementV1.logic_claims_root` is:

```text
LogicClaimsRoot = ListRoot_"zrm.logic_claim_list.v1"(
  LogicClaimHash values ordered by
  (role_tag, resource_id, resource_logic_id, logic_profile_id, logic_claim_hash)
)
```

It does not contain `LogicStatementV1`, so computing the parent transition hash is not circular. After the parent hash is known, the verifier authenticates the bound `LogicStatementV1`.

### 19.2 Binding requirements

A verified logic fact MUST bind the exact transition statement hash, claim hash, verifier, program/key identity selected by the verifier policy, and authenticated output. It MUST NOT be reusable for:

- another transition;
- another resource;
- another role;
- another ordinal;
- another machine/domain/application;
- another epoch or policy;
- another program or verifier profile.

### 19.3 Verifier result capability

The core-facing value is conceptually:

```rust
pub struct VerifiedLogicFact {
    transition_statement_hash: StatementHash,
    logic_claim_hash: LogicClaimHash,
    logic_statement_hash: LogicStatementHash,
    verifier_id: VerifierId,
    verifier_policy_id: VerifierPolicyId,
    output_root: Commitment,
    // private unforgeable seal
}
```

Requirements:

- private fields;
- no public unchecked constructor;
- no `Deserialize`;
- no `Default`;
- no conversion from `bool`;
- constructed only by a registered verifier adapter after exact verification;
- includes verifier identity and verifier policy ID;
- expires or becomes invalid when policy requires freshness.

### 19.4 Resource logic output

Resource logic MUST NOT create hidden value movement. The logic output may authorize or reject the explicit transition and may commit disclosures, but every created, consumed, minted, burned, rewarded, or transformed resource remains explicit in the transition and accounting rows.

---

## 20. Transformation contract

### 20.1 Transformation claim and proof-bound statement

```text
TransformationClaimV1 {
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

  input_resource_ids_root
  output_resource_ids_root
  delta_rows_root
  parameter_root
  evidence_root
  validity_start_epoch
  validity_end_epoch
}

TransformationClaimHash = H_"zrm.transformation_claim.v1"(
  canonical TransformationClaimV1 bytes
)

TransformationStatementV1 {
  schema_version
  transition_statement_hash
  transformation_claim_hash
}

TransformationStatementHash = H_"zrm.transformation_statement.v1"(
  canonical TransformationStatementV1 bytes
)
```

`TransitionStatementV1.transformation_claims_root` is:

```text
TransformationClaimsRoot = ListRoot_"zrm.transformation_claim_list.v1"(
  TransformationClaimHash values ordered by
  (transformation_rule_id, transformation_claim_hash)
)
```

It commits the proof-independent claim descriptors in the section 18 order. The proof-bound statement is formed only after the final transition statement hash exists. A verified transformation fact MUST bind both hashes, the selected verifier policy, and its authenticated output.

### 20.2 Transformation coverage

A transformation fact MUST name the exact resource inputs and outputs it authorizes. Two transformation facts MUST NOT claim the same non-shareable resource role unless the rule profile explicitly permits composition and defines deterministic ordering.

Every unmatched accounting delta MUST be covered exactly once. Every transformation-authorized delta MUST appear in accounting. Extra authorization is not harmless and MUST reject.

### 20.3 Transformation examples

```text
ProofTask + Capacity + Bond
  -> ProofAssignment
```

```text
ProofAssignmentResource + VerifiedProofReceiptResource + RewardEscrowResource
  -> RewardClaim + ResidualEscrow + ReleasedCapacity
```

```text
ModelCheckpoint(v) + DatasetCapability + ComputeCredit
  -> ModelCheckpoint(v+1) + EvaluationReceipt + ResidualCredit
```

```text
Balance(A) + SwapIntent + PoolState
  -> Balance(A') + Balance(B') + PoolState' + Fee + SwapReceipt
```

The examples are not core semantics. Application adapters define and prove the corresponding transformation rules.

---

## 21. Accounting model

### 21.1 Accounting row

```text
AccountingRowV1 {
  resource_kind_id
  unit_id
  consumed_atoms: u128
  created_atoms: u128
  authorized_mint_atoms: u128
  authorized_burn_atoms: u128
  authority_root
  transformation_set_root
}
```

All fields are nonnegative. Summation uses checked arithmetic. Overflow rejects.

### 21.2 Conservation equation

For each row:

```text
consumed_atoms + authorized_mint_atoms
  == created_atoms + authorized_burn_atoms
```

Ordinary transfers have zero mint and burn. Mint, burn, reward, slash, issuance, destruction, or conversion effects require an allowed authority or transformation fact.

### 21.3 Row derivation

The kernel derives accounting rows from canonical resource lists and verified facts. The proposer MUST NOT supply authoritative totals.

If a witness includes proposed rows for efficiency, the kernel MUST recompute and require exact equality.

```text
AccountingRowHash = H_"zrm.accounting_row.v1"(
  canonical AccountingRowV1 bytes
)

AccountingRowsRoot = ListRoot_"zrm.accounting_rows.v1"(
  AccountingRowHash values sorted by (resource_kind_id, unit_id)
)
```

Duplicate accounting dimensions reject rather than merge implicitly.

### 21.4 Units

Values with different `UnitId` values MUST NOT be added or compared as fungible quantities. Conversions require a transformation rule.

Names at language boundaries MUST include units where practical, such as:

```text
amount_atoms
fee_bps
epoch_height
expiry_epoch
resource_count
```

Floating-point arithmetic is forbidden in consensus, proof, accounting, and canonical-hash paths.

---

## 22. Verified authority facts

Authority facts include signatures, threshold approvals, governance permissions, mint/burn rights, revocation rights, and other capabilities.

They follow the same sealed-capability rule as logic facts. A serialized signature is not an authority capability until verified against the exact statement and current authority policy.

Authority statements MUST bind:

- machine/domain/application;
- transition statement hash;
- authority action;
- affected resource kinds and resource IDs;
- epoch and expiry;
- policy root;
- signer/registry root;
- nonce or anti-replay domain.

`AuthorityClaimV1` carries these proof-independent bindings directly or through its profile-defined `subject_root`; `AuthorityStatementV1` then binds the exact claim hash to the final transition statement hash. Every authority artifact and sealed authority fact must match that pair.

---

## 23. State accumulator abstraction

### 23.1 Profiles

The state commitment scheme is selected by `AccumulatorProfileId` and bound by machine policy and transition statement.

The core requires operations conceptually equivalent to:

```text
verify_active_membership(resource_id, proof, active_root)
verify_active_nonmembership(resource_id, proof, active_root)
verify_nullifier_nonmembership(nullifier, proof, nullifier_root)
apply_deletes_and_inserts(pre_root, update_set) -> post_root
```

### 23.2 Reference profile

The initial reference implementation MAY use an in-memory `BTreeMap`/`BTreeSet` and a domain-separated sorted-set root for clarity and conformance.

This profile is not automatically suitable for production scale. A production sparse-Merkle or JMT profile requires a separate RFC, profile ID, proof format, vectors, and refinement evidence.

### 23.3 State root

The v0.1 reference accumulator commits sorted fixed-width identifiers:

```text
ActiveResourceRoot = ListRoot_"zrm.active_resource_set.v1"(
  ResourceId values sorted ascending
)

NullifierRoot = ListRoot_"zrm.nullifier_set.v1"(
  Nullifier values sorted ascending
)

EMPTY_ACTIVE_RESOURCE_ROOT = EmptyListRoot_"zrm.active_resource_set.v1"
EMPTY_NULLIFIER_ROOT       = EmptyListRoot_"zrm.nullifier_set.v1"
```

`ResourceId` commits the complete canonical resource bytes, so committing the sorted IDs commits the active records. Duplicate IDs or nullifiers reject. This sorted-set profile is the deterministic reference profile; a tree-backed profile has a separate ID, proof format, and vectors.

```text
MachineStateRootV1 {
  schema_version
  machine_id
  domain_id
  accumulator_profile_id
  active_resource_root
  nullifier_root
  policy_root
  state_version
}
```

```text
MachineStateRoot = H_"zrm.machine_state.v1"(
  canonical MachineStateRootV1 bytes
)
```

Genesis requires an independently governed nonzero policy root, both canonical empty accumulator roots, and `state_version = 0`. The resulting machine-state root is published as a golden vector before any transition can be admitted. In the transparent profile, the monotonic nullifier set supplies consumed-output history. A future profile that cannot test historical output reuse through its nullifier domain MUST add a committed history root to its profile-specific state schema.

---

## 24. Correct-by-construction transition pipeline

The implementation MUST represent the pipeline as distinct types or equivalent authority boundaries:

```text
UntrustedBytes
  -> BoundedBytes
  -> CanonicalEnvelope
  -> PrevalidatedTransition
  -> AuthenticatedFacts
  -> ValidatedTransition
  -> CommitPlan + JournalDraft
  -> policy-selected VerifiedAdmissionFact
  -> CommittedTransition
  -> AcceptedJournal
```

### 24.1 UntrustedBytes -> BoundedBytes

Check byte limits before allocation or recursive parsing.

### 24.2 BoundedBytes -> CanonicalEnvelope

Strict decode, version check, no trailing bytes, no unknown critical fields, canonical re-encoding equality.

### 24.3 CanonicalEnvelope -> PrevalidatedTransition

Using `TrustedValidationContext`, the expected state view, and governed policy, perform deterministic cheap checks through the resource-policy stage: identity equality, counts, canonical roots, role disjointness, membership, freshness, validity windows, and resource-policy invariants. No proof artifact is trusted and no committed state is mutated. The private result carries exact expected verifier statements and snapshot bindings.

### 24.4 PrevalidatedTransition -> AuthenticatedFacts

Pass only bounded artifacts and exact expected statements to the governed verifier registry. Raw artifacts remain untrusted. Construct sealed facts only on successful cryptographic verification and binding checks. Verification MAY run in parallel, while result ordering and later reject precedence remain deterministic.

### 24.5 PrevalidatedTransition + AuthenticatedFacts -> ValidatedTransition

Require exact fact coverage with no missing, duplicate, or extra facts; validate authenticated outputs; derive accounting and transformations; and compute the claimed post-state. This stage is pure and does not mutate committed state.

### 24.6 ValidatedTransition -> CommitPlan + JournalDraft

Derive exact deletes, inserts, nullifiers, replay keys, post roots, canonical journal-draft bytes, and audit commitments. `CommitPlan` MUST be private, non-serializable, and bound to the exact pre-state root/version, `ValidationContextHash`, and `JournalDraftHash`.

### 24.7 Policy-bound admission proof

`MachinePolicyV1.admission_mode` determines whether a proof, signature, or threshold receipt over the exact `JournalDraft` is forbidden or required before commit. The artifact arrives through a separate bounded second-phase input after the draft is available. A verified admission fact binds the draft hash, expected verifier/program, policy, profile, release identity, and reserved verifier-cost slot. It authorizes admission only if the commit plan's pre-state still matches. `LocalKernel` requires no admission fact; `RequiredVerifier` requires the exact governed verifier policy and fails closed if it is absent or different.

### 24.8 CommitPlan -> CommittedTransition

The storage/runtime adapter atomically compares the expected pre-state root/version and current authenticated `ValidationContextHash`, checks the policy-selected admission fact against the plan's exact journal draft, and applies all writes. Failure returns without partial visibility. An epoch or ordering-context advance makes the old plan stale even when machine state did not otherwise change.

### 24.9 CommittedTransition -> AcceptedJournal

The accepted journal is returned only after durable commit according to the active storage profile. `JournalDraft` and `AcceptedJournal` wrap identical canonical payload bytes, but they are different authority types. No public conversion can mark a draft accepted; only the successful commit result performs that retyping.

---

## 25. Normative validation algorithm

An implementation MUST preserve the following logical order. Independent checks MAY be parallelized only when error precedence and side effects remain deterministic.

```text
1.  Enforce raw byte and nesting bounds.
2.  Strict-decode the envelope and statement.
3.  Re-encode and require canonical byte equality.
4.  Load TrustedValidationContext, machine policy, and pre-state expectations.
5.  Require exact context equality and validate the active machine-policy and top-level transition windows.
6.  Require every child resource, policy, claim, authority, and DA identity to equal the parent transition identity.
7.  Derive IDs; check roles/ordinals; recompute resource, claim, evidence, and count roots.
8.  Verify consumed/reference membership and created active-set nonmembership.
9.  Verify consumed-nullifier freshness, created historical-nullifier nonmembership, and every resource/policy/claim validity window.
10. Validate resource objects against resource-kind policies.
11. Authenticate every artifact against the final StatementHash, exact claim hash, verifier policy, and fact validity window.
12. Require exact verified-fact coverage, authenticated outputs, and no extras.
13. Derive accounting rows and require the committed accounting root.
14. Verify conservation and exact transformation coverage.
15. Derive transition footprint and conflict keys.
16. Derive active-set deletes/inserts and nullifier inserts.
17. Compute post accumulator roots and machine-state root.
18. Require computed post root equals claimed post root.
19. Build the canonical JournalDraft and bound commit plan.
20. Enforce admission_mode: for RequiredVerifier, bound and verify the separately supplied admission artifact against the exact draft and its reserved cost slot; for LocalKernel, require that no admission fact was supplied.
21. Atomically compare-and-commit against expected pre-state/version and current ValidationContextHash.
22. Retype the committed draft as AcceptedJournal and return its audit receipt.
```

Steps 1-10 produce `PrevalidatedTransition`; step 11 produces `AuthenticatedFacts`; steps 12-19 produce `ValidatedTransition`, `JournalDraft`, and `CommitPlan`. No committed state mutation is permitted before step 21.

---

## 26. Rejection model

### 26.1 Stable reject taxonomy

Rejects MUST be typed. `RejectCodeV1` is a `u32` encoded as `u16_be(stage) || u16_be(reason)`. Zero is invalid. Stage tags and evaluation order are:

| Stage tag | Stage | Scope |
| ---: | --- | --- |
| `0x0001` | `IngressBounds` | raw byte, count, nesting, and allocation ceilings |
| `0x0002` | `CanonicalDecode` | framing, version, tags, lengths, ordering, trailing bytes |
| `0x0003` | `TrustedContext` | machine, domain, trusted epoch equality, active machine policy, top-level transition window, profile, pre-state |
| `0x0004` | `TransitionStructure` | child identity equality, IDs, uniqueness, roles, ordinals, counts, proof-independent roots |
| `0x0005` | `StateMembership` | active membership and created active-set nonmembership |
| `0x0006` | `Freshness` | nullifier, replay, historical output, resource/policy/claim validity windows |
| `0x0007` | `ResourcePolicy` | resource object and kind-policy invariants |
| `0x0008` | `Authentication` | proof, signature, authority, DA, verifier policy, authenticated-fact freshness |
| `0x0009` | `StatementBinding` | exact authenticated-fact coverage, outputs, accounting root, claimed post-state |
| `0x000a` | `Accounting` | arithmetic, units, conservation, transformation coverage |
| `0x000b` | `Conflict` | footprint, ordering, and declared scheduling conflicts |
| `0x000c` | `Admission` | journal-draft admission receipt |
| `0x000d` | `Commit` | state/version CAS including stale plans, atomic storage, durability |
| `0x00ff` | `Internal` | fail-closed internal error with no stronger public claim |

Within a stage, reason tags are append-only and never reused. The WP1 `ResourceWireV1` assignments are:

| Code | Label |
| ---: | --- |
| `0x00010001` | `zrm.bounds.resource_wire_bytes` |
| `0x00020001` | `zrm.malformed.resource_wire_header` |
| `0x00020002` | `zrm.malformed.resource_wire_magic` |
| `0x00020003` | `zrm.malformed.resource_wire_version` |
| `0x00020004` | `zrm.malformed.resource_wire_object` |
| `0x00020005` | `zrm.malformed.resource_wire_field_count` |
| `0x00020006` | `zrm.malformed.resource_wire_field_header` |
| `0x00020007` | `zrm.canonical.resource_wire_field_tag` |
| `0x00020008` | `zrm.canonical.resource_wire_field_length` |
| `0x00020009` | `zrm.malformed.resource_wire_field_value` |
| `0x0002000a` | `zrm.canonical.resource_wire_option_tag` |
| `0x0002000b` | `zrm.canonical.resource_wire_trailing` |

Public diagnostic labels use these normative namespaces:

```text
zrm.malformed.*
zrm.canonical.*
zrm.bounds.*
zrm.policy.*
zrm.domain.*
zrm.state.*
zrm.resource.*
zrm.nullifier.*
zrm.logic.*
zrm.authority.*
zrm.accounting.*
zrm.transform.*
zrm.evidence.*
zrm.da.*
zrm.conflict.*
zrm.commit.*
zrm.internal.*
```

### 26.2 Reject receipt

```text
RejectReceiptV1 {
  schema_version
  request_digest: Option<RequestDigest>
  transition_statement_hash: Option<StatementHash>
  pre_machine_state_root: Option<Commitment>
  reject_code: RejectCodeV1
}
```

For any complete bounded request bytes:

```text
RequestDigest = H_"zrm.untrusted_request.v1"(request_bytes)
```

Field presence is determined by completed parser milestones, never by caller choice or a diagnostic-disclosure policy:

| Completed milestone | `request_digest` | `transition_statement_hash` | `pre_machine_state_root` |
| --- | --- | --- | --- |
| no complete bounded request | absent | absent | absent |
| complete bounded request, but no canonical statement | present | absent | absent |
| canonical statement constructed and hashed | present | present | present |

An oversized or incomplete stream has no complete bounded request. A complete request is bounded before hashing, so `request_digest` is present even if a later decode or semantic stage rejects it. The statement hash and its claimed pre-machine-state root become present together if and only if strict decode, supported-version checks, canonical re-encoding equality, and statement-hash construction all succeed. Later rejection cannot suppress either field. All three fields use the canonical option tags from section 11.

The reject stage is derived as `u16(reject_code >> 16)`; it is never independently encoded. The constructor rejects zero/unknown stages, zero reasons, invalid option dependencies, and trailing fields.

```text
RejectReceiptHash = H_"zrm.reject_receipt.v1"(
  canonical RejectReceiptV1 bytes
)
```

A reject receipt is deterministic diagnostic evidence, not a state-transition authority object. Correlation IDs and private adapter details belong to a noncanonical logging envelope outside `RejectReceiptV1`. A disclosure profile may suppress the entire receipt, but it MUST NOT rewrite field presence and call the result a canonical `RejectReceiptV1`.

### 26.3 Error precedence

Given the same bytes, policy, state, and verified facts, the implementation MUST return the same reject code. Error precedence MUST be documented and tested.

### 26.4 Sensitive diagnostics

External reject messages MUST NOT expose secrets, private witness data, cryptographic internals, or oracle details beyond the active disclosure profile. Logs MAY include a correlation ID and internal diagnostic code in trusted environments.

---

## 27. Journal draft and accepted transition journal

```text
ResourceTransitionJournalV1 {
  schema_version
  machine_id
  domain_id
  application_id
  epoch

  transition_id
  statement_hash
  machine_policy_root
  verifier_set_root

  pre_machine_state_root
  post_machine_state_root
  pre_state_version
  post_state_version
  pre_active_resource_root
  post_active_resource_root
  pre_nullifier_root
  post_nullifier_root

  consumed_resources_root
  referenced_resources_root
  created_resources_root
  consumed_nullifiers_root
  logic_claims_root
  transformation_claims_root
  authority_claims_root
  data_availability_claims_root
  accounting_rows_root

  evidence_root
  provenance_root
  data_availability_root
  data_availability_certificate_root
  execution_context_root
  ordering_context_root

  consumed_count
  referenced_count
  created_count
  logic_claim_count
  transformation_claim_count
  authority_claim_count
  data_availability_claim_count
  accounting_row_count
}
```

The journal payload MUST be small, canonical, deterministic, and verifier-oriented. It MUST NOT contain hidden side conditions or free-form claims.

```text
JournalPayloadHash = H_"zrm.transition_journal.v1"(
  canonical ResourceTransitionJournalV1 bytes
)

JournalDraftHash = JournalPayloadHash before commit
JournalHash      = JournalPayloadHash after commit
```

`JournalDraft` and `AcceptedJournal` contain the same payload and digest. Their authority differs. A draft is deterministic precommit data bound into a `CommitPlan`; an accepted journal is returned only by successful durable commit. A journal payload by itself remains data. Consumers MUST authenticate its source through a trusted committed runtime result, signature, proof, or governed verifier receipt.

---

## 28. Atomic persistence and exact-once commit

### 28.1 Atomic write set

A persistent commit MUST atomically include:

- active-resource deletions;
- active-resource insertions;
- nullifier insertions;
- transition-ID replay record;
- journal-draft bytes retyped as the accepted journal and its hash;
- state version update;
- policy-required admission receipt reference, when applicable;
- reward or escrow movement when part of the transition;
- outbox records for external effects, when applicable;
- audit record required by profile.

### 28.2 Compare-and-swap

The commit linearization point MUST atomically require this tuple to equal the plan's expected values:

```text
(machine_state_root, state_version, validation_context_hash)
```

The runtime obtains `validation_context_hash` from the same authenticated epoch/ordering authority used to construct `TrustedValidationContext`. A concurrent state winner or an epoch/order-context advance changes the tuple, causing the plan to reject as stale. Implementations MUST use one transactional/locked comparison or a refinement-equivalent primitive; separate non-atomic checks are forbidden.

The stable `CommitError` variants are:

```text
StaleState
StaleValidationContext
AdmissionRequired
AdmissionUnexpected
AdmissionMismatch
AtomicWriteFailed
DurabilityFailed
Internal
```

No variant implies that a partial commit is acceptable. Adapter-specific errors are mapped into this fail-closed taxonomy and retained only in bounded private diagnostics.

### 28.3 Crash consistency

The storage profile MUST define its crash-consistency mechanism, such as transactional database commit or write-ahead log plus fsync and atomic pointer update. Tests MUST inject crashes before and after each persistence boundary.

### 28.4 No split replay state

Replay/nullifier state MUST NOT be committed separately from value or authority effects. Otherwise a crash can produce consumed-without-value or value-without-consumed states.

### 28.5 Exact-once scope

ZRM exact-once semantics cover effects represented in the atomic committed machine write set. An external network message, payment rail, storage upload, or other side effect is outside that boundary. Such effects require an atomically persisted outbox key derived from `TransitionId` and an idempotent receiver or a profile that explicitly declares at-least-once delivery. Documentation MUST NOT promote outbox persistence into an exact-once external-delivery claim.

---

## 29. Concurrency and scheduling

### 29.1 Parallel validation

Proof verification and pure semantic validation MAY run concurrently.

### 29.2 Conflict footprint

The kernel derives:

```text
TransitionFootprintV1 {
  read_resource_ids_root
  consumed_resource_ids_root
  created_resource_ids_root
  nullifier_writes_root
  policy_reads_root
  application_conflict_keys_root
}
```

The proposer may suggest a footprint, but the kernel MUST derive or verify it.

### 29.3 Safe parallel commit

The v0.1 profile has one machine-state root and one global state version. Commits are therefore serialized by deterministic order. Proof verification and pure validation MAY run in parallel, but after one plan commits, every other plan built on the prior global root/version is stale and must be rejected or deterministically revalidated into a new plan.

A later profile MAY permit parallel commits only after it specifies shard or key-range versions, MVCC validation, journal ordering, root composition, and a proof of serializability or disjoint commutativity under a distinct accumulator/profile ID. The abstract commutativity theorem alone does not authorize parallel durable writes.

### 29.4 Ordering

Any ordering-dependent semantics MUST bind `ordering_context_root`. A pre-order proof MUST NOT be reused after final ordering unless the profile defines and proves the relationship.

---

## 30. Proof-system adapter interface

### 30.1 Verifier policy

```text
VerifierPolicyV1 {
  schema_version
  verifier_policy_id
  machine_id
  domain_id
  backend_family_id
  verifier_id
  program_or_key_digest
  artifact_codec_id
  statement_schema_root
  journal_schema_root
  proof_parameter_root
  proof_mode
  coverage_claims_root
  non_claims_root
  trusted_computing_base_root
  verifier_cost_model_id
  max_verifier_cost_units
  max_artifact_bytes
  max_public_input_bytes
  max_public_output_bytes
  validity_start_epoch
  validity_end_epoch
}
```

`proof_mode` is exactly one of `Production`, `Development`, or `Test`. A production machine policy MUST authorize only `Production` verifier policies for authority-bearing facts. Development, fake, skipped, assumed, or test receipts MUST fail the production registry path even if their byte format and public output otherwise match.

The verifier registry MUST require `VerifierPolicyV1.verifier_cost_model_id == MachinePolicyV1.verifier_cost_model_id`, use checked addition for every charged cost, and reject before verification would exceed either the per-verifier or total machine-policy budget.

#### Deterministic verifier charge

One governed cost model defines the units used by every verifier policy under a machine policy:

```text
VerifierCostRowV1 {
  backend_family_id: BackendFamilyId
  base_units: u64
  artifact_byte_units: u64
  statement_byte_units: u64
  reserved_output_byte_units: u64
}

VerifierCostModelV1 {
  schema_version: u16
  rows_root: Commitment
  max_charge_units: u64
}
```

Rows are sorted by `backend_family_id`, are unique, and cover every authorized backend family. Each row and the model ID are derived as:

```text
VerifierCostRowHash = H_"zrm.verifier_cost_row.v1"(
  canonical VerifierCostRowV1 bytes
)

rows_root = ListRoot_"zrm.verifier_cost_rows.v1"(
  VerifierCostRowHash values in backend_family_id order
)

VerifierCostModelId = H_"zrm.verifier_cost_model.v1"(
  schema_version,
  rows_root,
  max_charge_units
)
```

For each planned verifier dispatch, the registry selects the exact row for `VerifierPolicyV1.backend_family_id` and computes:

```text
charge_units =
    base_units
  + artifact_byte_units * artifact_len
  + statement_byte_units * canonical_statement_len
  + reserved_output_byte_units * VerifierPolicyV1.max_public_output_bytes
```

`artifact_len` is the exact bounded artifact byte length presented to the governed wrapper. `canonical_statement_len` is the exact canonical statement byte length presented to that wrapper. The reserved output term uses the policy maximum rather than backend-produced output, so an untrusted backend cannot lower or raise its pre-dispatch charge.

Before this calculation, the registry MUST enforce the verifier policy's artifact, public-input, and public-output bounds. Every multiplication and addition uses a checked `u128` intermediate. The result MUST fit `u64` and MUST be no greater than both `VerifierCostModelV1.max_charge_units` and `VerifierPolicyV1.max_verifier_cost_units`.

The registry MUST construct the complete cost plan and sum all charges before invoking any transition-fact verifier. The plan includes every supplied logic, transformation, authority, and DA artifact. Dispatch-plan order is the fixed fact-class order just listed, followed by each class's canonical claim order.

Before that governed registry exists, an implementation MUST NOT expose a
public operation that accepts a caller-selected row and returns an
authority-shaped checked quote. Likewise, a structural comparison between
caller-provided machine and verifier candidates MUST NOT be exposed as verifier
admission. Pre-registry arithmetic and compatibility predicates may exist only
as internal assurance helpers and construct no public capability.

When `admission_mode` is `RequiredVerifier`, the admission artifact and draft do not yet exist. The cost plan therefore adds one conservative admission reservation selected from the required admission verifier policy:

```text
admission_reserved_units =
    base_units
  + artifact_byte_units * VerifierPolicyV1.max_artifact_bytes
  + statement_byte_units * VerifierPolicyV1.max_public_input_bytes
  + reserved_output_byte_units * VerifierPolicyV1.max_public_output_bytes
```

The same checked arithmetic and per-verifier/model limits apply to this reservation. `LocalKernel` has no admission reservation. Checked cumulative addition, including the reservation, MUST remain at or below `MachinePolicyV1.max_total_verifier_cost_units`. On successful transition-fact authentication, `AuthenticatedFacts` privately carries the planned total and admission reservation; finalization transfers both into the bound `CommitPlan`.

After finalization produces the exact draft, the separate admission-verification call bounds the artifact, requires the canonical draft length to fit `max_public_input_bytes`, computes its actual charge using `artifact_len` and `canonical_statement_len`, and requires that charge to be no greater than the stored reservation. It does not change the planned total.

The planned total is fixed even if a transition-fact or admission verifier later rejects its artifact; failure does not refund or recompute the request's planned charge. Missing or extra transition-fact artifacts reject before their dispatch phase. A missing or extra admission artifact rejects in the second phase before commit. Parallel execution MUST preserve the same plan, total, and error precedence. Postcommit aggregation and anchor verification are outside this transition-admission budget and require their own governed budget.

Each backend wrapper MUST document and evidence that this row upper-bounds its governed worst-case verification work for every permitted program/key and bounded input. The deterministic charge meters one transition attempt; it does not claim wall-clock equivalence across hardware and does not replace deployment-level request rate limits.

The coverage and non-claim documents are canonical, content-addressed profile artifacts. They state which relation the verifier establishes, what public inputs and outputs it binds, privacy properties, assumptions, unsupported operations, and known metadata leakage. A valid proof establishes only that named relation under the pinned verifier policy.

The journal draft's `verifier_set_root` is:

```text
VerifierSetRoot = ListRoot_"zrm.verifier_set.v1"(
  sorted unique VerifierPolicyId values in verifier_set
)

verifier_set =
  policies used by finalized logic/transformation/authority/DA facts
  union
  { policy-required expected admission verifier policy, if any }
```

The expected admission policy ID is included before its proof arrives so `JournalDraft` remains stable. Commit fails unless the supplied admission fact matches that exact expected policy and draft hash. Postcommit aggregation or anchor verifier IDs are excluded because they cannot alter the already accepted journal.

Multiple facts may use the same verifier policy. `verifier_set` deliberately records each policy ID once; claim multiplicity and ordering remain committed by the logic/transformation claim roots. This specified set projection is not silent deduplication of an input list.

### 30.2 Port ownership and sealed registration

The verifier API crate defines narrow ports and owns all verified-fact constructors. The semantic kernel depends only on those sealed capabilities. Concrete backends depend inward.

Conceptual Rust API:

```rust
pub trait RegisteredLogicVerifier: sealed::Sealed {
    type Artifact;
    type Error;

    fn verify_untrusted(
        &self,
        expected: &LogicStatementV1,
        artifact: &Self::Artifact,
        policy: &VerifierPolicyV1,
    ) -> Result<BackendVerifiedOutput, Self::Error>;
}

impl VerifierRegistry {
    pub fn verify_logic(
        &self,
        expected: &LogicStatementV1,
        artifact: &BoundedArtifact,
        policy: &VerifierPolicyV1,
    ) -> Result<VerifiedLogicFact, VerifyError>;
}
```

`BackendVerifiedOutput` and `VerifiedLogicFact` have private constructors. Registry code checks that the backend is compiled into or authenticated by the governed registry, that its release digest and policy are current, and that its output exactly matches the expected bound statement before constructing the fact.

An arbitrary downstream crate cannot implement `sealed::Sealed`, register a runtime callback, or mint a fact. Adding a backend requires a reviewed registry wrapper, policy entry, release identity, negative tests, and trusted-computing-base update. A remote verifier response is untrusted until the registry verifies its signature or proof locally.

Equivalent sealed registry paths exist for transformations, authorities, DA certificates, admission receipts, and postcommit aggregation receipts.

### 30.3 Adapter requirements

Every adapter MUST:

- enforce input byte and depth bounds;
- reject debug/fake/placeholder artifacts under production profiles;
- verify exact program/verifier identity;
- verify exact statement and public output;
- verify proof/profile/policy compatibility;
- bind freshness and expiry;
- derive verified facts locally;
- expose stable typed errors;
- produce replayable verification evidence;
- publish explicit non-claims.

### 30.4 Fact-class binding

Fact classes bind the artifact available at their stage:

- precommit logic, transformation, authority, and DA facts bind the final `StatementHash`, their exact claim hash, expected authenticated output, verifier policy, and validity window;
- a precommit admission fact binds the exact `JournalDraftHash`, program/key, policy, profile, and release identity;
- a postcommit aggregation or anchor fact binds exact `AcceptedJournal` bytes and hashes plus the ordered manifest it aggregates.

Precommit resource facts MUST NOT claim to bind an accepted journal that does not yet exist. Postcommit receipts MUST NOT be used to retroactively authorize an already committed transition.

### 30.5 Supported backend classes

Potential adapters include:

- deterministic native verifier;
- signatures and threshold certificates;
- RISC0 or another zkVM;
- specialized ZKML inference/training verifier;
- Lean theorem receipt;
- SMT or bounded state-machine result;
- public replay harness;
- trusted-hardware attestation;
- oracle quorum certificate.

No backend is trusted merely because its artifact has a known file extension or proof-looking structure.

---

## 31. Recursive-proof integration

### 31.1 Semantic leaf

A recursive semantic leaf authenticates exact `ResourceTransitionJournalV1` payload bytes and the wrapper stage declared by its profile:

- an **admission leaf** binds a `JournalDraftHash` and is verified before the bound commit plan attempts compare-and-swap;
- an **aggregation leaf** binds an `AcceptedJournal` and is used only for postcommit compression, audit, or anchoring.

The profile MUST distinguish these modes. An aggregation leaf cannot authorize admission, and an admission leaf does not prove that its draft ultimately committed.

### 31.2 Semantic epoch root

For an epoch containing accepted journals sorted by a governed canonical key:

```text
semantic_epoch_root = H_"zrm.semantic_epoch.v1"(
  epoch,
  policy_root,
  u32_be(journal_count),
  journal_hash_0,
  ...,
  journal_hash_n
)
```

### 31.3 Proof-tree root

A separate `proof_tree_root` binds recursive topology, child claims, intermediate images, and receipt identities.

Even when transport discards individual proof bytes after aggregation, the aggregate statement and retained audit record MUST commit an ordered manifest containing each child journal hash, transition statement hash, verifier policy ID, program/key digest, proof profile, release identity, and child position. Omission, duplication, substitution, or reordering rejects.

Requirement:

```text
same ordered semantic journals
  -> same semantic_epoch_root
```

regardless of valid proof-tree grouping.

### 31.4 Root acceptance

A consumer accepting a recursive root MUST verify:

- root proof and expected program;
- exact common recursive journal and ordered child manifest;
- semantic epoch root;
- machine/domain/epoch/policy;
- expected transition count or partition plan;
- DA policy;
- no replay of root, transition, nullifier, or descendant identity;
- wrapper mode (`admission` or `postcommit_aggregation`);
- atomic state integration for admission mode, including the current root/version CAS.

Recursive compression does not solve DA, finality, or application semantics by itself.

---

## 32. Data availability

### 32.1 Commitment versus availability

`data_availability_root` proves only which bytes or objects a computation committed to. It does not prove retrieval.

### 32.2 Verified DA fact

A profile requiring availability MUST consume a sealed `VerifiedDaFact` produced by a governed DA verifier.

The fact MUST bind the final transition `StatementHash`, exact `DataAvailabilityClaimHash` and `DataAvailabilityStatementHash`, governed verifier policy, committed content root, expected certificate root, and validity window. Exact claim/artifact/fact coverage follows section 18.3.

Possible certificate profiles include:

- full local blob inclusion;
- erasure-coded sampling receipt;
- storage-provider quorum;
- chain blob inclusion;
- IPFS/Filecoin/Arweave retrieval and persistence policy;
- public replay bundle.

### 32.3 Failure posture

If a transition is bound to a policy that requires DA verification, unavailable verification MUST reject. A weaker DA profile may be used only when it was independently selected and bound into machine policy and the transition statement before evaluation. Runtime fallback or silent downgrade after a verifier failure is forbidden. The weaker profile's UI and journal make no availability claim.

---

## 33. Privacy profiles

### 33.1 Transparent v0.1

The reference profile is transparent. Resource commitments, nullifiers, counts, timing, and journals may reveal linkable information.

### 33.2 Future shielded profile

A shielded profile requires separate specifications for:

- commitment and nullifier schemes;
- data privacy;
- function privacy;
- selective disclosure;
- key management and recovery;
- network metadata leakage;
- timing and proof-size leakage;
- wallet scanning and state discovery;
- audit and regulatory disclosure policy.

A computational-integrity proof MUST NOT be described as private or zero-knowledge unless the complete profile establishes those properties.

---

## 34. External and physical-resource attestations

ZRM MAY model signed meter readings, hardware attestations, data licenses, geolocation claims, carbon certificates, or legal credentials as evidence resources.

The journal MUST distinguish:

```text
attestation authenticated
```

from:

```text
attested proposition independently true
```

Policy determines which issuers and mechanisms are trusted. The trust assumption appears in the machine policy, provenance, UI, and non-claims.

---

## 35. Proof Resource Machine reference adapter

The first application adapter SHOULD be a Proof Resource Machine because proof validity and exact-once rewards are objectively checkable.

### 35.1 Resource kinds

```text
ProofTaskResource
ProofBudgetResource
ProverCapacityResource
ProverBondResource
ProofAssignmentResource
VerifiedProofReceiptResource
AggregationTaskResource
RewardEscrowResource
RewardClaimResource
ChallengeResource
SlashClaimResource
```

### 35.2 Lifecycle transitions

#### Publish task

```text
ProofBudget + TaskSpecification
  -> ProofTask + RewardEscrow
```

#### Assign

```text
ProofTask + ProverCapacity + ProverBond
  -> ProofAssignment + ReservedCapacity + LockedBond
```

#### Complete

```text
ProofAssignmentResource + VerifiedProofFact
  -> VerifiedProofReceiptResource + RewardClaimResource + ReleasedCapacity + ReleasedBond
```

#### Timeout/reassign

```text
ExpiredAssignment + StandbyCapacity
  -> ReplacementAssignment + timeout accounting
```

#### Challenge/slash

```text
Verified counterexample or invalid-proof evidence + LockedBond
  -> SlashClaim + residual bond
```

#### Settle

```text
RewardClaim + RewardEscrow
  -> ProverPayment + ResidualEscrow
```

### 35.3 Market integrity requirements

- one canonical reward per task unless policy pays explicit redundancy;
- assignment and proof bind exact task statement;
- capacity cannot be double-reserved;
- bonds and rewards commit atomically;
- timeout uses logical epoch, not wall clock inside the kernel;
- proof verification result comes from a sealed verifier adapter;
- a valid proof submitted after another valid canonical proof may be accepted as evidence but is unpaid unless policy states otherwise;
- auction and bidding logic live in an adapter, not the ZRM core.

---

## 36. Application adapter conformance

Every application adapter MUST define:

1. resource kinds and units;
2. resource-kind policies;
3. consumed, referenced, and created resource semantics;
4. resource logic statements;
5. transformation rules;
6. accounting rows;
7. authority roots;
8. validity windows and replay domains;
9. DA requirements;
10. privacy profile;
11. conflict footprint;
12. reject taxonomy;
13. canonical vectors;
14. disaster states;
15. explicit non-claims.

An adapter MUST NOT add hidden mutable state outside resources unless that state is explicitly rooted in the transition statement and governed by a separate, documented state machine.

---

## 37. Recommended Rust workspace architecture

```text
crates/
  zrm-types/          opaque IDs, wire inputs, validated value types
  zrm-codec/          normative encoding, strict transport decoding
  zrm-crypto/         hash-suite traits and reference suite
  zrm-policy/         machine and resource-kind policy types
  zrm-verifier-api/   ports and sealed verified-fact capabilities
  zrm-kernel/         pure transition validation and commit-plan derivation
  zrm-journal/        journal-draft, accepted-journal, and reject-receipt ABIs
  zrm-reference/      in-memory deterministic reference machine
  zrm-conformance/    golden vectors and cross-language harness
  zrm-store/          optional persistence ports and reference adapter

adapters/
  proof-resource-machine/
  reference-asset-transfer/
  reference-capability-workflow/
  risc0/
  signatures/
  data-availability/

formal/
  lean/
  verus/
  kani/
  state-machine-models/
  tla/
```

### 37.1 Trusted core boundary

The smallest practical trusted semantic core is:

```text
zrm-types
zrm-codec
zrm-policy
zrm-verifier-api capability boundary
zrm-kernel
zrm-journal
reference hash suite
```

Networking, databases, CLI, JSON, UI, proof generation, model inference, and application-specific logic are outside this core.

### 37.2 `no_std`

Core crates SHOULD support `no_std`; bounded allocation may use `alloc`. `std` features belong in adapters and tooling.

### 37.3 Unsafe code

Core crates MUST declare:

```rust
#![forbid(unsafe_code)]
```

An optimized adapter requiring unsafe code MUST isolate it in a separate crate and provide:

- written safety invariants;
- `// SAFETY:` explanation at each unsafe operation;
- Miri tests;
- Kani or equivalent proof harness where feasible;
- fuzzing;
- independent review;
- a safe reference implementation and differential tests.

---

## 38. Public API design

### 38.1 Minimal capability API

Conceptual API:

```rust
pub fn prevalidate_transition(
    context: &TrustedValidationContext,
    state: &impl StateView,
    policy: &MachinePolicyV1,
    envelope: CanonicalTransitionEnvelope<'_>,
) -> Result<PrevalidatedTransition, Reject>;

impl VerifierRegistry {
    pub fn authenticate_transition(
        &self,
        prevalidated: &PrevalidatedTransition,
    ) -> Result<AuthenticatedFacts, Reject>;

    pub fn verify_admission(
        &self,
        plan: &CommitPlan,
        draft: &JournalDraft,
        artifact: &BoundedArtifact,
    ) -> Result<VerifiedAdmissionFact, Reject>;
}

pub fn finalize_transition(
    prevalidated: PrevalidatedTransition,
    facts: AuthenticatedFacts,
) -> Result<(CommitPlan, JournalDraft), Reject>;

pub trait AtomicCommitPort {
    fn commit(
        &mut self,
        current_context: &TrustedValidationContext,
        plan: CommitPlan,
        admission: Option<VerifiedAdmissionFact>,
    ) -> Result<(CommittedTransition, AcceptedJournal), CommitError>;
}
```

`TrustedValidationContext`, `PrevalidatedTransition`, `AuthenticatedFacts`, `CommitPlan`, `JournalDraft`, `VerifiedAdmissionFact`, `CommittedTransition`, and `AcceptedJournal` have private authority-bearing fields. `CommitPlan` is consumed by commit and is not reusable.

`verify_admission` is available only for a plan whose policy selected `RequiredVerifier`. It requires the supplied draft to be the plan's exact draft, dispatches only through the plan's governed admission verifier policy, and enforces the cost reservation created before transition-fact verification. A `LocalKernel` plan rejects this call.

### 38.2 API rules

- no boolean parameters on security-critical APIs; use enums or named input structs;
- no untyped string modes;
- no implicit `Default` for critical types;
- constructors validate all invariants;
- functions returning decisions or plans use `#[must_use]`;
- exhaustive matches for protocol enums;
- public fields only for inert data-transfer objects; validated types use getters;
- no `unwrap`, `expect`, `panic!`, indexing panic, or unchecked conversion in production core paths;
- typed errors, not string matching;
- no hidden allocation proportional to untrusted input beyond established bounds;
- no public API that accepts both verified and unverified forms under one type.

---

## 39. Clean architecture and maintainability requirements

### 39.1 SOLID adapted to Rust

**Single Responsibility:** each crate/module/type/function has one reason to change. Parsing, authentication, semantic validation, persistence, and reporting are separate.

**Open/Closed:** add resource kinds and verifier backends through versioned policies and narrow adapters, not edits to a giant central `match` over every application.

**Liskov Substitution:** every adapter implementation satisfies the same preconditions, postconditions, error semantics, and no-side-effect guarantees. A faster adapter cannot weaken semantics.

**Interface Segregation:** ports are small. A hash provider does not also provide networking; a state view does not expose commit; a verifier does not mutate state.

**Dependency Inversion:** core policy and semantics own interfaces. Infrastructure depends inward.

### 39.2 DRY without premature abstraction

DRY applies to semantic rules, encodings, domain strings, error codes, and test vectors. It does not require abstracting every repeated three-line block.

Use the rule of three for incidental implementation repetition. Prefer two clear local implementations over one obscure generic abstraction when the semantics differ.

Never duplicate canonical encoding or hash logic across languages without golden vectors or generated specifications.

### 39.3 Self-documenting code

- names include domain meaning and units;
- types distinguish IDs and roots;
- functions are verbs describing one operation;
- comments explain invariants, authority, and non-obvious reasoning, not syntax;
- each public function documents preconditions, postconditions, failure modes, side effects, complexity, and panic behavior;
- every unsafe or cryptographic boundary documents assumptions;
- every profile documents non-claims.

### 39.4 Complexity budgets

These are review budgets; exceeding them requires an ADR, focused tests, and reviewer approval.

| Item | Preferred budget | Hard review trigger |
| --- | ---: | ---: |
| critical function logical lines | <= 40 | > 60 |
| cyclomatic complexity | <= 8 | > 12 |
| cognitive complexity | <= 10 | > 15 |
| nesting depth | <= 3 | > 4 |
| positional parameters | <= 4 | > 6 |
| critical module logical lines | <= 400 | > 700 |
| public trait methods | <= 7 | > 10 |
| generic type parameters on public API | <= 3 | > 4 |

Split functions by invariant family, not arbitrary line count.

### 39.5 Forbidden code smells

- god objects or manager classes containing parsing, validation, storage, and policy;
- boolean blindness;
- stringly typed IDs, modes, or error codes;
- primitive obsession for 32-byte IDs;
- shotgun edits across unrelated crates;
- hidden fallback;
- feature flags that bypass verification;
- `HashMap` iteration in canonical paths;
- wall-clock access in semantic paths;
- floating point in authority paths;
- duplicated validation in host and guest without parity evidence;
- comments used to excuse an unenforced invariant;
- broad `allow` attributes without a reason and issue;
- tests that duplicate implementation logic rather than state the invariant.

---

## 40. Testing strategy

Tests are evidence layers, not substitutes for good construction.

### 40.1 Required layers

1. type-level construction tests;
2. unit tests named by invariant;
3. canonical encoding and hash vectors;
4. negative and mutation tests;
5. property tests;
6. model checking;
7. fuzz and malformed grammar tests;
8. differential tests against reference semantics;
9. BDD integration scenarios;
10. persistence/crash tests;
11. proof-adapter tests;
12. release replay.

### 40.2 BDD scope

BDD/Gherkin is REQUIRED for cross-layer, actor-visible behavior such as exact-once admission, proof task payout, stale-policy rejection, and crash recovery.

BDD is NOT the primary tool for pure hashing, arithmetic, or codec invariants. Use unit/property/formal tests for those.

Scenarios SHOULD have one business rule and roughly 3-5 steps. `Then` assertions target observable outputs or stable protocol decisions rather than private implementation details.

### 40.3 Property tests

Required properties include:

- canonical encode/decode round trip;
- noncanonical encodings reject;
- list permutations canonicalize or reject according to profile;
- duplicate resources reject;
- resource commitment changes when any authority field changes;
- nullifier changes across machine/domain/resource identity;
- same input produces same journal;
- reject preserves state;
- accounting rows conserve;
- uncovered transformation deltas reject;
- disjoint accepted transitions commute;
- stale pre-root commit fails;
- semantic epoch root is tree-shape independent.

Seeds and minimized counterexamples MUST be committed.

### 40.4 Mutation tests

Every critical guard needs at least one mutation that removes, inverts, or redirects the guard. No critical mutant may survive promotion.

Mandatory mutant classes:

- skip nullifier check;
- skip output nonmembership;
- accept stale policy;
- remove resource-role binding from logic statement;
- trust proposed accounting rows;
- allow arithmetic wrap;
- commit before final validation;
- accept proof metadata without verification;
- replace expected root with sibling root;
- accept unknown schema field;
- change sort key or silently deduplicate;
- accept stale pre-state commit.

### 40.5 Fuzzing

Fuzz targets include:

- resource decoder;
- transition envelope decoder;
- journal decoder;
- list/count framing;
- maximum-bound edges;
- proof adapter envelopes;
- diagnostic JSON duplicate keys;
- state proofs and membership proof decoders.

Fuzzers MUST be bounded in CI. Crashes and hangs are failures. Minimized corpus entries become regression tests.

### 40.6 Coverage

Coverage percentages are not sufficient promotion evidence. Recommended goals:

- critical core line and branch coverage: 100% review target;
- workspace line coverage: >= 90%;
- workspace branch coverage: >= 85%;
- critical mutation score: 100% for enumerated critical mutants;
- general mutation score: >= 90%.

Any exclusion requires a reason.

### 40.7 Undefined-behavior and interpreter checks

Miri MUST run on crates that contain `unsafe`, custom allocation, raw pointers, FFI shims, or byte-level transmutation. Miri success is evidence for the exercised executions, not a soundness proof. Unsafe code still requires a written safety contract, API-level invariant tests, fuzzing, and independent review.

Where practical, CI SHOULD exercise different Miri seeds, randomized layout, and endian-sensitive golden vectors. Cryptographic key generation MUST NOT run under Miri's deterministic fake RNG.

### 40.8 Concurrency exploration

Loom or an equivalent deterministic concurrency model MUST cover any in-process synchronization used by atomic admission, commit coordination, replay-state updates, caches that influence authority, or proof-market assignment. The model MUST include at least:

- two plans racing to consume one resource;
- reader/writer visibility around commit;
- cancellation or timeout racing with completion;
- lock poisoning or task failure where applicable;
- stale state-version compare-and-swap.

Loom coverage is incomplete if synchronization hidden in dependencies is not replaced or modeled. Durable database atomicity and distributed consensus require separate crash/state-machine models.

### 40.9 Differential and metamorphic testing

An optimized kernel MUST be tested against a deliberately simple reference semantics. Differential tests compare:

- accept/reject decision;
- stable reject class;
- accounting rows;
- state roots;
- nullifiers;
- accepted journal bytes.

Metamorphic tests SHOULD check domain separation, role substitution, permutation behavior, addition of irrelevant diagnostic metadata, and equivalent proof-tree groupings.

---

## 41. Formal assurance strategy

Use multiple techniques for different failure classes rather than forcing one tool onto every problem.

### 41.1 Kani

Use Kani for bit-precise bounded verification of:

- panic freedom;
- checked arithmetic;
- bounds and indexing;
- codec round trips over bounded domains;
- unsafe adapter invariants;
- state-transition corner cases.

### 41.2 Verus or Creusot

Select one primary deductive Rust verification lane by RFC. Use it for functional correctness of stable pure kernel components such as:

- exact-once transition relation;
- accounting derivation;
- role uniqueness;
- commit-plan invariants;
- deterministic canonicalization.

Do not maintain two full proof stacks for the same code during v0.1.

### 41.3 Lean

Use Lean for stable mathematical and refinement theorems:

- framing/hash injectivity under explicit assumptions;
- conservation preservation;
- exact-once theorem shape;
- disjoint commutativity;
- semantic epoch associativity/tree independence;
- reference-model equivalence.

No `sorry` in promoted theorem modules.

### 41.4 SMT and state-machine models

Use bounded SMT and state-machine models such as TLA+ or Alloy for:

- concurrent double spend;
- stale-policy transitions;
- crash/replay states;
- proof-market assignment and reward exact-once;
- finite transformation coverage;
- state-version monotonicity;
- governance rotation.

`UNKNOWN`, timeout, missing solver, or nondeterministic fingerprints do not count as proof.

### 41.5 Aeneas or equivalent extraction research lane

Aeneas MAY be evaluated for translating the supported safe-Rust subset into Lean, F*, Rocq/Coq, or HOL4. This is a research and refinement lane, not an automatic promotion gate. Before relying on extraction, the project MUST pin the translator and Rust frontend, record unsupported Rust features, review all handwritten external models, and prove or test that the extracted entry points match the runtime ABI.

### 41.6 Refinement obligation

A formal model is useful only if the runtime implementation is linked to it through:

- shared generated constants;
- golden vectors;
- extraction/code generation;
- verified implementation;
- or a documented refinement argument plus tests.

Theorem-shaped prose is not evidence. Translation or proof-tool success does not verify the Rust compiler, LLVM, operating system, proof backend, or deployment environment unless those components are separately covered.

---

## 42. Defensive Rust rules

Core crates MUST:

- use safe Rust only;
- deny warnings in CI;
- deny missing documentation on public APIs;
- use checked arithmetic;
- avoid panicking APIs;
- avoid recursion over untrusted data;
- bound every collection derived from untrusted input;
- use `BTreeMap`/`BTreeSet` or sorted vectors in deterministic paths;
- use explicit integer widths;
- avoid platform-dependent `usize` in canonical encodings;
- avoid `as` for potentially lossy conversion; use `TryFrom`;
- avoid `Default` for authority-bearing values;
- avoid `serde(default)` on critical fields;
- reject unknown critical fields;
- isolate wire types from validated types;
- use `#[must_use]` on plans, decisions, and receipts;
- use stable error enums;
- avoid secret-bearing `Debug` implementations;
- make default `Debug` output for opaque identifiers, roots, commitments, and
  nonces constant and redacted; raw canonical-wire diagnostic formatting MUST
  redact every 32-byte identifier, root, commitment, and nonce candidate;
  numeric scalar candidates MAY remain visible, and diagnostic fingerprints
  MUST NOT include the redacted bytes;
- zeroize secrets in future private profiles;
- include `rust-version` and a pinned `rust-toolchain.toml`.

Lint suppression SHOULD use `#[expect(..., reason = "...")]` where supported, so obsolete suppressions become visible.

---

## 43. Dependency and supply-chain policy

### 43.1 Minimal dependencies

The trusted core SHOULD minimize dependencies. Every new dependency in the TCB requires:

- purpose;
- alternatives considered;
- license;
- maintenance and security status;
- build scripts/proc macros/native code;
- unsafe code footprint;
- feature set;
- transitive dependency delta;
- removal plan.

### 43.2 Cargo policy

- commit `Cargo.lock`;
- use `--locked` in CI and `--frozen` in release builds;
- pin critical proof and cryptographic dependencies exactly;
- deny unapproved git and path dependencies in releases;
- review build scripts and proc macros as executable TCB;
- run `cargo deny`, `cargo audit`, and, when configured, `cargo vet`;
- produce an SBOM;
- maintain a cryptographic bill of materials for algorithms and parameters;
- reject known affected dependencies before release.

### 43.3 Provenance

Release artifacts SHOULD target SLSA v1.2 provenance and follow NIST SSDF practices. A release manifest includes:

- source commit and clean-tree status;
- source archive digest;
- compiler and Cargo executable digests;
- target and linker;
- lockfile and dependency closure;
- generated-source roots;
- build command and environment policy;
- offline/network-isolation status;
- binary and library digests;
- SBOM/CBOM;
- test, fuzz, mutation, formal, and conformance reports;
- signed provenance and verification summary;
- known gaps and non-claims.

### 43.4 Reproducibility

A production release requires independent clean builds in isolated environments. Compiler-visible absolute paths, home paths, timestamps, and nondeterministic code generation MUST be removed, remapped, or explicitly demonstrated not to affect artifacts.

---

## 44. CI and quality gates

### 44.1 Pull-request gate

- format;
- compile all targets/features;
- Clippy correctness/suspicious/complexity plus curated pedantic lints;
- unit and integration tests;
- canonical vectors;
- dependency policy;
- changed-file complexity report;
- CBC matrix consistency;
- docs build;
- no forbidden patterns.

### 44.2 Nightly gate

- property tests with expanded corpus;
- fuzz smoke;
- mutation suite;
- Kani harnesses;
- Miri where applicable;
- SMT and state-machine models;
- coverage report;
- differential replay;
- dependency advisory refresh.

### 44.3 Release gate

- all PR/nightly gates;
- clean source archive;
- reproducible build comparison;
- SBOM/CBOM;
- signed provenance;
- full conformance corpus;
- formal theorem build;
- public replay bundle;
- independent security review disposition;
- claims registry and non-claims review;
- no pending critical CBC obligation.

---

## 45. Generated-code policy

Generated code is permitted only when:

- source schema/generator is versioned and reviewed;
- generator input and output are deterministic;
- generator runs offline for release;
- output includes a generated-file header;
- generated files are not manually edited;
- regeneration produces no diff;
- generated authority bytes have golden vectors;
- generator and templates are part of the source and build provenance;
- generated APIs follow the same documentation and type-safety rules.

Coding agents MUST NOT edit generated files to bypass the generator.

---

## 46. Agent implementation contract

The repository-level `AGENTS.md` is normative for coding agents. At minimum, an agent MUST:

1. read this specification, `AGENTS.md`, active RFCs/ADRs, and the CBC matrix;
2. identify affected disaster states and invariants before coding;
3. state the exact typed statement and authority boundary;
4. add or update negative tests before or with implementation;
5. make the smallest coherent change;
6. preserve dependency direction and crate boundaries;
7. avoid broad refactors unrelated to the task;
8. never weaken or delete tests merely to obtain green CI;
9. never treat local proof generation as production evidence;
10. update documentation, vectors, and the CBC matrix with honest status;
11. run the required narrow and full gates;
12. report commands, results, assumptions, and remaining gaps.

An agent cannot promote its own change to production authority. Critical code requires human review and governed release evidence.

---

## 47. BDD acceptance scenarios

### 47.1 Exact-once consumption

```gherkin
Feature: Exact-once resource consumption

  Rule: An active resource can be consumed only once

    Scenario: First valid consumption commits
      Given an active resource under the current machine policy
      And a transition with valid controller and logic proofs
      When the transition is prepared and atomically committed
      Then the resource is absent from the active set
      And its nullifier is present
      And the accepted journal binds the new state root

    Scenario: Replay is rejected without mutation
      Given the resource was already consumed
      When the same or a different transition tries to consume it again
      Then the transition is rejected as a spent resource
      And active resources, nullifiers, rewards, and state version are unchanged
```

### 47.2 Stale policy

```gherkin
Feature: Policy pinning

  Scenario: Stale policy cannot authorize a transition
    Given governance has activated policy P2
    And a transition is bound to prior policy P1
    When the transition is evaluated
    Then it is rejected with a stale-policy code
    And no verifier fact from P1 is treated as current authority
    And state remains unchanged
```

### 47.3 Unauthorized mint

```gherkin
Feature: Conserved accounting

  Scenario: Mint without authority rejects
    Given a conserved resource kind
    And a transition creates more atoms than it consumes
    When no current mint authority fact covers the delta
    Then accounting rejects
    And no output resource or reward is committed
```

### 47.4 Concurrent double spend

```gherkin
Feature: Concurrent commit safety

  Scenario: Two valid plans race to spend the same resource
    Given two plans were validated against the same pre-state
    When the first plan commits
    And the second plan attempts commit
    Then exactly one commit succeeds
    And the second fails its pre-state compare-and-swap
    And no partial writes from the second plan are visible
```

### 47.5 Wrong proof program

```gherkin
Feature: Verified fact authority

  Scenario: Valid proof from the wrong program rejects
    Given a cryptographically valid proof under program B
    And the resource logic requires program A
    When the verifier adapter evaluates the proof
    Then no VerifiedLogicFact is constructed
    And the semantic kernel cannot accept the proof artifact directly
```

### 47.6 DA non-overclaim

```gherkin
Feature: Data availability claims

  Scenario: Commitment without certificate does not imply availability
    Given a transition binds a data availability root
    And the active policy requires a verified availability certificate
    When no valid certificate is supplied
    Then the transition rejects or uses an explicitly weaker non-availability profile
    And no UI or journal claims retrievability
```

### 47.7 Proof-market reward replay

```gherkin
Feature: Exact-once proof rewards

  Scenario: Canonical proof reward pays once
    Given a funded proof task
    And a verifier-authenticated proof receipt
    When the completion transition commits
    Then one reward claim is created
    And the task and assignment are consumed

  Scenario: Duplicate proof cannot create another reward
    Given the task was already completed and rewarded
    When the proof receipt is submitted again
    Then the transition rejects or records unpaid duplicate evidence according to policy
    And no second reward claim is created
```

---

## 48. Formal obligations before v0.1 promotion

The following properties require executable evidence:

1. canonical encoding determinism;
2. strict decode rejects trailing and noncanonical bytes;
3. resource commitment binds every semantic field;
4. exact-once consumption;
5. output uniqueness including historical recreation protection;
6. reject-is-no-op;
7. accounting conservation;
8. transformation coverage soundness;
9. stale policy rejection;
10. proof statement role/ordinal binding;
11. concurrent double-spend safety under atomic commit;
12. deterministic journal derivation;
13. disjoint transition commutativity over bounded state;
14. semantic epoch root independence from proof-tree grouping;
15. proof-task reward exact-once.

At least exact-once, conservation, reject-is-no-op, and concurrency MUST have both runtime evidence and a bounded or deductive model.

---

## 49. Conformance levels

### ZRM-L0: Types and vectors

- typed schemas;
- canonical encoders;
- hash vectors;
- constructor rejection tests.

### ZRM-L1: Deterministic reference kernel

- accepted/rejected transition semantics;
- exact-once;
- accounting;
- reject-is-no-op;
- proof-independent execution.

### ZRM-L2: Verified-fact integration

- sealed verifier capabilities;
- signature or proof adapter;
- wrong-program/profile/policy negatives;
- replayable verification evidence.

### ZRM-L3: Durable machine

- atomic persistent commit;
- concurrency tests;
- crash recovery;
- replay state integrated with effects.

### ZRM-L4: Recursive proof integration

- authenticated ZRM journal leaf;
- semantic epoch root;
- recursive root proof;
- DA policy;
- root replay protection.

### ZRM-L5: Release-backed high assurance

- no pending critical CBC obligations;
- formal obligations satisfied;
- independent review;
- reproducible build and SLSA provenance;
- public replay;
- governed release and claims registry.

No level may be implied by a higher-level design document without evidence for every lower level.

---

## 50. Initial implementation roadmap

### Phase A — Repository and schemas

- workspace skeleton;
- primitive newtypes;
- manual canonical encoder;
- resource and policy constructors;
- diagnostic JSON wire types;
- golden vectors.

### Phase B — Reference state and kernel

- in-memory state;
- active/nullifier roots;
- prepare/commit pipeline;
- stable rejects;
- conservation and transformation engine;
- deterministic journal.

### Phase C — Assurance

- property tests;
- mutation suite;
- fuzz targets;
- Kani harnesses;
- bounded exact-once/conservation model;
- initial Lean theorem statements.

### Phase D — Proof Resource Machine

- task, budget, capacity, assignment, receipt, reward, timeout, and challenge resources;
- signature or local deterministic verifier adapter;
- BDD workflows;
- reward exact-once model.

### Phase E — Reference application adapters

- one bounded fungible-asset transfer or swap-style transition;
- one non-financial capability workflow;
- canonical resource mappings;
- accounting and authorized-transformation rows;
- differential tests against independently specified reference semantics;
- explicit non-claims for unsupported lifecycle surfaces.

### Phase F — Recursive proof and runtime integration

- ZRM journal leaf adapter;
- semantic epoch root;
- recursive proof;
- durable runtime admission;
- DA certificate;
- governed anchor adapter.

---

## 51. Promotion rule

A public implementation claim requires all of:

```text
Typed schemas exist
&& deterministic reference semantics exist
&& canonical vectors pass
&& negative tests cover named disaster states
&& critical mutants are killed
&& bounded/formal invariants pass
&& verifier adapters bind exact statements and policies
&& reject-is-no-op passes
&& release claims match evidence
```

A production-ready claim additionally requires:

```text
Durable atomic commit
&& concurrency/crash evidence
&& no pending critical CBC obligations
&& release provenance and reproducibility
&& public replay
&& independent review
&& governed policy and verifier roots
&& explicit DA and privacy posture
```

If any item is missing, documentation MUST state the narrower status.

---

## 52. References and standards basis

Normative and informative design inputs include:

- BCP 14: RFC 2119 and RFC 8174 for normative requirement language.
- Anoma Resource Machine specification for immutable resources, active-resource state, nullifiers, balance/compliance/resource-logic proof separation, and transparent versus shielded profiles.
- NIST SP 800-218 Secure Software Development Framework for secure-development lifecycle practices.
- NIST SP 800-218A as an informative AI-system development profile; agent-generated code remains untrusted until ordinary review and evidence gates pass.
- SLSA v1.2 source/build tracks, provenance, verification summaries, and verified properties.
- Reproducible Builds' bit-for-bit reproducibility definition and guidance on build paths, timestamps, locales, stable ordering, and environment capture.
- Rust API Guidelines for predictable, type-safe, dependable, debuggable, and future-compatible public APIs.
- Kani for bit-precise bounded model checking of Rust safety and custom correctness properties.
- Verus and Creusot for deductive functional verification of stable Rust kernels.
- Aeneas as a research path for translating supported safe Rust into theorem-prover backends.
- Miri for undefined-behavior detection on exercised Rust executions.
- Loom for deterministic exploration of concurrent executions.
- cargo-fuzz/libFuzzer for coverage-guided malformed-input testing.
- cargo-mutants for test-adequacy checks through mutation testing.
- OpenSSF Scorecard, dependency review, CodeQL/SAST, branch protection, and vulnerability-management practices as repository-security inputs.
- Public literature on recursive proof composition, verifier binding, proof profiles, and scoped claim discipline as high-assurance proof-boundary inputs.

This specification deliberately combines resource-machine semantics, capability-style authority, type-state construction, deterministic reference execution, formal methods, adversarial testing, recursive-proof separation, supply-chain provenance, and clean modular engineering. No single cited system establishes the complete ZRM design, and no reference transfers authority to an implementation without conformance evidence.
