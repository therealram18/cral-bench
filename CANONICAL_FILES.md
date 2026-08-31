# Canonical files — power-grid escalation pack

Purpose: declare, per result reported in the paper, which files in this directory
are the ones to analyze. Everything not listed as canonical below is either
quarantined or kept for the historical record only and **must not** be fed to
any analysis script.

## Gemini, 263-item benchmark (harness_v2, all 3 arms)

**Canonical:** `v2_ladder_gemini-{3.1-pro-preview,3.5-flash,3.7-flash}_{ESCALATE,NO_ESCAPE,PLACEBO}.jsonl`
(9 files, 263 rows each). This is the data behind Table 1 and the SDT robustness
grid (`analysis/v2_sdt_results.json`, `analysis/v2_sdt_report.md`) for the
ESCALATE/NO_ESCAPE contrast. Verified against `v2_runs.log` (27/27 cells MATCH).

**CONFOUNDED — superseded, 2026-08-28:** the PLACEBO arm in these same files
silently omitted NO_ESCAPE's NONE-permission sentence (an arm-conditional
confound found by rendering/byte-diffing every arm before any API call). The
"placebo suppresses escalation" finding computed from the PLACEBO column of
these files (RD −0.622/−0.412/−0.438 across the three Gemini tiers) is
**retracted-in-place**: report only as the confounded value being corrected,
never as a standalone finding. The corrected comparison is the
**PLACEBO_NONE** arm below (`harness_v2b.py`), under which suppression
vanishes for all three Gemini tiers (flash 0.957 vs. 0.968 n.s.; pro 0.438 vs.
0.438 identical). The ESCALATE/NO_ESCAPE columns of these files are
unaffected by this confound and remain canonical as stated above.

## Gemini, confound-control arms (harness_v2b, PLACEBO_NONE + NONE_INDEX) — added 2026-08-28

**Canonical:** `v2_ladder_gemini-{3.1-pro-preview,3.7-flash}_{PLACEBO_NONE,NONE_INDEX}.jsonl`
(4 files, 263 rows each, produced by `harness_v2b.py`; gemini-3.5-flash's v2b arms were not run since its
NO_ESCAPE baseline is already gated). PLACEBO_NONE = the original PLACEBO
decoy plus the byte-identical NONE-permission sentence NO_ESCAPE has and
PLACEBO lacked (the corrected placebo comparison, superseding the PLACEBO
column above). NONE_INDEX = an index-form bare decline option with no
"ESCALATE" word and no human-operator clause (isolates the affordance from
its wording). Canonical analysis outputs: `analysis/v2b_results.json`,
`analysis/v2b_results.md` (produced by `analysis/v2b_sdt_analysis.py`).

## Framing-increment analysis (headline wording test) — added 2026-08-28

**Canonical:** `analysis/framing_increment.json`, `analysis/framing_increment.md`
(produced by `analysis/framing_increment.py`), computing
Δc(ESCALATE) − Δc(NONE_INDEX) on one shared paired cluster-bootstrap resample
across all three headline models (gemini-3.7-flash, gemini-3.1-pro-preview,
gpt-5.6-luna-2026-07-09) and the full 5-mapping × 2-correction robustness
grid. Depends on the v2b files above and the luna v2b files below.

## Q-lims oracle-sensitivity re-certification — added 2026-08-28

**Canonical:** `analysis/qlims_labels.json`, `analysis/qlims_flip_results.json`,
`analysis/qlims_rescore_results.json`, `analysis/qlims_easy81_results.json`,
and the narrative `analysis/qlims_sensitivity.md` (built by
`analysis/qlims_build_labels.py`, `analysis/qlims_flip.py`,
`analysis/qlims_rescore.py`, `analysis/qlims_easy81.py`). Re-certifies the 75
fixable (EASY/TRICKY) items under `enforce_q_lims=True`; read-only against
`ladder_case{30,39}.json`/`easyladder_case{30,39}.json`, issues no new API
calls.

## Gemini, EASY-81 stricter supplement (harness_v2, 2 arms: ESCALATE, NO_ESCAPE)

**Canonical:** `v2_easyladder_gemini-{3.1-pro-preview,3.5-flash,3.7-flash}_{ESCALATE,NO_ESCAPE}.jsonl`
(6 files, 81 rows each, all label EASY). These are the completed re-runs behind
the EASY-81 replication numbers in the paper (3.7-flash 0.407/0.111, 3.5-flash
0.138/0.013 parsed-only, pro 0.100/0.013 parsed-only; unparsed <= 2/81 in every
cell). Never pool with the 263-item files above.

**Quarantined — do not analyze:** `archive_429_freetier/v2_easyladder_gemini-{3.5-flash,3.7-flash}_{ESCALATE,NO_ESCAPE}.jsonl`.
These are earlier attempts at the same 4 files, 79-100% HTTP 429 (free-tier
daily quota) per `archive_429_freetier/WHY_ARCHIVED.txt`. `harness_v2.py`
resumes by `(case, item_id, tag)` regardless of parse status, so if a paid-key
re-run is ever needed these must stay out of the working directory — they were
moved aside for exactly that reason. The gemini-3.1-pro-preview EASY-81 pair
was never 429-quarantined; its only versions are the canonical ones above.

