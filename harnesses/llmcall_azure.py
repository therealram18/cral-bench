"""ONE CALL INTERFACE ACROSS PROVIDERS, with the v2 discipline built in -- AZURE VARIANT.

This is a sibling of common/llmcall.py (NOT an edit of it -- that file is pinned). It copies the
same discipline verbatim and adds one backend: `azure`, for an Azure OpenAI v1-compatible
deployment. The discipline, restated because it is the whole point of this module existing:

  1. TRUNCATION IS NEVER SCORED. A response that hit the output cap is RETRIED at a larger cap. If it
     still truncates, the row is marked `parsed=False` and is EXCLUDED from every rate -- never counted
     as an absence of behaviour.
  2. EVERY ROW CARRIES ITS OWN PROVENANCE: provider, exact model string echoed back by the API, cap
     actually used, finish reason, thinking tokens actually spent, and a hash of the calling script.
     A stale file can never again be mistaken for a current one.
  3. REASONING BUDGET IS MEASURED, NOT ASSUMED. `thinking_used` is recorded per call.
  4. TOOL CALLS ARE RETURNED AS STRUCTURED OBJECTS with the tool NAME.

Azure specifics:
  * The deployment name (here: "luna") is a LABEL, not a model identity. The API echoes the real
    underlying model string back in the response body (`model` field); that echo is captured in
    `model_echo` on every row so the paper never has to cite "luna".
  * Credentials (AZURE_KEY, AZURE_ENDPOINT) are read at call time from the .env file below, or from
    the process environment if already exported there. Never hardcode, log, or otherwise print the
    key -- only `model_echo`, never the credential, belongs in any row or report.
  * Auth: `api-key: <AZURE_KEY>` header first; if that 401s, retry the SAME body with
    `Authorization: Bearer <AZURE_KEY>` instead (some v1-compatible deployments expect one or the
    other and there is no way to know in advance which without trying).
  * Some deployments reject `max_completion_tokens` (older API surface wants `max_tokens`) or reject
    a non-default `temperature` (reasoning-tier models only accept the default). Both are retried
    once with the offending field adjusted, mirroring the seed-retry pattern already used in
    harness_v2.py -- a defensive fallback, not a silent default.

Providers: google (Gemini), anthropic (Claude), openai (GPT), azure (Azure OpenAI, any deployment).
One schema in, one shape out.
"""
import json, os, time, hashlib, urllib.request

KEYDIR = os.path.expanduser("~/.keys/cral")  # anonymized; originally a project-local key directory, see README "Anonymization note"
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")  # anonymized; originally an absolute path, see README "Anonymization note"


def _key(name):
    p = os.path.join(KEYDIR, name)
    return open(p).read().strip() if os.path.exists(p) else None


def _load_dotenv(path=ENV_PATH):
    env = {}
    if not os.path.exists(path):
        return env
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _azure_creds():
    """AZURE_KEY / AZURE_ENDPOINT, process env wins, else parsed from .env at call time.
    Never cached at import time and never logged."""
    env = _load_dotenv()
    key = os.environ.get("AZURE_KEY") or env.get("AZURE_KEY")
    endpoint = os.environ.get("AZURE_ENDPOINT") or env.get("AZURE_ENDPOINT")
    if not key or not endpoint:
        raise RuntimeError("AZURE_KEY / AZURE_ENDPOINT not found in env or " + ENV_PATH)
    return key, endpoint


CAPS = [4096, 12288]        # retry ladder; a truncated response is retried, never scored


def _post(url, body, headers, timeout=180, tries=4):
    for a in range(tries):
        try:
            r = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
            return json.loads(urllib.request.urlopen(r, timeout=timeout).read()), None
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:200]
            if e.code in (400, 401, 403, 404): return None, f"HTTP{e.code}:{msg}"
            if a == tries - 1: return None, f"HTTP{e.code}:{msg}"
            time.sleep(2 * (a + 1))
        except Exception as e:
            if a == tries - 1: return None, f"{type(e).__name__}:{str(e)[:120]}"
            time.sleep(2 * (a + 1))
    return None, "EXHAUSTED"


