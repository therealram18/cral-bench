# v2 SDT analysis — power-grid escalation benchmark

seed=20260827 | bootstrap B=20,000 | cluster = (case, item_id), n_clusters=40 | gate = 0.05

**Truncation handling, stated once and applied everywhere:** every rate, every SDT count and
every bootstrap in this document is **parsed-only by construction**. An unparsed/truncated row
is a MISSING response and is excluded from both numerator and denominator; it is never scored
as a non-escalation. Any (model, arm, label) cell whose unparsed rate exceeds 5% is flagged
NOT REPORTABLE and any SDT mapping that consumes such a cell is flagged NOT REPORTABLE too.

Item ledger: {'TRICKY': 58, 'EASY': 17, 'INFEASIBLE': 188}; TRICKY single-certifying-action split {'drastic': 41, 'benign': 17} (DRASTIC = shed / open_line, per mint_easy.py taxonomy).

## Executive summary

1. **Verification.** All 27 (model x arm x label) escalation rates, unparsed counts and gate flags reproduce `v2_runs.log` exactly: MATCH.

2. **Criterion shift is the robust result.** delta c = c(ESCALATE) - c(NO_ESCAPE) is negative in 20/20 reportable cells and its 95% paired cluster-bootstrap CI excludes zero in **20 of 20** reportable cells (30 total, 10 NOT REPORTABLE because the mapping consumes a gated cell). Naming the escalate option lowers the abstention criterion under every mapping, every rate correction, every non-gated model.

3. **Discrimination does NOT collapse — and where it moves, it moves the other way.** delta d' has a CI excluding zero in only **4 of 20** reportable cells, and **all 4 of them are POSITIVE** (gemini-3.1-pro-preview, M1 and M3, both corrections: +1.31 to +1.46); 0 cell anywhere is significantly negative. The pre-rebuild claim 'naming the option destroys discrimination' is **not supported by v2 data** and its sign is reversed for the pro tier.

4. **Placebo suppression holds on INFEASIBLE for all three models** and is the largest effect in the pack: PLACEBO vs NO_ESCAPE risk difference -0.622 / -0.412 / -0.438 (3.7-flash / 3.5-flash / pro), Fisher p = 7e-42 / 1.3e-26 / 1.5e-29.

5. **The README's c-c* numbers are NOT M1+clamp.** Under M1+clamp only 1 of the 9 published numbers reproduces; under **M2 (noise = EASY+TRICKY) + loglinear + parsed-only, 8 of 9 reproduce** to the printed precision. The README's stated formula c* = -logit(pi)/d' is correct; the mapping and correction behind those numbers are undocumented and are M2 + loglinear, which contradicts the M1 status quo described in signal_noise_sensitivity.py.

6. **gemini-3.5-flash contributes no reportable SDT delta at all.** Its NO_ESCAPE arm has EASY at 0.118 and TRICKY at 0.052 unparsed, both above the 5% gate, and every mapping M1-M5 needs EASY. All 10 of its delta cells are NOT REPORTABLE. Its NO_ESCAPE arm must be re-run before any SDT number for that model can be published.


## 1. Escalation rates per model x arm x label, and verification against v2_runs.log

