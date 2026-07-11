# WP0 SBOM and CBOM generation work log

**Date:** 2026-07-11
**Change class:** Class B, non-authority supply-chain tooling

## Design packet

### Goal

Add deterministic, offline-capable generation of a source dependency software bill of materials (SBOM) and cryptographic bill of materials (CBOM) for both the root semantic workspace and the isolated fuzz workspace. Bind every registry component to its locked checksum, expose dependency edges plus build-script/proc-macro surface, and require every implemented cryptographic primitive to have a complete, live, machine-readable registry record.

### Affected crates/modules

- new `tools/generate_bom.py` generator and validator;
- new focused tests under `tools/tests/test_bom.py`;
- new reviewed cryptography registry under `supply-chain/cryptography.json`;
- new exact build-script/proc-macro policy under `supply-chain/build_surface.json`;
- updated `docs/DEPENDENCY_POLICY.md` command and claim boundary;
- CI supply-chain job generation of `target/zrm-sbom.json` and `target/zrm-cbom.json`;
- `ZRM-CBC-040` evidence and this work log.

No Rust crate, dependency version, protocol type, or authority path changes.

### Exact typed statement or API

```text
build_sbom(
  workspaces: [CargoMetadataSnapshot],
  lockfiles: [CargoLockSnapshot],
) -> ZrmSourceSbomV1

build_cbom(
  registry: CryptographyRegistryV1,
  sbom: ZrmSourceSbomV1,
  repository_root: RepositoryRoot,
) -> ZrmCbomV1

apply_build_surface_policy(
  sbom: ZrmSourceSbomV1,
  policy: BuildSurfacePolicyV1,
  repository_root: RepositoryRoot,
) -> ZrmSourceSbomV1
```

The CLI obtains locked Cargo metadata for `Cargo.toml` and `fuzz/Cargo.toml`, then writes canonical sorted JSON only beneath `target/`.

`ZrmSourceSbomV1` records:

- every package's name, version, source classification, declared license, exact registry checksum, activated features, workspace scopes, and target kinds;
- deterministic dependency edges with dependency kind and target condition;
- explicit build-script and proc-macro component lists;
- root and fuzz lockfile SHA-256 digests;
- source-inventory non-claims.

`ZrmCbomV1` records each implemented primitive's algorithm, parameter set, exact implementation package/version, protocol domains, purpose, source/test references, claimed properties, non-claims, and dependency-component binding.

### Authority boundary

The outputs are repository and release-review evidence. They cannot validate a transition, construct a verified fact, authorize a dependency, attest source authenticity, sign provenance, or grant production authority. Cargo metadata and the cryptography registry are inputs to a fail-closed inventory process, not independent trust anchors.

### Invariants preserved/added

- both Cargo invocations use `--locked` and fixed manifest paths;
- registry packages require a matching lockfile entry and lowercase 64-hex checksum;
- path/workspace packages never embed local absolute paths;
- package identity and dependency edges are stable under metadata and mapping insertion order;
- root runtime and isolated fuzz scopes remain explicit;
- build scripts and proc macros cannot disappear from the report;
- every discovered build script and proc macro must exactly match a reviewed package/version/scope policy record with live review references;
- duplicate package identities, edges, crypto IDs, protocol domains, JSON keys, or references reject;
- every CBOM implementation package/version must exist in the SBOM;
- every CBOM source/test reference must be normalized, repository-relative, live, and non-symlinked;
- output paths cannot escape `target/` or overwrite source;
- reports contain no clock, environment, hostname, or absolute-path data.

### Disaster states affected

- a transitive dependency or checksum omitted from release review;
- fuzz-native build tooling mistaken for shipped runtime TCB;
- build scripts or proc macros hidden in an undifferentiated package list;
- cryptographic algorithm, parameter, domain, or implementation drift without CBOM review;
- a cryptographic dependency entering the lockfile without a registry record;
- local paths or nondeterministic timestamps making evidence unreplayable;
- an internal inventory mislabeled as standardized or signed provenance.

### Canonical bytes or hashes affected

No protocol bytes or hashes change. The generated JSON uses tooling-only schemas `zrm/source-sbom/v1`, `zrm/cryptography-registry/v1`, and `zrm/cbom/v1`. Canonical JSON means UTF-8, sorted keys, deterministic list ordering, two-space indentation, and one trailing newline. It is not a protocol authority encoding.

