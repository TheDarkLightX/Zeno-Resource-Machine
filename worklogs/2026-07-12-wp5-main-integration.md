# WP5 main integration work log

**Author:** Dana Edwards

**Drafting assistance:** GPT-5.6

**Status:** local Class C integration candidate; no production authority

## Goal and scope

Integrate the independently reviewed WP5 bounded-artifact endpoint onto
`main` after the semantic-closure recovery merged. Preserve the reviewed Rust
source and evidence commit in ancestry, reconcile only overlapping status
documents, and keep both candidate scopes unpromoted.

## Authority and semantic delta

The integrated API remains:

```text
BoundedArtifactV1::try_new(&[u8], u32)
  -> Result<BoundedArtifactV1, ArtifactErrorV1>
```

It establishes only an owned byte copy under a caller-selected limit capped by
the protocol ceiling. It creates no canonical object, authenticated policy
decision, verified fact, state effect, commit capability, or journal.

The merge changed no WP5 Rust source or tests from reviewed endpoint
`365ea983a066ac71d802d0c9e14eb29fa8fd05fc`. The original evidence-bound source
revision `47fb1e536e1e8f4ffc753d607d4b65e1b9bf287a` remains an ancestor.

## Conflict resolution

Three files overlapped with the semantic-closure recovery:

- `README.md`;
- `CONFORMANCE_MATRIX.json`;
- `PACKAGE_MANIFEST.json`.

Their combined wording retains both scopes:

- WP5 remains an unreviewed bounded-artifact candidate;
- the semantic-closure RFC package remains unapproved Class E design;
- neither scope expands the reviewed ZRM-L0 implementation claim;
- no release or production claim is made.

## Structural review packet

```text
Change class:
  C, because this adds a public semantic staging type for untrusted verifier
  bytes, while granting no verifier authority.

Design forces:
  Preserve exact reviewed source, deterministic error precedence, bounded
  allocation, inward dependencies, and absence of authority.

Pattern selected:
  No new pattern. Retain the private-field bounded value object and private
  test-only reservation seam from the reviewed endpoint.

Invalid states prevented:
  Limit above protocol ceiling, input above selected limit, allocation refusal
  reported as success, and ordinary Debug disclosure of artifact bytes.

Alternatives rejected:
  Rebase or cherry-pick, because rewriting the reviewed source revisions would
  weaken evidence identity; force-pushing the obsolete PR branch; combining
  governed registry or proof verification work into this slice.

Canonical/API/resource impact:
  New pre-alpha Rust type only. No canonical bytes or hashes. At most one exact
  reservation and copy bounded by MAX_PROOF_ARTIFACT_BYTES.

Technical AI-review status:
  Combined-tree gates passed. Final independent combined-tree review remains
  required before publication.
```

## Exact integration endpoint

```text
base revision:
  105f236e18ff954a4295996c4d11538dcc391d74

integration revision:
  b6ab212958992c844bf469f555b9bd7eb79413dc

integration tree:
  3da0471de2933acba93fd87d4387d1fbd8eb2331

reviewed WP5 endpoint:
  365ea983a066ac71d802d0c9e14eb29fa8fd05fc
```

## Local results

- package manifest: 41 payload files matched;
- conformance: 45 obligations, live anchors, valid states, acyclic;
- hygiene and architecture: passed;
- complexity: 38 files, 300 functions, zero warnings or exceptions;
- code quality: `excellent-candidate`, 16 rules, 5 decisions, zero advisories;
- Python policy/tooling tests: 76 passed;
- Rust runtime tests: 116 passed;
- compile-fail doctests: 3 passed;
- formatting, compilation, Clippy with warnings denied, and documentation:
  passed;
- independent vector replay: 6 binary artifacts and 4 protocol digests;
- generated fuzz corpus replay: passed.

The machine-readable receipt is
[`evidence/wp5-main-integration-2026-07-12.json`](../evidence/wp5-main-integration-2026-07-12.json).

## Remaining gaps and non-claims

- Human Class C behavior/evidence review remains required.
- Hosted CI on the integration branch remains required.
- Prior line, branch, mutation, and Miri evidence remains bound to the exact
  earlier reviewed source revision and unchanged source hashes.
- No WP5-specific Kani harness or fuzz target exists.
- No authenticated artifact limit, aggregate budget, proof parser, verifier
  registry, cryptographic verification, verified fact, state transition,
  persistence, atomic commit, release, or production authority exists.
