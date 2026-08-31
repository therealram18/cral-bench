# Framing increment: does human-operator ESCALATE wording add a criterion shift beyond
# a bare in-schema NONE_INDEX affordance?

seed=20260827 | bootstrap B=20,000 | cluster = (case, item_id), n_clusters=40 | gate = 0.05

**CAVEAT (read first).** The ESCALATE<->NONE_INDEX contrast is a TWO-EDIT BUNDLE: (1) the menu label word 'ESCALATE' is replaced with 'NONE', and (2) the clause '; hand this to a human operator or a multi-action planner' is deleted. Any 'framing increment' reported here is the joint effect of both edits together, not of word choice alone.

Motivating null: Ling et al. 2507.16199 report abstain-option wording is irrelevant to model behavior (all pairwise comparisons n.s.). Their null predicts the increment tested here should be indistinguishable from zero.

## 0. Pipeline validation

Reproduction of the two published deltas per model, M4+loglinear, before any new computation:

| model | delta_c(ESCALATE-NO_ESCAPE) computed | published | match | delta_c(NONE_INDEX-NO_ESCAPE) computed | published | match |
|---|---|---|---|---|---|---|
| gemini-3.7-flash | -0.589 | -0.589 | OK | -0.332 | -0.332 | OK |
| gemini-3.1-pro-preview | -1.163 | -1.163 | OK | -0.774 | -0.774 | OK |
| gpt-5.6-luna | -1.400 | -1.400 | OK | -0.617 | -0.617 | OK |

**Validation result: ALL 6 VALUES MATCH to 3 decimals.**

## 1. Primary result: the increment, M4+loglinear

Increment = Delta c(ESCALATE) - Delta c(NONE_INDEX) = c(ESCALATE) - c(NONE_INDEX) on the SAME paired-cluster resample (the shared NO_ESCAPE term cancels algebraically; verified numerically in-script). 95% CI from B=20,000 paired cluster bootstrap iterates.

| model | delta_c(ESCALATE) | delta_c(NONE_INDEX) | INCREMENT | 95% CI | excludes 0? | status |
|---|---|---|---|---|---|---|
| gemini-3.7-flash | -0.589 | -0.332 | **-0.257** | [-0.462,-0.091] | **YES** | ok |
| gemini-3.1-pro-preview | -1.163 | -0.774 | **-0.388** | [-0.599,-0.224] | **YES** | ok |
| gpt-5.6-luna | -1.400 | -0.617 | **-0.783** | [-1.204,-0.364] | **YES** | ok |

## 2. Robustness: full 5-mapping x 2-correction grid

Total cells = 5 mappings x 2 corrections x 3 models = 30.
NOT REPORTABLE (gated cell consumed): **0 of 30**. Reportable: **30**.
Of reportable cells, increment 95% CI excludes zero: **21 of 30** (21 negative, 0 positive).

