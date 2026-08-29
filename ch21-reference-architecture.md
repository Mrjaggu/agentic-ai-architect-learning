# Chapter 21: The Enterprise Agentic AI Reference Architecture

> The capstone. Twenty chapters collapse into one picture you can draw from memory, defend layer by layer, and reuse in interviews, leadership forums, and design reviews.

## 1. The architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│ EXPERIENCE LAYER                                                │
│   channels (web/app/branch/contact-center) · streaming UX (Ch6) │
│   approval surfaces (Ch20) · agent-to-UI events (Ch14)          │
├─────────────────────────────────────────────────────────────────┤
│ AGENT LAYER                                                     │
│   routers + specialist agents (Ch3/15) · autonomy matrix (Ch20) │
│   per-agent identity & owner (Ch19)                             │
├─────────────────────────────────────────────────────────────────┤
│ ORCHESTRATION & HARNESS LAYER                                   │
│   graphs, state, checkpoints, interrupts (Ch4)                  │
│   harness: bounds, tool policy, sandbox, context asm (Ch5/8)    │
│   memory services (Ch9) · job queue + workers (Ch6)             │
├─────────────────────────────────────────────────────────────────┤
│ KNOWLEDGE LAYER                                                 │
│   RAG service (Ch10) · knowledge graph (Ch11) · semantic layer  │
│   + live APIs, unified by knowledge routing (Ch12)              │
├─────────────────────────────────────────────────────────────────┤
│ TOOL & INTEGRATION LAYER                                        │
│   tool registry (Ch13) · MCP gateway: authN/authZ/audit (Ch14)  │
│   AI gateway: model routing, caching, quotas (Ch18)             │
├─────────────────────────────────────────────────────────────────┤
│ ENTERPRISE SYSTEMS                                              │
│   core banking · CRM · LOS · data platform · payment rails      │
└─────────────────────────────────────────────────────────────────┘
   CROSS-CUTTING (every layer, by design, not decoration):
   SECURITY (Ch19) · OBSERVABILITY (Ch16) · EVALS (Ch17)
   GOVERNANCE (Ch20) · RELIABILITY & COST (Ch18) · DEPLOYMENT (Ch7)
```

## 2. The ten defining decisions (the defense of the diagram)

Each layer earns its place through a decision you can now argue both sides of:

1. **Control flow**: deterministic graphs with model-owned edges counted and named (Ch1/4) — the non-determinism budget.
2. **One harness, many agents** (Ch5): reliability machinery is platform, not per-team craft.
3. **Async by construction** (Ch6): job/queue/worker with streaming — agents never live on the request path.
4. **Identity, not keys** (Ch7/19): workload identity everywhere; agents are governed NHIs with owners and kill handles.
5. **Context as budgeted, governed assembly** (Ch8): the assembler is a compliance component.
6. **Knowledge routed, not stuffed** (Ch10–12): four source types behind contracts; the graph as explainability substrate.
7. **Tools as capability grants** (Ch13/14): registry + gateway = one governed choke point; user entitlements travel with every call.
8. **Multi-agent only on named justifications** (Ch15): context, permissions, cost tiers, parallelism — never metaphor.
9. **Traces → evals → gates** (Ch16/17): telemetry is the audit record; evals decide releases; production feeds the datasets.
10. **Autonomy per action class + governance as platform features** (Ch20): the matrix, MRM inventory, audit, kill drills — FREE-AI-ready by construction.

## 3. What flows through it (one request, annotated)

"Should we raise customer X's card limit?" → Experience layer authenticates, opens job (Ch6) → router sends to card agent (Ch3), running under its identity for this RM (Ch19) → graph plans (Ch4); context assembled under budget with entitlement-filtered data (Ch8) → knowledge routing fans out: policy (RAG), exposure (graph), history (SQL), balance (API) (Ch12) via gateway-audited tools (Ch14) → synthesis with per-claim citations; recommendation is L1, the limit change is L2 → interrupt; RM approves on an evidence-bearing surface (Ch20) → action executes idempotently (Ch6/13); trace, cost, and outcome recorded (Ch16); sampled into next month's eval suite (Ch17). Every chapter, one request.

## 4. Build order (the pragmatic sequencing)

Platforms fail by building all layers thin. Sequence by value-with-proof: (1) one use case, single agent, harness + traces from day one; (2) backend + deployment (it's a service now); (3) evals before scaling usage; (4) knowledge layer as the second use case demands routing; (5) gateway + registry as the third team arrives; (6) governance features as autonomy ambition rises. The platform emerges from use cases that worked — it is *extracted*, not pre-built.

## 5. Deliverables of this capstone (the portfolio centerpiece)

1. **The reference architecture document** (10–15 pages): the diagram, the ten decisions each with alternatives-considered and trade-offs, the annotated request flow, and the FREE-AI/MRM control mapping (Ch20).
2. **The diagram set**: full architecture, request sequence, autonomy matrix, threat model.
3. **The three projects as evidence**: Banking Agent Platform (layers 1–3 + 5), Knowledge Intelligence Agent (layer 4), Eval & Observability platform (cross-cutting) — each README pointing back to the decisions it demonstrates.

Together these say the one thing a portfolio must say at AVP/architect level: *not "I can build an agent" but "I can design, defend, and govern the system agents live in."*

## 5b. Frontier watchlist (know them; don't build on them yet)

Topics to track without coupling the platform to them: **computer-use / GUI agents** (agents operating browsers and desktops directly — powerful where no API exists, currently slow and brittle; in a bank, treat as RPA's successor with RPA's controls); **learning agents** (Ch9's adaptation loops maturing toward continuous improvement — governance-gated); **exploration/discovery agents** (open-ended research patterns — fits innovation labs, not the production path); and **voice-native agents** (your Siddhi adjacency — the harness/eval machinery here applies unchanged, with latency budgets tightened 10×). Each gets a paragraph in leadership briefings and zero load-bearing roles in the reference architecture until the controls story matures.

## 6. Architect's take: using this artifact

In interviews: draw layers left-to-right in ninety seconds, then let the interviewer pick a box — every box has a chapter behind it. In leadership forums: lead with the cross-cutting bar and the autonomy matrix; executives buy governance and cost posture, not graph frameworks. On LinkedIn: publish the diagram + ten decisions as a series. Internally: use it as the review template — every new agent proposal answers "where does this sit, and which of the ten decisions does it stress?"

## Governance & security lens — the roll-up

Every chapter's lens converges here into one statement for leadership: **each layer of the platform carries its own named controls, and the cross-cutting bar is where they aggregate** — placement decisions documented (Ch1), bounds and grants (Ch2/5), auditable patterns and graphs (Ch3/4), job ledgers and idempotency (Ch6), identity-based deployment (Ch7), the context assembler as data-governance chokepoint (Ch8), governed memory (Ch9), entitlement-aware knowledge (Ch10–12), the capability registry (Ch13), the gateway (Ch14), topology as authz (Ch15), traces as protected audit records (Ch16), evals as evidence (Ch17), validated fallbacks and clean kills (Ch18), bounded blast radius (Ch19), and the autonomy matrix (Ch20). The design habit this curriculum trains: **at every layer, ask the governance question in the same breath as the scaling question** — because in a regulated enterprise, a design that scales but can't be governed doesn't ship.

## Interview-ready lines

- "Six layers, six cross-cutting concerns, ten decisions — ask me about any box."
- "The platform is extracted from working use cases, never pre-built."
- "Executives don't buy agents; they buy bounded blast radius, audit trails, and a cost curve."
- "The reference architecture is the difference between knowing agents and owning the system they live in."
