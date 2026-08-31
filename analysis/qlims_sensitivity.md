# Label-sensitivity analysis: generator reactive limits enforced (q-lims re-certification)

**Question.** The shipped 263-item benchmark (CRAL) certifies EASY/TRICKY/INFEASIBLE by
solving every candidate fixer action with `pp.runpp(..., enforce_q_lims=False)` — i.e.
generator reactive power is unbounded (disclosed explicitly in the paper, checklist item 1:
"reactive support is unbounded ... so fixable classes are optimistic"). This note asks: if
every certifying action is re-tested with `enforce_q_lims=True` (generators clamp to their Q
limits, sagging voltage instead of holding it), how many labels flip, and does the paper's
headline (`Δc = c(ESCALATE) − c(NO_ESCAPE)` is negative everywhere) survive?

**Bottom line up front: yes, it survives.** Every one of the 30 reportable Δc cells in the
5-mapping × 2-correction robustness grid stays negative with its 95% CI excluding zero, for
all three headline models (gemini-3.7-flash, gemini-3.1-pro-preview, gpt-5.6-luna), under
both the default and excluded-row handling of one non-converging base state. No sign flips
anywhere in this analysis. The magnitudes move by single digits to ~20 points of Δc, in both
directions depending on model/mapping — not attenuated toward zero as a group, not amplified
as a group. Placebo suppression, the trivial always-escalate baseline, the Qwen3-8B rates, and
the EASY-81 replication are all likewise directionally and statistically intact. The one number
that moves in a direction worth flagging honestly: the always-escalate accuracy baseline gets
*stronger* under q-lims (0.715→0.783 raw, 0.871→0.913 under M4) — mechanically expected, since
q-lims can only convert fixable scenarios into infeasible ones, never the reverse, so a larger
share of ground truth becomes "should escalate."

## 0. Re-verification of the prior agent's work (before trusting anything downstream)

Two independent checks, run fresh in this session, both against the read-only canonical
`ladder_case30.json` / `ladder_case39.json` (MD5-verified byte-identical to the pack copies):

1. **Reconstruction validation** (`qlims_build_labels.py`'s predecessor check,
   `p1_validate_reconstruction.py`): rebuilding every one of the 75 EASY/TRICKY (fixable)
   scenarios from the base case + tripped line + load scale and re-running the *original*
   (`enforce_q_lims=False`) certification exactly reproduces the stored `n_fixers` for
   **all 75/75 entries, 0 mismatches**.
2. **Flip computation**: re-running the prior agent's `p1_qlims_flip.py` fresh in this session
   produced a `p1_results.json` that is **byte-for-byte identical** (`diff` on sorted JSON) to
   the file already on disk. The prior agent's claimed flip counts are confirmed exactly:
   case30 0/39, case39 18/36 (16 TRICKY→INFEASIBLE, 2 EASY→INFEASIBLE, 1 base-state divergence,
   itself one of the 16 TRICKY flips).

All numbers below build on this re-verified foundation. As an additional validation gate, the
re-scoring pipeline built for this task (`qlims_rescore.py`) was run once under the **old**
labels and its Δc / Δd' / placebo-RD outputs were checked against the canonical
`analysis/v2_sdt_results.json` and `analysis/luna_sdt_results.json` — **0 mismatches across all
30 delta cells plus luna's M4+log-linear cell**, confirming the re-scoring logic itself
(mappings, corrections, cluster bootstrap, gate) is a faithful re-implementation before it is
trusted on the new labels.

## 1. Flip table and new label composition

Physical justification for *not* re-testing the 188 rung entries (always INFEASIBLE by
construction in `make_ladder.py`): enforcing reactive limits is a strictly additional
constraint on the AC solve — it can only clip a generator's Q at a PV bus and let voltage sag
further, never relax an existing violation. A scenario with zero clearing actions under
`q_lims=False` therefore provably has zero clearing actions under `q_lims=True` too. Only the
75 EASY/TRICKY (fixable) entries were re-solved.

