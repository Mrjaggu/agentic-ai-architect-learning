# Chapter 12: Agentic Retrieval & Knowledge Routing

> The question is no longer "how do I retrieve?" but "which knowledge source should answer this, and who decides?"

## 1. Concept

```text
                USER QUESTION
                      │
                      ▼
                KNOWLEDGE ROUTER
                      │
     ┌──────────┬─────┴─────┬──────────┐
     ▼          ▼           ▼          ▼
  Vector     Knowledge     SQL /     Live
  (Ch10)     Graph (Ch11)  semantic  APIs
                           layer
```

The agent (or a router in front of it) classifies the question's *shape* — similarity, traversal, aggregation, or current-state — and dispatches accordingly. Each source is exposed as a tool with a clean contract (Ch13); the routing decision is itself evaluable (Ch17).

## 2. The routing taxonomy

| Question shape | Source | Example |
|---|---|---|
| "What does the policy say about…" | Vector/RAG | Semantics over documents |
| "How is X connected to Y…" | Graph | Relationships, paths, rings |
| "How many / sum / trend…" | SQL/semantic layer | Aggregation over records |
| "What is the balance *now*…" | Live API | Current state, real-time |
| Mixed | Multiple + synthesis | Most real questions |

The mixed row is the point: "Should we increase this customer's card limit?" needs policy (vector), exposure (graph), history (SQL), and current balance (API). Routing is usually *decomposition*, not selection.

## 3. Agentic retrieval patterns

- **Query planning**: decompose the question into sub-queries per source; run (parallel where independent); synthesize with per-source citations.
- **Multi-hop**: use hop-1 results to form hop-2 queries ("find the policy → find exceptions to that clause → check if customer qualifies").
- **Self-correcting retrieval**: grade the retrieved evidence ("does this actually answer the question?"); on failure, rewrite the query, try the *next-best source*, or escalate to "insufficient evidence" — never generate from garbage. This closes RAG's can't-recover failure from Ch1.
- **The semantic layer for SQL**: text-to-SQL against raw schemas is fragile and dangerous; text-to-SQL against a governed semantic layer (defined metrics, joins, row-level security baked in) is deployable. The semantic layer is to structured data what the ontology is to the graph.

## 3b. The cascade router, visualized

```python
def route(q: str) -> list[Source]:
    if m := POLICY_PATTERNS.match(q):   return [VECTOR]      # rules for the head
    if m := METRIC_PATTERNS.match(q):   return [SQL]         # cheap, predictable
    plan = llm(f"Decompose into sub-queries per source:\n{q}",
               schema=RoutePlan)                              # model for the tail
    return plan.legs                    # e.g. [VECTOR, GRAPH, API] — decomposition

evidence = gather(route(q))             # parallel where independent
if not grade(evidence, q).sufficient:   # self-correction: check before generating
    evidence = retry_next_best(q) or return INSUFFICIENT_EVIDENCE
```

## 4. Design decisions

- **Who routes?** Deterministic classifier for stable, high-volume traffic (cheap, predictable, evaluable); model-based routing for the long tail; in practice a cascade — rules first, model fallback. Same owner-of-control-flow logic as Ch4.
- **Contracts over cleverness**: each source-tool declares what shapes it answers, cost, latency, and freshness. The router reasons over declared contracts, not vibes.
- **Failure semantics per source**: vector miss → try graph? SQL timeout → degrade to cached? Declare the fallback chain; don't improvise it at runtime.
- **Citations by source type**: clause lineage (vector), path (graph), query + rows (SQL), endpoint + timestamp (API). Synthesis must preserve per-claim attribution.

## 5. Trade-offs

