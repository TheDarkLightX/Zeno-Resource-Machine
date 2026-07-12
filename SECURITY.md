# Security Policy

## Project status

Zeno Resource Machine is currently **pre-alpha specification work with reviewed repository-local WP0 controls, a reviewed WP1 canonical-codec slice, and an unreviewed pre-RFC WP2 policy-model candidate**. There is no supported production release, and no implementation in this repository is claimed safe for funds, legal rights, model-training authority, physical resources, or safety-critical use.

The repository's public security posture is fail-closed:

- absence of evidence is not evidence of safety;
- a local test is not production evidence;
- a proof artifact is not authority until the expected verifier, statement, policy, and release identity are independently checked;
- a data commitment is not an availability guarantee;
- computational integrity is not a privacy claim;
- a digital attestation is not physical-world truth.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/TheDarkLightX/Zeno-Resource-Machine/security/advisories/new) when enabled for this repository. If the private form is unavailable, open only a metadata-free issue requesting a private maintainer contact. Do not place exploit details, secrets, keys, accepted malformed proofs, or reproducible state-corruption paths in a public issue.

A useful report includes:

- affected revision, tag, or artifact digest;
- affected crate/module/function;
- threat actor and prerequisites;
- exact statement or invariant violated;
- minimal deterministic reproduction;
- accepted/rejected outputs and state roots;
- whether reject-is-no-op fails;
- impact on funds, authority, privacy, availability, replay, or release integrity;
- suggested mitigation, if known;
- whether the issue is already public.

Do not send live private keys, production secrets, or personal data. Use synthetic fixtures.

## Vulnerability classes of special interest

Critical reports include:

- double consumption, duplicate reward, or nullifier bypass;
- resource existence or membership bypass;
- unauthorized mint, burn, transform, revoke, or reward;
- proof/signature accepted under wrong program, key, profile, statement, policy, domain, or release;
- raw metadata or caller booleans creating verified authority;
- reject path mutating committed state;
- split commit between application state, replay state, journal, or rewards;
- stale plan or concurrency race allowing two commits;
- canonical encoding collision, parser differential, duplicate-key ambiguity, or hash omission;
- overflow, truncation, sign conversion, unit confusion, or rounding that changes semantics;
- state-root or journal mismatch accepted;
- proof-tree grouping changing canonical semantic identity unexpectedly;
- unavailable data represented as available;
- transparent computation represented as zero knowledge or private;
- reproducibility or provenance claims that can be forged;
- unsafe Rust/FFI path exposing undefined behavior to safe callers;
- denial of service before byte/count/depth/resource limits apply;
- leakage of witnesses, keys, private resource data, or sensitive diagnostics.

Default diagnostic formatting must not disclose complete opaque identifiers,
roots, commitments, nonces, or fixed-width resource-wire candidate fields.
These values use constant redaction rather than fingerprints because even a
truncated value permits correlation. Explicit raw-byte access is
security-sensitive protocol code and must not be copied into logs or public
evidence.

## Coordinated disclosure

The maintainers should:

1. acknowledge receipt;
2. assign a private tracking identifier;
3. reproduce or explain why reproduction is not yet possible;
4. classify affected claims and releases;
5. revoke or downgrade affected evidence immediately when soundness is uncertain;
6. develop a fix and regression evidence;
7. rotate verifier, policy, key, or release identities where necessary;
8. publish an advisory and affected-version range after remediation or coordinated disclosure;
9. update the CBC matrix, claims, non-claims, and replay artifacts.

No response-time guarantee is made while the project is pre-alpha.

## Security boundaries

The ZRM semantic core does not itself secure:

- the host operating system;
- compiler or linker correctness;
- proof-system cryptographic assumptions;
- key custody;
- consensus/finality;
- data availability;
- network privacy;
- oracle truth;
- physical attestations;
- application-specific resource logic.

Each integration must define its own trusted computing base, authority roots, revocation path, incident plan, and non-claims.

## Security testing policy

Good-faith testing is welcome when it:

- uses local or explicitly authorized systems;
- avoids privacy violations, service disruption, and data destruction;
- does not access third-party accounts or infrastructure;
- reports exploitable findings privately;
- preserves enough evidence for deterministic reproduction.

The project does not authorize testing of unrelated systems, chains, services, or users.

## Supported versions

None. Until the first signed release, every commit and artifact is experimental and may be incompatible or revoked.
