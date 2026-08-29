# Chapter 18: Reliability & Cost Engineering

> The goal of this chapter: an agent an SRE team will accept in production and a CFO will keep paying for.

## 1. Reliability: deterministic boundaries around stochastic cores

The organizing principle (Ch1's dial, made operational): wrap every stochastic component in deterministic contracts.

- **Structured output validation** at every boundary (Ch13): typed schemas, one repair pass with the validation error, then fail closed. Never let unvalidated model output cross into a downstream system.
- **Retries with judgment**: retry *transient* failures (timeouts, 429s) with exponential backoff + jitter; do NOT blind-retry model calls that returned confidently wrong content — that's a different failure needing a different prompt/path, not repetition. Retries are only safe where tools are idempotent (Ch6/13).
- **Timeouts everywhere**: per tool call, per model call, per node, per run — nested budgets, each enforced by the harness (Ch5). An agent without timeouts is an outage with extra steps.
- **Fallback chains, defined not improvised**: primary model → fallback model (same schema!) → degraded deterministic path → honest failure with state preserved (Ch4 checkpoint) for resume or human pickup. Degrading gracefully ("here's what I found; I couldn't complete X") beats both silent failure and heroic hallucination.
- **Circuit breakers** per dependency (model endpoint, each tool): trip on error-rate, fail fast, probe to recover. Protects both your latency and the struggling dependency.
- **Error recovery as design**: distinguish *retriable* (transient), *reroutable* (this path failed, try another — Ch12's self-correction), and *terminal* (stop, checkpoint, surface). Tag every failure mode in the codebase with one of the three; untagged errors default to terminal.

## 1b. The fallback chain, visualized

```python
async def call_model(ctx, step_type):
    model = ROUTE[step_type]                     # "classify"→small, "synthesize"→large
    for attempt in backoff(retries=2):
        try:
            out = await llm(model, ctx, timeout=TIMEOUTS[step_type])
            return OutputSchema.model_validate_json(out)   # contract at the boundary
        except (Timeout, RateLimited):  continue           # retriable: transient only
        except ValidationError as e:
            out = await llm(model, ctx + repair_prompt(e)) # ONE repair pass
            return OutputSchema.model_validate_json(out)   # then fail closed
    if breaker.allows(FALLBACK[model]):
        return await call_model(ctx, step_type, model=FALLBACK[model])  # eval-gated
    checkpoint(ctx); raise Degraded("partial result preserved")  # fail clean, resumable
```

## 2. Cost: the four levers

Agent cost = calls × context × model price × retries. The levers, in typical ROI order:

1. **Context discipline** (Ch8) — the flat-context-curve work is usually the single biggest saving; wandering, non-converging runs (Ch16's metric) are pure waste to hunt down.
2. **Prompt caching** — structure prompts stable-prefix-first (system + tools, then volatile) and cache hit rates transform economics on loops that re-send context every turn; know your provider's cache pricing (and Ch7's trap: cache markers on unsupported models throw misleading errors).
3. **Model routing** — cheap models for classification, extraction, summarization; expensive models for planning and synthesis. Route by *step type*, validated by evals (Ch17) so downgrades are proven safe, not hoped. An LLM-gateway layer (LiteLLM-class or your platform's own) centralizes routing, quotas, and provider failover.
4. **Budgets as hard rails** — per run, per user, per tenant, per day (Ch5/6); alert at 80%, halt gracefully at 100% with state checkpointed. The Ch7 billing alarm is the backstop; harness budgets are the frontstop.

## 3. Capacity & performance

Queue-depth-based worker autoscaling (Ch6); provider rate limits are a *shared* resource — a token-bucket at the gateway prevents one tenant's batch from starving everyone (Ch6's fairness); p95 matters more than mean because agent latency is long-tailed (one extra loop turn doubles a run); streaming buys *perceived* latency even when totals are fixed.

## 4. Trade-offs

Reliability machinery adds code paths that themselves need testing (chaos-style fault injection — Ch16's lab — is the honest way). Fallback models risk quality cliffs: gate them with evals, and prefer "degrade the task" over "degrade the model" where quality is contractual. Aggressive caching risks staleness in the cached prefix (tool schema changes must bust the cache). Cost optimization that adds 200ms of routing to save fractions of a cent is theater — measure both sides.

## 5. Industry implementation

The mature pattern is an **AI gateway** (routing, caching, quotas, failover, cost attribution in one layer) in front of all model providers — self-hosted LiteLLM-class or cloud-native equivalents — plus harness-level budgets and graph-level checkpoints. SRE teams accept agents when they see familiar shapes: SLOs, error budgets, circuit breakers, runbooks. Give them those shapes.

## 6. Hands-on lab

Harden the banking agent: nested timeouts, tagged error taxonomy (retriable/reroutable/terminal), a two-model fallback chain validated by your Ch17 suite, a circuit breaker on the flakiest tool, prompt-cache-aligned context assembly, and per-user daily budgets. Then chaos day: inject provider 429s, a hung tool, and a malformed-output storm; publish the before/after table of runs completed, degraded, failed-clean, failed-dirty. Target: zero failed-dirty.

## 7. Architect's take: the banking read

Banks already run the most reliability-mature software estate in industry — the win is *mapping agent concepts onto controls the bank already trusts*: circuit breakers and DR runbooks (ops), budget rails (financial control), fallback chains and kill-behavior (Ch20's kill-switch expectation lands here: a halt must leave state checkpointed, auditable, and resumable — "stop cleanly" is a designed feature, not a power cut). Cost attribution per department/use case is what lets an AI platform survive its second budget cycle — build showback from day one.

## Governance & security lens

Reliability machinery has governance meaning: fallback models must clear the same eval and safety gates as primaries (a degraded model serving credit answers is a silent policy change); kill behavior must checkpoint state and leave a clean audit trail — "stop cleanly" is the RBI kill-switch expectation made real; budget rails are financial controls with owners and review, not engineer-tunable knobs; and degraded modes are documented states the business signed off on, not improvisations. Governing questions: **is every fallback path as validated as the primary, and when we halt an agent, can we show exactly what it had done and resume without loss?**

## Interview-ready lines

- "Wrap every stochastic component in a deterministic contract — validate, bound, fallback, fail closed."
- "Never blind-retry a confidently wrong model call; that's a reroute, not a retry."
- "Route by step type, prove downgrades with evals."
- "A kill switch that loses state isn't a control, it's a second incident."
