# WP0 complexity-report implementation work log

## Design packet

Goal:

Implement the machine-readable source-complexity report and exception-validation workflow required by `ZRM-CBC-033`, without changing protocol semantics or authority code.

Change class:

Class B non-authority tooling. The checker observes repository Rust source and reports review triggers. It cannot construct protocol values, influence accepted state, or approve an exception.

Affected crates/modules:

- new dependency-free `tools/check_complexity.py` and `tools/rust_complexity.py` modules;
- focused Python unit tests;
- an empty reviewed-exception registry schema;
- CI invocation if the current source baseline has no unapproved review-trigger findings;
- `ZRM-CBC-033` evidence and this work log.

Exact typed statement or API:

```text
Rust source bytes
  -> lexical source model
  -> deterministic file/item metrics
  -> preferred-limit warnings + review-trigger findings
  -> exact finding IDs
  -> validated approved-exception coverage
  -> machine-readable report + pass/review-needed decision
```

The Python API exposes typed dataclasses for measured functions, measured traits, findings, exception evaluation, and file analysis. The CLI writes canonical repository-relative JSON and exits nonzero when a review-trigger finding lacks one exact approved exception, when an exception is stale, or when the exception registry is malformed.

Authority boundary:

None. The tool is advisory and gate-supporting. Its output is evidence for review scope, not semantic authority, formal verification, human approval, or production readiness. Exception entries record approval metadata but do not prove that the named reviewer performed the review.

Invariants preserved or added:

- inputs and outputs use repository-relative paths only;
- discovery and report ordering are deterministic;
- comments and string contents do not create false Rust items or brace depth;
- nested block comments are handled fail closed;
- function length, lexical brace depth, positional parameter count, public trait method count, and module length use explicit project thresholds;
- cyclomatic and cognitive complexity remain explicit unmeasured gaps;
- every over-trigger finding requires one exact, non-stale approved exception;
- every approved exception requires a revision, reviewer, rationale, decomposition alternatives, and focused tests;
- stale or duplicate exception entries reject;
- the checker never edits source or generated artifacts.

Disaster states affected:

- critical functions or modules become too complex for reliable local review (`ZRM-CBC-033`);
- agent-authored code bypasses evidence and review workflow (`ZRM-CBC-039`, preserved but not promoted).

Canonical bytes or hashes affected:

None. Report SHA-256 fingerprints and finding IDs are tooling identities only. They are not protocol hashes, canonical authority bytes, release digests, or evidence-record roots.

Compatibility/versioning impact:

The report and exception registry use explicit tooling schemas under `zrm/complexity-*/v1`. Changes to metric meaning require a tooling-schema version change. No protocol or public Rust API changes.

Tests to add first:

- comments and ordinary/raw string literals do not alter function discovery or nesting;
- multiline functions have deterministic noncomment source-line counts;
- receiver syntax is excluded from positional API parameter counts;
- public trait method counting ignores nested default-method bodies;
- preferred-limit findings warn while review-trigger findings require approval;
- malformed, duplicate, stale, and unapproved exceptions fail closed;
- report paths, ordering, fingerprints, and JSON are deterministic;
- the current repository source produces no unapproved review-trigger finding before CI integration.

Formal/model obligations:

None for this Class B slice. Unit fixtures and repository replay cover the lexical contract. The checker does not calculate or claim cyclomatic complexity, cognitive complexity, semantic criticality, AST correctness, or proof of auditability.

Dependency impact:

No new dependency. The implementation uses only the Python standard library already required by repository policy tooling.

Performance/resource bounds:

The checker reads each discovered Rust source file once, rejects files above the repository one-megabyte review ceiling, and uses memory linear in total scanned source bytes. It does not execute Cargo, rustc, source macros, build scripts, or network operations.

Non-claims and known gaps:

- no cyclomatic or cognitive-complexity measurement;
- no Rust macro expansion or compiler AST analysis;
- lexical nesting is a conservative brace-depth metric and is not cognitive complexity;
- no automatic classification of which functions are semantically critical;
- no claim that an exception reviewer identity is authenticated;
- no human review or promotion is supplied by this agent-authored tooling;
- no protocol, authority, state, verifier, persistence, proof, or release behavior changes.

## Evidence log

The first repository replay found one unapproved review trigger:

```text
crates/zrm-policy/src/limits.rs
validate_candidate
function_noncomment_source_lines = 89
review trigger = 60
```

No exception was added because this agent cannot supply the required reviewer approval.

## Scope-extension design packet: WP2 limit-validator decomposition

Goal:

Remove the discovered review trigger through a semantics-preserving decomposition of the ordered policy-limit validator.