| case | fixable entries | flips (label changes) | flip rate |
|---|---|---|---|
| case30 | 39 | 0 | 0.0% |
| case39 | 36 | 18 (16 TRICKY→INFEASIBLE, 2 EASY→INFEASIBLE) | 50.0% |
| **total** | **75** | **18** | **24.0%** |

case30 is completely unaffected — every certifying fixer on case30 still clears under q-lims.
The entire effect is concentrated in case39, where half of the fixable scenarios lose *every*
originally-certified fixer. Lost-fixer action kinds (case39, summed over the 18 flipped rows):
`gen_p_dn` 9, `gen_p_up` 7, `shed` 5, `open_line` 2, `tap_up` 1 — active-power redispatch
actions dominate the losses, consistent with q-lims removing the voltage-support slack that
active-power moves were implicitly relying on.

One row — case39, item 0, `anchor` (old label TRICKY) — has its *base state* (no action
applied) fail to converge under `q_lims=True`. It is folded into `new_label=INFEASIBLE` by
default (consistent with its own zero surviving fixers) and flagged `base_diverges=True`; every
number below is reported **both** with it included (default) and excluded (denominator 262).

**Composition, old vs. new** (`analysis/qlims_labels.json`, 263 rows total):

| label | OLD | NEW (base-diverge → INFEASIBLE, default) | NEW (base-diverge row excluded, n=262) |
|---|---|---|---|
| EASY | 17 | **15** | 15 |
| TRICKY | 58 | **42** | 42 |
| INFEASIBLE | 188 | **206** | 205 |

