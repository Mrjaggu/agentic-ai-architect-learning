# Chapter 10: Enterprise RAG, Properly

> RAG didn't die when agents arrived — it became one knowledge source among several, and the bar for doing it well went up.

## 1. Repositioning RAG

In an agentic platform, RAG is a *service the agent calls*, not the application itself:

```text
                 KNOWLEDGE LAYER
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Documents      Structured       Live data
   (this ch.)     (SQL/semantic)   (APIs/events)
        │              │              │
        └──── the agent routes among them (Ch12) ────┘
```

This chapter is about making the document leg excellent, because "agentic" doesn't fix bad retrieval — it just retries it.

## 2. The pipeline, with the decisions that matter

**Ingestion** — parsing quality bounds everything downstream (tables, scanned pages, headers/footers; you know this pain from document intelligence work). Track document *lineage*: source system, version, classification.

**Chunking is a design decision, not a preprocessing detail.** Structure-aware beats fixed-size (respect sections/clauses); attach metadata (doc, section, effective date, product); size for the *retrieval unit a human would cite*. Policy documents chunk by clause; FAQs by pair; contracts by section. Late/hierarchical chunking (retrieve small, expand to parent) gets you precision and context together.

**Indexing** — embeddings for semantic similarity **plus** BM25/keyword for exact terms (product codes, section numbers, names). Hybrid search is the default in 2026, not an optimization; pure vector search whiffs on the exact identifiers enterprise queries are full of.

**Retrieval** — top-k similarity is a *candidate generator*. Then: metadata filtering (product, date, jurisdiction) *before* or alongside similarity; **reranking** with a cross-encoder over the candidates (the single highest-ROI upgrade in most pipelines); deduplication and diversity.

**Generation contract** — grounded answers with citations to chunk lineage, and an explicit "not found in sources" path. An enterprise RAG that can't say "I don't know" is a liability generator.

## 2b. The retrieval pipeline, visualized

```python
def retrieve(query, user):
    cands = (vector_search(query, k=40)               # candidate generator...
             + bm25_search(query, k=40))              # ...hybrid: ids need keywords
    cands = [c for c in cands
             if c.meta["acl"] in user.entitlements    # entitlements at query time
             and c.meta["effective"] covers today]    # the CURRENT policy version
    ranked = cross_encoder.rerank(query, cands)[:5]   # the highest-ROI step
    return ranked or NOT_FOUND                        # "not in sources" is an answer
```

## 3. Freshness & re-indexing

Knowledge changes; embeddings are snapshots. Design for it: incremental ingestion on document change events; versioned indexes with **blue/green re-indexing** (build the new index alongside, validate with an eval set, cut over, keep rollback) for embedding-model upgrades; effective-dating so "what was the policy in March?" is answerable. Retrieval evals (Ch17) run on every index build — recall@k on a golden set is your regression gate.

## 4. Trade-offs

- Bigger chunks: more context per hit, worse precision, costlier windows. Smaller: the reverse. There is no universal answer — only per-corpus tuning against an eval set.
- Reranking adds ~100–300ms and a model dependency; almost always worth it above trivial corpora.
- Hybrid search doubles index maintenance; still the default because enterprise queries are id-heavy.
- Multilingual (your Siddhi world): multilingual embedding models vs translate-then-embed — decide with evals per language pair, not vibes.

## 5. Industry implementation

The mature stack: object store → parsing service → chunker → dual index (vector + keyword) → retrieval API with filters + reranker — exposed to agents *as a tool* with a clean schema (Ch13). Managed services (Bedrock KBs, Azure AI Search, Vertex) give you the skeleton; the differentiating work — chunking policy, metadata schema, eval set, freshness pipeline — is never in the box.

## 6. Hands-on lab

Build the policy-document leg for the banking agent: ingest 20+ real-ish policy PDFs; structure-aware chunking with metadata; hybrid index; retrieval API with filter + rerank. Then build the eval set *first-class*: 50 questions with known source clauses; measure recall@5 and answer groundedness; then break it (swap to fixed-size chunks, drop the reranker) and quantify the damage. That table is the portfolio artifact.

## 7. Architect's take: the banking read

In a bank, RAG's differentiators are governance-shaped: retrieval must respect document classification and the *user's* entitlements (filter at query time by ACL, not by hoping the corpus is clean); citations must point to the authoritative version of the policy, because "the bot said X" incidents end with "which document version said X?"; and effective-dating is not optional when regulations change quarterly. Bad RAG in a bank isn't just unhelpful — it's an incorrect-disclosure risk.

## Governance & security lens

RAG's core risk in an enterprise is *wrong or unauthorized disclosure*: retrieval must filter by the requesting user's entitlements at query time (never rely on a "clean" corpus), respect document classification, cite the authoritative version (incidents end with "which document version said that?"), and honor effective dates. The corpus is also an injection surface — a poisoned document is an instruction delivery vehicle, which is why retrieved content carries trust labels (Ch8). Governing questions: **can a user ever retrieve a chunk their role couldn't read at the source, and can we trace every generated claim to a governed document version?**

## Interview-ready lines

- "Top-k similarity is a candidate generator; filtering and reranking make it retrieval."
- "Chunking is a design decision with an eval, not a preprocessing default."
- "Hybrid search is the default because enterprise queries are full of exact identifiers."
- "An enterprise RAG that can't say 'not in sources' is a liability generator."
