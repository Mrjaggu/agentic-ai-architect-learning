# Chapter 4: Agent Graphs & State Machines

> The central design question: should intelligence control the workflow, or should deterministic software control the workflow? Graphs are how you answer "both, precisely."

## 1. The architecture

```mermaid
flowchart TD
    START(["START"]) --> CLASSIFY["CLASSIFY"]
    CLASSIFY --> Search
    CLASSIFY --> Action
    CLASSIFY --> Analysis
    Search --> VALIDATE{"VALIDATE"}
    Action --> VALIDATE
    Analysis --> VALIDATE
    VALIDATE -->|fail| RETRY["retry / escalate"]
    VALIDATE -->|pass| DONE(["END"])
    RETRY -.bounded loop.-> CLASSIFY
    style START fill:#4f46e5,color:#fff,stroke:none
    style DONE fill:#059669,color:#fff,stroke:none
    style VALIDATE fill:#b45309,color:#fff,stroke:none
    style RETRY fill:#be123c,color:#fff,stroke:none
```

Instead of `Agent → Agent → Agent` or an unbounded ReAct loop, model the system as a **stateful graph**. Nodes do work (call a model, run a tool, run plain code). Edges define legal transitions. **Conditional edges** route based on state — the router can be a rule (`if score < 0.7`) or a model decision (Ch3's owner-of-control-flow question, asked per edge). **State** is a typed, shared object every node reads and writes — not a chat transcript.

## 2. Why the industry needed it — the story behind the shift

Chapter 1 told the invoice-agent story at a high level: a pure ReAct loop given a goal and let run produced brilliant demos and ungovernable production incidents — unbounded cost, non-reproducible outcomes, unauditable transcripts. Here's the mechanism of the fix, because "add a graph" undersells what actually changed.

A pure loop has exactly one place decisions live: inside the model's head, turn by turn, with no record of what paths were *available* versus what path was *taken*. When something goes wrong, you have a transcript — a description of one run — but no map of the system's possible behavior. Two engineers debugging the same incident draw two different mental models of "what the agent could have done," because nothing forces the possibility space to be written down.

A graph forces exactly that: the possibility space is drawn *before* the agent runs a single query. `CLASSIFY` can route to `Search`, `Action`, or `Analysis` — and to nothing else. If a bug sends a query somewhere the graph doesn't permit, that's not a subtle behavioral drift; it's a hard runtime error, immediately visible. Rebuild the invoice agent as a graph and the incident from Chapter 1 becomes structurally impossible in two of its three failure modes: the cost blowup is capped because the graph has a bounded retry edge, not an open-ended loop, and the two-runs-different-answers problem is caught because every node's input/output is now typed and checkpointed — you can diff two runs' state at each node and see exactly where they diverged, rather than diffing two 40-turn transcripts by eye.

## 3. Nodes, edges, and the state object — a worked design

Design the dispute-investigation agent from Chapter 2 as a graph, because seeing the same problem solved two ways — as a loop, then as a graph — is the fastest way to feel the difference.

**State schema first**, because in graph design the schema *is* the architecture:

```python
class DisputeState(TypedDict):
    customer_id: str
    transaction: dict | None
    profile: dict | None
    policy_ref: str | None
    recommendation: str | None
    attempts: int
    criteria_met: dict[str, bool]   # explicit goal criteria (Ch2 §3)
```

**Nodes**, each a pure function `State -> partial State`: `fetch_transaction`, `fetch_profile`, `check_policy`, `validate` (checks whether `criteria_met` is complete and internally consistent), `create_case`. Five small, individually testable, individually retriable units — compare this to the ReAct version, where the equivalent logic was folded into one model's undifferentiated reasoning across five turns.

**Edges.** `START → fetch_transaction → fetch_profile → check_policy → validate`, then a **conditional edge** out of `validate`: if criteria incomplete and `attempts < 3`, loop back to whichever fetch is missing (a rule-owned edge — deterministic, because "did we get the data" is a factual check, not a judgment call); if criteria complete, proceed to `create_case → END`. Notice only one edge in this entire graph is remotely judgment-shaped (which fetch to retry), and even that's resolvable by a rule (check which field in state is still `None`). This is normal and good: most real graphs are mostly deterministic plumbing around one or two genuinely intelligent nodes (here, `check_policy`'s interpretation of which policy clause applies).

