# Chapter 3: Agent Design Patterns — and When NOT to Use Them

> Knowing patterns is easy. Knowing when not to use multi-agent architecture is architect-level knowledge.

## 1. Why patterns, and how to hold them

Design patterns in agentic AI play the same role the GoF patterns played in software: shared vocabulary for recurring solutions, so teams stop reinventing and start naming. But there's a trap the GoF era also taught: **pattern-hoarding** — reaching for the fanciest pattern because you know it, not because the problem asks for it. So hold this catalog the way an architect holds any catalog: every pattern is a trade, and the selection framework in §3 matters more than any single entry.

## 2. The catalog — mechanics, worked example, failure mode, verdict

### ReAct (Reason → Act → Observe → repeat)

The default single-agent pattern; Chapter 2's worked dispute trace *is* ReAct. Each turn the model reasons over everything so far and picks the next action; no plan exists beyond the current step. **Wins when** the path is genuinely unknowable and each observation should steer the next move — investigation, research, debugging. **Fails by** wandering: without goal criteria and bounds it can circle (retrieve → reconsider → retrieve similar → …), and its "plan" can't be reviewed in advance because it never exists in advance. **Verdict:** the workhorse; pair it always with Ch2's bounded stop.

### Plan-and-Execute

A planner produces an explicit plan (typically as structured steps); an executor runs each step; optionally a re-planner repairs the plan when a step's result invalidates it. Worked example — "prepare a relationship review for customer X": the planner emits *[1: fetch profile+holdings; 2: fetch 12-month activity; 3: exposure summary from graph; 4: policy check on eligibility; 5: synthesize]*, and steps 1–2 run in parallel (they're independent), 3–4 follow, 5 synthesizes. **Wins when** structure is stable and reviewable: the plan is an artifact — auditable before execution, delegable to cheaper executor models, parallelizable by inspection. **Fails by** staleness: if step 2 reveals the customer closed two accounts last week, steps 3–5 as planned are wrong; without a re-plan trigger the executor marches on. The mitigation is a *plan-validity check* between steps — which is itself a mini-reflect, so real systems drift toward a ReAct/plan hybrid. **Verdict:** prefer it where audit or delegation matters; budget for re-planning.

### Reflection (Generate → Critique → Improve)

A second pass — same or different model — critiques the output against criteria, then a revision incorporates the critique. **Wins when** errors are *detectable by inspection*: code (does it run? pass tests?), structured documents (schema-valid? all sections present?), calculations (recomputable?). A drafted loan-assessment memo critiqued against a checklist ("DTI computed? collateral valued per policy 7.1? exceptions flagged?") catches real omissions. **Fails when** the critic shares the generator's blind spots — asking the same model "is this good?" about open-ended prose mostly harvests agreement; and every reflection pass costs 30–100% more tokens. **Verdict:** attach it to inspectable outputs with explicit rubrics; skip it as a generic "quality" sprinkle. (Pointed at the long term — critiques stored and retrieved for future tasks — reflection becomes learning, Ch9 §4b.)

### Router

A classifier — rules, a small model, or both — dispatches each request to a specialized handler: intent classification in front of {policy-RAG, account-workflow, dispute-agent}. This is the pattern quietly running most production "agent systems," and it's the architecture of Ch23's Walmart case, where a complexity classifier routes simple queries *away* from the agent entirely — worth 53% latency. **Wins:** cheap, predictable, evaluable (routing accuracy is a labeled-classification metric — Ch17), and it maps traffic onto the cost-appropriate rung of Ch1's ladder. **Fails by** misroute at the boundaries — mitigate with a fallback route to the most capable handler plus routing-accuracy monitoring. **Verdict:** the front door of nearly every real deployment; boring, and boring is a feature.

### Supervisor

