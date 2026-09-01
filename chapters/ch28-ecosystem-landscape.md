# Chapter 28: The 2026 Agentic AI Ecosystem

> Technologies are examples, concepts are permanent. Every tool named in this chapter is one implementation of a pattern taught earlier in this course — the harness, the gateway, the loop, the eval gate. The tool names will be wrong within eighteen months; the patterns underneath them are what you were actually hired to design.

## 1. Why a landscape map, and how to read it

This chapter is different from the other twenty-seven. Everywhere else, the goal was to teach you a pattern deeply enough that you could defend it in a design review. Here, the goal is narrower: to give you a labeled map of the tooling ecosystem as it stood in September 2026, so a newcomer to the field can walk into a vendor conversation, a bake-off, or an internal platform debate without feeling lost.

Read it that way and no other. Do not memorize this chapter for an interview the way you'd memorize Ch5's harness anatomy or Ch18's cost equation — an interviewer who asks "what does LangGraph do" wants to hear the *concept* (explicit graph, typed state, checkpointing) with the tool name as a label, not a recitation of this table. This chapter will age faster than any other in the course, on purpose: it is a snapshot of a market that reshuffles every few months, sitting on top of twenty-seven chapters of material that doesn't. If you're reading this a year after it was written, expect at least one row below to be wrong — that's not a defect in the chapter, it's the reason §3 exists.

## 2. The map

Each table below has three columns: the tool, what it's actually for, and which chapter of this course teaches the underlying concept it implements — the thing to actually learn.

### 2.1 Orchestration

| Tool | What it's for | Where this course covers the concept |
|---|---|---|
| LangGraph | Explicit graph orchestration — typed state, declared edges, built-in checkpointing and interrupts | Ch4 (the graph pattern), Ch2 §7 |
| OpenAI Agents SDK | Runner-owned loop — configure agent + tools, the SDK iterates, handoffs express delegation | Ch2 §7, Ch4 §8 |
| Microsoft Agent Framework | Unified successor to AutoGen and Semantic Kernel, reached GA in 2026 | Ch4, Ch15 |
| Google Agent Development Kit (ADK) | Google's orchestration and multi-agent toolkit, tightly integrated with Gemini/Vertex | Ch4, Ch15 |
| Claude Agent SDK / harness-style tooling | Minimal visible loop; engineering effort goes into what surrounds it — context, tool policy, sandboxing | Ch5 |
| Amazon Bedrock AgentCore | Managed runtime + harness layer sold as infrastructure rather than framework | Ch7 §8 |

The one genuine change worth flagging against earlier chapters: **AutoGen and Semantic Kernel, discussed separately in Ch4 and Ch9, merged into the Microsoft Agent Framework in 2026, and AutoGen now ships no new features on its own** — a live example of the vendor-consolidation risk §4 below asks you to plan for, not a hypothetical. LangGraph remains this course's reference stack for the reason Ch4 §8 gives: the graph is explicit and inspectable, which is what a bank's architecture review actually wants to see. None of these is "better" in the abstract — the same three questions Ch4 taught you to ask (where does state live, who owns each edge, what happens on a crash at step 7 of 9) still sort every one of these tools correctly.

### 2.2 Multi-Agent Frameworks

| Tool | What it's for | Where this course covers the concept |
|---|---|---|
| CrewAI | Role/task metaphors over a multi-agent crew; fastest path to a working demo | Ch15 |
| Microsoft Agent Framework | Conversable multi-agent patterns, the direct successor to AutoGen's role in this space | Ch15 |
| Google ADK | Multi-agent teams as a first-class construct inside Google's orchestration stack | Ch15 |
| LangGraph (supervisor/hierarchical graphs) | Multi-agent topology built from the same graph primitives as a single agent | Ch4, Ch15 |

"Multi-agent framework" is less of a distinct category in 2026 than it was even a year earlier — every orchestration framework in §2.1 now ships multi-agent primitives out of the box, so the meaningful choice usually isn't "which multi-agent package" but "which orchestration framework's multi-agent primitives fit my topology." What doesn't commoditize is the design work Ch15 covers: the delegation contract, the join problem, and who owns the state each sub-agent hands back — pick any of the four tools above and you still have to design all of that yourself.

### 2.3 Observability

