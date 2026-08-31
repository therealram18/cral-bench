# Critic-v4 verification + computation pass

Pack: `neurips26_powergrid_pack_2026-08-27/powergrid/`. Pass #4 in the adversarial-review chain
(critic_v2, critic_v3 already on disk). No API calls; all computation is local pandapower 3.5.4 AC
power-flow (CPU, `numba=False`) or reads of canonical on-disk JSON/JSONL, run fresh with new code
for this pass. Full machine-readable detail: `analysis/critic_v4_checks.json`.

---

## Item 1 — Convergence sweep under the shipped certifier

**Which "18 flagged case39 scenarios."** Reconstructed from `analysis/qlims_flip_results.json`:
every row with `case=="case39"` and `all_fixers_lost==True` gives exactly the 18 `(item_id, tag)`
pairs listed in the task (16 old-label TRICKY `anchor` entries + 2 old-label EASY `far_anchor`
entries, item_id 3 and 17). `(item_id=0, tag=anchor)` is confirmed as one of the 16 TRICKY flips
whose *base state* also fails to converge under q-lims (`base_state_converges_qlims=False`) — not
an 18th item on top. Menu length verified as 50 from `ladder_case39.json`'s top-level `"menu"`
field, and `menu[i]` was verified to order-match `per_action[i]` for all 18 scenarios before any
solve.

**A different, non-matching candidate set exists and must not be conflated.** Every anchor/
far_anchor/rung entry in `ladder_case39.json` carries `menu_converged` (count out of 50, from the
original `enforce_q_lims=False` build). Entries with `menu_converged<50`: **19 entries, spanning
16 unique item_ids** (labels: 18 already-INFEASIBLE, 1 TRICKY), summing to **103** failing
(scenario,action) pairs in the original build. This set includes `item_id=19`, which is **never**
in the q-lims-flip 18-set, and is dominated by rung entries whose old label was already
INFEASIBLE — it is a different scope from the paper's "18 flagged case39 scenarios," which the
paper's own text (main.tex, Oracle-sensitivity paragraph) defines via "17 of 36 case39 fixable
items flip ... [18 =] the 18 flagged case39 scenarios." **103 ≠ 102** either, so this scope does
not produce the external critic's number.

