# Chapter 8: Context Engineering

> Prompt engineering asks "how do I phrase this?" Context engineering asks "what should the model see at this exact moment?" The second question is an architecture question.

## 1. The architecture

Every model call is a context assembly decision:

```text
SYSTEM (identity, rules, tool schemas)
+ TASK (the goal, its constraints)
+ MEMORY (relevant cross-run facts)      ← selected
+ KNOWLEDGE (retrieved docs/rows)        ← selected
+ HISTORY (state so far)                 ← compressed
+ TOOL RESULTS (recent observations)     ← shaped
──────────────────────────────────────────
= the context window for THIS call
```

The harness assembles this deterministically each turn (Ch5). The engineering discipline is deciding the *policy*: what gets in, in what form, in what order, within what budget.

## 2. Why the industry needed it — a wrong recommendation, traced to a bad window

Long context windows made the problem worse, not better, and the mechanism is worth tracing through a concrete failure rather than stating as a slogan. Three empirical realities forced the discipline: **degradation** — models reason worse over 100k tokens of mush than 8k of signal ("lost in the middle" is real, and it's not a training artifact that newer models simply fix; it recurs across model generations because attention genuinely dilutes with irrelevant tokens); **cost** — context is billed per call, and a 20-turn loop re-sends it 20 times, so an unmanaged context grows the bill quadratically with conversation length; **poisoning** — one bad retrieved document or stale tool result steers every subsequent decision, because the model has no way to know a fact in its window is wrong.

Here's poisoning as an incident, not an abstraction. A card-services agent's `check_policy` step retrieves relevant policy documents via RAG (Ch10) to decide whether a disputed transaction qualifies for a fee waiver. The retrieval pipeline's index hadn't been re-run since a policy update three weeks earlier — an operational gap, not a bug in the agent itself — so the top-ranked retrieved chunk was the *previous* version of the fee-waiver policy, which had a more generous threshold than the current one. Nothing in the context window flagged this chunk as stale; it looked exactly like a current, authoritative policy document, because to the retrieval system it was simply the highest-scoring match. The model reasoned correctly *given what it saw* — that's the uncomfortable part of a poisoning failure: the model's reasoning step, examined in isolation, looks fine. It approved a fee waiver that the current policy no longer permitted, and it kept doing so consistently for every similar dispute until someone doing a routine policy-audit sample noticed a mismatch. The root cause traced back not to the model, not to the harness's tool policy, but specifically to context assembly having no mechanism to detect or flag a stale retrieval — which is the argument for treating "what entered this window, and how do we know it's current" as its own design surface, not an assumed property of retrieval working correctly.

## 3. The techniques — worked through the dispute-investigation agent

Ground each technique in the same running example so the abstractions don't float free of a real system.

- **Selection** — retrieve/include only what this step needs. The question is per-*step*, not per-task: `fetch_transaction` needs the transaction record and nothing else; `check_policy` needs the retrieved policy chunks and the transaction's category, not the customer's entire profile history. Feeding `check_policy` the full context every other node used is exactly how the poisoning incident in §2 got harder to catch — more irrelevant material in the window means more places a stale fact can hide unnoticed.
- **Prioritization & ordering** — critical instructions at the start and end; the middle is where attention goes to die. Order retrieved policy chunks by relevance *and* recency, not raw similarity score alone — the fix that would have caught §2's incident directly: a retrieval ranker that penalizes document age, or that surfaces "this chunk was last verified on [date]" as a visible field the model can reason about, turns a silent staleness bug into a visible one.
- **Compression** — summarize resolved history ("steps 1–6 accomplished X") instead of carrying raw transcripts. Compress tool results to what matters: a 200-row SQL result becomes stats + 5 sample rows + row count, not 200 rows of raw JSON competing for the model's attention against the one policy clause that actually matters.
- **Pruning** — drop superseded attempts, failed paths (keep one-line lessons), and stale retrievals. State (Ch4) holds everything; context holds what's *live*. This is where the poisoning fix belongs structurally: a retrieval result that fails a freshness check should be pruned from context before the model ever sees it, not left in for the model to (hopefully) discount.
- **Token budgets** — a per-call budget with allocations per section (system / task / knowledge / history), enforced by the harness. When knowledge overflows its share, re-rank and cut — don't silently eat the history's share, which is how an agent starts "forgetting" what it already established earlier in the run purely because a retrieval step happened to return a lot of matches.
- **Sub-agent isolation** — the strongest tool: give a subtask a *fresh, minimal* context and return only its distilled result to the parent. Multi-agent architectures are often justified by context isolation alone (this is the legitimate version of Ch3's "when to split") — a sub-agent whose only job is "verify this one policy chunk is current and applicable" can be given a narrow, easily-audited context, distinct from the main investigation's broader window.
- **Caching alignment** — stable prefix (system + tools) first, volatile content last, so prompt caching (Ch18) actually hits. Retrieved knowledge, being volatile per-query, goes late in the assembly order specifically so the stable system/tool prefix keeps its cache hit rate high across a run's many calls.

## 4. Budgeted assembly, visualized

```python
BUDGET = {"system": 2000, "task": 1000, "knowledge": 6000, "history": 4000}

def assemble(state) -> list[Message]:
    knowledge = rerank(retrieve(state.query))          # select
    knowledge = [k for k in knowledge if is_fresh(k)]   # prune stale (the §2 fix)
    knowledge = trim_to(knowledge, BUDGET["knowledge"]) # cut low-rank, not history
    history = (state.turns[-6:] if fits(state.turns, BUDGET["history"])
               else [summarize(state.turns[:-4]), *state.turns[-4:]])  # compress
    return [SYSTEM, *tag(knowledge, origin="retrieved", as_of=knowledge.indexed_at),  # trust + freshness labels (Ch19)
            *history, task(state)]                     # stable prefix first → cache
```

Deterministic policy, intelligent content — and every call's composition is loggable (Ch16). Notice the one line added versus a naive version: `is_fresh(k)` — a single filter step that turns "the model has to notice a document is stale" (it usually won't) into "a stale document never reaches the model at all" (which is the entire lesson of §2).

## 5. Design decisions

- **Who assembles?** Deterministic policy assembles; the model can *request* more (a retrieval tool) but never controls the assembly directly — otherwise context becomes another injection surface (Ch19): a model that can decide unilaterally what enters its own next context is a model that a crafted document can manipulate into pulling in more of itself.
- **What's the unit of history?** Turns? Steps? Summarized episodes? Pick per use case; conversational agents keep recent turns verbatim + older summary; task agents keep the plan + latest results. The dispute agent, being a bounded task rather than an open conversation, keeps the plan and the latest state snapshot — carrying five turns of "I checked X, then I checked Y" prose forward would waste budget the retrieved policy chunks need more.
- **Where does compression run?** A small cheap model summarizing for a big one is standard and pays for itself — routing this specific sub-task to a cheaper model (Ch18's routing-by-step-type pattern) is one of the easiest cost wins in the whole stack, because summarization is a much easier task than the reasoning it's in service of.
- **Freshness as a first-class field.** Per §2, any retrieved content that can go stale (policy documents, product terms, rate tables) needs an explicit "as of" timestamp carried alongside it into the window and a pruning rule that acts on it — this is a design decision worth making explicitly rather than assuming retrieval relevance implies retrieval currency.

## 6. Trade-offs

Every compression is a lossy bet — you will occasionally cut the fact that mattered. Mitigate with retrieval-over-state: keep everything in the store, compress the *view*, and let the agent fetch back detail via a tool rather than trying to guess up front exactly which detail will matter. Aggressive isolation costs integration quality: sub-agents that return over-distilled results starve the parent — a policy-verification sub-agent that returns only "approved" with no clause reference gives the parent nothing to cite if a customer later disputes the outcome. Freshness filtering has its own trade-off: too strict a staleness threshold and you prune documents that are still valid, starving the agent of legitimate context; too loose and §2's incident recurs. Tune all three with traces, not intuition — the right threshold is an empirical question, answered by looking at what actually got pruned and whether the agent's downstream decisions changed.

## 7. Industry implementation

The published lessons from serious agent builders (Anthropic's context-engineering guidance, coding-agent postmortems) converge: treat context as a budgeted, curated resource; use sub-agents for isolation; compact aggressively between phases; put stable content first for cache. Frameworks now expose the levers (LangGraph state + message trimming, SDK sessions) but the *policy* is always yours — no framework can know that your fee-waiver policy documents need a freshness check while your product-brochure documents don't; that's domain knowledge only the architect designing the system has.

## 8. Hands-on lab

Instrument your Ch6 worker to log, for every model call: total tokens, tokens per section, and cache hit rate. Run a 15-turn job; plot context growth. Then add four policies — history summarization after 8 turns, tool-result compression, budget enforcement, and a freshness filter on retrieved content (reject or flag anything older than a configurable threshold) — and re-run. As a specific verification step, seed your retrieval index with one deliberately stale document (mirroring §2) and confirm the freshness filter either excludes it or visibly flags its age in a way that changes the model's confidence in citing it. Target: flat context curve, same task success, measurably lower cost, and a demonstrated catch of the staleness failure mode. The before/after chart plus the staleness-catch demo is a portfolio artifact — it shows you didn't just learn the technique, you can point to the specific failure it prevents.

## 9. Architect's take: the banking read

Context assembly is also a *data-governance* control point: it is exactly where you enforce "the model may see this customer's data only for this session's purpose" — masking PII fields not needed for the task, watermarking retrieved documents with their classification, and logging what was shown (you cannot answer a DPDP data-access question if you don't know what entered the window). §2's incident adds a second banking-specific reason to take this seriously: a stale policy document silently steering a compliance-relevant decision (a fee waiver, in that example) is not just a quality bug — it's a documented instance of the system acting on outdated policy, which is exactly the kind of finding an internal audit or an RBI examination is built to surface. In a bank, the context assembler is a compliance component and deserves a design review as one, with freshness and provenance treated as controls, not conveniences.

## Governance & security lens

The context assembler is a data-governance chokepoint: it is where purpose limitation is enforced (only task-relevant fields enter the window), where PII is masked, where retrieved content gets trust and freshness labels that downstream policy keys off, and where "what did the model see?" becomes answerable — log context composition or forfeit the ability to investigate incidents like §2's stale-policy waiver. Governing questions: **can we state, for any run, exactly what customer data entered the window and under what entitlement; can we state whether every policy-relevant document shown was current as of that run; and can untrusted content ever trigger a mutating action without a human?** If any of these three answers isn't a structural "yes" (or a structural "no" for the third), you're running on luck rather than a control.

## Interview-ready lines

- "Long windows made context engineering more necessary, not less — degradation, cost, and poisoning all scale with mush."
- "Selection is per-step, not per-task."
- "State holds everything; context holds what's live; retrieval bridges them."
- "The context assembler is where data governance is enforced — it's a compliance component."
- "A model reasoning correctly over a stale document still produces a wrong answer — the fix is a freshness check in context assembly, not better reasoning."
- "Retrieval relevance and retrieval currency are different properties — a document can be the best match and still be three weeks out of date."
