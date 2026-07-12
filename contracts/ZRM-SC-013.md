# ZRM-SC-013 — Independent semantic review protocol

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

This contract creates **review evidence only**. It never creates protocol authority or substitutes for tests, formal proof, external audit, or accountable human release approval.

## Independence objective

The reviewer must derive what the component must do from the specification, threat model, and semantic contracts rather than from the implementation's abstractions or tests.

“Independent” is a property of information flow and incentives, not merely a second invocation of the same reviewer.

## Required roles

For Class C-E work, identify these roles explicitly:

| Role | Responsibility |
| --- | --- |
| **Specification owner** | Resolves normative ambiguity through the correct process; does not waive evidence. |
| **Implementer** | Writes production code and implementation-focused tests. |
| **Oracle reviewer** | Independently writes decision tables, reference semantics, vectors, and expected rejects before reading implementation rationale. |
| **Adversarial reviewer** | Inspects the completed design/code for substitutions, downgrades, replay, invalid states, and composition failures. |
| **Authority-boundary reviewer** | Required for D/E; reviews who can mint trusted types and how governance/release identity enters. |
| **Formal/evidence reviewer** | Checks proof/model assumptions, bounds, exclusions, and replayability. |
| **Release approver** | Accepts residual risk; cannot treat self-review as independent approval. |

One person may hold multiple roles only when the change class permits it and the loss of independence is recorded. The author cannot provide the required independent approval.

## Independence requirements

1. The oracle reviewer receives the normative specification, threat model, relevant contracts, and public interfaces first—not the implementation's internal rationale, private scratchpad, or implementation-authored tests.
2. Before detailed code inspection, the oracle reviewer produces:
   - accepted-state decision table;
   - invalid-state matrix;
   - counterexample list;
   - reference function/model or exact vectors where feasible;
   - ambiguous clauses and fail-closed interpretations.
3. Oracle artifacts are committed or content-addressed separately from production code and record author/tool/model/version provenance.
4. The implementation is then compared against the independent oracle. The oracle is not edited merely to match observed code; discrepancies are dispositioned as implementation defect, oracle defect, or specification ambiguity.
5. The adversarial reviewer begins from the authority map and disaster states, not from line coverage.
6. Re-running the same agent with the same prompt, context, scratchpad, implementation rationale, and tests is **corroboration**, not independent semantic review.
7. AI-assisted independence is strengthened by:
   - isolated contexts;
   - different role prompts;
   - no shared chain-of-thought or draft tests before the first oracle pass;
   - preferably a different model/provider or a human reviewer for the authority boundary;
   - explicit recording of correlated assumptions.
8. High coverage, mutation score, fuzz executions, formal proofs, and clean code do not compensate for a missing semantic oracle. Each answers a different question.
9. Reviewers search for both commission and omission: missing checks, missing fields, unrepresentable permissions, unsatisfiable policies, and authority granted by an identifier without content binding.
10. Composition receives a second review after components are integrated; local contract conformance does not prove end-to-end authority safety.

## Required review packet

Every Class C-E pull request contains or links:

```text
Change class:
Affected semantic contract IDs:
Normative specification clauses:
Authority newly created or changed:
Attacker-controlled inputs:
Governed/trusted inputs:
Derived values:
Accepted-state decision table:
Invalid-state/counterexample matrix:
Canonical/hash impact:
State/replay/atomicity impact:
Resource bounds:
Reference oracle/model:
Differential results:
Negative and mutation evidence:
Formal/model obligations and bounds:
Independent reviewer identity/provenance:
Disagreements and resolution:
Residual gaps and non-claims:
```

## Counterexample-first review

For each affected contract, the independent packet records attempted attacks in this form:

```text
Attempt:
Expected result and contract clause:
Observed result:
Evidence:
Disposition:
```

At minimum, reviewers attempt:

- same ID with different contents;
- correct content in wrong domain/version/role/ordinal;
- test or development downgrade;
- stale/revoked policy;
- missing, duplicate, extra, and reordered coverage;
- arithmetic boundary and overflow;
- active nonmembership but historical replay;
- rejection after partial mutation;
- concurrent conflicting plans;
- optional commitment present but unchecked;
- external row/policy/artifact substitution;
- log/diagnostic disclosure;
- component-correct but composition-invalid behavior.

## Approval rules

| Change class | Minimum semantic review |
| --- | --- |
| A | Normal documentation review; contract text cannot silently change semantics |
| B | Reviewer confirms no authority impact |
| C | One reviewer independent of the implementation, plus an independent oracle or counterexample packet |
| D | Two independent approvals, including an authority-boundary reviewer |
| E | Approved RFC/version plan, two independent approvals, formal/vector obligations, migration/replay analysis, and external review before production |

Branch protection SHOULD enforce required approvals and prevent the sole code owner or author from bypassing them.

## Review outcomes

The reviewer selects exactly one:

- `APPROVE`: contract obligations are satisfied for the claimed scope;
- `APPROVE_WITH_TRACKED_GAPS`: nonblocking gaps and non-claims are explicit;
- `REQUEST_CHANGES`: implementation or evidence is deficient;
- `BLOCK_AMBIGUOUS_SPEC`: normative behavior must be resolved before implementation;
- `BLOCK_UNSATISFIED_AUTHORITY_OBLIGATION`: a Class D/E boundary lacks required evidence.

## Required evidence

- separately authored oracle artifact;
- review provenance and information-flow declaration;
- counterexample log;
- implementation-to-contract traceability;
- discrepancy disposition;
- independent approval records;
- branch-protection/reviewer enforcement evidence for production profiles.

## Non-claims

Independent semantic review reduces correlated design and oracle errors; it does not prove the absence of all vulnerabilities.
