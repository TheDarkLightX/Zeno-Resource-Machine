# Dependency and toolchain policy

Runtime dependencies are exact-pinned and default features are disabled unless a dependency review justifies them. Each direct dependency has a review under `docs/dependency-reviews/` covering purpose, alternatives, licenses, build scripts, proc macros, native code, unsafe surface, enabled features, transitive closure, determinism, and removal.

Required local and CI checks are:

```text
cargo metadata --format-version 1 --locked
cargo audit
cargo deny check
```

`cargo vet` is planned after maintainers select and review trusted audit imports. Until then, absence of a vet policy remains an explicit WP0 gap rather than an implied audit.

The semantic workspace uses Rust `1.87.0`. Fuzzing and Miri use `nightly-2025-03-02`. Kani is pinned to `0.60.0`. `cargo-deny 0.20.2` uses Rust `1.88.0` because older releases cannot parse current CVSS v4 advisory records; this tooling compiler does not build ZRM runtime artifacts. Moving aliases such as `stable` and `nightly` are forbidden in evidence commands.
