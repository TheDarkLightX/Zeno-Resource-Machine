# Zeno Resource Machine (ZRM)

**Author:** Dana Edwards

**Drafting assistance:** GPT-5.6

**A proof-system-neutral semantic kernel for exact-once, proof-carrying resource transitions.**

> **Status: incubation / pre-alpha.** The protocol, schemas, APIs, and security model are not stable. No production-readiness, privacy, consensus, token-value, physical-resource, or safety-critical claim is made.

Machine-readable release posture:

```text
public_implementation_claim_allowed = true
claim_scope = reviewed initial repository-local WP0 controls and WP1 canonical-codec slice
merged_but_unpromoted_candidate_scope = WP2 policy model, WP0 assurance extensions, WP3a structural resource roles, WP3b intrinsic resource construction, WP3c intrinsic-body role and ordinal binding, and WP5 bounded artifact input boundary
unapproved_design_scope = Class E semantic-closure RFC package
production_ready = false
current_level = ZRM-L0
```

## Implementation scope

The repository contains a maintainer-reviewed, merged pre-alpha implementation of the initial repository-local WP0 controls and WP1 canonical-codec slice:

- the reviewed WP1 set of opaque nonzero primitive identifier and digest types;
- the closed, schema-fixed SHA-256 reference suite;
- strict bounded `ResourceWireV1` encoding and decoding;
- stable decoder reject codes and deterministic precedence;
- exact absent-expiry and present-expiry bytes, preimages, and hashes;
- independent Python vector generation and replay;
- malformed-input regressions, property-style field sensitivity tests, fuzzing, bounded Kani harnesses, Miri, coverage, and mutation testing;
- pinned CI, dependency policy, conformance, architecture, and repository-hygiene checks.

The current branch also contains an unreviewed pre-RFC WP2 candidate for specialized opaque root types, private-field in-memory policy values, protocol ceilings, exact unit checks, admission-mode consistency, validity windows, and checked verifier-cost quotes. This candidate deliberately defines no policy codec, policy hash, root derivation, trusted validation context, verifier registry, backend dispatch, or verified authority fact. Canonical policy bytes, roots, and hashes remain blocked on a Class E RFC and independent vectors.

The repository includes locally replayed candidate WP0 controls for multi-axis code quality and deterministic source/cryptography inventories. Their recorded local gates and the merged default-branch hosted CI pass. They remain unpromoted assurance evidence and do not create release provenance, third-party trust, standardized BOM conformance, or production authority.

The merged WP3a boundary contains the bounded CBC-003 structural role partition. It checks consumed, referenced, and created counts before internal allocation; sorts each role by `ResourceId`; rejects within-role duplicates and all three collision pairs in deterministic order; and derives zero-based ordinals from the canonical lists. The partition remains inert and establishes no membership, transition validity, list root, state change, or commit authority.

WP3b adds a sealed `IntrinsicResourceV1` stage. It rejects zero identifiers, roots, and nonce, expiry before creation, and every nonzero v1 flag; preserves exact quantity and epoch widths; and derives its own `ResourceId` from the complete existing canonical wire value. The type fixes the v1 field set but proves no strict-decoder provenance. It establishes only policy-independent body consistency and body-to-ID binding.

The merged but unpromoted WP3c candidate composes those stages into `RoleBoundIntrinsicResourceV1`. The sole binding operation looks up the intrinsic body's internally derived `ResourceId` in the supplied sealed canonical partition and stores the exact resulting role and ordinal. A caller cannot inject a mismatched identifier, role, or ordinal independently of that partition. The partition itself remains caller-proposed and unauthenticated. Absence rejects without changing either input. Separation of different bodies relies on the schema-fixed SHA-256 resource-ID derivation and its collision-resistance assumption; concrete mutation tests do not prove hash injectivity. The revision-bound local evidence index records the exhaustive small atlas, ordinal ceiling, coverage, generated and manual mutation, Kani, targeted Miri, fuzz, quality, and supply-chain results. Hosted CI passed on the merged default branch. The repository does not contain an independent human Class C approval record for WP3c, so that review status remains unclaimed. This per-resource result proves neither complete body coverage of the partition nor policy, state, logic, transition, or commit authority.

