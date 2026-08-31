"""EASY-81 false-alarm decomposition: NO_ESCAPE -> NONE_INDEX -> ESCALATE.

All rows in the EASY-81 supplement are label EASY (a feasible, solver-certified scenario has
served_load >= 0.99), so ANY escalation on these items is, by construction, a false alarm --
the model declining to act (or naming a human-operator escalation) when a single menu action
would have cleared every violation. This script decomposes that false-alarm rate into two
single-variable steps, using harness_v2b.py's NONE_INDEX arm as the midpoint between the two
existing reference arms:

  N -> I  (NO_ESCAPE  -> NONE_INDEX):  adds a bare "NONE -- no single action above resolves all
           violations" INDEX option to the menu, with NO change to response format (index stays
           an index) and NO human-escalation language. Isolates the effect of OFFERING a
           decline-shaped menu slot at all.
  I -> E  (NONE_INDEX -> ESCALATE):    the SAME index slot, but reworded to name "ESCALATE" and
           add "hand this to a human operator or a multi-action planner." Isolates the effect of
           the ESCALATE WORDING/human-operator framing on top of an already-offered decline slot.

Reference arms verified against CANONICAL_FILES.md before this script was written:
  gemini-3.7-flash:        NO_ESCAPE 9/81, ESCALATE 33/81
  gemini-3.1-pro-preview:  NO_ESCAPE 1/79 (parsed), ESCALATE 8/80 (parsed)
gpt-5.6-luna had NO EASY-81 NO_ESCAPE/ESCALATE arms on disk before this run (checked: no
v2_easyladder_gpt-5.6-luna_* files existed). Both were run fresh via harness_v2_azure.py
(162 calls) so the three-model decomposition is complete rather than NONE_INDEX-rate-only.

Every CI here is a PAIRED cluster bootstrap: cluster = (case, item_id). For the EASY-81 set
every cluster contains exactly 1 row (this corpus has no margin-ladder rungs the way the
263-item benchmark does -- see clustered_ci.py's discussion of 263 rows -> 40 clusters for
contrast), so this reduces to an ordinary item-level bootstrap, but it is still described as
"cluster bootstrap over the EASY-81 item clusters" per the task brief and to keep the method
name consistent with the rest of this pack's analyses. All three arms are run on the IDENTICAL
81-item set for a given model (verified: cluster sets match byte-for-byte across all 9 files),
so the same per-model bootstrap resample is reused across arms (paired design) -- unparsed rows
are excluded from a cluster's contribution to whichever arm they occurred in, never scored as
non-escalation.

Reads   v2_easyladder_{model}_{NO_ESCAPE,NONE_INDEX,ESCALATE}.jsonl for
        model in (gemini-3.7-flash, gemini-3.1-pro-preview, gpt-5.6-luna).
Writes  analysis/easy81_none_index.json, analysis/easy81_none_index.md
"""
import json, os, collections
import numpy as np
from scipy.stats import fisher_exact

ROOT = "/path/to/cral_original_pack/powergrid"  # anonymized original pack root; see README "Anonymization note"
OUTDIR = os.path.join(ROOT, "analysis")
SEED = 20260827
B = 20000
GATE = 0.05
MODELS = ["gemini-3.7-flash", "gemini-3.1-pro-preview", "gpt-5.6-luna"]
ARMS = ["NO_ESCAPE", "NONE_INDEX", "ESCALATE"]

rng = np.random.default_rng(SEED)