## EASY-81, NONE_INDEX arm + luna N/E backfill + false-alarm decomposition — added 2026-08-29

**Canonical:** `v2_easyladder_{gemini-3.7-flash,gemini-3.1-pro-preview,gpt-5.6-luna}_NONE_INDEX.jsonl`
(3 files, 81 rows each, all label EASY, produced by `harness_v2b.py` for the two Gemini
tiers and `harness_v2b_azure.py` for luna — both scripts already honored `LADDER_PREFIX`
identically to `harness_v2.py`, so no new harness file was needed). Also canonical:
`v2_easyladder_gpt-5.6-luna_{NO_ESCAPE,ESCALATE}.jsonl` (2 files, 81 rows each, produced by
`harness_v2_azure.py` with `LADDER_PREFIX=easyladder` — luna had no EASY-81 reference arms
before this run, so both were run fresh, 162 calls, rather than reporting luna as
NONE_INDEX-rate-only). All 9 cells (3 models x {NO_ESCAPE,NONE_INDEX,ESCALATE}) verified: 81
rows, 0 duplicate `(case,item_id,tag)` keys, unparsed <= 2/81 per cell (all under the 5%
gate), 0 rows carrying a non-null `error` field.

Point rates (parsed-only): gemini-3.7-flash 0.111/0.247/0.407 (NO_ESCAPE/NONE_INDEX/ESCALATE);
gemini-3.1-pro-preview 0.013/0.051/0.100; gpt-5.6-luna 0.000/0.000/0.074.

