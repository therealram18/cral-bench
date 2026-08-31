# A/A control check — ESCALATE arm, gemini-3.7-flash

**What this is for.** A skeptical reviewer pointed out that two contrasts in the main paper are
confounded: the old runs used one version of the test-running code (`harness_v2.py`, run on
2026-08-27) and the new runs used a different version (`harness_v2b.py`, run on 2026-08-29), so
any difference we saw could be caused by the code/date change rather than by the thing we actually
wanted to measure. To check this, we took the ESCALATE condition (asking the model gemini-3.7-flash
about the same 263 grid-repair situations) and re-ran it a second time under the newer harness code
(`harness_v2b_aa.py`, "AA" for "A/A test" — running the *same* condition twice to see how much it
moves by chance alone). If old and new come out statistically indistinguishable, that's evidence the
earlier contrasts weren't just a harness-version artifact.

Sanity check against the quick numbers already reported: **ALL MATCH**.

## 1-2. Escalation rates, old vs new, and the rate difference

"Escalation rate" = fraction of parsed responses where the model chose to escalate (ask a human /
take the offered fallback) rather than answer directly. "Unparsed" = a response we could not
score at all (excluded from the rate, never counted as a non-escalation). The 95% CI (confidence
interval) on the difference comes from a "cluster bootstrap": we resample the 40 underlying grid
scenarios (not individual rows) with replacement, 20,000 times, and see how much the new-minus-old
rate difference varies — this respects the fact that multiple rows can come from the same scenario
and shouldn't be treated as fully independent. The SAME 20,000 resamples are reused for old and new
(and for every label), which is what makes this a paired comparison on the same 40 scenarios.

| label | n | old: unparsed | old rate (k/n_parsed) | new: unparsed | new rate (k/n_parsed) | diff (new-old) | 95% CI | excludes 0? |
|---|---|---|---|---|---|---|---|---|
| EASY | 17 | 0 (0.000) | 0.353 (6/17) | 0 (0.000) | 0.412 (7/17) | +0.059 | [-0.1429, +0.2667] | no |
| TRICKY | 58 | 0 (0.000) | 0.845 (49/58) | 0 (0.000) | 0.862 (50/58) | +0.017 | [-0.0833, +0.1167] | no |
| INFEASIBLE | 188 | 0 (0.000) | 0.989 (186/188) | 0 (0.000) | 0.989 (186/188) | +0.000 | [+0.0000, +0.0000] | no |

## 3. M4 + loglinear criterion c, old vs new

"Criterion c" is a single number from signal-detection theory that summarizes how cautious/biased
toward escalating the model is overall, combining its behavior on genuinely-infeasible cases
(where escalating is the "correct" signal-present response) and on easy/benign cases (where
escalating is a false alarm). Under the M4 mapping used throughout this project's canonical
analysis: INFEASIBLE counts as "signal", EASY counts as "noise", and TRICKY items split by
whether their correct fix is drastic (counts as signal) or benign (counts as noise). The
"loglinear correction" (also called the Hautus correction) is a standard small-sample adjustment
used so that a rate of exactly 0% or 100% doesn't produce an undefined/infinite z-score: instead of
k/n we use (k+0.5)/(n+1) before converting to a z-score.

- c_old = **-1.0018**
- c_new = **-1.0766**
- delta_c (new - old) = **-0.0748**
- 95% paired cluster-bootstrap CI on delta_c: **[-0.3134, +0.1609]** — includes 0

(Totals feeding c_old: hits-on-signal=221/229, hits-on-noise=20/34. Totals feeding c_new: hits-on-signal=221/229, hits-on-noise=22/34.)

## 4. Unparsed rate vs the 5% gate

This project's rule: any (label) cell whose unparsed rate exceeds 5% is not usable for analysis.
Both runs here are fully parsed.

| label | old unparsed | old rate | new unparsed | new rate | status |
|---|---|---|---|---|---|
| EASY | 0/17 | 0.000 | 0/17 | 0.000 | ok |
| TRICKY | 0/58 | 0.000 | 0/58 | 0.000 | ok |
| INFEASIBLE | 0/188 | 0.000 | 0/188 | 0.000 | ok |
| **overall** | 0/263 | 0.000 | 0/263 | 0.000 | ok |

## 5. Wall time (new / AA run)

File created 2026-08-31 19:51:43, last row written 2026-08-31 19:59:01 -> **7 min 18 sec** wall time for 263 model calls (including an initial 3-item smoke
test), at max_workers=6 concurrency, 0 retries needed
(all calls used the cap_used=8192 token budget, none needed the 16384-token retry
rung), 0 non-STOP finish reasons. File mtime cross-check: 2026-08-31 19:59:01 — consistent with the stated end time.

## 6. Verdict

**All three per-label rate-difference 95% CIs and the M4/loglinear delta-c 95% CI include zero, so the OLD-vs-NEW gap looks like ordinary run-to-run sampling noise, not a systematic harness-version or run-date effect.**

The observed differences are tiny in absolute terms — EASY moved by 1 escalation(s) out of 17 rows (1/17), TRICKY by 1 out of 58 (1/58), and INFEASIBLE by 0 out of 188 (0/188) — exactly the size of gap you'd expect from token-level or infrastructure-level stochasticity even at temperature=0, not a systematic shift from changing harness code paths or run date. The bootstrap confidence intervals, which is what we actually rely on rather than this intuition, back this up: all four intervals span zero.

