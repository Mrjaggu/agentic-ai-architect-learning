# Chapter 15: Multi-Agent Systems

> First question in every multi-agent design review: do you actually need multiple agents? Usually the honest answer is "not yet."

## 1. The legitimate reasons to split

From Ch3 and Ch8, the *only* durable justifications:

1. **Context isolation** — subtasks whose working context would poison or bloat each other (a research sweep vs a synthesis pass).
2. **Permission boundaries** — the card agent holds card-system credentials; the loan agent holds LOS credentials; no agent holds both (least privilege as architecture).
3. **Heterogeneous models/costs** — a cheap fast model for triage, an expensive one for synthesis.
4. **Parallelism across independent subtasks** — wall-clock, not quality.
5. **Organizational ownership** — different teams ship and eval their agents independently (a platform reason, Ch21).

"Researcher + writer + critic because that's how humans do it" is not on the list (anthropomorphic decomposition, Ch3).

## 2. Topologies

**Supervisor** — one agent decomposes, delegates, integrates:

```text
                SUPERVISOR
          ┌─────────┼─────────┐
          ▼         ▼         ▼
      Research    Data      Action
       agent     agent      agent
```

Strengths: single point of coherence and audit. Weakness: the supervisor is a bottleneck and its context accumulates everything (compress worker results aggressively — Ch8).

**Router + specialists** (most production "multi-agent") — classify, dispatch, done. No inter-agent chatter at all.

**Pipeline** — agent A's artifact feeds agent B. Deterministic order, agents inside stages.

**Peer/network** — agents invoke each other. Rarely justified internally; this is where A2A-style contracts (Ch14) matter because coherence must come from task contracts, not shared context.

## 3. The hard problems (why multi-agent is expensive)

- **Shared state**: who may write what? Use the Ch4 graph state with per-agent write scopes and reducers for parallel joins — never "everyone appends to one transcript."
- **Information loss at boundaries**: every delegation is a summary, and every summary is lossy (the Ch8 trade-off, squared). The most common multi-agent failure is a worker succeeding at the wrong task because the delegation under-specified it. Delegation messages deserve the same design care as tool schemas: goal, constraints, output contract.
- **Conflict resolution**: two workers return contradictory findings — the supervisor needs an explicit policy (prefer higher-confidence source, escalate, or run a tiebreak) rather than silently picking one.
- **Cost multiplication**: N agents × M turns × context each. Multi-agent systems routinely cost 5–15× a single-agent baseline on the same task. Anthropic's published multi-agent research experience is blunt about this: parallelism buys speed on genuinely parallel tasks, at a large token premium.
- **Debugging**: a wrong answer now has a *provenance problem* — which agent, which handoff? Without per-agent tracing (Ch16) you are archaeology-ing transcripts.

## 3b. A delegation contract, visualized

```python
class Delegation(BaseModel):          # every handoff is typed — never a vibe
    goal: str                         # "Summarize credit exposure for cust 4471"
    constraints: list[str]            # ["exclude closed accounts", "INR"]
    output_schema: type[BaseModel]    # ExposureSummary — the worker's contract
    budget: Budget                    # max_tokens=20k, max_turns=8
    on_behalf_of: str                 # user identity travels (Ch19)

result = worker.run(Delegation(...))          # supervisor holds NO credentials
state["exposure"] = compress(result, 500)     # distill before it enters supervisor ctx
```

## 4. Design decisions

- Start single-agent; split only when traces show a named reason from §1. Record which reason justified each split — it disciplines the design and gives evals a hypothesis to test.
- Fixed topology beats emergent: declare who may talk to whom (it's an authorization matrix, not an emergent property).
- Contract-first delegation: every agent-to-agent interface gets a typed task contract (goal, inputs, output schema, budget) — which also makes you A2A-ready for free.
- Independent evolvability: each agent gets its own eval suite (Ch17) so teams can ship without cross-breaking.

## 5. Framework comparison (the architect's matrix)

Run the same design through three lenses: **LangGraph** — topology is an explicit graph; state, scopes, and checkpoints are yours; most control, most code. **OpenAI Agents SDK** — handoffs-as-tool-calls; lightweight, elegant for supervisor patterns; less declared structure. **CrewAI** — role/task metaphors; fastest demo; the metaphor pushes toward anthropomorphic decomposition — resist it. Evaluation axes: where does state live, how are handoffs audited, what happens on partial failure, can topologies be constrained. (This matrix, filled in from your lab runs, is a strong portfolio artifact.)

## 6. Hands-on lab

Take one genuinely decomposable task — "prepare a relationship review for customer X: exposure summary, service history, product recommendations" — and build it three ways: single agent with tools; supervisor + three workers (LangGraph); the same supervisor design in Agents SDK or CrewAI. Measure cost, latency, quality (rubric), and debuggability (time to locate an injected fault). Write the memo: which reasons from §1 were real here?

## 7. Architect's take: the banking read

In a bank, the permission-boundary justification usually *is* the architecture: agents map to systems-of-record entitlements, the supervisor holds no credentials at all (it only orchestrates), and every delegation is an auditable record between named identities (Ch19's NHI). That design survives risk review because it mirrors how the bank already separates duties between humans. Multi-agent as org-chart theater does not survive first contact with the token bill.

## Governance & security lens

Multi-agent topology *is* an authorization matrix: who may talk to whom is declared, each agent runs under its own identity with its own grants, the supervisor holds no credentials, and every delegation carries the on-behalf-of user — producing maker-checker-shaped audit records banks already understand. The new risk class is cascading compromise: one poisoned agent's output becomes another's trusted input, so inter-agent messages get the same trust-labeling as retrieved content, and a worker's output never triggers another agent's irreversible action without the same gates a user-triggered action would face. Governing question: **if agent X is fully compromised, which other agents can it influence, and what's the worst combined action the topology permits?**

## Interview-ready lines

- "Split on context, permissions, cost tiers, or parallelism — never on human metaphors."
- "Every delegation is a lossy summary; delegation messages deserve schema-level design."
- "The supervisor should hold no credentials — orchestration and capability are separate concerns."
- "Multi-agent costs 5–15× single-agent; the traces must justify the multiplier."