The WP5 candidate adds only `BoundedArtifactV1`, an owned copy of untrusted verifier bytes under a caller-supplied limit that cannot exceed the protocol ceiling. The type deliberately has no `Debug` implementation and creates no verified fact. Passing its constructor proves no policy selection, proof format, canonicality, program identity, statement binding, cryptographic verification, or authority. A future governed verifier registry must recheck the retained length against authenticated machine and verifier policies before dispatch.

`ResourceWireV1` remains an inert syntactic candidate, and neither `IntrinsicResourceV1` nor `RoleBoundIntrinsicResourceV1` is a final policy-valid resource. The current policy schema cannot express the specification's explicit permission for zero-quantity marker resources, so these stages preserve zero as unresolved data. The repository does not yet implement final `ResourceV1`, authenticated policy activation, a complete semantic transition kernel, authenticated facts, state membership, persistence, atomic commit, proof adapters, application adapters, or a production release. Host-side branch, vulnerability-reporting, and release-environment controls remain incomplete. There is no stable package-wide ABI, external security audit, or production-readiness claim. Detailed status and remaining evidence are machine-readable in [`CONFORMANCE_MATRIX.json`](CONFORMANCE_MATRIX.json).

The current documentation branch also contains two unapproved Class E semantic-closure RFCs covering policy suspension, authority-context freshness, acyclic semantic-effect commitment, linearizable retry classification, uncertain commit outcomes, and serialized recursive journal composition. They change no implemented Rust authority and require independent semantic review before approval. See [`rfcs/README.md`](rfcs/README.md) and the [`semantic-closure review package`](formal/state-machine/semantic_closure_v1/README.md).

> **zkVMs prove that code ran. ZRM defines what the result is allowed to change.**

Zeno Resource Machine models digital assets, rights, capabilities, evidence, computation, model checkpoints, proof tasks, publication authority, storage commitments, and other scarce or replay-sensitive objects as **typed resources**.

A transition consumes or references active resources and creates new resources. It is accepted only when resource existence, freshness, controller authority, resource logic, unit compatibility, conservation or authorized transformation, policy bindings, and public commitments all verify.

ZRM is designed to run with a deterministic local verifier, a zkVM, a specialized ZKML prover, a formal verifier, or multiple independently governed proof backends. The semantic core does not depend on one chain, one proof system, one database, or one application.

---

## Core law

```text
Anyone may propose a resource transition.
Only a transition whose semantics and authority verify may commit.
```

More precisely:

```text
ResourceTransitionAccepted
  -> ConsumedResourcesExist
  && ReferencedResourcesExist
  && NullifiersAreFresh
  && CreatedResourcesAreUnique
  && ResourceLogicsVerify
  && ControllerAuthorityVerifies
  && UnitsAreCompatible
  && ConservationOrTransformationIsAuthorized
  && PolicyIsCurrent
  && PublicBindingsMatch
  && CommitIsAtomic
```

Proposers may supply transitions, witnesses, schedules, and proof artifacts. They do not decide what is trusted. Typed constructors, semantic validation, governed verifier adapters, formal models, and release gates do.

---

## Why ZRM?

Modern zkVMs can prove that a committed program executed correctly. ZKML systems can prove that a committed model performed a particular inference, evaluation, or bounded training computation. Recursive proof systems can compress many proofs into one root proof.

A proof of computation alone does not answer:

- Did the consumed asset, capability, checkpoint, or evidence object exist?
- Had it already been consumed?
- Was the caller authorized to use it?
- Were quantities conserved or explicitly transformed under an allowed rule?
- Was the verifier and policy version current?
- Which new resources became canonical?
- Was a reward paid exactly once?
- Did rejection leave committed state unchanged?

ZRM provides that semantic layer.

---

## What is a resource?

A resource is an immutable, typed commitment representing something that can be created, controlled, transformed, consumed, or referenced under explicit rules.

Examples include:

- a token balance, position, escrow, or settlement receipt;
- a proof task, prover assignment, bond, capacity reservation, or reward claim;
- a model checkpoint, model delta, evaluation receipt, or dataset-use capability;
- a claim, evidence artifact, challenge, or bounty;
- a publication grant, revocation right, storage lease, or provenance record;
- an oracle report, reporter bond, or quorum certificate.