### Compatibility/versioning impact

No Rust or protocol compatibility impact. Changes to inventory field meaning, package identity, scope semantics, or cryptography registry meaning require a tooling-schema version change. CI gains additive supply-chain evidence commands.

### Tests to add first

- metadata and lockfile insertion order cannot change either report;
- exact registry checksum and dependency edges are retained;
- root and fuzz scope membership remains distinct;
- build-script and proc-macro target kinds are surfaced;
- missing, stale, duplicate, or scope-mismatched build-surface approvals reject;
- absolute manifest/source paths never appear;
- missing or malformed checksums, duplicate components/edges/JSON keys, missing resolve graphs, and empty workspaces reject;
- duplicate crypto IDs/domains, missing required fields, stale references, symlinks, and an implementation absent from the SBOM reject;
- output paths outside `target/`, parent traversal, and source overwrite reject;
- repository replay generates both reports successfully.

### Formal/model obligations

None. This is bounded release tooling over Cargo JSON/TOML inputs. Focused fixtures, repository replay, and CI are the appropriate evidence. The tool does not establish artifact provenance or third-party source correctness.

### Dependency impact

No new Rust, Python, build, action, or network dependency. The implementation uses Python 3.12 standard-library `json`, `tomllib`, `hashlib`, `pathlib`, and `subprocess`, plus the already pinned Cargo toolchain. This deliberately avoids adding a framework or SBOM generator to the trusted build surface.

### Performance/resource bounds

- at most two fixed Cargo metadata subprocesses;
- fixed root and fuzz manifests and lockfiles;
- one-megabyte ceiling per metadata/lockfile/registry input;
- time and memory proportional to dependency components plus edges;
- reports written only beneath `target/` after complete validation;
- no network access is requested by the tool, though Cargo may require an already available locked index/cache to produce metadata.

### Non-claims and known gaps

- the v1 output is a ZRM-native source inventory, not a claim of SPDX, CycloneDX, or regulatory schema conformance;
- it inventories Cargo source dependencies, not compiled binary contents, linker inputs, operating-system packages, containers, or deployment firmware;
- a crates.io checksum does not prove source review, maintainer identity, absence of malicious code, or reproducible compilation;
- CBOM completeness is enforced against the current explicit registry and implemented crypto dependency set; future proof systems, signatures, TLS, OS crypto, and hardware primitives require new records and checks;
- cargo-vet adoption still requires human trust criteria, audits, or reviewed imports; this agent will not self-certify third-party crates;
- no vulnerability scan, signed provenance, artifact signature, clean-tree receipt, or reproducibility claim is created by these reports.

## Implementation and verification record

### Tooling modularity scope extension

Self-review found that the first passing implementation placed input validation, Cargo graph normalization, build-surface policy, CBOM validation, and CLI I/O in one 755-nonblank-line Python module. That crosses the repository's 700-line hard review trigger and gives the module several reasons to change.

Before final verification, split the implementation into:

- `tools/bom_common.py` for schemas, bounded value/path/JSON helpers, and shared data types;
- `tools/bom_sbom.py` for Cargo lock/metadata normalization and build-surface policy;
- `tools/bom_cbom.py` for cryptography registry and SBOM binding;
- `tools/generate_bom.py` for fixed subprocess capture, confined report I/O, CLI wiring, and compatibility re-exports used by tests.

The split must preserve report bytes, fingerprints, CLI behavior, error posture, and the existing focused tests. No protocol or dependency change is authorized by this refactor.

### Summary

Implemented a deterministic source SBOM and cryptography CBOM lane for both Cargo workspaces. The final repository inventory contains:

- 22 unique source components;
- 58 scope-qualified dependency edges;
- 5 repository packages with normalized relative manifest paths;
- 3 reviewed `custom-build` components (`getrandom 0.4.3`, `libc 0.2.186`, and `libfuzzer-sys 0.4.13`);
- zero proc-macro components;
- one implemented SHA-256 CBOM component binding four exact implementation/support packages and three protocol domains.

The first live replay falsified an existing review statement that the root SHA-256 closure had no build script. Cargo metadata identifies a `custom-build` target for `libc 0.2.186`. The SHA-256 and libFuzzer dependency reviews now record the exact observed build surface, and `supply-chain/build_surface.json` makes future drift fail closed.

