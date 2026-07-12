# ZRM authority-transition map

**Status:** normative review aid; implementation status remains governed by
`CONFORMANCE_MATRIX.json`

This map records where data may acquire additional meaning or authority. Every
arrow is a separate review boundary. No arrow may be replaced by a caller
boolean, copied identifier, process exit status, or success from a weaker
stage.

```text
raw bytes
  -> bounded bytes
  -> canonical wire value
  -> policy-independent intrinsic value
  -> role-bound intrinsic value
  -> authenticated active-policy context
  -> policy-validated resource
  -> authenticated proof/authority facts
  -> validated transition
  -> private commit plan
  -> atomic durable commit
  -> accepted canonical journal
```

The first four stages are partially implemented. Authenticated policy,
verifier, transition, state, commit, and accepted-journal stages are not.

## Boundary contracts

| Boundary | Invoker/input | Required evidence | Newly trusted | Still untrusted | Replay/resource defense | Current status |
| --- | --- | --- | --- | --- | --- | --- |
| Raw bytes -> bounded bytes | ingress adapter; attacker-controlled bytes | object-specific byte ceiling before allocation | only the byte bound | syntax, identity, semantics, authority | fixed maximum; rejection allocates or mutates nothing | implemented for `ResourceWireV1` |
| Bounded bytes -> canonical wire | strict decoder | exact magic, version, tags, lengths, order, option encoding, and no trailing bytes | one syntactically canonical value | all semantic field claims | deterministic reject precedence; bounded parsing | implemented for `ResourceWireV1` |
| Canonical wire -> intrinsic value | semantic constructor | nonzero fixed fields and nonce, epoch order, known flags, canonical self-derived ID | policy-independent body consistency | policy validity, membership, state, controller, proofs | fixed field set; checked conversion; no state access | implemented candidate |
| Intrinsic value -> role-bound intrinsic | structural kernel | canonical disjoint role partition contains the resource's internally derived ID exactly once | exact proposed role and ordinal binding | role-list authentication, transition completeness, state membership | bounded counts; duplicate/collision rejection | implemented candidate on WP3c branch |
| Candidate policies -> authenticated active-policy context | governed state/configuration adapter | canonical policy content, content commitment, active-set membership, activation/revocation state, trusted epoch/root/version | exact active machine and child-policy contents | request echoes, network metadata, wall clock | stale-root/version rejection; bounded policy records | unimplemented; Class E ABI required |
| Active policy -> governed verifier/cost model | registry | canonical sorted unique rows, derived model identity, exact verifier-policy content, program/key/release binding, production mode | registry-selected policy and internal cost row | proof artifact and claimed metadata | authenticated roots; revocation; input/output/artifact/cost ceilings | unimplemented; public candidate success APIs quarantined |
| Policy-bound resource -> policy-validated resource | pure semantic kernel | active resource-kind policy, unit, positive quantity, mode-specific rules, validity, allowed logic/controller roots | resource dimensions and policy binding | state existence, controller proof, transition-wide accounting | deterministic total predicate; no mutation | partial predicate only; no sealed final type |
| Artifact -> authenticated fact | governed verifier wrapper | bounded artifact, exact canonical statement, exact program/key/profile/policy/release, cryptographic verification | one sealed fact with exact coverage | facts outside declared coverage; oracle/physical truth | pre-dispatch cost reservation; no fallback/downgrade | unimplemented |
| Resources + facts + state view -> validated transition | pure kernel | existence/freshness, role/ordinal coverage, authority, conservation/transformation, DA policy, statement binding | deterministic acceptance decision | commit success and concurrent freshness | bounded complete fact plan; rejection is no-op | unimplemented |
| Validated transition -> private commit plan | finalizer | exact expected state root/version, read/write footprint, nullifiers, outputs, journal draft, admission reservation | immutable planned effects | durable success | no public constructor; checked cumulative bounds | unimplemented |
| Commit plan -> durable commit | commit port | atomic compare-and-swap on expected root/version and all effects | one committed transition | external finality/consensus unless adapter proves it | exact-once nullifiers; crash recovery; one-winner conflicts | unimplemented |
| Durable commit -> accepted journal | journal constructor after successful commit | durable commit receipt bound to exact draft and post-state | canonical accepted record | privacy, DA, external truth beyond explicit facts | journal/effect atomicity; deterministic root | unimplemented |

## Governed verifier-policy resolution contract

### Authority granted

Permission to treat a verifier result as one specifically typed ZRM fact.

### Attacker-controlled inputs

- requested policy identifier;
- proof or signature artifact;
- public statement bytes;
- claimed backend/program metadata;
- request-provided epoch, mode, limits, or cost coefficients.

### Governed inputs

- canonical verifier-policy contents and content commitment;
- active registry membership and revocation state;
- exact verifier implementation and program/key/release identity;
- proof mode, statement and journal schemas, proof parameters, and coverage;
- canonical cost model and resource limits;
- trusted machine/domain/epoch/state context.

### Required bindings

- Policy identity binds every security-relevant content field.
- Registry membership binds that exact content to current governed state.
- Production authority accepts only the production proof mode.
- Verification binds the artifact to the exact program/key and statement.
- Cost selection comes from the governed model, never caller coefficients.

### Forbidden states

- same policy identifier with different content;
- development/test verifier under production authority;
- wrong program, key, release, codec, schema, parameters, or coverage;
- inactive, expired, stale, or revoked policy;
- caller-selected row or unbounded input/output/artifact;
- successful structural compatibility treated as a verified fact.

## Governed verifier-cost contract

```text
canonical cost rows
  -> exact field validation
  -> sort by backend family
  -> reject duplicate or missing authorized backend
  -> derive each row hash and rows root
  -> derive exact cost-model identity
  -> authenticate active registry membership
  -> seal GovernedVerifierCostModel
```

The sealed model performs internal lookup by the backend selected by a governed
verifier policy. Its quote API accepts lengths and policy-derived bounds, never
external coefficients or an external row. Every multiply/add uses checked
`u128`, fits `u64`, and remains below model, verifier, and transition caps before
expensive dispatch.

## Review method

For each changed boundary, the review packet identifies:

- authority affected;
- attacker-controlled and governed fields;
- new valid and invalid states;
- exact cryptographic, policy, freshness, and resource bindings;
- failure precedence and no-op behavior;
- an independently derived decision table or executable oracle;
- counterexamples attempted and their observed disposition;
- evidence scope and remaining non-claims.

Implementation, oracle, and adversarial-review tracks use separate initial
contexts for Class C-E changes. They may converge only after each track records
its independent artifact. A human maintainer reviews the behavior/evidence
packet. Authority-bearing release still requires the additional independent
review and audit gates in `QUALITY_GATES.md`.
