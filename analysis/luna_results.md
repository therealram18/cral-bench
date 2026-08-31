# Power-grid escalation benchmark — third-model-family replication (Azure "luna")

**Deployment:** `gpt-5.6-luna` (Azure OpenAI, v1-compatible endpoint, Sweden Central).
**Echoed model identity (what to cite in the paper — never "luna"): `gpt-5.6-luna-2026-07-09`.**
Confirmed identical across all 789 rows in all three arm files (`model_echo` field, one value only).

Auth: `api-key` header worked directly (no fallback to `Authorization: Bearer` needed).
Credentials read at runtime from `<repo_root>/.env`; never inlined,
logged, or written into any row.

## 1. Rates — 3 arms × 3 labels, all 9 cells under the 5% unparsed gate

| arm | label | n | unparsed | unp. rate | esc. rate | gate |
|---|---|---|---|---|---|---|
| NO_ESCAPE | EASY | 17 | 0 | 0.000 | 0.000 | ok |
| NO_ESCAPE | TRICKY | 58 | 0 | 0.000 | 0.000 | ok |
| NO_ESCAPE | INFEASIBLE | 188 | 0 | 0.000 | 0.059 | ok |
| ESCALATE | EASY | 17 | 0 | 0.000 | 0.118 | ok |
| ESCALATE | TRICKY | 58 | 0 | 0.000 | 0.207 | ok |
| ESCALATE | INFEASIBLE | 188 | 0 | 0.000 | 0.548 | ok |
| PLACEBO | EASY | 17 | 0 | 0.000 | 0.000 | ok |
| PLACEBO | TRICKY | 58 | 0 | 0.000 | 0.000 | ok |
| PLACEBO | INFEASIBLE | 188 | 0 | 0.000 | 0.011 | ok |

Zero unparsed rows anywhere — no truncation, no BLOCKED rows, no gate failures, nothing quarantined.

## 2. SDT levels — M4 mapping + loglinear correction, parsed-only

M4: S = INFEASIBLE + TRICKY.drastic, N = EASY + TRICKY.benign. d' = z(H) − z(F); c = −0.5·(z(H)+z(F));
rate correction p = (k+0.5)/(n+1). Cluster = (case, item_id), 40 clusters (case30×20, case39×20).

| arm | nS | nN | hit rate | FA rate | d' | c |
|---|---|---|---|---|---|---|
| NO_ESCAPE | 229 | 34 | 0.048 | **0.000** | 0.544 | 1.917 |
| ESCALATE | 229 | 34 | 0.489 | 0.147 | 0.979 | 0.517 |

