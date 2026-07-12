# RFC-0002: Pre-authority API quarantine and boundary hardening

**Status:** Review
**Authors:** ZRM maintainers, implementation prepared for review
**Reviewers:** Two independent reviewers required, including one authority-boundary reviewer
**Created:** 2026-07-12
**Target version:** pre-alpha v0.1 candidate surface
**Change class:** E

## Summary

This RFC removes public operations that can turn caller-selected verifier rows,
policy identifiers, or arbitrary same-length bytes into authority-shaped typed
results before ZRM has an authenticated policy and verifier registry. It also
defines the immediate version-one zero-quantity rule and constant-redacted
diagnostic formatting for opaque and 32-byte wire values. Canonical
resource bytes and expected resource identifiers remain unchanged.

## Motivation

The current pre-RFC policy model exposes deterministic arithmetic and structural
compatibility checks as public methods. Those methods are documented as inert,
but a future consumer could mistake their successful return values for governed
cost or verifier admission. The public resource hash helper likewise accepts
any byte string having one of two valid lengths, even though its name implies
canonicality. The policy-bound resource check accepts zero quantity for four of
five accounting modes, while the version-one policy schema has no field that
can explicitly authorize marker resources. Default `Debug` output also reveals
complete opaque identifiers, roots, commitments, resource nonces, and 32-byte
resource-wire candidate arrays.

These are unsafe boundaries to carry into final resource admission, verifier
dispatch, persistence, or commit work.

## Goals

- Reject zero quantity under every version-one resource-kind policy.
- Canonicalize the lifecycle non-fungible maximum to exactly one atom.
- Prevent external callers from producing a checked quote from a selected cost
  row or an admission-like success from candidate policy identity.
- Make the canonical codec the sole supported public typed resource-ID path.
- Prevent default diagnostic formatting from disclosing opaque identifiers,
  roots, commitments, nonces, or 32-byte resource-wire candidate arrays.
- Preserve exact resource-wire bytes, hashes, vectors, and nullifier semantics.

## Non-goals

- Define canonical policy or verifier-policy bytes.
- Define cost-row hashing, a rows-root tree, model-ID derivation, registry
  membership, activation, revocation, release binding, or trusted epoch.
- Implement verifier dispatch or construct a verified fact.
- Define zero-quantity marker resources.
- Claim that static repository files enforce live host reviewer settings.

## Current behavior

- `ResourceKindPolicyV1::validate_dimensions` checks unit, lifecycle quantity,
  and maximum, but accepts zero in non-lifecycle modes.
- Lifecycle policy candidates may declare any `quantity_max`, even though the
  only accepted lifecycle resource quantity is one.
- A caller can select a `VerifierCostRowV1` independently of a model's opaque
  `rows_root` and obtain a public quote.
- Candidate verifier compatibility checks compare only a subset of
  authority-relevant fields and accept a caller-selected epoch.
- A public crypto helper hashes any 595-byte or 603-byte slice into a typed
  `ResourceId`.
- `Debug` prints all 32 bytes of opaque values, including `ResourceNonce`, and
  raw resource-wire formatting prints every 32-byte candidate array.

## Proposed semantics

### Resource dimensions

The version-one profile has no zero-marker permission field. Quantity zero is
never accepted. Its exact typed rejection follows the fixed precedence:

```text
LifecycleNonFungible quantity == 0
  -> LifecycleQuantityMustBeOne
every other accounting mode quantity == 0
  -> ZeroQuantityForbidden
```

Validation precedence remains:

```text
unit mismatch
  -> lifecycle quantity is not one
  -> zero quantity
  -> quantity exceeds maximum
  -> accept
```

Lifecycle policy construction additionally requires:

```text
accounting_mode == LifecycleNonFungible -> quantity_max == 1
```

A future marker-resource rule requires a new versioned policy field and RFC. It
cannot be inferred from `EvidenceOnly` or any other accounting mode.

This is a fixed-mode canonicalization rule, not a general policy-inhabitation
rule. A non-lifecycle candidate with `quantity_max = 0` may still construct but
admits no positive quantity. Disabling and activation semantics remain future
governed-policy work. Constructor rejection order is schema, validity-window
shape, then lifecycle maximum; resource-dimension order is the sequence above.

### Verifier-cost and candidate compatibility quarantine

The existing arithmetic and shape predicates remain internal implementation
and assurance helpers. Default external consumers cannot call them and cannot
receive their quote or admission-like success values.

