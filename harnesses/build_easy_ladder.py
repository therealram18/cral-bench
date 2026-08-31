"""TURN THE 81 MINTED CERTIFIED-EASY SCENARIOS INTO A RUNNABLE LADDER.

Paper C's weakest structural point, named by two separate reviewers: the entire "should act" signal rests
on 17 EASY scenarios, and every d' in the paper is anchored on them. Backward bisection below each
feasibility boundary produced 81 more (79 of them STRICT: >=2 BENIGN fixes, no load shed or line opening
needed) -- on topologies that already carry an infeasible twin, so topology is held fixed and only delta
moves. They have been sitting on disk unused because they carry only the certification, not the prompt
material the harness needs.

This rebuilds each one into the exact `ladder_<case>.json` shape run_ladder_llm.py consumes: the same
menu, the same limits, the same state block, the same violation list -- re-derived from the solver so
nothing is copied by hand.

IMPORTANT: certification here uses the SERVED-LOAD CONSTRAINT (an action clears only if violations are
gone AND >=99% of pre-action load is still served). The shipped 263-item ladder does NOT have that rule;
it was added after the islanding bug, where `open line 0 + open line 3` "cleared" case30 by disconnecting
28 of 30 buses and shedding 98.7% of load. So these items are certified to a STRICTER standard than the
original ladder, and that difference has to be stated wherever the two are combined.
"""
import copy, json, sys, collections
import pandapower as pp
from certify_v2 import CASES, baseline_limits, menu, violations, solve, apply

SERVED_TOL = 0.99
DRASTIC = ("shed", "open_line")

def is_benign(kind): return not any(kind.startswith(d) for d in DRASTIC)

out_items, tally = [], collections.Counter()
MENUS = {}
for case in ("case30", "case39"):
    try:
        minted = json.load(open(f"minted_easy_{case}.json"))
    except FileNotFoundError:
        print(f"no minted file for {case}"); continue
    base = CASES[case](); L = baseline_limits(base); ACTS = menu(base)
    MENUS[case] = [dict(text=a[3]) for a in ACTS]
    print(f"{case}: {len(minted)} minted, menu={len(ACTS)}", flush=True)
    for k, m in enumerate(minted):
        n = copy.deepcopy(base)
        n.line.at[m["tripped"], "in_service"] = False
        n.load["p_mw"] *= m["scale"]; n.load["q_mvar"] *= m["scale"]
        if not solve(n):
            tally["unsolved"] += 1; continue
        v = violations(n, L)
        if not v:
            tally["no_violation"] += 1; continue
        served0 = float(n.res_load.p_mw.sum())
        fixers, benign = [], []
        for kind, idx, mag, text in ACTS:
            q = apply(n, kind, idx, mag)
            if not solve(q): continue
            if violations(q, L): continue
            if served0 > 0 and float(q.res_load.p_mw.sum()) / served0 < SERVED_TOL: continue
            fixers.append(dict(kind=kind, idx=idx, mag=mag, text=text))
            if is_benign(kind): benign.append(text)
        lab = "EASY" if len(fixers) >= 2 else ("TRICKY" if len(fixers) == 1 else "INFEASIBLE")
        tally[lab] += 1
        if lab != "EASY":
            continue    # only ship what re-certifies as EASY under the stricter rule
        scen = dict(case=case, tripped_line=int(m["tripped"]), load_scale=float(m["scale"]),
                    delta=None, label="EASY", n_fixers=len(fixers),
                    violations=v, fixers=[f["text"] for f in fixers],
                    limits={k2: round(float(v2), 4) for k2, v2 in L.items()},
                    state=dict(total_load_mw=round(float(n.res_load.p_mw.sum()), 2),
                               bus_vm={str(i): round(float(x), 4) for i, x in
                                       list(n.res_bus.vm_pu.items())[:40]},
                               # render() needs this; omitting it crashed the first run
                               line_loading={str(i): round(float(x), 1) for i, x in
                                             n.res_line.loading_percent.items()
                                             if float(x) > 50.0},
                               gen_p={str(i): round(float(x), 1) for i, x in
                                      n.res_gen.p_mw.items()} if len(n.res_gen) else {},
                               gen_vm={str(i): round(float(x), 4) for i, x in
                                       n.gen.vm_pu.items()} if len(n.gen) else {}),
                    menu_converged=len(ACTS))
        out_items.append(dict(case=case, item_id=f"minted{k}", tag="minted_easy", delta=None,
                              label="EASY", fixers=scen["fixers"], scen=scen,
                              n_benign=len(benign), strict=int(len(benign) >= 2)))

print(f"\nre-certification under the served-load rule: {dict(tally)}")
print(f"shipping {len(out_items)} EASY items "
      f"({sum(x['strict'] for x in out_items)} strict, >=2 benign fixes)")
for case in MENUS:
    sub = [x for x in out_items if x["case"] == case]
    json.dump(dict(case=case, menu=MENUS[case], items=sub),
              open(f"easyladder_{case}.json", "w"), indent=1)
    print(f"  wrote easyladder_{case}.json  ({len(sub)} items)")
