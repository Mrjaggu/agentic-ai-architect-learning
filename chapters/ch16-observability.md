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


## Interview Questions & Answers

**Q1: Why can't you just observe an AI agent the way you observe a normal microservice with your existing APM stack?**

Traditional APM answers "is the service healthy?" — uptime, latency, error rate. Agents introduce a failure mode APM is structurally blind to: the service returns 200, latency is fine, no exception is thrown, and the answer is still wrong — the wrong tool was called, retrieval returned garbage that got faithfully summarized, or the agent looped and converged on the wrong goal. None of that trips a traditional alarm because nothing "failed" in the infrastructure sense. You need visibility into the decision sequence itself — what the model saw, what it chose, and why — not just the request/response envelope, which is why agent traces model the run as a tree of spans (LLM calls, tool calls, sub-agents) rather than a single log line.

**Q2: What's the difference between a trace and a span in an agent observability pipeline, and what should a well-instrumented banking agent actually capture at each level?**

A trace is the whole job — one job_id tied to a user, an agent, and a version — and a span is one decision inside it: an llm_call, a tool_call, or a sub_agent invocation, each nested under an outer agent_run span. The agent_run span carries the goal, outcome, and total tokens/cost/latency; each llm_call span carries the model ID, a prompt fingerprint, and tokens in/out; each tool_call span carries the tool name, masked arguments, result size, latency, and status; and a sub_agent span (say, an exposure-analysis specialist) carries its own full subtree so its internal reasoning is inspectable on its own. The ordered sequence across all of these — the trajectory — is the actual unit you debug, and it's also the raw material that feeds evals later, so span granularity isn't a nice-to-have, it's what makes both debugging and eval-building possible.

**Q3: A customer complains about a bad outcome, but when you go to pull the trace for that job, it's missing. What do you do?**

First fall back to structured logs keyed by job_id/trace_id — that layer sits below tracing in the dependency stack and should survive even when the richer trace didn't. Then check whether the run was actually flushed: if tracing ran in a background worker, an unflushed buffer means a finished job's trace simply never got sent, which is a known failure mode, not a mystery. Next, check the sampling policy — if outcome capture classified this run as a "success" (no error, no escalation) it may have been sampled at a lower rate, which exposes a real gap: a run can look like a success in cheap signals while still being a bad answer to the customer, so it gets under-sampled precisely when you need it most. The fix isn't just retrying harder on this one job — it's alarming on trace-completeness itself, and treating "outcome disputed but full trace unavailable" as its own alert category going forward.

**Q4: Your convergence-failure rate alarm fires. Walk me through what happens after that, downstream.**

You go alarm → trace → offending span → context composition, which is the exact workflow the observability pipeline needs to support in under a couple of minutes, not hours. Inside the trace you're looking for a repeated-action pattern — the same signature as an agent listing a directory forty times — and you cross-check the prompt fingerprint against the last known-good version to see whether a recent system-prompt, tool-schema, or model change is the actual cause, since without that fingerprint you can't attribute a regression to anything. Once you've found the offending span, the fix is usually a stop condition, a tool description change, or a budget cap, but the loop doesn't close until that trajectory is fed back as a labeled failing case into evals so the same regression can't silently reappear next release. If the run touched a live customer decision, it also routes into HITL review and the audit retention path, because a convergence failure on a real account isn't just an engineering bug, it's a record.

**Q5: What are the cost trade-offs of full tracing and prompt/response capture, and how do you keep costs under control without losing your ability to debug?**

Full capture is invaluable for debugging and expensive at volume — storing every prompt and response for every run adds real storage cost, and synchronous tracing adds latency on the request path if you don't batch and flush asynchronously. The lever that actually works is asymmetric sampling: sample successes, but keep every failure and every HITL-touched run in full, because agents break in the tail and that's exactly the data a uniform sampling rate would throw away. On top of that, tiering retention — hot, uncompressed traces for recent runs and summarized or compressed payloads for older ones, bounded by record-keeping minimums rather than engineering convenience — controls storage cost without breaking the audit obligation. The real cost KPI, though, isn't storage spend at all — it's the ratio of tokens spent on retries and wandering versus the productive path, because a harness that wanders is burning far more money in inference than any tracing pipeline ever will.

**Q6: Trace stores end up holding full prompts and tool arguments, which in a bank means customer PII and financial data. What's the security exposure, and how do you mitigate it?**

A trace store is a concentrated pool of exactly the data a bank is most obligated to protect — account numbers, transaction details, and customer context can all show up inside system prompts, tool arguments, and model outputs, sitting in one place that's queryable across every agent and every customer. The mitigation starts at capture time, not after the fact: mask PII by default in the instrumentation itself, with unmasked access gated behind explicit approval and logged when it's used, so "who saw raw customer data and why" is always answerable. Retention has to follow the data's actual sensitivity class rather than one blanket policy — a trace behind a financial decision keeps longer than a debug-only trace — and the store needs integrity guarantees, because an audit trail that engineers can quietly edit isn't an audit trail. Self-hosting the backend (a Langfuse-class deployment rather than a SaaS default) also matters here, since it keeps that concentrated customer data inside the bank's own data-residency boundary instead of a third party's.

