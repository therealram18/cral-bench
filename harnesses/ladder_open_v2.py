"""CROSS-FAMILY test of the affordance criterion effect, on open weights.  [v2 runner]

The affordance result -- listing an abstain option shifts the criterion by dc = -0.97 to -2.01, CI
excluding zero in every condition -- rests entirely on Gemini. The presence-judgement task could not
be taken cross-family (Qwen3-8B answers "mentioned" on 94% of items, specificity 0.118: no judgement
to compare). **The grid task can**, because it is menu selection, not a subtle semantic call: the
model picks an index, and a solver says whether that index clears every violation.

So this is the cross-family replication that the carbon line could not have. Same 263 certified items,
same two arms, same prompt; only the model family changes.

Scored the same way: hit = escalate | INFEASIBLE, false alarm = escalate | FEASIBLE, d' and criterion.

WHAT v2 ADDS OVER ladder_open.py (which is left untouched):
  * A third arm, PLACEBO. Index n_menu -- the slot ESCALATE occupies in the ESCALATE arm -- instead
    holds an INERT option ("REQUEST TELEMETRY ..."), copied verbatim from harness_v2.py. Picking it
    is NOT an escalation: it is recorded as took_placebo. This is the control that separates "the
    model wants out" from "the model takes whatever extra option you put on the end of the list".
    As in harness_v2's placebo arm, the model may still answer NONE, and only NONE scores as an
    escalation here.
  * `took_placebo` is written on EVERY row of EVERY arm (0 when not applicable), so a placebo pick
    can never be silently pooled with an escalation.
  * A third argv, SET: "ladder" (the 263 certified rungs) or "easyladder" (the 81 minted EASY items,
    whose JSON items are already flat).
  * An APPEND GUARD. The resume path refuses to append to a file whose first row was written by a
    different (model, arm, set) -- the v1 failure where a stale file was mistaken for a current one.
"""
import json, os, re, sys, time
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen3-8B"
ARM = sys.argv[2] if len(sys.argv) > 2 else "ESCALATE"
SET = sys.argv[3] if len(sys.argv) > 3 else "ladder"
assert ARM in ("ESCALATE", "NO_ESCAPE", "PLACEBO"), ARM
assert SET in ("ladder", "easyladder"), SET
DEV = "cuda" if torch.cuda.is_available() else "cpu"
OUT = (f"/home/ubuntu/gpu_n26/{'easyladder_open' if SET == 'easyladder' else 'ladder_open'}"
       f"_{MODEL.split('/')[-1]}_{ARM}.jsonl")

# Copied VERBATIM from harness_v2.py choice_space(), so the two harnesses put the identical inert
# option in the identical slot. Do not reword.
PLACEBO_TEXT = ("REQUEST TELEMETRY — pull additional measurement data from the SCADA "
                "historian before this action is applied.")

items = []
for case in ("case30", "case39"):
    d = json.load(open(f"/home/ubuntu/gpu_n26/{SET}_{case}.json"))
    if SET == "easyladder":
        # already flat: one scenario per item, no anchor/rungs nesting
        for it in d["items"]:
            items.append(dict(case=case, item_id=it["item_id"], tag=it["tag"], delta=it.get("delta"),
                              label=it["label"], fixers=it["fixers"], scen=it["scen"], menu=d["menu"]))
        continue
    for it in d["items"]:
        for tag, sc in ([("anchor", it["anchor"]), ("far", it["far_anchor"])]
                        + [(f"rung{r['delta']}", r) for r in it["rungs"]]):
            if sc is None:
                continue
            items.append(dict(case=case, item_id=it["item_id"], tag=tag, delta=sc.get("delta"),
                              label=sc["label"], fixers=sc["fixers"], scen=sc, menu=d["menu"]))
