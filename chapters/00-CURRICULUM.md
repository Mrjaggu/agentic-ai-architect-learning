# The Agentic AI Architect Curriculum

**Positioning goal:** Enterprise Agentic AI / AI Platform Architect — someone who designs the complete ecosystem (agents, orchestration, knowledge, tools, governance, evals, observability, security, production deployment), not another framework developer.

**Running thread:** every chapter adds a layer to one evolving design — **"An Enterprise Agentic AI Platform for a Bank"** — so by the end there is both deep conceptual confidence and a reference architecture you can defend in interviews, leadership discussions, and on LinkedIn.

**How we work each chapter (agreed):**
1. Interactive deep-dive discussion in conversation first
2. Then distilled into a polished chapter file in this folder before moving on
3. Labs are **multi-framework**: LangGraph as the primary reference stack, with comparative exposure to CrewAI, OpenAI Agents SDK, and MCP — because an architect compares frameworks; a developer marries one
4. No fixed timeline — the progress tracker below tracks where we are

**Per-chapter format:**
Concept → Why the industry needed it → Architecture → Design decisions → Trade-offs → How companies actually implement it → Hands-on lab → **Architect's take: how would you design this for a regulated bank?** → **Governance & security lens** — every chapter, not just Module F, closes by asking what can go wrong at this layer, which controls apply, and what question a risk review would ask — so governance and security are design-time habits, weighed in the same breath as scaling. Chapters stay architect-level but each core concept carries a small code/config snippet to visualize it; full runnable implementations live in the labs (specs in each chapter) and in Gulli's book (see Reference Shelf).

---

## Module A — Foundations & Agent Design

### Chapter 1: The Evolution of AI Systems
GenAI → LLM apps → RAG → Agents → Agentic workflows → Agentic systems → Enterprise agent platforms. Why RAG alone wasn't enough; what actually makes something an agent; agent vs workflow vs chatbot vs autonomous system; where agents should NOT be used. The architectural limitation that forced each generation to emerge.

### Chapter 2: Anatomy of an AI Agent
The agent loop: reasoning, planning, tool selection, action, observation, reflection. Memory and state as first-class components. LLM ≠ agent — the LLM generates intelligence; the agent uses it to act. Lab: build a minimal agent loop from scratch (no framework) so every framework afterwards is demystified.

### Chapter 3: Agent Design Patterns — and When NOT to Use Them
ReAct, Plan-and-Execute, Reflection, Router, Supervisor, Hierarchical, Human-in-the-loop, Event-driven, Parallel, Sequential pipelines. The architect-level content: a decision framework for choosing patterns — and the strong default of *one good agent + tools* over premature multi-agent. Lab: same task implemented as ReAct vs Plan-and-Execute; compare cost, latency, failure modes.

---

## Module B — Orchestration, Harness & Backend Systems

### Chapter 4: Agent Graphs & State Machines
Nodes, edges, conditional routing, loops, checkpoints, interrupts, retries, durable execution. The central design question: should intelligence control the workflow, or should deterministic software control the workflow? Lab: LangGraph deep dive; then the same orchestration sketched in OpenAI Agents SDK and CrewAI to compare orchestration philosophies.

### Chapter 5: Agent Harness Engineering
The environment around the agent that makes it reliable. Core principle: *put a frontier model into a badly designed agent system and you get a more articulate failure* — model quality matters less than the scaffolding around it. The five harness components as one interconnected design: tools, prompts, memory, orchestration, and human-in-the-loop placement. Plus: context assembly, tool policies, execution sandboxing, permissions, retries, timeouts, state persistence, cost control. Why the industry shifted from "clever prompts" to "reliable agent infrastructure."

### Chapter 6: Backend & System Design for Agent Services
How agent workloads differ from web request workloads — long-running (90s+), asynchronous, iterative, expensive to retry — and why the naive synchronous `POST /agent → agent.run()` pattern fails six ways: held-open connections, jobs lost on client disconnect, expensive retries, spinner-with-no-feedback UX, no cancellation, no progress recovery. The production reference architecture: async job submission API, job queues, worker pools, streaming (SSE/WebSockets) for progress, structured output handling, session management, checkpointing for resume, cancellation, rate limiting and cost controls. Lab: convert a synchronous agent endpoint into a queue + worker + streaming architecture (FastAPI-style, framework-agnostic principles).