| model | arm | label | n | unparsed | unp.rate | n parsed | esc rate | gate | log esc | log unp | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE | EASY | 17 | 0 | 0.000 | 17 | 0.118 | ok | 0.118 | 0.000 | MATCH |
| gemini-3.7-flash | NO_ESCAPE | TRICKY | 58 | 0 | 0.000 | 58 | 0.569 | ok | 0.569 | 0.000 | MATCH |
| gemini-3.7-flash | NO_ESCAPE | INFEASIBLE | 188 | 0 | 0.000 | 188 | 0.968 | ok | 0.968 | 0.000 | MATCH |
| gemini-3.7-flash | ESCALATE | EASY | 17 | 0 | 0.000 | 17 | 0.353 | ok | 0.353 | 0.000 | MATCH |
| gemini-3.7-flash | ESCALATE | TRICKY | 58 | 0 | 0.000 | 58 | 0.845 | ok | 0.845 | 0.000 | MATCH |
| gemini-3.7-flash | ESCALATE | INFEASIBLE | 188 | 0 | 0.000 | 188 | 0.989 | ok | 0.989 | 0.000 | MATCH |
| gemini-3.7-flash | PLACEBO | EASY | 17 | 0 | 0.000 | 17 | 0.000 | ok | 0.000 | 0.000 | MATCH |
| gemini-3.7-flash | PLACEBO | TRICKY | 58 | 0 | 0.000 | 58 | 0.121 | ok | 0.121 | 0.000 | MATCH |
| gemini-3.7-flash | PLACEBO | INFEASIBLE | 188 | 0 | 0.000 | 188 | 0.346 | ok | 0.346 | 0.000 | MATCH |
| gemini-3.5-flash | NO_ESCAPE | EASY | 17 | 2 | 0.118 | 15 | 0.000 | **NOT REPORTABLE** | 0.000 | 0.118 | MATCH |
| gemini-3.5-flash | NO_ESCAPE | TRICKY | 58 | 3 | 0.052 | 55 | 0.055 | **NOT REPORTABLE** | 0.055 | 0.052 | MATCH |
| gemini-3.5-flash | NO_ESCAPE | INFEASIBLE | 188 | 1 | 0.005 | 187 | 0.417 | ok | 0.417 | 0.005 | MATCH |
| gemini-3.5-flash | ESCALATE | EASY | 17 | 0 | 0.000 | 17 | 0.118 | ok | 0.118 | 0.000 | MATCH |
| gemini-3.5-flash | ESCALATE | TRICKY | 58 | 0 | 0.000 | 58 | 0.569 | ok | 0.569 | 0.000 | MATCH |
| gemini-3.5-flash | ESCALATE | INFEASIBLE | 188 | 0 | 0.000 | 188 | 0.899 | ok | 0.899 | 0.000 | MATCH |
| gemini-3.5-flash | PLACEBO | EASY | 17 | 0 | 0.000 | 17 | 0.000 | ok | 0.000 | 0.000 | MATCH |
| gemini-3.5-flash | PLACEBO | TRICKY | 58 | 1 | 0.017 | 57 | 0.000 | ok | 0.000 | 0.017 | MATCH |
| gemini-3.5-flash | PLACEBO | INFEASIBLE | 188 | 3 | 0.016 | 185 | 0.005 | ok | 0.005 | 0.016 | MATCH |
| gemini-3.1-pro-preview | NO_ESCAPE | EASY | 17 | 0 | 0.000 | 17 | 0.000 | ok | 0.000 | 0.000 | MATCH |
| gemini-3.1-pro-preview | NO_ESCAPE | TRICKY | 58 | 1 | 0.017 | 57 | 0.105 | ok | 0.105 | 0.017 | MATCH |
| gemini-3.1-pro-preview | NO_ESCAPE | INFEASIBLE | 188 | 3 | 0.016 | 185 | 0.438 | ok | 0.438 | 0.016 | MATCH |
| gemini-3.1-pro-preview | ESCALATE | EASY | 17 | 0 | 0.000 | 17 | 0.000 | ok | 0.000 | 0.000 | MATCH |
| gemini-3.1-pro-preview | ESCALATE | TRICKY | 58 | 0 | 0.000 | 58 | 0.586 | ok | 0.586 | 0.000 | MATCH |
| gemini-3.1-pro-preview | ESCALATE | INFEASIBLE | 188 | 2 | 0.011 | 186 | 0.903 | ok | 0.903 | 0.011 | MATCH |
| gemini-3.1-pro-preview | PLACEBO | EASY | 17 | 1 | 0.059 | 16 | 0.000 | **NOT REPORTABLE** | 0.000 | 0.059 | MATCH |
| gemini-3.1-pro-preview | PLACEBO | TRICKY | 58 | 3 | 0.052 | 55 | 0.000 | **NOT REPORTABLE** | 0.000 | 0.052 | MATCH |
| gemini-3.1-pro-preview | PLACEBO | INFEASIBLE | 188 | 7 | 0.037 | 181 | 0.000 | ok | 0.000 | 0.037 | MATCH |

**Verification result: ALL 27 CELLS MATCH v2_runs.log EXACTLY** (escalation rate to 3 dp, unparsed count, parsed n, and gate flag).

Gated cells (unparsed > 5%, NOT REPORTABLE): gemini-3.5-flash/NO_ESCAPE/EASY (0.118), gemini-3.5-flash/NO_ESCAPE/TRICKY (0.052), gemini-3.1-pro-preview/PLACEBO/EASY (0.059), gemini-3.1-pro-preview/PLACEBO/TRICKY (0.052)

## 2. SDT levels per model x arm x mapping x rate correction (parsed-only)

d' = z(H) - z(F); c = -0.5*(z(H)+z(F)). H = P(escalate | signal), F = P(escalate | noise).

### M1 — S=INF  N=EASY  (TRICKY dropped)

| model | arm | corr | nS | nN | hit | FA | d' | c | status |
|---|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE | clamp | 188 | 17 |  0.968 |  0.118 |  3.040 | -0.333 | ok |
| gemini-3.7-flash | NO_ESCAPE | loglinear | 188 | 17 |  0.968 |  0.118 |  2.905 | -0.367 | ok |
| gemini-3.7-flash | ESCALATE | clamp | 188 | 17 |  0.989 |  0.353 |  2.680 | -0.963 | ok |
| gemini-3.7-flash | ESCALATE | loglinear | 188 | 17 |  0.989 |  0.353 |  2.575 | -0.932 | ok |
| gemini-3.5-flash | NO_ESCAPE | clamp | 187 | 15 |  0.417 |  0.000 |  1.625 |  1.022 | **NOT REPORTABLE** (gated: EASY) |
| gemini-3.5-flash | NO_ESCAPE | loglinear | 187 | 15 |  0.417 |  0.000 |  1.655 |  1.035 | **NOT REPORTABLE** (gated: EASY) |
| gemini-3.5-flash | ESCALATE | clamp | 188 | 17 |  0.899 |  0.118 |  2.462 | -0.044 | ok |
| gemini-3.5-flash | ESCALATE | loglinear | 188 | 17 |  0.899 |  0.118 |  2.349 | -0.089 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | clamp | 185 | 17 |  0.438 |  0.000 |  1.733 |  1.023 | rate at floor/ceiling — d' rests on the correction |
| gemini-3.1-pro-preview | NO_ESCAPE | loglinear | 185 | 17 |  0.438 |  0.000 |  1.759 |  1.035 | rate at floor/ceiling — d' rests on the correction |
| gemini-3.1-pro-preview | ESCALATE | clamp | 186 | 17 |  0.903 |  0.000 |  3.190 |  0.295 | rate at floor/ceiling — d' rests on the correction |
| gemini-3.1-pro-preview | ESCALATE | loglinear | 186 | 17 |  0.903 |  0.000 |  3.202 |  0.313 | rate at floor/ceiling — d' rests on the correction |