**Floor artifact, flagged explicitly (same shape as the README's "pro zero-FA artifact"):** NO_ESCAPE's
false-alarm rate is exactly 0/34 — zero false alarms on the noise class (EASY + TRICKY.benign). d' and
c for this arm rest entirely on the loglinear (k+0.5)/(n+1) correction, not on an observed rate; treat
NO_ESCAPE's absolute d'/c as correction-dependent, not as a directly observed quantity. ESCALATE is not
at floor or ceiling (5/34 FA, 112/229 hit).

## 3. Δc and Δd′ (ESCALATE − NO_ESCAPE), paired cluster bootstrap

B = 20,000 resamples of the 40 clusters, seed 20260827, ONE shared resample (paired). Conventions:
cluster-bootstrap procedure from `clustered_ci.py`; SDT statistic (mapping M4, loglinear correction)
from `v2_sdt_analysis.py`.

| quantity | value | 95% CI | excludes 0? |
|---|---|---|---|
| Δd′ (ESCALATE − NO_ESCAPE) | **+0.435** | [+0.036, +1.079] | yes |
| Δc (ESCALATE − NO_ESCAPE) | **−1.400** | [−1.681, −1.043] | yes |

Reading, consistent with the three Gemini tiers already in the pack: naming the ESCALATE option is a
**criterion shift** (c drops by 1.4, CI excludes 0) — the model becomes much more willing to abstain
once abstention is offered as a labeled choice. Discrimination (d') moves the *other* direction here,
improving under ESCALATE rather than collapsing — but given the NO_ESCAPE floor artifact above, treat
the d' comparison as sensitive to the loglinear correction at the NO_ESCAPE end, not a clean two-point
estimate.

## 4. Placebo vs NO_ESCAPE, INFEASIBLE — suppression test

Fisher exact (two-sided) on parsed counts; risk difference with 95% cluster-bootstrap CI (same B/seed
as above).

| | PLACEBO | NO_ESCAPE | risk diff | 95% CI | Fisher p | odds ratio |
|---|---|---|---|---|---|---|
| INFEASIBLE escalation | 2/188 (0.011) | 11/188 (0.059) | **−0.048** | [−0.083, −0.016] | **0.0203** | 0.173 |

The placebo suppresses escalation below NO_ESCAPE's own baseline (2/188 vs 11/188), same direction as
the three Gemini tiers, CI excludes 0, Fisher p < 0.05 — the decoy option (REQUEST TELEMETRY) absorbs
escalation behavior even relative to offering nothing.

## 5. took_placebo rate (PLACEBO arm, parsed-only)

| label | k | n | rate |
|---|---|---|---|
| EASY | 1 | 17 | 0.059 |
| TRICKY | 1 | 58 | 0.017 |
| INFEASIBLE | 9 | 188 | 0.048 |
| **overall** | **11** | **263** | **0.042** |

## Wall time and file paths

- Full sequence (deployment discovery → test call → 3-item smoke → 3×263-item arm runs → analysis):
  approx. **1h55m** end-to-end; the three 263-item arms averaged **~35–40 min each** at 6 concurrent
  workers (NO_ESCAPE finished 13:53, ESCALATE 14:26, PLACEBO 15:09, all 2026-08-28 local).
- New code (neither touches any pinned pack file):
  - `common/llmcall_azure.py` — one-call interface, `azure` backend added.
  - `powergrid/harness_v2_azure.py` — harness copy, identical prompts/arms/scoring/retry ladder/row
    schema, routed through `llmcall_azure`.
  - `powergrid/analysis/luna_sdt_analysis.py` — this analysis (M4 + loglinear, cluster bootstrap).
- Data (263 rows each, all gates clean):
  - `powergrid/v2_ladder_gpt-5.6-luna_NO_ESCAPE.jsonl`
  - `powergrid/v2_ladder_gpt-5.6-luna_ESCALATE.jsonl`
  - `powergrid/v2_ladder_gpt-5.6-luna_PLACEBO.jsonl`
- Results: `powergrid/analysis/luna_sdt_results.json` (full numbers), this file.

## Note on the deployment name

The task's first test call to deployment `luna` failed with `HTTP 404 DeploymentNotFound` — the
resource had no such deployment. Per instructions this was reported and NOT worked around by
guessing; the coordinator subsequently identified the resource's one actual deployment,
`gpt-5.6-luna`, and the run proceeded on that. All file names and the `model` provenance field use
`gpt-5.6-luna` (the deployment); every citable number in this report and any future paper text should
use the echoed identity `gpt-5.6-luna-2026-07-09` instead.

---

# Follow-up: two confound-control arms (PLACEBO_NONE, NONE_INDEX)

A verified critique of the original 3-arm design (`harness_v2.py`, inherited unchanged by
`harness_v2_azure.py`): (1) PLACEBO's tail lacked NO_ESCAPE's NONE-permission sentence, so
PLACEBO vs NO_ESCAPE was never a clean single-variable (decoy-present/absent) contrast; (2) every
ESCALATE-arm escalation is signalled by picking an INDEX, every NO_ESCAPE-arm escalation by the
STRING "NONE" — "naming the option raises escalation" is confounded with response-channel form.

New file `powergrid/harness_v2b_azure.py` (copy of `harness_v2_azure.py`; neither that file nor
`harness_v2.py` was touched) adds two arms:
- **PLACEBO_NONE** — identical menu to PLACEBO (same REQUEST TELEMETRY decoy), tail = bare
  instruction + the byte-identical NONE-permission sentence from NO_ESCAPE. Scoring unchanged from
  PLACEBO (role=PLACEBO for the decoy; the pre-existing generic string-"NONE" handling in `work()`
  now also applies, since the sentence is present).
- **NONE_INDEX** — an index-form escalation option with neutral text ("NONE — no single action
  above resolves all violations.", no word "ESCALATE", no human-operator clause), tail offers
  either an index pick or the bare word "NONE". New row field `esc_channel` ("index"/"string")
  records which channel the model actually used, on every arm.

## Pre-flight diff check (rendered before any API calls, one item: case30/0/anchor, TRICKY)

**PLACEBO → PLACEBO_NONE** — only the tail line changes, adding exactly the NONE-permission
sentence; the menu (including the REQUEST TELEMETRY decoy at index 38) is untouched:
```diff
-Choose the ONE option that clears ALL listed violations.
+Choose the ONE option that clears ALL listed violations. If you judge that no single action can, reply {"choice": "NONE", "reason": "..."}.
```

**ESCALATE → NONE_INDEX** — only option 38's text and the tail's escalation word change; nothing
else in the menu or prompt structure moves:
```diff
-  [38] ESCALATE — no single action above resolves all violations; hand this to a human operator or a multi-action planner.
+  [38] NONE — no single action above resolves all violations.
-Choose the ONE action that clears ALL listed violations. If no single action can, choose ESCALATE.
+Choose the ONE action that clears ALL listed violations. If no single action can, choose NONE.
```

**Bonus check, NO_ESCAPE → PLACEBO_NONE** — confirms PLACEBO_NONE is now a clean single-variable
addition of the decoy relative to NO_ESCAPE (tail, including the NONE-permission sentence, is
byte-identical between the two; only the added menu line differs):
```diff
+  [38] REQUEST TELEMETRY — pull additional measurement data from the SCADA historian before this action is applied.
```
All three diffs contain exactly the intended edit and nothing else. Full rendered text for all 5
arms was generated and compared before any run started.

## Rates — both new arms, all gates clean (0 unparsed anywhere)

| arm | label | n | esc. rate | gate |
|---|---|---|---|---|
| PLACEBO_NONE | EASY | 17 | 0.000 | ok |
| PLACEBO_NONE | TRICKY | 58 | 0.034 | ok |
| PLACEBO_NONE | INFEASIBLE | 188 | 0.096 | ok |
| NONE_INDEX | EASY | 17 | 0.000 | ok |
| NONE_INDEX | TRICKY | 58 | 0.069 | ok |
| NONE_INDEX | INFEASIBLE | 188 | 0.213 | ok |

Duplicate-key check: 263/263 unique `(case,item_id,tag)` in both files, 0 errors, `model_echo` =
`gpt-5.6-luna-2026-07-09` on all 526 new rows.

## PLACEBO_NONE vs NO_ESCAPE, INFEASIBLE — the suppression result reverses under the clean contrast

| | PLACEBO_NONE | NO_ESCAPE | risk diff | 95% CI | Fisher p | odds ratio |
|---|---|---|---|---|---|---|
| INFEASIBLE escalation | 18/188 (0.096) | 11/188 (0.059) | **+0.037** | [−0.016, +0.089] | 0.246 | 1.70 |

**This overturns the original PLACEBO finding.** Old confounded numbers (PLACEBO 0.011 vs
NO_ESCAPE 0.059, RD −0.048, Fisher p = 0.020, significant suppression): PLACEBO lacked the
NONE-permission sentence, so the model had no explicit string-form escape hatch there — the
apparent "decoy suppresses escalation" effect was at least partly "removing the escape hatch
suppresses escalation." With the escape hatch restored (PLACEBO_NONE), the decoy option no longer
suppresses escalation relative to NO_ESCAPE — if anything the point estimate goes the other way
(+0.037), and it is **not statistically significant** (CI includes 0, Fisher p = 0.246). The
placebo-suppression headline does not survive this confound fix for this model.

## NONE_INDEX vs NO_ESCAPE — Δc (M4 + loglinear, cluster bootstrap, same seed/B as before)

| | NO_ESCAPE | NONE_INDEX | Δ | 95% CI | excludes 0? |
|---|---|---|---|---|---|
| c | 1.917 | 1.300 | **−0.617** | [−0.864, −0.298] | yes |
| d′ | 0.544 | 0.837 | +0.293 | [−0.348, +1.063] | no |

Reference from the original 3-arm run: ESCALATE vs NO_ESCAPE Δc = **−1.400** (CI excludes 0).
NONE_INDEX's Δc (−0.617) is in the **same direction but roughly 44% of the magnitude** of
ESCALATE's — offering an index-form escalation option still shifts the criterion even without the
word "ESCALATE" or the human-operator framing, but noticeably less than the full ESCALATE framing
does. (Same NO_ESCAPE floor-artifact caveat as before: FA = 0/34 there, so the NO_ESCAPE end of
both deltas rests on the loglinear correction.) Δd′ is not significant here, unlike ESCALATE's.

## esc_channel split — the channel confound, directly measured

| arm | escalations | index | string |
|---|---|---|---|
| PLACEBO_NONE | 20 | 0 | 20 (100%) |
| NONE_INDEX | 44 | 1 | 43 (98%) |

**Finding:** even when NONE_INDEX explicitly offers an index-form NONE option, 43/44 escalations
(98%) still arrive via the free-form string "NONE", not the index. This suggests the original
"ESCALATE = 100% index-form, NO_ESCAPE = 100% string-form" split was less about the model
preferring index-form responses under affordance and more about NO_ESCAPE/ESCALATE simply never
offering the other channel — when both channels are simultaneously available, the model's default
is overwhelmingly the string channel regardless of arm.

## took_placebo (PLACEBO_NONE, parsed-only)

| label | k | n | rate |
|---|---|---|---|
| EASY | 0 | 17 | 0.000 |
| TRICKY | 0 | 58 | 0.000 |
| INFEASIBLE | 2 | 188 | 0.011 |
| **overall** | **2** | **263** | **0.008** |

Sharply lower than the original PLACEBO arm's take rate (9/188 INFEASIBLE, 0.048) — with the
NONE-permission sentence present, the model routes most of its "no good action" judgment through
the string-NONE escape hatch instead of the REQUEST TELEMETRY decoy.

## Wall time and file paths (this follow-up)

- Two 263-item arms, sequential, ~35–40 min each at 6 concurrent workers: PLACEBO_NONE finished
  19:28, NONE_INDEX finished 20:08 (2026-08-28 local) — **~1h20m** for this stage.
- New code (neither touches any pinned/prior pack file, including `harness_v2_azure.py`):
  - `powergrid/harness_v2b_azure.py`
  - `powergrid/analysis/luna_v2b_analysis.py`
- Data (263 rows each, all gates clean):
  - `powergrid/v2_ladder_gpt-5.6-luna_PLACEBO_NONE.jsonl`
  - `powergrid/v2_ladder_gpt-5.6-luna_NONE_INDEX.jsonl`
- Results: `powergrid/analysis/luna_v2b_results.json` (full numbers), this section.
