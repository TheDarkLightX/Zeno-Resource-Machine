# ZRM Independent Semantic Review Packet

**Change or PR:**  
**Change class:** A / B / C / D / E  
**Affected contracts:** `ZRM-SC-___`  
**Normative specification/RFC version:**  
**Oracle reviewer:**  
**Adversarial reviewer:**  
**Authority-boundary reviewer:**  
**Review date:**  
**Packet digest:**  

> This packet records implementation-independent expected behavior and adversarial review evidence. It creates no protocol authority and does not replace conformance evidence, formal proof, or release approval.

---

## 1. Independence and information-flow declaration

```text
Materials received before the oracle pass:
Materials intentionally withheld before the oracle pass:
Prior involvement in the implementation:
Shared prompts, scratchpads, tests, or rationale:
Model/tool/provider and version, when AI-assisted:
Known correlated assumptions:
Why this review qualifies as independent, or why it is only corroborative:
```

The oracle pass should begin from the specification, threat model, relevant semantic contracts, and public interface. Implementation control flow, private rationale, and implementation-authored tests should be withheld until the initial oracle artifacts below are frozen or content-addressed.

## 2. Normative inputs

| Source | Version/digest | Clauses used | Ambiguities found |
| --- | --- | --- | --- |
| `SPECIFICATION.md` |  |  |  |
| Approved RFC/ADR |  |  |  |
| Semantic contract |  |  |  |
| Threat/CBC obligation |  |  |  |

For each ambiguity, record the fail-closed interpretation or block implementation pending specification resolution.

## 3. Authority map

```text
Untrusted source
  -> bounded/canonical boundary
  -> governed lookup or authentication boundary
  -> sealed capability
  -> pure semantic decision
  -> private commit plan
  -> atomic commit
  -> accepted result
```

### Authority created or changed

### Attacker-controlled inputs

### Governed or trusted inputs

### Derived values

### Trusted constructors and who owns them

### Authority that must remain unavailable

## 4. Accepted-state decision table

| Case | Preconditions | Governed policy/context | Expected success value | Contract clause |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 5. Invalid-state matrix

| Dimension | Invalid mutation/state | Expected reject or API impossibility | Precedence | Contract clause |
| --- | --- | --- | --- | --- |
| Identity/content | Same ID, different contents |  |  |  |
| Domain/version | Correct content, wrong domain/version |  |  |  |
| Lifecycle | Wrong role/ordinal or stage |  |  |  |
| Policy | Stale, revoked, predecessor misuse |  |  |  |
| Mode | Production-to-test/debug downgrade |  |  |  |
| Coverage | Missing, duplicate, extra, reordered |  |  |  |
| Arithmetic | Boundary, overflow, unit mismatch |  |  |  |
| Replay | Fresh active lookup but historical reuse |  |  |  |
| Atomicity | Failure after partial mutation |  |  |  |
| Concurrency | Two conflicting plans |  |  |  |
| Optional data | Nonempty but unchecked commitment |  |  |  |
| Diagnostics | Secret or full nonce disclosure |  |  |  |
| Composition | Locally valid parts, invalid composition |  |  |  |

## 6. Independent oracle or reference semantics

**Artifact path/digest:**  
**Language/tool:**  
**Why it is simpler than production:**  
**How it avoids copying production control flow:**  
**Input domain and bounds:**  
**Known exclusions:**  

Include one or more of:

- executable reference function;
- decision table;
- canonical vectors;
- state-machine model;
- formal property;
- counterexample generator.

## 7. Counterexample log

| Attempt | Expected result and clause | Observed result | Evidence | Disposition |
| --- | --- | --- | --- | --- |
| Same identifier with changed security-relevant content |  |  |  |  |
| Correct proof/content under wrong role, ordinal, domain, or version |  |  |  |  |
| Test/development downgrade |  |  |  |  |
| Stale/revoked policy |  |  |  |  |
| Missing/duplicate/extra/reordered coverage |  |  |  |  |
| Overflow or limit edge |  |  |  |  |
| Historical replay/recreation |  |  |  |  |
| Rejection after attempted mutation |  |  |  |  |
| Concurrent conflict |  |  |  |  |
| Caller-supplied row/policy/artifact substitution |  |  |  |  |
| Diagnostic disclosure |  |  |  |  |
| Composition failure |  |  |  |  |

## 8. Post-implementation comparison

```text
Implementation commit:
Oracle commit/digest frozen before comparison:
Differential-test command and result:
Unexpected implementation acceptances:
Unexpected implementation rejections:
Reject-precedence differences:
Performance/bounds differences:
```

A discrepancy must be classified as one of:

- implementation defect;
- oracle defect supported by the normative source;
- specification ambiguity requiring a block or RFC;
- explicitly accepted residual gap with no strengthened claim.

The oracle must not be edited solely because the implementation behaves differently.

## 9. Evidence review

- [ ] accepted and boundary tests
- [ ] negative/counterexample atlas
- [ ] independent vectors or reference model
- [ ] differential tests
- [ ] property/metamorphic tests
- [ ] fuzzing
- [ ] mutation evidence
- [ ] compile-fail/API sealing tests
- [ ] reject-is-no-op evidence
- [ ] concurrency/crash evidence, where applicable
- [ ] formal/model evidence with assumptions and bounds
- [ ] TCB, provenance, SBOM/CBOM, and release evidence, where applicable

## 10. Disagreements and resolution

| Issue | Reviewer position | Implementer position | Normative basis | Resolution |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 11. Residual gaps and non-claims

## 12. Review outcome

Select exactly one:

- [ ] `APPROVE`
- [ ] `APPROVE_WITH_TRACKED_GAPS`
- [ ] `REQUEST_CHANGES`
- [ ] `BLOCK_AMBIGUOUS_SPEC`
- [ ] `BLOCK_UNSATISFIED_AUTHORITY_OBLIGATION`

**Rationale:**  
**Required follow-up:**  
**Reviewer signature or authenticated approval reference:**  
