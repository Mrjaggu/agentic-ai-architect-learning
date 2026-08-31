# Chapter 15: Multi-Agent Systems

> First question in every multi-agent design review: do you actually need multiple agents? Usually the honest answer is "not yet."

## 1. The architecture

```mermaid
flowchart TB
    subgraph SUP["Supervisor"]
      direction TB
      S0["Supervisor"] --> S1["Research agent"]
      S0 --> S2["Data agent"]
      S0 --> S3["Action agent"]
    end
    subgraph PIPE["Pipeline"]
      direction LR
      P1["Agent A"] --> P2["Agent B"] --> P3["Agent C"]
    end
    style S0 fill:#4f46e5,color:#fff,stroke:none
```

From Ch3 and Ch8, the *only* durable justifications for splitting one agent into several:

1. **Context isolation** — subtasks whose working context would poison or bloat each other (a research sweep vs a synthesis pass).
2. **Permission boundaries** — the card agent holds card-system credentials; the loan agent holds LOS credentials; no agent holds both (least privilege as architecture).
3. **Heterogeneous models/costs** — a cheap fast model for triage, an expensive one for synthesis.
4. **Parallelism across independent subtasks** — wall-clock, not quality.
5. **Organizational ownership** — different teams ship and eval their agents independently (a platform reason, Ch21).

"Researcher + writer + critic because that's how humans do it" is not on the list (anthropomorphic decomposition, Ch3).

**Topologies.** **Supervisor** — one agent decomposes, delegates, integrates; single point of coherence and audit, but a bottleneck whose context accumulates everything (compress worker results aggressively — Ch8). **Router + specialists** (most production "multi-agent") — classify, dispatch, done, no inter-agent chatter at all. **Pipeline** — agent A's artifact feeds agent B feeds agent C; deterministic order, no shared context at all, each agent sees only what the one before it handed off. **Peer/network** — agents invoke each other; rarely justified internally, and where A2A-style contracts (Ch14) matter most, because coherence must come from task contracts, not shared context.

## 2. Why the industry needed it — the join problem

Most retrieval questions have one answer that lives in one place — "who is the CFO of this company" resolves to one record, and a single-agent tool call is the right shape for that. A useful category of enterprise question doesn't work that way: the answer only exists once you combine two things that live in genuinely separate systems and were never going to show up together in one search result. "Which of our mid-market corporate relationships have had a leadership or funding event in the last quarter, *and* which of those contacts have we not reached out to since?" isn't answerable from one query against one source, because the trigger event lives in market and regulatory news, and the contact's role history and relationship status live in an entirely different system.

A single generalist agent *can* answer this — by searching, opening a dozen pages, reading past the marketing copy for the one paragraph that matters, and repeating that for every candidate company — but that's an expensive, brittle way to do a join. Every fetched page returns a pile of unstructured text the model has to re-parse, and the model doing that re-parsing at every step is exactly the "fragment reassembly" tax Ch8's context-engineering argument warns about, paid over and over across dozens of candidates. The industry's answer is the one this chapter has been building toward since §1: split the join into stages, give each stage a narrow, well-scoped job and only the tools that job needs, and let the final stage merge two already-clean records instead of reconstructing them from scratch. Retrieval tools that return whole structured records instead of search snippets (Ch10's chunking argument, generalized — a snippet is a badly-drawn chunk of an answer) make each stage cheaper and more reliable, but the multi-agent shape is what makes the join possible at all.

## 3. A worked example — the relationship-opportunity pipeline

A mid-market corporate relationship team wants a standing pipeline that surfaces, every morning, which existing clients just had something happen worth a phone call — a new CFO, a funding round, a credit-relevant expansion — and who on the relationship-management team should make that call, with a specific reason to open with. This is Ch15's textbook join problem: the trigger event and the contact's current role live in different places, and the team's own book of relationships lives in a third place entirely. Three agents, in a strict pipeline (§1):