| mapping | corr | model | delta_c(ESC) | delta_c(NONE_IDX) | increment | 95% CI | excl.0 | status |
|---|---|---|---|---|---|---|---|---|
| M1 | clamp | gemini-3.7-flash | -0.630 | -0.445 | -0.185  | [-0.495,+0.107] | no | ok |
| M1 | clamp | gemini-3.1-pro-preview | -0.728 | -0.669 | -0.059  | [-0.335,+0.294] | no | ok |
| M1 | clamp | gpt-5.6-luna | -1.195 | -0.385 | -0.810* | [-1.168,-0.400] | yes | ok |
| M1 | loglinear | gemini-3.7-flash | -0.565 | -0.402 | -0.163  | [-0.465,+0.101] | no | ok |
| M1 | loglinear | gemini-3.1-pro-preview | -0.722 | -0.769 | +0.048  | [-0.328,+0.344] | no | ok |
| M1 | loglinear | gpt-5.6-luna | -1.248 | -0.378 | -0.870* | [-1.194,-0.398] | yes | ok |
| M2 | clamp | gemini-3.7-flash | -0.578 | -0.208 | -0.370* | [-0.616,-0.152] | yes | ok |
| M2 | clamp | gemini-3.1-pro-preview | -1.369 | -1.003 | -0.366* | [-0.527,-0.238] | yes | ok |
| M2 | clamp | gpt-5.6-luna | -1.636 | -0.816 | -0.820* | [-1.195,-0.544] | yes | ok |
| M2 | loglinear | gemini-3.7-flash | -0.548 | -0.203 | -0.344* | [-0.602,-0.145] | yes | ok |
| M2 | loglinear | gemini-3.1-pro-preview | -1.345 | -0.984 | -0.360* | [-0.517,-0.234] | yes | ok |
| M2 | loglinear | gpt-5.6-luna | -1.636 | -0.837 | -0.799* | [-1.141,-0.536] | yes | ok |
| M3 | clamp | gemini-3.7-flash | -0.681 | -0.480 | -0.201  | [-0.490,+0.060] | no | ok |
| M3 | clamp | gemini-3.1-pro-preview | -0.653 | -0.629 | -0.024  | [-0.234,+0.308] | no | ok |
| M3 | clamp | gpt-5.6-luna | -1.160 | -0.389 | -0.770* | [-1.118,-0.369] | yes | ok |
| M3 | loglinear | gemini-3.7-flash | -0.635 | -0.439 | -0.196  | [-0.461,+0.048] | no | ok |
| M3 | loglinear | gemini-3.1-pro-preview | -0.649 | -0.730 | +0.081  | [-0.233,+0.354] | no | ok |
| M3 | loglinear | gpt-5.6-luna | -1.214 | -0.382 | -0.831* | [-1.145,-0.367] | yes | ok |
| M4 | clamp | gemini-3.7-flash | -0.607 | -0.342 | -0.265* | [-0.483,-0.093] | yes | ok |
| M4 | clamp | gemini-3.1-pro-preview | -1.209 | -0.809 | -0.400* | [-0.630,-0.230] | yes | ok |
| M4 | clamp | gpt-5.6-luna | -1.383 | -0.533 | -0.850* | [-1.191,-0.363] | yes | ok |
| M4 | loglinear | gemini-3.7-flash | -0.589 | -0.332 | -0.257* | [-0.462,-0.091] | yes | ok |
| M4 | loglinear | gemini-3.1-pro-preview | -1.163 | -0.774 | -0.388* | [-0.599,-0.224] | yes | ok |
| M4 | loglinear | gpt-5.6-luna | -1.400 | -0.617 | -0.783* | [-1.204,-0.364] | yes | ok |
| M5 | clamp | gemini-3.7-flash | -0.565 | -0.343 | -0.222* | [-0.453,-0.005] | yes | ok |
| M5 | clamp | gemini-3.1-pro-preview | -1.282 | -0.825 | -0.457* | [-0.715,-0.264] | yes | ok |
| M5 | clamp | gpt-5.6-luna | -1.408 | -0.529 | -0.879* | [-1.227,-0.388] | yes | ok |
| M5 | loglinear | gemini-3.7-flash | -0.530 | -0.331 | -0.199  | [-0.438,+0.000] | no | ok |
| M5 | loglinear | gemini-3.1-pro-preview | -1.232 | -0.789 | -0.443* | [-0.682,-0.256] | yes | ok |
| M5 | loglinear | gpt-5.6-luna | -1.425 | -0.613 | -0.812* | [-1.239,-0.390] | yes | ok |

### Per-model summary

| model | cells | reportable | excludes 0 | negative | positive | all reportable points negative? |
|---|---|---|---|---|---|---|
| gemini-3.7-flash | 10 | 10 | 5 | 5 | 0 | True |
| gemini-3.1-pro-preview | 10 | 10 | 6 | 6 | 0 | False |
| gpt-5.6-luna | 10 | 10 | 10 | 10 | 0 | True |

Pooled directionality across all 30 computable points (reportable and gated cells alike, point estimate only): 28 negative, 2 positive. All reportable-and-significant cells negative: **False**.

## 3. Raw-rate version: INFEASIBLE escalation rate, ESCALATE - NONE_INDEX

Paired cluster bootstrap (same shared resample machinery) on the raw rate difference, not a
criterion. Reference point-estimates supplied in the task brief are reproduced from file.

| model | ESCALATE rate (k/n) | NONE_INDEX rate (k/n) | risk diff | 95% CI | excludes 0? |
|---|---|---|---|---|---|
| gemini-3.7-flash | 0.989 (186/188) | 0.973 (183/188) | +0.016 | [+0.000,+0.036] | no |
| gemini-3.1-pro-preview | 0.903 (168/186) | 0.804 (148/184) | +0.099 | [+0.042,+0.160] | **YES** |
| gpt-5.6-luna | 0.548 (103/188) | 0.213 (40/188) | +0.335 | [+0.253,+0.419] | **YES** |

## 4. Verdict

**The framing increment EXCLUDES ZERO for all three models under the primary M4+loglinear spec, and is negative in every reportable cell of the full 5x2 grid where it excludes zero (21/30 reportable grid cells). Ling et al.'s null of wording-irrelevance FAILS to hold in this agentic escalation setting: naming a human operator / multi-action planner shifts the criterion measurably beyond what a bare in-schema NONE affordance already produces. This is the joint effect of the two-edit bundle described in the caveat above, not an isolated word-choice effect.**