### M2 — S=INF  N=EASY+TRICKY

| model | arm | corr | nS | nN | hit | FA | d' | c | status |
|---|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE | clamp | 188 | 75 |  0.968 |  0.467 |  1.937 | -0.885 | ok |
| gemini-3.7-flash | NO_ESCAPE | loglinear | 188 | 75 |  0.968 |  0.467 |  1.902 | -0.869 | ok |
| gemini-3.7-flash | ESCALATE | clamp | 188 | 75 |  0.989 |  0.733 |  1.680 | -1.463 | ok |
| gemini-3.7-flash | ESCALATE | loglinear | 188 | 75 |  0.989 |  0.733 |  1.606 | -1.417 | ok |
| gemini-3.5-flash | NO_ESCAPE | clamp | 187 | 70 |  0.417 |  0.043 |  1.509 |  0.964 | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| gemini-3.5-flash | NO_ESCAPE | loglinear | 187 | 70 |  0.417 |  0.043 |  1.444 |  0.930 | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| gemini-3.5-flash | ESCALATE | clamp | 188 | 75 |  0.899 |  0.467 |  1.359 | -0.596 | ok |
| gemini-3.5-flash | ESCALATE | loglinear | 188 | 75 |  0.899 |  0.467 |  1.346 | -0.591 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | clamp | 185 | 74 |  0.438 |  0.081 |  1.241 |  0.777 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | loglinear | 185 | 74 |  0.438 |  0.081 |  1.206 |  0.759 | ok |
| gemini-3.1-pro-preview | ESCALATE | clamp | 186 | 75 |  0.903 |  0.453 |  1.417 | -0.591 | ok |
| gemini-3.1-pro-preview | ESCALATE | loglinear | 186 | 75 |  0.903 |  0.453 |  1.403 | -0.586 | ok |

### M3 — S=INF+TRICKY  N=EASY

| model | arm | corr | nS | nN | hit | FA | d' | c | status |
|---|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE | clamp | 246 | 17 |  0.874 |  0.118 |  2.332 |  0.021 | ok |
| gemini-3.7-flash | NO_ESCAPE | loglinear | 246 | 17 |  0.874 |  0.118 |  2.223 | -0.026 | ok |
| gemini-3.7-flash | ESCALATE | clamp | 246 | 17 |  0.955 |  0.353 |  2.076 | -0.661 | ok |
| gemini-3.7-flash | ESCALATE | loglinear | 246 | 17 |  0.955 |  0.353 |  2.035 | -0.662 | ok |
| gemini-3.5-flash | NO_ESCAPE | clamp | 242 | 15 |  0.335 |  0.000 |  1.407 |  1.130 | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| gemini-3.5-flash | NO_ESCAPE | loglinear | 242 | 15 |  0.335 |  0.000 |  1.438 |  1.144 | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| gemini-3.5-flash | ESCALATE | clamp | 246 | 17 |  0.821 |  0.118 |  2.107 |  0.134 | ok |
| gemini-3.5-flash | ESCALATE | loglinear | 246 | 17 |  0.821 |  0.118 |  2.000 |  0.085 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | clamp | 242 | 17 |  0.360 |  0.000 |  1.530 |  1.125 | rate at floor/ceiling — d' rests on the correction |
| gemini-3.1-pro-preview | NO_ESCAPE | loglinear | 242 | 17 |  0.360 |  0.000 |  1.556 |  1.136 | rate at floor/ceiling — d' rests on the correction |
| gemini-3.1-pro-preview | ESCALATE | clamp | 244 | 17 |  0.828 |  0.000 |  2.835 |  0.472 | rate at floor/ceiling — d' rests on the correction |
| gemini-3.1-pro-preview | ESCALATE | loglinear | 244 | 17 |  0.828 |  0.000 |  2.855 |  0.487 | rate at floor/ceiling — d' rests on the correction |

### M4 — S=INF+TR.drastic  N=EASY+TR.benign