Routing adds a decision layer that can itself be wrong — measure routing accuracy as a first-class eval (it's the cheapest place to fix quality). Decomposition multiplies latency and cost; parallelize independent legs and cache aggressively. And beware the "one more source" temptation: every source added must earn its contract, or the router's job degrades combinatorially.

## 6. Industry implementation

This is the architecture behind every serious "enterprise copilot": Glean-class assistants, Databricks/Snowflake agents over semantic layers, deep-research systems doing plan-retrieve-grade-synthesize loops. Notice the shared skeleton — planner, per-source tools, evidence grading, synthesis with citations — that skeleton is Portfolio Project 2.

## 7. Hands-on lab (Portfolio Project 2 core)

Build the Knowledge Intelligence Agent: the Ch10 vector leg, the Ch11 graph, a small SQL mart with a minimal semantic layer (5 defined metrics), and one mock live API. A cascade router (rules → model), decomposition planning, evidence grading with one retry, and synthesis with per-claim citations. Eval on 40 questions across the four shapes + 10 mixed; report routing accuracy separately from answer quality. Demonstrable insight: fixing routing errors lifts answer quality more per unit effort than tuning any single retriever.

## 8. Architect's take: the banking read

Routing is also an *entitlement* boundary: the same question from a teller and a credit officer should route to the same sources with different row-level access — enforce entitlements inside each source (semantic layer RLS, graph filters, document ACLs), never in the router's prompt. And the "insufficient evidence" path is a compliance feature: a banking agent that answers anyway is generating unauthorized advice; one that says "I need the credit bureau result, which I can't access for you" is behaving exactly as a regulated institution requires.

## Governance & security lens

Routing is where entitlements must *travel*: the user's identity accompanies every leg of a decomposed query, and each source enforces its own access rules (RLS in the semantic layer, ACL filters in retrieval, traversal limits in the graph) — the router's prompt is never the enforcement point. The routing log itself is an audit record: which data sources were consulted to answer what, for whom. And "insufficient evidence" is a compliance feature — an agent that answers anyway is generating unauthorized advice. Governing question: **for any answer, can we list every source touched, under whose entitlement, and show each claim's citation?**

## Interview-ready lines

- "Routing is usually decomposition, not selection — real questions span sources."
- "Rules route the head of the distribution; the model routes the tail."
- "Text-to-SQL is deployable exactly when there's a semantic layer under it."
- "Routing accuracy is the cheapest quality lever in the whole knowledge stack — measure it separately."


## Interview Questions & Answers

**Q1: Why not just run every question through the same RAG/vector pipeline instead of building a router?**

Because most banking questions aren't semantic-similarity questions at all — "how many accounts crossed 90 DPD this quarter" is an aggregation, "is this beneficiary connected to a flagged account" is a graph traversal, and "what is the balance right now" needs a live API call, not an embedding lookup. Forcing all four question shapes through vector search either fails silently (a vector index has no concept of "sum" or "current") or gets hacked around with brittle prompt engineering. A router lets each source do what it's actually good at, and it makes the retrieval strategy itself something you can evaluate and improve, rather than one monolithic pipeline you can only tune by adding more chunks. The cost of skipping it isn't a slightly worse answer — it's confidently wrong aggregation or traversal answers coming out of a tool that was never built to compute them.

**Q2: How do you decide, given a question, whether it should go to the vector store, the knowledge graph, SQL/semantic layer, or a live API?**

Classify the question by its *shape*, not its topic: "what does the policy say" is a similarity match over documents and goes to vector/RAG; "how is X connected to Y" is a traversal and goes to the graph; "how many / sum / trend" is aggregation over records and belongs in SQL against a governed semantic layer; and "what is the balance right now" is a current-state lookup that only a live API can answer correctly. In practice most real questions are mixed — a credit-limit-increase question needs the policy (vector), the customer's exposure network (graph), transaction history (SQL), and today's balance (API) all at once. So routing isn't really "pick one source," it's decomposition into per-source sub-queries that get gathered, graded, and synthesized with per-claim citations.

**Q3: What happens if the router sends a question to the wrong source, or a question actually needs two sources at once?**

This is exactly why routing is treated as decomposition rather than single-source selection — the router's real job on a mixed question like "should we increase this customer's card limit" is to split it into legs (policy from vector, exposure from graph, history from SQL, current balance from API) and run the independent ones in parallel. When a single leg is simply misrouted, self-correcting retrieval catches it: the evidence is graded against the original question, and if it doesn't actually answer it, the system rewrites the query, tries the next-best source, or escalates to an "insufficient evidence" response rather than synthesizing from a wrong or empty result. The failure mode to avoid is generating an answer from mismatched evidence just because *some* evidence came back — grading before synthesis is the guardrail that prevents that.

**Q4: Walk through what happens after retrieval returns evidence that's actually insufficient or irrelevant — what's the downstream path?**

The evidence gets graded against the original question before anything is synthesized — "does this actually answer what was asked" — and if it fails that check, the system doesn't paper over it with a generic LLM answer. It retries with a rewritten query, falls back to the next-best source declared in that source's failure-semantics contract (vector miss → try graph, SQL timeout → degrade to cache), and if none of that resolves it, the agent returns an explicit "insufficient evidence" response instead of generating from garbage. That's the mechanism that closes RAG's classic can't-recover failure mode — the system fails loudly and specifically rather than fluently and wrong, which in a banking context is the difference between a controlled gap and unauthorized advice.

**Q5: What's the cost trade-off of adding query decomposition and routing versus just running one fixed retrieval pipeline for everything?**

A fixed pipeline is cheap and predictable but wrong for most non-trivial questions, so the real comparison isn't "router vs. no router," it's how much routing intelligence you pay for. A cascade design keeps cost down: deterministic rule-based classifiers handle the high-volume, stable head of the query distribution at near-zero marginal cost, and the more expensive model-based decomposition is reserved for the long tail where rules can't confidently classify. Decomposition itself multiplies latency and LLM spend because each sub-query is effectively its own retrieval call, so independent legs need to run in parallel and results need aggressive caching, or the cost curve gets ugly fast. The rule of thumb worth defending to a cost-conscious stakeholder is that every additional source in the router must earn its contract — bolting on "one more source" degrades routing accuracy and cost combinatorially, not linearly.

**Q6: What data security implications come from a single router being able to reach vector stores, SQL, a graph, and live APIs?**

Each backend has different sensitivity and a different native control mechanism — document ACLs on the vector index, row-level security in the semantic layer, traversal limits in the graph, and auth scopes on the API — so a router that can reach all of them is only as safe as the weakest of those enforcement points, and it must never become a single point that bypasses any of them. The critical design rule is that entitlements are enforced *inside* each source, never inside the router's prompt or reasoning: a router that decides "this user can see this" based on natural-language instructions is trivially prompt-injectable and audit-proof. Because a decomposed query can touch three or four systems for one answer, the routing log itself becomes a security artifact — it has to capture which sources were consulted, under whose identity, for every leg, so a security review can reconstruct exactly what data was touched to produce any given answer.

**Q7: What guardrails would you put around an agentic retrieval/routing system before letting it face customers or staff?**

The first guardrail is evidence grading before synthesis — never let the agent generate an answer from retrieved evidence that hasn't been checked for relevance, and never let it fabricate when evidence is missing; "insufficient evidence" has to be a legitimate, first-class output, not a failure state to be engineered away. The second is declared failure semantics per source rather than improvised fallback — vector miss escalates to graph, SQL timeout degrades to cache, and those chains are defined at design time, not decided by the model at runtime under pressure. Third, citations must be preserved by source type through synthesis — clause lineage for vector, path for graph, query-plus-rows for SQL, endpoint-and-timestamp for API — so every claim in the final answer traces back to something a reviewer can verify. And routing accuracy itself needs to be evaluated as its own metric, separate from answer quality, because a router that silently degrades is the cheapest and most dangerous failure to miss.

**Q8: How do access control and least-privilege actually get enforced across a multi-source router — where does entitlement checking belong?**

Entitlements have to travel with the query through every leg of a decomposition, not live in the router's prompt: the same question asked by a teller and a credit officer should be routed to the *same* sources, but each source enforces different row-level access for each identity — RLS in the semantic layer, ACL filters in the vector retriever, traversal-depth limits in the graph. This means the router's job is purely about question shape, and each downstream tool is independently responsible for refusing or filtering based on the caller's actual entitlement, so a compromised or manipulated router can't leak data it was never authorized to fetch in the first place. Treating the router as the enforcement point is a common design mistake — it's convenient because it's one place to write the logic, but it's also one place an attacker or a bad decomposition can bypass, whereas per-source enforcement fails closed even if the router's reasoning goes wrong.

**Q9: In production, how do you monitor whether the router is actually working, and what's the fallback when it isn't?**

Routing accuracy needs to be tracked as its own metric, separate from downstream answer quality, precisely because it's the cheapest place in the whole stack to catch and fix a quality regression — if the router silently starts misclassifying a question shape, every downstream retriever can be performing perfectly and the answer will still be wrong. That means logging the router's decision (which source or sources, and why) alongside the eventual evidence-grading outcome, so you can distinguish "router sent it to the wrong place" from "the right source came back empty." Each source-tool should declare its own failure semantics — timeout, empty result, low-confidence match — so the system degrades predictably: retry with a rewritten query, fall back to the next-best declared source, or serve from cache, rather than the model improvising a fallback at runtime. Operationally, this looks like a labeled eval set of question-shape examples run continuously against the live router, plus alerting when the observed routing distribution drifts from the expected one.

**Q10: Design the knowledge routing layer for a bank's internal copilot that has to answer questions spanning policy documents, a customer relationship graph, core banking SQL, and a live credit bureau API — how would you structure it?**

I'd start with a cascade router: deterministic pattern rules classify the high-volume, predictable head of the traffic straight to vector (policy language), SQL (metric/aggregation phrasing), graph (relationship phrasing), or API (current-state phrasing), and only the ambiguous tail falls through to an LLM-based decomposition planner that splits a question like "should we raise this customer's limit" into parallel sub-queries per source. Each source is wrapped as a tool with a declared contract — what shapes it answers, its cost, latency, and freshness — and each one independently enforces entitlements for the caller's identity, so a teller and a credit officer hit the same router logic but get different rows back. Evidence from every leg gets graded against the original question before synthesis; anything that fails grading triggers a rewrite, a fallback to the next-best source, or an explicit "insufficient evidence" response, and the final answer preserves per-claim citations by source type so a compliance reviewer can trace exactly what backed each sentence. I'd eval this continuously on a labeled set spanning all four question shapes plus mixed/decomposed questions, reporting routing accuracy separately from answer quality, because that's the fastest lever for catching regressions before they reach a customer.

**Q11: Why is text-to-SQL against a raw database schema considered risky in production, and what changes when there's a semantic layer underneath it?**

Text-to-SQL against a raw schema is fragile because the model has to correctly infer joins, column semantics, and business logic (what counts as "active," how metrics are actually defined) from table and column names alone, and it's dangerous because there's nothing stopping a generated query from reading rows the caller isn't entitled to or running an expensive unbounded scan. A governed semantic layer fixes both problems at once: metrics, joins, and row-level security are defined once by people who own the data model, so the LLM is generating queries against a constrained, pre-vetted surface rather than the raw schema, and entitlement enforcement happens automatically rather than depending on the model getting a WHERE clause right. That's the same relationship the ontology has to the graph layer — in both cases, you're putting a governed abstraction between the model's natural-language reasoning and the raw structured store, which is what makes the pattern deployable in a regulated environment instead of just a demo.

**Q12: How would you implement multi-hop retrieval for a question where the answer to one sub-query determines what to look up next?**

Multi-hop retrieval means the first hop's results shape the second hop's query rather than firing all sub-queries independently and hoping synthesis reconciles them — for example, find the relevant policy clause first, then use that clause's text to find its exceptions, then check whether the specific customer's facts satisfy or trip those exceptions. Architecturally this needs the router/planner to be a loop, not a single decomposition pass: gather evidence, grade it, and only then decide whether the question is answered or whether another hop is needed, with each hop potentially targeting a different source (policy clause from vector, then the exception check against the customer's exposure in the graph or SQL). The main risks are runaway cost and latency if hops aren't bounded, and citation drift if you don't keep per-hop provenance — the final synthesized answer still has to show which claim came from which hop and which source, or a reviewer has no way to audit a multi-step chain of reasoning that produced the final answer.