A resource is not necessarily money, fungible, transferable, public, or tied to a blockchain.

ZRM primarily verifies **digital state and digital attestations**. A claim about physical energy, hardware location, legal rights, sensor readings, or real-world events requires an external trust root such as a signed meter, hardware attestation, oracle network, legal credential, or challenge mechanism. ZRM can verify that a policy used those attestations correctly; it cannot manufacture truth about the physical world.

---

## State-transition model

The logical machine state contains at least:

```text
MachineState {
  active_resource_root
  nullifier_root
  policy_root
  state_version
}
```

Expiry and policy windows are checked against a sealed `TrustedValidationContext` supplied by the runtime from authenticated ordering/state data. A proposer-provided epoch has no authority.

A proposed transition contains consumed resources, referenced resources, created resources, resource-logic claims, transformation authorities, and public commitments:

```text
TransitionStatementV1 {
  machine_id
  domain_id
  application_id
  epoch
  machine_policy_root
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
}
```

`TransitionId` is derived from the canonical `TransitionStatementV1` hash. It is never authoritative caller input. Full resource bodies, claim descriptors, membership proofs, and proof artifacts travel in a bounded witness envelope and must reproduce every committed root.

If `C` is the consumed set and `O` is the created set, an accepted transition updates active resources as:

```text
A_(t+1) = (A_t - C) union O
```

and inserts every consumed resource nullifier into the nullifier accumulator.

A rejected transition is a no-op:

```text
reject(transition, state) -> state' = state
```

### Conservation and authorized transformation

For a conserved resource kind:

```text
consumed + authorized_mint = created + authorized_burn
```

For transformations across unlike kinds, a versioned transformation rule must authorize the change. For example:

```text
ModelCheckpoint(v)
+ DatasetUseCapability
+ ComputeCredit
+ TrainingSpecification
    ->
ModelCheckpoint(v+1)
+ EvaluationReceipt
+ ResidualComputeCredit
```

The transformation rule—not a host assertion—defines which outputs are authorized by which inputs.

---

## Architecture

```text
Application intent
      |
      v
Application-specific resource adapter
      |
      v
Proposed ResourceTransition
      |
      +-----------------------------+
      |                             |
      v                             v
Deterministic/formal logic       zkVM/ZKML/proof verifier
      |                             |
      +-------------+---------------+
                    v
          Authenticated logic facts
                    |
                    v
             ZRM semantic kernel
  existence | freshness | authority | units | conservation
                    |
                    v
        CommitPlan + JournalDraft
                    |
        policy-selected admission proof
                    v
          atomic runtime commit
                    |
                    v
            AcceptedJournal
                    |
          optional postcommit aggregation
                    v
        consensus / external anchor
```

### Separation of responsibilities

| Layer | Responsibility |
| --- | --- |
| **ZRM** | Defines whether a resource transition is semantically valid. |
| **Proof adapters** | Authenticate signatures, zkVM receipts, ZKML proofs, formal-verifier outputs, and external attestations. |
| **Recursive proof fabric** | Authenticates a journal draft for admission or aggregates accepted journals after commit under an explicitly distinct profile. |
| **Proof market** | Assigns proving work, capacity, bonds, redundancy, deadlines, and rewards. |
| **Ledger or runtime** | Orders transitions and commits state, replay protection, and rewards atomically. |
| **Consensus or anchor** | Establishes canonical history, governed policy, checkpointing, or hard finality. |
| **Application adapters** | Define domain-specific resources, transformations, and resource logics. |

The dependency direction remains inward: the ZRM core must not depend on any product runtime, proof backend, chain, network client, database, wall clock, or randomness source.

---

## Design principles

