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

## Case: the Banking Operations Agent — this course's reference implementation, assembled

Every chapter so far has leaned on the same handful of recurring examples — the dispute-investigation agent, the card-limit-change request, the R. Kapoor relationship-outreach pipeline, the fraud flag that outlived its evidence — treated one at a time as each chapter's worked illustration of its own layer. Put back together, they aren't four unrelated stories; they're one bank's operations platform, and this is what it looks like assembled, with the mechanism each dimension draws from named explicitly.

**Architecture.** The platform is Ch1's ladder, populated with real workloads instead of hypothetical ones. A balance lookup is deterministic RAG. Ch21 §3's own worked request — "should we raise customer X's card limit?" — is a *workflow*: LLM steps inside a compliance-fixed sequence (plan → gather evidence → synthesize a recommendation → interrupt for RM approval → execute idempotently). The dispute-investigation loop from Ch2 §2 — the ReAct trace against customer 4471's ₹4,300 POS charge — is a genuine *agent*, because the order of `get_transactions` → `get_customer_profile` → `search_policy` → `create_case` isn't fixable in advance; that same trace gets re-examined twice more, as Ch5's harness-hardening subject and then Ch18 §3's reliability-and-cost subject. And the R. Kapoor relationship-outreach pipeline from Ch15 §3 — Signal Scout → Counterparty Enricher → Relationship Strategist — is a strict *pipeline* multi-agent topology, justified on Ch15 §1's permission-boundary and context-isolation grounds, not chosen because three agents felt more sophisticated than one. A router (Ch12) sits in front of all three shapes, and the same harness (Ch5) — typed state, checkpointer, bounded iterations, interrupt-before-mutation — wraps whichever one is currently running.

**Tools.** The dispute agent's four tools are exactly what Ch5's per-tool-grant discipline looks like in practice: `get_transactions`, `get_customer_profile`, `search_policy`, `create_case`, and nothing else — "grant everything, let the model figure it out" was never on the table. Ch15's pipeline pushes the same minimalism up to the agent level: Signal Scout holds only the external news-retrieval tool, Counterparty Enricher holds only the internal KYC-cleared lookup, and the Relationship Strategist holds no tool at all — three agents, three separately bounded blast radii, none powerful enough alone to leak the other's job. The card-limit workflow's mutating step sits behind the same capability-grant model Ch13's registry describes: a tool the harness will execute, not a capability the model talks itself into.

**Memory.** This is where Ch9 §2's fraud-flag story stops being a cautionary anecdote and becomes the platform's governing schema. Every memory record this system writes carries Ch9 §5's fields — `customer_id` partition key, `source_ref` provenance, a `confidence` score, a `purpose` tag, and a `ttl_days` that defaults short for anything risk-adjacent. That is the direct fix for what happened in Ch9's incident: an unattributed, unconfirmed inference (`"customer exhibits fraud-risk transaction pattern"`) survived eight months and fourteen retrievals with no expiry, quietly biasing a loan pre-approval agent it had no evidentiary connection to. Under this schema the same inference either fails the extraction allowlist outright or lands with low confidence and a short TTL — it decays before it can do that. The dispute agent itself needs almost none of this: being a bounded task rather than an open conversation (Ch8 §5), its working memory is plan-plus-latest-state, discarded at case close — Ch9's governance is what applies to whatever, if anything, is written past that boundary.

**Knowledge.** Ch21 §3's card-limit walkthrough is knowledge routing in miniature: policy from the vector store, exposure from the knowledge graph, payment history from the SQL semantic layer, current balance from a live API — fanned out, graded, and synthesized with per-claim citations, where "insufficient evidence" is a legal answer rather than a failure to route around. The dispute agent's `search_policy` step draws on the same knowledge layer under a narrower need, and it's also where Ch8 §2's staleness incident actually happened: a retrieval index three weeks behind a policy update let a superseded, more generous fee-waiver threshold get retrieved as if it were current, and the model reasoned correctly given a false premise — approving waivers policy no longer permitted, consistently, until a routine audit sample caught the mismatch. The fix now threads through every knowledge call in this system: freshness as a first-class field, an `is_fresh()` filter that prunes a stale document before the model ever sees it (Ch8 §4), not a hope that the model notices a chunk's age on its own.

