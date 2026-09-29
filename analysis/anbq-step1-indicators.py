#!/usr/bin/env python3
"""
anbq-step1-indicators.py -- Paper 2 (A-NBQ), Step 1: exploratory analysis of Paper-1 E2 data.

Question: which locally observable indicators separate regime-map cells where NBQ-MAODV beats AODV
from cells where AODV beats NBQ-MAODV, and how much of the oracle gain would a simple rule recover?

    python3 ~/anbq-repo/analysis/anbq-step1-indicators.py ~/nbqmaodv-fanet/results/main/runs.csv \
            [--out ~/anbq-fanet/results/step1] [--boot 2000]

Read-only on runs.csv (Paper-1 tree is never modified). Uses only numpy/pandas/scipy/matplotlib
(same as Paper-1 analyze_main.py).

STATUS: exploratory. E2 uses evaluation seeds 1-20. Nothing selected here may be tuned on these
numbers and then reported as a Paper-2 result; thresholds for A-NBQ are fitted later on tuning seeds
(101-103) and Paper-2 evaluation uses seeds that were not looked at here (see docs/anbq-step1.md).

Units of analysis
  cell     = (K, N, L) of the E2 grid (36 cells), values = means over paired seeds.
  policy   = a rule mapping a cell's indicator vector to {AODV, NBQ}; value = mean PDR over cells of the
             protocol it picks.  Oracle = per-cell best; best-fixed = better of always-AODV / always-NBQ.
  fraction of oracle gain recovered = (V_policy - V_bestfixed) / (V_oracle - V_bestfixed).

Indicator sources
  aodv : indicators measured in the AODV runs of the cell   (what a node sees in AODV-like mode)
  nbq  : indicators measured in the NBQ-MAODV runs          (what a node sees in NBQ mode)
  xfer : rule trained on aodv-source, applied to nbq-source (a selector must decide from whatever mode it
         is currently in -- tests whether thresholds survive the mode switch)
"""
import argparse, math, os, sys, warnings
import numpy as np
import pandas as pd
from scipy import stats, optimize
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore", category=stats.ConstantInputWarning)

A, B = "AODV", "NBQ-MAODV"
KS = ["K0", "K1", "K2"]
# node-observable (per node, EWMA-able online); avgDistBs needs own position + BS position
LOCAL = ["macAckRatio", "avgNeighbours", "avgMacQueue", "rerrRate", "rreqRate"]
LOCAL_DIST = LOCAL + ["avgDistBs"]
DESIGN = ["Kord", "N", "L"]           # scenario descriptors: NOT observable, reference only
FEATSETS = {"local": LOCAL, "local+dist": LOCAL_DIST, "design(ref)": DESIGN}
PAPER1_METRICS = ("pdr", "delayP95Ms", "nrl")   # pdr first
MIN_LEAF = 3                          # cells per leaf in policy trees
REPORT = []
SEEDPDR = {}                          # (K,N,L) -> (pdr AODV, pdr NBQ) per paired seed, for the cross-fitted oracle


def say(*a):
    s = " ".join(str(x) for x in a); print(s); REPORT.append(s)


def holm(p):
    p = np.asarray(p, float); n = len(p); order = np.argsort(p); adj = np.empty(n); run = 0.0
    for i, idx in enumerate(order):
        run = max(run, (n - i) * p[idx]); adj[idx] = min(1.0, run)
    return adj