1. **Proof-system neutral.** The semantic kernel must run without a zkVM and must not depend on one proof backend.
2. **Typed before proved.** Resources, statements, policies, journals, rejects, and authority facts are defined before proof code.
3. **Make invalid states unrepresentable.** Raw bytes, decoded values, validated objects, authenticated facts, commit plans, and committed results are distinct types.
4. **Canonical and bounded.** Consensus-relevant bytes, roots, counts, nesting, and schemas have explicit encodings and resource limits.
5. **Exact once by construction.** Consumption, assignment, rewards, and replay keys represented in committed ZRM state are explicit machine-state properties.
6. **Authority is explicit.** Mint, burn, transformation, revocation, and reward effects require versioned authority.
7. **Provers propose; verifiers decide.** Caller-provided booleans and metadata never create authority.
8. **Reject is no-op.** Parsing, authentication, semantic validation, and conflict checks complete before atomic commit.
9. **Application semantics stay in adapters.** The core contains no financial, ML, publishing, scientific, or market-specific policy.
10. **Non-claims are first-class.** A profile must state what it does not establish.
11. **Proof topology is not semantic identity.** Different valid proof trees over the same canonical transitions should bind the same semantic epoch identity.
12. **Correctness precedes deduplication.** DRY never justifies merging semantically different rules behind an abstraction that is harder to audit.

Exact-once guarantees cover effects inside the atomic ZRM machine write set. External delivery requires an outbox and an idempotent receiver, or an explicit at-least-once profile.

### Construction Boundary Conformance

ZRM uses **Construction Boundary Conformance (CBC)** identifiers for its machine-readable assurance obligations. Each `ZRM-CBC-*` entry names a disaster state, the construction rule that prevents or detects it, the evidence required for promotion, and the claim that remains unavailable. A specified CBC entry records a design obligation. It does not record an implemented or verified result.

In this repository, **CBC** always means **Construction Boundary Conformance**. The broader engineering approach commonly called **correct by construction** is abbreviated **CbC** when an abbreviation is needed. The distinction avoids treating an assurance obligation identifier as a correctness claim.

---

## Initial reference application: Proof Resource Machine

The first reference application models proof production itself:

```text
RewardEscrow
+ ProofTask
+ ProverCapacity
+ ProverBond
    ->
ProofAssignment
    ->
VerifiedProofReceiptResource
+ RewardClaim
+ ResidualCapacity
```

This provides an objective, exact-once state machine for proof tasks, assignments, retries, challenges, and rewards.

A second reference adapter should exercise a materially different domain, such as a bounded asset transfer, capability workflow, or evidence lifecycle. ZRM is not considered application-neutral until the same core cleanly supports at least two distinct domains without importing domain-specific assumptions.

---

## What ZRM is not

ZRM is not, by itself:

- a blockchain or consensus protocol;
- a recursive proof system;
- a zero-knowledge privacy system;
- a data-availability network;
- an oracle of real-world truth;
- proof that physical compute or energy was consumed;
- a token or promise of token value;
- a universal truth machine;
- a production-ready financial or safety-critical ledger.

**Verifiable does not mean private.** Privacy requires separate profiles, disclosure rules, an adversary model, and analysis of timing, size, retrieval, and network metadata.

---

## Initial scope: v0.1

The first release target is deliberately narrow:

- canonical resource identifiers and commitments;
- active-resource and nullifier state roots;
- exact-once consumption;
- typed quantities and unit identifiers;
- same-kind conservation;
- explicit authorized transformations;
- deterministic transition validation;
- typed and stable rejection reasons;
- reject-is-no-op;
- canonical accepted journals and typed reject receipts;
- cross-language golden vectors;
- one bounded formal model;
- one proof-resource reference adapter;
- one materially different reference adapter.

Not included in v0.1:

- privacy;
- recursion;
- consensus or networking;
- production token settlement;
- generalized auctions;
- physical-resource attestation;
- arbitrary application logic.

---

## Repository documents