An agent that decomposes, delegates to worker agents, and integrates results — staying in the loop throughout (unlike a router, which dispatches and exits). **Wins when** subtasks genuinely need different contexts or permissions *and* their results need intelligent integration — the relationship-review example, if exposure analysis and service history live behind different systems with different credentials. **Fails by** bottlenecking (everything flows through one context that accumulates all workers' output — compress at the boundary, Ch8) and by *lossy delegation*: the most common multi-agent bug is a worker succeeding at the wrong task because the delegation under-specified it (typed delegation contracts, Ch15). **Verdict:** legitimate, but demand the justification (§3) before paying for it.

### Hierarchical (supervisors of supervisors)

**Wins** at very large scopes with clean divisional boundaries. **Fails by** telephone-game information loss — every layer summarizes, and summaries of summaries drift from ground truth — plus multiplied latency and cost. **Verdict:** in an enterprise, if you think you need three layers of agents, you usually need Ch21's *platform* (several independent agent products with clear contracts) instead of one giant organism.

### Human-in-the-Loop

An interrupt point where a person approves, edits, or redirects (mechanics: Ch4 checkpoint+interrupt; policy: Ch20). **Placement rule:** exactly where actions become irreversible, nowhere else — approvals sprinkled everywhere breed rubber-stamping, which is worse than no gate because it *looks* like control. **Verdict:** not optional in banking for mutating actions; design the approval surface as carefully as the agent (Ch20's evidence-bearing approvals).

### Event-driven agents

Agents triggered by events — a document lands, a threshold breaches, a payment fails — rather than requests. Pairs naturally with Ch6's queue architecture (the event *is* a job). **Watch for:** event storms (one upstream burst → a thousand agent runs → budget rails, Ch18) and idempotency (events redeliver; runs must not double-act). **Verdict:** how agents become *operational* rather than conversational; most back-office value lives here.

### Parallelization

Independent subtasks fanned out and joined — Gulli's pattern 3. Cuts wall-clock, not cost (same tokens, less waiting). Requires a join with a *reducer* for concurrent state writes (Ch4) and conflict policy when branches disagree (Ch15). **Verdict:** use whenever the dependency graph allows; it's free speed, not free work.

### Sequential pipeline / prompt chaining

Fixed stages, each stage's output the next stage's input (Gulli's pattern 1): extract → categorize → draft → format. The honest name for many production "agent systems" — and often the *right* design, per Ch1's placement. **Verdict:** never be embarrassed to ship a pipeline; be embarrassed to ship an agent where a pipeline sufficed.

### Prioritization

When an agent holds multiple pending goals, ordering is itself a decision: deterministic scoring (urgency × value × cost) where possible, model judgment for the ambiguous tail — the same owner-of-control-flow split as everywhere else, and the ranking gets logged either way.

**Naming note:** the literature has variants of the supervisor idea — the **Coordinator-Worker-Delegator (CWD)** model (Biswas & Talukdar) separates the front-door coordinator, the doers, and a delegator that assigns work. Useful vocabulary; identical design questions.

## 3. The selection framework — then worked, three times

Ask in order:

1. **Is the task path known in advance?** Yes → workflow/pipeline. No → continue.
2. **Can one agent with good tools do it?** Yes → single agent (ReAct or Plan-and-Execute). This is the strong default.
3. **Do subtasks need genuinely different contexts, tools, or permissions?** Only then multi-agent — split on *context and permission boundaries*, never on human org-chart metaphors.
4. **Is output quality checkable by inspection?** Add Reflection with an explicit rubric.
5. **Where are the irreversible actions?** HITL exactly there.

**Worked: complaint handling.** Path known? Partially — categories are known, investigations aren't. → Router front door (rule-based on intent). Simple categories → pipelines (acknowledge, categorize, draft). "Investigate" category → single ReAct agent with read tools. Irreversible action = sending the customer response → HITL before send. No multi-agent anywhere: nothing needed a second context or credential set.

**Worked: quarterly credit-review pack for 40 corporate accounts.** Path known? Yes — the pack's structure is fixed. → Plan-and-Execute per account (the plan doubles as the reviewer's checklist — audit artifact), parallelized across accounts (independent), Reflection on each memo against the credit-policy rubric (inspectable), HITL: the credit officer signs the pack. Multi-agent? Only if data access splits by system credentials — a data-gathering worker (read-only, broad) feeding an analysis agent (no system access at all) is a *permission* split, and passes question 3 legitimately.

**Worked: "monitor payment failures and fix what you can."** Event-driven trigger per failure; router on failure type; known types → remediation *workflows* (retry, re-route, notify — fixed by ops policy); unknown types → ReAct diagnostic agent that assembles a case and escalates (its irreversible actions: none — it only reads and reports, which is what makes autonomy acceptable here). This one composes five patterns and *still* contains no supervisor — composition ≠ hierarchy.

## 4. Anthropomorphic decomposition — the failure mode with a story

The most seductive wrong design of the multi-agent era: "we'll have a researcher agent, a writer agent, an editor agent, a fact-checker agent — like a newsroom!" A team builds exactly this for market-summary reports. Demo: charming — agents "discussing." Production: the researcher summarizes for the writer (information lost), the writer's draft goes to the editor who lacks the research context to catch substantive errors (so it polishes prose), the fact-checker re-retrieves everything the researcher already had (cost doubles), and a wrong figure in the final report takes a day to trace through four agents' transcripts. Total cost: ~8× a single-agent baseline. Quality: indistinguishable. The rebuild: *one* agent with retrieval tools, a Reflection pass against a factual rubric, HITL sign-off. Cost: 1×. Debugging: one trace.

The lesson, generalized: **humans divide work that way because human attention doesn't scale and human specialties are real; agents don't share those constraints.** Agents share a model. Splitting them creates *communication boundaries* — and every boundary is a summary, and every summary loses information (Ch15 formalizes this). Split only when a boundary *does* something: isolates a context, isolates a credential, isolates a cost tier, or enables true parallelism.

## 5. Trade-off table

| Pattern | Cost | Latency | Auditability | When it wins |
|---|---|---|---|---|
| ReAct | Medium | Medium | Low | Unknown paths, exploratory tasks |
| Plan-and-Execute | Medium | Medium | **High** | Stable multi-step structure; audit/delegation needs |
| Reflection | +30–100% | +1 pass | Medium | Inspectable outputs with explicit rubrics |
| Router + specialists | Low per query | Low | High | Heterogeneous traffic (i.e., all real traffic) |
| Supervisor | High | High | Medium | True delegation across context/permission boundaries |
| Hierarchical | Very high | Very high | Low | Rarely; prefer platform decomposition |
| Pipeline | **Lowest** | **Lowest** | **Highest** | Known paths |
| Parallel | Same tokens | **Low** | Medium | Independent subtasks |

Read the table columns as *currencies*: you're always buying adaptivity with some mix of cost, latency, and auditability. The verdict column of §2 is this table with reasons attached.

## 6. How the industry actually converged

Across published engineering lessons (Anthropic's agent-building guidance prominent among them), production systems converge on the same stack: **router at the front, single capable agents behind it, pipelines for the known paths, Reflection where outputs are inspectable, HITL at irreversible actions** — and multi-agent only where the Ch15 justifications hold. The recurring written advice is almost monotonous: start with the simplest pattern that works; add structure only when traces show you need it; elaborate agent societies demo well and page you at 3am. The Walmart selective-agency result (Ch23) is the same convergence measured: the win came from routing *around* the agent.

## 7. Hands-on lab

Implement one task — "given a customer complaint email, produce a categorized case with a drafted response" — twice: as ReAct with tools, and as Plan-and-Execute. Run both on 20 varied complaints (include two ambiguous ones and one that's not a complaint at all). Log tokens, latency, failure modes, and — for Plan-and-Execute — how often the plan needed repair. Then add a Reflection pass with an explicit rubric to whichever won, and measure what it caught vs what it cost. Deliverable: a half-page memo — *which goes to production and why* — written in the trade-table's currencies. (The memo matters more than the code; it's the §3 framework internalized.)

## 8. Architect's take: the banking read

Pattern choice in a bank is *risk allocation*. Plan-and-Execute gives you a reviewable artifact per run — often worth its staleness tax for that alone. Router + specialists maps cleanly onto the bank's permission topology: the card agent holds card-system credentials, the loan agent holds LOS credentials, no agent holds both — pattern design *is* least-privilege design (Ch19), and presenting it that way ("the architecture enforces separation of duties") is what gets multi-agent designs approved rather than questioned. And keep §4's story loaded: when someone proposes a newsroom of agents, you want the 8×-cost, same-quality, one-day-debugging version told in ninety seconds.

## Governance & security lens

Pattern choice is risk allocation. Plan-and-Execute produces an auditable plan artifact; Router+specialists maps agents onto permission boundaries so no agent holds combined credentials; HITL placement decides where a human is legally in the decision chain. Governing question: **which pattern gives the auditor an artifact, and which split enforces least privilege?** If a proposed multi-agent design doesn't change the permission or audit story, it's probably org-chart theater with extra attack surface.

## Interview-ready lines

- "Split agents on context and permission boundaries, never on org-chart metaphors — agents don't need meetings."
- "One good agent plus tools beats ten agents talking to each other — until traces prove otherwise."
- "Plan-and-Execute's plan is an audit artifact; in regulated industries that's a feature, not overhead."
- "Reflection pays only where errors are detectable by inspection — a critic that shares the generator's blind spots just harvests agreement."
- "The router is the highest-ROI pattern in production: it puts every query on the cheapest rung that solves it."
- "HITL goes exactly where actions become irreversible — everywhere else it's just latency that trains rubber-stamping."
