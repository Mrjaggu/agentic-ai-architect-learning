# End-to-End Case Studies — System Design Interview + Real Industry Stack

> Two case studies. Part A is the *interview*: one question walked end-to-end the way you'd answer it live, with the probes interviewers actually push on. Part B is the *industry*: a documented production system using the full modern stack, mapped element-by-element to our chapters.

---

# Part A — The Interview Case

## The question

*"Design an AI assistant platform for a retail bank: customers ask about products and their accounts, dispute transactions, and request actions like card blocking. Operations staff use it to investigate cases. Design it."*

This is the new class of system-design question. The evaluation criteria (from published interviewer guides): do you clarify before drawing, do you distinguish pipelines from reasoning loops, do you handle failure and recovery, and — the known differentiator — do you raise **guardrails and governance unprompted**.

## Step 1 — Clarify (3 minutes; never skip)

Ask: Who are the users (customers + staff → two trust levels)? What actions beyond answering (card block, dispute filing → irreversible actions exist)? Volumes (say 50k conversations/day, 5% needing investigation)? Latency expectations (interactive answers seconds; investigations can take minutes async)? Compliance constraints (it's a bank: audit, data residency, approval flows — say RBI/DPDP out loud). Model constraints (assume hosted models with workload identity; on-prem variant if data residency demands).

Each answer moves architecture: irreversible actions ⇒ HITL; minutes-long investigations ⇒ async backend; two user classes ⇒ entitlement propagation; compliance ⇒ traces as audit records.

## Step 2 — Place the workload on the ladder (2 minutes)

Say this early — it's the architect signal (Ch1): "This isn't one system, it's three kinds of work behind one door. Product/policy Q&A is **RAG**. Card blocking is a **workflow** with LLM steps — compliance fixes the sequence, code owns control flow. Transaction investigation is a genuine **agent** — the path can't be known upfront. A router in front dispatches among them, so I only pay for non-determinism where it earns its keep."

## Step 3 — High-level architecture (draw this, ~5 minutes)

```text
Channels (app / web / branch console)
        │  auth: user identity + entitlements travel with every request
        ▼
   API (fast path) ──► job store ──► QUEUE ──► WORKER POOL (slow path)
        │                                        │
        │ SSE progress events ◄──────────────────┤
        ▼                                        ▼
   ┌─────────── ROUTER (rules first, model fallback) ───────────┐
   ▼                        ▼                                   ▼
 RAG pipeline         Fixed workflows                    Investigation AGENT
 (policy/product)     (card block, dispute file)         (LangGraph, checkpointed)
   │                        │                                   │
   └────────────┬───────────┴───────────────┬───────────────────┘
                ▼                           ▼
        KNOWLEDGE LAYER                TOOL LAYER
   vector (policies, hybrid+rerank)   MCP gateway: authN/authZ/audit
   knowledge graph (cust-acct-txn)    core banking · CRM · card system
   SQL semantic layer (metrics)       tools: read / mutating / irreversible
   live APIs (balances)
   
 Cross-cutting: harness bounds · guardrails · traces · evals · budgets · kill switch
```

Narrate the shape in Ch6 terms: API answers in milliseconds with a job_id; the queue absorbs; workers think; progress streams; nothing slow sits on the request path.

## Step 4 — Deep dives (the interviewer picks; be ready for all)

**The agent loop & harness (Ch2/4/5).** Investigation agent = LangGraph with typed state, checkpointer, bounded loops, interrupt before any mutating action. Harness policy as data: tool grants, max 12 iterations, 60k token budget, fail closed.

**Knowledge routing (Ch10–12).** "Why did this customer's EMI bounce?" decomposes: graph (linked accounts/mandates), SQL (payment history), vector (policy on bounced mandates), API (current balance). Rules route the head; model decomposes the tail; evidence is graded before synthesis; "insufficient evidence" is a legal answer. Entitlements enforced inside each source (RLS, ACL filters) — never in the prompt.

**Context & caching (Ch8/18).** Budgeted assembly per step; stable prefix (system + tools) first for prompt-cache hits; history summarized past 8 turns; semantic caching for the FAQ-shaped head of traffic (embed query → serve validated cached answer at ~zero cost, TTL-bound and entitlement-checked). Two caches, two purposes: prompt cache cuts token cost inside runs; semantic cache eliminates runs.

**HITL & autonomy (Ch20).** Reads L3; recommendations L3 (drafts by nature); customer comms L2; card block L2 with the *customer* as approver in-app (elegant: the affected party approves); money movement — not the platform's. Override rates monitored.

**Failure modes (Ch18) — raise unprompted.** Model outage → fallback chain, eval-gated; tool flaky → circuit breaker; run crash → checkpoint resume; malformed output → one repair pass then fail closed with state preserved; runaway cost → budget rails at 80/100%.

**Security (Ch19) — raise unprompted.** Injection via a dispute description or uploaded document is *expected*: trust-labeled context (retrieved/user content can never trigger mutations without HITL), least-privilege grants per sub-agent, egress allowlists, agent NHIs with kill handles. State the blast radius sentence.

**Evals & rollout (Ch17).** Golden suite from pilot traces, judge calibrated on ops-staff labels, routing accuracy tracked separately, canary evals on sampled live traffic; ship L1 → earn L2/L3 with override-rate history. Numbers, not vibes, gate each autonomy step.

## Step 5 — The 45-minute clock

Clarify 3' → ladder placement 2' → high-level 8' → two deep dives 20' (follow the interviewer) → failure/security/governance 7' → cost & rollout 5'. If time collapses, the ladder placement + async backend + unprompted guardrails are the three things that must survive.

---

# Part B — The Industry Case: the full stack in production

## Anchor case: Walmart's AdaptJobRec (career recommendation agent)

Walmart Global Tech published a system that is almost a checklist of the modern stack — and its headline number is an *architecture* result, not a model result: **response latency cut by up to 53.3%** while improving recommendation quality.

| Stack element (your list) | How Walmart did it | Our chapter |
|---|---|---|
| **Routing / selective agency** | A query-complexity classifier decides: simple queries take a fast deterministic path; only complex ones invoke agentic reasoning. The 53% latency win comes largely from *not* running the agent when a workflow suffices | Ch1, Ch3, Ch12 |
| **Workflow + agentic mix** | Fixed recommendation pipeline for the head of traffic; multi-step agent for ambiguous career questions | Ch1, Ch4 |
| **Knowledge graph** | Roles, skills, and career pathways as a graph — recommendations are traversals (role → adjacent skills → target roles), which also makes them explainable | Ch11 |
| **Context engineering + memory** | Conversation state distilled per turn; the graph supplies compact, structured context instead of stuffed documents | Ch8, Ch9 |
| **Caching / semantic layer** | Fast-path answers effectively served from precomputed/cached structures rather than fresh reasoning | Ch18 |
| **Harness** | The classifier, the bounded agent path, and the fallback to the simple path are exactly "deterministic bounds around a stochastic core" | Ch5 |

The architect's lesson to quote in interviews: **the biggest documented wins come from deciding when NOT to run the agent.** Selective agency is the pattern; everything else supports it.

## Supporting cases (one line each, all documented)

- **Klarna** (customer service): assistant handled work equivalent to ~700 human agents in month one — the business case for the Ch6 backend + Ch17 evals discipline at scale.
- **Uber — QueryGPT**: natural language → SQL with *routing across schema domains* and curated semantic context instead of raw schemas — the Ch12 semantic-layer argument, from a company that measured it.
- **Simply AI** (voice agents): GraphRAG over a Neo4j graph to cut hallucinations in real-time calls — Ch10+11 hybrid retrieval under a latency budget.
- **Syntes AI** (enterprise digital twin): graph + Cypher translation with logging and approvals — Ch11 explainability + Ch20 governed actions.
- **Mem0** (memory layer): graph-based selective memory extraction cutting token usage across long workflows — Ch9's pipeline as a product.
- **Kambui Nurse** (tech-debt agent): deterministic Cypher over an ephemeral graph in CI, exposed via MCP — reliability by *removing* LLM inference from the load-bearing step; the Ch1 dial pushed deliberately left.
- **OpenAI — Codex building an internal product**: ~1M lines of code and ~1,500 PRs, zero hand-written, three engineers at 3.5 PRs/day — the Ch5 harness-as-infrastructure argument proven at a lab's own engineering org, and a live example (their own "minimal blocking gates" call) of exactly where a bank's gate placement has to diverge from theirs.

## The meta-pattern across every case

Read the six cases together and one shape repeats: **classify → route → deterministic where possible → agentic where necessary → graph/semantic layer for structure and explainability → cache the head of the distribution → bound and observe everything.** That is precisely the reference architecture of Ch21 — which is the point: the curriculum isn't a theory of how this *should* work; it's a description of how the systems that work *do*.

## Lab (capstone-level)

Recreate selective agency on your banking platform: add a complexity classifier in front of the Ch12 router, serve the simple 70% via cached/workflow paths, and measure — latency, cost per query, and answer quality across both paths. Present it Walmart-style: one number for leadership ("X% latency/cost reduction, quality flat or up"), one architecture diagram for engineers.
