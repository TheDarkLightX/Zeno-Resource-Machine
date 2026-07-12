# Security and correctness review remediation, July 2026

**Status:** RFC-0003 accepted; implementation reviewed but unpromoted

This register records the disposition of six findings against the pre-alpha
ZRM slice. Dana Edwards accepted RFC-0003 on 2026-07-12 after technical review.
That decision fixes the pre-authority semantics below; it does not establish a
governed authority path or make ZRM production-ready.

## Finding register

| ID | Affected boundary | Confirmed behavior | Remediation candidate | Residual risk/status |
| --- | --- | --- | --- | --- |
| ZRM-01 | Resource-kind policy dimensions | Zero was accepted in four accounting modes; lifecycle maxima were unconstrained | Zero rejects under every v1 policy; `EvidenceOnly` grants no exception; lifecycle maximum is canonically one | RFC-0003 accepts the exact lifecycle maximum; marker resources remain unsupported and require a future versioned rule |
| ZRM-02 | Verifier-cost planning | A caller-selected same-backend row could produce a zero quote independent of `rows_root` | Default public quote/request/result surface removed; arithmetic retained only as internal or fuzz assurance helper; architecture gate blocks named reintroduction | Governed canonical rows, root, model identity, internal lookup, activation, and dispatch plan remain unimplemented |
| ZRM-03 | Verifier policy/admission | A copied policy ID with altered sensitive content could pass partial structural checks | Default public compatibility/admission success surface removed; internal counterexample retained; architecture and compile-fail gates enforce quarantine | Content-derived/authenticated policy identity, registry membership, production mode, program/key/release, revocation, trusted epoch, and public-I/O ceilings remain unimplemented |
| ZRM-04 | Resource-ID derivation | Public raw helper hashed any 595/603-byte slice into typed `ResourceId` | Raw typed derivation removed; canonical codec privately hashes its own encoding; exact vectors preserved; malformed same-length bytes have no supported public typed path | Callers can independently compute or construct inert identifier bytes; later semantic admission must recompute the canonical ID |
| ZRM-05 | Diagnostic privacy | Opaque values and raw 32-byte wire candidates printed complete bytes, including nonce | All opaque 32-byte values use constant redaction; `ResourceWireV1` manually redacts every 32-byte array candidate; nested intrinsic formatting is nonce-value-independent | Numeric wire scalars remain visible; future artifacts, witnesses, private state, errors, log sinks, and evidence bundles need separate disclosure review and zeroization where applicable |
| ZRM-06 | Semantic/governance review | Strong automation could encode the wrong oracle; one visible CODEOWNER cannot prove independent review | Independent implementation/oracle/adversarial tracks, counterexample review, semantic-change declarations, authority map, and stronger branch-protection requirements added | RFC-0003 received maintainer semantic approval; static files cannot prove live host settings or organizational independence, and remaining authority changes plus production still require their applicable reviews and external audit |

## Counterexamples retained

### Implicit marker resource

```text
mode = EvidenceOnly
quantity = 0
maximum = 1
expected = reject: ZeroQuantityForbidden
```

Lifecycle quantity zero retains the more specific lifecycle error after unit
matching because lifecycle exact-one precedes the general zero check.

### Cost-row substitution

```text
model.rows_root = committed_nonzero_candidate
external_row.backend = expected_backend
external_row.coefficients = [0, 0, 0, 0]
old internal arithmetic result = 0
required external result = no callable quote API
```

The internal counterexample remains a test so later code cannot forget why
registry-owned selection is required.

### Policy-content substitution

```text
candidate.policy_id = expected_id
candidate.program_or_key_digest = changed
candidate.proof_mode = Test
candidate.schema/parameter/release fields = changed
old partial shape result = success when checked subset still matched
required external result = no callable admission/compatibility success API
```

The final governed registry must reject each field mutation after binding exact
canonical content and active membership.

### Same-length malformed resource bytes

```text
length = 595
magic/tag/field-length/option encoding = malformed
expected = strict decoder rejects; no public raw-byte typed-ID operation exists
```

### Diagnostic nonce variation

```text
resource A nonce != resource B nonce
expected default Debug nonce representation = identical constant redaction
```

## Accepted review decision

The prior specification required lifecycle resources to have quantity one but
did not explicitly require a lifecycle policy maximum of exactly one. This
remediation adopts that constructor invariant because zero creates an
uninhabited policy and larger maxima are redundant for a fixed-quantity mode.
It narrows the accepted pre-alpha policy-candidate state space and changes a
public exhaustive error enum. RFC-0003 acceptance approves that semantic and
source-compatibility change.

That approval also confirms these associated choices:

- non-lifecycle maximum zero remains a constructible empty policy candidate;
  the amendment canonicalizes the fixed lifecycle mode and does not introduce
  a general policy-inhabitation rule;
- constructor precedence is schema version, validity-window shape, then the
  lifecycle maximum;
- after unit matching, lifecycle quantity zero reports the more specific
  lifecycle exact-one failure before the general zero failure;
- no persisted-policy or canonical-byte migration exists because neither policy
  bytes nor an authority activation path have been frozen or implemented.

The accepted implementation and specification retain the canonical lifecycle
maximum, its constructor guard, and its deterministic error. Any later change
requires a new versioned semantic decision and compatibility analysis.

## Promotion boundary

This remediation is sufficient only to continue experimental development with
the identified public misuse paths closed. It does not authorize final resource
admission, proof dispatch, value transfer, state mutation, or production use.
Those paths remain blocked on the authenticated policy/cost/registry ABI and
the later state, exact-once, accounting, and atomic-commit work packages.
