# RFC-0004 CBC obligation remediation

**Date:** 2026-07-15
**Change class:** Class E assurance traceability for an unapproved Class E proposal
**Scope:** conformance metadata, checker, and focused regression coverage only

## Design packet

Goal:
Add explicit CBC obligations for RFC-0004 so its scoped semantic, canonical
encoding, provenance, proof/refinement, boundary, and research evidence cannot
be mistaken for an approved implementation.

Affected crates/modules:
`CONFORMANCE_MATRIX.json`, `PACKAGE_MANIFEST.json`, the RFC-0004 research
manifest, `tools/check_conformance.py`, the policy and count-dependent
delegation tests, and this worklog. No Rust crate or proof source changes.

Exact typed statement or API:
The v1 matrix gains sequential obligations `ZRM-CBC-047` through
`ZRM-CBC-055`. The checker requires identifiers `001..055`; the policy test
requires all nine RFC-0004 families and the unexecuted ESSO plan to stay visible.

Authority boundary:
The matrix, model, vectors, and proofs remain evidence and release gates, not
protocol authority. RFC-0004 remains unapproved. Only a governed profile,
sealed verifier facts, and the semantic/commit pipeline can create authority.

Attacker-controlled versus governed inputs:
Proposed aggregate fields, model outputs, vectors, proofs, and research receipts
are untrusted evidence. Profile limits and identity, verifier identities,
accepted-journal schemas, retention policy, RFC approval, and release promotion
are governed inputs that do not yet exist for this profile.

New states or transitions introduced:
None.

Invariants preserved/added:
Identifiers remain unique and sequential; every obligation has live normative
anchors; scoped evidence remains scoped; aggregate totals never grant leaf or
commit authority; missing openings, vectors, refinement, circuit evidence,
independent review, or approval block promotion.

Disaster states affected:
Cross-profile or cross-domain substitution; proof-tree-dependent numeric
definedness; omitted or relabeled accounting provenance; theorem/runtime drift;
unsafe net projection; and release claims exceeding evidence.

Canonical bytes or hashes affected:
No protocol bytes, domains, vectors, roots, or hashes change. Only the package
manifest's digest and byte count for the matrix payload are regenerated.

Replay and cross-domain separation impact:
No replay domain changes. The rows retain profile, accepted-journal,
accounting-row-hash, coverage, and proof-binding separation as unresolved work.

Compatibility/versioning impact:
No schema or protocol ABI change. Matrix consumers must accept the extended
sequential set through `ZRM-CBC-055`.

Tests to add first:
A focused test that fails while RFC-0004 rows are absent, followed by checker,
tool-test, packet, vector, model, and package-manifest replay.

Independent oracle:
RFC-0004's exact section anchors and the review finding define coverage. The
conformance checker validates structure, refs, status, dependencies, and claim
posture.

Counterexample and mutation strategy:
Deleting a row breaks sequential IDs; removing a required RFC anchor or the
unexecuted ESSO plan breaks focused coverage; existing checker mutations retain
status, reference, and promotion-boundary coverage.

Formal/model obligations:
No theorem changes. Existing Lean evidence must remain distinct from missing
Rust refinement, canonical-byte proof, circuit constraints, proof-system
binding, and independently reviewed release evidence.

Dependency impact:
None.

Performance/resource bounds:
Nine bounded JSON rows add negligible linear checker work and no runtime cost.

Non-claims and known gaps:
This change does not approve RFC-0004, freeze its ABI, complete vectors,
implement Rust or a recursive guest, prove a circuit, execute ESSO, establish
DA or privacy, satisfy independent review, or permit production claims.

Design forces:
Gaps must close independently while staying auditable in one machine-readable
release gate.

Pattern selected, or no additional pattern:
No new pattern; use the existing obligation record and dependency graph.

Invalid states prevented:
A matrix containing RFC-0004 artifacts without explicit semantic, codec,
provenance, proof, authority, and research gaps fails focused coverage.

Extension point or closed-set reason:
The matrix is a closed sequential set for this revision; additions require an
explicit checker and test update.

Alternatives rejected:
One omnibus row hides independently closable gaps. Generic CBC-027, CBC-036,
CBC-037, and CBC-043 do not identify RFC-0004's new bytes, retained openings,
coverage, proof binding, or research plan.

Pattern-specific failure modes:
Overlapping rows can double-count evidence, and scoped proofs can overstate
runtime implementation. Each row therefore names its boundary, dependencies,
next action, and non-claim.

