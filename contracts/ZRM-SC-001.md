# ZRM-SC-001 — Canonical data and derived identities

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

Successful completion may create:

- a canonical typed protocol object;
- a domain-separated commitment, root, hash, or identifier derived from that object;
- evidence that the accepted bytes have exactly one interpretation under the selected schema.

It does **not** establish policy validity, state membership, authorization, freshness, acceptance, privacy, data availability, or durable commit.

## Inputs

### Untrusted

- transport bytes;
- decoded field candidates;
- caller-supplied IDs, hashes, roots, lengths, tags, versions, and counts;
- transport-library objects or diagnostic JSON.

### Governed

- supported schema version;
- object tag and exact field table;
- protocol and policy byte/count/depth limits;
- fixed hash suite or explicitly bound `CryptoSuiteId`;
- domain-separation strings and canonical empty roots.

### Derived

- canonical bytes;
- object/list roots;
- content-derived IDs and hashes;
- canonical lengths and counts.

## Preconditions and invariants

1. Raw byte, count, and nesting limits are checked before allocation or recursive parsing.
2. Decoding is strict: wrong magic, version, object tag, field count, tag order, field length, option tag, truncation, duplicate field, unknown critical field, or trailing bytes rejects.
3. Accepted bytes satisfy:

   ```text
   encode(decode(bytes)) = bytes
   ```

4. Consensus and authority hashes use the manual normative encoder, never struct layout, Serde, diagnostic JSON, host endianness, locale, or map iteration.
5. Every variable-length field and list uses the specification's explicit framing.
6. Each semantic object and list uses its own domain string. A domain string is never reused with different bytes or meaning.
7. All-zero IDs and commitments reject except for a specification-named domain-separated empty root.
8. A caller-supplied derived value is checked against recomputation and never becomes authoritative merely because its width is correct.
9. Public APIs use semantically distinct newtypes. A `PolicyId`, `ResourceId`, `Commitment`, and `VerifierPolicyId` are not interchangeable byte aliases.
10. Canonical-byte provenance is represented by a sealed type or by an API that cannot be called with arbitrary raw bytes. Raw hashing helpers remain private or explicitly non-authoritative.
11. Schema downgrade, cross-version reinterpretation, and noncanonical alternative encodings reject.
12. Full opaque values and nonces are not emitted by default `Debug`; diagnostics use redaction or bounded fingerprints unless an explicit disclosure API and profile permit full output.

## Required postconditions

- The result is the unique canonical value for the accepted bytes and schema.
- Every derived identifier matches the exact documented preimage.
- No untrusted byte sequence that failed canonical decoding receives an authoritative identity.
- Failure creates no trusted type and performs no state mutation.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| A correctly sized random byte array is passed to a function named “canonical wire hash” | Cannot compile through the authoritative API, or rejects after strict decode |
| Same payload under another object's domain | Different hash; substitution rejects |
| Fields reordered but individually valid | Canonical-decode rejection |
| Duplicate map/list key | Rejection, never silent deduplication |
| Unknown critical field | Rejection |
| Valid object plus one trailing byte | Rejection |
| Caller supplies a different `ResourceId` for the same resource bytes | Recomputed mismatch rejection |
| Diagnostic JSON round-trip changes field order or precision | Cannot affect authority identity |
| All-zero identifier | Constructor rejection |
| Full nonce appears in ordinary debug logs | Review failure |

## Required evidence

- independent byte and hash vectors;
- one-field mutation matrix;
- malformed, truncation, trailing, duplicate, version, and ordering tests;
- parser fuzzing;
- bounded model checking for lengths and arithmetic where applicable;
- cross-language or separately authored replay;
- compile-fail/API test showing arbitrary raw bytes cannot impersonate sealed canonical bytes;
- diagnostic redaction tests.

## Non-claims

Canonicality does not imply semantic validity, policy authorization, state membership, availability, privacy, or commit.

## Specification anchors

Sections 5.5, 10, 11, 12, 13.3, 13.6, and 26.
