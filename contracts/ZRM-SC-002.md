# ZRM-SC-002 — Resource and resource-kind policy

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

Successful construction may create a policy-valid `ResourceV1` for a specific machine, domain, application, logical epoch, and governed resource-kind policy.

It does not establish that the resource is active, unspent, authorized for a transition role, or durably committed.

## Inputs

### Untrusted

- canonical `ResourceWireV1` or policy-independent intrinsic resource candidate;
- quantity, unit, logic IDs, roots, nonce, creation/expiry epochs, and flags;
- echoed resource-kind policy ID or root.

### Governed

- `TrustedValidationContext`;
- active `MachinePolicyV1`;
- exact resource-kind policy resolved from an authenticated policy set;
- current creation-policy mapping and accepted predecessor set;
- allowed logic/profile/transformation/controller/authority roots.

### Derived

- `ResourceId`;
- transparent-profile `Nullifier`;
- resource live/expired status;
- policy-relative validation result.

## Preconditions and invariants

1. All intrinsic resource invariants hold: supported schema, required nonzero IDs/roots/nonce, valid expiry relation, and no unknown v1 flags.
2. Resource machine, domain, and application equal the parent transition and trusted validation context.
3. The resource-kind policy is resolved from governed state. The resource's echoed policy ID cannot supply the policy contents.
4. Policy identity must bind the complete canonical policy content once the policy codec is frozen. Until then, candidate policy objects remain non-authoritative.
5. Unit equals the resource-kind policy unit exactly.
6. Quantity does not exceed `quantity_max`.
7. **Operational v1 fail-closed rule:** quantity zero is forbidden for every accounting mode because `ResourceKindPolicyV1` has no explicit zero-marker permission field. A future zero-quantity marker requires a versioned policy field and approved compatibility rules.
8. `LifecycleNonFungible` resources have quantity exactly `1`; their policy constructor requires `quantity_max == 1`.
9. `ConservedFungible` does not permit authorized mint or burn.
10. `AuthorityMintableFungible` mint/burn effects require exact authenticated authority coverage.
11. `Transformable` unmatched deltas require an allowed transformation rule.
12. `EvidenceOnly` cannot be treated as fungible value merely because a numeric field exists; its profile must define the bounded semantic use of quantity or require the neutral value chosen by the approved specification.
13. Resource logic ID and logic profile are members of the policy-authorized sets.
14. The resource-kind policy is live at `current_epoch`.
15. Consumed and referenced resources may use a still-authorized predecessor policy; created resources use exactly the current creation policy.
16. A created resource has `created_epoch == current_epoch`; a consumed or referenced resource has `created_epoch <= current_epoch` and is not expired.
17. Policy constructors reject internally incoherent or unsatisfiable combinations rather than creating “valid policy objects” no resource can satisfy.

## Required postconditions

- The resulting type privately binds the resource body, derived ID, exact governed policy identity, and validation epoch.
- No downstream caller can swap the policy contents while retaining the validated-resource type.
- Failure creates no policy-valid resource and is a state no-op.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| Quantity `0` under any current v1 accounting mode | Rejection |
| `LifecycleNonFungible` with resource quantity other than `1` | Rejection |
| `LifecycleNonFungible` policy with `quantity_max = 0` or `> 1` | Policy-construction rejection |
| Correct policy ID copied onto different policy contents | Registry/content-binding rejection |
| Accepted predecessor policy used to create a new resource | Rejection |
| Unit differs by one byte | Rejection |
| Logic ID allowed but profile ID not allowed | Rejection |
| Expired resource referenced read-only | Rejection |
| Nonzero v1 flag | Rejection |
| Caller-provided “validated=true” or accounting-mode label | No authority |

## Required evidence

- independent decision table across accounting modes;
- exhaustive boundary tests for `0`, `1`, `quantity_max`, and overflow-adjacent values;
- policy-constructor coherence tests;
- predecessor-read/current-create matrix;
- one-field policy and resource mutation tests;
- differential reference model;
- compile-fail test for private validated-resource construction.

## Non-claims

A policy-valid resource is not necessarily active, unspent, controllable by the proposer, or accepted into state.

## Specification anchors

Sections 9.1, 13, 14, 15, 15.1, and 18.1.
