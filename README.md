# A-NBQ: adaptive selection between AODV-like and NBQ-MAODV behaviour in FANETs (Paper 2)

Follow-up to NBQ-MAODV (Paper 1, frozen repo: https://github.com/Letronghien/nbqmaodv-fanet).
Each UAV decides online, from local observable signals, how much to trust neighbour-bootstrapped
Q-learning versus the plain shortest AODV route.

Authors: Trong-Hien Le, Khoa Tran Thi-Minh, Huu-Dung Ngo (IUH, Vietnam).

## Layout

| Path | Content |
|---|---|
| `docs/anbq-paper2-brief.md` | context and plan |
| `docs/anbq-step<n>.md` | method note of each step |
| `src/nbqmaodv/` | Paper-1 baseline module (verbatim) |
| `src/anbqmaodv/` | A-NBQ module (from Step 3) |
| `scratch/anbq-*` | scenarios (shared core `anbq-core.h`) |
| `ns3-patches/` | patches to upstream ns-3.48 |
| `tools/anbq-*` | setup, sync, verification, runners |
| `analysis/anbq-*` | offline analyses |

VM: repo `~/anbq-repo`, isolated ns-3 tree `~/anbq-fanet/ns-3-anbq`, results `~/anbq-fanet/results`
(see `docs/anbq-step0.md`). The Paper-1 tree is never modified.

## Step log

| Step | Content |
|---|---|
| 0 | Isolated ns-3.48 tree, Paper-1 baseline imported, `anbq-` naming, bit-exact verification |
| 1 | Which local indicators separate NBQ-better from AODV-better cells (Paper-1 E2); oracle gain recoverable by simple rules |
