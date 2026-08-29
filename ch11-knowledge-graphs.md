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
