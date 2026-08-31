# Chapter 11: Knowledge Graphs & Graph RAG

> Vector search answers "what is similar to this?" A graph answers "what is connected to this, and how?" Enterprise questions are mostly the second kind.

## 1. Concept

```text
            CUSTOMER
            /       \
       ACCOUNT ---- LOAN
          │           │
    TRANSACTION   COLLATERAL
          │
       MERCHANT
```

A knowledge graph stores **entities** (nodes), **relationships** (typed, directed edges), and **properties** — under an **ontology**: the schema declaring which entity types exist and which relationships are legal between them. The ontology is to a graph what the state schema is to Ch4: the design artifact that outlives every tool choice.

## 2. When a graph beats a vector store

Vector retrieval fails structurally (not fixably-with-better-embeddings) on: **multi-hop** questions ("which merchants received funds from accounts linked to defaulted loans?" — no document contains this; it must be *traversed*); **aggregation over relationships** ("how many customers share this address with a flagged account?"); **temporal linkage** ("what did we know about this customer when the loan was approved?"); and **explanation** ("why is this transaction suspicious?" — the answer *is* a path). If your questions decompose into similarity, use vectors. If they decompose into joins-with-meaning, use the graph.

## 3. Building the graph efficiently (your named question)

The cost is not the database — it's construction and maintenance. The discipline:

- **Ontology first, small.** Start with 5–8 entity types and the relationships your actual questions need. Ontologies grow well and shrink badly.
- **Structured sources first.** A bank's core systems already *are* entities and relationships — Customer/Account/Transaction land in the graph by deterministic mapping, no LLM needed, perfect precision. This is 80% of the value at 20% of the cost.
- **LLM extraction only for unstructured residue** (agreements, correspondence, notes) — extract against the ontology (constrained, not open-ended), with confidence scores and human review queues above a risk threshold.
- **Entity resolution is the hard part** — the same customer as "A. Sharma," "Anil Sharma," and a PAN. Blocking + matching + survivorship rules; your address-dedup embedding work is exactly this discipline. Bad resolution poisons every downstream traversal.
- **Incremental, event-driven updates** from source-system changes; never periodic full rebuilds. Timestamp edges (valid_from/valid_to) so the graph answers as-of questions.

## 4. Graph RAG: the retrieval patterns

- **Entity-anchored expansion**: link the query's entities to graph nodes, pull the k-hop neighborhood, serialize it (triples or prose) into context. The workhorse pattern.
- **Text-to-graph-query**: model generates Cypher/Gremlin against the ontology; run it; return rows. Powerful, needs query validation (read-only, cost-limited).
- **Hybrid vector + graph**: vector search finds relevant *documents*; the graph connects the *entities* they mention; both land in context. Chunks carry entity annotations so the two indexes cross-reference.
- **Community summaries** (à la Microsoft GraphRAG): pre-summarize graph neighborhoods for global "tell me about X's exposure" questions that neither top-k nor a single traversal answers.

## 4b. A traversal no vector store can do, visualized

```cypher
// "Which merchants received funds from accounts linked to defaulted loans?"
MATCH (l:Loan {status:'DEFAULT'})<-[:HOLDS]-(c:Customer)
      -[:OWNS]->(a:Account)-[:PAID]->(m:Merchant)
WHERE a.paid_ts > l.default_ts          // temporal edge: order matters
RETURN m.name, count(DISTINCT a) AS accounts, sum(a.amount) AS exposure
ORDER BY exposure DESC LIMIT 10
// The answer is a PATH — and the path *is* the explanation (see §8)
```

## 5. Trade-offs

Graphs cost: ontology governance (someone must own it), entity-resolution operations, and a second query language in the stack. They pay when relationship questions are frequent and high-value — in banking (fraud rings, exposure, KYC linkage) they are. Don't build a graph to answer questions vectors already answer; that's résumé-driven architecture.

## 6. Industry implementation

Neo4j/TigerGraph/Neptune for property graphs; banks have run entity graphs for AML for a decade — the new move is *wiring them into the agent's knowledge layer* rather than keeping them analyst-only. Microsoft GraphRAG mainstreamed community summaries; temporal-knowledge-graph memory (Zep/Graphiti-style, Ch9) shows the same machinery serving agent memory. The convergence to notice: **the graph is becoming the connective tissue between documents, structured data, and memory.**

