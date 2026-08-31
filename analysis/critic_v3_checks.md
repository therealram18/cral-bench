# Critic-v3 verification + computation pass

Pack: `neurips26_powergrid_pack_2026-08-27/powergrid/`. Draft (read-only):
`papers/powergrid/main.tex`. No API calls; all computation local (pandapower 3.5.4 venv,
numpy/scipy). Every number below was independently recomputed from canonical on-disk
JSON/JSONL with a fresh script, not copy-pasted from prior markdown -- and cross-checked
against `analysis/v2_sdt_results.json`, `analysis/luna_sdt_results.json`,
`analysis/qlims_rescore_results.json`, and `framing_increment.py`'s own validation constants
before being trusted. Full machine-readable detail: `analysis/critic_v3_checks.json`.

---

## 1. Composition accounting (N3)

**Numbers** (from `analysis/qlims_labels.json` rows, recomputed directly):

| | EASY | TRICKY | INFEASIBLE | total |
|---|---|---|---|---|
| OLD | 17 | 58 | 188 | 263 |
| NEW, folded/relabeled (base-diverge -> INFEASIBLE) | 15 | 42 | 206 | 263 |
| NEW, **true dropped** (base-diverge row excluded) | 15 | 42 | 205 | **262** |

Flips: **18 including** the diverging row (16 TRICKY->INFEASIBLE + 2 EASY->INFEASIBLE), **17
if the diverging row is excluded as a true drop** (15 TRICKY->INFEASIBLE + 2 EASY->INFEASIBLE).
case39 fixable = 36, case30 fixable = 39, total fixable = 75 (all confirmed).

Ratios: 17/263 = 6.46%, **17/262 = 6.49%** (defensible "% of benchmark" under true-dropped
accounting), 17/75 = 22.67% (% of fixables), **17/36 = 47.22%** (fraction of case39 fixables).
Always-escalate raw under true-dropped accounting: 205/262 = **0.7824**.

Δc under true-dropped accounting (M4+loglinear, from `qlims_rescore_results.json`
`new_excl_bd`, independently re-pulled): flash **−0.703**, pro **−1.141**, luna **−1.199** —
vs. the paper's printed −0.714/−1.145/−1.197 (the **folded/relabeled** `new_with_bd` variant).

**VERDICT — confirmed inconsistency, not a conclusion-changer.** main.tex lines 345–349 say the
diverging item "is dropped, not relabeled" but then prints "new composition 15/42/206" (sums to
**263** — the item is still counted, just moved into INFEASIBLE) and Δc values that match the
**folded/relabeled** computation, not a true drop. A genuine drop gives 262/15-42-205/17 flips,
which differs from the printed numbers by ≤0.02 in every Δc and by 1 in the flip count — no sign
flips, no changed conclusion. Fix: reword "dropped, not relabeled" → "folded into infeasible
(relabeled), not dropped," keeping the current (already-computed) 18/263/15-42-206 numbers. That
is the smaller edit and matches what was actually run.

## 2. Six EASY deltas, cluster-bootstrapped (N1)

Recomputed from `v2_ladder_{model}_{NO_ESCAPE,ESCALATE,NONE_INDEX}.jsonl`, EASY-label rows only
(17 items), same seed/B/cluster machinery as `framing_increment.py`:

| model | N rate | I rate | E rate | Δ(I−N) [95% CI] | Δ(E−I) [95% CI] |
|---|---|---|---|---|---|
| flash | 0.118 (2/17) | 0.353 (6/17) | 0.353 (6/17) | **+0.235** [0.056, 0.455] * | +0.000 [−0.167, 0.167] |
| pro | 0.000 (0/17) | 0.059 (1/17) | 0.000 (0/17) | +0.059 [0.000, 0.200] | −0.059 [−0.200, 0.000] |
| luna | 0.000 (0/17) | 0.000 (0/17) | 0.118 (2/17) | +0.000 [0.000, 0.000] | +0.118 [0.000, 0.294] |

(* excludes zero.)

**VERDICT — confirmed, 5 of 6 straddle zero**, matching the "expect most" prior. The single
exception is flash's bare-affordance (NONE_INDEX − NO_ESCAPE) EASY-rate delta. Low power (n=17)
and floor effects (0/17 in most cells) explain most of the null results — these are absence-of-
evidence, not evidence-of-absence.

## 3. Share CIs (N8)

Share = Δc(NONE_INDEX−NO_ESCAPE) / Δc(ESCALATE−NO_ESCAPE), M4+loglinear, bootstrapped on the
same paired resample used for the increment (denominator never crosses zero in 20,000 draws for
any model):

| model | Δc(E−N) | Δc(I−N) | share | 95% CI |
|---|---|---|---|---|
| flash | −0.589 | −0.332 | **56.4%** | [29.8%, 82.5%] |
| pro | −1.163 | −0.774 | **66.6%** | [50.8%, 80.1%] |
| luna | −1.400 | −0.617 | **44.1%** | [21.7%, 68.1%] |

