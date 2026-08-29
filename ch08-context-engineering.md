# Chapter 8: Context Engineering

> Prompt engineering asks "how do I phrase this?" Context engineering asks "what should the model see at this exact moment?" The second question is an architecture question.

## 1. Concept

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

## 2. Why the industry needed it

Long context windows made the problem worse, not better. Three empirical realities forced the discipline: **degradation** — models reason worse over 100k tokens of mush than 8k of signal ("lost in the middle" is real); **cost** — context is billed per call, and a 20-turn loop re-sends it 20 times; **poisoning** — one bad retrieved document or stale tool result steers every subsequent decision. Stuffing is not a strategy.

## 3. The techniques

- **Selection** — retrieve/include only what this step needs. The question is per-*step*, not per-task: the planning step and the execution step deserve different context.
- **Prioritization & ordering** — critical instructions at the start and end; the middle is where attention goes to die. Order retrieved items by relevance, not arrival.
- **Compression** — summarize resolved history ("steps 1–6 accomplished X") instead of carrying raw transcripts. Compress tool results to what matters: a 200-row SQL result becomes stats + 5 sample rows + row count.
- **Pruning** — drop superseded attempts, failed paths (keep one-line lessons), and stale retrievals. State (Ch4) holds everything; context holds what's *live*.
- **Token budgets** — a per-call budget with allocations per section (system / task / knowledge / history), enforced by the harness. When knowledge overflows its share, re-rank and cut — don't silently eat the history's share.
- **Sub-agent isolation** — the strongest tool: give a subtask a *fresh, minimal* context and return only its distilled result to the parent. Multi-agent architectures are often justified by context isolation alone (this is the legitimate version of Ch3's "when to split").
- **Caching alignment** — stable prefix (system + tools) first, volatile content last, so prompt caching (Ch18) actually hits.

## 3b. Budgeted assembly, visualized

```python
BUDGET = {"system": 2000, "task": 1000, "knowledge": 6000, "history": 4000}

def assemble(state) -> list[Message]:
    knowledge = rerank(retrieve(state.query))          # select
    knowledge = trim_to(knowledge, BUDGET["knowledge"]) # cut low-rank, not history
    history = (state.turns[-6:] if fits(state.turns, BUDGET["history"])
               else [summarize(state.turns[:-4]), *state.turns[-4:]])  # compress
    return [SYSTEM, *tag(knowledge, origin="retrieved"),  # trust labels (Ch19)
            *history, task(state)]                     # stable prefix first → cache
```

Deterministic policy, intelligent content — and every call's composition is loggable (Ch16).

## 4. Design decisions

- **Who assembles?** Deterministic policy assembles; the model can *request* more (a retrieval tool) but never controls the assembly directly — otherwise context becomes another injection surface (Ch19).
- **What's the unit of history?** Turns? Steps? Summarized episodes? Pick per use case; conversational agents keep recent turns verbatim + older summary; task agents keep the plan + latest results.
- **Where does compression run?** A small cheap model summarizing for a big one is standard and pays for itself.

## 5. Trade-offs

Every compression is a lossy bet — you will occasionally cut the fact that mattered. Mitigate with retrieval-over-state: keep everything in the store, compress the *view*, and let the agent fetch back detail via a tool. Aggressive isolation costs integration quality: sub-agents that return over-distilled results starve the parent. Tune with traces, not intuition.

## 6. Industry implementation

The published lessons from serious agent builders (Anthropic's context-engineering guidance, coding-agent postmortems) converge: treat context as a budgeted, curated resource; use sub-agents for isolation; compact aggressively between phases; put stable content first for cache. Frameworks now expose the levers (LangGraph state + message trimming, SDK sessions) but the *policy* is always yours.

## 7. Hands-on lab

Instrument your Ch6 worker to log, for every model call: total tokens, tokens per section, and cache hit rate. Run a 15-turn job; plot context growth. Then add three policies — history summarization after 8 turns, tool-result compression, budget enforcement — and re-run. Target: flat context curve, same task success, measurably lower cost. The before/after chart is a portfolio artifact.

## 8. Architect's take: the banking read

Context assembly is also a *data-governance* control point: it is exactly where you enforce "the model may see this customer's data only for this session's purpose" — masking PII fields not needed for the task, watermarking retrieved documents with their classification, and logging what was shown (you cannot answer a DPDP data-access question if you don't know what entered the window). In a bank, the context assembler is a compliance component and deserves a design review as one.

## Governance & security lens

The context assembler is a data-governance chokepoint: it is where purpose limitation is enforced (only task-relevant fields enter the window), where PII is masked, where retrieved content gets trust labels that downstream policy keys off, and where "what did the model see?" becomes answerable — log context composition or forfeit the ability to investigate incidents. Governing questions: **can we state, for any run, exactly what customer data entered the window and under what entitlement — and can untrusted content ever trigger a mutating action without a human?** If the second answer isn't a structural "no," injection defense is running on luck.

## Interview-ready lines

- "Long windows made context engineering more necessary, not less — degradation, cost, and poisoning all scale with mush."
- "Selection is per-step, not per-task."
- "State holds everything; context holds what's live; retrieval bridges them."
- "The context assembler is where data governance is enforced — it's a compliance component."