### Chapter 7: Deploying Agent Systems — IaC, CI/CD & Cloud Runtime 🆕
Taking the Chapter 6 architecture to the cloud. The fast-path/slow-path split as deployment shape: three containers (frontend / API / worker) where only the frontend is internet-reachable and the worker has no address at all — it only pulls from the queue; API and worker run the *same image* with different start commands so they can never drift; worker sized ~2x the API because it holds whole agent runs in memory. Infrastructure as Code: Terraform with workspaces (one config → isolated dev and prod stacks; never copy-paste environment folders — drift is found during incidents), remote state with locking, run-once bootstrap. CI/CD: GitHub Actions → AWS via OIDC (no long-lived cloud secrets anywhere; the environment-vs-branch token-subject trap), checks-then-deploy pipelines, approval gates as the entire promotion policy (`environment: prod` + required reviewer), tag-based prod promotion, never cancel a running deploy (state locks). Identity as the security boundary: execution role vs task role — "if it fails before the first log line, it's the execution role" — and the architect's line: *restricting an agent in the prompt is a request; restricting it in the task role is a fact.* Model access via workload identity (Bedrock-style, zero API keys); choosing models that *converge* in long tool-calling loops, not just emit valid tool calls. Production wiring: structured JSON logs → metric filters → alarms (an alarm on a pattern your logs don't emit can never fire), budget alarms because agent stacks spend quietly, tracing with spans + callbacks + explicit flush in background workers, and the verification rule — a green pipeline is not proof; run one real job end-to-end, because nothing before a real job ever calls the model. Testing agent apps in CI: don't test what the model says (non-deterministic → ignored suite); test the machinery — state transitions, result parsing, truncation — and that SDKs import inside the built image. Lab: deploy the Chapter 6 stack to ECS/Fargate with Terraform + GitHub Actions across dev and prod. Ties forward to Ch16 (tracing), Ch17 (evals vs CI testing), Ch19 (identity-based agent security).

### Chapter 8: Context Engineering
The successor to prompt engineering: what should the agent see at this exact moment? Context selection, prioritization, compression, pruning, summarization, token budgets, long-context strategies, sub-agent context isolation. Lab: instrument a real agent's context window and optimize it.

### Chapter 9: Memory Architecture
Short-term, working, long-term, episodic, semantic memory — and when agents should NOT remember. The 2026 memory-framework landscape (Mem0, Letta, Zep, LangMem, Cognee) as an architect's comparison, not a tool tour. Privacy, staleness, wrong personalization, and security risks of bad memory design. Architect's take: memory design under RBI/DPDP constraints in a bank.

---

## Module C — Knowledge Architecture (your named focus area)

### Chapter 10: Enterprise RAG, Properly
Beyond naive RAG: chunking strategy as a design decision, hybrid search, reranking, metadata filtering, freshness, evaluation of retrieval quality, re-indexing without downtime. Where RAG sits as ONE knowledge source among several.

### Chapter 11: Knowledge Graphs & Graph RAG
Ontologies, entity relationships, graph databases, when a graph beats a vector store, Graph RAG and hybrid vector+graph retrieval. How to structure graph knowledge efficiently: schema design, entity resolution, incremental graph construction, cost of maintenance. Lab: build a banking-domain graph (Customer–Account–Transaction–Loan–Collateral–Merchant) and run graph-augmented retrieval against pure vector retrieval.

### Chapter 12: Agentic Retrieval & Knowledge Routing
The agent decides which knowledge source to use: vector DB vs knowledge graph vs SQL/semantic layer vs live APIs. Query planning, multi-hop retrieval, self-correcting retrieval. This chapter turns Modules B+C into one system — the Knowledge Router that becomes Portfolio Project 2.

---

## Module D — Tools, MCP & Multi-Agent

### Chapter 13: Tools, Function Calling & Agent Skills
Tool schemas as API design, structured outputs, tool selection failure modes, idempotency, tool result design (what the model should see back). Designing tools an LLM can actually use well. Plus Agent Skills (the SKILL.md open standard): packaged procedural knowledge with progressive disclosure — MCP connects, skills instruct — and their governance as a capability class.

### Chapter 14: MCP, A2A & the Agent Protocol Stack
MCP architecture: servers, clients, resources, tools, prompts, discovery, auth. Then the wider 2026 protocol stack an architect must be able to map: A2A (agent-to-agent), plus the emerging edges — AG-UI/A2UI (agent-to-user-interface), WebMCP, ACP/ANP — and which will matter for enterprises vs which are noise. The enterprise pattern: an MCP gateway in front of CRM / core banking / data platforms, with authentication, authorization, and audit at the gateway. Lab: build an MCP server for a mock core-banking API and put a policy-enforcing gateway in front of it.

### Chapter 15: Multi-Agent Systems
Supervisor, specialization, delegation, shared state, communication, conflict resolution, parallel execution — and the honest question first: do you actually need multiple agents? Framework comparison lab: the same multi-agent design in LangGraph vs CrewAI vs OpenAI Agents SDK, with an architect's evaluation matrix.

---

## Module E — Production AI (the credibility module)

### Chapter 16: Agent Observability
Beyond logs/metrics/tracing: agent trajectories, spans across LLM calls and tool calls, token/cost/latency accounting, tool failure tracking, hallucination surfacing. Logs say a job ran; traces say what the agent actually did — a bad answer without an error looks like success in the logs. Lab: instrument the banking agent with OpenTelemetry-style tracing and a LangSmith/Langfuse-class tool.

