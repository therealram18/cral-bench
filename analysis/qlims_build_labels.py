"""
Build the q-limited label map for all 263 (case, item_id, tag) rows.

GT (old label) construction is copied verbatim from analysis/v2_sdt_analysis.py Section 0
(same DRASTIC_KINDS, same tag naming: "anchor", "far", "rung{delta}").

Overlay: for the 75 EASY/TRICKY (fixable) rows, p1_results.json (independently re-verified
byte-identical against a fresh re-run in this session; reconstruction pre-check 75/75 clean)
gives new_n_fixers_surviving under enforce_q_lims=True re-test of every originally-certified
fixer, against the SAME baseline-referenced limits. Rungs are always INFEASIBLE by construction
(make_ladder.py) and are not re-tested -- enforcing reactive limits is a strictly additional
constraint on the AC solve (it can only clip Q at a PV bus and let voltage sag further; it
cannot relax a violation), so a scenario with zero clearing actions under q_lims=False provably
has zero clearing actions under q_lims=True too. That is the physical justification, stated
explicitly, for not re-running the other 188 rows.

New label rule per fixable row:
  new_n_fixers_surviving == 0  -> INFEASIBLE  (flip)
  new_n_fixers_surviving == 1  -> TRICKY
  new_n_fixers_surviving >= 2  -> EASY

One row (case39, item 0, anchor) has base_state_converges_qlims == False: the *unmodified*
scenario net (no action applied) already fails to converge under q_lims=True. Its
new_n_fixers_surviving is also 0 (consistent -- if the base state won't even solve, no action
can be verified to clear it), so under the "count divergence as INFEASIBLE" convention it is
already folded into new_label=INFEASIBLE. We ADDITIONALLY flag it base_diverges=True and report
composition/analysis numbers both WITH it (as INFEASIBLE, the default) and WITHOUT it (excluded
entirely, denominator 262), per the task's instruction.
"""
import json, os, collections

ROOT = "/path/to/cral_original_pack/powergrid"  # anonymized original pack root; see README "Anonymization note"
QLIMS_RESULTS = "/path/to/anonymized/scratchpad/p1_results.json"  # anonymized session-scratch path; see README "Anonymization note"
OUT = os.path.join(ROOT, "analysis", "qlims_labels.json")

DRASTIC_KINDS = ("shed", "open_line")


def is_drastic(kind):
    return any(kind.startswith(d) for d in DRASTIC_KINDS)


GT = {}
for case in ("case30", "case39"):
    d = json.load(open(os.path.join(ROOT, f"ladder_{case}.json")))
    kind_of = {m["text"]: m["kind"] for m in d["menu"]}
    for it in d["items"]:
        scens = [("anchor", it["anchor"]), ("far", it["far_anchor"])] + \
                [(f"rung{r['delta']}", r) for r in it["rungs"]]
        for tag, sc in scens:
            if sc is None:
                continue
            kinds = [kind_of[f] for f in sc["fixers"]]
            sub = None
            if sc["label"] == "TRICKY":
                sub = "drastic" if all(is_drastic(k) for k in kinds) else "benign"
            GT[(case, str(it["item_id"]), tag)] = dict(
                case=case, item_id=str(it["item_id"]), tag=tag,
                old_label=sc["label"], old_sub=sub, n_fixers_old=len(sc["fixers"]))

assert len(GT) == 263, len(GT)

# overlay from p1_results.json (fixable EASY/TRICKY rows only)
TAGMAP = {"anchor": "anchor", "far_anchor": "far"}
qrows = json.load(open(QLIMS_RESULTS))
n_overlaid = 0
for r in qrows:
    tag = TAGMAP[r["tag"]]
    key = (r["case"], str(r["item_id"]), tag)
    assert key in GT, key
    g = GT[key]
    assert g["old_label"] == r["old_label"], (key, g["old_label"], r["old_label"])
    assert g["n_fixers_old"] == r["old_n_fixers"], key
    nfx = r["new_n_fixers_surviving"]
    new_label = "INFEASIBLE" if nfx == 0 else ("TRICKY" if nfx == 1 else "EASY")
    g["new_n_fixers_qlims"] = nfx
    g["new_label"] = new_label
    # sub (drastic/benign) recompute under new labels: old TRICKY items have exactly ONE
    # certifying fixer by definition, so if it survives (new_label stays TRICKY) it is the SAME
    # action as before -- sub is unchanged. Verified empirically: 0 rows transition
    # EASY->TRICKY (only EASY->EASY, EASY->INFEASIBLE, TRICKY->TRICKY, TRICKY->INFEASIBLE occur),
    # so no new TRICKY row is ever newly created from a former EASY item requiring a fresh
    # drastic/benign classification. Hence new_sub = old_sub whenever new_label == "TRICKY".
    g["new_sub"] = g["old_sub"] if new_label == "TRICKY" else None
    g["base_diverges"] = (not r["base_state_converges_qlims"])
    g["flipped"] = (new_label != g["old_label"])
    g["re_tested_under_qlims"] = True
    n_overlaid += 1