**Agent 1 — Signal Scout.** Given the bank's list of existing corporate relationships, it queries a market/news retrieval tool for events in a fixed lookback window: leadership changes, funding rounds, expansions, credit-rating actions. It holds *only* this tool — no access to the bank's internal counterparty systems, because its job is external signal-finding, and giving it more than that widens its blast radius for no benefit (Ch5's tool-policy discipline, applied here at the agent level instead of the tool level). Output: a typed list of `{company, person_name_as_reported, event_type, event_date, source}` — deliberately *not* a resolved identity yet, because the name in a news headline is not the same thing as a verified contact record, which is exactly what §4's failure story is about.

**Agent 2 — Counterparty Enricher.** Given Agent 1's output, it queries the bank's internal, KYC-cleared counterparty and contact database for each named individual, resolving the reported name to a specific, structured contact record — current title, tenure, relationship-manager of record, and contact permissions. It holds *only* this internal-lookup tool; it cannot reach the open web, because its job is resolution and enrichment against data the bank already governs, not discovery. This is the "permission boundaries" reason from §1 doing real work: Agent 1 and Agent 2 each hold exactly one tool, and neither tool is powerful enough on its own to leak the other's job.

**Agent 3 — Relationship Strategist.** Holds *no* retrieval tools at all — it reasons only over what Agents 1 and 2 already produced, merging a resolved contact record with its triggering event into a ranked list: who to call, why now, and a one-line reason grounded in the specific event. Because it never touches a tool, its failure modes are limited to reasoning over already-verified inputs — it cannot itself misidentify a person, only propagate a bad identification if one reached it (which is exactly what happens in §4).

**A hybrid heuristic worth stating explicitly:** for the single most senior trigger at a client — a CEO or board-level change — a broader, human-reviewed source is the more reliable first call, because that signal is rare, high-stakes, and worth a person's judgment before it reaches a relationship manager's call list. Agent 1's automated news scan earns its keep at the layer below that: the dozens of VP- and director-level changes across a large book of relationships that no team has the headcount to track by hand. Chaining "generalist judgment at the top, automated pipeline for the depth below" gets more coverage than either alone, and is a cleaner design than trying to make one retrieval tool authoritative at every seniority level.

## 4. A failure story — the outreach call to someone who'd already left

Agent 1 surfaced a real event: a headline reporting that a client company's CFO was stepping down, with a successor named later in the same article. The delegation from Agent 1 to Agent 2 — per §1's typed-handoff pattern, but under-specified in this instance — passed only a bare name string, "R. Kapoor," extracted from the headline's first sentence, with no field distinguishing *outgoing* from *incoming*. The article had, in fact, named the outgoing CFO first. Agent 2 resolved "R. Kapoor" against the bank's counterparty database, found a matching contact, and enriched a complete, accurate record — for the departing executive, not the new one. Nothing in Agent 2's output looked wrong: it was a real person, a real prior role at that company, a plausible-looking record. Agent 3 merged it with the trigger event and produced exactly what it was designed to produce — a ranked outreach recommendation with a specific opening line congratulating this contact on the new role. A relationship manager, trusting the pipeline's output, called the number on file to offer congratulations, and reached someone who had left the company two months earlier and was, understandably, confused and a little irritated. No system alarm fired, because every individual step had done its job correctly against the input it was given — the failure lived entirely in what the delegation between Agent 1 and Agent 2 left unsaid.

## 5. Design decisions

- **Delegation payloads carry structured identifiers, not bare names.** §4's incident traces to a `person_name` string with no `role_direction` (outgoing/incoming) or other disambiguating field — the fix is the same principle Ch19 applies to entitlements: identify by structured, checkable fields, not by a string a human (or a model) has to interpret correctly on every hop. §3b's `Delegation` contract should have a required field for exactly this kind of ambiguity whenever the upstream source itself is ambiguous.
- **Each agent gets exactly the tools its job needs, never "just in case."** §3's Signal Scout and Counterparty Enricher each hold one tool; the Strategist holds none. This isn't caution for its own sake — it's what makes each agent's failure surface small enough to reason about, and it's the same logic as Ch5's per-tool grants, applied at the granularity of an entire agent.
- **Route by seniority and stakes, not by a single retrieval tool for everything.** §3's hybrid heuristic — human-reviewed judgment for the rare, high-stakes signal; an automated pipeline for the high-volume layer below — is a legitimate multi-agent design decision, not a tooling afterthought: it's deciding *which* agent (or human) is authoritative for which slice of a problem.
- Start single-agent; split only when traces show a named reason from §1. Record which reason justified each split — it disciplines the design and gives evals a hypothesis to test.
- Fixed topology beats emergent: declare who may talk to whom (it's an authorization matrix, not an emergent property).
- Independent evolvability: each agent gets its own eval suite (Ch17) so teams can ship without cross-breaking.

## 5b. The delegation contract, visualized

```python
class Delegation(BaseModel):          # every handoff is typed — never a vibe
    goal: str                         # "Resolve and enrich this reported contact"
    subject: ReportedPerson           # {name_as_reported, role_direction, company}  <- the §4 fix
    constraints: list[str]            # ["match on company + role_direction, not name alone"]
    output_schema: type[BaseModel]    # ResolvedContact — the worker's contract
    budget: Budget                    # max_tokens=8k, max_turns=3
    on_behalf_of: str                 # user/team identity travels (Ch19)

result = enricher.run(Delegation(...))        # Agent 2 holds ONE tool, no web access
state["contact"] = compress(result, 300)      # distill before it enters the Strategist's ctx
```

## 6. Trade-offs

- **Cost multiplication.** N agents × M turns × context each. Multi-agent systems routinely cost 5–15× a single-agent baseline on the same task. Anthropic's published multi-agent research experience is blunt about this: parallelism buys speed on genuinely parallel tasks, at a large token premium — §3's pipeline isn't parallel, so the multiplier here is closer to "three sequential calls," a smaller and more predictable cost than a fan-out topology.
- **Debugging becomes a provenance problem.** A wrong answer now has to be traced through which agent, which handoff — §4's incident took a human noticing an awkward phone call, not a system alert, because the failure was a *correct* execution of an *incomplete* instruction. Without per-agent tracing (Ch16) you are archaeology-ing transcripts after the fact.
- **Information loss at boundaries.** Every delegation is a summary, and every summary is lossy (the Ch8 trade-off, squared). §4 is the sharpest version of this: not information lost from *too much* compression, but a critical disambiguating field that was never in the payload to begin with.
- **Conflict resolution needs an explicit policy.** Two workers return contradictory findings — the supervisor (or, in a pipeline, the final synthesis stage) needs an explicit policy: prefer higher-confidence source, escalate, or run a tiebreak, rather than silently picking one.
- **What it buys, worth restating against all of the above.** A cleanly-scoped pipeline turns an expensive, brittle join (one generalist agent re-parsing fragments across dozens of candidates) into a cheap, reliable merge across two already-clean records — §2's whole argument, and the reason the cost multiplier is often still worth paying.

## 7. Industry implementation

**MCP (Ch14) is what makes selective, per-agent tool grants cheap to build.** A retrieval tool exposed once as an MCP server can be connected to exactly the agents that need it — Agent 1 and Agent 2 in §3's pipeline, not Agent 3 — without custom integration code per agent; the framework's job becomes wiring connections, not writing adapters.

**Structured-record retrieval is a real, growing category of tool worth knowing**, distinct from general web search: rather than returning ranked links with snippets that an agent must fetch, parse, and reassemble, a handful of newer retrieval APIs (Seltz is a recent, venture-backed example — a "web index for agents" that returns full structured person and news records in one call) are built specifically to make the multi-agent join in §2 cheap: one call per agent, a complete record back, no second fetch. The pattern is worth recognizing even where you build the equivalent yourself against internal systems, which is exactly what §3's Counterparty Enricher does against the bank's own KYC-cleared database instead of an external API.

**Framework comparison (the architect's matrix).** Run the same design through three lenses: **LangGraph** — topology is an explicit graph; state, scopes, and checkpoints are yours; most control, most code. **OpenAI Agents SDK** — handoffs-as-tool-calls; lightweight, elegant for supervisor patterns; less declared structure. **CrewAI** — role/task metaphors, agents connect to a shared MCP tool via a simple `mcps=[...]` parameter per agent, and tasks pass typed context to the next task by declaring `context=[prior_task]` — fast to stand up a §3-shaped pipeline, though the role/task metaphor pushes toward anthropomorphic decomposition (§1's warning) if you're not deliberate about which agent gets which tool and why. Evaluation axes for all three: where does state live, how are handoffs audited, what happens on partial failure, can topologies be constrained. (This matrix, filled in from your own lab runs, is a strong portfolio artifact.)

## 8. Hands-on lab

Build §3's relationship-opportunity pipeline, then prove the fix for §4's failure with a deliberate-break test:

**Stage 1 — build it as specified, with the gap.** Three agents, sequential, Agent 1 and 2 each with exactly one tool (or a mock/stub if you don't have live data sources), Agent 3 with none. Use a bare `person_name` string in the Agent 1 → Agent 2 delegation, matching §4 exactly.

**Stage 2 — reproduce the failure on purpose.** Feed Agent 1 a synthetic headline naming two people (an outgoing and incoming role-holder) for the same event, and confirm Agent 2 resolves the wrong one at least some of the time — this is the concrete, reproducible version of §4's incident.

**Stage 3 — fix it with §5's structured identifier.** Add `role_direction` (or equivalent) to the delegation schema, require Agent 1 to populate it from the source article, and require Agent 2 to match on company + role_direction, not name alone. Re-run Stage 2's synthetic case and confirm the correct person resolves every time.

**Stage 4 — measure the multiplier.** Compare this three-agent pipeline against a single generalist agent doing the same end-to-end task with one broad tool. Report cost, latency, and — using Stage 2/3's test case as your rubric — accuracy on the specific failure mode this chapter is about.

Deliverable: a before/after table (like §4/§5's fix) plus the cost-multiplier comparison from Stage 4, written as the design-review memo you'd actually bring to defend the multi-agent decision.

## 9. Architect's take: the banking read

In a bank, the permission-boundary justification usually *is* the architecture: agents map to systems-of-record entitlements, no single agent holds both external-discovery and internal-lookup credentials, and every delegation is an auditable record between named identities (Ch19's NHI). §3's pipeline is a clean illustration because the boundary isn't incidental — Agent 1 (external signal) and Agent 2 (internal counterparty data) *must* stay separate, because merging their credentials would mean one compromised or misconfigured agent could pivot from public news scanning straight into KYC-cleared internal records. There's a banking-specific angle §2's generic "join problem" framing doesn't have to consider: any pipeline that turns public signals into outreach touches marketing-consent and relationship-disclosure rules that a generic sales tool never has to think about — "we saw your CFO change in the news, so we called" is a very different compliance conversation for a bank than for a SaaS vendor's sales team, and that conversation needs to happen before the pipeline ships, not after a relationship manager makes the first call.

## Governance & security lens

Multi-agent topology *is* an authorization matrix: who may talk to whom is declared, each agent runs under its own identity with its own grants, and every delegation carries the on-behalf-of user — producing maker-checker-shaped audit records banks already understand. The new risk class is cascading compromise: one poisoned agent's output becomes another's trusted input, so inter-agent messages get the same trust-labeling as retrieved content, and a worker's output never triggers another agent's irreversible action without the same gates a user-triggered action would face. §4 adds a narrower but very concrete control: any delegation built from an *external, unverified* source (a news headline, a scraped page) must carry enough structure for the next agent to disambiguate identity — a bare name string crossing that boundary is itself a governance gap, not just a data-quality nuisance. And per §9, any pipeline that converts external signals into customer or prospect outreach needs a compliance sign-off on the underlying data use *before* build, not a retrofit after a relationship manager has already made a call. Governing question: **if agent X is fully compromised, which other agents can it influence, and what's the worst combined action the topology permits — and separately, has legal/compliance signed off on every external data source this pipeline's outreach decisions are allowed to be triggered by?**

## Interview-ready lines

- "Split on context, permissions, cost tiers, or parallelism — never on human metaphors."
- "Every delegation is a lossy summary; delegation messages deserve schema-level design."
- "The supervisor should hold no credentials — orchestration and capability are separate concerns."
- "Multi-agent costs 5–15× single-agent; the traces must justify the multiplier."
- "A join across two separate systems is the strongest legitimate reason for a multi-agent pipeline — not because it's elegant, but because a single agent doing that join has to reassemble structure from fragments, over and over, at cost."
- "A bare name string crossing an agent boundary is an incident waiting for an ambiguous headline — identify by structured, checkable fields, the same discipline Ch19 applies to entitlements."
- "Route by stakes: human judgment for the rare, high-value signal; an automated pipeline for the high-volume layer underneath it. Neither one alone covers the whole book."
