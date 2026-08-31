# v2b analysis — de-confounding the power-grid placebo and affordance results

seed=20260827 | bootstrap B=20,000 | cluster = (case, item_id), n_clusters=40 | gate = 0.05
Models: gemini-3.7-flash, gemini-3.1-pro-preview. New arms from harness_v2b.py: PLACEBO_NONE, NONE_INDEX.

**Design.** PLACEBO_NONE = PLACEBO's decoy option, PLUS the byte-identical NONE-permission 
sentence from NO_ESCAPE (fixes the 'two edits at once' confound in the original PLACEBO arm). 
NONE_INDEX = ESCALATE's tail/index-based response format, but the menu option carries ONLY 
ESCALATE's bare assertion with the human-escalation clause and the word ESCALATE removed 
(fixes the index-vs-string response-format confound between ESCALATE and NO_ESCAPE).

## 0. Unparsed-rate gate check, all 5 arms x 2 models x 3 labels

| model | arm | label | n | unparsed | rate | status |
|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE | EASY | 17 | 0 | 0.000 | ok |
| gemini-3.7-flash | NO_ESCAPE | TRICKY | 58 | 0 | 0.000 | ok |
| gemini-3.7-flash | NO_ESCAPE | INFEASIBLE | 188 | 0 | 0.000 | ok |
| gemini-3.7-flash | ESCALATE | EASY | 17 | 0 | 0.000 | ok |
| gemini-3.7-flash | ESCALATE | TRICKY | 58 | 0 | 0.000 | ok |
| gemini-3.7-flash | ESCALATE | INFEASIBLE | 188 | 0 | 0.000 | ok |
| gemini-3.7-flash | PLACEBO | EASY | 17 | 0 | 0.000 | ok |
| gemini-3.7-flash | PLACEBO | TRICKY | 58 | 0 | 0.000 | ok |
| gemini-3.7-flash | PLACEBO | INFEASIBLE | 188 | 0 | 0.000 | ok |
| gemini-3.7-flash | PLACEBO_NONE | EASY | 17 | 0 | 0.000 | ok |
| gemini-3.7-flash | PLACEBO_NONE | TRICKY | 58 | 0 | 0.000 | ok |
| gemini-3.7-flash | PLACEBO_NONE | INFEASIBLE | 188 | 0 | 0.000 | ok |
| gemini-3.7-flash | NONE_INDEX | EASY | 17 | 0 | 0.000 | ok |
| gemini-3.7-flash | NONE_INDEX | TRICKY | 58 | 0 | 0.000 | ok |
| gemini-3.7-flash | NONE_INDEX | INFEASIBLE | 188 | 0 | 0.000 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | EASY | 17 | 0 | 0.000 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | TRICKY | 58 | 1 | 0.017 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | INFEASIBLE | 188 | 3 | 0.016 | ok |
| gemini-3.1-pro-preview | ESCALATE | EASY | 17 | 0 | 0.000 | ok |
| gemini-3.1-pro-preview | ESCALATE | TRICKY | 58 | 0 | 0.000 | ok |
| gemini-3.1-pro-preview | ESCALATE | INFEASIBLE | 188 | 2 | 0.011 | ok |
| gemini-3.1-pro-preview | PLACEBO | EASY | 17 | 1 | 0.059 | **GATED** |
| gemini-3.1-pro-preview | PLACEBO | TRICKY | 58 | 3 | 0.052 | **GATED** |
| gemini-3.1-pro-preview | PLACEBO | INFEASIBLE | 188 | 7 | 0.037 | ok |
| gemini-3.1-pro-preview | PLACEBO_NONE | EASY | 17 | 0 | 0.000 | ok |
| gemini-3.1-pro-preview | PLACEBO_NONE | TRICKY | 58 | 1 | 0.017 | ok |
| gemini-3.1-pro-preview | PLACEBO_NONE | INFEASIBLE | 188 | 3 | 0.016 | ok |
| gemini-3.1-pro-preview | NONE_INDEX | EASY | 17 | 0 | 0.000 | ok |
| gemini-3.1-pro-preview | NONE_INDEX | TRICKY | 58 | 2 | 0.034 | ok |
| gemini-3.1-pro-preview | NONE_INDEX | INFEASIBLE | 188 | 4 | 0.021 | ok |