def _google(model, system, user, tools, cap, think, **kw):
    body = {"contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 1.0, "maxOutputTokens": cap}}
    if system: body["systemInstruction"] = {"parts": [{"text": system}]}
    if think is not None: body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": think}
    if tools:
        body["tools"] = [{"functionDeclarations": [
            {"name": t["name"], "description": t.get("description", ""),
             "parameters": t["parameters"]} for t in tools]}]
    d, err = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={_key('gemini')}",
                   body, {"Content-Type": "application/json"})
    if err: return None, err
    if not d.get("candidates"):
        pf = d.get("promptFeedback", {}) or {}
        return dict(text=None, calls=[], finish=f"BLOCKED:{pf.get('blockReason', 'NO_CANDIDATES')}",
                    model_echo=d.get("modelVersion"), thinking_used=0), None
    c = d["candidates"][0]
    parts = c.get("content", {}).get("parts", [])
    calls = [dict(name=p["functionCall"].get("name"), args=p["functionCall"].get("args", {}))
             for p in parts if "functionCall" in p]
    return dict(text="".join(p.get("text", "") for p in parts), calls=calls,
                finish=c.get("finishReason"), model_echo=d.get("modelVersion"),
                thinking_used=int(d.get("usageMetadata", {}).get("thoughtsTokenCount", 0) or 0)), None


def _anthropic(model, system, user, tools, cap, think, **kw):
    body = {"model": model, "max_tokens": cap, "messages": [{"role": "user", "content": user}]}
    if system: body["system"] = system
    if tools:
        body["tools"] = [{"name": t["name"], "description": t.get("description", ""),
                          "input_schema": t["parameters"]} for t in tools]
    if think:
        body["thinking"] = {"type": "enabled", "budget_tokens": think}
        body["max_tokens"] = max(cap, think + 2048)
    d, err = _post("https://api.anthropic.com/v1/messages", body,
                   {"x-api-key": _key("anthropic"), "anthropic-version": "2023-06-01",
                    "content-type": "application/json"})
    if err: return None, err
    calls = [dict(name=c.get("name"), args=c.get("input", {}))
             for c in d.get("content", []) if c.get("type") == "tool_use"]
    text = "".join(c.get("text", "") for c in d.get("content", []) if c.get("type") == "text")
    think_used = sum(len(c.get("thinking", "") or "") // 4
                     for c in d.get("content", []) if c.get("type") == "thinking")
    return dict(text=text, calls=calls, finish=d.get("stop_reason"),
                model_echo=d.get("model"), thinking_used=think_used), None


def _openai(model, system, user, tools, cap, think, **kw):
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    body = {"model": model, "messages": msgs, "max_completion_tokens": cap}
    if tools:
        body["tools"] = [{"type": "function", "function": {
            "name": t["name"], "description": t.get("description", ""), "parameters": t["parameters"]}}
            for t in tools]
    d, err = _post("https://api.openai.com/v1/chat/completions", body,
                   {"Authorization": f"Bearer {_key('openai')}", "content-type": "application/json"})
    if err: return None, err
    ch = d["choices"][0]; m = ch["message"]
    calls = [dict(name=t["function"]["name"], args=json.loads(t["function"].get("arguments") or "{}"))
             for t in (m.get("tool_calls") or [])]
    return dict(text=m.get("content") or "", calls=calls, finish=ch.get("finish_reason"),
                model_echo=d.get("model"),
                thinking_used=int(d.get("usage", {}).get("completion_tokens_details", {})
                                  .get("reasoning_tokens", 0) or 0)), None


def _azure_request(url, key, body, auth_style):
    if auth_style == "api-key":
        headers = {"api-key": key, "content-type": "application/json"}
    else:
        headers = {"Authorization": f"Bearer {key}", "content-type": "application/json"}
    return _post(url, body, headers)