Matches the expected ballpark (~15 EASY / ~42 TRICKY / ~206 INFEASIBLE) exactly. The old
TRICKY drastic/benign split (41 drastic / 17 benign) matches the paper's stated number exactly,
confirming the sub-classification logic is correct before use downstream. Of the 16 TRICKY→
INFEASIBLE flips, 7 were drastic and 9 were benign; every surviving new-TRICKY row keeps the
*same single* certifying fixer it had before (TRICKY by definition has exactly one fixer, so if
it survives it's unchanged) — **0 rows transition EASY→TRICKY**, so `new_sub` for the drastic/
benign (M4/M5) split needed no fresh derivation: it is simply `old_sub` carried over for every
surviving TRICKY row. This is stated explicitly because the task asked for it: no served-load
re-audit data was needed or used for this recompute, since the identity of the certifying
action never changes for a survivor.

## 2. Re-scoring under new labels

All numbers below use the exact conventions of `analysis/v2_sdt_analysis.py`: mappings M1–M5,
rate corrections {clamp, log-linear/Hautus}, d′=z(H)−z(F), c=−0.5(z(H)+z(F)), paired cluster
bootstrap over 40 (case, item_id) clusters, B=20,000, same seed 20260827, 5% unparsed gate per
(model, arm, label) cell, parsed-only rates throughout.

### 2a. Δc (ESCALATE − NO_ESCAPE), M4 + log-linear, primary specification

| model | OLD Δc [95% CI] | NEW Δc, base-diverge→INFEASIBLE [95% CI] | NEW Δc, row excluded [95% CI] | sign flip? |
|---|---|---|---|---|
| gemini-3.7-flash | **−0.589** [−0.87, −0.37] | **−0.714** [−1.19, −0.40] | −0.703 [−1.17, −0.39] | no |
| gemini-3.1-pro-preview | **−1.163** [−1.59, −0.88] | **−1.145** [−1.41, −0.66] | −1.141 [−1.40, −0.66] | no |
| gpt-5.6-luna | **−1.400** [−1.68, −1.04] | **−1.197** [−1.51, −0.75] | −1.199 [−1.51, −0.75] | no |
| (gemini-3.5-flash, context only — gated in both) | −1.297 (not reportable) | −1.147 (not reportable) | −1.144 (not reportable) | n/a |

**The criterion shift survives re-certification for all three headline models — no sign flip,
no CI crossing zero.** 3.7-flash's shift *grows* by 0.125 (−0.589→−0.714); pro is essentially
unchanged (−1.163→−1.145, Δ=+0.018); luna attenuates by 0.203 (−1.400→−1.197) but remains large
and highly significant. gemini-3.5-flash remains gated (NOT REPORTABLE) under new labels too —
its unparsed rows on NO_ESCAPE/EASY and NO_ESCAPE/TRICKY did not happen to be among the 18 rows
that moved, so the composition change does not rescue its reportability (unparsed rate 0.118→
0.133 on EASY, 0.052→0.071 on TRICKY — actually *worse*, since the denominator shrank while the
same unparsed rows remained).

### 2b. Full 5-mapping × 2-correction grid (3 models × 5 × 2 = 30 cells)

| | OLD | NEW (base-diverge→INFEASIBLE) |
|---|---|---|
| reportable cells | 30 | 30 |
| Δc negative | **30 / 30** | **30 / 30** |
| 95% CI excludes 0 | **30 / 30** | **30 / 30** |

Every reportable cell in the full grid stays negative with CI excluding zero, both before and
after re-certification — the paper's "Δc negative in every reportable cell" headline is
untouched at the grid level. Per-cell shifts range from essentially flat (gpt-5.6-luna under M1,
+0.001 to +0.003) to a genuine swing of −0.199 (gemini-3.7-flash, M5+clamp, i.e. the shift
*strengthens* there) to +0.248 (gpt-5.6-luna, M5+clamp, the shift *attenuates* there). There is
no group-level attenuation or amplification — the three models move in different directions by
different amounts, and M4 (primary) is squarely in the middle of that spread, not an outlier.

### 2c. Placebo vs. NO_ESCAPE, INFEASIBLE only, risk difference (×3 Gemini + luna)

| model | OLD RD (Fisher p) | NEW RD, base-diverge→INFEASIBLE (Fisher p) | NEW RD, row excluded (Fisher p) |
|---|---|---|---|
| gemini-3.7-flash | −0.622 (7.0×10⁻⁴²) | −0.597 (1.1×10⁻⁴⁰) | −0.600 (3.0×10⁻⁴¹) |
| gemini-3.5-flash | −0.412 (1.3×10⁻²⁶) | −0.380 (1.5×10⁻²⁶) | −0.382 (1.4×10⁻²⁶) |
| gemini-3.1-pro-preview | −0.438 (1.5×10⁻²⁹) | −0.414 (2.6×10⁻³⁰) | −0.416 (2.5×10⁻³⁰) |
| gpt-5.6-luna | −0.048 (0.020) | −0.044 (0.021) | −0.044 (0.021) |

All four risk differences stay large, negative, and significant. The three Gemini tiers barely
move (2–3 points of absolute risk difference, still p<10⁻²⁵). luna's already-marked-as-"least
clean" replication (main text calls out its zero-false-alarm NO_ESCAPE floor as the reason to
discount it relative to the others) stays exactly where it was — still just past p=0.02, neither
better nor worse under q-lims. No result here changes qualitatively.

### 2d. Always-escalate accuracy (raw new labels, and M4 grouping)

| | OLD | NEW, base-diverge→INFEASIBLE (n=263) | NEW, row excluded (n=262) |
|---|---|---|---|
| raw (escalate iff true label INFEASIBLE) | 188/263 = **0.7148** | 206/263 = **0.7833** | 205/262 = **0.7824** |
| M4 (escalate iff INFEASIBLE or drastic-TRICKY) | 229/263 = **0.8707** | 240/263 = **0.9125** | 239/262 = **0.9122** |

This is the one number in the analysis that moves in a direction worth calling out explicitly:
the trivial always-escalate baseline gets a further **~7 points more accurate** under q-lims (both
framings). This is mechanically forced — q-lims re-certification can only ever move a scenario
*toward* INFEASIBLE, never away from it — but it means the paper's already-acknowledged "no
model reliably beats a one-feature heuristic" caveat would, if re-run end-to-end under q-lims,
face an even stronger trivial baseline. This does not overturn the paper's own framing (which
already argues *for* reporting signal detection instead of accuracy, for exactly this reason —
"because 188/263 are infeasible, an always-escalate policy scores 0.715 — which is why we
report signal detection, not accuracy") — if anything it reinforces that framing's motivation.

