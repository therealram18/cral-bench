"""
P1: verify the critique's claim that re-certifying the ladders with enforce_q_lims=True
flips certified-fixer labels for case30 / case39's EASY/TRICKY (fixable) scenarios.

Methodology: mirror certify_v2.py's solve/violations/apply logic EXACTLY, with the single
change of enforce_q_lims=True passed to pp.runpp() in solve(). Baseline-referenced limits L
are NOT recomputed -- we reuse the limits already stored in the ladder JSON (computed once,
under the original enforce_q_lims=False solve, exactly as certify_v2.py's baseline_limits()
produced them when the ladder was built). This isolates the effect of q_lims on the FIXER
RE-TEST from any effect on the reference/limit computation itself.

For every scenario in ladder_case30.json / ladder_case39.json whose original label is EASY or
TRICKY (the "fixable" classes -- rungs are always INFEASIBLE by construction in make_ladder.py,
so only anchor + far_anchor entries can ever be EASY/TRICKY):
  1. Reconstruct the exact net: base case, trip `tripped_line`, scale all loads by `load_scale`.
     (This exactly matches make_ladder.py's build().)
  2. Also resolve that *unmodified* scenario net under enforce_q_lims=True (no action applied)
     to check whether the base state itself still converges -- the critique calls this out
     separately as "base states diverge".
  3. For every action that was a CERTIFIED FIXER in the original (q_lims=False) run -- i.e.
     per_action[i]["clears"] == 1 -- apply that action (apply() copied verbatim from
     certify_v2.py) to the scenario net and re-solve with enforce_q_lims=True. Check violations
     against the SAME baseline-referenced limits L using violations() copied verbatim.
  4. If NONE of the originally-certified fixers still clear all violations under q_lims=True,
     the scenario's label would flip: EASY/TRICKY -> "no fixer survives" (both TRICKY, which had
     exactly 1 fixer, and EASY, which had >=2, count if ALL are lost).

Outputs a compact per-scenario table + summary counts to p1_results.json.
"""
import copy, json
import pandapower as pp
import pandapower.networks as nw

CASES = {"case14": nw.case14, "case30": nw.case30, "case39": nw.case39, "case118": nw.case118}


def solve_qlims(net, max_iteration=30):
    """Exactly certify_v2.solve(), except enforce_q_lims=True."""
    try:
        pp.runpp(net, numba=False, max_iteration=max_iteration, enforce_q_lims=True)
        return bool(net.converged)
    except Exception:
        return False


def violations(net, L):
    """Verbatim copy of certify_v2.violations()."""
    v = []
    for i, r in net.res_line[net.res_line.loading_percent > L["load_pct"]].iterrows():
        v.append(dict(kind="line", idx=int(i), val=round(float(r.loading_percent), 1),
                      text=f"line {i} loaded to {r.loading_percent:.0f}% (limit {L['load_pct']:.0f}%)"))
    b = net.res_bus
    for i, r in b[(b.vm_pu < L["v_min"]) | (b.vm_pu > L["v_max"])].iterrows():
        v.append(dict(kind="bus", idx=int(i), val=round(float(r.vm_pu), 4),
                      text=f"bus {i} voltage {r.vm_pu:.3f} pu "
                           f"(band {L['v_min']:.3f}-{L['v_max']:.3f})"))
    return v


def apply(net, kind, idx, mag):
    """Verbatim copy of certify_v2.apply()."""
    n = copy.deepcopy(net)
    if   kind == "gen_v_up":   n.gen.at[idx, "vm_pu"] += mag
    elif kind == "gen_v_dn":   n.gen.at[idx, "vm_pu"] -= mag
    elif kind == "gen_p_up":   n.gen.at[idx, "p_mw"] *= (1 + mag)
    elif kind == "gen_p_dn":   n.gen.at[idx, "p_mw"] *= (1 - mag)
    elif kind == "slack_v_up": n.ext_grid.at[idx, "vm_pu"] += mag
    elif kind == "slack_v_dn": n.ext_grid.at[idx, "vm_pu"] -= mag
    elif kind == "tap_up":     n.trafo.at[idx, "tap_pos"] += 1
    elif kind == "tap_dn":     n.trafo.at[idx, "tap_pos"] -= 1
    elif kind == "shunt_on":   n.shunt.at[idx, "in_service"] = True
    elif kind == "shunt_off":  n.shunt.at[idx, "in_service"] = False
    elif kind == "shed":       n.load.at[idx, "p_mw"] *= (1 - mag); n.load.at[idx, "q_mvar"] *= (1 - mag)
    elif kind == "open_line":  n.line.at[idx, "in_service"] = False
    else: raise ValueError(kind)
    return n


