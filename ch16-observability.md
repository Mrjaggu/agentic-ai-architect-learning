# Chapter 16: Agent Observability

> Logs say a job ran. Traces say what the agent actually did. A bad answer without an error looks like success in the logs — this layer exists to show the truth.

## 1. Why traditional observability isn't enough

Logs/metrics/APM answer "is the service healthy?" Agents add a failure class those can't see: *the service was healthy and the answer was wrong* — wrong tool, garbage retrieval faithfully summarized, a loop that converged on the wrong goal. You need visibility into the **decision sequence**, not just the request.

## 2. The trace model

An agent run is a tree of spans:

```text
TRACE: job_id=…, user, agent, version
└─ span: agent_run (goal, outcome, total tokens/cost/latency)
   ├─ span: llm_call #1 (model, prompt fingerprint, tokens in/out, finish reason)
   ├─ span: tool_call get_transactions (args*, result size, latency, status)
   ├─ span: llm_call #2 …
   ├─ span: sub_agent exposure_analysis (its own subtree)
   └─ span: llm_call #n (final synthesis)
```

*args masked per data policy. The **trajectory** — the ordered sequence of decisions — is the unit of debugging (and the raw material of Ch17's evals). Emit via OpenTelemetry GenAI conventions where possible; store in a Langfuse/LangSmith/Phoenix-class backend that understands LLM spans (token accounting, prompt/response capture, cost rollups).

## 3. What to capture, beyond the obvious

- **Prompt/config fingerprints** — hash of system prompt, tool schema versions, model ID: without them you can't attribute a regression to the change that caused it.
- **Context composition** (Ch8's sections and budgets) — "what did the model see?" is the first debugging question and most teams can't answer it.
- **Tool error rates by tool and by error class** — distinguishes broken integrations from model misuse.
- **Convergence metrics** — turns per run, repeated-action detection (the Ch7 model that listed a directory forty times shows up here first).
- **Cost attribution** — per run, per user, per agent, per *step type*; the ratio "tokens spent on retries and wandering vs productive path" is your harness-quality KPI.
- **Outcome signal** — explicit (thumbs, task completion) or proxy (user rephrased, escalated to human). Traces without outcomes can't become evals.

## 3b. Instrumentation, visualized

```python
@observe(name="run_job")                      # outer span: the trajectory's root
def run_job(job_id, goal):
    with span("llm_call", model=MODEL_ID,
              prompt_fp=sha256(SYSTEM + TOOLSCHEMA_V)):     # fingerprint = attribution
        reply = llm(ctx, tools=tools)
        record(tokens_in=reply.usage.in_, tokens_out=reply.usage.out,
               cost=usd(reply.usage), cache_hit=reply.cached)
    with span("tool_call", tool=call.name, args=mask_pii(call.args)):
        result = execute(call)
    langfuse_flush()                          # background worker: flush or lose it
```

Every span answers a future question: what did it see, what did it choose, what did it cost?

## 4. From traces to operations

Wire the layers in dependency order (Ch7's lesson: alarm patterns must match what logs actually emit):

1. Structured logs with job_id/trace_id — cross-container correlation.
2. Metrics + alarms on rates: error rate, p95 latency, cost per run, queue depth, *convergence-failure* rate. Include budget alarms — agent stacks spend quietly.
3. Traces for the "why" behind every alarm.
4. Dashboards per audience: SRE (health), product (outcomes, cost), risk (policy events, HITL rates — Ch20).

And the meta-rule: **verify observability with a real job** — an unverified trace pipeline is worse than none because you'll trust it (Ch7).

## 5. Trade-offs

Full prompt/response capture is invaluable for debugging and radioactive for privacy — decide retention and masking per data class, not globally (in banking: mask by default, unmasked access gated and audited). Sampling saves cost but agents break in the tail; sample *successes*, keep all failures and all HITL-touched runs. Tracing adds latency if synchronous — batch and flush (and in background workers, flush explicitly or finished jobs' traces sit unsent — Ch7).

## 6. Industry implementation

The 2026 stack has consolidated: OTel GenAI semantics as the wire format; LangSmith, Langfuse (self-hostable — relevant for data residency), and Arize Phoenix as the LLM-native backends; traditional APM alongside, not replaced. The differentiator among mature teams is not tooling but *discipline*: fingerprinting configs, capturing outcomes, and closing the loop into evals.

## 7. Hands-on lab (Portfolio Project 3 core)

Instrument the banking agent end-to-end: OTel spans for every model/tool/sub-agent call, config fingerprints, cost rollups, convergence metrics, self-hosted Langfuse backend. Build the "why did job X fail?" workflow: from alarm → trace → offending span → context composition in under two minutes. Then inject three faults (broken tool, poisoned retrieval, non-converging prompt) and demonstrate each is *diagnosable from telemetry alone*, no code reading. That demo is the portfolio piece.

## 8. Architect's take: the banking read

Observability is where three bank obligations converge: **operations** (SLOs for agent services like any other), **audit** (the trace *is* the record of what the AI did on whose behalf — retention per record-keeping rules), and **model risk** (Ch20's monitoring requirements need exactly these signals: drift in convergence, tool errors, outcome rates). Design one telemetry pipeline that serves all three, with access controls per audience — build it once, defend it three times.

## Governance & security lens

Telemetry is double-edged: the trace is the audit record regulators expect *and* a concentrated store of customer data. Controls: PII masking by default with gated, audited unmasked access; retention per record-keeping rules (traces of financial decisions keep longer than debug logs); access tiered by audience (SRE sees health, risk sees policy events, few see raw prompts); and integrity — an audit trail that engineers can edit isn't one. Governing questions: **who can read raw traces, how long do we keep them, and can we prove a trace wasn't altered?** Observability that fails these questions turns your best control into your largest leak.

## Interview-ready lines

- "Agents add a failure class APM can't see: healthy service, wrong answer."
- "The trajectory is the unit of debugging; the trace is the audit record."
- "No config fingerprints, no regression attribution."
- "Sample successes, keep every failure — agents break in the tail."
