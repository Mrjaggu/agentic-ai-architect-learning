# Interview Q&A Bank — What They Actually Ask

> Compiled from published 2026 interview banks, system-design interview guides, and community discussions, mapped to our chapters. Answers are deliberately short — the 30-second version you say first; every chapter has the depth behind it. The published banks are strong on basics and weak on memory, MCP/A2A, context engineering, and structured system design — which is exactly where you'll differentiate.

---

## Ch 1 — Evolution & Fundamentals

**Q. What is agentic AI, and how does it differ from a chatbot or a RAG app?**
An agent is what you get when control flow moves from code into the model — it decides what to do next in a loop, instead of following a fixed pipeline. A chatbot generates replies; RAG retrieves-then-generates on one hardwired path; an agent can decompose, recover, choose sources, and act.

**Q. Why isn't RAG enough? When would you still choose plain RAG?**
RAG is a fixed pipeline: it can't decompose multi-part questions, can't recover from bad retrieval, can't choose between knowledge sources, and can't take actions. I'd still choose it for stable, high-volume document Q&A — an agent there adds cost and non-determinism for nothing.

**Q. Agent vs workflow — how do you decide?**
Ask who should own control flow. If the task path is known in advance (compliance sequences, fixed processes), code owns it — that's a workflow, even with ten LLM calls inside. If the path genuinely can't be known upfront, the model owns it — that's an agent.

**Q. Where should agents NOT be used?**
Fixed-sequence regulated processes, latency-critical paths, high-volume/low-value queries, and anywhere the decision path must be exactly replayable for audit. Saying this unprompted signals seniority.

## Ch 2 — Agent Anatomy & Reasoning

**Q. Walk me through the agent loop.**
Reason over goal + state → choose an action from granted tools → the *harness* executes it (the model only emits a request) → result appended to context → reflect: done or loop. Bounded by max iterations, token budget, and timeouts — the model makes two decisions (what next, am I done); everything else is software.

**Q. What is chain-of-thought and why does it matter for agents?**
Making the model reason step-by-step before acting — it improves decision quality in the loop. The 2026 update: reasoning models internalize this as test-time compute, so the design question becomes which steps deserve a reasoning model at what token budget.

**Q. What's the difference between the system prompt and the user prompt?**
The system prompt sets durable identity, rules, and tool context — assembled by the harness, stable across turns (and cache-friendly). The user prompt carries the task. In agent systems both are just sections of a budgeted context assembly.

**Q. What is the context window and why does its size matter less than people think?**
It's the model's per-call input capacity. Bigger windows didn't solve the problem because reasoning degrades over mush, cost scales per call, and one poisoned chunk steers everything — hence context engineering.

## Ch 3 — Design Patterns

**Q. Which agent design patterns do you know, and how do you choose?**
ReAct, Plan-and-Execute, Reflection, Router, Supervisor, hierarchical, HITL, parallel, pipelines. Selection: is the path known (→ pipeline)? Can one agent + tools do it (→ strong default)? Do subtasks need different contexts or permissions (→ only then multi-agent)? Where are irreversible actions (→ HITL exactly there)?

**Q. How do you make an agent prioritize competing goals or tasks?** *(real question from published banks)*
Deterministically where possible — score tasks on urgency × value × cost in code — and use model judgment only for the ambiguous tail. Same principle as all agent control flow: give the model the decision only where judgment is genuinely required, and log the ranking either way.

**Q. When is multi-agent the wrong answer?**
When the split follows human org metaphors (researcher/writer/editor) rather than context, permission, cost, or parallelism boundaries. One good agent with tools beats ten agents talking — at 5–15× less cost.

## Ch 4 — Orchestration & Graphs

**Q. Why did graph-based orchestration (LangGraph-style) win for production agents?**
Graphs declare a legal state space: the model chooses among transitions you drew, and can't invent paths. That plus checkpoints, interrupts, and per-node retries gives enterprises the auditability and durability a raw loop can't.

**Q. How do you implement human-in-the-loop technically?**
Checkpoint + interrupt: the graph pauses at a declared node, state persists, a human approves or edits, execution resumes from the checkpoint. HITL is a graph feature, not a UI hack.

**Q. What happens when your agent crashes at step 7 of 9?**
With checkpointing, state persisted after each node means resume at step 7 — not re-run (and re-pay) the whole job. Without it, you have a demo. I'd also mention idempotent tools so redelivered work is safe.

## Ch 5 — Harness

**Q. What is an agent harness and why does it matter more than the model?**
Everything around the model that makes it reliable: context assembly, tool policy and execution, bounds, sandboxing, persistence, cost control, trace hooks. Same model, different harness → wildly different reliability; the model sets the ceiling, the harness sets the floor.