The coverage-guided cost target receives one `cfg(fuzzing)` public assertion
sink taking raw bytes and returning `()`. It constructs all candidate rows,
models, policies, requests, and quotes internally, performs no I/O or authority
transition, and exposes no quote, cost, policy decision, or capability. The
architecture gate exact-allowlists this exceptional surface and its unit-return
signature. A pinned compiler-derived, canonical span-free rustdoc JSON
projection independently binds the complete `zrm-policy` public API under both
default and `cfg(fuzzing)` profiles without binding checkout or Cargo-home
paths. Conditional compilation across every `zrm-policy` source is limited to
the reviewed `test`, `kani`, and `fuzzing` profiles so `cfg(doc)` cannot hide a
default-build API from rustdoc. This scan handles outer and inner attributes,
Rust comments, and raw attribute identifiers. Policy `path` attributes are
exact-allowlisted and must resolve to regular files inside the complete scanned
policy source tree. Linked source directories, source inclusion, and unreviewed
macro definitions or invocation paths fail closed. Macro imports, aliases, glob
imports, and protected-root shadowing are rejected. Digest updates require
Class E review.

The future governed interface must have this shape:

```text
authenticated active policy bundle
  -> authenticated canonical cost model
  -> internal backend-row selection
  -> bounded quote reservation
  -> exact verifier/program/key/release dispatch
  -> sealed verified fact
```

No public compatibility shim returns success. Documentation, deprecation, or a
copied identifier is insufficient quarantine.

### Resource-ID boundary

`ResourceWireV1::resource_id()` is the supported public typed derivation. The
exact raw hash operation is private to the canonical codec boundary. External
callers cannot pass arbitrary same-length bytes to a ZRM API that returns a
typed `ResourceId`.

This does not claim that Rust can prevent a caller from independently computing
SHA-256 or constructing inert nonzero identifier bytes. Later semantic
validation must still recompute and compare the canonical identifier before
granting resource authority.

### Diagnostic privacy

Every opaque 32-byte identifier, root, commitment, and nonce uses
type-labeled, constant-redacted `Debug` output. Raw `ResourceWireV1` formatting
redacts every 32-byte candidate array, including the nonce. Nested resource
values inherit that redaction. Numeric quantity, epoch, optional expiry, and
flag candidates remain visible. Explicit byte accessors remain available for
narrowly scoped protocol code.

## Typed interfaces

Removed or narrowed from the default external API:

```text
VerifierCostModelV1::compute_quote(caller_row, request)
VerifierPolicyV1::cost_quote_request(...)
VerifierPolicyV1::admission_reservation_quote_request()
MachinePolicyV1::validate_verifier_candidate_compatibility(candidate, caller_epoch)
MachinePolicyV1::validate_admission_verifier_candidate(candidate, caller_epoch)
VerifierCostQuoteRequestV1
VerifierCostQuoteV1
VerifierCompatibilityErrorV1
derive_resource_id_from_canonical_wire(raw_bytes)
HashConstructionError::InvalidResourceWireLength
ResourceIdDerivationError::Hash(HashConstructionError)
```

The codec-owned replacement exposes
`ResourceIdDerivationError::{Encode, HashFrameLengthOverflow, AllZeroDigest}`.
This is a pre-alpha exhaustive-enum source break. Default `Debug` text for all
opaque 32-byte types and `ResourceWireV1` 32-byte array fields also changes
from complete bytes to constant redaction.

Added fail-closed policy errors:

```text
ResourceDimensionErrorV1::ZeroQuantityForbidden
PolicyValidationErrorV1::LifecycleQuantityMaximumMustBeOne
```

Both additions change public exhaustive enums and therefore are deliberate
pre-alpha source-compatibility breaks.

The exact Rust visibility and test-only helper placement are implementation
details, provided no default external path can obtain the quarantined result.

## Authority and trust boundary

- Untrusted inputs: all current machine, resource-kind, verifier, row, model,
  byte, epoch, and identifier candidates.
- Authenticated facts: none added.
- Governing policy: none activated by this RFC.
- Commit authority: none.
- Revocation/rotation: unresolved and required before dispatch.
- Trusted computing base: canonical codec and closed hash implementation for
  inert resource-ID derivation; existing Rust toolchain and SHA-256 dependency.

## Canonical encoding and hashing

There is no canonical encoding or domain change. Both frozen `ResourceWireV1`
encodings and resource-ID vectors must replay exactly. The implementation owner
of the private resource-wire hash operation may move between crates without
changing:

```text
domain = "zrm.resource.v1"
outer frame = u16_be(domain_len) || domain || u32_be(payload_len)
payload = u32_be(canonical_wire_len) || canonical_wire
hash = SHA-256
```

## Accounting and resource effects

No resource is consumed, referenced, or created by these helpers. Zero
rejection narrows future policy-bound resource admission. It does not mutate
state and it does not change canonical wire decoding.

## State, concurrency, and atomicity

No state, concurrency, persistence, or commit behavior is introduced.
Rejection remains side-effect free.

## Privacy and disclosure

Opaque and 32-byte resource-wire candidate diagnostics are redacted.
Scalar quantity, epoch, optional expiry, and flag candidates remain visible.
This RFC does not establish transaction privacy, unlinkability, witness
secrecy, zeroization, or log-sink security.