assert n_overlaid == 75, n_overlaid

# rungs (and any row not touched above) keep old_label -> new_label unchanged; never re-tested,
# justified above (q_lims is a strictly additional constraint; cannot un-fail an already-failed
# single-action clearance). All INFEASIBLE by construction for rungs specifically.
for g in GT.values():
    if "new_label" not in g:
        g["new_label"] = g["old_label"]
        g["new_sub"] = g["old_sub"]  # unchanged (== None for all rungs; INFEASIBLE has no sub)
        g["new_n_fixers_qlims"] = None
        g["base_diverges"] = False
        g["flipped"] = False
        g["re_tested_under_qlims"] = False

# sanity: no EASY->TRICKY transitions occurred (would need a fresh sub classification we can't
# derive from old_sub alone)
bad = [g for g in GT.values() if g["old_label"] == "EASY" and g["new_label"] == "TRICKY"]
assert not bad, bad

rows = sorted(GT.values(), key=lambda g: (g["case"], int(g["item_id"]), g["tag"]))

# ---- composition, WITH the base-diverging row (default: base_diverges counted as INFEASIBLE)
old_ct = collections.Counter(g["old_label"] for g in rows)
new_ct_with = collections.Counter(g["new_label"] for g in rows)
# ---- composition, WITHOUT the base-diverging row (excluded entirely)
rows_excl = [g for g in rows if not g["base_diverges"]]
new_ct_without = collections.Counter(g["new_label"] for g in rows_excl)
old_ct_without = collections.Counter(g["old_label"] for g in rows_excl)

flips = [g for g in rows if g["flipped"]]
flip_by_case = collections.Counter(g["case"] for g in flips)
flip_transition = collections.Counter((g["old_label"], g["new_label"]) for g in flips)

out = dict(
    meta=dict(
        n_rows=len(rows), n_fixable_retested=75, n_rungs_or_untested=len(rows) - 75,
        source_flip_results="p1_results.json (re-verified byte-identical to an independent "
                             "fresh re-run in this session; reconstruction pre-check 75/75 "
                             "0 mismatches)",
        rule="new_n_fixers_surviving==0 -> INFEASIBLE, ==1 -> TRICKY, >=2 -> EASY; rows not in "
             "the 75 fixable set (i.e. all rungs, which are INFEASIBLE by construction) are "
             "assumed to stay INFEASIBLE under q_lims and are not re-solved -- enforcing "
             "reactive limits is a strictly additional constraint on the AC solve and cannot "
             "create a clearing action that did not already exist without it.",
        base_diverges_handling="case39 item 0 anchor: the unmodified scenario net fails to "
                                "converge under enforce_q_lims=True even before any action is "
                                "applied. Folded into new_label=INFEASIBLE by default (consistent "
                                "with its own new_n_fixers_surviving=0), flagged base_diverges=True, "
                                "and BOTH with/without variants of every composition and downstream "
                                "number are reported.",
    ),
    old_composition=dict(old_ct),
    new_composition_with_base_diverge_as_infeasible=dict(new_ct_with),
    new_composition_excluding_base_diverge_row=dict(new_ct_without),
    old_composition_excluding_base_diverge_row=dict(old_ct_without),
    n_flips_total=len(flips),
    n_flips_by_case=dict(flip_by_case),
    flip_transitions=[dict(old=k[0], new=k[1], n=v) for k, v in flip_transition.items()],
    rows=rows,
)
json.dump(out, open(OUT, "w"), indent=1)

print("OLD composition:", dict(old_ct), "sum=", sum(old_ct.values()))
print("NEW composition (WITH base-diverge row as INFEASIBLE):", dict(new_ct_with),
      "sum=", sum(new_ct_with.values()))
print("NEW composition (EXCLUDING base-diverge row):", dict(new_ct_without),
      "sum=", sum(new_ct_without.values()))
print("total flips:", len(flips), "by case:", dict(flip_by_case))
print("flip transitions:", dict(flip_transition))
print(f"wrote {OUT}")