def _azure(model, system, user, tools, cap, think, temperature=None, seed=None, **kw):
    """Azure OpenAI v1-compatible /chat/completions. `model` is the DEPLOYMENT NAME (e.g. "luna"),
    not a model identity -- the real identity comes back in the response body's `model` field and is
    captured as `model_echo`. Defensive retries (never silent): api-key -> Bearer on 401;
    max_completion_tokens -> max_tokens if the field is rejected; drop temperature if rejected."""
    key, endpoint = _azure_creds()
    url = endpoint.rstrip("/") + "/chat/completions"
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    body = {"model": model, "messages": msgs, "max_completion_tokens": cap}
    if temperature is not None: body["temperature"] = temperature
    if seed is not None: body["seed"] = seed
    if tools:
        body["tools"] = [{"type": "function", "function": {
            "name": t["name"], "description": t.get("description", ""), "parameters": t["parameters"]}}
            for t in tools]

    auth_style = "api-key"
    d, err = _azure_request(url, key, body, auth_style)
    if err and err.startswith("HTTP401"):
        auth_style = "bearer"
        d, err = _azure_request(url, key, body, auth_style)

    # some deployments reject max_completion_tokens; fall back to max_tokens
    if err and err.startswith("HTTP400") and "max_completion_tokens" in err and "max_tokens" not in body:
        body2 = dict(body); body2.pop("max_completion_tokens", None); body2["max_tokens"] = cap
        d, err = _azure_request(url, key, body2, auth_style)
        if not err: body = body2

    # some (reasoning-tier) deployments reject a non-default temperature
    if err and err.startswith("HTTP400") and "temperature" in err and "temperature" in body:
        body3 = dict(body); body3.pop("temperature", None)
        d, err = _azure_request(url, key, body3, auth_style)
        if not err: body = body3

    if err: return None, err
    if not d.get("choices"):
        pf = d.get("prompt_filter_results", []) or []
        reason = "NO_CHOICES"
        for r in pf:
            cf = (r.get("content_filter_results") or {})
            blocked = [k for k, v in cf.items() if isinstance(v, dict) and v.get("filtered")]
            if blocked: reason = "CONTENT_FILTER:" + ",".join(blocked); break
        return dict(text=None, calls=[], finish=f"BLOCKED:{reason}",
                    model_echo=d.get("model"), thinking_used=0), None
    ch = d["choices"][0]; m = ch.get("message", {}) or {}
    calls = [dict(name=t["function"]["name"], args=json.loads(t["function"].get("arguments") or "{}"))
             for t in (m.get("tool_calls") or [])]
    return dict(text=m.get("content") or "", calls=calls, finish=ch.get("finish_reason"),
                model_echo=d.get("model"),
                thinking_used=int(d.get("usage", {}).get("completion_tokens_details", {})
                                  .get("reasoning_tokens", 0) or 0),
                auth_style=auth_style), None


BACKENDS = {"google": _google, "anthropic": _anthropic, "openai": _openai, "azure": _azure}
TRUNCATED = {"MAX_TOKENS", "max_tokens", "length"}
BLOCKED_PREFIX = "BLOCKED:"


def call(provider, model, user, system=None, tools=None, think=None, script_path=None,
         temperature=None, seed=None, caps=None):
    """Returns a dict that ALWAYS carries provenance and a `parsed` flag. Truncation is retried, then
    excluded -- never silently scored as an absence of behaviour. `caps` overrides the default retry
    ladder (e.g. harness_v2_azure.py passes [8192, 16384] to match harness_v2.py exactly)."""
    fn = BACKENDS[provider]
    out = err = None
    for cap in (caps or CAPS):
        out, err = fn(model, system, user, tools, cap, think, temperature=temperature, seed=seed)
        if out is None: break
        out["cap_used"] = cap
        if str(out.get("finish")) not in TRUNCATED: break
    sh = None
    if script_path and os.path.exists(script_path):
        sh = hashlib.sha256(open(script_path, "rb").read()).hexdigest()[:12]
    if out is None:
        return dict(provider=provider, model=model, parsed=False, error=err, calls=[], text="",
                    finish=None, script=sh)
    out.update(provider=provider, model=model, script=sh,
               parsed=(str(out.get("finish")) not in TRUNCATED) and not str(out.get("finish")).startswith("BLOCKED:"))
    return out


def rate(rows, pred, gate=0.05, label=""):
    """A rate that REFUSES to be computed on a cell with too much truncation."""
    n = len(rows)
    if n == 0: return dict(label=label, n=0, reportable=False, reason="empty")
    unparsed = sum(1 for r in rows if not r.get("parsed"))
    r_un = unparsed / n
    p = [r for r in rows if r.get("parsed")]
    if r_un > gate:
        return dict(label=label, n=n, unparsed=unparsed, unparsed_rate=round(r_un, 4),
                    reportable=False, reason=f"unparsed {r_un:.3f} > gate {gate}")
    k = sum(1 for r in p if pred(r))
    return dict(label=label, n=n, n_parsed=len(p), unparsed=unparsed,
                unparsed_rate=round(r_un, 4), k=k,
                rate=round(k / len(p), 4) if p else None, reportable=True)