Enforcement and tests:
The conformance checker, focused policy test, delegation fixture, package
manifest, and existing CI tool-test job.

Technical AI-review status:
Independent read-only audits completed before and after editing. All five
post-edit findings were remediated and focused gates passed. RFC approval still
requires the independent human reviewers named by RFC-0004.

## Completion report

Summary:
Added nine RFC-0004 obligations, expanded the fail-closed CBC universe from 46
through 55, pinned the deliberate status/dependency/non-claim split in tests,
kept the profile unreviewed at ZRM-L0, and synchronized both generated manifests.

Files changed:
`CONFORMANCE_MATRIX.json`, `PACKAGE_MANIFEST.json`,
`research/zrm_accounting_aggregate_v1/manifest.json`,
`tools/check_conformance.py`, `tools/tests/test_delegation_plan.py`,
`tools/tests/test_policy_checks.py`, and this worklog.

Typed statements/APIs changed:
No protocol type or runtime API changed. The matrix closed set is now
`ZRM-CBC-001..055`.

Invariants added or preserved:
RFC-0004 arithmetic, tree-definedness, encoding, retained-opening, coverage,
profile-binding, resource-bound, sealed-fact, and net-boundary obligations are
independently tracked. The ZRM-L0 claim scope is unchanged. The ESSO campaign is
tested as `specified_not_executed`, not counted as evidence.

Disaster states addressed:
Silent RFC evidence promotion, missing canonical/provenance/proof obligations,
cross-profile substitution, proof-tree-dependent arithmetic, theorem/runtime
drift, forged recursive authority, and net-as-no-op overclaim.

Tests added:
One focused matrix regression now pins all nine RFC rows, their status split,
blocking dependencies, RFC anchors, candidate scope, top-level non-claims, and
the unexecuted ESSO gap. The count-dependent delegation fixture now uses 55 IDs.

Mutants killed:
The pre-fix focused test produced nine missing-obligation failures and one
dependent lookup error. The final test passes. Existing packet mutation tests
also preserve the ESSO non-execution and manifest-integrity boundaries. No
runtime protocol guard changed, so no Rust mutant was introduced.

Formal/model evidence:
No proof source changed. The referenced Lean package rebuilt successfully as 10
Lake jobs and `leanchecker --verbose ZrmAccountingAggregateV1` replayed its
five modules. The scoped 34-test accounting model and 16-artifact independent
vector replay passed.

Commands run and exact results:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tools.tests.test_policy_checks.ConformanceHelperTests.test_rfc_0004_obligation_families_are_release_tracked -v`: pre-fix FAILED with nine missing rows plus one dependent lookup error; post-fix passed.
- `python3 tools/update_package_manifest.py`: updated 49 payload records.
- `python3 tools/check_zrm_accounting_research.py --write-manifest`: regenerated and then validated 12 experiments, 74 nodes, 85 edges, 20 hypotheses, 24 Morph candidates, and 22 sources.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/tests -v`: 150/150 passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference_models/tests -v`: 122/122 passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest reference_models.tests.test_accounting_aggregate_v1 -v`: 34/34 passed.
- `python3 vectors/independent_python/replay_accounting_aggregate_v1.py --check`: passed, 16 binary artifacts, 4 rows, 2 coverage entries.
- `lake build --wfail && lake env leanchecker --verbose ZrmAccountingAggregateV1`: 10 jobs built; five modules replayed.
- `lake clean`: removed generated local-path build metadata after the hygiene gate correctly rejected it.
- Final repository chain covering hygiene, conformance, delegation, architecture, complexity, code quality, package manifest, accounting packet, and `git diff --check`: all passed; conformance reports 55 live, acyclic obligations.

Canonical hashes/vectors changed:
No protocol domain, preimage, root, hash, or vector changed. Only generated
manifest byte counts and SHA-256 records changed.

Dependencies changed:
None.

Performance/resource-bound impact:
Nine bounded JSON rows add negligible linear checker work and no runtime,
storage, proof, or consensus cost.

Remaining gaps and non-claims:
RFC-0004 remains unapproved and unimplemented in Rust or a recursive guest.
Profile limits and ID, complete independent vectors, retained-opening parser and
availability, exact ordered coverage refinement, Rust/circuit refinement,
executed ESSO evidence, benchmarks, sealed verified fact, DA/privacy review,
independent human review, audit, release, and production authority remain open.

