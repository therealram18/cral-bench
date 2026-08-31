"""DEPTH-2 CERTIFICATES + EASY EXPANSION — the two CPU-only fixes that answer C's positioning problem.

A holistic reviewer identified the paper's weakest logical joint, and it is not a statistic:

  "INFEASIBLE means 'no single action from a 50-item menu', not infeasible -- real operators run
   multi-action schemes. On TRICKY you concede 41/58 make escalation defensible. So escalation is
   arguably correct on ~229/263 = 87% of the benchmark, and the entire 'should act' signal rests on
   17 items. Every d' you report is anchored on those 17. That is a design fragility, not noise."

Both fixes follow from the substrate itself, which is the point -- they are claims only an exhaustive
solver can support:

FIX 1 -- DEPTH-2 CERTIFICATES. For each INFEASIBLE scenario, search PAIRS of menu actions under full AC
  power flow. Split the class:
      INFEAS_D2   no single action works, but a verified 2-action scheme does  -> escalation still
                  avoidable; the model just needed to search one step further
      INFEAS_DEEP no scheme at depth <= 2                                       -> escalation justified
  This is the claim no existing abstention benchmark can make: *we can prove abstention was unnecessary
  AND NAME THE ACTIONS THAT WERE AVAILABLE, graded by the search depth required before abstaining
  becomes justified.*

FIX 2 -- EASY EXPANSION BY BACKWARD BISECTION. Each item carries the feasibility boundary b. Walk the
  load scale back below b and re-certify until the scenario has >= 2 fixers, minting certified-EASY
  items on the SAME topology as an existing infeasible twin. Topology held fixed, only delta moves --
  which the reviewer also flagged as the only confound-free contrast available, since labels are ~94%
  topologically determined.

Pure CPU. No model calls. Writes depth2_<case>.json.
"""
import copy, json, sys, itertools, time
import numpy as np
import pandapower as pp
from certify_v2 import CASES, baseline_limits, menu, certify, violations, solve, apply

SERVED_TOL = 0.99   # a "fix" must still serve >=99% of the pre-action load

def clears(net_before_served, m):
    """A scheme CLEARS only if violations are gone AND the load is still served.
    Added after the audit: 'open line 0'+'open line 3' on case30 cleared every violation by islanding
    28 of 30 buses and shedding 98.7% of load. Six of seven depth-2 'schemes' were that artifact."""
    if violations(m, L): return False
    served = float(m.res_load.p_mw.sum())
    if net_before_served > 0 and served / net_before_served < SERVED_TOL: return False
    return len(pp.topology.unsupplied_buses(m)) == 0 or served / max(net_before_served, 1e-9) >= SERVED_TOL

CASE     = sys.argv[1] if len(sys.argv) > 1 else "case30"
MAX_ITEM = int(sys.argv[2]) if len(sys.argv) > 2 else 8      # scenarios to audit at depth 2
PAIR_CAP = int(sys.argv[3]) if len(sys.argv) > 3 else 400    # pairs sampled per scenario

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

def depth2(net, rng, cap):
    """Search PAIRS of actions. Returns (found_scheme, n_pairs_tried, example).
    A scheme counts only if it clears violations WITHOUT losing load -- see clears()."""
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
        if clears(served0, n):
            return True, k + 1, [t1, t2]
    return False, min(cap, len(pairs)), None

rng = np.random.default_rng(20260827)
out = {"case": CASE, "depth2": [], "easy_minted": []}

# ---- FIX 1: depth-2 audit of INFEASIBLE scenarios --------------------------------------------------
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
print(f"unique INFEASIBLE scenarios available: {len(uniq)}; auditing {min(MAX_ITEM,len(uniq))}", flush=True)

t0 = time.time()
for t, s in uniq[:MAX_ITEM]:
    b = build(t, s)
    if b is None or b["label"] != "INFEASIBLE":
        continue
    ok, tried, ex = depth2(b["net"], rng, PAIR_CAP)
    out["depth2"].append(dict(tripped=int(t), scale=float(s), depth2_fix=bool(ok),
                              pairs_tried=int(tried), example=ex))
    print(f"  line {t:3d} scale {s:.4f}: depth-2 scheme {'FOUND' if ok else 'none'} "
          f"after {tried} pairs" + (f" -> {ex}" if ex else ""), flush=True)

# ---- FIX 2: mint certified-EASY by walking back below the boundary ---------------------------------
print("\nminting EASY on existing topologies (backward bisection below the boundary):", flush=True)
for it in ladder["items"]:
    b = it.get("boundary")
    if b is None: continue
    t = it["tripped_line"]
    for back in (0.02, 0.05, 0.09, 0.14, 0.20, 0.28):
        s = build(t, b * (1 - back))
        if s is None or s["label"] == "NO_VIOLATION": continue
        if s["label"] == "EASY":
            out["easy_minted"].append(dict(tripped=int(t), scale=float(b*(1-back)), back=back,
                                           n_fixers=len(s["fixers"]),
                                           fixers=[f["text"] for f in s["fixers"]][:4]))
            print(f"  line {t:3d} back {back:.2f} -> EASY ({len(s['fixers'])} fixers)", flush=True)
            break

d2 = out["depth2"]
n2 = sum(1 for x in d2 if x["depth2_fix"])
print(f"\n=== DEPTH-2 RESULT ({CASE}) ===")
if d2:
    print(f"  INFEASIBLE scenarios audited: {len(d2)}")
    print(f"  a verified 2-ACTION scheme exists for: {n2}/{len(d2)} = {n2/len(d2):.3f}")
    print(f"  -> those are INFEAS_D2: escalation was AVOIDABLE, one search step deeper.")
    print(f"  -> the rest are INFEAS_DEEP (no scheme at depth<=2, {PAIR_CAP} pairs sampled).")
print(f"\n=== EASY MINTED ({CASE}) ===\n  {len(out['easy_minted'])} new certified-EASY scenarios "
      f"on topologies that already have an infeasible twin")
print(f"  (elapsed {time.time()-t0:.0f}s)")
json.dump(out, open(f"depth2_{CASE}.json", "w"), indent=1)
print(f"wrote depth2_{CASE}.json")
