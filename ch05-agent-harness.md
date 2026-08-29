# Chapter 5: Agent Harness Engineering

> Put a frontier model into a badly designed agent system and you get a more articulate failure. The harness — not the model — is where reliability lives.

*Source: Karan Shingde, "System Design for Agent Systems (Part 1)," AI That Ships.*

## 1. Concept

The **harness** is everything around the model that makes an agent reliable:

```text
        ┌──────────────────────────────┐
        │        AGENT HARNESS         │
        │  Context assembly            │
        │  Tool execution & policies   │
        │  Memory & state persistence  │
        │  Retry / timeout / bounds    │
        │  Sandboxing & permissions    │
        │  Cost control                │
        │  Eval & observability hooks  │
        └──────────────┬───────────────┘
                       ▼
                    MODEL
```

Five components form one interconnected design — **tools, prompts, memory, orchestration, and human-in-the-loop placement**. They are not five features to configure independently; a change to one shifts load onto the others (better tools need less prompt; better memory needs less context stuffing).

## 2. Why the industry needed it

2023–24 optimism said capability lives in the model, so wait for the next model. What production taught: two teams with the same model get wildly different reliability, and the difference is entirely harness. By 2026 "harness engineering" is a named discipline with its own tooling ecosystem and hiring demand. The shift in one line: **from clever prompts to reliable infrastructure.**

## 3. The harness responsibilities, as design surfaces

- **Context assembly** — deciding what the model sees each turn (whole of Ch8). The harness owns the assembly *policy*; deterministic code builds the prompt from parts.
- **Tool policy** — which tools this agent, this user, this task may call; argument validation before execution; result shaping after (Ch13). The model *requests*; the harness *decides and executes*.
- **Execution environment** — where tool code runs. Anything that executes generated code or touches untrusted content runs sandboxed (container/VM, no network by default, allowlisted egress). The sandbox is a harness component, not an afterthought.
- **Bounds** — max iterations, per-run token budget, wall-clock timeout, per-tool timeout. Every intelligent behavior bracketed by a deterministic bound.
- **Persistence** — checkpointed state (Ch4) so runs survive crashes and can be resumed, replayed, and audited.
- **Cost control** — budget per run, per user, per day; model routing (cheap model for cheap steps); caching. Agent stacks spend money quietly (Ch7's budget alarms are the backstop; the harness is the frontstop).
- **Hooks** — every model call and tool call emits trace events (Ch16) and is capturable for eval datasets (Ch17). If the harness doesn't emit it, you can't measure it.

## 4. Design decisions

- **One harness, many agents.** The harness is platform, agents are tenants. Twenty teams each building retries and tool policy is how you get twenty half-harnesses — the argument that becomes Ch21.
- **Policy as data, not code.** Tool grants, bounds, and budgets should be configuration reviewable by non-engineers (risk teams will want to).
- **Fail closed.** Unknown tool? Malformed arguments? Budget exceeded? Stop and surface — never guess.

## 4b. Policy as data, visualized

```yaml
# harness-policy.yaml — reviewable by a risk team, no code reading required
agent: card-services
bounds:   { max_iterations: 12, run_token_budget: 60000, wall_clock_s: 180 }
tools:
  get_card_status:    { grant: allow,  timeout_s: 5, retries: 2 }
  block_card:         { grant: hitl,   idempotency: required }   # human approves
  send_notification:  { grant: allow,  rate_per_user_day: 3 }
  transfer_funds:     { grant: deny }                            # absent = impossible
on_violation: fail_closed
```

The model never sees this file — the harness enforces it around every request the model makes.

## 5. Trade-offs

Harness rigor costs iteration speed early on; teams under demo pressure skip it and accrue reliability debt that surfaces as "agents don't work here." The mature position: a thin harness from day one (bounds + tracing + tool policy), thickened as traces reveal need — not a cathedral before the first agent runs.

## 6. Industry implementation

The best-known harnesses are coding agents (Claude Code, Codex-style systems) — study them as *harness* case studies, not coding tools: aggressive context management, sandboxed execution, permission prompts at dangerous actions, everything traced. The awesome-harness-engineering ecosystem catalogs the emerging toolchain; the pattern to notice is that every serious lab now invests more engineering in the harness than in prompting.

## 7. Hands-on lab

Take your Ch2 raw loop and harden it into a harness: per-tool timeout and retry, a run token budget that halts gracefully, tool-argument validation, JSON trace events for every model/tool call, and a config file (not code) declaring which tools are enabled. Break each guard deliberately and watch it fail closed.

## 8. Architect's take: the banking read

In a bank the harness is where policy becomes enforcement. "The agent won't do X" is a hope if X is prevented by prompt, and a control if X is prevented by the harness (no tool grant, no network, budget cap). Frame every harness component as a named control — bounds, grants, sandbox, audit trail — and your agent platform inherits the vocabulary your risk and audit functions already speak. This framing alone will differentiate you in any enterprise AI discussion.

## Governance & security lens

The harness is where policy stops being a request and becomes enforcement: grants, bounds, budgets, and sandbox rules live here as *data a risk team can review* without reading code, and violations fail closed. Governing questions: **who approves changes to the policy file, is it version-controlled with the same rigor as code, and does every enforcement decision (blocked tool, exhausted budget) land in the audit stream?** A harness whose policy can be changed by the same engineer who writes the agent, without review, is a control on paper only — separation of duties applies to configuration, not just money.

## Interview-ready lines

- "Model quality sets the ceiling; harness quality sets the floor — and production lives on the floor."
- "The model requests, the harness decides and executes. That boundary is where both reliability and security live."
- "Harness policy should be data a risk team can review, not code they must trust."
- "A prompt is a request; the harness is a fact." 
