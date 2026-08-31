"""Served-load threshold sensitivity sweep for the depth-2 escape-hatch audit.

Adapted from the pack's depth2.py (FIX 1 only -- the depth-2 INFEASIBLE audit; the EASY-minting
FIX 2 section is irrelevant to this question and dropped). Logic, menu, certify(), solve(),
build(), and the pair-search loop are copied verbatim from depth2.py / certify_v2.py so the
physics and the search procedure are unchanged. The only new axis is SERVED_TOL, which is swept
over {0.99, 0.95, 0.90} instead of being hardcoded at 0.99.

Runs entirely against local copies in the scratchpad dir:
  ./certify_v2.py       (verbatim copy of the pack's certify_v2.py)
  ./ladder_case30.json  (verbatim copy of the pack's ladder_case30.json)
No file in the original pack is read or written by this script (all paths are relative to CWD,
and CWD is the scratchpad dir when this is run).

Reproduction check: at SERVED_TOL=0.99, MAX_ITEM=10, PAIR_CAP=500, seed=20260827, this must
exactly reproduce depth2_v2.log's 0/10 result (same scenarios, same pair order per scenario,
since build()/certify() are deterministic and rng.shuffle is seeded identically and called in
the same sequence).
"""
import copy, json, itertools, time
import numpy as np
import pandapower as pp
from certify_v2 import CASES, baseline_limits, menu, certify, violations, solve, apply

CASE     = "case30"
MAX_ITEM = 10     # matches depth2_v2.log (the audited 10-scenario run)
PAIR_CAP = 500     # matches depth2_v2.log ("after 500 pairs" on every row)
SEED     = 20260827

base = CASES[CASE]()
L = baseline_limits(base)
ACTS = menu(base)
print(f"{CASE}: menu={len(ACTS)} actions -> {len(ACTS)*(len(ACTS)-1)//2} possible pairs", flush=True)

ladder = json.load(open(f"ladder_{CASE}.json"))


def build(tripped, scale):
    n = copy.deepcopy(base)
    n.line.at[tripped, "in_service"] = False
    n.load["p_mw"] *= scale; n.load["q_mvar"] *= scale
    if not solve(n): return None
    v = violations(n, L)
    if not v: return dict(net=n, label="NO_VIOLATION", fixers=[])
    lab, fx, ns = certify(n, L, ACTS)
    return dict(net=n, label=lab, fixers=fx, viol=v)


def clears(net_before_served, m, served_tol):
    """A scheme CLEARS only if violations are gone AND the load is still served >= served_tol."""
    if violations(m, L): return False
    served = float(m.res_load.p_mw.sum())
    if net_before_served > 0 and served / net_before_served < served_tol: return False
    return len(pp.topology.unsupplied_buses(m)) == 0 or served / max(net_before_served, 1e-9) >= served_tol


def depth2(net, rng, cap, served_tol):
    """Search PAIRS of actions (same enumeration/order as depth2.py). Returns
    (found, n_pairs_tried, example_texts, served_frac_achieved)."""
    served0 = float(net.res_load.p_mw.sum())
    idx = list(range(len(ACTS)))
    pairs = list(itertools.combinations(idx, 2))
    rng.shuffle(pairs)
    for k, (i, j) in enumerate(pairs[:cap]):
        n = copy.deepcopy(net)
        k1, i1, m1, t1 = ACTS[i]; k2, i2, m2, t2 = ACTS[j]
        n = apply(n, k1, i1, m1)
        n = apply(n, k2, i2, m2)
        if not solve(n): continue
        if clears(served0, n, served_tol):
            served_frac = float(n.res_load.p_mw.sum()) / served0 if served0 > 0 else 1.0
            return True, k + 1, [t1, t2], served_frac
    return False, min(cap, len(pairs)), None, None


# ---- reconstruct the same 10 unique INFEASIBLE scenarios depth2.py would select ----
infeas = []
for it in ladder["items"]:
    rungs = it.get("rungs", {})
    seq = list(rungs.values()) if isinstance(rungs, dict) else list(rungs)
    for sc in [it.get("anchor"), it.get("far_anchor")] + seq:
        if isinstance(sc, dict) and sc.get("label") == "INFEASIBLE":
            infeas.append((it["tripped_line"], sc["load_scale"]))
seen = set(); uniq = []
for t, s in infeas:
    if (t, round(s, 4)) in seen: continue
    seen.add((t, round(s, 4))); uniq.append((t, s))
print(f"unique INFEASIBLE scenarios available: {len(uniq)}; auditing {min(MAX_ITEM, len(uniq))}", flush=True)

scenarios = uniq[:MAX_ITEM]

results = {}
for served_tol in (0.99, 0.95, 0.90):
    print(f"\n### served-load threshold = {served_tol} ###", flush=True)
    rng = np.random.default_rng(SEED)   # re-seeded identically for every threshold
    rows = []
    t0 = time.time()
    for t, s in scenarios:
        b = build(t, s)
        if b is None or b["label"] != "INFEASIBLE":
            rows.append(dict(tripped=int(t), scale=float(s), skipped=True))
            print(f"  line {t:3d} scale {s:.4f}: SKIPPED (build failed or not INFEASIBLE)", flush=True)
            continue
        ok, tried, ex, served_frac = depth2(b["net"], rng, PAIR_CAP, served_tol)
        rows.append(dict(tripped=int(t), scale=float(s), depth2_fix=bool(ok),
                          pairs_tried=int(tried), example=ex,
                          served_frac=served_frac))
        print(f"  line {t:3d} scale {s:.4f}: depth-2 scheme {'FOUND' if ok else 'none'} "
              f"after {tried} pairs" + (f" -> {ex} (served={served_frac:.4f})" if ex else ""), flush=True)
    n2 = sum(1 for r in rows if r.get("depth2_fix"))
    print(f"  === served_tol={served_tol}: {n2}/{len(rows)} scenarios have a verified 2-action fix "
          f"(elapsed {time.time()-t0:.0f}s)")
    results[str(served_tol)] = dict(served_tol=served_tol, n_found=n2, n_total=len(rows), rows=rows)

json.dump(dict(case=CASE, max_item=MAX_ITEM, pair_cap=PAIR_CAP, seed=SEED, results=results),
          open("depth2_sensitivity.json", "w"), indent=1)
print("\nwrote depth2_sensitivity.json")
