# Step 1 — which local indicators separate the regimes? (exploratory)

Script: `analysis/anbq-step1-indicators.py` (read-only on Paper-1 `results/main/runs.csv`, E2 rows only).

## Question

From Paper-1 E2 (36 cells = K × N × L, AODV vs NBQ-MAODV, seeds 1–20): do locally observable indicators
tell "NBQ better" cells from "AODV better" cells, and how much of the oracle gain can a simple rule recover?

## Method

| Part | What | Why |
|---|---|---|
| A | Regime counts and oracle; Holm exactly as Paper 1 (PDR, p95 delay, NRL together) | Sanity check: must reproduce Paper-1 `report.txt` |
| B | Spearman ρ of each indicator with the NBQ − AODV PDR difference, over all cells and **within each channel** | Paper 1 only has the pooled ρ; a pooled ρ can come only from channel differences |
| C | Mode invariance: indicator in NBQ runs vs in AODV runs | A node sees its signals in its *current* mode; a threshold that moves with the mode causes oscillation |
| D | Cross-validated **policies**: depth-1/2 policy trees and cost-sensitive logistic regression; feature sets `local`, `local+dist`, `design(ref)`; LOCO and LOKO | Key number = fraction of oracle gain recovered |
| E | Rules fitted on all cells + how often the same stump feature is chosen across LOCO folds | Interpretation and stability only |

Definitions:

- Indicators (per node, EWMA-able online): `macAckRatio`, `avgNeighbours` (within 250 m), `avgMacQueue`,
  `rerrRate` and `rreqRate` (per node per second over the measurement window); `avgDistBs` (needs own
  position and BS position). In E2 the BS is always at the centre, so `avgDistBs` is nearly constant there.
- `design(ref)` = (K, N, L). Not observable by a node; it is the upper reference for "knowing the scenario".
- Policy tree: splits maximise the total PDR of the chosen protocol (policy value), not an impurity; ≥ 3 cells per leaf.
- Logistic: label = NBQ better, weight = |PDR difference|, L2 (λ = 1), standardised features.
- Fraction recovered = (V_policy − V_bestfixed) / (V_oracle − V_bestfixed); V = mean PDR over cells;
  best-fixed = better of always-AODV / always-NBQ; 95 % CI by cell bootstrap (LOCO).
- LOCO = leave one cell out (36 folds). LOKO = leave one channel out (3 folds; the rule has never seen
  that channel). `aodv->nbq` = trained on AODV-run indicators, applied to NBQ-run indicators.

## Known limitations (stated up front)

1. Cell means over 20 seeds and 240 s, averaged over all nodes. A node sees one noisy local EWMA; Step 1 only
   says whether the information exists at network scale, not whether one node can extract it.
2. 36 cells, strongly structured (the grid). CV numbers carry wide intervals; LOKO is the honest test.
3. Indicators are taken from runs of a fixed mode. An adaptive node changes its own signals (part C
   measures how much).

## Seed discipline (decision needed before Step 2)

E2 uses the Paper-1 **evaluation** seeds 1–20. Step 1 is used only to choose *which signals* and *what rule
shape* go into A-NBQ. It does not fix any threshold. Proposed rule for Paper 2:

- Thresholds / selector parameters: fitted on tuning seeds 101–103 only (new runs of the E2 grid).
- Paper-2 evaluation: seeds 21–40 (never looked at), same grid, AODV and NBQ-MAODV re-run on those seeds for
  the oracle. Paper-1 numbers on seeds 1–20 are cited but are not the Paper-2 comparison.

## Output

`~/anbq-fanet/results/step1/`: `anbq-step1-report.txt` (paste this back), `anbq-step1-cells.csv`, `anbq-step1-spearman.csv`,
`anbq-step1-policies.csv`, `anbq-step1-scatter.png`.