Change class:

Class C semantic-code refactor because the edited function enforces authority-path resource limits, even though no intended accepted/rejected behavior changes.

Affected crates/modules:

- `crates/zrm-policy/src/limits.rs`;
- focused limit reject-precedence tests in `crates/zrm-policy/tests/policy_model.rs`;
- `ZRM-CBC-016`, `ZRM-CBC-033`, and `ZRM-CBC-045` evidence references remain scoped to the existing candidate implementation plus this replay.

Exact typed statement or API:

`PolicyLimitsCandidateV1 -> PolicyLimitsV1 | PolicyValidationErrorV1` remains unchanged. The validator delegates to three private helpers in the original field order, then performs the 603-byte resource-wire minimum check last.

Authority boundary:

Unchanged. This remains local, deterministic candidate validation. It creates no policy hash, authenticated policy, trusted context, verifier fact, state capability, or commit authority.

Invariants preserved or added:

- every existing ceiling guard remains present exactly once;
- reject order remains declaration order across helper boundaries;
- the resource-wire minimum remains after every protocol-ceiling check;
- no public type, constructor, error, bound, canonical byte, or hash changes;
- the previously over-trigger function and each new helper remain within the source-line review trigger.

Disaster states affected:

- overflow or resource-bound bypass through a lost/reordered guard (`ZRM-CBC-016`, `ZRM-CBC-045`);
- locally unauditable critical validation (`ZRM-CBC-033`).

Canonical bytes or hashes affected:

None.

Compatibility/versioning impact:

None. Private implementation structure only.

Tests to add first:

Add one cross-family precedence test with simultaneous faults proving envelope-before-claim, claim-before-runtime, and runtime-before-resource-minimum ordering.

Formal/model obligations:

Existing Kani coverage of the resource-byte interval remains applicable. No stronger proof claim follows from the refactor or lexical checker.

Dependency impact:

None.

Performance/resource bounds:

The same constant number of comparisons and branches execute in the same order. Private calls are expected to inline in optimized builds; no performance claim is made.

Non-claims and known gaps:

- refactoring plus tests is not formal equivalence proof;
- the WP2 policy slice remains unreviewed candidate code until human Class C review;
- complete dispatch planning and end-to-end resource-exhaustion assurance remain unimplemented.

## Implementation summary

- added a dependency-free lexical Rust-source analyzer with deterministic, source-sensitive finding IDs;
- split lexical measurement from exception/report/CLI policy so both tooling modules remain below the 700-line review trigger;
- added preferred warnings and mandatory review triggers for noncomment source lines, lexical code-brace depth, explicit positional parameters, public-trait method counts, and module lines;
- added a fail-closed exception registry that rejects malformed, duplicate, stale, unapproved, or missing-test approvals;
- restricted report writes to nonsymlinked JSON paths beneath `target/`;
- integrated the checker into the ordinary CI repository/conformance step;
- decomposed the single over-trigger WP2 limit validator into three private invariant-family helpers while retaining exact error order;
- regenerated only the derived conformance-matrix entry in the specification package manifest.

## Files changed

- `.github/workflows/ci.yml`;
- `CONFORMANCE_MATRIX.json`;
- `PACKAGE_MANIFEST.json` through `tools/update_package_manifest.py`;
- `crates/zrm-policy/src/limits.rs`;
- `crates/zrm-policy/tests/policy_model.rs`;
- `tools/check_complexity.py`;
- `tools/complexity_exceptions.json`;
- `tools/rust_complexity.py`;
- `tools/tests/test_complexity.py`;
- this work log.

## Typed statements and APIs changed

No public Rust API changed. `PolicyLimitsCandidateV1 -> PolicyLimitsV1 | PolicyValidationErrorV1` retains the same public constructor and errors.

New non-authority Python APIs include `analyze_rust_source`, `classify_findings`, `validate_exception_registry`, and `build_report`, plus private repository discovery and target-only report writing.

## Invariants added or preserved

- all sixteen policy ceilings and the final resource-wire minimum remain checked in the original order;
- simultaneous faults still select envelope before claim, claim before proof/runtime, and proof/runtime before the resource-wire minimum;
- exception IDs bind the complete source-file SHA-256 as well as location, metric, measured value, and review trigger;
- same-size unreviewed source edits invalidate prior exception IDs;
- report discovery, file order, finding order, JSON serialization, and source fingerprinting are deterministic;
- zero approved exceptions cannot authorize a review-trigger finding;
- out-of-target or symlinked report destinations fail before a source file can be replaced.

## Disaster states addressed

