# Policy activation v1 formalization packet

**Status:** candidate theorem and disaster-model obligations for `ZRM-TASK-001`; no completed proof claim

The executable reference model is:

```text
reference_models/policy_activation_v1.py
```

This packet fixes theorem statements and counterexample targets before a Rust authority implementation exists. The Python artifact is executable finite evidence. Lean and ESSO should be derived from this packet and the approved RFC, not from observed Rust behavior.

## Neutral mathematical model

Let `K` be recognized resource kinds; `C` immutable policy-content identities; `A` activation identities; `O` governance operation identities; `D = {Usable, HardRevoked}`; and `R = {Create, Consume, Reference}`.

A snapshot is:

```text
S = (
  machine,
  domain,
  version,
  parent,
  kinds,
  contents,
  activations,
  selection,
  operations
)
```

with:

```text
contents : C -> optional K
activations : A -> optional (C, K, Nat+, D)
selection : K -> Enabled(A) | Suspended
operations : O -> optional (CommandDigest, Nat+)
```

Derived disposition is:

```text
disposition(S, a) =
  HardRevoked                 if status(a) = HardRevoked
  CurrentCreation             if selection(kind(a)) = Enabled(a)
  AcceptedPredecessor         otherwise
```

The command algebra is:

```text
RegisterContent(content, kind)
Activate(content, kind, retire_current_as?)
Suspend(kind, retire_current_as)
HardRevokePredecessor(kind, activation)
```

The transition function returns:

```text
Applied(S') | AlreadyApplied(S, original_version) | Rejected(S, reason)
```

## Lean tasks

Suggested module split:

```text
ZRM/PolicyActivation/Types.lean
ZRM/PolicyActivation/WellFormed.lean
ZRM/PolicyActivation/Step.lean
ZRM/PolicyActivation/Disposition.lean
ZRM/PolicyActivation/Replay.lean
ZRM/PolicyActivation/Refinement.lean
```

### Data and decidability

1. **`wellFormed_decidable`**  
   Prove `Decidable (WellFormed s)` for finite maps or sorted finite lists.

2. **`disposition_total_on_activation`**  
   For every activation present in a well-formed snapshot, derived disposition is defined.

3. **`disposition_unique`**  
   An activation has exactly one of `CurrentCreation`, `AcceptedPredecessor`, or `HardRevoked`.

4. **`selected_iff_current`**  
   In a well-formed snapshot, `selection k = Enabled a` if and only if `a` has kind `k` and disposition `CurrentCreation`.

5. **`at_most_one_current_per_kind`**  
   Two current activations of one kind are equal.

6. **`suspended_has_no_current`**  
   `selection k = Suspended` implies no activation of kind `k` has disposition `CurrentCreation`.

### Genesis and preservation

7. **`genesis_well_formed`**  
   Under uniqueness and kind-binding assumptions for bootstrap content, genesis is well formed.

8. **`applied_preserves_well_formed`**  
   If `WellFormed s` and `step s c = Applied s'`, then `WellFormed s'`.

9. **`applied_version_successor`**  
   Every applied command produces `s'.version = s.version + 1`.

10. **`applied_parent_exact`**  
    Every applied command sets `s'.parent = SnapshotId s`.

11. **`content_monotone`**  
    Existing content records never change or disappear across an applied command.

12. **`activation_monotone`**  
    Existing activation identity fields never change or disappear.

13. **`generation_contiguous`**  
    Per-kind generations remain exactly `{1, ..., n}` after any reachable applied transition.

14. **`hard_revocation_monotone`**  
    If activation `a` is hard-revoked in `s`, then it remains hard-revoked in every reachable descendant.

15. **`operation_log_monotone`**  
    Successful steps preserve all old replay records and append exactly one new record.

### Failure and replay

16. **`reject_noop`**  
    `step s c = Rejected s' r` implies `s' = s`.

17. **`exact_replay_idempotent`**  
    If command `c` previously applied with operation ID `o` and exact digest `d`, retrying the same command returns `AlreadyApplied` and does not change state.

18. **`operation_id_non_equivocation`**  
    If operation ID `o` is recorded with digest `d`, any command with `o` and digest `d' != d` rejects.

19. **`replay_before_freshness`**  
    Exact replay remains `AlreadyApplied` even if the current snapshot has advanced beyond the command's original expected parent.

20. **`stale_parent_noop`**  
    A new operation whose expected snapshot differs from the current snapshot rejects and is a no-op.

21. **`no_version_fast_forward`**  
    No command controls the successor version; every applied step advances by exactly one.

### Lifecycle authority

22. **`predecessor_no_create`**  
    `AcceptedPredecessor` implies `allowed Create = false`.

23. **`predecessor_existing_use`**  
    At the lifecycle stage only, `AcceptedPredecessor` permits `Consume` and `Reference`.

24. **`hard_revoked_no_use`**  
    `HardRevoked` rejects all members of `R`.

25. **`current_revocation_atomic`**  
    `HardRevokePredecessor` cannot transform a selected current activation. A current activation becomes hard-revoked only through an applied `Activate` or `Suspend` that also changes selection.

26. **`activation_nonresurrection`**  
    Once activation ID `a` is hard-revoked, no reachable snapshot gives `a` another disposition.