| Tool | What it's for | Where this course covers the concept |
|---|---|---|
| Langfuse | Self-hostable LLM-native tracing backend — relevant when data residency rules out SaaS | Ch16 |
| LangSmith | LangChain-native tracing, monitoring, and dataset management | Ch16 |
| Arize Phoenix | Open-source, OTel-native LLM observability | Ch16 |
| OpenTelemetry GenAI semantic conventions | The wire format underneath all three — how spans are shaped, not where they're stored | Ch16 §6 |

This category consolidated early and has stayed consolidated: OTel GenAI conventions won as the wire format, and the three backends above differ mainly in hosting model and dataset tooling, not in what they capture. Ch16 already makes the point worth repeating here — the differentiator among mature teams was never which of these three you picked, it was whether you actually closed the loop from trace to eval (Ch16 §4).

### 2.4 Evals

| Tool | What it's for | Where this course covers the concept |
|---|---|---|
| Braintrust | Dataset management and CI-gated eval runs for LLM apps | Ch17 |
| DeepEval | Open-source, pytest-style eval framework | Ch17 |
| promptfoo | Open-source CLI for prompt and eval testing | Ch17 |
| LangSmith / Langfuse / Arize Phoenix | Also ship eval and dataset tooling alongside their observability product | Ch17 §7 |

Same story as observability, one layer up: tooling differs in dataset management, judge configuration, and CI integration, but every one of these tools assumes the traces-to-suites flywheel Ch17 teaches. The maturity marker Ch17 names is still the right one — not which tool, but whether eval results, not vibes, actually decide what ships.

### 2.5 Knowledge & Retrieval

| Tool | What it's for | Where this course covers the concept |
|---|---|---|
| LlamaIndex | Retrieval/indexing framework — document parsing, chunking, agentic RAG pipelines | Ch10 |
| Vector databases (Pinecone, Weaviate, Milvus, Qdrant, pgvector) | Embedding storage and similarity search, the substrate under most RAG | Ch10 |
| Graph databases (Neo4j and peers) | Structured relationship retrieval where "how are these connected" beats "which passage is similar" | Ch11 |
| Structured-record retrieval APIs (Seltz-class) | Agent-native retrieval — one call returns a complete structured record instead of links to fetch and parse | Ch12, Ch15 §7 |
| Mem0, Zep, Letta, LangMem, Cognee, Bedrock AgentCore Memory | Long-term *agent memory*, a different job from RAG even though both look like "retrieval" | Ch9 §4 |

This is the least consolidated category on the map, and worth calling out for that reason alone: no single winner has emerged the way OTel did for observability, because retrieval and memory are still genuinely different problems wearing similar-looking APIs. Keep Ch9's distinction sharp when you evaluate any tool here — a vector database answers "what's relevant," a memory store answers "what should this specific customer's agent still know a month from now," and confusing the two is the exact failure mode Ch9 §2's fraud-flag story was built to warn against.

### 2.6 Protocols

| Tool | What it's for | Where this course covers the concept |
|---|---|---|
| MCP (Model Context Protocol) | Agent↔system standard — tools, resources, prompts; turns N×M integrations into N+M | Ch14 |
| A2A (Agent2Agent) | Agent↔agent standard — Agent Cards, task lifecycle, cross-vendor and cross-org | Ch14 |
| Agentic AI Foundation (Linux Foundation) | Since 2026, houses governance for *both* MCP and A2A under one umbrella | Ch14 §4 |
| AG-UI / A2UI | Standardizes agent↔user-interface event streaming | Ch14 §4 |
| WebMCP | Websites exposing MCP endpoints directly, instead of agents scraping pages | Ch14 §4 |
| ACP, ANP | Adjacent/competing protocols, still consolidating around MCP and A2A | Ch14 §4 |

The one concrete update here since Ch14 was written: MCP and A2A now share a governance home under the Linux Foundation's Agentic AI Foundation, rather than sitting as two separately-stewarded specs. That's a reason for more confidence in both, not less — it's exactly the kind of shape-level stability Ch14's closing advice already told you to depend on ("depend on protocol shapes — discovery, task lifecycle, capability manifests — not on spec details"), and it held up.

## 3. What doesn't change

Strip away every name in §2 and this is what's left — the material the rest of this course actually teaches, and the reason a tool churning out from under you shouldn't cost you your architecture:

- **The harness pattern (Ch5).** Bounds, sandboxing, tool policy, and persistence sit *around* the model loop regardless of which SDK owns the loop's syntax. Swap LangGraph for the Microsoft Agent Framework and the harness you built doesn't move.
- **The gateway pattern (Ch14).** One governed choke point for every tool call, whatever protocol carries it. MCP is today's shape; the gateway is the permanent idea.
- **The autonomy ladder (Ch20 §1).** Which layer a workload runs at — assisted, approved, supervised, autonomous — is a governance decision independent of vendor. A new framework doesn't change what layer a fee-waiver decision is allowed to run at.
- **State vs. memory (Ch2 §5, Ch9).** Every "memory" product in §2.5 is an implementation of a distinction this course teaches you to make yourself, with or without the product.
- **The eval gate and typed-retry discipline (Ch17, Ch18).** Whatever framework routes your calls, a fallback path still needs the same eval clearance as the primary before it reaches a production decision.
- **The cost equation (Ch18 §1).** Calls × context × price × retries doesn't change shape because you changed orchestration frameworks — only the levers you pull to shrink it do.

## 4. Architect's take: the banking read

You will be asked, repeatedly and for the rest of your career, "should we adopt [tool that didn't exist when this chapter was written]?" The evaluation method below is built to still work when every name in §2 is out of date, because it asks about the pattern, not the product:

1. **Where does it put state, and who can read the checkpoint after a crash?** If the answer is "trust the vendor's dashboard," that's a gap, not an answer — Ch4's crash-at-step-7 question still applies.
2. **Can it sit fully behind your existing gateway (Ch14), or does it want direct access to systems?** A tool that insists on bypassing the gateway is asking for an exception to your entire governance model, not just a pilot.
3. **What's the exit cost if the vendor sunsets it, gets acquired, or pivots?** §2.1's AutoGen note is the concrete answer to "could this happen to us" — it already happened, to a framework with tens of thousands of production users, inside the same year this chapter was written.
4. **Does adopting it require a new eval suite, a new trace format, or a new data-residency review?** If yes, budget that cost explicitly rather than discovering it after the pilot succeeds and someone wants to scale it.
5. **Would you present this exactly the same way to a risk committee regardless of which vendor built it?** If the pitch only works because of the brand name, it isn't ready.

None of those five questions has a shelf life. That's the point of building the evaluation this way instead of maintaining a running scorecard of which framework currently "wins."

## Governance & security lens

Every tool in §2 is a vendor relationship, a data flow, or both, and adopting one is a procurement decision wearing an engineering decision's clothes. The questions that matter don't change by category:

- **Data residency and processing location.** Where does this tool's data — traces, memory records, retrieved documents, prompts — actually sit, and does that satisfy the same obligations the primary system it touches already cleared? Ch16 already flags this for observability (self-hosted Langfuse over a SaaS default, specifically for this reason); the same question applies to every memory store and knowledge-retrieval tool in §2.5.
- **Vendor concentration and lock-in.** A framework that owns your state schema, your trace format, and your eval harness all at once is a much harder thing to exit than one that owns only one of those. Prefer tools that let you keep your own schema and swap the implementation underneath — the same "storage layer is replaceable, the schema is yours forever" principle Ch9 §4 states for memory generalizes to this whole chapter.
- **Supply-chain review for anything with tool-execution access.** Ch14's MCP-servers-are-supply-chain framing applies to every orchestration and multi-agent framework too — anything that can call a tool, read a schema, or touch customer data through your gateway gets the same vetting a new vendor integration would.
- **A named owner for every adoption decision.** Not "the platform team likes it" — a specific accountable owner who can answer, on record, why this tool cleared review and what the exit plan is if it doesn't survive its own vendor's next pivot.

Governing question: **if every tool in this chapter's tables were retired tomorrow, which of your controls would still hold — and which ones were quietly implemented as "whatever the vendor's dashboard shows"?**

## Interview-ready lines

- "Technologies are examples, concepts are permanent — I can tell you what any framework in this space does by naming which pattern from this course it implements."
- "AutoGen going into maintenance mode in 2026 isn't a cautionary tale, it's the base rate — plan every framework adoption assuming this happens to it too."
- "The harness sits under the framework, not inside it — swap LangGraph for anything else and the bounds, sandboxing, and tool policy don't move."
- "MCP and A2A now share a governance home under one foundation — that's the shape-level stability worth trusting, not any single spec's version number."
- "Observability and evals tooling consolidated around OTel and the traces-to-suites flywheel; knowledge and memory tooling didn't — because retrieval and memory are still genuinely different problems."
- "Evaluate a new framework on where it puts state, whether it can sit behind your gateway, and what your exit cost is — never on what's trending."

