# ZRM Semantic Contract Template

**Contract ID:** `ZRM-SC-___`  
**Title:**  
**Version:**  
**Status:** Draft / Specified / Implemented partial / Verified partial / Blocked  
**Minimum change class:** A / B / C / D / E  
**Normative source:** `SPECIFICATION.md` sections; approved RFCs  
**Owner:**  
**Independent oracle reviewer:**  
**Authority-boundary reviewer:**  

> This contract is a derived review oracle. It MUST NOT broaden the behavior permitted by `SPECIFICATION.md` or an approved RFC.

---

## 1. Authority granted

State the exact conclusion or trusted capability downstream code may rely upon after success.

Also state what success does **not** establish.

## 2. Boundary

### Untrusted inputs

List every field, byte stream, object, artifact, proof, signature, identifier, root, count, time value, callback, or metadata value the adversary may influence.

### Governed/trusted inputs

List the exact authenticated state, policy, registry, release, context, or runtime capability that supplies authority.

### Derived values

List every value that MUST be recomputed rather than trusted from the caller.

## 3. Preconditions

Number every required condition. Include:

- identity/domain/version equality;
- canonicality;
- policy activity and freshness;
- count/byte/depth limits;
- membership or nonmembership;
- exact verifier/program/release bindings;
- arithmetic and unit constraints;
- required coverage;
- state/context snapshot bindings.

## 4. Invariants

State what must remain true through every successful path and every failure path.

Prefer equations, decision tables, and closed enums over prose where possible.

## 5. Required postconditions

On success:

- what trusted type is constructed;
- exactly which fields and evidence it binds;
- what later operation it may authorize.

On failure:

- which trusted types are unavailable;
- required no-op behavior;
- stable error/reject class.

## 6. Forbidden states and mandatory counterexamples

| Counterexample | Expected result | Contract clause | Evidence reference |
| --- | --- | --- | --- |
|  |  |  |  |

Include at least:

- same ID with changed contents;
- wrong domain/version/role/ordinal;
- stale or revoked policy;
- debug/test downgrade;
- missing/duplicate/extra/reordered data;
- arithmetic boundary/overflow;
- replay/historical recreation;
- partial mutation;
- concurrent conflict;
- unchecked optional commitment;
- diagnostic disclosure;
- composition failure.

## 7. Deterministic failure behavior

Define:

- reject/error stage and precedence;
- whether multiple checks may run in parallel;
- how the same input/state produces the same public result;
- what private diagnostics may be retained;
- why failure is a committed-state and external-effect no-op.

## 8. Resource bounds and complexity

Record:

- raw byte ceiling;
- list/count ceilings;
- nesting/depth ceiling;
- verifier/cycle/cost ceiling;
- storage-write ceiling;
- algorithmic complexity;
- allocation timing;
- timeout/failure posture.

## 9. Independent oracle

Describe the implementation-independent expected-behavior artifact:

- small reference function/model;
- decision table;
- canonical vectors;
- state-machine model;
- formal property;
- counterexample generator.

Record separate provenance and explain how it avoids copying production control flow.

## 10. Required evidence

- [ ] accepted cases
- [ ] boundary cases
- [ ] negative/counterexample atlas
- [ ] independent vectors or oracle
- [ ] differential tests
- [ ] property/metamorphic tests
- [ ] fuzzing
- [ ] mutation coverage
- [ ] compile-fail/API sealing tests
- [ ] Kani/SMT/Lean/Verus/TLA+ obligation, where applicable
- [ ] reject-is-no-op evidence
- [ ] concurrency/crash evidence, where applicable
- [ ] TCB/provenance update, where applicable
- [ ] independent review record

## 11. Non-claims and residual risk

State assumptions, exclusions, boundedness, unimplemented profiles, and claims that remain unavailable.

## 12. Traceability

### Specification

- `SPECIFICATION.md#...`
- RFC/ADR:

### Implementation

- module/API:

### Tests and vectors

- test/vector:

### Formal/model evidence

- model/proof:

### Conformance/CBC

- `ZRM-CBC-...`

## 13. Independent review record

```text
Reviewer:
Role:
Information received before oracle pass:
Implementation rationale/tests withheld:
Oracle artifact and digest:
Counterexamples attempted:
Disagreements:
Resolution:
Residual gaps:
Outcome:
```

Allowed outcomes:

- `APPROVE`
- `APPROVE_WITH_TRACKED_GAPS`
- `REQUEST_CHANGES`
- `BLOCK_AMBIGUOUS_SPEC`
- `BLOCK_UNSATISFIED_AUTHORITY_OBLIGATION`
