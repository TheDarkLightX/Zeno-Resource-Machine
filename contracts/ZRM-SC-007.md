# ZRM-SC-007 — Verifier cost model and dispatch budget

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

A successful governed cost plan authorizes the registry to attempt the exact bounded verifier dispatch set without exceeding the machine-policy budget.

It does not prove wall-clock limits, backend availability, or successful verification.

## Inputs

### Untrusted

- artifact lengths and bytes;
- caller-supplied cost rows or coefficients;
- claimed backend family or produced-output size.

### Governed

- one canonical verifier cost model selected by machine policy;
- exact canonical sorted unique row set;
- exact verifier policies and their maxima;
- machine total budget.

### Derived

- row hashes and `rows_root`;
- `VerifierCostModelId`;
- per-dispatch charge;
- complete ordered cost plan;
- admission reservation and total planned units.

## Preconditions and invariants

1. Cost rows are canonical, sorted by `BackendFamilyId`, unique, and cover every authorized backend family.
2. `rows_root` is derived from the exact row hashes; `VerifierCostModelId` binds schema version, `rows_root`, and `max_charge_units`.
3. The governed model owns or authenticates its rows. The quote API accepts a backend/policy/request, not an externally supplied coefficient row.
4. Row lookup selects exactly the row committed by the active model for the verifier policy's backend family.
5. Verifier policy cost-model ID equals machine policy cost-model ID.
6. Artifact, public-input, and public-output bounds are checked before charge computation and dispatch.
7. Charge is:

   ```text
   base
   + artifact_byte_units * exact_artifact_len
   + statement_byte_units * exact_canonical_statement_len
   + reserved_output_byte_units * verifier_policy.max_public_output_bytes
   ```

8. Every multiplication and addition uses checked `u128` intermediates; the result fits `u64`.
9. Each charge is at most both model and verifier-policy maxima.
10. The registry constructs and sums the complete canonical dispatch plan before invoking any transition-fact verifier.
11. Dispatch order is fixed by fact class, then canonical claim order.
12. `RequiredVerifier` reserves the policy-bounded worst-case admission charge before first-phase dispatch. Actual admission charge cannot exceed the stored reservation.
13. Planned total is fixed for the request even if a verifier rejects; failure does not refund, reorder, or recompute authority.
14. Total, including reservation, is at most the machine-policy total budget.
15. Zero coefficients are authoritative only if they occur in the exact governed row; a caller cannot substitute them.
16. Cost units are deterministic audit units and documented worst-case bounds, not claims of equal wall-clock cost across hardware.

## Required postconditions

`AuthenticatedFacts` and then `CommitPlan` privately carry the exact plan total, ordered dispatch identities, and admission reservation. No later phase can increase them.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| Caller supplies same backend ID with cheaper coefficients | API impossibility or authenticated-row mismatch |
| Duplicate backend rows | Model-construction rejection |
| Row content changed without changing model ID | Hash/root mismatch rejection |
| Missing row for authorized backend | Policy/model rejection |
| Arithmetic overflow | Rejection before dispatch |
| Per-verifier charge below model cap but above verifier cap | Rejection |
| Total exceeds machine cap | Rejection before any verifier runs |
| Actual admission charge exceeds reservation | Admission rejection |
| Failed proof causes budget to be recomputed lower | Forbidden |
| Backend-produced short output lowers reserved charge | Forbidden; policy maximum is used |

## Required evidence

- independent row/root/model-ID vectors;
- cheap-row substitution regression;
- duplicate/missing/unsorted row tests;
- boundary and overflow tests;
- full dispatch ordering and total vectors;
- invalid-artifact tests confirming planned charge remains fixed;
- admission reservation/actual-charge tests;
- documented backend worst-case evidence and explicit wall-clock non-claim.

## Non-claims

The budget controls deterministic admitted verification work; it does not replace rate limiting or prove latency.

## Specification anchors

Sections 15, 24.4, 24.7, and 30.1.