## 7. Hands-on lab

Build the banking graph: ontology (Customer, Account, Transaction, Loan, Collateral, Merchant + 8 relationship types); load synthetic structured data deterministically; LLM-extract entities from 10 synthetic loan-agreement texts into the same ontology with confidence scores; implement entity-anchored expansion as a tool. Benchmark against pure vector RAG on 20 questions — half similarity-shaped, half traversal-shaped — and present the split result. (The split is the insight: each wins its half.)

## 8. Architect's take: the banking read

Fraud, AML, and credit exposure are *graph-native domains* — rings, layering, and connected-party exposure are literally path queries. An agent with graph tools can explain its suspicion as a path ("A→shared device→B→merchant M flagged twice"), which is exactly the explainability regulators ask of AI systems and vector similarity can never provide. Position the graph as the explainability substrate of the platform, not just another index.

## Governance & security lens

A graph's power is also its risk: it *joins data that was deliberately separated* — one traversal can aggregate customer, account, transaction, and relationship data into a profile no single source system would have released. So access control applies to traversals, not just nodes (entitlements limit hop depth and edge types per role); generated Cypher runs read-only with cost limits; and the ontology has an owner, because schema changes change what can be inferred. The flip side is a governance *asset*: paths are explanations, giving the explainability regulators ask for. Governing question: **what can this role learn from k hops that it couldn't learn from any single system it's entitled to — and is that acceptable?**

## Interview-ready lines

- "Vectors answer similarity; graphs answer connection; enterprise questions are mostly connection."
- "Structured sources build 80% of the graph deterministically — save the LLM for the residue."
- "Entity resolution is the hard part; a graph with bad resolution is confidently wrong at scale."
- "In banking, the graph is the explainability substrate — suspicion as a traversable path."


## Interview Questions & Answers

**Q1: Why would you introduce a knowledge graph instead of just tuning the vector RAG pipeline harder — better chunking, better embeddings, reranking?**

Because the failure isn't a retrieval-quality problem, it's a shape problem. A question like "which merchants received funds from accounts linked to defaulted loans?" has no single document that answers it — the answer only exists as a path across Customer, Loan, Account, and Merchant nodes, so no amount of chunking or reranking manufactures it. Vector search retrieves things that read as similar to the query; this question needs things that are *connected* to each other in a specific, typed way, which is a traversal, not a similarity score. The tell is in the question itself: if it decomposes into "find things like X," vectors win; if it decomposes into "find things joined to X through a relationship," you need the graph. In banking, multi-hop, aggregation-over-relationships, and explanation-as-a-path questions are common enough — fraud rings, AML linkage, exposure — that this isn't an edge case, it's a core workload.

**Q2: How do you decide, for a given enterprise question, whether to route it to vector retrieval or graph traversal?**

I look at how the question decomposes. If it's "what is similar to this document/clause/customer profile," that's a similarity query and belongs on vectors. If it's "what is connected to this, and how many hops away, through which relationship types," that's a graph query — multi-hop questions, aggregation over relationships, and temporal-linkage questions ("what did we know when the loan was approved?") all fall structurally outside what embeddings can do, no matter how good the embedding model gets. In practice I don't pick one system per use case, I run hybrid: vector search finds the relevant documents, the graph connects the entities those documents mention, and both land in the same context window, with chunks carrying entity annotations so the two indexes cross-reference. The lab benchmark in this chapter makes the point directly — on a question set that's half similarity-shaped and half traversal-shaped, each approach wins its own half, which is the actual argument for hybrid over "pick a winner."

**Q3: What happens if entity extraction gets it wrong — say the LLM merges two different customers into one node, or fails to link "A. Sharma," "Anil Sharma," and a PAN as the same person?**

This is entity resolution, and it's the hard part of the whole pipeline, not a footnote — a graph with bad resolution isn't unhelpful, it's confidently wrong at scale, because every downstream traversal inherits the error silently. A false merge quietly blends two customers' transaction histories into one profile, which in a KYC or exposure context is a materially wrong answer delivered with full graph-traversal confidence. A missed match does the opposite: it fragments one customer's real exposure across multiple nodes and undercounts risk. The mitigation is blocking, matching, and survivorship rules — the same discipline as address-dedup embedding work — plus confidence scores on any LLM-extracted edge or node so uncertain resolutions route to a human review queue above a defined risk threshold, rather than being written into the graph as fact.