- locally unauditable critical validation (`ZRM-CBC-033`);
- lost or reordered resource-bound checks (`ZRM-CBC-016`, `ZRM-CBC-045`);
- stale or fabricated complexity exceptions within the limits of unauthenticated repository metadata.

## Tests added or changed

- fourteen focused Python tests cover comments, nested comments, ordinary/raw strings, character literals versus lifetimes, delimiters, function lines, brace depth, parameters, trait methods, empty discovery, deterministic reports, source-sensitive IDs, exact exceptions, stale/duplicate/unapproved/missing-test rejects, path escape, and source-overwrite prevention;
- one Rust integration test covers reject precedence across all three new helper boundaries and the final minimum check.

## Mutants killed or surviving

The full configured workspace campaign tested 302 mutants: 239 were caught and 63 were unviable. There were zero missed or timed-out mutants. No mutation score is claimed for the Python checker because the repository has no governed Python mutation lane.

## Formal/model evidence

Kani 0.60.0 verified all 8 existing workspace harnesses, including the exact resource-byte interval harness, with 0 failures. Kani emitted target-feature, future-incompatibility, and unsupported-construct warnings; the reported unsupported constructs were not reachable from the completed harnesses. This is bounded verification, not a general equivalence proof of the refactor.

Miri under `nightly-2025-03-02` passed all 66 Rust tests and four zero-test doc suites. Miri does not prove soundness or policy correctness.

## Canonical hashes and vectors changed

No protocol bytes, hashes, domains, schemas, vectors, IDs, roots, or reject codes changed. The package manifest's derived size and SHA-256 entry for `CONFORMANCE_MATRIX.json` changed after the matrix evidence update. Complexity fingerprints and finding IDs are tooling-only identities.

## Dependencies changed

None. The checker uses only the Python standard library. Workspace and fuzz advisory and dependency-policy gates passed.

## Performance and resource-bound impact

The Rust validator retains the same constant number and order of comparisons. The checker reads each Rust source once under the existing one-megabyte repository file ceiling and uses memory linear in scanned source bytes. It executes no build script, macro expansion, Cargo command, network request, or Rust source.

## Commands executed

| Command | Exact result | Evidence or note |
| --- | --- | --- |
| `python3 -m unittest discover -s tools/tests -p test_complexity.py -v` before implementation | failed with `ModuleNotFoundError: tools.check_complexity` after correcting the test fixture syntax | test-first implementation evidence |
| same focused Python command after adding source-sensitive, path-write, lifetime, and empty-discovery regressions | failed 2 of 11, then 1 of 12, then 2 of 14; final replay passed 14 of 14 | every identified gap was fixed |
| `python3 tools/check_complexity.py --report target/complexity-report.json` before refactor | failed: one unapproved trigger, `validate_candidate` 89 lines over trigger 60 | no exception was added |
| same complexity command after refactor | passed: 16 files, 185 functions, 5 preferred warnings, 0 review triggers, 0 approved exceptions | final source fingerprint `03b47706d9e268fa3f71bee54ddf5505263371f80bc672222170b77f9ca594d0` |
| `cargo test -p zrm-policy --test policy_model --locked` | passed 20 tests | includes new cross-family precedence test |
| `python3 -m unittest discover -s tools/tests -v` | final replay passed 29 tests after the auditability module split | repository policy helper suite |
| `python3 tools/check_conformance.py` | passed 45 obligations, live anchors, promotion states, and acyclic dependencies | matrix remains `implemented_partial` for CBC-033 |
| `python3 tools/update_package_manifest.py` | updated 14 payload entries | generator used; manifest not edited manually |
| `python3 tools/check_package_manifest.py` | passed all payload sizes and SHA-256 digests | derived package metadata |
| `python3 tools/check_architecture.py` | passed exact internal and external dependency allowlists | no dependency edge changed |
| `python3 tools/check_repository_hygiene.py` | passed after removing a literal local-context test marker | source, mode, size, secret, and action-pin checks |
| `cargo fmt --all --check` | passed after one mechanical formatting application | no remaining format diff |
| `cargo metadata --format-version 1 --locked --no-deps` | passed for four workspace crates | command output itself contains local diagnostic paths and is not a public artifact |
| `cargo check --workspace --all-targets --all-features --locked` | passed | full compile gate |
| `cargo clippy --workspace --all-targets --all-features --locked -- -D warnings` | passed | no lint suppression added |
| `cargo test --workspace --all-features --locked` | passed 66 tests, 0 failures | four doc suites also ran with 0 doctests |
| `cargo test --workspace --doc --locked` | passed four suites, 0 doctests | explicit doc-test gate |
| `cargo doc --workspace --no-deps --locked` | passed | workspace documentation built |
| `python3 vectors/independent_python/replay_resource_wire_v1.py --check` | passed 6 binary artifacts and 4 protocol digests | confirms no vector drift |
| `cargo +nightly-2025-03-02 llvm-cov --workspace --all-features --locked --branch --json --output-path target/llvm-cov-branch.json` | passed and wrote the report | branch instrumentation warned that the option is unstable |
| workspace coverage threshold check | passed: lines 98.24%, branches 96.94% | thresholds 90% / 85% |
| `zrm-policy` coverage threshold check | passed: lines 99.13%, branches 100.00% | thresholds 95% / 100% |
| `cargo mutants --workspace --timeout 10 --build-timeout 60 --jobs 2 --output target/mutants-complexity-followup` | passed: 302 tested in about 2 minutes, 239 caught, 63 unviable | zero missed/timeouts |
| `cargo kani --workspace` | passed: 8 of 8 harnesses, 0 failures | warnings retained as scoped caveats |
| `cargo +nightly-2025-03-02 miri test --workspace --all-features --locked` | passed all 66 tests | no unsafe code added |
| root and fuzz `cargo +1.87.0 audit` commands | passed after loading 1,159 advisories; scanned 13 and 22 dependencies | live advisory database used |
| root and fuzz `cargo +1.88.0 deny ... check` commands | both passed advisories, bans, licenses, and sources | no dependency delta |
| `python3 fuzz/generate_corpus.py --check` | passed resource boundary and three policy-cost seeds | no fuzz target or grammar changed |
| `python3 .../codex_peer_review.py ...` | unavailable: peer returned HTTP 401 for missing API authentication | no independent peer-review claim |

