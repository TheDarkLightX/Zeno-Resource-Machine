# ZRM Semantic Contract Suite

**Version:** 0.1.0-draft.1  
**Date:** 2026-07-12  
**Status:** Derived review oracle for the pre-alpha design  
**Applies to:** Class C-E ZRM changes and every authority-bearing implementation path

> **This document is not a second protocol specification.** `SPECIFICATION.md`, together with approved RFCs that amend it, remains the single normative source of ZRM semantics. These contracts restate that source as implementation-independent review obligations, counterexamples, and evidence requirements. If a contract and the specification appear to conflict, implementation MUST fail closed and the conflict MUST be resolved through the repository's change-class process before code is promoted.

> **A contract being written does not mean it is implemented, verified, audited, or production-ready.** Contract status records what reviewers must check; conformance status remains in `CONFORMANCE_MATRIX.json`.

---

## 0. Purpose

The contract suite exists to prevent a common assurance failure:

```text
implementation behavior
  -> implementation-authored tests
  -> high coverage
  -> mistaken confidence that the intended semantics were implemented
```

ZRM instead requires:

```text
specification and threat model
  -> implementation-independent semantic contract
  -> independently authored oracle/counterexamples
  -> implementation
  -> differential, negative, and formal evidence
  -> independent approval
```

A semantic contract defines the authority created by a component, the exact inputs allowed to influence that authority, the invariants and forbidden states, rejection behavior, and the evidence needed to show conformance.

---

## 1. Authority and precedence

### 1.1 Source hierarchy

The source hierarchy is:

1. `SPECIFICATION.md` and approved RFCs that explicitly amend it;
2. versioned semantic contracts derived from those sources;
3. canonical vectors and independently authored reference models;
4. production implementation;
5. implementation-authored tests and comments.

A lower layer MUST NOT broaden the accepted state space of a higher layer.

### 1.2 Ambiguity rule

When the specification does not determine a successful behavior:

- the implementation MUST reject or leave the capability unavailable;
- the contract MUST mark the point `UNRESOLVED`;
- accepting a new behavior requires the appropriate RFC, versioning, replay, and migration analysis;
- a test, comment, work log, or existing implementation does not resolve the ambiguity.

A fail-closed contract refinement may narrow an unimplemented candidate behavior, but it MUST NOT silently change frozen canonical bytes, hashes, public authority identity, or an already promoted protocol behavior.

### 1.3 Contract conformance is not authority

A Markdown file, checklist, review report, test result, proof artifact, or agent assertion cannot itself create ZRM authority. Authority is created only by the types and runtime boundaries named in the active protocol profile.

---

## 2. Contract vocabulary

| Term | Meaning |
| --- | --- |
| **Untrusted input** | Data an adversary may choose, alter, omit, duplicate, reorder, replay, or make expensive. |
| **Governed input** | Data selected through authenticated policy or release governance, not by the request being evaluated. |
| **Trusted capability** | A non-serializable, non-forgeable in-process value constructed only by its owning authority boundary. |
| **Derived value** | A value recomputed from canonical inputs; a caller-supplied copy has no authority. |
| **Authority granted** | The exact new conclusion downstream code may rely upon after successful construction. |
| **Forbidden state** | A state the public API must make unrepresentable or deterministically reject. |
| **Counterexample** | A concrete mutation or adversarial case that must fail for a stated reason. |
| **No-op rejection** | Failure leaves committed machine state and external effects unchanged. |
| **Coverage** | A one-to-one or otherwise policy-defined relation between committed claims and authenticated facts. |
| **Independent oracle** | Expected behavior derived from the specification and contract without inheriting the implementation's control flow or assumptions. |

---

## 3. Contract registry