**Q4: The graph still shows a loan as active, but it was closed last week in the core system — what breaks when an agent traverses that edge, and how do you prevent it?**

An agent that traverses a stale edge produces an answer that's internally consistent and completely wrong — it might explain a transaction as suspicious "funds paid from an account linked to a defaulted loan" when the loan was in fact settled, which in a compliance context is worse than no answer because it's delivered with the same confident, path-based explanation the graph is supposed to be trusted for. The fix in this architecture is incremental, event-driven updates from source-system changes rather than periodic full rebuilds, so the graph never carries a week-old view of a core banking fact. It also means timestamping edges with valid_from/valid_to so the graph can answer as-of questions honestly, and so a traversal can be checked against the edge's own freshness window before an agent treats it as current. Where sub-second freshness genuinely matters — active fraud holds, live credit lines — I'd read that one fact from the system of record at query time rather than trusting the graph copy at all.

**Q5: After an agent surfaces a fraud explanation like "A→shared device→B→merchant M flagged twice," what happens next — does the system act on it automatically?**

No — the path is evidence for a human decision, not an automated action, and that's actually the point of building the graph this way. Because the answer is a traversable path rather than an opaque similarity score, it routes cleanly into existing fraud-ops workflow: the path becomes the case narrative an investigator reviews, with each hop (shared device, shared merchant, flagged twice) auditable and challengeable rather than a black-box "the model is 87% confident." Downstream, that case gets a disposition — escalate, freeze, clear — and that disposition should feed back into the graph as a labeled outcome, because those labels are what let you validate whether the traversal pattern you flagged on is actually predictive over time. Treating the graph's output as an explanation surface for a human, not a decisioning engine, is also what keeps it defensible to a regulator asking why an account was actioned.

**Q6: Isn't a knowledge graph a lot more expensive to build and operate than a vector index — how do you justify that cost to the business?**

The honest framing is that the database itself isn't the cost — construction and maintenance are, specifically ontology governance, entity resolution operations, and running a second query language in the stack. I control that cost by getting 80% of the graph's value at 20% of the cost: a bank's core systems already *are* entities and relationships, so Customer, Account, Transaction load in by deterministic mapping with no LLM involved and perfect precision, and the LLM extraction budget goes only toward the unstructured residue — agreements, correspondence, notes — where deterministic mapping isn't possible. On the other side of the ledger, I don't build the graph to answer questions vectors already answer cheaply; that's résumé-driven architecture. I build it because fraud rings, AML layering, and connected-party exposure are literally path queries with no vector substitute, so the cost is justified use-case by use-case against a class of question the bank is already paying analysts to answer manually.

**Q7: A graph joins data that was deliberately kept separate across systems — what data security risks does that introduce, and how do you mitigate them?**

The risk is that a single traversal can aggregate customer, account, transaction, and relationship data into a profile that no individual source system would ever have released on its own — the graph's whole value proposition (connecting things) is also its exposure surface. A role that's entitled to read account balances in one system and correspondence notes in another might, through k hops of traversal, infer something neither system alone would disclose, like a customer's full connected-party network or undisclosed related-party exposure. The mitigation is to treat this as a first-class governance question, not an afterthought: access control has to apply to the traversal itself, not just to nodes, limiting hop depth and permitted edge types per role, and any LLM-generated graph query runs read-only with cost limits so it can't be used to go fishing across the joined data. The governing question I keep coming back to is: what can this role learn from k hops that it couldn't learn from any single system it's entitled to — and is that acceptable?

**Q8: For the text-to-graph-query pattern, where the model writes Cypher or Gremlin directly, what guardrails do you put around that before it touches production data?**

First, the generated query runs read-only against the graph, full stop — no agent-generated traversal should ever have write access, because a malformed or adversarially-prompted query could otherwise mutate relationship data that downstream compliance processes depend on. Second, every generated query is cost-limited — bounded hop depth, bounded result size, and a query timeout — so a runaway or maliciously broad traversal can't do the graph equivalent of a full-table scan across joined customer data. Third, the query targets the ontology, not free-form graph structure, meaning the model is constrained to entity and relationship types that are declared and owned, which is also what makes the query auditable after the fact. And because the ontology defines what can legally be inferred, changes to it go through the same owner and review process as a schema change to a core system, since a broader ontology silently broadens what any approved query is capable of learning.