# ------------------------------------------------------------------------------------ data
def load(path):
    df = pd.read_csv(path)
    df["exps"] = df["exps"].fillna("")
    df = df[df.exps.str.contains(r"(?:^|;)E2(?:$|;)", regex=True) & df.proto.isin([A, B])].copy()
    if df.empty:
        sys.exit("no E2 rows for AODV / NBQ-MAODV in " + path)
    for c in ("pdr", "delayP95Ms", "nrl", "rerr", "rreq", "macAckRatio", "avgNeighbours", "avgMacQueue", "avgDistBs", "sim", "warm"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    dur = (df.sim - df.warm).clip(lower=1)
    df["rerrRate"] = df.rerr / (df.N * dur)       # RERR per node per second (measurement window)
    df["rreqRate"] = df.rreq / (df.N * dur)
    df["Kord"] = df.K.map({k: i for i, k in enumerate(KS)})
    return df


def cells(df):
    """one row per (K,N,L): paired PDR stats + indicator means per source."""
    rows = []
    for (K, N, L), g in df.groupby(["K", "N", "L"]):
        ga, gb = g[g.proto == A].set_index("seed"), g[g.proto == B].set_index("seed")
        s = ga.index.intersection(gb.index)
        if len(s) < 3:
            continue
        pa, pb = ga.loc[s, "pdr"].astype(float), gb.loc[s, "pdr"].astype(float)
        r = dict(K=K, N=N, L=L, Kord=KS.index(K), n=len(s), pdrA=pa.mean(), pdrB=pb.mean(), diff=(pb - pa).mean(),
                 seedOracle=np.maximum(pa, pb).mean())
        SEEDPDR[(K, N, L)] = (pa.to_numpy(float), pb.to_numpy(float))
        for m in PAPER1_METRICS:  # same tests as Paper-1 analyze_main.py (Holm over all of them below)
            xa = pd.to_numeric(ga.loc[s, m], errors="coerce"); xb = pd.to_numeric(gb.loc[s, m], errors="coerce")
            d = xb - xa
            r[f"d_{m}"] = d.mean()
            r[f"ci_{m}"] = stats.t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / math.sqrt(len(d)) if len(d) > 1 else np.nan
            try:
                r[f"p_{m}"] = stats.wilcoxon(xb, xa).pvalue if (d != 0).any() else 1.0
            except ValueError:
                r[f"p_{m}"] = 1.0
        for f in LOCAL_DIST:
            r[f"aodv:{f}"] = ga.loc[s, f].astype(float).mean()
            r[f"nbq:{f}"] = gb.loc[s, f].astype(float).mean()
        rows.append(r)
    c = pd.DataFrame(rows)
    # Holm over all 3 metrics x cells, exactly as Paper-1 compare_vs_aodv("E2") -> identical regime labels
    P = c[[f"p_{m}" for m in PAPER1_METRICS]].to_numpy(float)
    c["p"] = c["p_pdr"]
    adj = holm(P.ravel()).reshape(P.shape)
    for i, m in enumerate(PAPER1_METRICS):
        c[f"ph_{m}"] = adj[:, i]
    c["p_holm"] = c["ph_pdr"]
    c["regime"] = np.where(c.p_holm < 0.05, np.where(c["diff"] > 0, "NBQ better", "AODV better"), "equivalent")
    c["best"] = np.where(c.pdrB > c.pdrA, "NBQ", "AODV")
    return c


def xfit_oracle(c, reps, rng):
    """cross-fitted cell oracle: choose the protocol on one random half of the paired seeds, score it on the
    other half (and vice versa). Removes the upward 'max of two noisy means' bias of the plain cell oracle;
    it is biased slightly downward instead (choice made on half the seeds), so the true oracle lies between."""
    vals = []
    for _ in range(reps):
        tot = 0.0
        for K, N, L in zip(c.K, c.N, c.L):
            pa, pb = SEEDPDR[(K, N, L)]
            idx = rng.permutation(len(pa)); h1, h2 = idx[: len(idx) // 2], idx[len(idx) // 2:]
            v = 0.0
            for sel, ev in ((h1, h2), (h2, h1)):
                v += (pb[ev].mean() if pb[sel].mean() > pa[sel].mean() else pa[ev].mean()) / 2
            tot += v
        vals.append(tot / len(c))
    return float(np.mean(vals))


def X_of(c, feats, source):
    cols = [f if f in DESIGN else f"{source}:{f}" for f in feats]
    return c[cols].to_numpy(float)


# ------------------------------------------------------------------------------------ policies
def _leaf(vA, vB):
    return (vB.sum() > vA.sum()), max(vA.sum(), vB.sum())


def fit_tree(X, vA, vB, depth):
    """policy tree: splits chosen to maximise total PDR of the chosen protocol (not impurity)."""
    choose, val = _leaf(vA, vB)
    node = dict(leaf=True, nbq=choose, val=val)
    if depth == 0 or len(vA) < 2 * MIN_LEAF:
        return node
    best = None
    for j in range(X.shape[1]):
        xs = np.unique(X[:, j])
        for t in (xs[:-1] + xs[1:]) / 2:
            m = X[:, j] <= t
            if m.sum() < MIN_LEAF or (~m).sum() < MIN_LEAF:
                continue
            v = _leaf(vA[m], vB[m])[1] + _leaf(vA[~m], vB[~m])[1]
            if best is None or v > best[0] + 1e-12:
                best = (v, j, t)
    if best is None or best[0] <= val + 1e-12:
        return node
    _, j, t = best
    m = X[:, j] <= t
    return dict(leaf=False, j=j, t=t, lo=fit_tree(X[m], vA[m], vB[m], depth - 1),
                hi=fit_tree(X[~m], vA[~m], vB[~m], depth - 1))


def pred_tree(node, x):
    while not node["leaf"]:
        node = node["lo"] if x[node["j"]] <= node["t"] else node["hi"]
    return node["nbq"]


def tree_str(node, feats, ind=""):
    if node["leaf"]:
        return f"{ind}-> {'NBQ' if node['nbq'] else 'AODV'}\n"
    f = feats[node["j"]]
    return (f"{ind}{f} <= {node['t']:.4g}\n" + tree_str(node["lo"], feats, ind + "   ")
            + f"{ind}{f} >  {node['t']:.4g}\n" + tree_str(node["hi"], feats, ind + "   "))


def fit_logit(X, vA, vB, lam=1.0):
    """cost-sensitive L2 logistic regression: label = NBQ better, weight = |PDR difference|."""
    mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1
    Z = (X - mu) / sd
    y = (vB > vA).astype(float); w = np.abs(vB - vA); w = w / w.mean() if w.sum() > 0 else np.ones_like(w)
    Z1 = np.c_[np.ones(len(Z)), Z]

    def nll(b):
        z = Z1 @ b
        return np.sum(w * (np.logaddexp(0, z) - y * z)) + 0.5 * lam * np.sum(b[1:] ** 2)
    b = optimize.minimize(nll, np.zeros(Z1.shape[1]), method="L-BFGS-B").x
    return dict(mu=mu, sd=sd, b=b)


def pred_logit(m, x):
    return float(m["b"][0] + ((x - m["mu"]) / m["sd"]) @ m["b"][1:]) > 0


MODELS = {
    "stump":  (lambda X, a, b: fit_tree(X, a, b, 1), pred_tree),
    "tree2":  (lambda X, a, b: fit_tree(X, a, b, 2), pred_tree),
    "logit":  (fit_logit, pred_logit),
}


def cv_predict(c, feats, src_train, src_test, model, folds):
    fit, pred = MODELS[model]
    Xtr_all, Xte_all = X_of(c, feats, src_train), X_of(c, feats, src_test)
    vA, vB = c.pdrA.to_numpy(float), c.pdrB.to_numpy(float)
    out = np.zeros(len(c), bool)
    for te in folds:
        tr = np.setdiff1d(np.arange(len(c)), te)
        m = fit(Xtr_all[tr], vA[tr], vB[tr])
        for i in te:
            out[i] = pred(m, Xte_all[i])
    return out


def value(c, nbq):
    return np.where(nbq, c.pdrB, c.pdrA).mean()


def frac(c, nbq):
    fa, fb, orc = c.pdrA.mean(), c.pdrB.mean(), np.maximum(c.pdrA, c.pdrB).mean()
    fix = max(fa, fb)
    den = orc - fix
    return (value(c, nbq) - fix) / den if den > 1e-9 else np.nan


def boot_ci(c, nbq, nb, rng):
    idx = np.arange(len(c)); fs = []
    for _ in range(nb):
        s = rng.choice(idx, len(idx), replace=True)
        fs.append(frac(c.iloc[s].reset_index(drop=True), nbq[s]))
    fs = np.array(fs); fs = fs[~np.isnan(fs)]
    return (np.percentile(fs, 2.5), np.percentile(fs, 97.5)) if len(fs) else (np.nan, np.nan)


# ------------------------------------------------------------------------------------ report
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("--out", default=os.path.expanduser("~/anbq-fanet/results/step1"))
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(12345)
    pd.set_option("display.width", 200)

    df = load(a.runs)
    say(f"E2 runs loaded: {len(df)}  ({a.runs})")
    say(df.groupby(["proto", "K"]).size().unstack(fill_value=0).to_string())
    c = cells(df)
    c.to_csv(os.path.join(a.out, "anbq-step1-cells.csv"), index=False)
    say(f"cells with >= 3 paired seeds: {len(c)} / 36;  paired seeds per cell: min {c.n.min()}, max {c.n.max()}")
    if len(c) < 12:
        say("too few cells for the policy analysis; rerun when more of E2 is done"); flush(a.out); return

    # --- A. regime + oracle (sanity check against Paper-1 report.txt)
    say("\n[A] regime counts (PDR, Holm as in Paper 1: PDR, p95 delay, NRL over the cells present)")
    say(c.groupby(["K", "regime"]).size().unstack(fill_value=0).to_string())
    fa, fb = c.pdrA.mean(), c.pdrB.mean(); orc = np.maximum(c.pdrA, c.pdrB).mean()
    say(f"mean PDR over cells: always-AODV {fa:.2f}  always-NBQ {fb:.2f}  cell-oracle {orc:.2f}  "
        f"seed-oracle {c.seedOracle.mean():.2f}")
    say(f"cell-oracle gain over best fixed: {orc - max(fa, fb):+.2f} points  (denominator of 'fraction recovered')")
    global ORC_XF
    ORC_XF = xfit_oracle(c, 300, rng)
    say(f"cross-fitted cell oracle {ORC_XF:.2f} -> gain over best fixed {ORC_XF - max(fa, fb):+.2f} points "
        f"(noise-corrected lower bracket; the true oracle gain lies between this and the plain one)")

    say("\n[A2] per-cell NBQ - AODV difference, mean over paired seeds (* Holm p < 0.05, Holm as in Paper 1)")
    for m, unit in (("pdr", "PDR points"), ("delayP95Ms", "p95 delay ms, negative = NBQ faster"),
                    ("nrl", "NRL, negative = NBQ less overhead")):
        t = c.copy()
        t["cell"] = t.apply(lambda r: f"{r[f'd_{m}']:+7.1f}{'*' if r[f'ph_{m}'] < 0.05 else ' '}", axis=1)
        say(f"-- {m} ({unit})")
        say(t.pivot_table(index=["N", "L"], columns="K", values="cell", aggfunc="first").to_string())
        say("   per-channel mean: " + ", ".join(f"{K} {t[t.K == K][f'd_{m}'].mean():+.2f}" for K in KS if (t.K == K).any())
            + f";  significant cells: NBQ better {int(((t[f'ph_{m}'] < 0.05) & (t[f'd_{m}'] * (1 if m == 'pdr' else -1) > 0)).sum())}, "
            + f"AODV better {int(((t[f'ph_{m}'] < 0.05) & (t[f'd_{m}'] * (1 if m == 'pdr' else -1) < 0)).sum())}")

    # --- B. univariate: Spearman with diff, overall and within channel
    say("\n[B] Spearman rho of indicator (cell mean) with NBQ - AODV PDR difference")
    rows = []
    for src in ("aodv", "nbq"):
        for f in LOCAL_DIST:
            x = c[f"{src}:{f}"]
            r = dict(source=src, indicator=f, all=stats.spearmanr(x, c["diff"]).correlation)
            for K in KS:
                m = c.K == K
                r[K] = stats.spearmanr(x[m], c["diff"][m]).correlation if m.sum() >= 4 else np.nan
            rows.append(r)
    sp = pd.DataFrame(rows); sp.to_csv(os.path.join(a.out, "anbq-step1-spearman.csv"), index=False)
    say(sp.round(3).to_string(index=False))
    say("(within-K columns: does the indicator still separate cells once the channel is fixed? 12 cells each)")

    # --- C. mode invariance of indicators
    say("\n[C] mode invariance: indicator in NBQ runs vs in AODV runs (same cells)")
    rows = []
    for f in LOCAL_DIST:
        xa, xb = c[f"aodv:{f}"], c[f"nbq:{f}"]
        rows.append(dict(indicator=f, spearman=stats.spearmanr(xa, xb).correlation,
                         mean_aodv=xa.mean(), mean_nbq=xb.mean(), median_ratio=np.median(xb / xa.replace(0, np.nan))))
    say(pd.DataFrame(rows).round(4).to_string(index=False))
    say("(low rank agreement or a large ratio -> a threshold learned in one mode is wrong in the other)")

    # --- D. cross-validated policies
    n = len(c)
    loco = [np.array([i]) for i in range(n)]
    loko = [np.where(c.K == K)[0] for K in KS if (c.K == K).any()]
    setups = [(fs, s, s) for fs in FEATSETS for s in ("aodv", "nbq") if not (fs == "design(ref)" and s == "nbq")]
    setups += [("local", "aodv", "nbq")]
    rows = []
    for fs, s_tr, s_te in setups:
        feats = FEATSETS[fs]
        for model in MODELS:
            for cvname, folds in (("LOCO", loco), ("LOKO", loko)):
                if cvname == "LOKO" and fs == "design(ref)":
                    continue  # K is a feature; leaving a channel out makes the K split meaningless
                p = cv_predict(c, feats, s_tr, s_te, model, folds)
                lo, hi = boot_ci(c, p, a.boot, rng) if cvname == "LOCO" else (np.nan, np.nan)
                rows.append(dict(features=fs, source=s_tr if s_tr == s_te else f"{s_tr}->{s_te}", model=model,
                                 cv=cvname, V=value(c, p), frac=frac(c, p), frac_lo=lo, frac_hi=hi,
                                 frac_xf=(value(c, p) - max(fa, fb)) / (ORC_XF - max(fa, fb))
                                 if ORC_XF - max(fa, fb) > 1e-9 else np.nan,
                                 pickNBQ=p.mean(), agree_best=(p == (c.best == "NBQ")).mean(),
                                 sig_wrong=int(((c.regime == "NBQ better") & ~p).sum()
                                               + ((c.regime == "AODV better") & p).sum())))
    pol = pd.DataFrame(rows); pol.to_csv(os.path.join(a.out, "anbq-step1-policies.csv"), index=False)
    say("\n[D] cross-validated policies (V = mean PDR over cells; frac = fraction of oracle gain recovered,")
    say("    95% cell-bootstrap CI for LOCO; LOCO = leave one cell out, LOKO = leave one channel out;")
    say("    sig_wrong = cells with a significant regime where the policy picks the worse protocol;")
    say("    frac_xf = same with the cross-fitted oracle as denominator; > 1 means the plain oracle gain is mostly noise)")
    say(f"    reference: always-AODV {fa:.2f}, always-NBQ {fb:.2f}, oracle {orc:.2f}")
    say(pol.round(3).to_string(index=False))

    # --- E. interpretable rules fitted on all cells + stability of the stump under LOCO
    say("\n[E] rules fitted on all cells (for interpretation only -- NOT to be used as A-NBQ thresholds)")
    vA, vB = c.pdrA.to_numpy(float), c.pdrB.to_numpy(float)
    for fs, src in (("local", "aodv"), ("local", "nbq"), ("local+dist", "aodv")):
        feats = FEATSETS[fs]; X = X_of(c, feats, src)
        for d in (1, 2):
            t = fit_tree(X, vA, vB, d)
            p = np.array([pred_tree(t, x) for x in X])
            say(f"-- depth {d}, features {fs}, source {src}: in-sample frac {frac(c, p):.3f}")
            say(tree_str(t, feats).rstrip())
        X = X_of(c, feats, src); picks = []
        for te in loco:
            tr = np.setdiff1d(np.arange(n), te)
            t = fit_tree(X[tr], vA[tr], vB[tr], 1)
            picks.append("none" if t["leaf"] else f"{feats[t['j']]}")
        vc = pd.Series(picks).value_counts()
        say(f"   stump feature chosen across {n} LOCO folds ({fs}, {src}): " + ", ".join(f"{k} x{v}" for k, v in vc.items()))
        m = fit_logit(X, vA, vB)
        say("   logit standardized coefficients: " + ", ".join(f"{f} {b:+.2f}" for f, b in zip(feats, m["b"][1:])))

    # --- F. figure
    fig, axs = plt.subplots(2, len(LOCAL_DIST), figsize=(3.2 * len(LOCAL_DIST), 6.2))
    for row, src in enumerate(("aodv", "nbq")):
        for j, f in enumerate(LOCAL_DIST):
            ax = axs[row, j]
            for K, mk in zip(KS, "osD"):
                m = c.K == K
                sig = c.regime[m] != "equivalent"
                ax.scatter(c.loc[m, f"{src}:{f}"], c.loc[m, "diff"], marker=mk, s=np.where(sig, 40, 14),
                           label=K, alpha=.8)
            ax.axhline(0, color="k", lw=.6); ax.set_xlabel(f); ax.grid(alpha=.3)
            if j == 0:
                ax.set_ylabel(f"NBQ - AODV PDR ({src} runs)")
    axs[0, 0].legend(fontsize=8)
    fig.suptitle("E2 cells: indicator vs PDR difference (large marker = significant, Holm p < 0.05)")
    fig.tight_layout(); fig.savefig(os.path.join(a.out, "anbq-step1-scatter.png"), dpi=160); plt.close(fig)
    flush(a.out)


def flush(out):
    with open(os.path.join(out, "anbq-step1-report.txt"), "w") as f:
        f.write("\n".join(REPORT) + "\n")
    print(f"\nreport, tables and figure written to {out}")


if __name__ == "__main__":
    main()