def load(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def fp(model, arm):
    return os.path.join(ROOT, f"v2_easyladder_{model}_{arm}.jsonl")


# ---------------------------------------------------------------------------------------
# 0. load + gate check every cell; assert identical cluster set across arms within a model
# ---------------------------------------------------------------------------------------
DATA = {}
GATECHECK = []
CL = None
for model in MODELS:
    cl_model = None
    for arm in ARMS:
        path = fp(model, arm)
        R = load(path)
        keys = collections.Counter((r["case"], r["item_id"], r["tag"]) for r in R)
        dups = sum(v - 1 for v in keys.values() if v > 1)
        n = len(R)
        unparsed = sum(1 for r in R if not r["parsed"])
        rate_un = unparsed / n if n else float("nan")
        p = [r for r in R if r["parsed"]]
        esc = sum(r["escalated"] for r in p)
        labels = set(r["label"] for r in R)
        cl = sorted({(r["case"], r["item_id"]) for r in R})
        if cl_model is None:
            cl_model = cl
        GATECHECK.append(dict(model=model, arm=arm, n=n, dups=dups, unparsed=unparsed,
                              unparsed_rate=round(rate_un, 4),
                              gate_ok=bool(rate_un <= GATE), labels=sorted(labels),
                              n_clusters=len(cl), escalated=esc, n_parsed=len(p),
                              rate=round(esc / len(p), 4) if p else None))
        assert labels == {"EASY"}, f"{model}/{arm}: non-EASY rows present ({labels})"
        assert dups == 0, f"{model}/{arm}: {dups} duplicate (case,item_id,tag) rows"
        DATA.setdefault(model, {})[arm] = R
    assert cl_model is not None and len(cl_model) == 81, f"{model}: expected 81 clusters"
    if CL is None:
        CL = cl_model
    else:
        assert cl_model == CL, f"{model}: cluster set differs from {MODELS[0]}"

assert all(g["gate_ok"] for g in GATECHECK), "a cell exceeded the 5% unparsed gate"

NC = len(CL)
cidx = {c: i for i, c in enumerate(CL)}
BOOT = {model: rng.integers(0, NC, (B, NC)) for model in MODELS}  # per-model resample, shared
                                                                    # across that model's 3 arms


def cluster_vectors(rows):
    """-> per-cluster (sum escalated, count parsed) for a single arm's rows."""
    s = np.zeros(NC)
    n = np.zeros(NC)
    for r in rows:
        if not r["parsed"]:
            continue
        i = cidx[(r["case"], r["item_id"])]
        s[i] += r["escalated"]
        n[i] += 1
    return s, n


def boot_rate(s, n, boot):
    tot_n = n.sum()
    pt = s.sum() / tot_n if tot_n else float("nan")
    bs = s[boot].sum(1)
    bn = n[boot].sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        br = np.where(bn > 0, bs / bn, np.nan)
    return pt, br


def ci(v, lo=2.5, hi=97.5):
    v = np.asarray(v, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return (float("nan"), float("nan"))
    return (float(np.percentile(v, lo)), float(np.percentile(v, hi)))


def excludes_zero(lo, hi):
    return bool((lo > 0 and hi > 0) or (lo < 0 and hi < 0))


# ---------------------------------------------------------------------------------------
# 1. per-arm point rate + bootstrap distribution, per model
# ---------------------------------------------------------------------------------------
RATE = {}
for model in MODELS:
    RATE[model] = {}
    for arm in ARMS:
        s, n = cluster_vectors(DATA[model][arm])
        pt, br = boot_rate(s, n, BOOT[model])
        lo, hi = ci(br)
        p = [r for r in DATA[model][arm] if r["parsed"]]
        RATE[model][arm] = dict(point=pt, ci=[lo, hi], boot=br, k=int(s.sum()), n=int(n.sum()),
                                n_parsed=len(p))

# ---------------------------------------------------------------------------------------
# 2. decomposition: N->I (NONE_INDEX - NO_ESCAPE) and I->E (ESCALATE - NONE_INDEX)
#    paired: same per-model bootstrap resample used for both terms of each contrast
# ---------------------------------------------------------------------------------------
DECOMP = {}
for model in MODELS:
    sN, nN = cluster_vectors(DATA[model]["NO_ESCAPE"])
    sI, nI = cluster_vectors(DATA[model]["NONE_INDEX"])
    sE, nE = cluster_vectors(DATA[model]["ESCALATE"])

    ptN, brN = boot_rate(sN, nN, BOOT[model])
    ptI, brI = boot_rate(sI, nI, BOOT[model])
    ptE, brE = boot_rate(sE, nE, BOOT[model])

    d_NI = brI - brN  # N -> I bootstrap distribution of the difference (paired by resample)
    d_IE = brE - brI  # I -> E

    lo_NI, hi_NI = ci(d_NI)
    lo_IE, hi_IE = ci(d_IE)

    # descriptive Fisher exact on the raw (unclustered) 2x2, consistent with the rest of the
    # pack's style (e.g. v2b_results.md section A) -- NOT the primary inferential CI, which is
    # the cluster bootstrap above.
    kN, nnN = RATE[model]["NO_ESCAPE"]["k"], RATE[model]["NO_ESCAPE"]["n"]
    kI, nnI = RATE[model]["NONE_INDEX"]["k"], RATE[model]["NONE_INDEX"]["n"]
    kE, nnE = RATE[model]["ESCALATE"]["k"], RATE[model]["ESCALATE"]["n"]
    _, p_NI = fisher_exact([[kI, nnI - kI], [kN, nnN - kN]])
    _, p_IE = fisher_exact([[kE, nnE - kE], [kI, nnI - kI]])

    DECOMP[model] = dict(
        NO_ESCAPE=dict(rate=ptN, k=kN, n=nnN),
        NONE_INDEX=dict(rate=ptI, k=kI, n=nnI),
        ESCALATE=dict(rate=ptE, k=kE, n=nnE),
        N_to_I=dict(delta=float(ptI - ptN), ci=[lo_NI, hi_NI], fisher_p=float(p_NI),
                    excludes_zero=excludes_zero(lo_NI, hi_NI)),
        I_to_E=dict(delta=float(ptE - ptI), ci=[lo_IE, hi_IE], fisher_p=float(p_IE),
                    excludes_zero=excludes_zero(lo_IE, hi_IE)),
        total_N_to_E=dict(delta=float(ptE - ptN)),
    )

# ---------------------------------------------------------------------------------------
# 3. write outputs
# ---------------------------------------------------------------------------------------
OUT_JSON = dict(
    meta=dict(seed=SEED, B=B, gate=GATE, cluster="(case, item_id)", n_clusters=NC,
              models=MODELS, arms=ARMS,
              note="EASY-81: every cluster has exactly 1 row (no margin-ladder rungs); "
                   "cluster bootstrap here reduces to item-level bootstrap."),
    gate_check=GATECHECK,
    rates={m: {a: dict(point=RATE[m][a]["point"], ci=RATE[m][a]["ci"], k=RATE[m][a]["k"],
                       n=RATE[m][a]["n"]) for a in ARMS} for m in MODELS},
    decomposition=DECOMP,
)
with open(os.path.join(OUTDIR, "easy81_none_index.json"), "w") as f:
    json.dump(OUT_JSON, f, indent=2, default=float)

lines = []
lines.append("# EASY-81 false-alarm decomposition: NO_ESCAPE -> NONE_INDEX -> ESCALATE\n")
lines.append(f"seed={SEED} | bootstrap B={B:,} | cluster=(case,item_id), n_clusters={NC} "
             f"| gate={GATE}\n")
lines.append("Every row in this supplement is label EASY (solver-certified feasible; "
             "served_load >= 0.99), so every escalation counted below is a FALSE ALARM -- "
             "the model declining a fully-resolving single action.\n")
lines.append("## 0. Gate check (all 9 cells: 3 models x 3 arms)\n")
lines.append("| model | arm | n | unparsed | rate | status | escalated/parsed | point rate |")
lines.append("|---|---|---|---|---|---|---|---|")
for g in GATECHECK:
    status = "ok" if g["gate_ok"] else "**GATED**"
    lines.append(f"| {g['model']} | {g['arm']} | {g['n']} | {g['unparsed']} | "
                 f"{g['unparsed_rate']:.4f} | {status} | {g['escalated']}/{g['n_parsed']} | "
                 f"{g['rate']:.4f} |" if g["rate"] is not None else
                 f"| {g['model']} | {g['arm']} | {g['n']} | {g['unparsed']} | "
                 f"{g['unparsed_rate']:.4f} | {status} | {g['escalated']}/{g['n_parsed']} | n/a |")
lines.append("")
lines.append("## 1. Per-model false-alarm rate by arm (cluster-bootstrap point + 95% CI)\n")
lines.append("| model | NO_ESCAPE | NONE_INDEX | ESCALATE |")
lines.append("|---|---|---|---|")
for m in MODELS:
    row = f"| {m} |"
    for a in ARMS:
        r = RATE[m][a]
        row += f" {r['point']:.4f} [{r['ci'][0]:.4f},{r['ci'][1]:.4f}] (k={r['k']}/{r['n']}) |"
    lines.append(row)
lines.append("")
lines.append("## 2. Decomposition: N->I (offering a bare decline slot) and I->E "
             "(naming it ESCALATE + human-operator language)\n")
lines.append("| model | N->I delta | 95% CI | excludes 0 | Fisher p | I->E delta | 95% CI | "
             "excludes 0 | Fisher p | total N->E |")
lines.append("|---|---|---|---|---|---|---|---|---|---|")
for m in MODELS:
    d = DECOMP[m]
    ni, ie = d["N_to_I"], d["I_to_E"]
    lines.append(
        f"| {m} | {ni['delta']:+.4f} | [{ni['ci'][0]:+.4f},{ni['ci'][1]:+.4f}] | "
        f"{'YES' if ni['excludes_zero'] else 'no'} | {ni['fisher_p']:.4f} | "
        f"{ie['delta']:+.4f} | [{ie['ci'][0]:+.4f},{ie['ci'][1]:+.4f}] | "
        f"{'YES' if ie['excludes_zero'] else 'no'} | {ie['fisher_p']:.4f} | "
        f"{d['total_N_to_E']['delta']:+.4f} |")
lines.append("")
n_excl = sum(1 for m in MODELS for k in ("N_to_I", "I_to_E") if DECOMP[m][k]["excludes_zero"])
lines.append(f"Components excluding zero: {n_excl} of {2*len(MODELS)}.\n")

with open(os.path.join(OUTDIR, "easy81_none_index.md"), "w") as f:
    f.write("\n".join(lines) + "\n")

print("wrote analysis/easy81_none_index.json and .md")
for m in MODELS:
    d = DECOMP[m]
    print(f"\n{m}")
    print(f"  NO_ESCAPE={d['NO_ESCAPE']['rate']:.4f} ({d['NO_ESCAPE']['k']}/{d['NO_ESCAPE']['n']})  "
          f"NONE_INDEX={d['NONE_INDEX']['rate']:.4f} ({d['NONE_INDEX']['k']}/{d['NONE_INDEX']['n']})  "
          f"ESCALATE={d['ESCALATE']['rate']:.4f} ({d['ESCALATE']['k']}/{d['ESCALATE']['n']})")
    print(f"  N->I: {d['N_to_I']['delta']:+.4f}  CI={d['N_to_I']['ci']}  "
          f"excludes0={d['N_to_I']['excludes_zero']}  fisher_p={d['N_to_I']['fisher_p']:.4f}")
    print(f"  I->E: {d['I_to_E']['delta']:+.4f}  CI={d['I_to_E']['ci']}  "
          f"excludes0={d['I_to_E']['excludes_zero']}  fisher_p={d['I_to_E']['fisher_p']:.4f}")
