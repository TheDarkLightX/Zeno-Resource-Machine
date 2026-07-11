# Tooling review: cargo-deny 0.20.2

Purpose: enforce advisory, license, source, duplicate-version, and wildcard-dependency policy over both locked Cargo workspaces.

Scope: CI and offline supply-chain assurance only. It does not enter runtime crates or protocol bytes.

Version and compiler: exact tool version `0.20.2`, installed with its published lockfile using exact Rust `1.88.0`. The semantic workspace remains pinned to Rust `1.87.0`. Version `0.18.3` was rejected during local replay because its RustSec parser did not support a current CVSS v4 advisory and failed before evaluating the dependency graph.

Network and trust surface: the tool reads Cargo metadata, registry indices, license files, and the RustSec advisory database. CI grants read access to the checked-out repository and network access only during installation/index refresh. A successful run is dependency-policy evidence, not semantic correctness evidence.

Removal plan: replace only with a reviewed version that parses the active advisory schema and preserves fail-closed root and fuzz-workspace checks.