**Q. How do you stop an agent from looping forever or burning budget?**
Deterministic bounds enforced by the harness: max iterations, per-run token budget, wall-clock and per-tool timeouts, and convergence monitoring (repeated-action detection). Never rely on the model deciding to stop.

## Ch 6 — Backend

**Q. Why can't you serve an agent behind a normal synchronous API?**
Agent runs take minutes; a sync endpoint holds connections open, loses jobs on disconnect, re-runs expensive work on retries, can't stream progress, can't cancel, and loses everything on late failure. The fix: return a job_id in milliseconds, queue → worker pool, SSE progress events, checkpointed resume.

**Q. How do you handle idempotency?**
Idempotency keys on submission (retried submits return the same job), at-least-once queue delivery with idempotent job handling, and idempotent or deduplicated tool calls — critical when a duplicate job could duplicate a customer action.

**Q. How do you scale agent workers?**
On queue depth, not CPU — workers hold whole runs in memory (size ~2× the API), scale independently of the request path, with per-tenant fairness so one batch job can't starve interactive traffic.

## Ch 7 — Deployment

**Q. How would you deploy an agent system to production on AWS?**
Three containers: internet-facing frontend, thin API that enqueues, and a worker with no address at all — it only pulls the queue. Same image for API and worker, Terraform with workspaces for dev/prod, OIDC from CI (no cloud keys anywhere), model access via task-role identity (no API keys), approval gate on prod.

**Q. Your deployment is green but the agent fails on the first real request. What happened?**
Nothing before a real job ever calls the model — likely a missing task-role permission, un-enabled model access, or a lazily-loaded SDK missing from the image. That's why my deployment verification always includes one real job end-to-end, not just health checks.

**Q. Managed platforms like Bedrock AgentCore vs building your own?**
AgentCore packages the same layers (runtime, memory, gateway, identity, observability) as managed services — a strong default on AWS. I'd verify region/data-residency fit per service, watch consumption pricing at scale, and keep tool contracts MCP-standard as the exit hatch.

## Ch 8 — Context Engineering

**Q. What is context engineering and how is it different from prompt engineering?**
Prompt engineering asks how to phrase; context engineering asks what the model should see at this exact step — selection, prioritization, compression, pruning, budgets, sub-agent isolation, assembled deterministically each turn. It's an architecture discipline, not wording.

**Q. Your agent's context keeps growing across a 20-turn run. What do you do?**
Summarize resolved history, compress tool results at the source, enforce per-section token budgets, keep everything in state and retrieve detail back via tools. Target a flat context curve with unchanged task success — and measure it in traces.

## Ch 9 — Memory

**Q. How do you design agent memory — short-term vs long-term?**
Short-term is really state: session-scoped, checkpointed, dies with the run. Long-term is a pipeline — extract (by policy), consolidate (merge, resolve contradictions, expire), store typed records with provenance, retrieve filtered by partition *before* similarity. The write bar is higher than the read bar because memory mistakes persist.

**Q. How do you prevent memory from becoming a privacy problem?**
Allowlist extraction policy, purpose tags checked at retrieval, structural per-customer isolation (partition keys, not prompt discipline), TTLs, and provenance per memory so erasure can cascade to embeddings and summaries — DPDP's purpose limitation, minimization, and erasure as fields, not hopes.

## Ch 10 — RAG

**Q. What is RAG and what makes enterprise RAG hard?**
Retrieve relevant content, inject into context, generate grounded answers. Enterprise-hard parts: parsing quality, chunking as a design decision, hybrid (vector+keyword) search because queries are id-heavy, reranking, entitlement filtering at query time, effective-dating, and blue/green re-indexing.

**Q. Retrieval quality is bad. Walk me through your debugging.**
Eval set first (recall@k on golden questions), then isolate the stage: parsing loss? chunk boundaries? embedding mismatch? missing keyword leg? no reranker? filters too tight? Fix one variable at a time against the eval — never vibes.

## Ch 11 — Knowledge Graphs

**Q. When does a knowledge graph beat a vector store?**
When questions are about connection, not similarity: multi-hop traversals, aggregation over relationships, temporal linkage, and explanation-as-path (fraud rings, exposure). If it decomposes into joins-with-meaning, graph; into similarity, vectors.

**Q. How do you build an enterprise knowledge graph efficiently?**
Ontology first and small; load structured systems deterministically (80% of value, no LLM); LLM-extract only unstructured residue against the ontology with confidence thresholds; entity resolution is the hard part; incremental event-driven updates with temporal edges.

## Ch 12 — Agentic Retrieval