Important commands initially attempted inside the restricted wrapper sometimes failed before execution with a loopback namespace error. Each evidence-bearing command above was rerun through an approved execution boundary; wrapper failures are not counted as passes.

## Self-review

- [x] no unrelated source cleanup;
- [x] no weakened test, bound, reject, or claim;
- [x] no raw data promoted to authority;
- [x] reject-is-no-op and authority stages remain untouched;
- [x] arithmetic and resource ceilings are unchanged and checked in order;
- [x] no protocol bytes or vectors changed;
- [x] docs, matrix, derived manifest, and work log agree;
- [x] no dependency added;
- [x] remaining uncertainty and unavailable peer review are disclosed.

## Remaining gaps and non-claims

- the Python checker is lexical and does not expand macros or use rustc's AST;
- cyclomatic complexity, cognitive complexity, and semantic-criticality classification remain unmeasured;
- the five preferred-limit warnings do not cross review triggers, but remain visible in the report;
- exception reviewer identity and revision metadata are not cryptographically authenticated;
- no approved exception exists, and this agent cannot create one;
- the Rust refactor has tests, mutation, coverage, Kani, and Miri evidence, but no formal equivalence proof;
- no new fuzz target exercises the Python lexer; the deterministic corpus was replayed because no Rust wire grammar changed;
- the independent Codex peer review was unavailable, and human Class C review is still required;
- no canonical policy codec/hash, trusted context, verifier registry, authority fact, state, commit, journal, proof, release, or production claim is added.

## Human review required

- Required reviewers/roles: semantic owner and test/evidence reviewer for the Class C Rust refactor; maintainer or tooling owner for the Class B checker.
- Review focus: exact reject order, lexical-parser fail-closed limits, source-sensitive exception invalidation, target-only report writes, and honest unmeasured metrics.
- Promotion blocked until: the current diff receives the required human review and hosted CI replays the new checker.

## Final superseding quality update

The earlier five-warning replay above records the discovery baseline. The final tree removes all five advisories rather than approving them:

```text
22 production Rust files
192 functions
0 preferred warnings
0 review triggers
0 approved exceptions
```

The post-audit checker also rejects duplicate JSON object keys at every depth and no longer mistakes const-expression braces in return types or `where` clauses for function bodies. Public generic type parameters are explicitly listed as unmeasured rather than omitted from the report. The focused complexity suite passes 19 tests.

The combined multi-axis result, behavioral assurance evidence, and current human-review surface are authoritative in `worklogs/2026-07-11-wp0-code-quality-report.md`. Human review receives behaviors, exact evidence, gaps, and non-claims. Technical parser organization and pattern mechanics use AI review. `ZRM-CBC-033` remains `implemented_partial` because lexical analysis is not a compiler AST, cyclomatic complexity remains unmeasured, and the evidence does not prove semantic correctness.