**Q9: How do you enforce least-privilege access control over graph traversal, versus just locking down individual nodes?**

Node-level ACLs alone don't work for a graph, because the sensitive thing is often what a legal traversal across several individually-authorized nodes reveals in combination — a role can be entitled to read every node it touches and still learn something none of those systems would disclose alone. So entitlements need to constrain the traversal itself: how many hops a role can expand from a query entity, and which edge types it's allowed to follow, not just whether it can see a given node. That's enforced at the query layer — whether traversal is entity-anchored expansion or text-to-graph-query, the hop-depth and edge-type limits apply before results are serialized into context, and generated Cypher is read-only with cost limits as a second line of defense. The test I apply to any new role or agent tool is the same governing question from the governance lens: what can this role learn from k hops that it couldn't learn from any single system it's entitled to, and is that acceptable — if the answer is no, the entitlement needs a tighter hop-depth or edge-type restriction, not a blanket deny on the whole graph.

**Q10: How do you keep a production knowledge graph fresh without doing expensive full rebuilds — what does that pipeline actually look like?**

The rule is incremental, event-driven updates from source-system changes, never periodic full rebuilds — a nightly full rebuild both wastes compute reprocessing unchanged data and leaves the graph stale for however long the batch window is, which is unacceptable when an agent is traversing loan-status or account-linkage edges for a fraud decision. Structured sources — Customer, Account, Transaction, Loan — update by deterministic mapping the moment the source system changes, since that's a mechanical transform, not an LLM call. For the LLM-extracted residue — entities pulled from agreements or correspondence — the update path re-extracts only the changed documents against the same constrained ontology, with confidence scores, rather than reprocessing the corpus. Every edge carries valid_from/valid_to timestamps so the graph can honestly answer as-of questions and so a traversal can be checked for freshness rather than assumed current, and entity resolution runs continuously rather than as a batch step, since a late-arriving name variant or PAN match shouldn't wait for the next rebuild to resolve.

**Q11: Design a system for a bank that needs to map a customer's relationships across accounts, loans, and connected parties for AML monitoring — walk me through the architecture.**

I'd start with the ontology, kept small and specific to the questions AML analysts actually ask — Customer, Account, Loan, Collateral, Merchant, plus the relationship types that connect them (HOLDS, OWNS, PAID, GUARANTEES, SHARES_ADDRESS, SHARES_DEVICE) — because ontologies grow well and shrink badly, so I'd resist adding entity types speculatively. Structured core-banking data loads deterministically with no LLM involved, since Customer-Account-Loan relationships already exist as foreign keys in source systems; LLM extraction is reserved for unstructured residue like loan agreements and customer correspondence, run against the same ontology with confidence scores and a human review queue above a risk threshold. For retrieval I'd implement entity-anchored expansion as the workhorse tool — anchor the query's entities to graph nodes, pull the k-hop neighborhood, serialize it into context — and add text-to-graph-query for analysts who need ad hoc traversals, with that path read-only and cost-limited. Updates are incremental and event-driven off core-system changes with valid_from/valid_to timestamps on edges, entity resolution runs continuously with human review for low-confidence merges, and access control constrains hop depth and edge types per analyst role so the same governing question applies: what can this role learn from k hops that it couldn't learn from any single system it's entitled to.

**Q12: How specifically does GraphRAG improve multi-hop reasoning over standard RAG — can you give a concrete example?**

Standard RAG retrieves chunks that are semantically similar to the query and hopes the answer is sitting inside one of them; multi-hop questions fail this by construction because the answer is distributed across facts that individually look unrelated to the query. Take "which merchants received funds from accounts linked to defaulted loans" — no chunk in any document contains that sentence's answer, because it requires joining a loan's default status, to the customer who holds it, to the accounts that customer owns, to the payments those accounts made, filtered by timing. Graph RAG answers this because the graph already stores those relationships as typed edges, so entity-anchored expansion or a generated Cypher query traverses Loan→Customer→Account→Merchant directly and returns the join result, with the traversal order enforced by the temporal edge (payment must be after default) so the "linked to" isn't just co-occurrence. The result is also its own explanation — the path itself shows the reasoning chain a reviewer or regulator can walk, which a top-k similarity match never produces even when it accidentally retrieves the right documents.