**Q7: Beyond after-the-fact debugging, how does observability function as a guardrail — a live safety control rather than a forensic tool?**

The same span-level signals that make postmortems possible also arm real-time circuit breakers. Convergence-failure rate and repeated-action detection catch a degenerate loop while it's happening, not after a customer already saw the bad output; tool-error-rate-by-class alarms catch a broken integration before its garbage results get faithfully summarized into a wrong answer; and budget alarms cap runaway spend on a job that's wandering rather than letting it burn silently, which agent stacks are prone to do. Observability also gates rollout decisions directly — you can canary a new prompt or model version and watch its convergence and outcome metrics before widening exposure, turning telemetry into a pre-release control rather than a post-incident one. So the guardrail value isn't a separate system bolted on top of tracing — it's the same instrumentation, read on a shorter time horizon.

**Q8: Who should actually be allowed to read raw trace data at a bank, and how do you design that access control?**

Access needs to be tiered by audience rather than granted uniformly: SRE sees health signals, product sees outcomes and cost, risk and compliance see policy events and HITL rates, and only a small, explicitly audited group ever sees raw, unmasked prompts and responses — least privilege applied to telemetry the same way it's applied to production data, because in this case it effectively is production data. That access should be role-based with time-boxed elevation rather than standing permissions, and every unmasked read should itself be logged, since the trace store aggregates data across every customer and every agent in one place, making it a higher-value target than any single transactional system it's watching. It's also worth distinguishing narrow, ticket-linked access — "let me see job_id X to debug this complaint" — from bulk export, which should be the exception that requires its own sign-off, not a routine capability anyone with dashboard access has by default.

**Q9: How do you set up alerting, on-call, and dashboards for an agent in production so that when something fires, people actually trust it?**

Wire the layers in dependency order: structured logs with job_id/trace_id for cross-container correlation first, then metrics and alarms on rates — error rate, p95 latency, cost per run, queue depth, and specifically convergence-failure rate, plus budget alarms, since agent stacks spend quietly in ways a traditional service doesn't — then traces to explain the "why" behind any alarm, then dashboards split per audience so SRE, product, and risk each see what's relevant to them instead of one undifferentiated view. The step teams skip is verifying the pipeline against a real job before trusting it — an alarm pattern that doesn't actually match what your logs emit, or a trace pipeline nobody has fired end-to-end, is worse than having none at all, because you'll trust it right up until the moment it matters. The operational bar worth holding on-call to is going from alarm to the offending span to what the model actually saw in under two minutes — if that takes longer, the dashboards are decoration, not tooling.

**Q10: Design the observability setup for a banking agent that runs credit exposure analysis through a sub-agent — what do you instrument, and why?**

Start with an outer agent_run span carrying the overall goal, outcome, and rolled-up cost/latency, then llm_call spans underneath each carrying a prompt fingerprint — a hash of the system prompt, tool schema version, and model ID — so any regression in exposure calculations can be attributed to the exact config change that caused it. Wrap each data pull, such as get_transactions, in a tool_call span with masked arguments and explicit status so a bad answer can be traced back to broken retrieval rather than model misuse, and give the exposure-analysis sub-agent its own full span subtree so its internal reasoning is inspectable independently of the parent job, including its own convergence metrics to catch a specialist looping on its own. Emit all of this via OTel GenAI conventions into a self-hosted backend for data residency, mask PII by default with gated and audited unmasked access, and apply sampling asymmetrically — sample successful exposure runs, but keep every failure and every human-reviewed run in full, because a credit decision is exactly the kind of record that has to survive intact for audit, not just for debugging.

**Q11: Walk me through how you'd debug a production agent failure end to end, from the moment an alert fires to identifying root cause.**

The alarm — say, a convergence-failure spike or a cost-per-run budget breach — gives you the job_id, which you use to pull the trace_id from structured logs and open the span tree in the trace backend. From there you check the prompt fingerprint against the last known-good version to rule a recent config or model change in or out, then look at context composition to answer "what did the model actually see," because that's usually the first real debugging question and most teams can't answer it without this step. You then isolate the offending span and classify it into one of a small number of fault families — a broken tool integration, poisoned retrieval that got faithfully summarized, or a genuinely non-converging prompt causing a loop — each of which has a distinct fix and a distinct owner. The bar this course holds that workflow to is doing it in under two minutes with no code reading, which is a deliberately concrete test of whether the telemetry is actually diagnostic or just decorative.