### Files changed

- `.github/workflows/ci.yml`;
- `CONFORMANCE_MATRIX.json`;
- generated `PACKAGE_MANIFEST.json`;
- `docs/DEPENDENCY_POLICY.md`;
- `docs/dependency-reviews/sha2-0.11.0.md`;
- `docs/dependency-reviews/libfuzzer-sys-0.4.13.md`;
- `supply-chain/build_surface.json`;
- `supply-chain/cryptography.json`;
- `tools/bom_common.py`;
- `tools/bom_sbom.py`;
- `tools/bom_cbom.py`;
- `tools/generate_bom.py`;
- `tools/tests/test_bom.py`;
- this work log.

### Typed statements/APIs changed

No Rust or protocol API changed. Added the tooling APIs described in the design packet plus `apply_build_surface_policy`. The CLI retains fixed root/fuzz capture and writes only target-local reports.

### Invariants added or preserved

- exact lock checksum, component, edge, workspace-scope, target-kind, build-surface, crypto-package, protocol-domain, evidence-reference, and output-path checks described above are implemented;
- distinct Cargo package IDs cannot collapse when host paths are sanitized;
- recognizable cryptography-named Cargo packages must have CBOM ownership;
- repeated repository generation is byte-identical;
- the modular split preserved the final SBOM fingerprint exactly;
- module nonblank lines are 71 (`bom_common`), 449 (`bom_sbom`), 214 (`bom_cbom`), and 141 (`generate_bom`), all below the preferred 400-line target except the cohesive Cargo graph module, which remains below the 700-line review trigger.

### Disaster states addressed

- omitted transitive/checksum/build/proc-macro inventory;
- root/fuzz scope confusion;
- unreviewed executable build-surface drift;
- crypto implementation/domain/parameter drift;
- stale or fabricated review references;
- host-path and timestamp nondeterminism;
- source inventory overclaimed as a standard, artifact, provenance, or audit receipt.

### Tests added

Twelve focused Python tests cover deterministic ordering, exact checksums, scope and edge retention, executable target discovery, empty/missing graphs, malformed/missing checksums, duplicate locks, sanitized local-package collisions, build-surface policy exactness, CBOM dependency/reference binding, duplicate crypto identities/domains, unregistered crypto packages, duplicate JSON keys, and report-path confinement.

The initial test-first replay failed with `ModuleNotFoundError: tools.generate_bom`. The focused suite passed after implementation and after the responsibility split.

### Mutants killed

No Python mutation engine is configured, so no BOM-specific mutation score is claimed. The combined shared Rust tree replay tested 302 mutants: 239 caught and 63 unviable, with zero missed mutants or timeouts. That campaign does not test the Python BOM guards.

### Formal/model evidence

No formal obligation applies to the Class B BOM logic. The combined shared Rust tree replay verified all 8 Kani harnesses with zero failures. Kani reported existing x87/sse2 future warnings, `sha2` future incompatibility, and unsupported constructs; completed verification succeeded because those constructs were unreachable in the harnesses. This is bounded Rust evidence and does not verify BOM completeness or third-party source correctness.