**Q. How does an agent decide which knowledge source to use?**
A routing layer over declared source contracts: rules for the head of the distribution, model-based decomposition for the tail — most real questions decompose across vector, graph, SQL, and live APIs, then synthesis with per-claim citations. Routing accuracy is its own eval; it's the cheapest quality lever in the stack.

**Q. What is self-correcting retrieval?**
Grade the evidence before generating: does this actually answer the question? On failure, rewrite the query, try the next-best source, or return "insufficient evidence" — never generate from garbage. It closes RAG's can't-recover gap.

## Ch 13 — Tools

**Q. What makes a good tool for an LLM agent?**
The description is the interface — when to use, when not, what comes back; tight schemas (enums over free strings); results shaped for decisions, not dumps; errors written as recovery instructions; and read-only/mutating/irreversible annotations the harness turns into policy.

**Q. What are Agent Skills, and how do they differ from tools and MCP?**
Skills are packaged procedural knowledge — a SKILL.md of instructions plus optional scripts, loaded progressively (name/description at startup, full content only when the task matches). Tools/MCP give the agent *access*; skills give it *know-how* — MCP connects, skills instruct. Governance-wise a skill is like a tool grant: versioned, owned, reviewed before install, because bundled instructions + scripts are an injection vector with packaging.

**Q. What are tool use and function calling?**
The model emits a structured `{name, arguments}` request against declared JSON schemas; the harness validates, authorizes, executes, and returns the result into context. The model never executes anything — that boundary is where security lives.

## Ch 14 — MCP & A2A

**Q. What is MCP and why did it win?**
The Model Context Protocol standardizes agent↔capability connections — servers declare tools/resources/prompts, any MCP host can use them, turning N×M integrations into N+M. Enterprises add a gateway in front for authN/authZ/audit as one choke point.

**Q. MCP vs A2A?**
MCP is vertical (agent to systems); A2A is horizontal (agent to agent) — Agent Cards for discovery, task lifecycles, opaque internals. They compose: my loan agent uses MCP to reach the LOS and A2A to answer another agent's request.

## Ch 15 — Multi-Agent

**Q. Design a multi-agent system. When and how do you split?**
Split only on context isolation, permission boundaries, model/cost tiers, or true parallelism. Fixed topology (who may talk to whom is an authz matrix), typed delegation contracts (goal, constraints, output schema, budget), supervisor holds no credentials, per-agent traces and evals.

**Q. What are the classic multi-agent failure modes?**
Lossy delegation (worker succeeds at the wrong task), contradictory results without a resolution policy, shared-state races, cost multiplication, and un-debuggable provenance. Each has a named mitigation — contracts, tiebreak policy, write scopes, budgets, per-agent tracing.

## Ch 16 — Observability

**Q. What is tracing? What are spans?** *(verbatim from published banks)*
A trace is the tree of everything one run did; spans are its nodes — each LLM call, tool call, and sub-agent with tokens, cost, latency, and status. For agents, the trajectory (the ordered decisions) is the debugging unit, because a wrong answer can hide inside an all-green run.

**Q. What would you monitor for an agent in production?**
Beyond error rate and p95: cost per run, turns per run, repeated-action/convergence failures, tool error rates by class, cache hit rate, outcome signal, HITL override rate — with config fingerprints so regressions attribute to the change that caused them.

## Ch 17 — Evals

**Q. What are evals and how do you evaluate an agentic system?**
Dataset + scoring method + baseline + decision rule. For agents, layered: outcome (goal met?), trajectory (reasonable path?), tool selection, routing accuracy, safety, cost/latency — with LLM-as-judge for the subjective layers, calibrated against humans and decomposed into narrow criteria.

**Q. How do you test something non-deterministic in CI?**
Don't assert on model text — test the machinery deterministically, and gate quality statistically: run the golden suite, compare pass rates against baseline with enough N, block on regression. Production traces continuously feed the suites.

**Q. What are LLM-as-judge failure modes?**
Position bias, verbosity bias, self-preference for its own model family, and drift when the judge model changes. Mitigations: decomposed binary criteria, human calibration with reported agreement, evidence-cited verdicts, judge ≠ generator.

## Ch 18 — Reliability & Cost

**Q. How do you make an agent reliable enough for an SRE team?**
Deterministic contracts around every stochastic part: schema validation with one repair pass then fail-closed, nested timeouts, retries only for transient failures on idempotent ops, eval-gated fallback models, circuit breakers per dependency, and checkpointed clean failure — never failed-dirty.

