# Paper 2 brief — A-NBQ: adaptive selection between AODV-like and NBQ-MAODV behaviour

Paste this file at the start of a new conversation to continue the work.

## 1. Who / what

- Authors: Trong-Hien Le, Khoa Tran Thi-Minh, Huu-Dung Ngo (IUH, Vietnam).
- Research line: PMAODV (IAAA'25) → QMAODV (ICIT 2025) → SA-QMAODV → **NBQ-MAODV (Paper 1, journal,
  in preparation)** → **A-NBQ (Paper 2, this brief)**.
- Paper 1 repo (frozen for reproducibility): https://github.com/Letronghien/nbqmaodv-fanet
- Paper 2 repo (to create): https://github.com/Letronghien/anbq-fanet

## 2. Environment (Google Cloud VM, Ubuntu, 8 vCPU)

- ns-3.48, isolated project tree `~/nbqmaodv-fanet/ns-3-nbq` (optimized build), patched
  `WifiRadioEnergyModel` (`ns3-patches/`), shared scenario core `scratch/fanet-core.h`,
  one scenario per module `scratch/fanet-scenario-<module>.cc`.
- Workflow: Claude writes patches (verified by compiling against ns-3.48 headers), the user applies
  them with `git apply`, builds, runs, pastes outputs. Step-by-step, one change per step, every change
  behind an attribute whose "off" value reproduces the previous results exactly.
- Paper 2 must NOT modify the Paper-1 tree: copy it to `~/anbq-fanet` after Paper 1's main runs end.

## 3. What Paper 1 established (fill in exact numbers from Paper 1's report.txt)

- All protocols share one multipath AODV core (ns-3 AODV copy): RREQ rate limit, buffering, RERR,
  alternative routes from duplicate RREQs (MaxPaths 3); they differ only in next-hop selection.
- Baselines were audited and corrected (docs/PROTOCOL_AUDIT.md): hop-by-hop selection, MAC-layer
  reward (AckedMpdu/DroppedMpdu), RERR-triggered ε bump, relay energy, PMAODV rebuilt on the shared core.
- **NBQ-MAODV**: Q(d,a) ← (1−α)Q + α[−(1−r) + γ′·V_u(d)], V_u advertised by the next hop on every
  control packet (QValueTag), V = 0 at the destination, V = −5 for dead ends, prior Q = −0.3·HC,
  ε0 0.1 / εmin 0.02, no RERR bump.
- Channel axis at equal effective range R_eff = 250 m: K0 ideal disc, K1 Nakagami m = 10 (−1.9 dBm),
  K2 m = 3/2/1.5 (−2.0 dBm). K0 hugely overestimates AODV (interference beyond 250 m ignored).
- Tuning-seed evidence: NBQ ≈ AODV on K0 at high load; NBQ > AODV on gray-zone channels at low load;
  AODV > NBQ on fading at high load. **Regime map + oracle from Paper 1 E2 quantify this.**

## 4. Paper 2 idea

No routing strategy is best everywhere. Each node decides online, from **local observable signals**,
how much to trust learning vs the plain shortest path:

- AODV-like mode: use the primary (shortest) route, ε = 0.
- NBQ mode: ε-greedy on neighbour-bootstrapped Q.
- Possibly a continuous mix (e.g. ε and "trust in Q" as functions of the signals).

Candidate signals (already logged per run in Paper 1, `# METRICS` line): MAC ACK ratio, number of
neighbours within 250 m, MAC queue length, RERR rate, distance to BS; per node they would be EWMAs.

## 5. Suggested plan

1. From Paper 1 `runs.csv`: which indicators separate "NBQ better" cells from "AODV better" cells
   (Spearman already in report.txt; add a small decision tree / logistic model).
2. Design a node-local rule (thresholds learned offline on tuning seeds 101–103 only) — or an online
   bandit that chooses the mode per destination.
3. Implement as a new module `anbqmaodv` (copy of nbqmaodv + selector), switch `AdaptiveMode`.
4. Evaluate on the Paper-1 regime-map grid against AODV, NBQ-MAODV and the oracle; the key metric is
   the fraction of the oracle gain recovered.
5. Frozen experiment design before main runs (same discipline as Paper 1).