| Contract | Boundary | Minimum change class | Principal authority |
| --- | --- | ---: | --- |
| `ZRM-SC-001` | Canonical data and derived identities | C; E if ABI/hash changes | Canonical typed object or identifier |
| `ZRM-SC-002` | Resource and resource-kind policy | C | Policy-valid `ResourceV1` |
| `ZRM-SC-003` | Trusted validation context and machine policy | D; E for policy identity/schema | Current authenticated validation authority |
| `ZRM-SC-004` | Transition structure, witness, roles, and roots | C; E for canonical schema | `PrevalidatedTransition` structure |
| `ZRM-SC-005` | Membership, freshness, and replay | C/D | Pre-state existence and exact-once evidence |
| `ZRM-SC-006` | Governed verifier registry and sealed facts | D | `Verified*Fact` capability |
| `ZRM-SC-007` | Verifier cost model and dispatch budget | D; E for cost identity/schema | Permission to dispatch bounded verification |
| `ZRM-SC-008` | Claim semantics and exact fact coverage | C/D | Authenticated claim set |
| `ZRM-SC-009` | Accounting and authorized transformation | C | Conserved or explicitly authorized state delta |
| `ZRM-SC-010` | Pure semantic kernel, finalization, and commit plan | C/D | `CommitPlan` plus `JournalDraft` |
| `ZRM-SC-011` | Admission, atomic commit, journals, and rejection | D/E | `CommittedTransition` and `AcceptedJournal` |
| `ZRM-SC-012` | Policy governance, versioning, and release claims | D/E | Activation or revocation of governed authority |
| `ZRM-SC-013` | Independent semantic review | Process gate | Review evidence; never protocol authority |

Every Class C-E pull request MUST list the affected contract IDs. “No contract impact” requires reviewer justification.

---

## 3.1 Contract documents

- [`ZRM-SC-001`](contracts/ZRM-SC-001.md) — Canonical data and derived identities
- [`ZRM-SC-002`](contracts/ZRM-SC-002.md) — Resource and resource-kind policy
- [`ZRM-SC-003`](contracts/ZRM-SC-003.md) — Trusted validation context and machine policy
- [`ZRM-SC-004`](contracts/ZRM-SC-004.md) — Transition structure, witness, roles, and roots
- [`ZRM-SC-005`](contracts/ZRM-SC-005.md) — Membership, freshness, and replay
- [`ZRM-SC-006`](contracts/ZRM-SC-006.md) — Governed verifier registry and sealed facts
- [`ZRM-SC-007`](contracts/ZRM-SC-007.md) — Verifier cost model and dispatch budget
- [`ZRM-SC-008`](contracts/ZRM-SC-008.md) — Claim semantics and exact authenticated-fact coverage
- [`ZRM-SC-009`](contracts/ZRM-SC-009.md) — Accounting and authorized transformation
- [`ZRM-SC-010`](contracts/ZRM-SC-010.md) — Pure semantic kernel, finalization, and commit plan
- [`ZRM-SC-011`](contracts/ZRM-SC-011.md) — Admission, atomic commit, journals, and rejection
- [`ZRM-SC-012`](contracts/ZRM-SC-012.md) — Policy governance, versioning, and release claims
- [`ZRM-SC-013`](contracts/ZRM-SC-013.md) — Independent semantic review protocol

---

## 4. Contract-to-code traceability

Each authority-bearing public item SHOULD document:

```text
Semantic contract:
Authority granted:
Untrusted inputs:
Governed inputs:
Derived values:
Preconditions:
Postconditions:
Stable errors:
Side effects:
Complexity and bounds:
Non-claims:
```

Each test, vector, model, and finding SHOULD name the contract clause it exercises. Contract IDs are stable; clause headings may evolve within a draft until frozen.

---

## 5. Initial audit-derived blockers

The first contract application records these blockers before authority integration:

1. **Zero-quantity ambiguity:** current v1 has no explicit marker permission; `ZRM-SC-002` therefore forbids zero until a versioned permission exists.
2. **Lifecycle policy coherence:** `LifecycleNonFungible` requires `quantity_max == 1`.
3. **Cost-row substitution:** `ZRM-SC-007` requires internal authenticated row lookup; caller-supplied rows cannot enter the authoritative quote path.
4. **Verifier-policy substitution:** `ZRM-SC-006` requires content-bound, registry-resolved policies; copied IDs cannot authorize changed contents.
5. **Raw canonical-byte hashing:** `ZRM-SC-001` requires a sealed canonical-byte provenance path.
6. **Opaque-value diagnostics:** `ZRM-SC-001` requires redacted default diagnostics.

These entries are review obligations, not evidence that remediation exists.

---

## 6. Adoption rule

Before the next Class C-E implementation package:

1. list the affected contract IDs;
2. create the independent oracle/counterexample packet;
3. resolve every `UNRESOLVED` behavior or fail closed;
4. map code and tests to contract clauses;
5. obtain the required independent review;
6. update `CONFORMANCE_MATRIX.json` only from replayable evidence.
