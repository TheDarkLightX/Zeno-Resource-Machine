# ZRM-SC-003 — Trusted validation context and machine policy

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

A sealed `TrustedValidationContext` authorizes the semantic kernel to treat one exact epoch, pre-state, state version, policy root, crypto suite, accumulator profile, and ordering context as current for one validation attempt.

An authenticated `MachinePolicyV1` authorizes only the profiles, policies, limits, and admission mode committed by that policy.

## Inputs

### Untrusted

- request-echoed epoch, policy root, state root/version, profile IDs, and ordering root;
- serialized `ValidationContextV1`;
- wall-clock time or adapter metadata not authenticated by the ordering profile.

### Governed

- committed machine state;
- authenticated ordering/epoch source;
- active machine policy and governance state;
- protocol ceilings.

### Derived

- `ValidationContextHash`;
- effective policy limits;
- current admission rule;
- stale/current plan status.

## Preconditions and invariants

1. Untrusted bytes cannot deserialize directly into `TrustedValidationContext`.
2. The runtime authenticates the context from committed state and ordering policy, then constructs the sealed capability.
3. The transition's machine, domain, epoch, pre-state root, policy root, crypto suite, accumulator profile, ordering root, and execution-context root exactly match the capability.
4. `statement.execution_context_root == ValidationContextHash`.
5. Wall-clock time has no semantic authority. Any timestamp/height/epoch mapping is profile-defined and authenticated.
6. Machine policy and selected child policies are active at `current_epoch`.
7. The proposer may echo the policy identity but cannot choose the expected policy.
8. Policy limits may tighten protocol ceilings but never exceed them.
9. One machine policy uses one exact verifier cost model for every summed verifier budget.
10. `LocalKernel` requires an absent admission verifier policy ID and rejects any admission fact.
11. `RequiredVerifier` requires one exact active production admission policy and never falls back to `LocalKernel`.
12. Policy activation is external to `TransitionStatementV1`; activation atomically changes policy root and state version and invalidates plans built on the prior tuple.
13. Policy activation preserves every predecessor policy still required to consume or reference live resources, or explicitly rejects activation as unsafe.
14. The capability is private-field, non-deserializable, and not caller-forgeable. Cloning is avoided unless the clone preserves one immutable authority token with no widening of scope.

## Required postconditions

- Every semantic time and policy decision is traceable to one authenticated context.
- Any epoch, policy, profile, or ordering change makes an old commit plan stale.
- Failure creates no trusted context or policy authority and mutates no state.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| Proposer selects a convenient epoch | Rejection |
| Statement policy root is stale but structurally valid | Rejection |
| `RequiredVerifier` backend unavailable | Rejection; no local fallback |
| Policy limit exceeds compile-time ceiling | Policy-construction rejection |
| Different cost model used by one child verifier | Rejection |
| Same machine state but ordering context advanced | Old plan rejected as stale |
| Serialized bytes converted directly to trusted capability | API/compile-time impossibility |
| Policy update strands a still-live predecessor resource | Activation rejection or explicitly governed migration; never silent |

## Required evidence

- capability-forgery compile-fail tests;
- exact context equality mutation matrix;
- policy ceiling boundary tests;
- admission-mode consistency tests;
- stale-policy, stale-epoch, and stale-ordering tests;
- policy activation model showing atomic root/version update and predecessor safety;
- explicit non-claim for rollback/migration behavior not yet specified.

## Non-claims

The context authenticates the runtime's selected state and ordering view; it does not prove consensus finality, wall-clock truth, or the correctness of external governance.

## Specification anchors

Sections 5.1, 9.7, 15, 15.1, 16.4, 24, and 28.2.