| model | arm | corr | nS | nN | hit | FA | d' | c | status |
|---|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE | clamp | 229 | 34 |  0.900 |  0.324 |  1.737 | -0.411 | ok |
| gemini-3.7-flash | NO_ESCAPE | loglinear | 229 | 34 |  0.900 |  0.324 |  1.713 | -0.413 | ok |
| gemini-3.7-flash | ESCALATE | clamp | 229 | 34 |  0.965 |  0.588 |  1.590 | -1.018 | ok |
| gemini-3.7-flash | ESCALATE | loglinear | 229 | 34 |  0.965 |  0.588 |  1.571 | -1.002 | ok |
| gemini-3.5-flash | NO_ESCAPE | clamp | 227 | 30 |  0.352 |  0.033 |  1.455 |  1.106 | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| gemini-3.5-flash | NO_ESCAPE | loglinear | 227 | 30 |  0.352 |  0.033 |  1.284 |  1.019 | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| gemini-3.5-flash | ESCALATE | clamp | 229 | 34 |  0.843 |  0.324 |  1.464 | -0.274 | ok |
| gemini-3.5-flash | ESCALATE | loglinear | 229 | 34 |  0.843 |  0.324 |  1.444 | -0.278 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | clamp | 225 | 34 |  0.378 |  0.059 |  1.253 |  0.938 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | loglinear | 225 | 34 |  0.378 |  0.059 |  1.155 |  0.888 | ok |
| gemini-3.1-pro-preview | ESCALATE | clamp | 227 | 34 |  0.841 |  0.324 |  1.458 | -0.271 | ok |
| gemini-3.1-pro-preview | ESCALATE | loglinear | 227 | 34 |  0.841 |  0.324 |  1.438 | -0.275 | ok |

### M5 — S=INF  N=EASY+TR.benign  (TR.drastic dropped)

| model | arm | corr | nS | nN | hit | FA | d' | c | status |
|---|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE | clamp | 188 | 34 |  0.968 |  0.324 |  2.311 | -0.698 | ok |
| gemini-3.7-flash | NO_ESCAPE | loglinear | 188 | 34 |  0.968 |  0.324 |  2.264 | -0.688 | ok |
| gemini-3.7-flash | ESCALATE | clamp | 188 | 34 |  0.989 |  0.588 |  2.080 | -1.263 | ok |
| gemini-3.7-flash | ESCALATE | loglinear | 188 | 34 |  0.989 |  0.588 |  2.003 | -1.218 | ok |
| gemini-3.5-flash | NO_ESCAPE | clamp | 187 | 30 |  0.417 |  0.033 |  1.625 |  1.022 | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| gemini-3.5-flash | NO_ESCAPE | loglinear | 187 | 30 |  0.417 |  0.033 |  1.453 |  0.934 | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| gemini-3.5-flash | ESCALATE | clamp | 188 | 34 |  0.899 |  0.324 |  1.733 | -0.409 | ok |
| gemini-3.5-flash | ESCALATE | loglinear | 188 | 34 |  0.899 |  0.324 |  1.708 | -0.410 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | clamp | 185 | 34 |  0.438 |  0.059 |  1.408 |  0.861 | ok |
| gemini-3.1-pro-preview | NO_ESCAPE | loglinear | 185 | 34 |  0.438 |  0.059 |  1.310 |  0.810 | ok |
| gemini-3.1-pro-preview | ESCALATE | clamp | 186 | 34 |  0.903 |  0.324 |  1.758 | -0.421 | ok |
| gemini-3.1-pro-preview | ESCALATE | loglinear | 186 | 34 |  0.903 |  0.324 |  1.732 | -0.422 | ok |

## 3. Delta c and delta d' (ESCALATE - NO_ESCAPE), paired cluster bootstrap

B = 20,000 resamples of the 40 (case, item_id) clusters; ONE shared resample so the two arms
are paired and the CI is on the delta itself. `*` = two-sided 95% CI excludes 0.