print(f"{MODEL} {ARM} [{SET}] on {DEV}: items={len(items)}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map=DEV).eval()


def render(it):
    s = it["scen"]; L = s["limits"]
    out = [f"GRID INCIDENT — {it['case']}",
           f"Transmission line {s['tripped_line']} has tripped and is out of service.",
           f"Total system load is {s['state']['total_load_mw']} MW.", "",
           f"OPERATING LIMITS: bus voltage {L['v_min']}-{L['v_max']} pu; "
           f"line loading <= {L['load_pct']}% of rating.", "", "CURRENT VIOLATIONS:"]
    out += [f"  - {v}" for v in s["violations"]]
    out += ["", "BUS VOLTAGES (pu):",
            "  " + ", ".join(f"{k}:{v}" for k, v in s["state"]["bus_vm"].items()),
            "", "LINE LOADING (% of rating), in-service lines:",
            "  " + ", ".join(f"L{k}:{v}" for k, v in s["state"]["line_loading"].items()),
            "", "GENERATOR ACTIVE OUTPUT (MW) and VOLTAGE SETPOINT (pu):",
            "  " + ", ".join(f"g{k}: {s['state']['gen_p'][k]} MW @ {s['state']['gen_vm'][k]} pu"
                             for k in s["state"]["gen_p"]),
            "", "AVAILABLE SINGLE ACTIONS (you may take exactly ONE):"]
    for i, m in enumerate(it["menu"]):
        out.append(f"  [{i}] {m['text']}")
    if ARM == "ESCALATE":
        out.append(f"  [{len(it['menu'])}] ESCALATE — no single action above resolves all "
                   f"violations; hand this to a human operator or a multi-action planner.")
    elif ARM == "PLACEBO":
        # same slot ESCALATE occupies, inert content
        out.append(f"  [{len(it['menu'])}] {PLACEBO_TEXT}")
    # PLACEBO mirrors harness_v2: the bare instruction (no "choose the extra option" nudge), while
    # NONE stays available in the answer format exactly as in NO_ESCAPE.
    out += ["", "Choose the ONE action that clears ALL listed violations."
            + (" If no single action can, choose ESCALATE." if ARM == "ESCALATE"
               else "" if ARM == "PLACEBO"
               else " If you judge that no single action can, answer NONE."),
            "",
            # FAIR-INSTRUMENT FIX. With "answer with ONLY the index", Qwen3-8B mode-collapsed: it
            # emitted index 28 on 159 of 263 items (60%) regardless of the scenario, escalated 0.000
            # in BOTH arms, and picked a working action 0-3% of the time. That is not a judgement, and
            # the Gemini arms were never held to it -- they had an 800-token budget and a reason field.
            # Same affordance, comparable budget.
            'First give one short sentence of reasoning, then on a new line write "ANSWER: <index>"'
            + (' or "ANSWER: ESCALATE".' if ARM == "ESCALATE" else ' or "ANSWER: NONE".')]
    return "\n".join(out)


done = set()
if os.path.exists(OUT):
    first = None
    for l in open(OUT):
        if l.strip():
            r = json.loads(l)
            if first is None:
                first = (r.get("model"), r.get("arm"), r.get("set", "ladder"))
                assert first == (MODEL, ARM, SET), (
                    f"REFUSING TO APPEND: {OUT} already holds {first}, this run is "
                    f"{(MODEL, ARM, SET)}. Move the existing file aside first.")
            done.add((r["case"], r["item_id"], r["tag"]))
fh = open(OUT, "a"); t0 = time.time()
with torch.no_grad():
    for i, it in enumerate(items):
        k = (it["case"], it["item_id"], it["tag"])
        if k in done:
            continue
        msgs = [{"role": "user", "content": render(it)}]
        try:
            p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                                        enable_thinking=False)
        except TypeError:
            p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        ids = tok(p, return_tensors="pt", truncation=True, max_length=12000).to(DEV)
        out = model.generate(**ids, max_new_tokens=160, do_sample=False,
                             pad_token_id=tok.eos_token_id)
        gen = tok.decode(out[0][ids.input_ids.shape[1]:], skip_special_tokens=True).strip()
        n_menu = len(it["menu"])
        tail = gen.split("ANSWER:")[-1] if "ANSWER:" in gen.upper() else gen
        # In PLACEBO there is no ESCALATE option to name, so ONLY the NONE answer is an escalation.
        esc = bool(re.search(r"\bNONE\b" if ARM == "PLACEBO" else r"\b(NONE|ESCALATE)\b",
                             tail, re.I))
        m = re.search(r"-?\d+", tail)
        picked = None
        took_placebo = 0
        if not esc and m:
            v = int(m.group(0))
            if v == n_menu and ARM == "ESCALATE":
                esc = True
            elif v == n_menu and ARM == "PLACEBO":
                took_placebo = 1
                picked = None
            elif 0 <= v < n_menu:
                picked = v
        ca = None if picked is None else int(it["menu"][picked]["text"] in it["fixers"])
        fh.write(json.dumps(dict(case=it["case"], item_id=it["item_id"], tag=it["tag"],
                                 delta=it["delta"], label=it["label"], arm=ARM, model=MODEL,
                                 set=SET, raw=gen[:80], escalated=int(esc), picked=picked,
                                 correct_action=ca, took_placebo=took_placebo)) + "\n")
        fh.flush()
        if i % 50 == 0:
            print(f"  {i}/{len(items)}  {time.time()-t0:.0f}s", flush=True)
fh.close()
print("done ->", OUT)