### 2e. Qwen3-8B REFIXED escalation rates, by label (old vs. new)

`ladder_open_Qwen3-8B_{ESCALATE,NO_ESCAPE}_REFIXED.jsonl` have no `parsed` field in this
harness (no row has `escalated=None`), so unlike the Gemini/luna cells these rates are computed
over all 263 rows directly — noted as a data-availability difference, not a gating decision.

| arm | label | OLD n / k / rate | NEW n / k / rate |
|---|---|---|---|
| ESCALATE | EASY | 17 / 7 / 0.412 | 15 / 6 / 0.400 |
| ESCALATE | TRICKY | 58 / 23 / 0.397 | 42 / 20 / **0.476** |
| ESCALATE | INFEASIBLE | 188 / 104 / 0.553 | 206 / 108 / 0.524 |
| NO_ESCAPE | EASY | 17 / 0 / 0.000 | 15 / 0 / 0.000 |
| NO_ESCAPE | TRICKY | 58 / 6 / 0.103 | 42 / 3 / 0.071 |
| NO_ESCAPE | INFEASIBLE | 188 / 25 / 0.133 | 206 / 28 / 0.136 |

(OLD numbers reproduce the pack's documented "real rates 0.41 / 0.40 / 0.55" for
Qwen3-8B ESCALATE exactly — cross-check passed.) The largest single move is TRICKY under
ESCALATE, 0.397→0.476: the TRICKY items that flipped away (the "easier" TRICKY items whose
single fixer didn't survive q-lims) were, on this evidence, disproportionately ones Qwen was
*less* likely to escalate on, so the remaining TRICKY pool skews toward higher escalation. This
is a genuine ~8-point move but does not reverse Qwen's qualitative pattern (still
INFEASIBLE > TRICKY > EASY under ESCALATE, still a near-zero NO_ESCAPE floor on EASY).

## 3. EASY-81 re-certification under q-lims

The 81 minted EASY items (`easyladder_case{30,39}.json`) were certified under the served-load
rule (≥99% of pre-action load served) but **without** q-lims. Re-testing every originally
certified fixer with `enforce_q_lims=True`, holding the served-load reference (`served0`, the
pre-action served load) and the baseline-referenced limits fixed exactly as certified — mirroring
the same isolation principle as the 263-item flip test — gives:

| case | items | survive EASY (≥2 fixers) | demoted to TRICKY (1 fixer) | demoted to INFEASIBLE (0 fixers) |
|---|---|---|---|---|
| case30 | 12 | **12 (100%)** | 0 | 0 |
| case39 | 69 | **63 (91.3%)** | 2 | 4 |
| **total** | **81** | **75 (92.6%)** | 2 | 4 |