| mapping | model | corr | d'(NO_ESC) | d'(ESC) | delta d' | 95% CI | c(NO_ESC) | c(ESC) | delta c | 95% CI | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | gemini-3.7-flash | clamp |  3.040 |  2.680 | -0.360  | [-1.27,+0.37] | -0.333 | -0.963 | -0.630* | [-1.08,-0.29] | ok |
| M1 | gemini-3.7-flash | loglinear |  2.905 |  2.575 | -0.330  | [-1.25,+0.36] | -0.367 | -0.932 | -0.565* | [-1.06,-0.26] | ok |
| M1 | gemini-3.5-flash | clamp |  1.625 |  2.462 | +0.838  | [+0.08,+1.78] |  1.022 | -0.044 | -1.066  | [-1.39,-0.67] | **NOT REPORTABLE** (gated: EASY) |
| M1 | gemini-3.5-flash | loglinear |  1.655 |  2.349 | +0.694  | [+0.00,+1.75] |  1.035 | -0.089 | -1.125  | [-1.42,-0.67] | **NOT REPORTABLE** (gated: EASY) |
| M1 | gemini-3.1-pro-preview | clamp |  1.733 |  3.190 | +1.457* | [+1.17,+1.83] |  1.023 |  0.295 | -0.728* | [-0.91,-0.59] | ok |
| M1 | gemini-3.1-pro-preview | loglinear |  1.759 |  3.202 | +1.443* | [+1.16,+1.81] |  1.035 |  0.313 | -0.722* | [-0.90,-0.58] | ok |
| M2 | gemini-3.7-flash | clamp |  1.937 |  1.680 | -0.257  | [-0.71,+0.20] | -0.885 | -1.463 | -0.578* | [-0.84,-0.37] | ok |
| M2 | gemini-3.7-flash | loglinear |  1.902 |  1.606 | -0.297  | [-0.71,+0.18] | -0.869 | -1.417 | -0.548* | [-0.83,-0.35] | ok |
| M2 | gemini-3.5-flash | clamp |  1.509 |  1.359 | -0.150  | [-0.93,+0.43] |  0.964 | -0.596 | -1.560  | [-1.94,-1.32] | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| M2 | gemini-3.5-flash | loglinear |  1.444 |  1.346 | -0.097  | [-0.89,+0.45] |  0.930 | -0.591 | -1.520  | [-1.91,-1.29] | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| M2 | gemini-3.1-pro-preview | clamp |  1.241 |  1.417 | +0.176  | [-0.47,+0.70] |  0.777 | -0.591 | -1.369* | [-1.69,-1.15] | ok |
| M2 | gemini-3.1-pro-preview | loglinear |  1.206 |  1.403 | +0.197  | [-0.40,+0.70] |  0.759 | -0.586 | -1.345* | [-1.64,-1.13] | ok |
| M3 | gemini-3.7-flash | clamp |  2.332 |  2.076 | -0.256  | [-1.06,+0.42] |  0.021 | -0.661 | -0.681* | [-1.13,-0.34] | ok |
| M3 | gemini-3.7-flash | loglinear |  2.223 |  2.035 | -0.189  | [-1.03,+0.43] | -0.026 | -0.662 | -0.635* | [-1.11,-0.33] | ok |
| M3 | gemini-3.5-flash | clamp |  1.407 |  2.107 | +0.700  | [-0.00,+1.52] |  1.130 |  0.134 | -0.997  | [-1.32,-0.61] | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| M3 | gemini-3.5-flash | loglinear |  1.438 |  2.000 | +0.562  | [-0.07,+1.51] |  1.144 |  0.085 | -1.059  | [-1.35,-0.61] | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| M3 | gemini-3.1-pro-preview | clamp |  1.530 |  2.835 | +1.306* | [+1.12,+1.51] |  1.125 |  0.472 | -0.653* | [-0.75,-0.56] | ok |
| M3 | gemini-3.1-pro-preview | loglinear |  1.556 |  2.855 | +1.299* | [+1.12,+1.50] |  1.136 |  0.487 | -0.649* | [-0.75,-0.56] | ok |
| M4 | gemini-3.7-flash | clamp |  1.737 |  1.590 | -0.147  | [-0.67,+0.37] | -0.411 | -1.018 | -0.607* | [-0.91,-0.39] | ok |
| M4 | gemini-3.7-flash | loglinear |  1.713 |  1.571 | -0.143  | [-0.64,+0.34] | -0.413 | -1.002 | -0.589* | [-0.87,-0.37] | ok |
| M4 | gemini-3.5-flash | clamp |  1.455 |  1.464 | +0.009  | [-0.59,+0.73] |  1.106 | -0.274 | -1.380  | [-1.67,-1.04] | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| M4 | gemini-3.5-flash | loglinear |  1.284 |  1.444 | +0.160  | [-0.61,+0.79] |  1.019 | -0.278 | -1.297  | [-1.67,-1.00] | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| M4 | gemini-3.1-pro-preview | clamp |  1.253 |  1.458 | +0.205  | [-0.54,+0.82] |  0.938 | -0.271 | -1.209* | [-1.59,-0.91] | ok |
| M4 | gemini-3.1-pro-preview | loglinear |  1.155 |  1.438 | +0.283  | [-0.54,+0.86] |  0.888 | -0.275 | -1.163* | [-1.59,-0.88] | ok |
| M5 | gemini-3.7-flash | clamp |  2.311 |  2.080 | -0.231  | [-0.84,+0.32] | -0.698 | -1.263 | -0.565* | [-0.86,-0.33] | ok |
| M5 | gemini-3.7-flash | loglinear |  2.264 |  2.003 | -0.261  | [-0.82,+0.31] | -0.688 | -1.218 | -0.530* | [-0.84,-0.31] | ok |
| M5 | gemini-3.5-flash | clamp |  1.625 |  1.733 | +0.109  | [-0.53,+0.91] |  1.022 | -0.409 | -1.430  | [-1.74,-1.08] | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| M5 | gemini-3.5-flash | loglinear |  1.453 |  1.708 | +0.255  | [-0.55,+0.96] |  0.934 | -0.410 | -1.344  | [-1.74,-1.04] | **NOT REPORTABLE** (gated: EASY,TRICKY) |
| M5 | gemini-3.1-pro-preview | clamp |  1.408 |  1.758 | +0.350  | [-0.42,+1.05] |  0.861 | -0.421 | -1.282* | [-1.70,-0.96] | ok |
| M5 | gemini-3.1-pro-preview | loglinear |  1.310 |  1.732 | +0.422  | [-0.41,+1.07] |  0.810 | -0.422 | -1.232* | [-1.68,-0.94] | ok |

**Headline robustness count.** Total cells = 5 mappings x 3 models x 2 corrections = 30.
- NOT REPORTABLE (mapping consumes a gated cell): **10 of 30**.
- Reportable cells: **20**.
- delta c with 95% CI excluding zero: **20 of 20** reportable cells (20 of 30 counting gated cells in the denominator).
- delta d' with 95% CI excluding zero: **4 of 20** reportable cells.

## 4. PLACEBO arm

### 4a. Escalation and placebo-take rate by label (parsed-only)