## 4. The durability layer — what turns a diagram into a system

Four features separate a graph on a whiteboard from a graph in production, and each solves a specific failure you will hit without it.

**Checkpoints.** State persists after every node. Without this, a crash between `fetch_profile` and `check_policy` means the *entire* run — including the transaction fetch that already succeeded and cost tokens and an API call — is lost and must restart from zero. With checkpointing, resume picks up exactly at `check_policy` with `transaction` and `profile` already populated. For a run that touches paid APIs or expensive retrieval, this is not a nicety; it's the difference between a five-second resume and a five-minute re-run that also duplicates any side effects the first attempt already caused (which is why Chapter 6's idempotency matters even inside a single graph run).

**Interrupts.** The graph pauses at a *declared* point, state persists, a human acts, execution resumes from that exact checkpoint with the human's input folded in. This is the entire mechanics of human-in-the-loop (Ch20) — not a UI trick layered on top, but a first-class graph feature. In the dispute graph, an interrupt before `create_case` when the recommended amount exceeds a threshold means the graph literally cannot proceed past that node until an approval event arrives.

**Retries per node.** A flaky tool call in `fetch_transaction` retries itself with backoff; the rest of the graph is unaffected and unaware. Compare to a raw loop, where "retry the last tool call" requires the model to notice failure and decide to retry — an intelligent decision doing a job that should be mechanical.

**Durable execution / time travel.** For processes that live hours or days (waiting on an external event — a document upload, a customer's reply), the same idea Temporal made standard in microservices applies directly: the workflow is replayable from an event log, can be resumed after the entire process restarts, and — critically for debugging — can be *replayed from any checkpoint with modified state* to answer "what would have happened if step 2 had returned a different result?" Know this pattern by name; agent platforms (AgentCore's Runtime, LangGraph Platform) are converging on it as a first-class primitive, not an add-on.

## 5. Design decisions