Gated cells: [('gemini-3.1-pro-preview', 'PLACEBO', 'EASY'), ('gemini-3.1-pro-preview', 'PLACEBO', 'TRICKY')].

## A. PLACEBO_NONE vs NO_ESCAPE — does placebo suppression survive with permission restored?

Old confounded PLACEBO arm (menu decoy present, NO permission sentence), INFEASIBLE label:
- gemini-3.7-flash: PLACEBO 0.346 vs NO_ESCAPE 0.968
- gemini-3.1-pro-preview: PLACEBO 0.000 vs NO_ESCAPE 0.438

New PLACEBO_NONE arm (same decoy, PLUS permission sentence) vs NO_ESCAPE, all labels:

| model | label | PLACEBO_NONE rate k/n | NO_ESCAPE rate k/n | risk diff | 95% CI | Fisher p | placebo-take rate | status |
|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | EASY | 0.176 (3/17) | 0.118 (2/17) | +0.059  | [+0.000,+0.200] | 1 | 0.000 | ok |
| gemini-3.7-flash | TRICKY | 0.621 (36/58) | 0.569 (33/58) | +0.052  | [-0.031,+0.148] | 0.705 | 0.000 | ok |
| gemini-3.7-flash | INFEASIBLE | 0.957 (180/188) | 0.968 (182/188) | -0.011  | [-0.038,+0.011] | 0.787 | 0.016 | ok |
| gemini-3.1-pro-preview | EASY | 0.000 (0/17) | 0.000 (0/17) | +0.000  | [+0.000,+0.000] | 1 | 0.000 | ok |
| gemini-3.1-pro-preview | TRICKY | 0.158 (9/57) | 0.105 (6/57) | +0.053  | [-0.056,+0.165] | 0.581 | 0.175 | ok |
| gemini-3.1-pro-preview | INFEASIBLE | 0.438 (81/185) | 0.438 (81/185) | +0.000  | [-0.076,+0.073] | 1 | 0.216 | ok |

Direct old-vs-new INFEASIBLE comparison:

| model | old PLACEBO rate | new PLACEBO_NONE rate | shift | interpretation |
|---|---|---|---|---|
| gemini-3.7-flash | 0.346 | 0.957 | +0.611 | suppression weaker once permission restored |
| gemini-3.1-pro-preview | 0.000 | 0.438 | +0.438 | suppression weaker once permission restored |

## B. NONE_INDEX vs NO_ESCAPE — does the criterion shift survive without escalation language?