| model | label | n parsed | esc rate | placebo-take rate | gate |
|---|---|---|---|---|---|
| gemini-3.7-flash | EASY | 17 | 0.000 | 0.000 | ok |
| gemini-3.7-flash | TRICKY | 58 | 0.121 | 0.121 | ok |
| gemini-3.7-flash | INFEASIBLE | 188 | 0.346 | 0.112 | ok |
| gemini-3.5-flash | EASY | 17 | 0.000 | 0.000 | ok |
| gemini-3.5-flash | TRICKY | 57 | 0.000 | 0.000 | ok |
| gemini-3.5-flash | INFEASIBLE | 185 | 0.005 | 0.124 | ok |
| gemini-3.1-pro-preview | EASY | 16 | 0.000 | 0.000 | **NOT REPORTABLE** |
| gemini-3.1-pro-preview | TRICKY | 55 | 0.000 | 0.127 | **NOT REPORTABLE** |
| gemini-3.1-pro-preview | INFEASIBLE | 181 | 0.000 | 0.403 | ok |

### 4b. Fisher exact, two-sided, on parsed counts; risk difference with 95% cluster bootstrap CI

**PLACEBO vs NO_ESCAPE — the suppression claim.**

| model | label | rate(arm) k/n | rate(NO_ESCAPE) k/n | risk diff | 95% CI | Fisher p | OR | status |
|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | EASY | 0.000 (0/17) | 0.118 (2/17) | -0.118  | [-0.294,+0.000] | 0.485 | 0.00 | ok |
| gemini-3.7-flash | TRICKY | 0.121 (7/58) | 0.569 (33/58) | -0.448* | [-0.547,-0.351] | 5.27e-07 | 0.10 | ok |
| gemini-3.7-flash | INFEASIBLE | 0.346 (65/188) | 0.968 (182/188) | -0.622* | [-0.703,-0.533] | 7.02e-42 | 0.02 | ok |
| gemini-3.5-flash | EASY | 0.000 (0/17) | 0.000 (0/15) | +0.000  | [+0.000,+0.000] | 1 | inf | **NOT REPORTABLE** (NO_ESCAPE:EASY) |
| gemini-3.5-flash | TRICKY | 0.000 (0/57) | 0.055 (3/55) | -0.055  | [-0.122,+0.000] | 0.115 | 0.00 | **NOT REPORTABLE** (NO_ESCAPE:TRICKY) |
| gemini-3.5-flash | INFEASIBLE | 0.005 (1/185) | 0.417 (78/187) | -0.412* | [-0.481,-0.342] | 1.26e-26 | 0.01 | ok |
| gemini-3.1-pro-preview | EASY | 0.000 (0/16) | 0.000 (0/17) | +0.000  | [+0.000,+0.000] | 1 | inf | **NOT REPORTABLE** (PLACEBO:EASY) |
| gemini-3.1-pro-preview | TRICKY | 0.000 (0/55) | 0.105 (6/57) | -0.105  | [-0.190,-0.034] | 0.0273 | 0.00 | **NOT REPORTABLE** (PLACEBO:TRICKY) |
| gemini-3.1-pro-preview | INFEASIBLE | 0.000 (0/181) | 0.438 (81/185) | -0.438* | [-0.514,-0.365] | 1.46e-29 | 0.00 | ok |

**ESCALATE vs NO_ESCAPE — the affordance claim.**

| model | label | rate(arm) k/n | rate(NO_ESCAPE) k/n | risk diff | 95% CI | Fisher p | OR | status |
|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | EASY | 0.353 (6/17) | 0.118 (2/17) | +0.235* | [+0.056,+0.455] | 0.225 | 4.09 | ok |
| gemini-3.7-flash | TRICKY | 0.845 (49/58) | 0.569 (33/58) | +0.276* | [+0.170,+0.383] | 0.00196 | 4.12 | ok |
| gemini-3.7-flash | INFEASIBLE | 0.989 (186/188) | 0.968 (182/188) | +0.021* | [+0.005,+0.044] | 0.284 | 3.07 | ok |
| gemini-3.5-flash | EASY | 0.118 (2/17) | 0.000 (0/15) | +0.118  | [+0.000,+0.294] | 0.486 | inf | **NOT REPORTABLE** (NO_ESCAPE:EASY) |
| gemini-3.5-flash | TRICKY | 0.569 (33/58) | 0.055 (3/55) | +0.514  | [+0.415,+0.618] | 1.26e-09 | 22.88 | **NOT REPORTABLE** (NO_ESCAPE:TRICKY) |
| gemini-3.5-flash | INFEASIBLE | 0.899 (169/188) | 0.417 (78/187) | +0.482* | [+0.408,+0.552] | 3.82e-24 | 12.43 | ok |
| gemini-3.1-pro-preview | EASY | 0.000 (0/17) | 0.000 (0/17) | +0.000  | [+0.000,+0.000] | 1 | inf | both arms zero — RD = 0 exactly, no test information |
| gemini-3.1-pro-preview | TRICKY | 0.586 (34/58) | 0.105 (6/57) | +0.481* | [+0.382,+0.582] | 5.1e-08 | 12.04 | ok |
| gemini-3.1-pro-preview | INFEASIBLE | 0.903 (168/186) | 0.438 (81/185) | +0.465* | [+0.388,+0.542] | 8.48e-23 | 11.98 | ok |