**VERDICT — point estimates exactly reproduce "44–67%," but the ordering is NOT statistically
stable.** All three CIs overlap heavily (luna's upper 68.1% sits inside both flash's and pro's
ranges; flash's CI alone spans nearly the whole luna-to-pro range). Report the 44–67% range as
a qualitative fact ("the bare in-schema affordance accounts for roughly half, not all, of the
named-ESCALATE effect") — do not present pro > flash > luna as a reliable per-model ranking.

## 4. Affordance-cost ratio (§4 item)

Computed exactly from canonical JSONLs, per model, both accountings:

| model | (a) raw: false/gain | (b) M4: false/gain | 
|---|---|---|
| flash | 20/4 = **5.00** | 9/15 = **0.60** |
| pro | 28/87 = **0.322** | 9/106 = **0.085** |
| luna | 14/92 = 0.152 | 5/101 = 0.050 |

Accounting (a) reproduces the critic's cited 28/87 and 20/4 **to the exact integer** from
`v2_ladder_{model}_{ESCALATE,NO_ESCAPE}.jsonl`. Accounting (b) additionally credits each
model's increased escalation rate on drastic-TRICKY (E−N) as a correct-deferral gain (flash
+11, pro +19, luna +9) and restricts the "false" denominator to EASY+benign-TRICKY (n=34).

**VERDICT — both accountings verified exactly; recommend (b) M4 for print.** The two tell
opposite stories for flash (raw: 5 false per correct gained, looks terrible; M4: 0.6 false per
correct, looks tolerable) purely because raw treats escalating on genuinely drastic TRICKY
items as neutral rather than correct. M4 is already the paper's primary mapping everywhere
else — using raw accounting for this one number while using M4 everywhere else would be an
inconsistent standard. Report M4's ratios (flash 0.60, pro 0.085, luna 0.050) as primary, raw
as a robustness footnote.

## 5. M4 defense facts (N9)

**(a) M2 vs M4 magnitude** (loglinear; both from `v2_sdt_results.json` / `qlims_rescore_results.json`):

| model | M2 Δc | M4 Δc | M4 larger in magnitude? |
|---|---|---|---|
| flash | −0.548 | −0.589 | **yes** (reversed vs. critic's claim) |
| pro | −1.345 | −1.163 | no — M2 larger, matches critic's quoted "−1.345 vs −1.163" exactly |
| luna | −1.636 | −1.400 | no — M2 larger |

**VERDICT — partially confirmed.** The critic's specific numbers (−1.345/−1.163) are pro's
exactly, and hold for pro and luna (M2 > M4 in magnitude). They do **not** generalize to flash,
where M4 is larger. Do not state "M2 is always larger than M4" — only true for 2 of 3 models.

**(b) Certified-action pick rates**, quoted verbatim from `signal_noise_sensitivity.log`
section [4c], lines 268–276/412–420: *"In the NO_ESCAPE arm, among items where gemini-3.7-flash
chose to act, it picked a certified action on 0.667 of EASY and 0.667 of TRICKY-benign — but
only 0.100 of TRICKY-drastic (thinking arm: 0.643/0.714/0.071)."* Across all Gemini rows in the
log, EASY ranges 0.600–0.667, TRICKY-drastic ranges 0.000–0.100 — **verbatim match** to the
claimed "~0–10% vs 0.60–0.67."

## 6. luna correction floor (N2)

Confirmed directly from `v2_ladder_gpt-5.6-luna_NO_ESCAPE.jsonl`: EASY **0/17**, TRICKY **0/58**
(so drastic 0/41 and benign 0/17 subsets are also 0) → FA=0 under **every** mapping's noise pool
(M1 0/17, M2 0/75, M3 0/17, M4 0/34, M5 0/34).

Log-linear constant: p_N = (0+0.5)/(n+1); for M4 (n=34), p_N=0.01429, z(p_N)=**−2.1893**.
Reproduces exactly: c(NO_ESCAPE)=+1.9171, c(ESCALATE)=+0.5168, **Δc = −1.4003** ≈ paper's −1.400.

**Correction-floor bound:** one hypothetical false alarm among the 34 noise items (0→1/34)
would move z(F) from −2.1893 to −1.7185, shifting c(NO_ESCAPE) by **0.235 SD** — about a sixth
of the reported 1.40 SD Δc. Honest phrasing: *"luna's criterion shift would stay outside ±1 SD
of its current value under any single plausible one-item change to its false-alarm count."*

**Correction-pinned** ≡ a (mapping, arm) SDT cell whose pooled hit or false-alarm count sits at
a hard floor/ceiling (reuses `v2_sdt_analysis.py`'s own `floor_ceiling` flag). Counts:

- **(a) E-vs-N grid: 10/10 cells pinned** (all 5 mappings × both corrections — NO_ESCAPE is
  always pinned since it has 0 escalations on both EASY and TRICKY, regardless of pooling).
- **(b) I-vs-N grid: 10/10 cells pinned**, same reason.
- **(c) E-vs-I increment grid: 4/10 cells pinned — only M1 and M3** (both corrections). luna's
  NONE_INDEX EASY=0/17 pins exactly M1 and M3, the only two mappings whose noise pool is EASY
  alone; M2/M4/M5 include TRICKY in that pool, and NONE_INDEX TRICKY=4/58 (nonzero), so those
  three are **not** pinned there.

**VERDICT — all confirmed with exact numbers.** The 0-FA floor is real and quantified (0.24 SD
per single-item perturbation under M4); its scope is precisely bounded (10/10, 10/10, 4/10
across the three grids), not "everything is pinned."

## 7. Sweep universe (N5)

Universe: **18 flagged case39 scenarios** (the q-lims TRICKY/EASY→INFEASIBLE flip set,
reconstructed from `analysis/qlims_flip_results.json`) × **50 menu actions** = **900**
scenario-action pairs, solved under `enforce_q_lims=True` with `certify_v2.py`'s own solver
settings (`numba=False, max_iteration=30`). **133/900 fail to converge.** 11 alternative
solver settings tried per failure (init∈{dc,flat}, max_iteration=500, tolerance_mva=0.001, and
combinations): **25/133 converge under at least one alternative, 0/133 both converge and clear
all violations.** (Source: `analysis/critic_v2_checks.json` `item2_convergence_rescue_sweep`,
restated verbatim — recomputing would re-run pandapower AC solves already logged by the prior
critic pass.)

**Round-1's "102" reconciliation:** `critic_v2_checks.md` already tested this and **found 102
does not reproduce under any scope, including the original (non-q-lims) settings** — under
`enforce_q_lims=False` only **1** of the 900 pairs fails, not 102. Nor does it match the
certified-fixer-only scope (24 pairs) or the base-state-excluded scope (88/850). **One-sentence
reconciliation: the hypothesis that round-1's 102 reflects the original non-q-lims settings is
false (that scope gives 1, not 102), so 102 remains an uncertified number from a missing prior
artifact and 133 (q-lims settings) is the only reproducible figure — do not attribute the gap to
a settings difference.**

## 8. Draft checks (read-only, `papers/powergrid/main.tex` + compiled `main.pdf`)

**(a) Footer** (pdftotext on `main.pdf` page 1): *"Submitted to 40th Conference on Neural
Information Processing Systems (NeurIPS 2026). Do not distribute."* — confirmed.

**(b) Limitations heading:** **No** `\section`/`\subsection` titled "Limitations" exists.
There are two inline-bold paragraph leads: line 378 `\textbf{Limitations.}` (main results,
`\label{sec:limitations}`) and line 562 `\textbf{Known limitations.}` (inside the checklist).
Content exists; it is not a titled section — a stylistic choice, not necessarily an error.

**(c) Table 1 caption** (`\label{tab:rates}`, line 269, the paper's first table): *"Escalation
rate by label/arm, parsed-only (\textsc{n}/\textsc{e}: harness v2; \textsc{i}=\textsc{none-
index}: harness v2b). Escalating is wrong on \textsc{easy}/\textsc{tricky}, right on
infeasible. gemini-3.5-flash omitted (gated; see text)."* Its EASY row (pro 0/0.059/0, flash
0.118/0.353/0.353, luna 0/0/0.118) exactly reproduces the independently-recomputed rates in
item 2 above.

**(d) "released" vs. no-repo:** Abstract (line ~49): *"...substrate, scorer, and labels
released"* (past tense). Checklist (lines 464–486): *"At camera-ready we will release...No
repository accompanies this anonymized submission."* **Confirmed contradiction** — recommend
"to be released" / "released at camera-ready" in the abstract.

**(e) EASY-81 sentence arm labels** (lines 337–339): no explicit N/E labels are printed, but the
implicit order (first number = ESCALATE, second = NO_ESCAPE) is verified correct against
`qlims_sensitivity.md`'s ALL-81 table for all three models — no mislabeling. Note: this
served-load-rule EASY-81 result is distinct from two *other* EASY-81 checks elsewhere (line 154
served-load re-audit "79/81 strict + 2 relaxed," and `qlims_sensitivity.md`'s q-lims
re-certification "75/81 = 92.6%," which is not quoted in main.tex) — three different stress
tests of the same 81 items, not an inconsistency, but worth confirming the scope choice is
intentional.

**(f) Fukui wording**, quoted verbatim (lines 81–83): *"SDT analysis of LLMs exists with
temperature \citep{sdtllms2026} or across generations at fixed orchestration
\citep{fukui2026cliff};"* — unchanged, editor should leave as-is.
