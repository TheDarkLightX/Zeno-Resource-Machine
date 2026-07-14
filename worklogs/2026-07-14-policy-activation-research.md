# Policy activation research and executable oracle

**Date:** 2026-07-14  
**Task:** `ZRM-TASK-001`  
**Change class:** B research/oracle tooling plus candidate Class E architecture  
**Author:** Dana Edwards  
**Drafting and research assistance:** GPT-5.6

## Goal

Turn the draft policy lifecycle into one small executable sequential object before any authenticated policy registry, final resource, trusted context, persistence, or commit implementation is attempted.

## Literature reviewed

Primary sources covering declarative authorization, revocation, responsibility separation, credential attenuation, reconfiguration, linearizability, rollback and fast-forward attacks, authenticated snapshot history, and irreversible state protocols are summarized in:

```text
docs/research/POLICY_ACTIVATION_V1_LITERATURE_REVIEW.md
```

## Architecture selected for review

- distinct policy content, activation, and snapshot identities;
- minimal stored activation status `Usable | HardRevoked`;
- current/predecessor disposition derived from explicit selection;
- one explicit `Enabled | Suspended` row per recognized kind;
- inert policy-content registration;
- closed command algebra for register, activate, suspend, and predecessor revocation;
- explicit retirement on replacement and suspension;
- current revocation only through atomic replacement or suspension;
- activation identity binds exact governance command digest, including retirement semantics;
- exact successor versions and parent-linked snapshots;
- exact replay before freshness, plus operation-ID non-equivocation;
- rejection returns the exact input snapshot.

## Files added

```text
docs/POLICY_ACTIVATION_V1_ARCHITECTURE.md
docs/research/POLICY_ACTIVATION_V1_LITERATURE_REVIEW.md
formal/state-machine/policy_activation_v1/README.md
reference_models/policy_activation_v1.py
reference_models/policy_activation_v1_counterexamples.json
reference_models/policy_activation_v1_explorer.py
reference_models/tests/test_policy_activation_v1.py
worklogs/2026-07-14-policy-activation-research.md
```

The delegation task remains `architect_required`; RFC approval, canonical identities, governance authorization, and independent review remain open.

## Executable evidence

The isolated candidate model and tests were run with the Python standard library only. Result:

```text
28 tests passed
```

The deterministic explorer result was:

```text
states=305
applied=304
rejected=271
replay_checks=608
max_depth=3
```

This evidence is finite and authoring-track only. Hosted repository gates and an independent oracle/review remain required.

## Important design improvement found during audit

The first activation-ID sketch bound the parent snapshot, operation label, content, kind, and generation. The final candidate instead binds the exact governance command digest. This directly commits activation provenance to all command fields, including whether the old current activation became a predecessor or was hard-revoked, and avoids relying indirectly on a separate operation-label lookup.

## Open decisions

- RFC-0001 approval;
- canonical policy-content bytes and content identity;
- canonical governance-command bytes and digest;
- canonical activation-ID preimage and domain separator;
- canonical snapshot and replay bytes;
- governance authorization and threshold roles;
- authenticated snapshot construction and loading;
- global non-equivocation or finality profile;
- independent semantic and authority-boundary review;
- Lean/ESSO execution of the formal packet.

## Non-claims

No Rust authority path, canonical protocol identity, policy activation, final resource, trusted context, state membership, persistence, commit, conformance promotion, security audit, release, or production claim is added.
