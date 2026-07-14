# ZRM accounting aggregate research packet

This revision-bound packet records the research, counterexamples, executable
models, formal proofs, vectors, and remaining falsification work behind
RFC-0004. It is an R&D artifact, not protocol authority.

The central result is a change of carrier. Recursive accounting must not merge
`AccountingRowV1` directly because its authority and transformation roots have
no additive law. It must not reduce the row to one bounded signed net because
checked signed addition can have proof-tree-dependent definedness. The proposed
carrier instead preserves four monotone U256 totals for each exact
`(ResourceKindId, UnitId)` dimension:

```text
resource debit   = sum(consumed_atoms)
resource credit  = sum(created_atoms)
authority debit  = sum(authorized_burn_atoms)
authority credit = sum(authorized_mint_atoms)
```

The four columns are a lossless numeric homomorphism from the current leaf
accounting schema. Authority remains leaf-local and is authenticated through an
ordered coverage manifest; aggregate totals never grant mint, burn, conversion,
or commit authority.

## Contents

- `breakthroughs.md` explains the architectural discoveries and their limits.
- `source_ledger.json` pins primary literature, specifications, code, and local
  repository anchors used in this run.
- `hypotheses.json` records falsifiers, dependencies, evidence, and status for
  twenty Research Kernel hypotheses.
- `knowledge_graph.json` is a typed graph connecting sources, counterexamples,
  claims, obligations, and design decisions.
- `experiments.json` separates executed evidence from specified future work.
- `research_kernel_receipt.json` records the actual MCP call counts, frontier,
  limitations, and promotion policy.
- `research_kernel_plan.json` is the replay and compounding plan for the next
  run; it deliberately does not embed credentials or private state.
- `morph_reformulations.json` preserves alternative formulations as candidates,
  not validated equivalences.
- `esso_campaign.json` specifies a future mutant campaign and explicitly records
  that it was not executed in this checkout.
- `evidence/` contains revision- and command-bound observations produced by the
  executable model, Lean, vector replay, and packet checker.
- `manifest.json` authenticates the packet and selected implementation artifacts.

## Replay

From the repository root:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  reference_models.tests.test_accounting_aggregate_v1 -v
PYTHONDONTWRITEBYTECODE=1 python3 -m reference_models.accounting_aggregate_v1_explorer
python3 vectors/independent_python/replay_accounting_aggregate_v1.py --check
python3 tools/check_zrm_accounting_research.py
python3 -m unittest tools.tests.test_zrm_accounting_research -v
(cd formal/lean/arm_zrm_frontier_v2 && lake build --wfail && \
  lake env leanchecker --verbose ArmZrmFrontier)
(cd formal/lean/zrm_accounting_aggregate_v1 && lake build --wfail && \
  lake env leanchecker --verbose ZrmAccountingAggregateV1)
```

The Research Kernel replay additionally needs the pinned Research Kernel MCP
source and its Python MCP dependency. Its plan is non-gating; the committed
receipt records what was actually observed in the run.

## Claim discipline

- `refuted` means a concrete counterexample defeated the exact baseline claim.
- `supported_bounded` means the listed executable or formal model supports the
  claim under its recorded assumptions and bounds.
- `source_supported` means a primary source supports the stated lineage or
  boundary, not that ZRM implements it.
- `under_test` and `unknown` are not promotions.

No packet status approves RFC-0004, changes `SPECIFICATION.md`, establishes a
production proof system, proves data availability, or makes Research Kernel,
Morph, ESSO, Lean, Python, SHA-256, or an external repository a source of ZRM
authority.
