# Kimi K3 external review of RFC-0005

**Date:** 2026-07-16

**Status:** Non-authority external AI review evidence

**Reviewed revision:** `bf136a19739ad19cdfcc7a533d67740d4e3fc286`

**Packet SHA-256:** `18f343a01e8308f83e49a555b9a74dd3afce1a73a59cd18c3bbc0497c16da5ca`

**Requested model:** `moonshotai/kimi-k3`

**Returned model:** `moonshotai/kimi-k3`

**Actual OpenRouter cost:** USD 0.799011
**Usage:** 140,462 prompt; 25,175 completion; 22,442 reasoning; 165,637 total tokens

The full packet contained `AGENTS.md`, `SPECIFICATION.md`,
`CONFORMANCE_MATRIX.json`, `IMPLEMENTATION_PLAN.md`, RFC-0001, RFC-0004,
RFC-0005, and the RFC-0005 design worklog. Source lines were numbered before
submission. The conservative preflight estimate was USD 2.705832 under a USD
3.00 cap.

A preceding practice review used `openrouter/free`, which routed to
`nvidia/nemotron-3-nano-30b-a3b:free`, reported zero cost, and demonstrated
the request, response, receipt, and artifact path before the paid request.

This review does not approve RFC-0005, promote CBC status, or fill either
independent human Class E reviewer slot.

---

# Independent Class E Review — RFC-0005 (Paired Transient Resource Lifecycle)

**Reviewer scope:** semantics **and** authority boundary. This is non-authority
advice; it cannot approve the RFC or promote CBC status.

## 1. Verdict: **REVISE**

The core design (four placements, dual uses, unique producer/consumer, dual
gross projection, durable transient nullifier) is internally coherent and its
non-claims are mostly honest. It is not approvable as written: there is one
internal normative contradiction, several undefined committed-list orderings,
an undefined journal-field scope, an undefined policy-mixture rule, and an
undefined graph term — each capable of producing divergent conforming
implementations. These are fixable specification defects, not fatal design
flaws, so reject is unwarranted.

## 2. Blocking findings

### B1 — Normative contradiction: graph checks vs. verifier dispatch order

