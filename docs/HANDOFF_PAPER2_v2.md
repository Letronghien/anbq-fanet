# HANDOFF — Paper 2 (A-NBQ: adaptive selection between AODV-like and NBQ-like forwarding) — v2

Attach this file at the start of the Paper-2 conversation (it supersedes PAPER2_BRIEF.md v1).

## 1. Context

- Authors: Trong-Hien Le, Khoa Tran Thi-Minh, Huu-Dung Ngo (IUH, Vietnam).
- Paper 1 (NBQ-MAODV, finishing): https://github.com/Letronghien/nbqmaodv-fanet — FROZEN, do not modify.
- Paper 2 repo: https://github.com/Letronghien/anbq-fanet (created, empty).
- VM: Google Cloud Ubuntu 8 vCPU. Copy `~/nbqmaodv-fanet` → `~/anbq-fanet` (ns-3.48 tree with patches,
  scenario core `scratch/fanet-core.h`, modules aodv/qmaodv/saqmaodv/nbqmaodv). Work only in the copy.
- Working rules: Vietnamese chat, English papers; step-by-step patches checked against ns-3.48 headers;
  every change behind an attribute whose default reproduces previous results; frozen experiment design
  before main runs; tuning seeds 101–103 only; honest reporting; critique results like a reviewer.

## 2. What Paper 1 established (inputs for Paper 2)

- NBQ-MAODV: Q(d,u) ← (1−α)Q + α[−(1−r) + γ′·V_u(d)], V advertised on control packets, reward from MAC
  ACK/drop, ε 0.1→0.02, selection at every hop, dead-end V = −5. Module `nbqmaodv` also contains:
  `TagsOnAir` (charges tag bytes on air) and `LiuQAodv` (external baseline, Liu et al. 2026).
- Regime map (PDR, NBQ − AODV), equal effective range 250 m:
  K0 ideal disc → AODV better (mean −3.8; −5.2 with signalling on air);
  K1 interference/soft edge → about equal (−1.2; −2.0 on air);
  K2 fading gray zone → NBQ ahead (+1.7; **+0.9 on air**, 12/12 cells positive, few significant).
- Oracle (best protocol per condition) gains only **+0.58 points** over always-AODV, because the regime
  boundary follows the channel axis.
- MAC ACK ratio of AODV runs: Spearman ρ = −0.85 with the NBQ advantage, but it mostly **separates
  channels**; within a channel it predicts poorly.
- Regime can change **over time** (K1: equal in 60–300 s, AODV better in 300–600 s).
- Selection at every hop helps in gray zones but costs 1.8 points on ideal links at high load.
- Signalling must be charged on air: packet tags hid about half of NBQ's gray-zone advantage.
- Raw data: `~/nbqmaodv-fanet/results/main/runs.csv` (3,860 runs, per-run local indicators:
  macAckRatio, avgNeighbours, avgMacQueue, avgDistBs, rreq/rrep/rerr) and `results/addendum/runs.csv`.

## 3. Consequences for Paper 2 (decided after Paper 1)

1. **Do not promise large average gains in stationary scenarios** — the oracle bound is small.
2. **Target non-stationary missions** where no fixed choice is right: link quality changing in time
   (UAVs entering/leaving an interference or fading region) or in space (part of the swarm in a gray zone,
   part in clear air). Paper 2 must first build such scenarios (e.g. channel parameters switching over
   time or by region) and show that the oracle gain there is substantial before designing the selector.
3. Selector signals must be **node-local and per-neighbour/time-varying** (EWMA of MAC ACK ratio per
   next hop, variance of link quality, RERR rate, queue), because run-level indicators only separate channels.
4. The selector may switch three things: forwarding strategy (primary route vs ε-greedy on Q),
   selection at every hop vs source only, and exploration level.
5. All signalling (values, indicators) charged on air from the start (`TagsOnAir=true` or real headers).
6. Baselines: AODV, NBQ-MAODV (on air), Liu et al. Q-Learning AODV (on air), and the oracle.

## 4. Suggested first steps

1. Copy the tree; verify that `fanet-scenario-aodv` and `-nbqmaodv` reproduce Paper-1 runs bit-exactly.
2. Design non-stationary channel scenarios (time-switching and region-based K0/K2) — pilot with AODV and
   NBQ only on tuning seeds; compute the oracle gain; continue only if it is meaningful.
3. Offline analysis of per-node signals → simple rule or bandit; then module `anbqmaodv`
   (copy of nbqmaodv + selector, attribute `AdaptiveMode`).
4. Frozen experiment design; main runs; key metric = share of the oracle gain recovered, plus never worse
   than the better fixed protocol by more than a small margin.