**Where the two inferences disagree** (bootstrap CI excludes 0 but Fisher p >= 0.05, or the reverse). Trust Fisher in these cells: the percentile cluster bootstrap is anti-conservative at tiny n or at a rate ceiling, and EASY is 17 rows spread over 17 distinct clusters:

- gemini-3.7-flash / EASY / ESCALATE vs NO_ESCAPE: RD +0.235 [+0.056,+0.455] (CI excludes 0) but Fisher p = 0.225 on 6/17 vs 2/17 — **not significant by the exact test**.
- gemini-3.7-flash / INFEASIBLE / ESCALATE vs NO_ESCAPE: RD +0.021 [+0.005,+0.044] (CI excludes 0) but Fisher p = 0.284 on 186/188 vs 182/188 — **not significant by the exact test**.

## 5. Base-rate-referenced criterion

pi = 188/263 = 0.7148 (label share of INFEASIBLE); logit(pi) = 0.9190;
formula as printed in README_POWERGRID.md: **c\* = -logit(pi)/d'**, so c\* = -0.9190/d'.

### Under M1 + clamp — **the spec named in the task brief**

| model | arm | d' | c | c* | c - c* | README | match? |
|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE (withheld) | 3.040 | -0.333 | -0.302 | **-0.031** | -0.39 | **MISMATCH** |
| gemini-3.7-flash | ESCALATE (offered) | 2.680 | -0.963 | -0.343 | **-0.620** | -0.84 | **MISMATCH** |
| gemini-3.5-flash | NO_ESCAPE (withheld) | 1.625 | +1.022 | -0.566 | **+1.587** | +1.61 | MATCH  (**gated**: EASY) |
| gemini-3.5-flash | ESCALATE (offered) | 2.462 | -0.044 | -0.373 | **+0.329** | +0.09 | **MISMATCH** |
| gemini-3.1-pro-preview | NO_ESCAPE (withheld) | 1.733 | +1.023 | -0.530 | **+1.553** | +1.52 | **MISMATCH** |
| gemini-3.1-pro-preview | ESCALATE (offered) | 3.190 | +0.295 | -0.288 | **+0.583** | +0.06 | **MISMATCH** |

Affordance sensitivity delta c = c(withheld) - c(offered), M1+clamp:
- gemini-3.7-flash: **0.630** vs README 0.55 -> **MISMATCH**
- gemini-3.5-flash: **1.066** vs README 1.52 -> **MISMATCH**
- gemini-3.1-pro-preview: **0.728** vs README 1.35 -> **MISMATCH**

### Under M2 + clamp

| model | arm | d' | c | c* | c - c* | README | match? |
|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE (withheld) | 1.937 | -0.885 | -0.474 | **-0.410** | -0.39 | MATCH |
| gemini-3.7-flash | ESCALATE (offered) | 1.680 | -1.463 | -0.547 | **-0.916** | -0.84 | **MISMATCH** |
| gemini-3.5-flash | NO_ESCAPE (withheld) | 1.509 | +0.964 | -0.609 | **+1.573** | +1.61 | **MISMATCH**  (**gated**: EASY,TRICKY) |
| gemini-3.5-flash | ESCALATE (offered) | 1.359 | -0.596 | -0.676 | **+0.080** | +0.09 | MATCH |
| gemini-3.1-pro-preview | NO_ESCAPE (withheld) | 1.241 | +0.777 | -0.740 | **+1.517** | +1.52 | MATCH |
| gemini-3.1-pro-preview | ESCALATE (offered) | 1.417 | -0.591 | -0.648 | **+0.057** | +0.06 | MATCH |

Affordance sensitivity delta c = c(withheld) - c(offered), M2+clamp:
- gemini-3.7-flash: **0.578** vs README 0.55 -> MATCH
- gemini-3.5-flash: **1.560** vs README 1.52 -> **MISMATCH**
- gemini-3.1-pro-preview: **1.369** vs README 1.35 -> MATCH

### Under M2 + loglinear — **the spec that actually reproduces the README**

| model | arm | d' | c | c* | c - c* | README | match? |
|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE (withheld) | 1.902 | -0.869 | -0.483 | **-0.386** | -0.39 | MATCH |
| gemini-3.7-flash | ESCALATE (offered) | 1.606 | -1.417 | -0.572 | **-0.844** | -0.84 | MATCH |
| gemini-3.5-flash | NO_ESCAPE (withheld) | 1.444 | +0.930 | -0.637 | **+1.567** | +1.61 | **MISMATCH**  (**gated**: EASY,TRICKY) |
| gemini-3.5-flash | ESCALATE (offered) | 1.346 | -0.591 | -0.683 | **+0.092** | +0.09 | MATCH |
| gemini-3.1-pro-preview | NO_ESCAPE (withheld) | 1.206 | +0.759 | -0.762 | **+1.521** | +1.52 | MATCH |
| gemini-3.1-pro-preview | ESCALATE (offered) | 1.403 | -0.586 | -0.655 | **+0.069** | +0.06 | MATCH |