**(a) Shipped settings (`enforce_q_lims=False`, `numba=False`, `max_iteration=30`, no init/
tolerance override — literally `certify_v2.py`'s `solve()`), 18×50 = 900 pairs:**

**1 / 900 fail to converge.** Exactly matches `critic_v2_checks.md`'s prior finding of "~1" —
confirmed a third time with fresh code.

**(b) Rescue of that 1 failure** under the same 11 alternative solver-setting combinations
(`enforce_q_lims` still `False`): **0/1 converge under any alternative, 0/1 clear.**

**(c) Reconciliation of "102."**

| scope | value |
|---|---|
| (i) shipped settings, 900 pairs | **1** |
| (ii) q-lims=True, 900 pairs | **133** (matches the paper) |
| (iii) menu_converged<50 scope (original-build failing actions) | **103** (not 102; also the wrong scope — see above) |

**102 does not reproduce under any scope constructible from anything on disk** — confirms both
prior passes' conclusion. The closest miss is scope (iii) at 103, off by exactly 1, but that scope
is definitionally not the "18 flagged case39 scenarios" the paper's sentence describes, so this is
a coincidence worth noting, not a candidate explanation.

**(d) Re-run of the q-lims=True sweep, same 18×50 = 900 pairs, shipped `numba`/`max_iteration`:**

**133 / 900 fail to converge** — matches the paper's printed figure and both prior critic passes
exactly.

**Rescue of the 133 failures**, same 11 alternative settings (`enforce_q_lims` stays `True`):

**19 / 133 converge under ≥1 alternative, 0 / 133 clear all violations.**

**CORRECTED — this disagrees with the paper's printed "25 of the 133 converge" (and with
critic_v2/critic_v3's stored 25/133).** Root-caused, not just re-measured: `critic_v2_checks.json`
`item2_convergence_rescue_sweep.rescue_detail` was pulled and every one of its 25 "rescued_any"
pairs was checked against exactly which settings-dict rescued it. **All 25 converge only under a
settings-dict that omits `max_iteration` entirely** (e.g. `{'init':'dc'}`, `{'tolerance_mva':
0.001}`) — under pandapower 3.5.4, an omitted `max_iteration` falls back to the library default
`max_iteration='auto'`, **not** the baseline's explicit `30`. The task's literal spec for the 11
alternatives is a factorial of `init ∈ {default, dc, flat}` × `max_iteration ∈ {30, 500}` (always
one of these two, explicitly passed — no "default" option on this axis) × `tolerance_mva ∈
{default, 1e-3}`. Under that literal spec (implemented here: every one of the 11 alternatives
passes `max_iteration` explicitly as 30 or 500), **none** of critic_v2's 25 auto-max_iteration
rescues reproduce — not one of them converges under any combo that explicitly sets
`max_iteration=500` together with other overrides. This pass's 19 successes come from a
genuinely different, literal-spec-compliant subset. **0/133 clear either way**, so the paper's
substantive claim ("non-convergence hides no fixes") is unaffected — only the "25" count needs a
fix (either hold `max_iteration` explicit in every alternative and print 19, or state precisely
which settings were left at library defaults).

---

## Item 2 — Cost curve + CI (flash / pro / luna)

**(a) Components**, `count_escalated(arm, pool)` on parsed-only rows, pools built from the GT
(label, sub) join (noise n=34, drastic n=41, infeasible n=188 — all confirmed):

| model | FA_added | drastic_added | infeasible_gain | ratio(0) raw | ratio(1) M4 | w* |
|---|---|---|---|---|---|---|
| gemini-3.7-flash | **9** | **11** | **4** | 20/4 = **5.000** | 9/15 = **0.600** | **0.7273** |
| gemini-3.1-pro-preview | 9 | 19 | 87 | 28/87 = **0.3218** | 9/106 = **0.0849** | −1.553 (∉[0,1]) |
| gpt-5.6-luna | 5 | 9 | 92 | 14/92 = **0.1522** | 5/101 = **0.0495** | −4.333 (∉[0,1]) |

flash's (FA_added, drastic_added, infeasible_gain) = **(9, 11, 4)** — confirmed exactly. ratio(0)
and ratio(1) confirmed at both endpoints for flash (5.00, 0.60) and w*≈0.73 confirmed. For pro and
luna, w* is negative (outside [0,1]) — **the raw/M4 curve never crosses 1 for either model**; both
start (w=0) and stay (w=1) below 1, unlike flash which starts above 1 and crosses down through it.

**(b) Cluster-bootstrap 95% CI on the M4 ratio**, one shared `BOOT_IDX` (seed 20260827, B=20,000,
40 clusters) across all three models, resampling cluster totals and recomputing
FA_added/(infeasible_gain+drastic_added) each draw:

| model | point M4 ratio | 95% CI | unusable draws |
|---|---|---|---|
| gemini-3.7-flash | 0.600 | **[0.208, 1.444]** | 0 / 20,000 |
| gemini-3.1-pro-preview | 0.0849 | **[0.0317, 0.1605]** | 0 / 20,000 |
| gpt-5.6-luna | 0.0495 | **[0.0103, 0.0988]** | 0 / 20,000 |

0 unusable draws for every model (denominator never hit zero). Note flash's CI is wide enough to
cross 1.0 at the upper end (1.444) — the "cost per correct escalation" point estimate (0.60 false
per correct) is not tightly pinned for flash at this sample size, unlike pro/luna whose CIs stay
comfortably below 1.

**(c) Ordering.** flash > pro > luna holds in **both** accountings, confirmed:
raw (w=0): 5.000 / 0.3218 / 0.1522. M4 (w=1): 0.600 / 0.0849 / 0.0495. Matches the task's expected
ballpark (~5.00/0.322/0.152 and ~0.60/0.085/0.050) exactly.

---

## Item 3 — Denominators after the drop

Dropped row confirmed: `qlims_labels.json` rows, `base_diverges==True` → exactly one row,
`(case39, item_id=0, tag=anchor, old_label=TRICKY)` — matches expected.

Fixable pools recomputed fresh from `qlims_labels.json` rows (`old_label` in EASY/TRICKY): case30
39, case39 36, total **75** — confirmed. `n_flips_total=18` (folded accounting) confirmed;
true-drop flip count = 18 − 1 = **17**.

| accounting | numerator | overall denom | overall % | case39 denom | case39 % |
|---|---|---|---|---|---|
| **true-drop** (item excluded from both num. and denom.) | 17 | **74** | **22.97%** | **35** | **48.57%** |
| critic_v3's printed accounting | 17 | 75 | 22.67% | 36 | 47.22% |

True-drop gives **17/74 ≈ 23.0%** and **17/35 ≈ 48.6%**, matching the task's expected ballpark.
**Verdict: true-drop (both numerator and denominator exclude the dropped item) is the
mathematically consistent accounting** for an item that is "dropped, not relabeled" — critic_v3's
75/36 keep the item in the denominator while dropping it only from the numerator, an inconsistent
halfway accounting that should not be used under that literal wording.

**New finding, current draft.** The paper's current `main.tex` (Oracle-sensitivity paragraph) has
*already* moved toward true-drop for some figures but not others, **within the same sentence**:
*"17 of 36 case39 fixable items flip (47%) --- 17/75 overall (22.7%), 17/262 of the benchmark
(6.5%); new composition 15/42/205 of 262."* The `17/262` figure and the `15/42/205` composition
(15+42+205=262) **are** true-drop (matches `qlims_sensitivity.md`'s "row excluded" column exactly,
and the paper's cited Δc range −0.589→−0.703 / −1.163→−1.141 / −1.400→−1.199 for
flash/pro/luna also matches the "row excluded" Δc column, not the "base-diverge→INFEASIBLE"
folded column). But the **same sentence's** "17 of 36" and "17/75" still use the pre-drop
denominators (36, 75), not 35/74. This is a sharper, more specific version of critic_v3's finding:
the paper is not just choosing one inconsistent accounting throughout — it mixes true-drop
(benchmark-level: 262, composition, Δc) with the old denominators (fixable-pool-level: 75, 36) in
one paragraph. Recommend replacing "17 of 36 ... 17/75" with "17 of 35 (48.6%) ... 17/74 (23.0%)"
for full internal consistency.

---

## Item 4 — Figure sums (I−N + E−I = E−N)

From `analysis/framing_increment.json`'s `primary_M4_loglinear`, full float precision:

| model | I−N (full) | increment (full) | sum | E−N (full) | identity holds (1e-9)? |
|---|---|---|---|---|---|
| gemini-3.7-flash | −0.332229116 | −0.256913504 | −0.589142620 | −0.589142620 | **yes** |
| gemini-3.1-pro-preview | −0.774407486 | −0.388277358 | −1.162684844 | −1.162684844 | **yes** |
| gpt-5.6-luna | −0.617323307 | −0.783018726 | −1.400342033 | −1.400342033 | **yes** |

The identity holds exactly (to float tolerance) for all three models — confirmed.

**Rounding artifact, confirmed as display-only, not computational.** Rounding each component to
3dp *before* summing:

| model | round(I−N,3) + round(inc,3) | vs. round(full E−N, 3) | match? |
|---|---|---|---|
| gemini-3.7-flash | −0.332 + −0.257 = **−0.589** | −0.589 | matches |
| gemini-3.1-pro-preview | −0.774 + −0.388 = **−1.162** | **−1.163** | **off by 0.001** |
| gpt-5.6-luna | −0.617 + −0.783 = **−1.400** | −1.400 | matches |

For pro: `delta_c_none_index = -0.7744074859616883` rounds individually to **−0.774**;
`increment = -0.3882773584904493` rounds individually to **−0.388**; their sum of rounded values
is −1.162. But the **true** (full-precision) sum is `-1.1626848444521376`, which rounds to
**−1.163**. This is a textbook round-then-sum vs. sum-then-round artifact (the true sum's third
decimal digit sits at the 0.1626848... boundary, close enough to .5 that rounding the two addends
first shaves off the carry) — **confirmed not a computational error**.

---

## Item 5 — Table 2 edit counts (N=NO_ESCAPE, I=NONE_INDEX, E=ESCALATE)

Quoted verbatim from source (re-read directly, byte-checked against the file a second time):

- **`harness_v2.py::choice_space()`**: NO_ESCAPE adds **no** extra menu entry. ESCALATE adds
  `"ESCALATE — no single action above resolves all violations; hand this to a human operator or a
  multi-action planner."`
- **`harness_v2.py::render()`** tail: NO_ESCAPE = `"Choose the ONE option that clears ALL listed
  violations."` + `' If you judge that no single action can, reply {"choice": "NONE", "reason":
  "..."}.'`. ESCALATE = `"Choose the ONE action that clears ALL listed violations. If no single
  action can, choose ESCALATE."`
- **`harness_v2b.py::choice_space()`**: NONE_INDEX adds `"NONE — no single action above resolves
  all violations."`
- **`harness_v2b.py::render()`** tail (NONE_INDEX): `"Choose the ONE action that clears ALL listed
  violations. If no single action can, choose NONE."`

**I − N: 3 edits, confirmed** (code-computed diff, not eyeballed):
1. Menu entry added: `[n] NONE — no single action above resolves all violations.` — present in I,
   absent from N entirely.
2. Tail sentence 1, word swap: N `"...option that clears..."` → I `"...action that clears..."` —
   confirmed a real, distinct edit (not folded into edit 3; the two sentences are independently
   diffable).
3. Tail sentence 2, full replace: N's hedge `'If you judge that no single action can, reply
   {"choice": "NONE", "reason": "..."}.'` → I's terser `"If no single action can, choose NONE."`

**E − I: 2 edits, confirmed:**
1. Menu entry text: I `"NONE — no single action above resolves all violations."` → E `"ESCALATE —
   no single action above resolves all violations; hand this to a human operator or a multi-action
   planner."` (word swap NONE→ESCALATE + appended clause).
2. Tail final word: I `"...choose NONE."` → E `"...choose ESCALATE."`. Tail sentence 1 (`"Choose
   the ONE action that clears ALL listed violations."`) is **byte-identical** between I and E —
   confirmed, no further edit there.

**Both counts match the task's stated expectation exactly (3 for I−N, 2 for E−I).**

---

## Item 6 — A/A reference numbers (gemini-3.7-flash, ESCALATE, harness_v2)

From `v2_ladder_gemini-3.7-flash_ESCALATE.jsonl`, parsed-only (0 unparsed in every label cell):

| label | k/n | rate |
|---|---|---|
| EASY | 6/17 | 0.353 |
| TRICKY | 49/58 | 0.845 |
| INFEASIBLE | 186/188 | 0.989 |

M4+log-linear criterion, computed fresh (signal = INFEASIBLE + TRICKY.drastic, noise = EASY +
TRICKY.benign, `(k+0.5)/(n+1)` correction): **c(ESCALATE) = −1.0018**, d′ = 1.5706.
Cross-check against `analysis/v2_sdt_results.json`'s `M4|gemini-3.7-flash|ESCALATE|loglinear` entry
(c=−1.0018426952687214, d=1.5706171416391008): **exact match** (both to <1e-6).

---

## Summary table

| item | verdict |
|---|---|
| 1a shipped-settings 900-pair sweep | CONFIRMED — 1/900 fail, matches critic_v2's prior "~1" exactly (3rd independent reconfirmation) |
| 1b shipped-settings rescue | CONFIRMED — 0/1 converge, 0/1 clear |
| 1c "102" reconciliation | CONFIRMED UNREPRODUCIBLE — no scope on disk gives 102 (closest: menu_converged<50 scope = 103, and that's the wrong scope anyway) |
| 1d q-lims=True 900-pair sweep | CONFIRMED — 133/900 fail, matches paper and both prior passes exactly |
| 1d rescue | **CORRECTED — 19/133 converge (not 25/133)**; 0/133 clear either way (substantive claim unaffected); root cause identified: paper's/critic_v2's 25 all rescue via combos that omit `max_iteration` (falls back to pandapower's `auto`), not the task's literal `{30,500}`-explicit factorial |
| 2a flash components | CONFIRMED — (FA_added, drastic_added, infeasible_gain) = (9, 11, 4) exactly; ratio(0)=5.00, ratio(1)=0.60, w*≈0.727 all confirmed |
| 2a pro/luna | CONFIRMED — raw 0.322/0.152, M4 0.085/0.050, both w* outside [0,1] (curve never crosses 1) |
| 2b bootstrap CIs | NEW — flash [0.208,1.444], pro [0.032,0.161], luna [0.010,0.099]; 0/20,000 unusable draws for all three |
| 2c ordering | CONFIRMED — flash>pro>luna holds in both raw and M4 accountings |
| 3 true-drop denominators | CONFIRMED — 17/74=22.97%, 17/35=48.57%, matches expected ~23.0%/~48.6%; critic_v3's 17/75, 17/36 confirmed as the inconsistent halfway accounting |
| 3 (new) | NEW FINDING — current main.tex mixes true-drop (262, composition, Δc) with pre-drop (36, 75) denominators within the same sentence |
| 4 identity | CONFIRMED — holds exactly (1e-9) for all 3 models |
| 4 rounding artifact | CONFIRMED — pro's 0.001 gap is a round-then-sum vs. sum-then-round display artifact, not a computational error |
| 5 edit counts | CONFIRMED — 3 edits I−N, 2 edits E−I, exact text quotes reproduced byte-for-byte from source |
| 6 A/A reference | CONFIRMED — EASY 6/17, TRICKY 49/58, INFEASIBLE 186/188; c(ESCALATE)=−1.0018, d′=1.5706, exact match to `v2_sdt_results.json` |
