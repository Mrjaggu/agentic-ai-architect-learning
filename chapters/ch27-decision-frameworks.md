# Chapter 27: Architecture Decision Frameworks

> Developer roadmaps teach how to build components. Architect roadmaps teach which to choose, and why — and being able to say why, in one sentence, with a named cross-reference, is the actual interview skill this chapter packages.

## 1. Why a decision index

Every chapter in this course already argues for or against a choice. Chapter 1 argues for workflows over agents on fixed-sequence compliance paths, and for agents over workflows the moment a path is genuinely unknowable. Chapter 11 argues for knowledge graphs over vector stores exactly where questions decompose into joins, not similarity. Chapter 15 sets a strict bar — five named justifications, nothing else — before a single agent becomes several. None of that reasoning is new here. This chapter does not re-derive it; it collects the verdicts the rest of the course already reached, compresses each into a scannable table and a committed default, and cross-links back to the chapter where the full argument — the worked example, the failure story, the trade-off table — actually lives.

The reason this is worth its own chapter, rather than an index page, is how these decisions actually show up in practice: not one at a time, in the order the curriculum teaches them, but bundled, under time pressure, in a design review or an interview where you have ninety seconds to say "here's the shape, here's why." An architect who has internalized RAG deeply and knowledge graphs deeply but has never had to *choose between them out loud, in front of a stakeholder, in one breath* is missing the actual AVP-level skill. This chapter is the rehearsal space for that moment, nine times over, plus a tenth section mapping the course's eight reference diagrams onto the same instinct: given a blank whiteboard, which shape do you draw first.

Hold this chapter the way you'd hold a laminated card, not a textbook. If a verdict below doesn't fully answer your specific case, that's the system working as designed — go to the cited chapter and read the worked example, the failure story, and the full trade-off table. The compression here is meant to get you to the right chapter fast, not to replace it.

## 2. The nine decisions

### 2.1 Workflow vs. Agent (Ch1, Ch3)

The tension: does deterministic code decide what happens next, or does the model?

| Dimension | Workflow | Agent |
|---|---|---|
| Path predictability | Known in advance; same sequence every time | Genuinely unknowable until you see the last observation |
| Replay / audit | Exact replay — the code *is* the explanation | Only trace-based replay; an observability obligation from day one |
| Cost & latency | Lowest; one fixed path | 5–10× a workflow's cost for the same answer, and non-deterministic latency |
| Where it wins | Fixed-sequence compliance processes, hard-latency paths, high-volume/low-value queries | Investigation-shaped work where each observation should steer the next move |

**The verdict:** default to workflow — code owns the sequence — and earn the move to agent only when the path can't be known in advance *and* one of RAG's four named failures (can't decompose, can't recover, can't choose, can't act) is actually biting. "Block my card and issue a replacement" is a workflow because compliance mandates the sequence; putting a model in charge of a mandated sequence is a design error you'd have to defend to a regulator and couldn't. "This customer's transactions look odd — investigate" is an agent because the path *is* the investigation. The reusable justification sentence, from Ch1 §7: *control flow here needs to be owned by X, because Y, and that costs us Z.* Learn the sentence shape before the specific verdicts — it's what a risk committee actually wants to hear.

### 2.2 Single Agent vs. Multi-Agent (Ch3, Ch15)

The tension: one capable agent with good tools, or several agents that hand off to each other.

| Dimension | Single Agent | Multi-Agent |
|---|---|---|
| Cost | 1× baseline | Routinely 5–15× baseline (Ch15 §6) |
| Debuggability | One trace | A provenance problem — the bug lives in what a handoff left unsaid |
| Earns its cost when | Almost always — the strong default | Context isolation, a real permission boundary, heterogeneous model/cost tiers, genuine parallelism, or separate team ownership — and *only* those five |
| Doesn't earn its cost when | — | "Researcher, writer, editor, fact-checker — like a newsroom" (anthropomorphic decomposition) |

