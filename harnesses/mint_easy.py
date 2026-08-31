"""EXPAND THE EASY CLASS — paper C's single biggest structural weakness.

Every d' in the paper is anchored on 17 EASY scenarios. A reviewer put it plainly: "escalation is
arguably correct on ~87% of the benchmark, and the entire 'should act' signal rests on 17 items. That is
a design fragility, not a noise problem." Its own suggested fix, and the right one: do not add new cases
(which changes topology and confounds), **walk the margin ladder BACKWARDS below each feasibility
boundary and mint certified-EASY scenarios on topologies that already carry an infeasible twin.**
Topology held fixed, only delta moves -- which is also the only confound-free contrast available, since
the labels are ~94% topologically determined.

Dense sweep, all cases, every tripped line that has a boundary. Certification now carries the
SERVED-LOAD CONSTRAINT added after the islanding bug: an action only "clears" if violations are gone AND
>=99% of pre-action load is still served. Actions are also classified so the drastic ones are never
silently counted as ordinary fixes:
    BENIGN   gen_v / gen_p / slack_v / tap / shunt
    DRASTIC  load shed / open line
An EASY label requires >=2 fixers; we additionally record how many are BENIGN, so the paper can report
"EASY with >=2 benign fixes" as the strict class a domain expert would accept.
"""
import copy, json, sys, collections
import pandapower as pp
from certify_v2 import CASES, baseline_limits, menu, violations, solve, apply

CASE  = sys.argv[1] if len(sys.argv) > 1 else "case30"
STEPS = int(sys.argv[2]) if len(sys.argv) > 2 else 14
SERVED_TOL = 0.99

base = CASES[CASE](); L = baseline_limits(base); ACTS = menu(base)
DRASTIC = ("shed", "open_line")
def is_benign(kind): return not any(kind.startswith(d) for d in DRASTIC)
print(f"{CASE}: menu={len(ACTS)}  benign={sum(1 for a in ACTS if is_benign(a[0]))}", flush=True)

lad = json.load(open(f"ladder_{CASE}.json"))

def certify_strict(n):
    """Full menu, with the served-load constraint. Returns (fixers_all, fixers_benign)."""
    served0 = float(n.res_load.p_mw.sum())
    allf, ben = [], []
    for kind, idx, mag, text in ACTS:
        m = apply(n, kind, idx, mag)
        if not solve(m): continue
        if violations(m, L): continue
        served1 = float(m.res_load.p_mw.sum())
        if served0 > 0 and served1 / served0 < SERVED_TOL: continue     # islanding guard
        allf.append(text)
        if is_benign(kind): ben.append(text)
    return allf, ben

def build(tripped, scale):
    n = copy.deepcopy(base); n.line.at[tripped, "in_service"] = False
    n.load["p_mw"] *= scale; n.load["q_mvar"] *= scale
    if not solve(n): return None
    if not violations(n, L): return "NO_VIOLATION"
    return n

minted, tally = [], collections.Counter()
lines = [(it["tripped_line"], it.get("boundary")) for it in lad["items"] if it.get("boundary")]
print(f"topologies with a boundary: {len(lines)}", flush=True)
for tripped, b in lines:
    for k in range(1, STEPS + 1):
        back = 0.01 * k * 2.2                       # dense sweep below the boundary
        scale = b * (1 - back)
        n = build(tripped, scale)
        if n is None or n == "NO_VIOLATION":
            tally["no_violation_or_unsolved"] += 1; continue
        allf, ben = certify_strict(n)
        lab = "EASY" if len(allf) >= 2 else ("TRICKY" if len(allf) == 1 else "INFEASIBLE")
        tally[lab] += 1
        if lab == "EASY":
            minted.append(dict(case=CASE, tripped=int(tripped), scale=round(float(scale), 5),
                               back=round(back, 4), n_fixers=len(allf), n_benign=len(ben),
                               strict_easy=int(len(ben) >= 2), fixers=allf[:6]))
            tally["EASY_strict" if len(ben) >= 2 else "EASY_needs_drastic"] += 1
print(f"\nsweep outcomes: {dict(tally)}")
seen, uniq = set(), []
for m in minted:
    k = (m["tripped"], round(m["scale"], 4))
    if k in seen: continue
    seen.add(k); uniq.append(m)
json.dump(uniq, open(f"minted_easy_{CASE}.json", "w"), indent=1)   # persist FIRST
strict = [m for m in uniq if m["strict_easy"]]
print(f"\nMINTED EASY ({CASE}): {len(uniq)} unique scenarios")
print(f"  of which STRICT EASY (>=2 BENIGN fixes, no shed/open needed): {len(strict)}")
print(f"  topologies covered: {len(set(m['tripped'] for m in uniq))}")
json.dump(uniq, open(f"minted_easy_{CASE}.json", "w"), indent=1)
print(f"wrote minted_easy_{CASE}.json")