Affordance sensitivity delta c = c(withheld) - c(offered), M2+loglinear:
- gemini-3.7-flash: **0.548** vs README 0.55 -> MATCH
- gemini-3.5-flash: **1.520** vs README 1.52 -> MATCH
- gemini-3.1-pro-preview: **1.345** vs README 1.35 -> MATCH

### Which analysis spec did the README actually use?

Sweep of all 20 (mapping x correction x truncation-rule) specs against the 9 numbers
the README prints (6 c-c* + 3 delta c), tolerance +/-0.03. Top rows:

| mapping | correction | rows | README numbers reproduced |
|---|---|---|---|
| M2 | loglinear | parsed-only | **8 of 9** |
| M2 | loglinear | all-rows (unparsed=non-escalation) | **7 of 9** |
| M2 | clamp | parsed-only | **6 of 9** |
| M2 | clamp | all-rows (unparsed=non-escalation) | **6 of 9** |
| M5 | clamp | parsed-only | **4 of 9** |
| M5 | clamp | all-rows (unparsed=non-escalation) | **4 of 9** |

- M1 / clamp / parsed-only: **1 of 9**.
- M1 / clamp / all-rows (unparsed=non-escalation): **1 of 9**.

## 6. Pre-rebuild vs v2, the two flash models

Old files ladder_llm_<model>_<arm>.jsonl. Old-file parsed flag = (raw_choice is not None),
the same rule signal_noise_sensitivity.py applies to those files.

| model | arm | label | pre-rebuild rate (n) | v2 rate (n) | delta | pre unparsed | v2 unparsed |
|---|---|---|---|---|---|---|---|
| gemini-3.5-flash | NO_ESCAPE | EASY | 0.118 (17) | 0.000 (15) | -0.118 | 0.000 | 0.118 GATED |
| gemini-3.5-flash | NO_ESCAPE | TRICKY | 0.241 (58) | 0.055 (55) | -0.187 | 0.000 | 0.052 GATED |
| gemini-3.5-flash | NO_ESCAPE | INFEASIBLE | 0.660 (188) | 0.417 (187) | -0.242 | 0.000 | 0.005 |
| gemini-3.5-flash | ESCALATE | EASY | 0.941 (17) | 0.118 (17) | -0.824 | 0.000 | 0.000 |
| gemini-3.5-flash | ESCALATE | TRICKY | 0.948 (58) | 0.569 (58) | -0.379 | 0.000 | 0.000 |
| gemini-3.5-flash | ESCALATE | INFEASIBLE | 0.979 (188) | 0.899 (188) | -0.080 | 0.000 | 0.000 |
| gemini-3.7-flash | NO_ESCAPE | EASY | 0.200 (15) | 0.118 (17) | -0.082 | 0.118 GATED | 0.000 |
| gemini-3.7-flash | NO_ESCAPE | TRICKY | 0.686 (51) | 0.569 (58) | -0.117 | 0.121 GATED | 0.000 |
| gemini-3.7-flash | NO_ESCAPE | INFEASIBLE | 0.979 (188) | 0.968 (188) | -0.011 | 0.000 | 0.000 |
| gemini-3.7-flash | ESCALATE | EASY | 0.800 (15) | 0.353 (17) | -0.447 | 0.118 GATED | 0.000 |
| gemini-3.7-flash | ESCALATE | TRICKY | 0.948 (58) | 0.845 (58) | -0.103 | 0.000 | 0.000 |
| gemini-3.7-flash | ESCALATE | INFEASIBLE | 1.000 (188) | 0.989 (188) | -0.011 | 0.000 | 0.000 |

**Did conclusions move?** The arm effect is ESCALATE minus NO_ESCAPE on the same label.

- gemini-3.5-flash / EASY: arm effect pre-rebuild **+0.824** -> v2 **+0.118** (same sign; |change| = 0.706).
- gemini-3.5-flash / TRICKY: arm effect pre-rebuild **+0.707** -> v2 **+0.514** (same sign; |change| = 0.192).
- gemini-3.5-flash / INFEASIBLE: arm effect pre-rebuild **+0.319** -> v2 **+0.482** (same sign; |change| = 0.163).
- gemini-3.7-flash / EASY: arm effect pre-rebuild **+0.600** -> v2 **+0.235** (same sign; |change| = 0.365).
- gemini-3.7-flash / TRICKY: arm effect pre-rebuild **+0.262** -> v2 **+0.276** (same sign; |change| = 0.014).
- gemini-3.7-flash / INFEASIBLE: arm effect pre-rebuild **+0.021** -> v2 **+0.021** (same sign; |change| = 0.000).

Reading: every v2 escalation rate is LOWER than its pre-rebuild counterpart on every label and
both arms (12/12 deltas negative), and the collapse is largest exactly where the pre-rebuild
instrument was most permissive — gemini-3.5-flash ESCALATE on EASY fell 0.941 -> 0.118. The
pre-rebuild ESCALATE arm escalated on ~95% of EVERYTHING including certified-easy items, so it
could not discriminate at all; v2 restores a graded response. The DIRECTION of the affordance
effect (ESCALATE > NO_ESCAPE) survives on every label of both models, but its MAGNITUDE is not
comparable across the rebuild, and the pre-rebuild 3.7-flash NO_ESCAPE / ESCALATE EASY+TRICKY
cells were themselves above the 5% unparsed gate. Pre-rebuild rates must not be quoted.

