# Chapter 4: Agent Graphs & State Machines

> The central design question: should intelligence control the workflow, or should deterministic software control the workflow? Graphs are how you answer "both, precisely."

## 1. Concept

Instead of `Agent → Agent → Agent`, model the system as a **stateful graph**:

```text
              ┌─────────┐
              │  START  │
              └────┬────┘
                   ▼
              ┌─────────┐
              │CLASSIFY │
              └────┬────┘
        ┌──────────┼──────────┐
        ▼          ▼          ▼
     Search      Action    Analysis
        │          │          │
        └──────────┼──────────┘
                   ▼
              ┌─────────┐
              │VALIDATE │──fail──► retry / escalate
              └────┬────┘
                   ▼
                  END
```

- **Nodes** do work (call a model, run a tool, run plain code).
- **Edges** define legal transitions. **Conditional edges** route based on state — the router can be a rule (`if score < 0.7`) or a model decision.
- **State** is a typed, shared object every node reads and writes — not a chat transcript.

## 2. Why the industry needed it

Pure agent loops gave unbounded behavior; pure pipelines gave no adaptivity. Graphs give you a *legal state space*: the model chooses among transitions you declared, and cannot invent a path you didn't draw. That single property is what made agents deployable in enterprises.

## 3. The durability layer

The features that separate a demo from a system:

- **Checkpoints** — persist state after each node; a crash resumes from the last checkpoint instead of re-running (and re-paying for) the whole graph.
- **Interrupts** — pause the graph at a declared point, wait for a human, resume with their input. This is *the* HITL mechanic; checkpoint + interrupt is why approval flows work.
- **Retries per node** — a flaky tool node retries itself; the graph doesn't care.
- **Time travel / replay** — re-run from any checkpoint with modified state; invaluable for debugging and for evals (Ch17).
- **Durable execution** — for long-lived processes (hours/days, waiting on external events), the same idea Temporal made standard in microservices applies: the workflow is replayable from an event log. Know this pattern by name; agent platforms are converging on it.

## 4. Design decisions

- **Rule edges vs model edges**: every conditional edge is a choice of owner. Default to rules; give the model the edge only where the routing decision genuinely requires judgment. Count your model-owned edges — that number is your non-determinism budget.
- **State schema**: design it like an API. Typed fields, explicit reducers for concurrent writes (parallel branches), no "misc" dict that becomes a landfill.
- **Granularity**: nodes should be the unit of retry and of observability. If you can't name what a node does in one sentence, split it.
- **Loops**: allowed, but every cycle needs a bound in *state* (attempt counter), not in hope.

## 5. Trade-offs

Graphs add ceremony: for a 3-step task, a plain loop is fine. The graph pays off exactly when you need checkpointing, interrupts, parallelism, or auditability — which is to say, in production. Over-graphing (a node per sentence of logic) is as real a smell as under-graphing.

## 6. Framework comparison (the architect's view)

- **LangGraph**: the graph is explicit and first-class; checkpointing, interrupts, and streaming are built in. Most direct expression of this chapter; our reference stack.
- **OpenAI Agents SDK**: control flow lives in code + handoffs between agents; simpler mental model, less declared structure — the graph exists but implicitly.
- **CrewAI**: role/task abstractions generate the flow; fastest to demo, least explicit state control.

The comparison question for any framework: *where is the state, who owns the edges, and what happens on a crash at step 7 of 9?*

## 6b. The shape in code (LangGraph, ~15 lines)

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

## 7. Hands-on lab

Build the complaint-handling task from Ch3 as a LangGraph: classify → (route) → handle → validate → END, with a checkpointer, a retry-bounded validation loop, and an interrupt before any outbound email. Kill the process mid-run and resume it. Then sketch (on paper is fine) the same design in Agents SDK handoffs and CrewAI tasks, and write down what each framework made you give up.

## 8. Architect's take: the banking read

The graph *is* the compliance story. "Here are the states, here are the legal transitions, here is where a human must approve, here is the checkpoint log of what actually happened" — that is a document a bank's risk function can approve. An unbounded loop is not. Design graphs so the picture you draw for the regulator and the code that runs are the same artifact.

## Governance & security lens

The graph is the governance artifact: declared states and transitions are the legal behavior space, checkpoints are the tamper-evident record of what actually happened, interrupts are where approval authority is structurally enforced, and the count of model-owned edges is your documented non-determinism budget. Governing question: **is the diagram shown to risk and the code that runs the same artifact?** Drift between the approved design and the deployed graph is a finding waiting to be written.

## Interview-ready lines

- "A graph turns the model's freedom into a choice among declared transitions — that's what made agents deployable."
- "Count your model-owned edges; that's your non-determinism budget."
- "Checkpoint + interrupt is the entire mechanics of human-in-the-loop."
- "Nodes are the unit of retry and observability; state schema is an API, not a scratchpad."