## Data availability and external attestations

No change. A commitment or identifier does not establish data availability or
external truth.

## Resource and performance bounds

The dimension check adds one constant-time integer comparison. Hash input sizes,
allocation bounds, cost arithmetic bounds, and asymptotic complexity remain
unchanged.

## Security analysis

| Disaster state | Defense | Residual risk | Evidence |
| --- | --- | --- | --- |
| Zero quantity accepted without explicit permission | Policy-bound zero rejection across all modes | Marker semantics remain unavailable | Mode matrix, oracle, Kani, fuzz, mutation |
| Caller substitutes a cheap cost row | Public quote path quarantined | Governed model is unimplemented | External compile-fail plus internal counterexample |
| Copied policy ID substitutes verifier contents | Public candidate admission path quarantined | Registry and exact field binding are unimplemented | External compile-fail plus field-substitution tests |
| Malformed same-length bytes receive typed ID through public helper | Raw helper private to codec | Callers can compute inert bytes independently | API-surface test and exact vectors |
| Opaque or wire candidate leaks through `Debug` | Constant opaque redaction and manual wire formatting for every 32-byte array field | Explicit byte access remains sensitive; scalar candidates remain visible | Direct, wire, and nested non-leak tests |
| Automation encodes the wrong semantic oracle | Counterexample review and independent approvals | Reviewer availability and host enforcement | Worklog, host settings evidence required |

## Alternatives considered

- Keep methods public with warnings or deprecation. Rejected because the
  authority-shaped success remains available.
- Return a substitute `AuthorityUnavailable` from the old methods. Rejected in
  favor of removing the misleading success surface during pre-alpha.
- Implement row-root membership immediately. Rejected because canonical row
  bytes, root construction, activation, and registry trust are unresolved.
- Parse resource wire again inside the crypto crate. Rejected because duplicate
  parsers create differential risk.
- Show a nonce fingerprint. Rejected because it preserves correlation.

## Compatibility and migration

This is a deliberate in-place pre-alpha v1 source and semantic amendment. The
repository has no canonical resource-kind-policy bytes, content-derived policy
identity, persisted or activated policy record, stable public ABI, governed
authority record, or accepted transition to migrate. Therefore, this draft
defines no predecessor-policy translation or wire migration. Downstream
experimental callers must stop using the quarantined methods and must reject
lifecycle maxima other than one. Future callers migrate to governed APIs only
after their separate RFC and evidence are accepted.

If reviewers identify any external durable policy identity or accepted policy
record, the in-place disposition is invalid: this RFC must return to Draft and
define a new schema/version plus replay and migration rules before merge.
Human approval of this disposition and the lifecycle acceptance-set narrowing
is required; implementation and tests cannot approve it.

Rollback is a source revert. Reintroducing any public success path requires an
authenticated authority design and a new Class E review. Canonical wire replay
across versions is unaffected.

## Test and assurance plan

- unit/invariant: all accounting modes, lifecycle maxima, error precedence;
- compile-fail/API surface: quarantined methods and raw hash unavailable;
- property/metamorphic: policy predicate oracle and exact vector stability;
- mutation: missing zero guard, one-mode exemption, row/policy quarantine;
- fuzz: arbitrary modes, quantities, maxima, units, and resource wire defects;
- Kani: full-width quantity/maximum predicate and arithmetic helpers;
- Miri: affected codec, policy, and diagnostic tests;
- review: specification-counterexample pass independent of implementation.

No theorem, fuzz run, or bounded proof is promoted beyond its stated scope.

## Supply-chain and release impact

No new third-party package is required. `zrm-codec` adds a direct edge to the
already locked, feature-minimal `sha2` package so its canonical encoder owns the
private resource-ID hash; `zrm-crypto` retains its direct edge for suite and
nullifier operations. The package set and transitive closure are unchanged.
Release promotion remains blocked on independent Class E review and live host
controls.

## Claim changes

After implementation and review, the repository may claim that the identified
pre-alpha public misuse paths are quarantined and zero quantity is rejected by
the current policy-bound check. It still cannot claim a secure resource machine,
authenticated policy, governed verifier, exact-once state transition, or
production readiness.

## Rollout and rollback

Land as an isolated remediation before any authority-bearing WP4/WP5 work.
Replay exact vectors and downstream compile checks. A rollback must restore no
public authority-shaped success path; if regression forces rollback, authority
integration remains frozen.

## Open questions

- Which future policy version, if any, introduces explicit marker resources?
- What canonical row schema and authenticated model root will govern costs?
- Which registry and release-attestation contract will construct verified facts?
- Which independent identities will enforce the required host-side approvals?

## Decision

Pending two independent reviews and explicit human approval of the in-place
pre-alpha v1 semantic disposition. Implementation may be evaluated on a draft
branch, but no authority integration or release promotion may rely on it until
the RFC is accepted.
