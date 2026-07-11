# WP0 multi-axis code-quality and assurance-remediation work log

**Date:** 2026-07-11
**Change classes:** Class B non-authority tooling; Class C behavior-preserving Rust refactors

## Goal and authority boundary

Extend the code-quality gate beyond line counts. Measure complexity, high-confidence code smells, authority-relevant antipatterns, test-evidence hazards, and completeness of technical design decisions as independent axes. Remove all existing preferred-budget debt without suppressions or exceptions.

The tooling is repository evidence only. It cannot construct a policy, verified fact, transition, commit plan, journal, or accepted state. Its reports grant no protocol authority and do not prove semantic correctness or production readiness.

## Behavior requirements

The implemented gate must:

- fail closed on malformed source, ambiguous JSON, missing references, path escape, symlinked policy input, empty source discovery, or source-overwrite attempts;
- bind each finding to its exact source digest, rule, path, line, and item;
- scan Rust production, integration-test, fuzz, benchmark, example, and build-script roles for lexical hazards;
- keep production complexity and all-role smell results as separate axes;
- reject boolean authority controls, boolean authority fields, stringly identities, primitive identities outside wire candidates, public validated fields, broad suppression, vague critical names, manager objects, wildcard imports, unordered hash collections, floating point, implicit fallback, suspicious `Default`, wall-clock access, verification-bypass features, and unguarded success-only tests;
- require technical AI-review evidence for design decisions, including the `no additional pattern` alternative;
- use no compensating scalar score;
- reserve human review for specification behavior and assurance evidence, not syntax or pattern mechanics;
- reach `excellent-candidate` only with zero active findings, zero complexity warnings, zero review triggers, and zero exception debt.

## Technical design review

- **Forces:** deterministic standard-library-only tooling, strong fail-closed input handling, low false-positive risk, and exact source binding.
- **Pattern selected:** separate lexical analysis, policy validation, and reporting modules; no additional framework.
- **Invalid states prevented:** ambiguous policy JSON, stale approvals, source-hidden findings, public authority state, nondeterministic primitives, and vacuous success-only tests.
- **Alternatives rejected:** a weighted score, mandatory pattern counts, broad clone detection, and adding a parser framework to the tooling TCB.
- **Failure modes:** lexical analysis cannot expand macros or prove semantic responsibility; compiler-backed Clippy remains the type-aware lane.
- **AI-review status:** complete through focused adversarial audit, two independent subagent reviews, and repository replay. The optional external peer-review helper produced no output before timeout and supplies no evidence.

## Rust remediation scope

The first report found five preferred-budget advisories and the audit found vacuous assurance paths. The remediation:

- decomposed the ordered policy-limit validator by invariant family while preserving all sixteen ceiling checks and final resource-wire minimum in exact order;
- made successful policy and cost fixtures fail closed through a typed test error and `?`;
- bound diagnostics to exact strings and a 64-byte ceiling;
- made Kani quote-success paths explicitly reachable and nonvacuous;
- split cost production, unit tests, and Kani harnesses into cohesive modules;
- split primitive types, quantities, resource flags, and reject taxonomy into cohesive private modules with unchanged root re-exports;
- simplified the resource decoder without changing field order or reject precedence;
- denied Clippy cognitive complexity at the workspace level;
- removed every preferred complexity warning without adding an exception or lint suppression.

No public Rust signature, protocol byte, hash, domain, vector, reject code, policy bound, or accepted/rejected behavior intentionally changed.

## Files

Quality tooling and policy:

- `tools/rust_complexity.py`
- `tools/check_complexity.py`
- `tools/complexity_exceptions.json`
- `tools/rust_quality.py`
- `tools/check_code_quality.py`
- `tools/design_pattern_decisions.json`
- `tools/tests/test_complexity.py`
- `tools/tests/test_code_quality.py`
- `.github/workflows/ci.yml`
- `Cargo.toml`

Behavior-preserving Rust refactors:

- `crates/zrm-codec/src/resource_wire_v1.rs`
- `crates/zrm-policy/src/limits.rs`
- `crates/zrm-policy/src/cost.rs`
- `crates/zrm-policy/src/cost/tests.rs`
- `crates/zrm-policy/src/cost/kani_harnesses.rs`
- `crates/zrm-policy/tests/policy_model.rs`
- `crates/zrm-types/src/lib.rs`
- `crates/zrm-types/src/opaque.rs`
- `crates/zrm-types/src/quantity.rs`
- `crates/zrm-types/src/resource_flags.rs`
- `crates/zrm-types/src/reject.rs`

Public quality contract and evidence references were updated in `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `QUALITY_GATES.md`, `REVIEW_CHECKLIST.md`, the work/PR templates, the conformance matrix, and the derived package manifest.

## Exact assurance results

| Evidence | Result |
| --- | --- |
| Complexity report | 22 production files, 192 functions, **0 warnings**, **0 review triggers**, **0 exceptions** |
| Code-quality report | `excellent-candidate`; 27 Rust files across production/test/fuzz roles; 16 rules; 5 AI-reviewed decisions; **0 findings**; advisory ceiling **0/0** |
| Python policy tests | 73 passed across BOM, quality, complexity, conformance, coverage, architecture, and workflow-pin fixtures |
| Rust tests | 70 passed, 0 failed |
| Strict Clippy | workspace/all targets/all features passed, including denied cognitive complexity |
| Workspace coverage | lines **98.48%**, branches **98.94%** |
| `zrm-policy` coverage | lines **99.70%**, branches **100.00%** |
| Mutation | 302 tested: **239 caught**, 63 unviable, **0 missed**, **0 timeouts** |
| Kani 0.60.0 | **8/8** harnesses verified, 0 failures; both cost covers reached |
| Miri | all **70** Rust tests passed; four zero-test doc suites passed |
| Independent vectors | 6 binary artifacts and 4 protocol digests replayed exactly |
| Fuzz | both targets replayed seeds and completed 10-second campaigns without crash or timeout |
| Formatting/diff | `cargo fmt --check` and `git diff --check` passed |
| Architecture/conformance | exact dependency allowlists and all 45 obligation records passed validation |
| External AI peer helper | no output before timeout; **unavailable**, not a pass |

Kani retained its existing target-feature, future-incompatibility, and unsupported-construct warnings. Kani reports that verification would fail if unsupported constructs were reachable; all eight selected harnesses completed successfully. The bounded results do not establish general program correctness.

## Confirmed behaviors for review

- Canonical resource vectors and resource IDs are unchanged.
- All twelve decoder reject outcomes remain reachable with stable multi-defect precedence.
- All policy ceilings accept the exact boundary and reject boundary plus one.
- Envelope, claim/accounting, proof/runtime, and resource-minimum rejection order is preserved across helper boundaries.
- Compatibility still binds admission mode, policy identity, machine, domain, cost model, validity windows, artifact limits, and cost limits.
- Successful cost quotes obey model and verifier caps; bounded reservation dominates actual cost.
- Nonzero opaque identifiers, flags, quantities, reject stages, reject codes, labels, and diagnostics retain their existing behavior.
- Constructor regressions can no longer turn the affected behavior tests green by skipping their principal assertions.
- No new complexity warning, smell, antipattern, or exception debt can enter CI silently.

## Remaining gaps and non-claims

- Lexical checks do not replace rustc/Clippy AST analysis or macro expansion.
- Cyclomatic complexity is not computed by the dependency-free lexical lane. Cognitive complexity is compiler-enforced by Clippy.
- Python quality-tool coverage was measured diagnostically but is not a governed release threshold; the combined focused run was 74% under local Coverage.py.
- No formal equivalence proof covers the structural Rust refactors. Tests, vectors, branch coverage, mutation, Kani, Miri, and fuzzing are the supplied evidence.
- This change does not implement state, membership, nullifiers, accounting, transformation, persistence, proof verification, commit, journal, or production release authority.
- `ZRM-CBC-033` remains `implemented_partial`; a structural quality report is one evidence layer, not a complete correctness claim.

## Human review surface

Human review needs only the confirmed behavior list, exact assurance table, obligation status, and non-claims above. Source organization and design-pattern mechanics are technical AI-review concerns. Semantic direction is required only if a future implementation discovers an ambiguity or conflict in the specification.
