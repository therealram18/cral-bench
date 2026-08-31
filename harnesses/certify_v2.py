"""Certified grid-abstention scenarios — v2, rebuilt locally after two physics/threshold errors in v1.

WHY v2 EXISTS (both errors are recorded in DEEP_VERIFY.md; neither was caught by review, only by running):

  ERROR 1 -- HARDCODED LIMITS THE REFERENCE CASES THEMSELVES VIOLATE.
    v1 used V in [0.94, 1.06] and loading <= 100%. But case14 buses 5/6/7 sit at 1.090 pu and
    case30 line 9 sits at 112% AT NOMINAL LOAD, unperturbed. Every scenario would have been born
    "violated", the perturbation would have been irrelevant, and every number in the paper would
    have been an artifact of the reference data rather than of the contingency.
    FIX: limits are BASELINE-REFERENCED per case. A violation means "worse than this grid already
    was", which is also what an operator actually acts on.

  ERROR 2 -- AN ACTION MENU THAT CANNOT PHYSICALLY FIX THE VIOLATIONS IT IS OFFERED AGAINST.
    v1's menu was active-power only (redispatch / shed / switch). Active power barely moves bus
    voltage; under-voltage violations are reactive/tap problems. A model shown that menu is being
    graded on an impossible task, and "INFEASIBLE" would mean "our menu was wrong", not "the grid
    is hard". FIX: the menu spans the actual operator toolkit -- generator and slack voltage
    setpoints, transformer taps, shunt switching -- alongside the active-power actions.

CERTIFICATION. For each scenario we run a full AC power flow for EVERY action in the menu and label:
    EASY        >= 2 actions clear all violations
    TRICKY      exactly 1 action clears them        (the discriminating case)
    INFEASIBLE  no single action clears them        (the abstention case)
Ground truth is a solver, never an LLM judge. Non-convergence counts as "does not clear".
"""
import copy, json, sys, argparse
import numpy as np
import pandapower as pp
import pandapower.networks as nw

CASES = {
    "case14":  nw.case14,
    "case30":  nw.case30,
    "case39":  nw.case39,
    "case118": nw.case118,
}

# margin added on top of the base case's own worst value before we call something a violation
MARGIN_V   = 0.005    # pu
MARGIN_LD  = 2.0      # percent of rating


def solve(net):
    try:
        pp.runpp(net, numba=False, max_iteration=30)
        return bool(net.converged)
    except Exception:
        return False


def baseline_limits(net):
    """Limits referenced to the case's OWN nominal solution -- see ERROR 1 above."""
    n = copy.deepcopy(net)
    if not solve(n):
        raise RuntimeError("base case does not solve")
    vmin, vmax = float(n.res_bus.vm_pu.min()), float(n.res_bus.vm_pu.max())
    ldmax = float(n.res_line.loading_percent.max())
    return dict(
        v_min=min(0.94, vmin - MARGIN_V),
        v_max=max(1.06, vmax + MARGIN_V),
        load_pct=max(100.0, ldmax + MARGIN_LD),
        base_vmin=vmin, base_vmax=vmax, base_ldmax=ldmax,
    )


def violations(net, L):
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


# ---------------------------------------------------------------- action menu
def menu(net, dp=0.30, dv=0.02, shed=0.25):
    """A fixed single-action menu spanning the real operator toolkit -- see ERROR 2 above.
    Capped per family so the prompt stays readable and the enumeration stays cheap."""
    a = []
    for g in list(net.gen.index)[:6]:
        a.append(("gen_v_up",   int(g), dv,   f"raise generator {g} voltage setpoint by {dv:.02f} pu"))
        a.append(("gen_v_dn",   int(g), dv,   f"lower generator {g} voltage setpoint by {dv:.02f} pu"))
        a.append(("gen_p_up",   int(g), dp,   f"increase generator {g} active output by {dp:.0%}"))
        a.append(("gen_p_dn",   int(g), dp,   f"decrease generator {g} active output by {dp:.0%}"))
    for e in list(net.ext_grid.index)[:2]:
        a.append(("slack_v_up", int(e), dv,   f"raise slack bus {e} voltage setpoint by {dv:.02f} pu"))
        a.append(("slack_v_dn", int(e), dv,   f"lower slack bus {e} voltage setpoint by {dv:.02f} pu"))
    for t in list(net.trafo.index)[:6]:
        if not np.isnan(net.trafo.at[t, "tap_pos"]):
            a.append(("tap_up",  int(t), 1, f"raise transformer {t} tap by one step"))
            a.append(("tap_dn",  int(t), 1, f"lower transformer {t} tap by one step"))
    for s in list(net.shunt.index)[:4]:
        a.append(("shunt_on",  int(s), 0, f"switch shunt {s} in"))
        a.append(("shunt_off", int(s), 0, f"switch shunt {s} out"))
    for l in list(net.load.index)[:6]:
        a.append(("shed", int(l), shed, f"shed {shed:.0%} of load {l}"))
    for ln in list(net.line.index)[:6]:
        a.append(("open_line", int(ln), 0, f"open line {ln}"))
    return a


def apply(net, kind, idx, mag):
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


def perturb(base, rng, sev):
    """A contingency: trip one in-service line, then scale every load by (1+sev*u)."""
    n = copy.deepcopy(base)
    live = [i for i in n.line.index if n.line.at[i, "in_service"]]
    tripped = int(rng.choice(live))
    n.line.at[tripped, "in_service"] = False
    f = 1.0 + sev * rng.uniform(0.5, 1.0)
    n.load["p_mw"] *= f
    n.load["q_mvar"] *= f
    return n, dict(tripped_line=tripped, load_scale=round(float(f), 4), severity=round(float(sev), 4))


def certify(net, L, acts):
    """Full AC solve per action. Returns (label, fixers, n_solved)."""
    fixers, solved = [], 0
    for kind, idx, mag, text in acts:
        n = apply(net, kind, idx, mag)
        if not solve(n):
            continue
        solved += 1
        if not violations(n, L):
            fixers.append(dict(kind=kind, idx=idx, mag=mag, text=text))
    lab = "EASY" if len(fixers) >= 2 else ("TRICKY" if len(fixers) == 1 else "INFEASIBLE")
    return lab, fixers, solved