**Q. Your agent bill doubled month over month. What do you do?**
Traces first: wasted-turn ratio and context growth are the usual culprits. Then in ROI order — context discipline, prompt-cache alignment, model routing by step type (eval-proven), and hard budget rails per run/user/tenant with 80% alerts.

## Ch 19 — Security

**Q. What security risks come with autonomous agents?** *(verbatim from published banks)*
Prompt injection through anything the agent reads, tool poisoning, data exfiltration, memory poisoning, excessive agency, identity abuse, cascading multi-agent compromise — the OWASP Agentic Top 10 names them. The senior framing: injection is a property, not a bug.

**Q. How do you actually defend, given injection can't be fully detected?**
Guardrails filter; architecture prevents: least-privilege tool grants (injected "email this" fails on absent capability), user-scoped authz per call, sandboxed execution with egress allowlists, trust-labeled context, and agent identity with a kill handle. State the blast radius: "fully compromised, it can do exactly X."

## Ch 20 — Governance & HITL

**Q. What is human-in-the-loop and where do you put it?**
A human approval/edit point exactly where actions become irreversible — nowhere else, or you breed rubber-stamping. Measure override rates: 0% means decorative checkpoint, 40% means the agent isn't ready. Escalation ("I'm not confident") is rewarded behavior.

**Q. How would you govern AI agents in a bank?**
Autonomy assigned per action class (read L3, recommend L3, communicate L2, move money — humans), an inventory with named owners, evals as validation evidence, traces as audit records, graded kill switches — mapped to RBI's FREE-AI and the draft Model Risk Management guidance so regulation is a mapping exercise, not a retrofit.

**Q. What are your views on the ethics of agentic AI?** *(commonly asked, deceptively soft)*
Concrete beats abstract: bias testing on protected segments in the eval suite, explanation generated from the actual evidence trail, uncertainty communicated honestly to prevent automation bias, accountability with a named human owner per agent. Ethics operationalized as controls, not sentiment.

## Ch 21 — Platform / System Design

**Q. Design an enterprise agent platform. Go.**
Six layers — experience, agents, orchestration+harness, knowledge, tools+gateway, enterprise systems — with security, observability, evals, governance, and cost as cross-cutting concerns. Then the ten defining decisions, and the build order: extracted from working use cases, never pre-built. (Full walkthrough: ch23 case study.)

---

## The governance & security question, per module

Interviewers at regulated companies increasingly ask the governance version of every design question. One per module, with the answer's spine:

**A — "How do you make an agent-vs-workflow choice defensible to a risk committee?"**
Document the placement with its justification: who owns control flow, what replay/audit story each rung gives, and what the choice costs. A workflow replays exactly; choosing "agent" creates a tracing obligation the same day.

**B — "You've given the model control flow. How do you govern non-determinism?"**
Bound it and count it: deterministic bounds around every intelligent decision, a counted budget of model-owned edges in the graph, checkpoints as the record of what actually happened, and harness policy as reviewable data with separation of duties on changes.

**C — "How do you stop the knowledge layer becoming a data-aggregation or leakage risk?"**
Entitlements enforced inside each source at query time (RLS, ACL filters, traversal limits) — never in the router's prompt; the graph gets special attention because it joins data that was deliberately separated; every answer lists sources touched under whose entitlement.

**D — "How do you vet third-party MCP servers and skills?"**
As supply chain: allowlist-only internal registry with named owners, review before availability (descriptions are injection vectors; servers see your arguments; skill scripts execute), version pinning, sandboxed execution under the agent's existing grants, per-integration kill switch at the gateway.

**E — "Your traces contain customer data. Now what?"**
The audit record is itself sensitive: PII-masked by default with gated unmasked access, retention per record class, access tiered by audience, integrity protected. And evals inherit the same handling because their datasets come from traces.

**F — "What's your kill-switch story?"**
Graded — per-agent (revoke identity), per-integration (gateway), platform-wide — with halts that checkpoint state and leave clean audit trails, drilled before an incident, mapped to RBI's kill-switch expectation. A kill switch that loses state is a second incident.

## Screening-round quick answers (they really do ask these)

- **"Which frameworks have you used?"** — Name LangGraph as primary with reasons (explicit state, checkpoints, interrupts), contrast with Agents SDK and CrewAI in one sentence each. Comparing frameworks is the architect signal; loyalty to one is the developer signal.
- **"How do you stay current?"** — Name specific sources: vendor engineering blogs (Anthropic/OpenAI/AWS), the OWASP agentic work, a couple of practitioners' newsletters, and building — your three portfolio projects are the honest answer.
- **"Describe a hard problem from a real AI project."** — Have one Siddhi story ready in STAR shape ending with a measured number (judge calibration, latency, scale). One deep true story beats five shallow ones.
