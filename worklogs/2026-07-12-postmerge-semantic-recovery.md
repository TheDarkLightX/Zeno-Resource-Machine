# Post-merge semantic recovery work log

**Author:** Dana Edwards

**Drafting assistance:** GPT-5.6

**Date:** 2026-07-12

## Design packet

- **Goal:** restore the exact reviewed PR #12 semantic-closure payload to the
  default branch after it was merged into an already-merged feature branch,
  then prevent the same stacked-merge failure from being mistaken for default-
  branch integration.
- **Change class:** Class E for transport of the already reviewed RFC and
  authority-design payload; Class B for the contribution-process clarification.
- **Affected surfaces:** RFC index and RFCs, semantic decision and refinement
  artifacts, review packets, conformance discovery metadata, package manifest,
  public candidate-status wording, contribution workflow, pull-request
  checklist, and repository-hygiene traversal.
- **Typed statement or API:** no Rust type, API, codec, hash preimage, root, or
  authority constructor changes.
- **Authority boundary:** this recovery transports design artifacts only. It
  creates no verifier fact, policy activation, commit capability, accepted
  journal, implementation promotion, or release authority.
- **Required invariant:** the recovered semantic payload must be byte-for-byte
  identical to the reviewed PR #12 payload except for separately identified
  status, process, tooling, recovery-metadata, and deterministic-manifest
  corrections that do not change either RFC's semantics.
- **Disaster states:** silently losing reviewed Class E material; changing the
  RFC semantics while presenting the change as history repair; publishing stale
  package hashes; treating a merge into a feature branch as integration into the
  default branch; exposing private project context.
- **Canonical and ABI impact:** none. The RFCs still defer new canonical byte
  tables and identities to later reviewed work.
- **Tests first:** establish that PR #12's reviewed head is not an ancestor of
  `origin/main`; after recovery require every reviewed payload path and byte to
  match, package and conformance checks to pass, and the recovery head to contain
  the reviewed payload.
- **Formal obligations:** no theorem is promoted. Existing bounded-model claims
  and non-claims remain unchanged.
- **Dependency impact:** none.
- **Performance bounds:** no runtime code changes.
- **Non-claims:** branch ancestry and green repository checks do not approve the
  RFCs, prove their semantics, implement the modeled machine, or establish
  production readiness.

## Initial counterexample

```text
PR #12 state: merged
PR #12 base: agent/semantic-contracts-v1
PR #8 state: already merged to main before PR #12
f2280901c8f0241726efe63ff98191b4596e7b69 ancestor of origin/main: false
```

This is a concrete integration failure: GitHub correctly merged PR #12 into its
declared base, while the reviewed payload remained absent from the default
branch.

## Planned preservation checks

1. Compare the recovered payload paths against PR #12's exact parent-relative
   tree delta.
2. Verify unchanged recovered files byte-for-byte.
3. Regenerate and check the package manifest only after all payload edits.
4. Run conformance, repository hygiene, architecture, code-quality, formatting,
   compilation, lint, tests, and documentation gates applicable to the final
   recovery branch.
5. Scan public tracked files for prohibited private context and attribution
   drift.

## Additional defects found during replay

1. The public README still described hosted CI as pending after the relevant
   default-branch run passed. The corrected wording records the pass while
   retaining WP3c's unpromoted status and the absence of a repository-bound
   independent human Class C approval record.
2. The repository-hygiene walker excluded a `.git` directory but scanned the
   `.git` pointer file used by linked worktrees. That local pointer contains an
   absolute path and produced a false privacy failure. A regression test now
   establishes that VCS metadata is excluded in both checkout forms.

Neither correction changes a protocol rule or promotes an implementation
claim.

## Local verification results

The recovery branch was replayed from current `origin/main` rather than from
either closed feature branch.

```text
PR #12 reviewed payload comparison:
  all RFC, formal, review, matrix, specification, and RFC-index payload bytes
  preserved; only the separately documented README status correction and
  regenerated PACKAGE_MANIFEST.json differ

python3 tools/check_package_manifest.py
  PASS: all payload sizes and SHA-256 digests match

python3 tools/check_conformance.py
  PASS: 45 obligations, live anchors, valid promotion states,
  acyclic dependencies

python3 tools/check_repository_hygiene.py
  PASS: configured context, secret, source, mode, size, and action-pin checks

python3 tools/check_architecture.py
  PASS: exact internal and external dependency allowlists match

python3 tools/check_complexity.py
  PASS: 36 files, 288 functions, 0 preferred-limit warnings,
  0 approved exceptions

python3 tools/check_code_quality.py
  PASS: excellent-candidate, technical AI review complete, 16 rules,
  5 design decisions, 0/0 complexity advisories

python3 -m unittest discover -s tools/tests -p 'test_*.py'
  PASS: 74 tests, 0 failures

cargo +1.87.0 fmt --all -- --check
  PASS

cargo +1.87.0 test --workspace --all-targets --locked
  PASS: 104 runtime tests, 0 failures

cargo +1.87.0 test --workspace --doc --locked
  PASS: 2 compile-fail doctests, 0 failures

cargo +1.87.0 clippy --workspace --all-targets --all-features --locked -- -D warnings
  PASS

cargo +1.87.0 doc --workspace --no-deps --locked
  PASS

python3 vectors/independent_python/replay_resource_wire_v1.py --check
  PASS: 6 binary artifacts and 4 protocol digests

python3 fuzz/generate_corpus.py --check
  PASS: every declared deterministic corpus seed matched
```

## Remaining review boundary

This recovery restores reachability and corrects evidence wording. It does not
convert either Class E RFC from draft to approved, supply the missing concrete
Rust-to-model refinement, or authorize implementation of the modeled commit and
recursive-composition semantics.