27. **`reactivation_fresh_identity`**  
    Under the injectivity assumption for `ActivationId`, reactivating identical content after revocation produces `a' != a`.

28. **`activation_id_binds_command`**  
    Under hash injectivity, two activation IDs are equal only if their exact activation command digests and all other activation-preimage fields are equal. In particular, changing predecessor versus hard-revoked retirement changes the activation identity.

29. **`content_kind_binding`**  
    One content identity cannot be registered for two distinct resource kinds under the content-ID injectivity assumption.

30. **`explicit_retirement`**  
    Replacing an existing current activation without a retirement choice cannot produce `Applied`.

31. **`suspension_no_creation_fallback`**  
    Explicit suspension yields no current creation activation; a usable unselected activation remains predecessor-only.

### Refinement obligations

32. **`python_relation_agrees_with_neutral_step`**  
    Translate the committed JSON counterexample corpus into Lean values and prove each expected decision under the neutral relation.

33. **`rust_step_refines_neutral_step`**  
    Reserved for the future Rust implementation. State exact field mappings, constructor invariants, hash assumptions, and reject-code projection. Do not prove this theorem until authority-bearing Rust types exist.

34. **`durable_linearization_refines_step`**  
    Reserved for the future store/runtime. One successful durable linearization must correspond to one `Applied`; exact retry returns the prior durable result; unknown outcomes are not modeled as clean rejection.

## Assumptions to name explicitly

The theorem files should make these assumptions parameters rather than hiding them:

- content-ID injectivity over approved canonical policy bytes;
- command-digest injectivity over approved command bytes;
- activation-ID injectivity over its approved preimage;
- snapshot-ID injectivity over the approved snapshot payload;
- finite and duplicate-free map or list representations;
- governance authorization is supplied by a separate sealed boundary;
- the model does not establish global non-equivocation without an external anchor or consensus profile.

## ESSO bounded-state work

A useful ESSO model should use small but nontrivial finite domains:

```text
2 machines or one fixed machine plus a substitution mutant
2 domains
2 resource kinds
3 content identities
4 activation identities
4 operation identities
versions 0..4
```

Model the exact command algebra and deterministic outcome precedence. Search for the following disaster mutants independently rather than changing the positive model to fit implementation output.

### Required disaster mutants

1. **Content/activation conflation**  
   Set `ActivationId = ContentId`; find stale capability resurrection after hard revoke and identical-content reactivation.

2. **Stored disposition drift**  
   Store `CurrentCreation` independently of selection; find a selected predecessor or unselected current state.

3. **Missing selection means suspended**  
   Delete a kind row; find ambiguity between unsupported, corrupt, and suspended state.

4. **Caller-selected next version**  
   Permit version jumps; find rollback or fast-forward/version-bomb traces.

5. **No parent binding**  
   Compare only scalar version; find substituted snapshot content with equal version.

6. **Revocation is reversible**  
   Allow `HardRevoked -> Usable`; find activation resurrection.

7. **Current standalone revocation**  
   Revoke selected current without changing selection; reach selected-and-revoked state.

8. **Implicit predecessor on replacement**  
   Omit retirement choice; find two implementations that disagree on old-current use.

9. **Predecessor creation**  
   Permit creation under unselected usable activation; find old authority surviving rotation.

10. **Replay after freshness**  
    Check stale parent before operation replay; find lost-ack retry misclassified as stale.

11. **Operation ID does not bind digest**  
    Reuse one operation ID for different commands; find audit/replay equivocation.

12. **Activation ID omits command digest**  
    Keep all other preimage fields equal while changing predecessor versus hard-revoked retirement; find equal activation identity for different provenance.

13. **Second hard revocation silently applies**  
    Normalize duplicate revocation into a new successful version; find audit ambiguity and spurious state advancement.

14. **Reject mutates replay log**  
    Insert operation record before semantic validation; find rejected command that changes state.

15. **Content ID copied across kind**  
    Register one content identity for two kinds; find kind-substitution acceptance.

16. **Generation gap or reuse**  
    Reuse a generation or skip one; find ambiguous activation ordering.

### ESSO success conditions

- every positive bounded invariant is inductive for the chosen domain;
- every disaster mutant yields a concrete shortest counterexample or a justified non-reachability result;
- solver `UNKNOWN`, timeout, or backend disagreement is reported as unresolved, never success;
- model source, exact command, solver versions, bounds, seeds, results, and hashes are committed in a later evidence PR;
- at least two solver backends agree on every claimed result before promotion.

## Suggested local division of work

### Lean

Start with obligations 2 through 6, 16, and 22 through 26. They require no cryptographic byte tables and test whether the minimal-state representation really eliminates contradictory lifecycle states.

Then prove obligations 8 through 15 for the abstract step relation. Leave obligations 27 through 29 parameterized by injectivity assumptions until canonical byte tables are approved.

### ESSO

Start with mutants 1, 2, 4, 7, 9, 10, 11, 12, and 14. These are the highest-value compositional failures. Preserve shortest traces as machine-readable fixtures for the independent review packet.

## Non-claims

This packet is not a Lean proof, ESSO result, Rust refinement proof, concurrency proof, crash-recovery proof, cryptographic proof, or production assurance artifact.