## Interview Questions & Answers

**Q1: Why are agent orchestration frameworks treated as a commodity layer in this course, while the harness and gateway patterns are treated as durable architecture?**

A framework is a syntax for expressing a loop — LangGraph draws it as a graph, the OpenAI Agents SDK wraps it in a runner, CrewAI hides it under role metaphors — and Ch2 §7 already shows all three are the same six-line loop with different opinions about where the boxes go. The harness (Ch5) and the gateway (Ch14) are different: they're where the actual governance surface lives — bounds, sandboxing, tool entitlements, audit logging, the single choke point every system call passes through — and none of that logic depends on which framework's syntax drew the loop above it. A bank that builds its harness and gateway as framework-agnostic layers can swap LangGraph for the Microsoft Agent Framework without touching a single control; a bank that builds its bounds and entitlements *inside* a specific framework's abstractions has quietly made its governance model as replaceable as the framework itself. That's the whole argument for teaching patterns instead of APIs in a curriculum meant to outlast this decade's frameworks.

**Q2: A framework your platform depends on gets deprecated or acquired with six months' notice. Walk through what actually breaks, and what doesn't.**

This isn't hypothetical — it's this chapter's own example: AutoGen, a framework with tens of thousands of production users, went into maintenance mode in 2026 when Microsoft folded it into the unified Agent Framework alongside Semantic Kernel. What breaks is real and needs a migration project: the framework-specific syntax for defining agents and edges, any framework-native persistence format your checkpoints were written in, and whatever CI tooling assumed that framework's APIs directly. What doesn't break, if you built it the way this course teaches, is the harness sitting around the loop, the gateway every tool call already passed through, the eval suite your fallback paths were gated against, and the state schema you designed yourself rather than inheriting from the framework's object model. The practical guardrail is to always own your state schema and your audit trail independent of any framework's native format — Ch9 §4 states this for memory specifically ("the storage layer is replaceable, the schema is yours forever") and it's exactly as true for orchestration.

**Q3: What are the real cost implications of choosing one orchestration framework over another?**

Directly, framework choice is close to cost-neutral — you're paying for model tokens either way, and none of the frameworks in §2.1 charge meaningfully different licensing for the open-source core. The cost implications are indirect and larger: a framework whose abstractions hide where state lives makes Ch18's cost equation harder to instrument (you can't route by step type or cache aggressively what you can't cleanly separate), a managed framework layer like Bedrock AgentCore trades engineering time for a recurring platform fee, and a framework you later need to migrate off of (per Q2) has a real, sometimes six-figure, one-time cost that never shows up in the original build estimate. The honest framing for a cost review is that framework choice determines how *easy* it is to apply Ch18's four levers — context discipline, caching, routing, budgets — not whether those levers exist at all; pick the framework that makes state and context assembly the most explicit and inspectable, because that's the one you'll be able to optimize later.

**Q4: What data security and vendor lock-in risks does adopting a third-party agent framework or tooling product introduce, beyond the model provider you're already using?**

Every tool in this chapter's tables is a new place data can land or a new dependency your architecture can't easily unwind: an observability backend concentrates traces (which can contain PII in prompts and tool arguments, per Ch16's own governance lens), a memory store holds long-lived customer facts that need the same TTL and deletion guarantees Ch9 §5 requires, and an orchestration framework that owns your state schema natively makes migration expensive exactly when you'd most want to leave — during a vendor's own instability. The mitigation is the same principle repeated across this course: prefer self-hostable or schema-portable options where the data is sensitive (Ch16's Langfuse-over-SaaS example), treat anything with tool-execution access as supply chain requiring the same vetting Ch14 applies to MCP servers, and never let a vendor's native format become your only copy of your own state or audit trail. Lock-in risk and data security risk are the same conversation in practice — the tool that's hardest to leave is usually also the tool holding the most sensitive data, because deep integration and data concentration tend to grow together.

**Q5: What guardrails would you put around a team's ability to adopt a new framework or tool quickly, without turning every genuinely useful new entrant into a six-month procurement fight?**

