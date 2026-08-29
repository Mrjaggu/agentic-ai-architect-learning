# Chapter 9: Memory Architecture

> The design question is not "how do agents remember?" — it's "what should be remembered, for how long, visible to whom, and forgettable on demand?"

## 1. The taxonomy

| Memory type | Contains | Lifetime | Example |
|---|---|---|---|
| Short-term | Current conversation | Session | The last few turns |
| Working | Current task state | Run (Ch4 state) | Plan, intermediate results |
| Episodic | What happened before | Long | "Last month this customer disputed a charge" |
| Semantic | Facts we know | Long | "Customer prefers Hindi; salaried; has a home loan" |
| Procedural | How to do things | Long | Learned resolutions, playbooks |

Short-term and working memory are really *state* (Ch2's distinction). The architecture problem is the long-term kinds: extraction, storage, retrieval, and governance.

## 2. The memory pipeline

```text
Conversation/run
      │  extract (what's worth keeping? — a model decision)
      ▼
  consolidate (merge with what's known; update, don't duplicate;
      │        resolve contradictions; decay/expire)
      ▼
    store (vector, graph, or structured — often all three)
      │  retrieve (what's relevant to THIS moment? → into context, Ch8)
      ▼
   apply
```

Each stage is a failure mode: extract too eagerly and you store noise (and liabilities); consolidate poorly and memories contradict; retrieve badly and the agent "remembers" irrelevant things at the wrong moment.

## 3. The 2026 framework landscape (architect's comparison)

Mem0, Zep, Letta, LangMem, Cognee dominate the open conversation; **Bedrock AgentCore Memory** is the managed entrant — explicit short-term (multi-turn, session-scoped) and long-term (cross-session, sharable across agents) stores with extraction strategies you configure rather than build, attractive when the rest of the stack is AgentCore (Ch7 §6b) and subject to the same governance axes below. Compare them on the axes that matter, not features: *where extraction runs* (inline vs async), *storage model* (vector-only vs temporal knowledge graph — Zep/Cognee lean graph, which pays off exactly when relationships and time matter), *whether consolidation is real* (updating and contradiction-handling vs append-forever), and *governance surface* (per-user isolation, TTL, deletion APIs). For a bank, the last axis is usually decisive — and it's the one feature checklists skip. Build-vs-buy: memory frameworks are young; the storage layer is replaceable, but the *schema of what you remember* is yours forever — design that yourself regardless.

## 3b. A governable memory record, visualized

```python
class Memory(BaseModel):
    customer_id: str            # partition key — isolation is STRUCTURAL
    kind: Literal["episodic", "semantic", "procedural"]
    fact: str                   # "prefers Hindi for service calls"
    source_ref: str             # trace/conversation id — provenance = deletability
    purpose: str                # DPDP purpose limitation, checked at retrieval
    ts: datetime
    ttl_days: int | None        # stale facts expire; balances aren't facts

def recall(customer_id, query, purpose):
    return search(query,
        filter={"customer_id": customer_id, "purpose": purpose})  # BEFORE similarity
```

Everything the governance sections below demand is a *field*, not a hope.

## 4. Design decisions

- **Remember by policy, not by default.** Define categories the system MAY store (stated preferences, case history) and categories it must NOT (inferred traits, sensitive attributes without purpose). Extraction runs against the policy.
- **Provenance per memory**: source conversation, timestamp, confidence. Unattributable memories are undeletable and unauditable.
- **Scope boundaries**: per-customer memory must be structurally isolated (partition keys, not prompt discipline) — retrieval for customer A must be *unable* to return customer B.
- **Expiry as a feature**: balances change, addresses change. Prefer durable phrasings, timestamp everything, decay what's stale.
- **Forgetting on demand**: deletion is an API and a regulatory obligation (DPDP right to erasure), which means derived artifacts (summaries, embeddings) must be traceable to their sources.

## 4b. Learning and adaptation — memory's active cousin

Memory stores; **learning changes future behavior**. Without touching model weights, agent systems adapt through: **procedural memory** — successful resolutions distilled into playbooks the agent retrieves ("last 5 KYC-exception cases resolved via steps X-Y-Z"); **feedback incorporation** — HITL corrections (Ch20) and eval outcomes (Ch17) written back as do/don't exemplars, making the traces→evals flywheel also a traces→behavior flywheel; **self-reflection** — post-run critique ("what would I do differently?") stored and retrieved for similar future tasks (the Reflection pattern, Ch3, pointed at the long term). The governance catch: a system that adapts is a system that *drifts* — learned content needs the same provenance, review thresholds, and rollback as any memory write, and in a bank, a changed behavior needs a traceable cause (an MRM expectation, Ch20). Design learning as versioned, reviewable memory — never as silent accumulation.

## 5. Why bad memory is worse than no memory

Wrong personalization (acting on stale or misattributed facts) destroys trust faster than forgetfulness. Memory is also an attack surface — a poisoned memory persists across sessions, unlike a poisoned context (Ch19). And every stored personal fact is a data-protection liability with a lifecycle. The bar for writing to memory should be *higher* than the bar for using context.

## 6. Industry implementation

Consumer assistants (ChatGPT memory, Claude memory) converge on: explicit extraction with user visibility, editable/deletable stores, and category exclusions for sensitive data. Enterprise deployments add tenancy isolation and retention schedules. Notice the pattern: the mature implementations spend most of their design on *governance*, not recall quality.

## 7. Hands-on lab

Build a minimal memory layer for the banking agent: an extraction step (small model + policy prompt) writing typed memories `{subject, fact, source_ref, ts, ttl}` to Postgres + embeddings; retrieval that filters by customer partition *before* similarity; a consolidation job that merges duplicates and expires stale rows; and a `DELETE /customers/{id}/memories` that provably clears derived data. Then attempt a cross-customer retrieval and prove it structurally impossible.

## 8. Architect's take: the banking read

RBI/DPDP framing turns memory design into three enforceable statements: (1) purpose limitation — memories are stored under a named purpose and retrieved only for it; (2) minimization — the extraction policy is a allowlist, reviewed like any data-collection form; (3) erasure — deletion cascades to embeddings and summaries, demonstrable in audit. An agent memory system you cannot make these three statements about is not deployable in an Indian bank, whatever its recall benchmarks say.

## Governance & security lens

Memory is the layer where a governance failure *persists*: a stored inference, a cross-customer leak, or a poisoned memory outlives the session that created it. The controls are structural, not procedural — allowlist extraction policy, purpose tags checked at retrieval, partition isolation, provenance on every record, TTLs, and erasure that cascades to derived artifacts. Governing questions: **can we show a regulator every memory held about a customer, why each was collected, and delete them provably — and can any write reach memory without passing the policy?** (This chapter and Ch19/20 are where the lens originates; the summary here is the checklist.)

## Interview-ready lines

- "The bar for writing memory should be higher than the bar for using context — memory persists, and so do its mistakes."
- "Isolation by partition key, not prompt discipline."
- "A memory without provenance is undeletable — and therefore non-compliant by construction."
- "Frameworks are replaceable; your memory schema and policy are the architecture."