**Evals.** The card-limit action class is Ch20's numbers-not-vibes rule made concrete: `generate_recommendation` sits at L3 with an explicit `eval_gate: ">=0.92"` (Ch20 §2b), and the limit change itself stays L2 regardless of how high that score climbs, because the harm is irreversible-for-the-customer, not because the model is untrusted — level and eval score answer different questions. The R. Kapoor pipeline is graded per-stage as well as end-to-end, and that distinction is the whole lesson of Ch15 §4's incident: a stage-level eval on Agent 2's identity resolution would have caught the outgoing-CFO mixup that an end-to-end "does this look like a plausible outreach recommendation" eval sailed straight past, because every individual agent's output was locally correct. Override rate (Ch20 §3) is the live cross-cutting signal on all three workloads: a 0% override on card-limit approvals means that checkpoint has gone decorative; a spike after a pipeline change is the canary that something in the resolution logic just regressed.

**Security.** The dispute agent is Ch19 §2's worked case for trust labeling: the customer's own dispute description and any retrieved policy content are both marked `untrusted` at assembly time (Ch8's assembler enforcing Ch19's policy), and a mutating tool — `create_case`, and certainly anything in the card-block path — cannot be triggered by a goal that originated in that untrusted content without a human in the loop. Each of the R. Kapoor pipeline's three agents is its own NHI with its own owner and its own short-lived, narrowly scoped credential (Ch19 §3): Signal Scout's identity can reach the news tool and nothing internal; Counterparty Enricher's can reach the KYC-cleared lookup and nothing external. A compromise of either has exactly the short blast radius Ch19 §2b's YAML is built to demonstrate — which is also, not incidentally, why the R. Kapoor mixup stayed an embarrassment and never became a leak: neither agent held a credential broad enough to make it one.

**Failure modes.** Ch18 §3 hardened this exact dispute agent twice, and the sequence matters: the first pass found a naive retry wrapper blind-retrying a malformed `check_policy` output three times at full token cost before failing — fixed by splitting retriable (timeout, rate-limit) from reroutable (schema mismatch → one repair prompt) from terminal (stop, checkpoint, surface). The second pass found no circuit breaker on the policy-lookup dependency, so its own bad ten minutes got compounded by every new run retrying against it at full cost — fixed by a breaker that fails fast instead. The resulting fallback chain — one repair pass, then an eval-gated fallback model, then a clean checkpointed failure with state preserved for resume — is what now sits under the card-limit workflow's LLM steps too, because Ch18 §4's incident found that an unvalidated fallback model isn't just a reliability gap, it's an un-reviewed policy decision wearing a reliability costume.

## Case: Anthropic's multi-agent research system — a real, published deep-research architecture

Unlike the banking case above, this one is externally documented, not assembled from this course's running examples. The source is Anthropic's own engineering blog, "How we built our multi-agent research system," published June 13, 2025 by Jeremy Hadfield, Barry Zhang, Kenneth Lien, Florian Scholz, Jeremy Fox, and Daniel Ford — a genuine production postmortem-style writeup of the system behind Claude's Research feature, not a marketing page, and the numbers below are quoted or closely paraphrased from it directly.

**Architecture.** An orchestrator-worker pattern: a lead agent (Claude Opus 4) reads the query, develops a research strategy, and spawns subagents (Claude Sonnet 4) that explore different angles in parallel, each returning a distilled result rather than a raw transcript. Anthropic's own internal eval found this configuration beat a single Opus 4 agent working alone by **90.2%** — a result in the same family as Walmart's selective-agency win above, except pointed the opposite direction: Walmart's number comes from *not* running the agent when a workflow suffices; this one comes from splitting the agent into pieces once a task is genuinely research-shaped. Both are evidence for the same underlying claim — architecture, not model choice, is where the biggest documented gains sit.

**Tools.** Subagents are prompted with explicit tool-selection heuristics — examine everything available first, match tool to intent, prefer a specialized tool over a generic one, use broad web search only for genuinely broad exploration — because a subagent with an unclear "when do I use X vs Y" rule burns turns finding out empirically. Anthropic built a *tool-testing agent*: given a flawed MCP tool, it exercises the tool, observes where it fails, and rewrites the tool's own description to route future agents around the failure — a change that alone produced a **40% decrease in task completion time** for later agents using the corrected description, which is a striking, very literal instance of Ch13's "the tool description is part of the interface" argument. Parallelism compounds on top of that: the lead agent spins up 3–5 subagents concurrently rather than serially, and each subagent fires 3+ tool calls in parallel rather than one at a time — together cutting research time on complex queries by **up to 90%**.