Reference: original ESCALATE vs NO_ESCAPE, M4+loglinear (the paper's primary spec):
- gemini-3.7-flash: delta c = -0.589 [-0.87,-0.37], delta d' = -0.143 [-0.64,+0.34]
- gemini-3.1-pro-preview: delta c = -1.163 [-1.59,-0.88], delta d' = +0.283 [-0.54,+0.86]

### Primary spec: M4 + loglinear

| model | d'(NO_ESC) | d'(NONE_INDEX) | delta d' | 95% CI | c(NO_ESC) | c(NONE_INDEX) | delta c | 95% CI | status |
|---|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash |  1.713 |  1.202 | -0.511 | [-0.97,-0.14] | -0.413 | -0.745 | -0.332 | [-0.56,-0.15] | ok |
| gemini-3.1-pro-preview |  1.155 |  1.561 | +0.406 | [-0.29,+0.89] |  0.888 |  0.113 | -0.774 | [-1.16,-0.51] | ok |

### Full 5-mapping x 2-correction grid

| mapping | model | corr | delta d' | 95% CI | delta c | 95% CI | status |
|---|---|---|---|---|---|---|---|
| M1 | gemini-3.7-flash | clamp | -0.729  | [-1.63,+0.00] | -0.445* | [-0.86,-0.12] | ok |
| M1 | gemini-3.7-flash | loglinear | -0.655  | [-1.60,+0.00] | -0.402* | [-0.83,-0.11] | ok |
| M1 | gemini-3.1-pro-preview | clamp | +0.689  | [-0.10,+1.25] | -0.669* | [-1.03,-0.42] | ok |
| M1 | gemini-3.1-pro-preview | loglinear | +0.475  | [-0.20,+1.25] | -0.769* | [-1.07,-0.42] | ok |
| M2 | gemini-3.7-flash | clamp | -0.257  | [-0.63,+0.14] | -0.208* | [-0.42,-0.04] | ok |
| M2 | gemini-3.7-flash | loglinear | -0.258  | [-0.61,+0.11] | -0.203* | [-0.40,-0.05] | ok |
| M2 | gemini-3.1-pro-preview | clamp | +0.022  | [-0.57,+0.47] | -1.003* | [-1.30,-0.77] | ok |
| M2 | gemini-3.1-pro-preview | loglinear | +0.045  | [-0.49,+0.48] | -0.984* | [-1.26,-0.76] | ok |
| M3 | gemini-3.7-flash | clamp | -0.659* | [-1.46,-0.04] | -0.480* | [-0.89,-0.16] | ok |
| M3 | gemini-3.7-flash | loglinear | -0.582* | [-1.44,-0.02] | -0.439* | [-0.87,-0.15] | ok |
| M3 | gemini-3.1-pro-preview | clamp | +0.608  | [-0.19,+1.13] | -0.629* | [-0.96,-0.41] | ok |
| M3 | gemini-3.1-pro-preview | loglinear | +0.397  | [-0.28,+1.12] | -0.730* | [-1.00,-0.40] | ok |
| M4 | gemini-3.7-flash | clamp | -0.528* | [-1.00,-0.15] | -0.342* | [-0.58,-0.15] | ok |
| M4 | gemini-3.7-flash | loglinear | -0.511* | [-0.97,-0.14] | -0.332* | [-0.56,-0.15] | ok |
| M4 | gemini-3.1-pro-preview | clamp | +0.346  | [-0.29,+0.88] | -0.809* | [-1.16,-0.52] | ok |
| M4 | gemini-3.1-pro-preview | loglinear | +0.406  | [-0.29,+0.89] | -0.774* | [-1.16,-0.51] | ok |
| M5 | gemini-3.7-flash | clamp | -0.526* | [-1.10,-0.02] | -0.343* | [-0.62,-0.13] | ok |
| M5 | gemini-3.7-flash | loglinear | -0.513* | [-1.05,-0.03] | -0.331* | [-0.59,-0.13] | ok |
| M5 | gemini-3.1-pro-preview | clamp | +0.378  | [-0.25,+0.93] | -0.825* | [-1.20,-0.53] | ok |
| M5 | gemini-3.1-pro-preview | loglinear | +0.435  | [-0.26,+0.94] | -0.789* | [-1.19,-0.52] | ok |

Total cells = 20; NOT REPORTABLE (gated) = 0; reportable = 20.
delta c CI excludes 0: 20 of 20 reportable cells.
delta d' CI excludes 0: 6 of 20 reportable cells.

## C. NONE_INDEX esc_channel split (index vs string)

| model | label | n parsed | n escalated | via index | via string | via other |
|---|---|---|---|---|---|---|
| gemini-3.7-flash | EASY | 17 | 6 | 5 | 1 | 0 |
| gemini-3.7-flash | TRICKY | 58 | 39 | 37 | 2 | 0 |
| gemini-3.7-flash | INFEASIBLE | 188 | 183 | 173 | 10 | 0 |
| gemini-3.7-flash | ALL | 263 | 228 | 215 | 13 | 0 |
| gemini-3.1-pro-preview | EASY | 17 | 1 | 1 | 0 | 0 |
| gemini-3.1-pro-preview | TRICKY | 56 | 24 | 15 | 9 | 0 |
| gemini-3.1-pro-preview | INFEASIBLE | 184 | 148 | 99 | 49 | 0 |
| gemini-3.1-pro-preview | ALL | 257 | 173 | 115 | 58 | 0 |