### Chapter 17: Evals
The biggest missing skill in the market. Outcome evals, trajectory evals, tool-selection evals, safety evals, cost and latency evals; LLM-as-judge design and its failure modes; building eval datasets from production traces (traces → test suites) and eval-driven development as a working method; the 2026 tool landscape (LangSmith, Langfuse, Arize Phoenix, DeepEval, Braintrust) as an architect's comparison; regression gates in CI. Directly extends what you already built for Siddhi's quality scoring — this chapter converts that experience into portfolio language.

### Chapter 18: Reliability & Cost Engineering
Deterministic boundaries, structured output validation, retries, fallback models, circuit breakers, idempotency, error recovery, graceful degradation, model routing for cost, caching, prompt caching economics. Making an agent something an SRE team will accept in production.

---

## Module F — Governance, Security & the Platform (capstone)

### Chapter 19: Security & Guardrails
Prompt injection, tool poisoning, data exfiltration, excessive autonomy — anchored to the OWASP Top 10 for Agentic Applications (2026). Agent identity as non-human identity (NHI) governance: credentials, scoping, rotation, and lifecycle for agents as first-class identities. Layered defense: input guardrails → agent → authorization → tools. RBAC/ABAC for tools, least-privilege tool grants (the Ch7 task-role principle generalized), auditability. Written for a regulated-bank threat model.

### Chapter 20: Autonomy Levels, Human-in-the-Loop & Governance
The autonomy ladder (assist → suggest → execute-with-approval → autonomous) and how to assign levels per action class (read customer data vs generate recommendation vs move money). Approval workflows, audit trails, model risk management — including RBI's FREE-AI framework (Aug 2025) and the 2026 draft Model Risk Management guidance (board-level MRMF, AI kill switches, third-party accountability) as the concrete regulatory anchor, plus DPDP and EU AI Act awareness.

### Chapter 21: The Enterprise Agentic AI Reference Architecture
The capstone. Layered architecture — Experience → Agent → Orchestration → Knowledge → Tools → Enterprise systems — with cross-cutting security, observability, evals, governance, and cost. Deliverable: a polished reference-architecture document + diagram set you can use in interviews and internal architecture forums.

---

## Portfolio Projects (built along the way, not at the end)

**Project 1 — Enterprise Banking Agent Platform** ⭐ flagship
Router + specialized agents (loan / account / card) with graph orchestration, RAG, MCP tool layer, memory, guardrails, observability, evals — served through the async queue + worker + streaming backend from Chapter 6, deployed with the IaC/CI-CD pipeline from Chapter 7. Starts in Module B, hardened in Modules E–F.

**Project 2 — Knowledge Intelligence Agent**
Agentic knowledge routing across Vector / Graph / SQL. Built in Module C — demonstrates Graph RAG, hybrid retrieval, and knowledge architecture (your named strength area).

**Project 3 — Agent Evaluation & Observability Mini-Platform**
Answers: which agent failed, why, at which step, with which tool, at what cost. Built in Module E — the rarest and most senior-signaling of the three.

---

## Framework Exposure Map (multi-framework lab plan)

| Framework / stack | Role in curriculum | Chapters |
|---|---|---|
| No framework (raw loop) | Demystification | 2 |
| LangGraph (+ LangSmith) | Primary reference stack | 3, 4, 12, 15, 16, 17 |
| FastAPI + queue/worker stack | Agent backend reference | 6, and Project 1 |
| Terraform + GitHub Actions + ECS/Fargate + Bedrock | Deployment reference | 7, and Project 1 |
| OpenAI Agents SDK | Orchestration-philosophy contrast | 4, 15 |
| CrewAI | Role-based multi-agent contrast | 15 |
| MCP | Enterprise tool layer | 14, and Project 1 |

---

## Reference Shelf

Two books mapped against this curriculum (both cross-checked 2026-08-29; their unique contributions folded into the chapters noted):

- **Gulli, *Agentic Design Patterns*** (Springer) — 21 hands-on patterns with runnable code; best used as the *implementation companion* to Modules A–D. Unique material absorbed: goal setting & monitoring + reasoning techniques (→ ch2), prompt chaining & prioritization (→ ch3), learning & adaptation (→ ch9), exploration/discovery + GUI agents (→ ch21 watchlist). Its chapters on tool use, MCP, A2A, memory, guardrails, and evals pair directly with ch13, 14, 15, 9, 19, 17.
- **Biswas & Talukdar, *Building Agentic AI Systems*** (Packt) — strongest on classical foundations and trust: deliberative/reactive/hybrid architectures + BDI (→ ch2), knowledge representation & reasoning theory (background for ch11), the Coordinator-Worker-Delegator model (→ ch3/15), and transparency/explainability/bias (→ ch20). Read Part 1 for interview-grade theoretical vocabulary; skim Part 3 alongside Module F.
