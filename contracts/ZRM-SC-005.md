# ZRM-SC-005 — Membership, freshness, and replay

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

Successful checks establish, relative to one authenticated pre-state and accumulator profile, that:

- consumed and referenced resources exist and are active;
- consumed resources and transition replay keys are fresh;
- created resources are new under the active and historical-recreation rules of the profile.

They do not establish authorization, conservation, or durable exclusion against a concurrent winner until atomic commit.

## Inputs

### Untrusted

- membership and nonmembership proofs;
- resource IDs, nullifiers, transition IDs, and claimed roots.

### Governed

- trusted pre-state root and version;
- active accumulator profile;
- active-resource and nullifier roots;
- current epoch and policy validity rules.

### Derived

- transparent nullifiers;
- membership/nonmembership results;
- replay footprint and conflict keys.

## Preconditions and invariants

1. Every consumed and referenced `ResourceId` verifies membership under the exact trusted active-resource root.
2. Every created `ResourceId` verifies active-set nonmembership.
3. Every consumed nullifier verifies nonmembership under the trusted nullifier root.
4. Under the v0.1 transparent profile, each created resource's deterministic nullifier also verifies historical nonmembership, preventing recreation of a previously consumed commitment.
5. Transition replay ID and any profile-defined authority nonce/replay key are absent before commit.
6. Membership proof format and verification are bound to the exact `AccumulatorProfileId`; proof formats are not inferred.
7. Resource and policy validity windows use `TrustedValidationContext.current_epoch`.
8. Membership and freshness checks are pure and do not reserve, insert, delete, or mutate state.
9. A concurrent race is resolved only by the atomic compare-and-swap and uniqueness checks at commit. Prevalidation alone never promises a spend will win.
10. A shielded profile cannot inherit the transparent profile's global historical-recreation claim without an equivalent committed mechanism.

## Required postconditions

- The prevalidated object records the exact root/profile against which each result was obtained.
- Any root/version/context change invalidates the result for commit.
- Failure is a state no-op.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| Membership proof valid for another root | Rejection |
| Proof valid under another accumulator profile | Rejection |
| Consumed nullifier already present | Rejection |
| Created resource absent from active set but historically consumed | Rejection in transparent v0.1 |
| Referenced resource expired | Rejection |
| Two concurrent plans spend the same resource | At most one commit winner |
| Prevalidation inserts a reservation/nullifier | Architectural review failure |
| Shielded profile claims historical exclusion without committed mechanism | Claim blocked |

## Required evidence

- membership/nonmembership root mutation tests;
- exact-once and historical-recreation property tests;
- two-plan concurrent commit test;
- bounded accumulator model;
- independent state-root vectors;
- profile-substitution negatives;
- explicit transparent/shielded non-claim tests and documentation.

## Non-claims

Prevalidation does not provide consensus ordering or durable exact-once behavior before commit.

## Specification anchors

Sections 9.1-9.4, 13.4, 23, 24.3, 28, and 29.