def build_scenario(base, tripped_line, load_scale):
    """Exactly make_ladder.py's build(): trip one line, scale ALL loads (p and q)."""
    n = copy.deepcopy(base)
    n.line.at[tripped_line, "in_service"] = False
    n.load["p_mw"] *= load_scale
    n.load["q_mvar"] *= load_scale
    return n


def collect_fixable_entries(ladder):
    """Every EASY/TRICKY entry among anchor + far_anchor (rungs are always INFEASIBLE)."""
    out = []
    for it in ladder["items"]:
        if it["anchor"]["label"] in ("EASY", "TRICKY"):
            out.append((it["item_id"], "anchor", it["anchor"]))
        if it["far_anchor"] and it["far_anchor"]["label"] in ("EASY", "TRICKY"):
            out.append((it["item_id"], "far_anchor", it["far_anchor"]))
        for ri, r in enumerate(it["rungs"]):
            if r["label"] in ("EASY", "TRICKY"):
                out.append((it["item_id"], f"rung[{ri}] delta={r['delta']}", r))
    return out


def run_case(case_name, ladder_path):
    ladder = json.load(open(ladder_path))
    base = CASES[case_name]()
    L = ladder["limits"]
    menu = ladder["menu"]  # order-matched to per_action in every entry (verified separately)

    entries = collect_fixable_entries(ladder)
    rows = []
    for item_id, tag, e in entries:
        tripped, scale = e["tripped_line"], e["load_scale"]
        old_label, old_nfix = e["label"], e["n_fixers"]

        # sanity: recount old fixers from per_action to make sure our indexing is right
        fixer_idx = [i for i, pa in enumerate(e["per_action"]) if pa["clears"] == 1]
        assert len(fixer_idx) == old_nfix, (case_name, item_id, tag, len(fixer_idx), old_nfix)
        for i in fixer_idx:
            assert menu[i]["kind"] == e["per_action"][i]["kind"]
            assert menu[i]["idx"] == e["per_action"][i]["idx"]

        scen_net = build_scenario(base, tripped, scale)

        # base-state convergence under q_lims=True (no action applied)
        base_ok = solve_qlims(copy.deepcopy(scen_net))

        survivors, lost = [], []
        for i in fixer_idx:
            m = menu[i]
            n2 = apply(scen_net, m["kind"], m["idx"], m["mag"])
            ok = solve_qlims(n2)
            still_clears = ok and not violations(n2, L)
            (survivors if still_clears else lost).append(dict(kind=m["kind"], idx=m["idx"],
                                                                text=m["text"], solved=ok))

        new_nfix = len(survivors)
        flipped_all_lost = (new_nfix == 0)
        rows.append(dict(
            case=case_name, item_id=item_id, tag=tag, tripped_line=tripped, load_scale=scale,
            old_label=old_label, old_n_fixers=old_nfix,
            base_state_converges_qlims=base_ok,
            new_n_fixers_surviving=new_nfix,
            all_fixers_lost=flipped_all_lost,
            lost_action_kinds=[a["kind"] for a in lost],
            surviving_action_kinds=[a["kind"] for a in survivors],
        ))
        print(f"{case_name} item={item_id:2d} {tag:22s} old={old_label:7s}(nfx={old_nfix}) "
              f"base_qlims_converges={base_ok} new_nfix={new_nfix} "
              f"{'FLIP->INFEASIBLE' if flipped_all_lost else 'ok'}", flush=True)
    return rows


if __name__ == "__main__":
    all_rows = []
    for case, path in [("case30", "ladder_case30.json"), ("case39", "ladder_case39.json")]:
        all_rows += run_case(case, path)

    json.dump(all_rows, open("p1_results.json", "w"), indent=1)

    from collections import Counter
    print("\n=== SUMMARY ===")
    for case in ("case30", "case39"):
        rows = [r for r in all_rows if r["case"] == case]
        n_total = len(rows)
        n_flip_easy = sum(1 for r in rows if r["all_fixers_lost"] and r["old_label"] == "EASY")
        n_flip_tricky = sum(1 for r in rows if r["all_fixers_lost"] and r["old_label"] == "TRICKY")
        n_base_diverge = sum(1 for r in rows if not r["base_state_converges_qlims"])
        n_flip_total = n_flip_easy + n_flip_tricky
        lost_kinds = Counter()
        for r in rows:
            if r["all_fixers_lost"]:
                lost_kinds.update(r["lost_action_kinds"])
        print(f"{case}: fixable_total={n_total} "
              f"EASY->flip={n_flip_easy} TRICKY->flip={n_flip_tricky} "
              f"total_flip={n_flip_total} ({100*n_flip_total/n_total:.1f}%) "
              f"base_states_diverge={n_base_diverge}")
        print(f"   lost action-kind counts: {dict(lost_kinds)}")
