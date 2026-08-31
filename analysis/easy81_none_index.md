# EASY-81 false-alarm decomposition: NO_ESCAPE -> NONE_INDEX -> ESCALATE

seed=20260827 | bootstrap B=20,000 | cluster=(case,item_id), n_clusters=81 | gate=0.05

Every row in this supplement is label EASY (solver-certified feasible; served_load >= 0.99), so every escalation counted below is a FALSE ALARM -- the model declining a fully-resolving single action.

## 0. Gate check (all 9 cells: 3 models x 3 arms)

| model | arm | n | unparsed | rate | status | escalated/parsed | point rate |
|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | NO_ESCAPE | 81 | 0 | 0.0000 | ok | 9/81 | 0.1111 |
| gemini-3.7-flash | NONE_INDEX | 81 | 0 | 0.0000 | ok | 20/81 | 0.2469 |
| gemini-3.7-flash | ESCALATE | 81 | 0 | 0.0000 | ok | 33/81 | 0.4074 |
| gemini-3.1-pro-preview | NO_ESCAPE | 81 | 2 | 0.0247 | ok | 1/79 | 0.0127 |
| gemini-3.1-pro-preview | NONE_INDEX | 81 | 2 | 0.0247 | ok | 4/79 | 0.0506 |
| gemini-3.1-pro-preview | ESCALATE | 81 | 1 | 0.0123 | ok | 8/80 | 0.1000 |
| gpt-5.6-luna | NO_ESCAPE | 81 | 0 | 0.0000 | ok | 0/81 | 0.0000 |
| gpt-5.6-luna | NONE_INDEX | 81 | 0 | 0.0000 | ok | 0/81 | 0.0000 |
| gpt-5.6-luna | ESCALATE | 81 | 0 | 0.0000 | ok | 6/81 | 0.0741 |

## 1. Per-model false-alarm rate by arm (cluster-bootstrap point + 95% CI)

| model | NO_ESCAPE | NONE_INDEX | ESCALATE |
|---|---|---|---|
| gemini-3.7-flash | 0.1111 [0.0494,0.1852] (k=9/81) | 0.2469 [0.1605,0.3457] (k=20/81) | 0.4074 [0.2963,0.5185] (k=33/81) |
| gemini-3.1-pro-preview | 0.0127 [0.0000,0.0390] (k=1/79) | 0.0506 [0.0123,0.1026] (k=4/79) | 0.1000 [0.0375,0.1728] (k=8/80) |
| gpt-5.6-luna | 0.0000 [0.0000,0.0000] (k=0/81) | 0.0000 [0.0000,0.0000] (k=0/81) | 0.0741 [0.0247,0.1358] (k=6/81) |

## 2. Decomposition: N->I (offering a bare decline slot) and I->E (naming it ESCALATE + human-operator language)

| model | N->I delta | 95% CI | excludes 0 | Fisher p | I->E delta | 95% CI | excludes 0 | Fisher p | total N->E |
|---|---|---|---|---|---|---|---|---|---|
| gemini-3.7-flash | +0.1358 | [+0.0617,+0.2099] | YES | 0.0391 | +0.1605 | [+0.0864,+0.2469] | YES | 0.0440 | +0.2963 |
| gemini-3.1-pro-preview | +0.0380 | [-0.0128,+0.0988] | no | 0.3670 | +0.0494 | [-0.0136,+0.1219] | no | 0.3688 | +0.0873 |
| gpt-5.6-luna | +0.0000 | [+0.0000,+0.0000] | no | 1.0000 | +0.0741 | [+0.0247,+0.1358] | YES | 0.0284 | +0.0741 |

Components excluding zero: 3 of 6.

