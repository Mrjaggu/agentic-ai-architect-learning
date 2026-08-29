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