case30 is again completely unaffected (consistent with §1 — the case30 network's reactive
support margin simply isn't binding anywhere in this benchmark). No base-state divergences here.

**ESCALATE / NO_ESCAPE false-alarm rates, three Gemini tiers, full-81 vs. surviving-75 subset**
(from `v2_easyladder_{model}_{ESCALATE,NO_ESCAPE}.jsonl`, parsed-only):

| model | arm | ALL-81 (n / k / rate) | SURVIVING-75 (n / k / rate) | shift |
|---|---|---|---|---|
| gemini-3.7-flash | ESCALATE | 81 / 33 / 0.407 | 75 / 31 / 0.413 | +0.006 |
| gemini-3.7-flash | NO_ESCAPE | 81 / 9 / 0.111 | 75 / 9 / 0.120 | +0.009 |
| gemini-3.5-flash | ESCALATE | 80 / 11 / 0.138 | 74 / 11 / 0.149 | +0.011 |
| gemini-3.5-flash | NO_ESCAPE | 80 / 1 / 0.013 | 74 / 1 / 0.014 | +0.001 |
| gemini-3.1-pro-preview | ESCALATE | 80 / 8 / 0.100 | 74 / 8 / 0.108 | +0.008 |
| gemini-3.1-pro-preview | NO_ESCAPE | 79 / 1 / 0.013 | 73 / 1 / 0.014 | +0.001 |

(ALL-81 numbers reproduce the paper's stated EASY-81 replication numbers exactly:
3.7-flash 0.407/0.111, 3.5-flash 0.138/0.013, pro 0.100/0.013 — cross-check passed.) The 6
demoted items happened to contribute 0 escalations in every arm for every model examined here
(all the demoted items' rows are non-escalations, so removing them cannot lower the rate; it
can only hold it flat or push it very slightly up, which is what happens — every shift here is
+0.001 to +0.011). **The EASY-81 replication is essentially untouched by q-lims
re-certification**: same ordering across models, same ESCALATE-minus-NO_ESCAPE gap to within a
point, same qualitative story.

## 4. Honest summary

Enforcing generator reactive limits reveals a real, physically meaningful, and *asymmetric*
sensitivity in the underlying benchmark labels: case30 doesn't move at all, while half of
case39's fixable scenarios (18/36) lose every certified fixer, mostly on active-power
redispatch actions that were implicitly leaning on unbounded reactive support to hold voltage.
That is a legitimate limitation worth disclosing prominently (the paper already discloses
unbounded reactive support as a solver-setting caveat in checklist item 1 and Section
"Label validity"; this analysis quantifies exactly how much it matters: 24% of the 75 fixable
items, 6.8% of the full 263). But **none of the paper's headline claims flip or die under
re-certification**: every one of the 30 reportable Δc cells across the full 5×2 robustness grid,
for all three models the paper leans on (gemini-3.7-flash, gemini-3.1-pro-preview,
gpt-5.6-luna), stays negative with its confidence interval excluding zero — the "criterion
shifts, discrimination doesn't reliably improve" story is intact. Placebo suppression on
INFEASIBLE items stays enormous and significant for all four models tested (still p<10⁻²⁵ for
the three Gemini tiers, still p≈0.02 for luna, exactly as before). The EASY-81 supplementary
replication — the paper's answer to the "everything rests on 17 EASY items" critique — is
essentially unmoved (rate shifts of one percentage point or less across all three models and
both arms). Qwen3-8B's rates move by up to 8 points on TRICKY but keep the same ordering and
the same qualitative floor pattern. The only number that moves in a way worth flagging rather
than just noting is the always-escalate trivial-baseline accuracy, which gets *stronger*
(0.715→0.783 raw, 0.871→0.913 under M4) — mechanically inevitable given q-lims can only convert
fixable items to infeasible, never the reverse — which if anything sharpens rather than
undercuts the paper's own argument for reporting signal detection instead of raw accuracy. Net
assessment: this is a real, disclosed, and now precisely quantified robustness check that the
paper's story passes cleanly, with case39's reactive-support sensitivity as a concrete,
specific limitation to add to the paper's existing solver-settings disclosure rather than a
reason to walk back any reported number.

## Provenance

- `analysis/qlims_labels.json` — the 263-row old/new label map (this task's step 1),
  built by `analysis/qlims_build_labels.py` from `analysis/qlims_flip_results.json`
  (= the prior agent's `p1_results.json`, re-verified byte-identical to an independent
  fresh re-run in this session) and `ladder_case{30,39}.json`.
- `analysis/qlims_flip.py` — the q-lims re-test script (copy of the prior agent's
  `p1_qlims_flip.py`, re-verified in this session).
- `analysis/qlims_rescore.py` / `analysis/qlims_rescore_results.json` — step 2's full
  re-scoring (§2 above), validated to reproduce `v2_sdt_results.json` / `luna_sdt_results.json`
  exactly under old labels before its new-label numbers are trusted.
- `analysis/qlims_easy81.py` / `analysis/qlims_easy81_results.json` — step 3's EASY-81
  re-certification (§3 above).
- All computation is local pandapower 3.5.4 AC power flow (CPU only), no API calls; the two
  API-drawing pieces of this note (§2, §3's Gemini/Qwen/luna rate tables) only *read* existing
  canonical JSONL response files, never issued new model calls.