**The verdict:** start single-agent, every time, and split only when traces show a named reason from Ch15 §1 — never a human org-chart metaphor. The newsroom story is the number to have memorized: a four-agent market-summary pipeline ran at ~8× a single agent's cost for indistinguishable quality, with a wrong figure taking a full day to trace across four transcripts; rebuilt as one agent with retrieval tools, a Reflection pass, and HITL sign-off, cost dropped to 1× and debugging became reading one trace (Ch3 §4). Where multi-agent *is* justified in a bank, it's almost always the permission-boundary reason — the card agent holds card-system credentials, the loan agent holds LOS credentials, no agent holds both — which makes pattern selection a least-privilege decision, not a modeling preference.

### 2.3 RAG vs. GraphRAG (Ch10, Ch11)

The tension: does the answer live in a document you can retrieve by similarity, or does it only exist as a path across connected entities?

| Dimension | RAG (vector) | GraphRAG |
|---|---|---|
| Question shape | "What does the policy say about…" — similarity | Multi-hop, aggregation-over-relationships, temporal linkage, "why is this connected" |
| Explainability | A citation to a chunk | The path itself *is* the explanation |
| Fails structurally on | Multi-hop joins, connected-party questions | — |
| Cost/complexity | Lower — chunking policy and an eval set | Ontology governance + entity resolution, on top of a query language |

**The verdict:** Ch11 §2's test decides it — if the question decomposes into "find things like X," use vectors; if it decomposes into "find things joined to X through a typed relationship," no amount of better chunking or reranking manufactures that answer, because the fact never lived in one document to begin with. "Which merchants received funds from accounts linked to defaulted loans?" is structurally a graph question; a vector index can retrieve prose *about* defaults and prose *about* merchants and still never produce the join. In practice the two are usually hybrid, not exclusive (Ch11 §4): vector search finds the relevant documents, the graph connects the entities they mention, and both land in context with cross-referencing metadata.

### 2.4 Vector DB vs. Knowledge Graph (Ch11)

The tension: as a storage and retrieval layer, when does the added machinery of a graph earn its keep over an index?

| Dimension | Vector DB | Knowledge Graph |
|---|---|---|
| Build cost | Low — embed and index | High for the LLM-extracted residue, but 80% of the graph loads by deterministic mapping from core systems at near-zero cost (Ch11 §3) |
| Wins at | Semantic/similarity retrieval | Fraud rings, AML layering, connected-party exposure, KYC linkage — path queries |
| Risk it introduces | Standard retrieval-entitlement risk | Joins data that was deliberately kept separate — a single traversal can aggregate more than any one source system would release |

**The verdict:** don't build a graph to answer questions vectors already answer cheaply — that's résumé-driven architecture (Ch11 §5). Build one where relationship questions are frequent and high-value, which in banking means fraud, AML, and credit exposure are graph-*native* domains, not edge cases: an agent that can explain suspicion as a traversable path ("A → shared device → B → merchant M flagged twice") gives regulators exactly the explainability a similarity score can't. Position the graph as the platform's explainability substrate, not a second index competing with the first.

### 2.5 SQL vs. Vector Retrieval (Ch10, Ch12)

The tension: is the question an aggregation over records, or a semantic match over prose?

