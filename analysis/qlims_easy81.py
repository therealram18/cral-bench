"""
Step 3: re-certify the EASY-81 minted items (easyladder_case{30,39}.json) with
enforce_q_lims=True, on top of the served-load rule they already carry (>=99% of
pre-action load served -- build_easy_ladder.py's SERVED_TOL=0.99). They were never
certified with q_lims before (certify_v2.solve() has no enforce_q_lims arg).

Methodology, mirroring p1_qlims_flip.py's design exactly:
  - Reconstruct each scenario net: base case + tripped line + load scale (identical to
    build_easy_ladder.py: n.line.at[tripped,'in_service']=False; loads *= scale).
  - Baseline-referenced limits L = certify_v2.baseline_limits(base), computed ONCE per
    case under q_lims=False -- NOT recomputed under q_lims=True, isolating the effect of
    q_lims on the fixer re-test only (same principle as p1).
  - served0 = the ORIGINALLY-recorded pre-action served load (scen['state']['total_load_mw'],
    a q_lims=False solve of the unmodified scenario net) -- reused, not recomputed, for the
    same isolation reason.
  - Re-test every ORIGINALLY-certified fixer (scen['fixers'], matched back to
    certify_v2.menu(base) by exact text) by applying it and solving with
    enforce_q_lims=True; it survives iff the solve converges, violations() against L is
    empty, AND served-after / served0 >= 0.99.
  - Also record whether the unmodified scenario net (no action) converges under
    enforce_q_lims=True, as a diagnostic (mirrors p1's base_state_converges_qlims).
  - new_label: EASY (>=2 survive), TRICKY (==1), INFEASIBLE (0).
"""
import copy, json, os
from certify_v2 import CASES, baseline_limits, menu, violations, apply
import pandapower as pp

ROOT = "/path/to/cral_original_pack/powergrid"  # anonymized original pack root; see README "Anonymization note"
SERVED_TOL = 0.99


def solve_qlims(net, max_iteration=30):
    try:
        pp.runpp(net, numba=False, max_iteration=max_iteration, enforce_q_lims=True)
        return bool(net.converged)
    except Exception:
        return False


def build_scenario(base, tripped_line, load_scale):
    n = copy.deepcopy(base)
    n.line.at[tripped_line, "in_service"] = False
    n.load["p_mw"] *= load_scale
    n.load["q_mvar"] *= load_scale
    return n


rows = []
for case in ("case30", "case39"):
    d = json.load(open(os.path.join(ROOT, f"easyladder_{case}.json")))
    base = CASES[case]()
    L = baseline_limits(base)
    ACTS = menu(base)  # list of (kind, idx, mag, text)
    text_to_act = {a[3]: a for a in ACTS}

    for it in d["items"]:
        scen = it["scen"]
        tripped, scale = scen["tripped_line"], scen["load_scale"]
        served0 = scen["state"]["total_load_mw"]
        old_fixer_texts = scen["fixers"]
        assert len(old_fixer_texts) == scen["n_fixers"] == len(it["fixers"])

        scen_net = build_scenario(base, tripped, scale)
        base_ok = solve_qlims(copy.deepcopy(scen_net))

        survivors, lost = [], []
        for text in old_fixer_texts:
            kind, idx, mag, _ = text_to_act[text]
            n2 = apply(scen_net, kind, idx, mag)
            ok = solve_qlims(n2)
            served_after = float(n2.res_load.p_mw.sum()) if ok else None
            served_ok = ok and served0 > 0 and (served_after / served0) >= SERVED_TOL
            clears = ok and not violations(n2, L) and served_ok
            (survivors if clears else lost).append(text)

        new_nfix = len(survivors)
        new_label = "EASY" if new_nfix >= 2 else ("TRICKY" if new_nfix == 1 else "INFEASIBLE")
        rows.append(dict(
            case=case, item_id=it["item_id"], tripped_line=tripped, load_scale=scale,
            old_label="EASY", old_n_fixers=len(old_fixer_texts),
            base_state_converges_qlims=base_ok,
            new_n_fixers_surviving=new_nfix, new_label=new_label,
            survives_as_easy=(new_label == "EASY"),
            lost_fixer_texts=lost, surviving_fixer_texts=survivors,
        ))
        print(f"{case} {it['item_id']:10s} old_nfix={len(old_fixer_texts)} "
              f"base_qlims_converges={base_ok} new_nfix={new_nfix} new_label={new_label}",
              flush=True)

json.dump(rows, open("p3_easy81_results.json", "w"), indent=1)

n_total = len(rows)
n_easy = sum(1 for r in rows if r["survives_as_easy"])
n_tricky = sum(1 for r in rows if r["new_label"] == "TRICKY")
n_infeasible = sum(1 for r in rows if r["new_label"] == "INFEASIBLE")
n_base_diverge = sum(1 for r in rows if not r["base_state_converges_qlims"])
print(f"\n=== EASY-81 SUMMARY ===")
print(f"total={n_total} survive_EASY={n_easy} demoted_TRICKY={n_tricky} "
      f"demoted_INFEASIBLE={n_infeasible} base_states_diverge={n_base_diverge}")
by_case = {}
for case in ("case30", "case39"):
    cr = [r for r in rows if r["case"] == case]
    by_case[case] = dict(total=len(cr), easy=sum(r["survives_as_easy"] for r in cr))
print("by case:", by_case)