**Memory.** The lead agent's context window caps at 200,000 tokens, and a long research task can genuinely exceed it — so the lead agent's standing practice is to write its plan to an external memory store *before* that happens, specifically so the plan survives truncation rather than being silently lost mid-task. Subagents take the isolation a step further: each spins up with a clean, empty context rather than inheriting the accumulated conversation, and continuity across that reset comes from a deliberately-written handoff (the retrieved plan, a task description) rather than from shared history. It's the same *sub-agent isolation* mechanism Ch8 §5 names as "the strongest tool" for context management and Ch15 §1 names as a first-class justification for splitting agents at all — here it's solving a different failure than either chapter's example: not poisoning, and not a permission boundary, but a hard token ceiling that a single long-running agent would otherwise walk straight into.

**Knowledge.** This system's knowledge layer is thinner than the banking platform's — open web search plus a handful of specialized tools, not a routed stack of vector store, knowledge graph, and semantic layer (Ch12). What it does carry over is source *grading*: subagents are steered toward primary and authoritative sources over lower-quality secondary ones, the same instinct behind Ch11's graph-as-explainability argument, done here with a lighter-weight heuristic instead of a graph structure. The gap is worth naming for architects, not glossing over: a bank's research agent over internal knowledge would need Ch12's full routing discipline; a general-web research agent apparently doesn't, and knowing which of your stack's layers a given workload actually needs is itself an architecture decision.

**Evals.** Anthropic converged on a single LLM-as-judge call per output, scoring 0.0–1.0 plus a pass/fail grade, against a rubric of factual accuracy, citation accuracy, completeness, source quality, and tool efficiency — and found that configuration more consistent and better human-aligned than more elaborate judging setups, which is Ch17 §3's "LLM-as-judge, done properly" argument validated at a lab's own scale. The team's development loop leaned on a small, fixed set of roughly 20 real-usage queries early on, finding that this alone made most regressions visible — a cheap, high-signal habit before a full golden suite exists. And critically, human evaluation kept surfacing failures the automated evals missed entirely: hallucinated answers on unusual queries, silent system failures, and a source-selection bias toward SEO-optimized content farms over academic PDFs and personal blogs that no rubric dimension was watching for — the concrete version of Ch17 §6's warning that a single blessed metric gets gamed and a held-out, human-reviewed set stays necessary regardless of how good the judge gets.

**Security.** Here the published writeup itself is thin, and it's worth saying so rather than papering over it: Anthropic's piece discusses reliability at length but does not substantially address prompt injection via search results, adversarial or malicious web content, or how a subagent might be manipulated by the pages it retrieves — it names only "deterministic safeguards like retry logic and regular checkpoints" as guardrails, which is a reliability control, not a security one. That gap is instructive on its own terms: a research agent that autonomously browses the open, untrusted internet is close to a textbook prompt-injection surface — retrieved web content steering a tool call — and applying this course's own framework rather than the source's, the missing piece is exactly Ch19 §2's trust-labeling discipline: content pulled from search results should enter a subagent's context labeled `untrusted`, with any tool capable of a side effect (as opposed to more searching) barred from firing on a goal that originated there without review. A bank adapting this architecture cannot skip that layer just because the source didn't need to describe it.

**Failure modes.** Early versions of the system over-corrected in both directions before the effort-scaling heuristic settled: agents that spawned 50 subagents for queries a single agent could have answered, agents that scoured the web indefinitely for sources that didn't exist, and subagents that distracted each other with excessive status updates — a coordination failure, not a capability one. The fix was an explicit effort budget by query shape: roughly 1 agent and 3–10 tool calls for simple fact-finding, 2–4 subagents at 10–15 calls each for comparisons, 10+ subagents with clearly divided responsibilities only for genuinely complex research. On the reliability side, the team's finding is the sharpest line in the piece: "the compound nature of errors in agentic systems means that minor issues for traditional software can derail agents entirely" — because agents hold state across long tool-call chains, a transient failure without durable execution can be catastrophic, so the system resumes from the point of failure rather than restarting, ships changes via rainbow deployments so a version shift never disrupts an in-flight long-running agent, and leans on full production tracing because agents are non-deterministic between runs even on identical prompts, which makes debugging structurally harder than for deterministic software. And the number that ties failure modes back to economics: agents run roughly **4×** the token cost of a single chat turn, multi-agent systems roughly **15×** — Anthropic's own stated conclusion is that this architecture is only worth it when a task's value clears that multiplier, which is the token-cost mirror of the Walmart lesson above: know when *not* to spin up the whole apparatus, on a cost axis instead of a latency one.

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