- [`SPECIFICATION.md`](SPECIFICATION.md) — normative protocol and implementation specification.
- [`AGENTS.md`](AGENTS.md) — mandatory contract for human and automated coding agents.
- [`CONFORMANCE_MATRIX.json`](CONFORMANCE_MATRIX.json) — machine-readable obligation and evidence matrix.
- [`QUALITY_GATES.md`](QUALITY_GATES.md) — CI, formal, fuzzing, mutation, and release gates.
- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) — ordered work packages and dependencies.
- [`SECURITY.md`](SECURITY.md) — security posture and disclosure policy.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — change classes, review requirements, and contribution workflow.
- [`REVIEW_CHECKLIST.md`](REVIEW_CHECKLIST.md) — high-assurance review checklist.
- [`rfcs/README.md`](rfcs/README.md) — draft protocol and authority RFC index.
- [`formal/state-machine/semantic_closure_v1/README.md`](formal/state-machine/semantic_closure_v1/README.md) — draft semantic decisions, review oracles, and refinement obligations.
- [`templates/RFC_TEMPLATE.md`](templates/RFC_TEMPLATE.md) — protocol and architecture proposal template.
- [`templates/ADR_TEMPLATE.md`](templates/ADR_TEMPLATE.md) — architectural decision record template.
- [`templates/AGENT_WORKLOG_TEMPLATE.md`](templates/AGENT_WORKLOG_TEMPLATE.md) — agent evidence report template.
- [`templates/PR_TEMPLATE.md`](templates/PR_TEMPLATE.md) — pull-request evidence template.
- [`PACKAGE_MANIFEST.json`](PACKAGE_MANIFEST.json) — package sizes and SHA-256 payload digests.
- [`LICENSE`](LICENSE) — MIT license for the repository and specification package.

Repository quality is evaluated as independent gates for complexity, code smells, authority-relevant antipatterns, and design-choice evidence. The automated `excellent-candidate` label is structural only. Design mechanics use AI review; human review receives a behavior-and-evidence summary covering specification obligations, exact assurance results, gaps, and non-claims. Existing preferred-budget advisories are visible under a no-increase ratchet until they are removed.

---

## Correctness posture

The intended assurance stack is:

```text
specification
  -> deterministic reference semantics
  -> canonical test vectors
  -> property and differential tests
  -> mutation and fuzz testing
  -> bounded model checking
  -> deductive or theorem-prover evidence
  -> proof-system adapters
  -> recursive aggregation
  -> governed release provenance
  -> atomic runtime admission
```

A generated proof is never sufficient by itself. Consumers must verify it against the expected program, statement, journal, policy, verifier parameters, and release identity before using it as authority.

---

## Related work and attribution

ZRM does not claim to have invented the resource-machine paradigm. It is an independent project informed by prior work on resource machines, intent-centric systems, capability security, proof-carrying state, zkVMs, ZKML, formal verification, and recursive proofs.

Useful background:

- [Anoma Resource Machine specification, version 1.0.0](https://specs.anoma.net/v1.0.0/arch/system/state/resource_machine/index.html)
- [Anoma ARM RISC Zero implementation](https://github.com/anoma/arm-risc0)
- [Introducing the ARM](https://anoma.net/blog/introducing-the-arm)
- [ZKML: Verifiable Machine Learning Using Zero-Knowledge Proofs](https://kudelskisecurity.com/modern-ciso-blog/zkml-verifiable-machine-learning-using-zero-knowledge-proof)
- [Principled Design and Analysis of Zero-Knowledge Protocols for Intent-Centric Private State Machines](https://medium.com/@gwrx2005/principled-design-and-analysis-of-zero-knowledge-protocols-for-intent-centric-private-state-99632c60a898)
- [Machine-Verifiable Proof Generation](https://www.emergentmind.com/topics/machine-verifiable-proof-generation), a secondary discovery index whose underlying papers should be cited for technical claims.

ZRM is not affiliated with the authors or organizations behind the linked materials.

---

## Contributing

This project is specification-first. Before adding a feature:

1. Define the resource and transition semantics.
2. Name the disaster states and authority boundaries.
3. Add accepted and rejected golden vectors.
4. Add deterministic reference behavior.
5. Add property, mutation, fuzz, concurrency, or formal evidence appropriate to the risk.
6. Only then add a proof adapter or optimization.

Changes to canonical bytes, hashes, nullifiers, units, transition authority, state roots, or journal meaning require a version bump or an explicit compatibility proof and migration plan.

Until a stable release and security review exist, do not use ZRM to control production funds, legal rights, model-training authority, physical resources, or safety-critical systems.