The guardrail isn't "no new tools" — it's a fast, repeatable checklist gated by blast radius: a tool touching only a developer's local sandbox with no customer data and no production tool-execution access can clear a lightweight review in days, while anything that can reach a production decision path, hold customer data, or execute tools through the gateway needs the full review this chapter's §4 five questions lay out (state ownership, gateway compatibility, exit cost, new-review triggers, committee-ready pitch). Pair that with a standing internal registry — the same pattern Ch14 already recommends for MCP servers — so "has this been vetted" is a lookup, not a re-litigation every time a team wants to try something new. The goal is a review process fast enough that engineers don't route around it, and consistent enough that a framework's marketing doesn't substitute for its actual answers to the five questions.

**Q6: How should a bank structure access control and procurement review when adopting third-party agent tooling — orchestration frameworks, observability platforms, memory stores — at scale?**

Procurement review for this category needs to ask questions generic vendor review checklists don't: does this tool get tool-execution access through your gateway, and if so under what entitlement scope; where does its data physically sit, and does that satisfy the residency obligations of whatever system it touches; and what's the actual exit path if the vendor pivots, given how often that's happened in this exact market in 2026. Access control follows the same least-privilege principle Ch18 §5 applies to fallback models — a new observability backend or memory store shouldn't inherit broad access "to get the pilot working faster," it should get exactly the scope its function requires, provisioned and reviewed on the same cadence as any other production credential. The structural fix is routing every one of these adoptions through the same registry-plus-gateway pattern Ch14 already establishes for MCP servers, so a new framework or tool is never granted direct access to core systems — it's granted access to the gateway, and the gateway is what actually touches core banking.

**Q7: What changes about your deployment approach when the underlying orchestration framework is one you expect to migrate away from within a few years?**

Deploy so the framework is a replaceable layer, not a load-bearing wall: keep state and checkpoints in your own schema rather than the framework's native persistence format, front every tool call through the gateway (Ch14) rather than letting the framework talk to systems directly, and instrument with OTel GenAI conventions (Ch16 §6) so your traces outlive whichever backend or framework produced them. Ch7's infrastructure discipline — IaC, CI/CD gates, the two-role split between build-time and run-time identity — should already be framework-agnostic if it was built correctly the first time, since none of that layer cares which SDK is calling the model. The practical test before any deployment: if you swapped the orchestration framework tomorrow, could you redeploy against the same gateway, the same trace pipeline, and the same eval suite without touching them — if not, the framework has leaked into layers it shouldn't own.

**Q8: A genuinely new framework shows up after this chapter was written — one you've never heard of, with no track record. How do you evaluate it without waiting for the market to consolidate around it?**

Run it through the five questions in §4 regardless of how new or unfamiliar it is: where does it put state and can you read a checkpoint after a crash, can it sit fully behind your existing gateway instead of demanding direct system access, what's your exit cost if it doesn't survive its first eighteen months, what new eval suite or data-residency review does adopting it trigger, and would you present the adoption to a risk committee the same way regardless of the vendor's name recognition. None of those questions requires the tool to have a track record — they require *you* to be disciplined about not granting it anything the five questions haven't cleared, the same discipline that would have caught AutoGen's eventual maintenance-mode status early rather than after migration became necessary. If the tool clears review, sandbox it at the lowest layer of Ch18's autonomy stack first — Layer 1, an engineer trying it interactively — before it's anywhere near a workload with production data, and require it to pass the same eval and policy gates any fallback model has to clear (Ch18 §4) before it can reach a real decision.

**Q9: MCP is a settled choice for a bank in 2026; A2A is described in this course as "design-ready but not yet production-crossing-organizations." How would you decide when it's actually time to adopt A2A for real cross-organization agent traffic, rather than just designing task lifecycles to be A2A-compatible?**

The signal isn't a version number or an adoption headline — it's whether identity and liability frameworks with the *specific* counterparty have matured enough that a task an external agent submits carries real accountability if it goes wrong, the same bar Ch14 sets before crossing an organizational boundary with any protocol. The fact that A2A now shares governance with MCP under one foundation is a reason for more confidence in the protocol's long-term shape, not a reason to accelerate adoption ahead of your own counterparty-risk readiness — shape-level stability and organizational trust are different questions answered by different reviews. Practically: keep building every agent's task lifecycle to be A2A-compatible now, since that costs nothing extra if you followed Ch6's async job pattern in the first place, and treat the actual first production A2A connection to an external fintech partner as a bilateral trust decision — reviewed like any other third-party integration with money-movement or data-sharing implications — rather than a platform upgrade you roll out once the spec looks mature enough on paper.