The BDD rule requires an all-transient component to "reject before verifier
dispatch" (RFC-0005:212-218). The reject taxonomy orders `logic-use shape and
exact fact binding` **before** `graph same-identity multiplicity, anchoring,
and cycle checks` (RFC-0005:995-997). Sealed-fact binding requires verifier
dispatch (SPECIFICATION.md:751-755, 789-804). An implementer must violate one of
the two normative statements. This also breaks deterministic reject precedence
(SPECIFICATION.md:909-910) and lets a structurally-invalid-but-well-proved
request burn the entire planned verifier-cost plan before rejection.
Structural graph validation needs only canonical claim descriptors and must be
pinned as pre-dispatch; sealed-fact binding is post-dispatch. The taxonomy must
be split accordingly.

### B2 — Canonical order undefined for new committed lists

RFC-0005 defines sort order only for placement lists (RFC-0005:223-224). It
does not define:

- the `LogicClaimV2` sort key (RFC-0005:632-659); the V1 key
  (SPECIFICATION.md:248-252) cannot be reused because `resource_role` is
  replaced by `resource_use`, and birth/death claims for one `q` share
  `(resource_id, resource_logic_id, logic_profile_id)`;
- the `TransformationResourceUseV2` input/output list order
  (RFC-0005:328-354);
- the `transient_nullifiers_root` element order (RFC-0005:726-731).

These orders determine `logic_claims_root`,
`input/output_resource_uses_root`, and journal bytes. They are logical
semantics (SPECIFICATION.md:228-279), not byte-table detail, and cannot be
wholly deferred to the canonical packet (RFC-0005:628-630).

### B3 — `consumed_nullifiers_root` scope under V2 undefined

The journal section scopes only `created_resources_root` to `O`
(RFC-0005:733) and adds `transient_nullifiers_root` (RFC-0005:726-731), but
never restates whether the inherited `consumed_nullifiers_root`
(SPECIFICATION.md:945) commits `nf(C)` or `nf(C ∪ Q)` given
`nullifier_inserts = nf(C) ∪ nf(Q)` (RFC-0005:437-444). Both readings are
defensible; they yield different journal bytes and different
`JournalDraftHash` for identical transitions, so an admission fact under one
reading rejects the other's draft. Every V1-inherited journal field's V2 scope
must be restated.

### B4 — Policy-schema mixture inside a V2 transition undefined

Transients require `ResourceKindPolicyV2` with `transient_use` and the
current creation policy (RFC-0005:303-321); activation allows existing V1
resources to participate without byte rewrite (RFC-0005:111-124). The RFC never
states whether `C`/`R`/`O` roles under `MachinePolicyV2` may resolve
against V1 kind policies, nor which policy schema authorizes persistent
creation under V2. This is authority semantics, not encoding. CBC-062's
required evidence (CONFORMANCE_MATRIX.json:2671-2676) contains no such mixture
matrix.

### B5 — "Connected component" undefined

Anchoring (RFC-0005:374-387) depends on component semantics. Under strong
connectivity, an acyclic digraph's components are singletons and the anchoring
rule is vacuous; only weak connectivity matches the stated intent and examples.
Different readings produce different accept/reject verdicts for the same
claims.

### B6 — TransitionIdV2 must remain a hard approval condition

The RFC honestly declines to freeze `TransitionIdV2` (RFC-0005:486-491,
782-785), but the Decision section (RFC-0005:528-550) does not restate that any
semantic approval is void of transition-identity and replay-finality claims
until the canonical packet and cross-version vectors exist. Make that
condition explicit in the Decision text.

## 3. Strongest counterexample

### Validly proved, well-formed, all-transient cycle (B1 weaponized)

A proposer submits a V2 transition whose claims are canonical, whose birth/death
logic and transformation artifacts are cryptographically valid (for example,
producer P births `q` under a legitimately authorized mint, consumer X deaths
`q`, component has no persistent boundary input or output), under a
`RequiredVerifier` policy.

- Under the BDD rule (RFC-0005:212-218), the request rejects **before any
  verifier dispatch**.
- Under the taxonomy (RFC-0005:995-997), the registry must first dispatch all
  `2|Q|` logic verifications and the transformation verifications, charging
  the full pre-planned cost, construct sealed facts, and only then reach graph
  checks and reject.

Two implementations faithful to different sections of the same RFC return
different reject-code families (structure/graph vs. post-authentication),
violating SPECIFICATION.md:909-910, and the taxonomy-faithful implementation
lets an attacker repeatedly burn the maximum planned verifier budget with
requests that were knowably invalid at zero verifier cost. The RFC cannot be
implemented as written without choosing which of its own normative statements
to break.

Runner-up (B3): implementation A commits
`consumed_nullifiers_root = ListRoot(nf(C))`; implementation B commits
`ListRoot(nf(C ∪ Q))`. Same transition, two journal hashes,
cross-implementation admission failure — a consensus-class split from one
unstated field scope.

## 4. Exact recommended revisions

1. **B1:** Rewrite the taxonomy as: policy and current-creation permission;
   logic-use shape (structural); transformation-use roots and
   producer/consumer coverage (structural); graph multiplicity, anchoring, and
   cycle (structural, pre-dispatch); verifier dispatch and exact sealed-fact
   binding; accounting and authority coverage; final state and journal
   derivation; admission and atomic commit. Add a named test asserting an
   unanchored/cyclic component with valid proofs rejects with zero verifier
   invocations and a stable reject code.
2. **B2:** Specify `LogicClaimV2` sorted by `(resource_use, resource_id,
   resource_logic_id, logic_profile_id, logic_claim_hash)`;
   `TransformationResourceUseV2` lists sorted by `(resource_id, logic_use)`
   with pairwise uniqueness rejecting duplicates; transient nullifiers sorted
   ascending.
3. **B3:** Restate every inherited journal field's V2 scope:
   `consumed_nullifiers_root = nf(C)`; `transient_nullifiers_root = nf(Q)`;
   `post_nullifier_root` commits `N ∪ nf(C) ∪ nf(Q)`;
   consumed/referenced/created roots scoped to `C`/`R`/`O`; and
   `verifier_set_root` includes the `2|Q|` birth/death fact policies.
4. **B4:** Add a policy-schema-mixture subsection stating exactly which
   kind-policy schemas may validate each role under `MachinePolicyV2`, and
   require `MachinePolicyV2` support roots to commit both kind-policy schema
   IDs. Add the mixture matrix to CBC-062 required evidence.
5. **B5:** Define a component as the **weakly** connected component of the
   undirected projection of the claim graph; add a connectivity-flip mutant to
   CBC-059.
6. **B6:** Amend the Decision section to state unconditionally that semantic
   approval confers no transition-identity, replay-finality, or V1/V2
   noncollision claim until `TransitionIdV2` derivation and cross-version
   vectors are approved.
7. Weaken the RFC-0004 fixture promise: coverage entries bind the row-level
   `transformation_set_root` but do **not** attribute per-transient quantity
   provenance.
8. Condition the UX goal: one user confirmation and one commit; authorization
   count depends on involved controller policies; `RequiredVerifier`
   admission adds a second adapter-orchestrated protocol phase. Fix BDD wording
   so roots commit B's `ResourceId`; the witness opens it.
9. CBC additions: CBC-056 evidence += journal-field scoping vectors and V1/V2
   policy-mixture matrix; CBC-059 evidence += pre-dispatch graph-precedence
   test; new formal obligations `GraphChecksPrecedeVerifierDispatch` and
   `V2JournalFieldScopingExact`.

## 5. Non-blocking improvements

- Name an accountable author for a Class E RFC.
- Clarify that a dust referenced resource satisfies anchoring; the real spam
  defense is count/nullifier budgets.
- Require transient `expiry_epoch` absent, or justify retaining an
  unobservable field.
- Restate that per-claim mint/burn rows respect each kind's
  `accounting_mode`.
- Add a named two-birth/zero-death corpus case.
- State that the V2 profile defines logic-fact cardinality per placement,
  amending the V1 default of one.
- Require both fixtures to map controller/authority facts, substantiating or
  retracting the one-authorization claim.
- Keep explicit that AI reviews do not count toward the two independent human
  Class E reviewers.
- State that maximum transient chain length derives from
  `max_transformation_claims`, or add an explicit bound.

## 6. Residual non-claims

No `TransitionIdV2`/cross-version noncollision; no selected numeric limits; no
frozen V2 bytes, domains, sort keys, or reject codes; no privacy, shielding, or
unlinkability; no ARM membership-optional equivalence; no fixture-validated
user value; no per-transient accounting-provenance granularity from RFC-0004
coverage; no recursive V2 support; no RFC-0001-coordinated journal successor;
no migration/rollback implementation; no durable, concurrency, or crash
evidence. Matrix non-claims must remain until evidence lands.

## 7. Review scope

**Both** semantics and authority boundary.