### Commands run and exact results

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s tools/tests -p 'test_bom.py' -v` before implementation | failed: `ModuleNotFoundError: tools.generate_bom` |
| same focused command on the final hardened tree | passed 19 tests |
| `python3 -m unittest discover -s tools/tests -v` | passed 73 tests |
| `python3 -m py_compile tools/bom_common.py tools/bom_sbom.py tools/bom_cbom.py tools/generate_bom.py tools/tests/test_bom.py` | passed |
| `python3 tools/generate_bom.py --sbom target/zrm-sbom.json --cbom target/zrm-cbom.json` | passed: 22 components, 58 edges, 1 cryptography component |
| two consecutive BOM generations plus `cmp` on both reports | passed; byte-identical SBOM and CBOM |
| `python3 tools/check_complexity.py --report target/complexity-report.json` | passed: 22 Rust files, 192 functions, 0 advisories, 0 exceptions |
| `python3 tools/check_code_quality.py --report target/code-quality-report.json` | passed: `excellent-candidate`, technical AI review complete, 16 rules, 5 decisions, 0/0 complexity advisories |
| `python3 tools/check_architecture.py` | passed exact internal/external allowlists |
| `python3 tools/check_conformance.py` | passed 45 obligations, live anchors, promotion states, and acyclic dependencies |
| `python3 tools/check_repository_hygiene.py` | passed context, secret, source, mode, size, and action-pin checks |
| `python3 tools/check_package_manifest.py` | passed after generated manifest refresh |
| `cargo fmt --all -- --check` | passed |
| `cargo metadata --format-version 1 --locked --no-deps` | passed for 4 workspace crates |
| `cargo check --workspace --all-targets --all-features --locked` | passed |
| `cargo clippy --workspace --all-targets --all-features --locked -- -D warnings` | passed |
| `cargo test --workspace --all-features --locked` | passed 70 tests, 0 failed |
| `cargo test --workspace --doc --locked` | passed; 4 crates, 0 doctests |
| `cargo doc --workspace --no-deps --locked` | passed |
| `python3 vectors/independent_python/replay_resource_wire_v1.py --check` | passed 6 binary artifacts and 4 protocol digests |
| `cargo +nightly-2025-03-02 llvm-cov --workspace --all-features --locked --branch --json --output-path target/llvm-cov-branch.json` plus both coverage checks | passed: workspace 98.48% lines / 98.94% branches; `zrm-policy` 99.70% lines / 100.00% branches |
| `cargo mutants --workspace --timeout 10 --build-timeout 60 --jobs 2 --output target/mutants-quality-supply-chain-followup` | passed: 302 tested, 239 caught, 63 unviable, 0 missed/timeouts |
| `cargo kani --workspace` | Kani 0.60.0; 8/8 harnesses verified, 0 failures |
| `cargo +nightly-2025-03-02 miri test --workspace --all-features --locked` | passed all 70 tests and 4 empty doctest suites |
| `cargo audit` | exit 0; loaded 1,159 advisories and reported no vulnerability for 13 root dependencies |
| `cargo audit --file fuzz/Cargo.lock` | exit 0; loaded 1,159 advisories and reported no vulnerability for 22 fuzz dependencies |
| `cargo +1.88.0 deny check` | advisories, bans, licenses, and sources all `ok` |
| `cargo +1.88.0 deny --manifest-path fuzz/Cargo.toml check` | advisories, bans, licenses, and sources all `ok` |
| `python3 fuzz/generate_corpus.py --check` | passed resource boundary and 3 policy-cost seeds |
| both configured cargo-fuzz targets with fixed seed and `-runs=3` | passed; no crash, panic, hang, or artifact |
| `git diff --check` | passed |

### Canonical hashes/vectors changed

No protocol hash, vector, domain, or authority byte changed. Tooling-only report identities from the final replay are:

- SBOM inventory: `6d0358f6a2e32440a6657a3c3a5c305e7d50114188b1abdf3002a2f9a4f6205a`;
- build-surface policy: `338fe86392f8afac107d7a4b7aebe0c8479bcf0b0d86e90e45e13469970f19e6`;
- CBOM inventory: `36dd0454a7f65d7e361efc749bb96fe0fde705101161b42b59180f30980dbc8c`;
- cryptography registry: `c128ea189e16381cd8687f77962d7a6a96a73d888db50956055835bc2089950c`.

### Dependencies changed

No external dependency was added: no Python package, Cargo crate, action, feature, external build tool, or network service. The slice adds repository-local Python standard-library BOM tooling.

### Performance/resource-bound impact

The generator performs two locked offline Cargo metadata calls, bounded one-megabyte reads, linear normalization over 22 components and 58 edges in the current closure, constant-count policy validation, and two target-local JSON writes. It has no runtime or protocol performance effect.

### Remaining gaps and non-claims

- technical AI review of the policy records and corrected build-surface statements is complete; human review receives their confirmed coverage, exact gate results, gaps, and non-claims;
- hosted CI has not yet replayed the new BOM command;
- cargo-vet remains deliberately unconfigured until maintainers select trust criteria and reviewed audits/imports;
- the reports are ZRM-native source inventories, not SPDX/CycloneDX, compiled-artifact, OS/container, signed provenance, SLSA, reproducibility, or vulnerability-freedom evidence;
- cryptography package recognition is conservative and must be extended when proof, signature, TLS, hardware, or OS cryptography enters scope;
- local tests and metadata do not establish third-party source authenticity, build-script safety, or production readiness.