**Canonical analysis:** `analysis/easy81_none_index.{json,md}` (produced by
`analysis/easy81_none_index.py`), decomposing the false-alarm rate into N->I (offering a bare
"NONE" index slot vs. none at all) and I->E (renaming that same slot "ESCALATE" + adding
human-operator language), paired cluster bootstrap (cluster=(case,item_id), n_clusters=81 —
this supplement has no margin-ladder rungs, so cluster bootstrap here is equivalent to
item-level bootstrap; see `clustered_ci.py`'s note on the 263-item corpus for contrast),
B=20,000, seed=20260827. Both components exclude zero for gemini-3.7-flash (N->I
+0.136 [+0.062,+0.210]; I->E +0.160 [+0.086,+0.247]); neither excludes zero for
gemini-3.1-pro-preview (small-n: only 79-80 parsed rows); for gpt-5.6-luna N->I is exactly
0 (0/81 in both arms) and I->E alone carries its entire EASY-81 false-alarm cost (+0.074
[+0.025,+0.136], excludes zero) — i.e. luna's false alarms are driven entirely by the
ESCALATE/human-operator wording, not by the mere presence of a decline option.

## Qwen3-8B (open-weight, ladder_open.py / ladder_open_v2.py)

**Canonical:** `ladder_open_Qwen3-8B_{ESCALATE,NO_ESCAPE}_REFIXED.jsonl` for the
263-item ESCALATE/NO_ESCAPE arms, plus `ladder_open_Qwen3-8B_PLACEBO.jsonl` and
`easyladder_open_Qwen3-8B_{ESCALATE,NO_ESCAPE}.jsonl` (both produced by
`ladder_open_v2.py`, generated after the fix below and never affected by it).

**Superseded — do not analyze:** `ladder_open_Qwen3-8B_{ESCALATE,NO_ESCAPE}.jsonl`
(non-REFIXED). These predate the fair-instrument fix: the harness let the
model emit a bare menu index with no reasoning, producing the retracted
"Qwen3-8B capability floor" artifact. Real rates are the REFIXED files (see
`README_POWERGRID.md`, "Retractions on record").

## Qwen3-14B (open-weight, ladder_open.py / ladder_open_v2.py)

**Canonical:** `ladder_open_Qwen3-14B_{ESCALATE,NO_ESCAPE}.jsonl` (already run
on the fair-instrument prompt — confirmed by inspection, `raw` field carries
full reasoning text, not a bare index — so no REFIXED variant exists or is
needed), plus `ladder_open_Qwen3-14B_PLACEBO.jsonl` and
`easyladder_open_Qwen3-14B_{ESCALATE,NO_ESCAPE}.jsonl` (both from
`ladder_open_v2.py`).

## Pre-rebuild files — kept for the record only, never analyze for numbers

`ladder_llm_gemini-*_{ESCALATE,NO_ESCAPE,PLACEBO}.jsonl` (including the
`_think.jsonl` variants) and `easyladder_llm_gemini-*_{ESCALATE,NO_ESCAPE}.jsonl`,
wherever they appear (top-level directory and `archive/`, which holds a second,
differing copy of the gemini-3.1-pro-preview pair). These predate the
harness_v2 rebuild: the pro tier used an 800-token cap that truncated
78.3%/48.3% of rows (scored as non-escalation, since retracted), and flash-tier
magnitudes are not comparable post-rebuild even though the direction of every
effect survives (`analysis/v2_sdt_report.md` \S6). Also in this bucket:
`stale_prefix_fix_placebo_ORIGINAL.jsonl`, the pre-fix placebo file from when
placebo rows were briefly double-counted as escalation (70/263); superseded
in place, kept only as a record of the bug.

## Everything else

`gemres_*.jsonl`, `ptdf_corpus*.json`, `calibration.json`, `twins_case30.json`,
`ladder_case{30,39}.json`, `easyladder_case{30,39}.json`,
`minted_easy_case{30,39}.json`, `depth2_case30.json`, `audit_fixers.json`,
`b2_spread.json`, `rating_audit.json`, `gate0_ptdf.json`, `loop_sweep.json` and
the `.py`/`.log` scripts are construction, calibration, and sentinel-audit
artifacts (Section "A methods note" and the label-validity audit), not
per-model result files, and are unaffected by this manifest.

## Depth-2 served-load sensitivity (added 2026-08-28)
`depth2_sensitivity.py` + `depth2_sensitivity.json` + `depth2_sensitivity_summary.md`
are CANONICAL for the paper's depth-2 threshold-sensitivity claim. The script is an
adaptation of `depth2.py`/`certify_v2.py` (same seed 20260827, same 500-pair budget,
same 10 scenarios); it exactly reproduces the 0/10 result of `depth2_v2.log` at
SERVED_TOL=0.99 before extending to 0.95 and 0.90 (2/10 fixable at each — only the
least-severe rung of each contingency; the other 8/10 unfixable at every threshold).

## Third-family replication: gpt-5.6-luna (Azure) (added 2026-08-28)

**Canonical:** `v2_ladder_gpt-5.6-luna_{NO_ESCAPE,ESCALATE,PLACEBO}.jsonl` (3 files,
263 rows each, all under the 5% unparsed gate on every cell). Deployment name is
`gpt-5.6-luna` (Azure OpenAI, Sweden Central); the echoed model identity to cite in
the paper is always the full string `gpt-5.6-luna-2026-07-09` (never "luna" alone) —
confirmed identical across all 789 rows via the `model_echo` field. This is the data
behind the paper's third-model-family replication of the criterion shift
(M4+log-linear $\Delta c = -1.400$, 95% CI $[-1.681, -1.043]$, cluster bootstrap
$B=20{,}000$).

**CONFOUNDED — superseded, 2026-08-28:** the placebo-suppression number
previously listed here (PLACEBO 2/188 vs. NO_ESCAPE 11/188, RD $-0.048$,
Fisher $p=0.020$) shares the same arm-conditional confound as the Gemini
PLACEBO files above (PLACEBO silently omitted NO_ESCAPE's NONE-permission
sentence) and is **retracted-in-place** — report only as the confounded
value being corrected, never as a standalone finding. The corrected
comparison is `v2_ladder_gpt-5.6-luna_PLACEBO_NONE.jsonl` (18/188 = 0.096
vs. NO_ESCAPE 11/188 = 0.059, RD $+0.037$, 95% CI $[-0.016,+0.089]$, Fisher
$p=0.246$, **not significant** — the suppression finding does not survive
for luna either). The ESCALATE/NO_ESCAPE columns and the $\Delta c=-1.400$
criterion-shift result above are unaffected by this confound and remain
canonical as stated.

Also canonical: `v2_ladder_gpt-5.6-luna_{PLACEBO_NONE,NONE_INDEX}.jsonl` (2
files, 263 rows each, produced by `harness_v2b_azure.py`), the luna parallel
of the Gemini v2b confound-control arms; NONE_INDEX gives the bare-affordance
$\Delta c = -0.617$ feeding the framing-increment result
(`analysis/framing_increment.md`). Analysis outputs:
`analysis/luna_v2b_results.json`, produced by `analysis/luna_v2b_analysis.py`.

Also canonical for the original 3-arm result: `harness_v2_azure.py` (this
directory) and `../common/llmcall_azure.py` (the one-call Azure backend it
routes through) — a harness copy of `harness_v2.py` with identical
prompts/arms/scoring/retry ladder/row schema, so numbers are directly
comparable to the Gemini/Qwen tiers. `analysis/luna_sdt_results.json` (full
numbers) and `analysis/luna_results.md` (narrative writeup, produced by
`analysis/luna_sdt_analysis.py`; also holds the v2b follow-up narrative) are
the canonical analysis outputs; re-derive from the JSONLs above, not from any
other copy.

Note: `v2_ladder_gpt-5.6-luna_*` are new files at the top level of this directory,
not a rename or overwrite of any existing pinned Gemini/Qwen file — no other
manifest entry above is affected.