| Dimension | SQL / semantic layer | Vector retrieval |
|---|---|---|
| Question shape | "How many / sum / trend…" — aggregation | "What does the policy say…" — semantics over documents |
| Precision | Exact, deterministic, given a correct query | Approximate ranking; can miss exact identifiers |
| Deployability risk | Text-to-SQL against a *raw* schema is fragile and dangerous | RAG asked an aggregation question fabricates a document-shaped answer to a question that needed a database (Ch1's "can't choose" failure) |

**The verdict:** route by shape, per Ch12's taxonomy — never let one hardwired knowledge path answer everything. "How many customers prepaid their home loans last quarter?" is a SQL question; sending it to a vector store retrieves policy prose *about* prepayment and generates something that only looks like an answer. The deployability condition matters as much as the routing rule: text-to-SQL against raw tables is a real production risk (wrong joins, no row-level security, an unbounded scan); text-to-SQL against a *governed semantic layer* — defined metrics, defined joins, RLS baked in — is the deployable version, the same relationship the ontology has to the graph (Ch12 §11).

### 2.6 MCP vs. API (Ch13, Ch14)

The tension: integrate each agent to each system with a bespoke connector, or standardize the connection.

| Dimension | Direct / native API | MCP |
|---|---|---|
| Integration cost | N agents × M systems — grows combinatorially | N + M — write the server once, any MCP-capable host uses it |
| Governance | Per-integration; N×M different answers to "how do agents reach systems?" | One protocol, one gateway, one audit format |
| When it's still right | A genuinely rich integration that justifies a native API internally | The default — and even the rich native integration should sit *behind* an MCP façade for governance uniformity |

**The verdict:** MCP is infrastructure now, not a bet (Ch14 §1) — treat it as the default tool-integration layer, fronted by a gateway that owns authN, authZ, rate/budget policy, and audit as one choke point (Ch14 §2). A native API is not disqualified; it's wrapped, because a bank's auditor wants one answer to "how do agents access systems," not a footnote explaining why one integration is different. The non-negotiable design rule underneath the whole decision: the agent must never be a super-user — the *user's* entitlements travel with every call through the gateway, not a blanket agent credential.

### 2.7 Sync vs. Async Execution (Ch4, Ch6)

The tension: does this call return in milliseconds and hold nothing, or does it run long enough — and touch enough — to need a job?

| Dimension | Synchronous | Async (job-queue-worker) |
|---|---|---|
| Duration | Seconds, bounded | Minutes, iterative, unbounded in the worst case |
| Side effects | None the customer would notice twice | Mutating or irreversible (refund, block card, send message) |
| Failure recovery | None — a crash restarts from zero | Checkpointed — resume at the last node, not step 1 |
| Retry safety | A network retry can silently double-execute | Idempotency key means a retry returns the existing job, never a second one |

**The verdict:** Ch6 §7's dividing line is the whole decision — does this call touch state or trigger a side effect anyone would care about happening twice? If yes, it goes behind the job-queue-worker shape (`POST /jobs` returns a job_id in milliseconds; the worker runs the graph with checkpoints; progress streams as events, not a spinner). If the call is genuinely short, read-only, and side-effect-free — "summarize this document," no tool calls — a plain synchronous endpoint is honest and correct, and the async machinery isn't worth its cost. The failure mode of getting this wrong is not hypothetical: a dispute-investigation agent shipped behind a sync endpoint produced two ₹4,300 refunds for one dispute, because a client-side retry, arriving after a 60-second timeout the server-side run had already exceeded, created a second independent run — the root cause was architectural, and a prompt fix would have done nothing (Ch6 §2).

### 2.8 Stateless vs. Stateful Agents (Ch2, Ch9)

The tension: does the agent need anything beyond the current call to do its job?

| Dimension | Stateless | Stateful |
|---|---|---|
| What persists | Nothing beyond one call | Per-run state (Ch4) and/or cross-run memory (Ch9) |
| Fits | One-shot Q&A with no continuity requirement | Multi-step investigation, multi-turn conversation, cross-session personalization |
| Governance cost | Minimal | A typed state schema and checkpointer (state); an extraction policy, provenance, and TTLs (memory) |

**The verdict:** the moment a task is path-contingent — the dispute-investigation trace in Ch2 §2 branches differently on turn 3 depending on what turn 2 returned — the agent needs state; there is no stateless version of "investigate and recommend" that works. Memory is a separate, higher bar: add it only when facts must survive *across* runs, and design it with the discipline Ch9 demands from day one, because conflating a per-run object with a governed cross-run store is a documented failure mode (a service agent's "memory" was just the growing chat transcript — sessions slowed as a state-sized object rode in every context window, a March address went stale and got used in September, and a privacy review got no better answer than "everything anyone ever typed"). State and memory are architecturally different problems with different owners; treat them as one and you get both failure classes for free.

### 2.9 Short-term vs. Long-term Memory (Ch2, Ch9)

The tension: given that memory is needed, what actually deserves to survive past this run, and for how long?

| Dimension | Short-term / working (really *state*) | Long-term (episodic, semantic, procedural) |
|---|---|---|
| Lifetime | Session or run | Persists across runs, potentially indefinitely |
| Contents | Messages, tool results, iteration count, goal criteria | User facts, past episodes, learned procedures |
| Governance bar | Schema + checkpointer | Extraction allowlist, confidence score, provenance, purpose tag, TTL, erasure API |

**The verdict:** Ch9's taxonomy draws the line precisely — short-term and working memory are really Ch2's *state*, not memory at all, and the actual architecture problem is the long-term kinds: what gets extracted, for how long, visible to whom, forgettable on demand. The bar for writing to long-term memory must be *higher* than the bar for using context, because a poisoned context costs one call and a poisoned memory costs every call until someone notices — concretely, an unconfirmed "fraud-risk transaction pattern" inference written with no confidence score and no expiry surfaced across fourteen interactions over eight months, coloring agent tone, tainting two human escalations, and contributing to a wrongly declined loan pre-approval, before an ombudsman complaint traced it back to one unreviewed memory write (Ch9 §2). Remember by policy, not by default: define what the system *may* store, not just build extraction and hope.

## 3. Reference Architecture Pattern Gallery

Eight diagrams already exist across this course. This is an index to them, not a new set — when a design needs a starting shape, pick one here and go read the chapter for the full picture.

- **Basic Agent Loop (Ch2)** — Reason → Plan → Select Tool → Act → Observe → Reflect, with the harness executing everything the model requests and never the reverse. Reach for this as the mental model underneath *every* agent framework — LangGraph, the OpenAI Agents SDK, CrewAI — before evaluating any of them, and as the reference shape for a single-agent, single-turn task.

- **Stateful Agent / Durable Graph (Ch4)** — CLASSIFY branching into typed nodes, converging on a VALIDATE gate with a bounded retry edge back, checkpointed at every node, interruptible at declared points. Reach for this the moment a design needs bounded cost, resumability after a crash, or a human-approval point that's a structural halt rather than a UI convention — in short, whenever Ch1's placement logic says "agent," this is the production shape of that agent.

- **Async Agent / Job-Queue-Worker (Ch6)** — Client submits to a fast API, a queue absorbs and buffers, a worker pool runs the graph, progress streams back as events, results land in a durable store. Reach for this the instant an agent's work is long-running or touches a mutating side effect — it's the architecture that makes idempotency, cancellation, and honest progress possible at all.

- **Agent + RAG (Ch10)** — A knowledge layer (documents, structured data, live APIs) sitting behind the agent, which routes among sources rather than being the source itself. Reach for this as the default knowledge-grounding shape for document-shaped questions, with the chunking discipline of Ch10 §3 as the part that actually determines whether it's trustworthy.

- **Agent + GraphRAG (Ch11)** — An ontology-governed entity graph (Customer/Account/Loan/Merchant, typed relationships) alongside the document layer, queried by entity-anchored expansion or text-to-graph-query. Reach for this when the questions are relationship-shaped, not similarity-shaped — and when the *path* returned needs to double as the explanation a regulator or investigator will read.

- **Multi-Agent Delegation (Ch15)** — Supervisor and Pipeline topologies with typed `Delegation` contracts carrying structured identifiers, budgets, and an `on_behalf_of` field, rather than free-text handoffs. Reach for this only after §2.2's five-justification test passes — and note the whole diagram exists to prevent the "bare name string crossing an agent boundary" failure class, not to look impressive on a slide.

- **Human-in-the-Loop / Autonomy Matrix (Ch20)** — The L0–L3 autonomy ladder (Assist / Suggest / Approve / Autonomous) paired with a per-action-class YAML matrix scored on reversibility, blast radius, detectability, and measured reliability. Reach for this whenever a design needs to answer "how autonomous should this be" — the answer is never "the agent," it's a row per action class, written down and defensible.

- **Enterprise Agent Platform (Ch21)** — The six-layer reference stack (Experience, Agent, Orchestration & Harness, Knowledge, Tool & Integration, Enterprise Systems) with Security, Observability, Evals, Governance, Reliability & Cost, and Deployment running cross-cutting through every layer. Reach for this when the conversation moves from "design this agent" to "design the platform eleven teams will build agents on" — every box in it is one of the other seven diagrams, or a chapter, given a home.

## 4. How to use this chapter

At the start of a design, don't open a blank canvas — walk the nine decisions in §2 in order, against the specific use case, and write down a one-line answer to each, even "not applicable here." Most designs will hit three or four of the nine hard (workflow-vs-agent and sync-vs-async are close to universal; the knowledge-source decisions only bite if the agent touches knowledge at all) — the exercise is cheap, and it surfaces the decision you'd otherwise make by accident, halfway through a build, under a deadline.

Once the nine decisions are answered, use §3's gallery to pick a starting reference shape rather than drawing from nothing — nearly every real system is a composition of two or three of those eight diagrams (a stateful graph, behind a job-queue-worker, calling into a RAG-plus-graph knowledge layer, with an autonomy matrix gating the one irreversible action it can take), not a novel ninth thing.

Then go deep in the cited chapter for whichever decision the design actually turns on. This chapter's verdicts are compressed on purpose — they're built to get a design 80% of the way to a defensible position in the first ten minutes of a review, not to survive a detailed cross-examination on their own. The cross-examination is what the source chapter's worked example and failure story are for.

## 5. Architect's take: the banking read

The differentiator at AVP level was never knowing any one of these nine trade-offs cold — plenty of engineers can. It's holding all nine simultaneously, correctly, under the specific pressure of a live design review where a VP asks "why not just use a graph for everything" or "why does this need to be async" and expects a one-breath answer with a reason, not a essay. This chapter is that rehearsal. A candidate who can walk a whiteboard through workflow-vs-agent, then single-vs-multi-agent, then sync-vs-async, each with a one-sentence verdict and a "why," in under two minutes, has just demonstrated the actual job — not agent-building, but architecture governance under time pressure, which is what an AVP is hired to do in a room full of people who don't have this course's twenty-six chapters memorized.

The second, quieter differentiator: every verdict in §2 comes with an explicit *default* and an explicit *flip condition* — never a bare "it depends." "It depends" is what a junior engineer says when they haven't done the work of deciding; "the default is X, and it flips to Y when Z is true" is what an architect says because they have. Practice giving the second answer, not the first, until it's reflexive.

## Governance & security lens

Every decision in §2 is a governance decision wearing an architecture costume — which one you pick changes the audit surface, the data-residency footprint, and the blast radius of a failure, not just the engineering effort. Workflow-vs-agent decides whether an answer can be exactly replayed or only trace-reconstructed (§2.1). Single-vs-multi-agent decides whether one agent holds combined credentials or credentials stay split along permission boundaries by design (§2.2). RAG-vs-GraphRAG and vector-vs-graph decide whether a single query can join data that was deliberately kept separate across systems (§2.3, §2.4). MCP-vs-API decides whether every integration passes through one auditable gateway or N different ones (§2.6). Sync-vs-async decides whether a duplicated network retry can duplicate a real-world customer action (§2.7). Stateful-vs-stateless and short-vs-long-term memory decide how long a wrong inference about a customer can keep influencing decisions before anyone notices (§2.8, §2.9). None of these is a purely technical call in a regulated bank — each one is a line item a risk committee is entitled to ask about, and each cited chapter's Governance & security lens is where the full control story lives.

## Interview-ready lines

- "Nine decisions, nine defaults, nine named flip conditions — 'it depends' is what you say when you haven't done the work of deciding."
- "Every architecture decision in this course is a governance decision wearing an engineering costume — the choice changes the audit surface, not just the code."
- "Start single-agent, start synchronous, start with a workflow, start with vectors — the default is always the cheaper, more auditable option, and you earn the more expensive one with a named reason."
- "A knowledge graph and a multi-agent system fail for the same underlying reason when they're built without justification: résumé-driven architecture — paying real cost and real governance overhead for a capability the traces never asked for."
- "The reusable sentence for any of these nine decisions: control flow (or credential, or store) here needs to be owned by X, because Y, and that costs us Z."
- "The bar for writing to long-term memory is higher than the bar for using context, for the same reason a bank double-checks a permanent record more than a phone call — memory costs every future decision until someone notices, context costs one."

## Interview Questions & Answers

**Q1: Why would an interviewer ask "how do you decide between X and Y" questions at architect level, instead of testing deep expertise in one specific technology?**

Because the job an AVP-level architect is actually hired to do is triage under pressure, not depth in isolation — a design review rarely asks "explain vector embeddings in detail," it asks "why did you choose a graph here instead of your existing RAG pipeline," and the answer has to arrive in one breath with a named reason, not a lecture. Deep expertise in any single area is necessary but not sufficient, because a system with excellent RAG and mediocre judgment about *when* to reach for RAG still ships the wrong architecture. What a decision-framework question actually tests is whether the candidate has internalized defaults and flip conditions across the whole stack — workflow versus agent, single versus multi-agent, sync versus async — well enough to commit to a position and defend it, rather than hedging with "it depends" because they haven't done the underlying work. That's also precisely why this course collects nine such decisions into one chapter: the individual arguments live in twenty-six other chapters, but the *skill* of holding all nine simultaneously and choosing fast is its own thing, and it's the thing interviews for this level are actually probing.

**Q2: A team wants to build an agent for "block my card and issue a replacement." Walk through how you'd decide workflow versus agent here, and what you'd tell them if they pushed back wanting more flexibility.**

This is a textbook workflow, not an agent, and the deciding fact is that compliance mandates the sequence — verify identity, block, order replacement, confirm — which makes adaptivity a defect here, not a feature; a model deciding whether to reorder or skip a step is a design error I'd have to defend to a regulator and couldn't (Ch1 §7). I'd still use an LLM *inside* the workflow — parsing the customer's free-text request and drafting the confirmation message — because that's an LLM step, not agentic control flow; the distinction that matters is who owns the sequence, not whether a model is involved anywhere. If the team pushes for "more flexibility," I'd ask what problem that flexibility solves: if it's handling ambiguous requests ("my card's not working, not sure if it's lost"), that's a *classification* step feeding into the same fixed workflow, not a reason to hand the whole sequence to the model. The justification sentence I'd bring back to them: control flow here needs to be owned by code, because compliance requires an exact, replayable sequence, and handing it to a model costs us exactly the auditability that makes this process defensible.

**Q3: When would you actually justify splitting a single agent into a multi-agent system, and what's the failure mode you'd point to if someone proposed it without justification?**

I'd apply Ch15's five-justification test before agreeing to any split: genuine context isolation, a real permission boundary, heterogeneous model or cost tiers, true parallelism across independent subtasks, or separate team ownership — and reject "it mirrors how a human team would divide the work," because agents don't share the constraints that made human specialization necessary. The concrete failure mode I'd cite is this course's newsroom story: a team built researcher, writer, editor, and fact-checker agents for market-summary reports, and it demoed beautifully but cost roughly 8× a single agent for indistinguishable quality, with a wrong figure taking a full day to trace across four agents' transcripts, because every handoff between them was a lossy summary and the editor lacked the research context to catch anything substantive. The one place I'd approve a split without much debate is a genuine permission boundary — a card agent holding only card-system credentials and a loan agent holding only LOS credentials, where merging them into one agent would mean a single compromised context could pivot across systems it should never touch together. Absent one of those five reasons, my default answer stays single agent with good tools, and I'd ask the proposing team to bring trace evidence, not intuition, before revisiting.

**Q4: How do you decide between plain vector RAG and a knowledge graph — and separately, when does building a graph at all actually pay for itself over just tuning your existing vector index?**

The test is how the question decomposes, not how important it sounds: "what does the policy say about X" is a similarity question and belongs on vectors; "which merchants received funds from accounts linked to defaulted loans" only exists as a path across Customer, Loan, Account, and Merchant nodes, and no amount of better chunking or reranking manufactures that answer, because it was never sitting in one document to retrieve (Ch11 §2). Whether to build the graph at all is a separate, harder-nosed cost question: I wouldn't build one to answer questions vectors already answer well — that's résumé-driven architecture — I'd build it where relationship questions are frequent and high-value, and in banking that's specifically fraud rings, AML layering, and connected-party exposure, domains where 80% of the graph loads for free by deterministic mapping off core systems and the LLM extraction budget only goes toward unstructured residue like loan agreements. The clinching argument for a risk-averse stakeholder is usually explainability, not retrieval quality: a graph traversal that surfaces "A → shared device → B → merchant flagged twice" gives an investigator a path they can walk and challenge, which a similarity score never provides.

**Q5: A stakeholder asks why the team built a semantic-layer-backed text-to-SQL tool instead of just letting the RAG pipeline answer "how many customers prepaid their home loans last quarter." How do you explain that decision, and what goes wrong if you get SQL-versus-vector routing wrong?**

I'd frame it around question shape, not preference: that's an aggregation question — count, sum, trend — and a vector index has no concept of "sum," so routing it to RAG doesn't fail loudly, it retrieves policy prose *about* prepayment and generates something that only reads like an answer, which is Chapter 1's "can't choose" failure in a very literal form. The reason it's specifically a *semantic-layer-backed* SQL tool and not raw text-to-SQL matters just as much as the routing decision itself: text-to-SQL against a raw schema is fragile because the model has to correctly infer joins and business logic from column names alone, and dangerous because nothing stops a generated query from reading unauthorized rows or running an unbounded scan — a governed semantic layer with defined metrics, defined joins, and row-level security baked in is what makes the pattern deployable rather than a live production risk. Getting this routing wrong in either direction is costly: sending an aggregation question to vectors produces a fluent, wrong, hard-to-detect answer; sending a genuine document question to raw SQL either fails outright or, worse, someone builds brittle prompt engineering trying to force it to work, which is a maintenance liability neither answer needed.

**Q6: When do you reach for MCP instead of just calling a bank's internal APIs directly from an agent, and does that mean native APIs are deprecated?**

The arithmetic is the actual argument, not a preference for standards: without MCP you're building N agents times M systems worth of bespoke integration code, and every new agent or new system multiplies that count again, whereas an MCP server written once against core banking can be used by any MCP-capable agent host going forward — N+M instead of N×M (Ch14 §1). For a bank specifically, the bigger win isn't the coding time saved, it's governance uniformity: every agent-to-system connection passing through one gateway means auditors get a single answer to "how do agents reach systems," instead of reconciling N×M different bespoke answers during an audit. Native APIs aren't deprecated — a genuinely rich integration can still justify a native connection internally — but I'd still front it with an MCP façade, because the alternative is a governance blind spot where one integration doesn't get the same authN, authZ, rate limiting, and audit logging every other one does. The non-negotiable rule underneath the whole decision is that the agent itself must never act as a super-user — user entitlements travel with every call through the gateway, whichever transport got it there.

**Q7: How do you decide whether an agent endpoint should be synchronous or asynchronous, and what's the actual cost of getting that decision wrong?**

The dividing line I use is Ch6's: does this call touch state or trigger a side effect anyone would care about happening twice? A short, read-only, no-tool-calls request like "summarize this document" can honestly stay synchronous — the job-queue-worker machinery isn't worth its cost there. The moment an agent can issue a refund, block a card, or send a customer a message, the sync anti-pattern becomes a standing liability, not a shortcut, because a long-running call held open behind a synchronous endpoint will eventually outlive a client's timeout, and a naive retry policy will silently double-execute the side effect. The cost of getting this wrong isn't hypothetical — it's a documented incident in this course: a dispute-investigation agent behind a sync endpoint occasionally ran past 90 seconds against a mobile client's 60-second timeout, the client silently retried, and the retry created a second, fully independent run that reached the same correct conclusion twice, producing two ₹4,300 refunds for one dispute that went unnoticed for eleven days. The fix wasn't a smarter model or a better prompt — the root cause was architectural, an idempotency key and a queue away from being closed entirely, which is exactly why this decision belongs in an architecture review and not left to whichever engineer wrote the first endpoint.

**Q8: Design the state and memory architecture for a customer-service agent that needs to hold a multi-turn conversation and also remember the customer across separate visits. Walk through your stateless/stateful and short-term/long-term decisions.**

Within one conversation the agent needs state, full stop — a multi-turn support interaction is path-contingent by nature, the same way Ch2's dispute-investigation trace branches differently depending on what an earlier tool call returned, so there's no stateless version of this that actually works; I'd give it a typed state schema and a checkpointer per Ch4, not a growing chat transcript treated as memory. Whether it needs *long-term* memory is a separate, higher-bar decision: only facts that genuinely need to survive across visits — a stated language preference, confirmed case history — belong in long-term storage, and I'd apply Ch9's allowlist discipline rather than let an extraction step write whatever it judges "worth remembering." I'd deliberately keep the bar for a memory write higher than the bar for using context, because the course's fraud-flag incident is the cautionary case for getting this backwards: an unconfirmed pattern match got written to memory with no confidence score and no expiry, then surfaced across fourteen unrelated interactions over eight months, coloring tone, tainting two escalations, and contributing to a wrongly declined loan pre-approval before anyone traced it back to one bad write. Concretely: state gets a schema and dies with the session; memory gets a confidence field, a source reference, a purpose tag, and a TTL, and nothing crosses from state into memory without passing that policy.

**Q9: What are the data security implications of getting the knowledge-source routing decision wrong — say, a question gets routed to the wrong retrieval architecture entirely?**

Each backend enforces access differently — document ACLs on the vector index, row-level security in the semantic layer, hop-depth and edge-type limits in the graph — so a misrouted question doesn't just risk a wrong answer, it risks bypassing the specific control that source was built around; a question that should have gone through the semantic layer's RLS but instead got answered by a looser vector retrieval path could surface rows a user's role was never entitled to see, simply because the enforcement point that would have caught it was never in the request's path. This is compounded in a graph specifically: a graph's whole value is joining data that was deliberately kept separate across systems, so a role that's individually entitled to two different source systems can, through a k-hop traversal, infer something neither system alone would have disclosed — which is why access control in that architecture has to apply to the traversal itself, not just to individual nodes. The governing rule that prevents this across every retrieval architecture is the same one: entitlements must be enforced *inside* each source at query time, never assumed from the router's reasoning or a "clean" corpus — a router or agent that decides access based on natural-language judgment is trivially bypassable and gives an auditor nothing to check. The practical takeaway for a review: for any answer, you should be able to list every source touched, under whose entitlement, and trace every claim back to a citation — if you can't, the routing decision already broke something before the answer was even wrong.

**Q10: A risk committee is skeptical of a proposal to build a knowledge graph for AML monitoring instead of continuing to extend the existing RAG pipeline. How would you defend that specific architecture decision in the room?**

I'd open with the shape of the failure, not the technology: the questions AML analysts actually need answered — "is this beneficiary connected to a flagged account," "which merchants received funds from accounts linked to defaulted loans" — are relationship questions, and no amount of better chunking or reranking on the existing RAG pipeline manufactures a join that was never sitting in one document, because that's a structural gap, not a tuning gap. I'd bring the cost containment story before they ask about it, since a graph's cost is the first objection any risk-conscious stakeholder raises: 80% of this graph loads by deterministic mapping straight off core banking systems with zero LLM involvement and perfect precision, and the LLM extraction budget is reserved only for unstructured residue like correspondence and agreements, with confidence scores and a human review queue above a defined risk threshold — this isn't an open-ended AI project, it's a scoped data-engineering effort with a narrow, governed AI component. Then I'd turn the graph's biggest risk into its strongest argument: because it joins data that was deliberately kept separate, I'd show the access-control model that constrains traversal depth and edge types per role, not just node-level ACLs, and the fact that any agent-generated query runs read-only with cost limits — and I'd close on the property a risk committee actually wants from an AML system, which is that a graph's output is a traversable path, so a suspicious-activity flag comes with its own audit trail baked in, rather than a similarity score nobody can walk through in an examination. The one-sentence version I'd leave them with, using this chapter's template: control flow — or here, the query capability — needs to sit in a graph, because the questions are relationship-shaped and the path itself is the explanation regulators already ask us for, and that costs us ontology governance and entity-resolution operations we've scoped and bounded, not an open-ended one.
