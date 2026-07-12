# Contributing to Zeno Resource Machine

ZRM is specification-first and high assurance. Small, reviewable, evidence-backed changes are preferred over broad feature delivery.

## Before contributing

Read:

1. `README.md`;
2. `SPECIFICATION.md`;
3. `AGENTS.md`;
4. `QUALITY_GATES.md`;
5. `CONFORMANCE_MATRIX.json`;
6. relevant RFCs, ADRs, threat models, modules, and tests.

Do not infer the protocol from a task title or README alone.

## Change classes

Classify the change before coding:

- **A — Documentation:** non-normative prose, comments, diagrams.
- **B — Tooling:** diagnostics or tooling that cannot authorize state.
- **C — Semantic:** types, codec, policy, state, accounting, journals.
- **D — Stable authority implementation:** verifier, signatures, proof adapters, persistence, concurrency, and rewards under an unchanged authority ABI.
- **E — Protocol/authority breaking:** canonical bytes, hashes, nullifiers, state roots, authority identity/semantics/ABI, public ABI, or release profile.

Classes C-E require an issue or change proposal. Class E requires an RFC and migration/compatibility plan before implementation.

## Required change proposal

A proposal states:

```text
Problem
Current behavior
Desired behavior
Non-goals
Affected invariants
Affected disaster states
Authority boundary
Data and privacy changes
Canonical ABI changes
Resource/cost bounds
Alternatives considered
Test plan
Formal/model plan
Migration/rollback plan
Claim and non-claim changes
```

## Development workflow

1. Reproduce or specify the current behavior.
2. Add a failing invariant, BDD, property, mutation, fuzz, or model test.
3. Define or update typed inputs, outputs, rejects, and authority facts.
4. Implement the smallest coherent change.
5. Run narrow tests continuously.
6. Run all required gates for the change class.
7. Update vectors, docs, CBC status, and evidence.
8. Self-review the complete diff.
9. Request the required human reviewers.

## Architecture requirements

- The semantic core remains pure and deterministic.
- Adapters depend on core; core never depends on applications, proof systems, databases, networks, clocks, or RNGs.
- Wire types, validated types, authenticated facts, commit plans, and committed results are distinct.
- Caller-supplied booleans never create authority.
- Rejection is a no-op.
- Effects and replay protection commit atomically.
- Domain-specific semantics stay in adapters.

## Code quality

Apply SOLID in an idiomatic Rust form:

- one reason to change per module/function;
- extend through versioned policies and adapters, not edits to unrelated core logic;
- trait implementations obey documented laws and conformance tests;
- capability traits are small;
- dependency inversion points inward.

Apply DRY carefully. Duplicate five obvious lines rather than create one opaque abstraction that merges semantically different authority rules. Deduplicate only when invariant, failure behavior, units, and versioning are genuinely shared.

Critical code preferred limits and review triggers:

| Metric | Preferred | Review trigger |
| --- | ---: | ---: |
| critical function logical lines | <= 40 | > 60 |
| cyclomatic complexity | <= 8 | > 12 |
| cognitive complexity | <= 10 | > 15 |
| nesting depth | <= 3 | > 4 |
| positional parameters | <= 4 | > 6 |
| public trait methods | <= 7 | > 10 |
| critical module logical lines | <= 400 | > 700 |

In addition:

- no `unsafe` in core;
- no `unwrap`, `expect`, panic, unchecked indexing, lossy casts, or floating point in semantic paths.

Exceptions require an explicit review rationale.

Quality is evaluated as separate gates for complexity, code smells, authority-relevant antipatterns, and design-choice evidence. Coverage or cleanliness in one dimension cannot offset a blocking result in another. For Class C-E work, AI review records the design forces, the selected pattern or `no additional pattern`, invalid states prevented, extension-point or closed-set reasoning, rejected alternatives, pattern-specific failure modes, enforcement, and tests. Human review packets report specified behaviors, exact assurance results, CBC coverage, residual gaps, and non-claims. Ask for human semantic direction only when the specification is ambiguous or a proposed behavior would change it.

## Tests

Each semantic rule needs:

- accepted case;
- boundary case;
- reject case;
- reject-is-no-op assertion;
- mutation that removes/inverts the rule;
- property test where a family of inputs exists;
- fuzz target for untrusted grammar;
- formal/model evidence if the invariant is mathematical or concurrent.

BDD is for actor-visible behavior. Hashing, arithmetic, codecs, and canonicalization use invariant, property, differential, fuzz, and formal tests.

## Dependencies

A new dependency requires:

- purpose and alternatives;
- direct and transitive TCB delta;
- license;
- maintenance and advisory status;
- unsafe/native/build-script/proc-macro review;
- minimal feature set;
- version policy;
- removal plan.

Do not add a dependency solely to avoid writing a small auditable function.

## Generated and AI-assisted contributions

Generated or AI-assisted code is treated as untrusted contribution material. The contributor is responsible for:

- understanding every line;
- verifying licensing/provenance;
- providing the change plan and evidence;
- ensuring no tests or claims were weakened;
- disclosing uncertainty;
- obtaining human review.

Do not commit chat transcripts, hidden prompts, private project names, local absolute paths, or confidential repository context.

## Pull request contents

A pull request includes:

- summary and motivation;
- change class;
- invariant/disaster-state mapping;
- exact authority boundary;
- tests and gates run with results;
- canonical vector or ABI impact;
- dependency impact;
- performance/resource impact;
- formal/model status;
- migration and rollback;
- remaining gaps and non-claims.

Keep unrelated refactors separate.

## Review requirements

| Class | Minimum review |
| --- | --- |
| A | one maintainer |
| B | one maintainer or domain owner |
| C | at least one non-author semantic reviewer + independent test/evidence review |
| D | two distinct non-author reviewers, including authority-boundary reviewer |
| E | approved RFC, two distinct non-author reviewers, formal/compatibility review, release-owner sign-off |

An author or coding agent cannot be the sole approver of its own critical change.
Every Class C-E review includes a specification-counterexample pass authored
independently of the implementation. The pass derives adversarial cases from
the normative requirements and disaster states, rather than only reading the
tests that accompany the patch.

## Commit and history policy

- commits should be reviewable and intentional;
- generated artifacts should be separate from hand-written semantic changes where practical;
- do not rewrite published release tags;
- canonical ABI changes name the version in the commit/PR;
- security fixes may use a private fork until coordinated disclosure.

## Definition of done

A contribution is complete only when requirements, implementation, tests, formal/model evidence, docs, vectors, matrix status, and claims all agree.