**Rule edges vs model edges.** Every conditional edge is a choice of owner (Ch1's dial, now applied at the granularity of a single branch point). Default to rules; hand the model an edge only where the routing decision genuinely requires judgment a rule can't encode. Count your model-owned edges per graph — that number is your non-determinism budget, and it should be small and deliberate, not "most of them, because it was easier to let the model decide."

**State schema discipline.** Design it like an API contract, because multiple nodes — possibly written by different engineers — depend on it. Typed fields, no `misc: dict` escape hatch (it becomes a silent landfill within two months), explicit reducers for concurrent writes when branches run in parallel (Ch3's Parallelization pattern) — without a reducer, two branches writing the same field race, and the winner is whichever finished last, which is not a decision anyone made on purpose.

**Granularity.** A node should be small enough to name in one sentence and to be the natural unit of retry and observability (its own span in Ch16's tracing). "Handle the customer request" is not a node; it's a graph. If you can't finish the sentence "this node's job is to ___" cleanly, split it.

**Loops need state-based bounds.** Any cycle in the graph must be bounded by a counter *in state* (`attempts`), never by hoping the condition resolves. An unbounded loop inside a "safely graphed" system is Chapter 1's invoice-agent failure, reintroduced through the back door.

## 6. Trade-offs

Graphs add real ceremony — a schema to design, nodes to wire, a checkpointer to configure — and for a genuinely 3-step task with no loops, no HITL, and no durability requirement, that ceremony can exceed the value; a plain function call is honest and correct there. The payoff arrives exactly when you need checkpointing, interrupts, parallelism, or an audit trail — which, per Chapter 1's placement logic, is most of what qualifies as "an agent" rather than "a workflow" in the first place. The failure mode in the other direction is real too: over-graphing (a node per line of logic, edges for things that are never actually conditional) produces a diagram that's technically accurate and practically unreadable — apply the same "can you name this node's job in one sentence" test to avoid it.

## 7. The shape in code (LangGraph, ~15 lines)

```python
class State(TypedDict):
    request: str; category: str; result: str; attempts: int

g = StateGraph(State)
g.add_node("classify", classify)          # each node: State -> partial State
g.add_node("handle", handle)
g.add_node("validate", validate)
g.add_edge(START, "classify")
g.add_conditional_edges("classify", route,          # rule or model owns this edge
    {"search": "handle", "action": "handle"})
g.add_conditional_edges("validate",
    lambda s: "handle" if s["attempts"] < 3 else END)  # bounded loop, in STATE
app = g.compile(checkpointer=PostgresSaver(...),        # survive crashes
                interrupt_before=["send_email"])        # HITL, declared
```

Every concept of this chapter is visible: typed state, declared edges, a bounded cycle, a checkpointer, an interrupt.

## 8. Framework comparison — the architect's view

**LangGraph**: the graph is explicit and first-class; checkpointing, interrupts, and streaming are built in; state, edges, and reducers are all yours to declare. This is the most direct expression of this chapter, which is why it's our reference stack. **OpenAI Agents SDK**: control flow lives in code plus handoffs between agents — a simpler mental model, but the "graph" is implicit in how you wire handoffs rather than declared as a data structure you can inspect or diff. **CrewAI**: role and task abstractions generate the flow underneath — fastest to a working demo, least explicit control over state and edges. None of these is "better" in the abstract; the comparison question for any framework, in an interview or a bake-off, is always the same three sub-questions: *where does state live, who owns each edge, and what happens on a crash at step 7 of 9?* A framework that can't answer the third question crisply isn't ready for production, whatever its demo looks like.

## 9. Hands-on lab

Build the dispute-investigation graph from §3 as a LangGraph: five nodes, the conditional retry edge with a state-based bound, a checkpointer (Postgres or SQLite for the lab), and an interrupt before `create_case` when the recommended action exceeds a mock threshold. Then run three deliberate breakages and observe the recovery: (1) kill the process mid-run after `fetch_profile` — resume and confirm `fetch_transaction`'s result wasn't re-fetched; (2) force `check_policy` to fail twice — confirm the retry edge fires and the third attempt succeeds or escalates cleanly at the bound; (3) trigger the interrupt — confirm the graph genuinely halts (no background continuation) and resumes correctly once you supply an approval. Deliverable: a short write-up of what each break would have looked like in the Chapter 2 raw-loop version, and why the graph made it recoverable instead of catastrophic.

## 10. Architect's take: the banking read

The graph *is* the compliance story, and this is worth internalizing as a literal presentation technique: when you show a risk committee "here are the states, here are the legal transitions, here is where a human must approve, here is the checkpoint log of what actually happened for run #4471" — that is a document risk can approve, because it's the same shape as a flowchart-and-controls document for any other regulated process. An unbounded loop has no equivalent document to offer; "the model figures it out" is not an answer a risk review accepts, and shouldn't be. Design graphs so the picture you'd draw on a whiteboard for the regulator and the code that actually runs are *the same artifact* — in LangGraph this is nearly free, since the graph definition **is** both the executable code and the diagram (most tooling can render it directly). That equivalence — approved design equals deployed code — is worth calling out explicitly in any design review; it's rarer than it should be and it's exactly the kind of detail that separates an architect's presentation from an engineer's.

## Governance & security lens

The graph is the governance artifact: declared states and transitions are the legal behavior space, checkpoints are the tamper-evident record of what actually happened, interrupts are where approval authority is structurally enforced, and the count of model-owned edges is your documented non-determinism budget. Governing question: **is the diagram shown to risk and the code that runs the same artifact?** Drift between the approved design and the deployed graph is a finding waiting to be written.

## Interview-ready lines

- "A graph turns the model's freedom into a choice among declared transitions — that's what made agents deployable in production."
- "Count your model-owned edges; that's your non-determinism budget, and it should be small and deliberate."
- "Checkpoint plus interrupt is the entire mechanics of human-in-the-loop — not a UI layer, a graph feature."
- "Nodes are the unit of retry and observability; state schema is an API contract, not a scratchpad."
- "In LangGraph the approved design and the deployed code are the same artifact — that's a governance property, not just a convenience."
