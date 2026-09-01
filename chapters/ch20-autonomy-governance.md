# Chapter 20: Autonomy Levels, Human-in-the-Loop & Governance

> Autonomy is not a property of the agent. It is a property you assign, per action class, and can defend in writing.

## 1. The autonomy ladder

```text
L0  Assist    — human does the task; AI informs        (search, summarize)
L1  Suggest   — AI proposes; human decides and acts    (draft reply, recommendation)
L2  Approve   — AI acts after explicit human approval  (execute-with-approval)
L3  Autonomous— AI acts; humans monitor and audit      (within bounded scope)
```

The unit of assignment is the **action class**, not the agent. One agent legitimately operates at three levels simultaneously: read customer data (L3, logged), generate a recommendation (L3, it's a draft by nature), send the customer a communication (L2), move money (L2 with maker-checker, or simply "humans only").

## 2. Assigning levels: the criteria

Score each action class on **reversibility** (can it be undone cheaply?), **blast radius** (money, customers, reputation, regulatory exposure), **detectability** (would a mistake be caught before harm?), and **measured reliability** (your Ch17 eval scores — not the vendor's benchmark). High reversibility + low blast radius + strong evals → autonomy is cheap to grant. Irreversible + high blast radius → approval, regardless of how good the evals look. Write the matrix down; it *is* your autonomy policy, and it converts "should agents be autonomous?" (unanswerable) into rows (answerable).

## 2b. The autonomy matrix, visualized

```yaml
# One page. This IS the autonomy policy — reviewable, versionable, defensible.
agent: card-services            # levels are per ACTION CLASS, not per agent
actions:
  read_customer_data:     {level: L3, basis: reversible+logged,     review: quarterly}
  generate_recommendation:{level: L3, basis: draft-by-nature,       eval_gate: ">=0.92"}
  send_customer_comms:    {level: L2, basis: reputational,          approver: RM}
  block_card:             {level: L2, basis: irreversible-for-user, approver: ops}
  transfer_funds:         {level: none, basis: policy}              # humans only
kill_switch: revoke identity arn:...:role/card-agent   # the handle (Ch19)
```

## 3. HITL that actually works

Mechanics from Ch4 (interrupt + checkpoint + resume), design from here:

- **Placement**: exactly where actions become irreversible (Ch3). Approvals sprinkled everywhere breed rubber-stamping — the operator who approves 200 items/day approves everything.
- **The approval must carry decision-relevant context**: what will happen, why the agent chose it, evidence with citations, confidence signals, and *what happens on reject*. An approval UI showing raw JSON is theater.
- **Attention budget as a designed quantity**: batch low-risk approvals, escalate only exceptions, rotate reviewers, and *measure* override rates — a 0% override rate means the checkpoint is decorative (remove it or enrich it); a 40% rate means the agent isn't ready for L2.
- **Escalation is a feature**: "I'm not confident; routing to a human with the case assembled" is desired behavior — reward it in evals rather than penalizing non-completion.
- **Async approval, not a blocked thread**: the agent doesn't sit inside a live call waiting on a human — that's what Ch4's checkpoint is for. Execution suspends at the approval boundary, state is checkpointed and durably persisted, and the compute is released; the decision, whenever it arrives, rehydrates the agent from that checkpoint to *resume* rather than restart. This is what makes L2 viable at volume — a reviewer clearing a queue at 6pm resumes agents that suspended hours earlier, with nothing held open in between.
- **Timeout policy belongs in the matrix, not left implicit**: decide, per action class, what happens when nobody approves in time — escalate to a backup approver, or fail closed (auto-deny), are the usual right answers. Auto-approve-on-timeout is almost always wrong above L1: it silently converts an L2 action back to L3 the moment the review queue backs up, which is exactly the failure the level was assigned to prevent, and nobody actually decided it should happen.

## 4. Governance: the machinery around the ladder

- **Model risk management (MRM)**: agents are models-plus — inventory every agent (purpose, owner, autonomy matrix, model/prompt versions), validate before deployment (Ch17 suites as the validation evidence), monitor in production (Ch16 signals), and re-validate on change.
- **Audit trails**: every action traceable to agent identity, on-behalf-of user, delegation record, trace, and (for L2) approver — Ch16's trace + Ch19's identity, retained per record-keeping rules.
- **Kill switches, graded**: per-agent, per-tool/integration (Ch14's gateway), and platform-wide; halting must checkpoint state and leave a clean audit trail (Ch18). Practice the drill; a kill switch first pulled during an incident is a hypothesis.
- **Accountability**: a named human owner per agent. "The AI decided" is not a sentence a bank can say to a regulator; "our system, owned by X, operating under policy Y, decided — and here's the record" is.

## 5. The regulatory anchor (India, and beyond)

**RBI's FREE-AI framework** (Framework for Responsible and Ethical Enablement of AI, Aug 2025) sets the direction for Indian financial services: board-approved AI policies, governance structures, risk-based oversight, data governance, and consumer protection — its seven *sutras* (trust, people-first, innovation-with-integrity, fairness, accountability, understandability, safety) map remarkably cleanly onto this curriculum's chapters. **RBI's 2026 draft Model Risk Management guidance** goes further: board-level MRM frameworks, validation independence, third-party model accountability (you own the risk of vendor models), and **kill-switch expectations** for AI systems. Add **DPDP** (purpose limitation, minimization, erasure — Ch8/Ch9 implement these) and, for perspective, the **EU AI Act's** risk-tiering (credit scoring sits in high-risk; its conformity mindset is coming everywhere). The architect's advantage: build the governance machinery *as platform features* now — inventory, evals-as-validation, audit trails, kill switches — and regulation becomes a mapping exercise rather than a retrofit.

## 5b. Trust, transparency & fairness — the user-facing layer

Governance machinery convinces regulators; **trust design** convinces users, and FREE-AI's fairness and understandability sutras make it obligatory, not optional:

- **Explainability at the point of decision**: every recommendation carries its "because" — sources cited (Ch10/12), path shown (Ch11's graph traversals), factors named. Design outputs so the explanation is *generated from the actual evidence trail*, not confabulated after the fact — the trace (Ch16) is the ground truth the explanation must match.
- **Uncertainty communication**: agents that always sound confident train users into automation bias — the costliest trust failure. Calibrate: hedge when evidence is thin, state what's missing, and make "I'm not sure — escalating" a first-class output (rewarded in evals, Ch17).
- **User control and consent**: visibility into what the agent did on your behalf, the ability to correct it, and consent boundaries for data use (DPDP again) — product features, but governance-shaped ones.
- **Bias and fairness testing**: for anything touching credit, pricing, or eligibility, fairness metrics across protected segments join the eval suite (Ch17) and the MRM validation evidence — in India, with FREE-AI's fairness sutra as the explicit anchor. Bias is evaluated, monitored for drift, and documented — not asserted.

## 6. Trade-offs

Governance overhead scales with autonomy ambition — the honest move is often to ship at L1/L2 and *earn* L3 with eval evidence and override-rate history, which is also exactly the story a risk committee wants to hear. Over-governance is real too: an approval on every read query kills the platform's value and trains contempt for the controls. The matrix, revisited quarterly with data, is the balancing instrument.

## 7. Hands-on lab

Write the autonomy matrix for the banking agent platform (10 action classes × the four criteria × assigned level, one page). Implement one L2 flow end-to-end: interrupt before `send_notification`, an approval surface showing evidence + reject path, override-rate metric on the dashboard. Then run the kill drill: revoke one agent's identity mid-run; verify clean halt, checkpointed state, audit entry, and resume-after-restore. Document the drill — that document is portfolio gold.

## 8. Architect's take: the banking read

This chapter is your home turf as an AVP: you already know how banks govern; the work is translating agents into that machinery. The strongest positioning move in your portfolio is the one-page autonomy matrix + FREE-AI mapping — no framework tutorial teaches it, almost no candidate has it, and every Indian bank building agents needs it. Governance-as-platform-feature is the difference between an AI architect and an AI enthusiast.

## Interview-ready lines

- "Autonomy is assigned per action class, not per agent — one agent, three levels, one matrix."
- "A 0% override rate means the human checkpoint is decorative; measure it."
- "Escalation is desired behavior — reward 'I'm not confident' in your evals."
- "Build inventory, evals-as-validation, audit, and kill switches as platform features, and regulation becomes a mapping exercise."


## Interview Questions & Answers

**Q1: Why should autonomy be treated as a graduated dial rather than a binary "the agent is autonomous or it isn't"?**

Because the real unit that matters is the action class, not the agent, and different actions carry wildly different reversibility and blast radius even inside one workflow. A card-services agent can safely read customer data at L3 (logged, reversible) while the same agent needs L2 approval to send a customer communication (reputational risk) and no autonomy at all to move money. Collapsing that into one autonomy flag for the whole agent either strangles the safe 90% of the work with unnecessary approvals or exposes the dangerous 10% with none. A per-action-class ladder — Assist, Suggest, Approve, Autonomous — lets you score reversibility, blast radius, detectability, and measured reliability independently for each action and write the answer down as a matrix a risk committee can actually review.

**Q2: A critique making the rounds is that "human in the loop" by itself isn't a real governance strategy — what's missing, and how would you respond to that in an interview?**

That critique is fair if HITL is implemented as a checkbox — a person clicks approve without the context to meaningfully disagree, which is rubber-stamping wearing a compliance costume. Real governance needs the approval to carry decision-relevant context (what will happen, why the agent chose it, evidence with citations, what happens on reject), an attention budget that routes only genuine exceptions to humans, and a measured override rate, because a 0% override rate is proof the checkpoint is decorative and should be removed or enriched, not evidence the agent is trustworthy. On top of that, HITL alone doesn't give you inventory, validation, audit trails, or a kill switch — it's one control inside an MRM program, not a substitute for one. So the honest answer isn't "we have a human in the loop," it's "we have a human in the loop whose override rate we track, backed by an audit trail and a named accountable owner."

**Q3: What if an agent takes an action it wasn't supposed to be autonomous for — say an L1 "suggest" agent somehow sends a customer communication without going through approval? Walk me through it.**

First, the trace has to make it possible to know this happened at all — every action needs to be traceable to agent identity, the on-behalf-of user, the delegation record, and the trace itself, so you're not relying on the customer complaining to find out. The immediate response is the kill switch: revoke that agent's identity or its tool integration through the gateway, which halts it cleanly, checkpoints state, and leaves an audit entry — this is exactly why you practice the drill before an incident forces you to. Next is root cause: was this a policy misconfiguration in the autonomy matrix, a prompt or tool-permission drift, or a genuine escape of the approval gate, because each has a different fix. Finally it becomes an MRM re-validation event — the agent is re-validated before it's allowed back to its prior autonomy level, and the incident and remediation get documented, because "the AI decided" is not an answer a bank can give a regulator; "our system, owned by X, operating under policy Y, failed this way and here's the fix" is.

**Q4: An L2 agent correctly gets human approval to block a card, but the downstream notification to the customer silently fails. What happens next, and how would you have caught it?**

The approval being correct doesn't mean the outcome was correct — governance has to extend past the approval checkpoint into the full action, which is why the audit trail needs to capture not just "approved" but the execution result and any downstream side effects tied to that trace. In production this should surface through the same monitoring signals used for evals and drift detection (Ch16), with the notification failure treated as a production incident, not a one-off support ticket, because a pattern of silent downstream failures behind a correctly-approved action is a systemic risk the matrix doesn't currently price in. The fix is usually to bring the downstream step inside the traced, monitored boundary — either the agent verifies delivery and re-attempts or escalates, or the notification service itself gets health checks wired into the same dashboard as the override-rate metric. This is also a good argument for why "the human approved it" can't be where accountability ends; the named owner is accountable for the whole action chain, not just the checkpoint.

**Q5: What are the cost trade-offs of putting a human in the loop at different autonomy levels — latency and throughput versus risk?**

Every approval step adds latency and consumes a scarce resource — human attention — so the cost isn't just the reviewer's time, it's the throughput ceiling on the whole workflow and the user experience hit of a customer waiting on a human who's approving 200 similar items a day. That volume is exactly what breeds rubber-stamping, so the naive fix of "add more approval gates" actually degrades the safety you're paying for while still paying the latency cost. The better trade is to spend the attention budget deliberately: batch low-risk approvals, escalate only genuine exceptions, and route routine, well-evidenced cases toward L3 once eval scores and override-rate history justify it — earning autonomy with evidence is cheaper in aggregate than gating everything at L2 forever. The honest framing for a risk committee is that governance overhead scales with autonomy ambition, and over-governance — an approval on every read query — kills platform value just as surely as under-governance creates blast-radius risk.

**Q6: What are the data security implications of granting an agent a higher autonomy level, for example L3 read access on customer data?**

Higher autonomy on data access widens the blast radius of a prompt injection, a compromised credential, or an agent bug, because at L3 the agent is acting on that data without a human checkpoint catching a misuse in real time — so the control has to move upstream, into what the agent's identity is scoped to touch in the first place. That's why the autonomy matrix pairs each action's level with its basis (reversible+logged, for read access) — logging is the compensating control for autonomy, giving you after-the-fact detectability even without a pre-action approval. It also means DPDP's purpose limitation and minimization principles aren't optional extras; they define the boundary of what an L3-autonomous agent is even allowed to read, independent of whether it's technically capable of reading more. Practically, granting L3 on data access should always be reviewed alongside the entitlements the agent's identity carries — autonomy level and access scope are two dials that need to move together, not independently.

**Q7: How would you design the guardrails — the autonomy dial and kill switches — for an agentic platform running in a bank?**

The autonomy dial is the matrix itself: a versioned, reviewable document mapping each action class to a level, its basis, and (for L2) its approver, so "should this agent be autonomous" becomes a row you can defend rather than a debate. Kill switches need to be graded — per-agent, per-tool or integration through the gateway, and platform-wide — because an incident involving one compromised tool shouldn't require pulling every agent offline, and each level needs to halt cleanly, checkpoint state, and leave a clean audit trail rather than just stopping mid-transaction. Both controls are only real if you practice them: a kill switch first pulled during a live incident is a hypothesis, not a control, so the drill — revoke identity mid-run, verify clean halt and resume-after-restore — belongs on a schedule. The dial and the switch work together: the dial decides who needs to approve before an action, the switch decides how fast you can stop everything if that decision turns out to be wrong.

**Q8: How should access control, least privilege, and entitlements be tied to an agent's autonomy level?**

They should move together but they're not the same lever — autonomy level governs whether a human approves before an action fires, while entitlements govern what the agent's identity is even capable of touching, and conflating them is how you end up with an agent that's technically L2-gated on sending comms but holds broad database credentials it doesn't need for that action. The right pattern is to scope the agent's role or ARN to exactly the actions in its matrix — read_customer_data, generate_recommendation, send_customer_comms — with transfer_funds simply absent from its entitlements rather than gated by policy alone, so a prompt injection or logic bug can't reach an action the agent was never credentialed for regardless of what the matrix says. This is also what makes the kill switch meaningful: revoking an identity only contains the blast radius if that identity's entitlements were already least-privilege: revoking a role with excess permissions still leaves standing sessions or cached credentials with reach the incident never accounted for. In short, autonomy level is the policy layer and entitlements are the enforcement layer, and MRM validation should check that the two actually match before deployment, not assume they do.

**Q9: From an MRM traceability standpoint, what does a bank need in production to prove an agent's decision was compliant, and how do you validate it before deployment?**

Treat the agent as a model-plus: it needs an inventory entry with purpose, owner, autonomy matrix, and model/prompt versions, validated before deployment using your eval suite as the validation evidence rather than a vendor's benchmark, and re-validated whenever the model, prompt, or matrix changes. In production, every action has to be traceable to agent identity, the on-behalf-of user, the delegation record, the trace itself, and — for L2 actions — the approver, retained per record-keeping rules, so an examiner asking "why did the agent do this on this date" gets an answer from the record, not from institutional memory. Monitoring has to run continuously, not just at go-live, using the same signals that feed the eval suite, because model risk doesn't stop accruing once something ships. The strongest artifact you can produce here is the one-page autonomy matrix itself plus its FREE-AI mapping — it's simultaneously your governance policy, your validation scope, and your audit answer to "how did you decide this agent could act on its own."

**Q10: Design the autonomy governance for a new agentic lending-assistant deployment at an Indian bank, referencing RBI's FREE-AI framework.**

Start with the matrix: reading applicant data and generating a draft eligibility recommendation can sit at L3 if evals clear your bar, because both are reversible and logged, but anything touching the actual credit decision or customer-facing communication about approval or rejection needs L2 with a named approver, given the reputational and regulatory exposure of getting a lending decision wrong. Map this directly to FREE-AI's seven sutras — accountability and understandability drive the audit trail and explainability requirements, fairness drives bias testing across protected segments as part of the eval suite and MRM validation evidence, and safety drives the kill-switch and MRM validation posture RBI's 2026 draft guidance calls out explicitly, including third-party accountability if the lending model is vendor-supplied. Layer DPDP on top for data minimization and purpose limitation on applicant data, and treat EU AI Act-style risk tiering as a preview of where India is headed, since credit scoring is squarely high-risk under that framework too. The deliverable a candidate should describe is exactly this chapter's lab artifact: a one-page matrix plus explicit FREE-AI and MRM mapping, because that turns "is this compliant" from an open question into a document a risk committee can sign off on.

**Q11: Who is accountable when an autonomous agent's decision turns out to be wrong, and how do you stop "the AI decided" from becoming the answer?**

Accountability has to be assigned to a named human owner per agent before the agent ever runs at L2 or L3, not discovered after an incident — the inventory entry that MRM requires already forces this, because "owner" is a mandatory field alongside purpose and autonomy matrix. The audit trail is what makes that ownership defensible rather than nominal: agent identity, on-behalf-of user, delegation record, trace, and approver reconstruct exactly what happened and under what policy, so the answer to a regulator is "our system, owned by X, operating under policy Y, decided — and here's the record," not a shrug toward the model. This is also why the autonomy matrix matters for accountability specifically: if an action was assigned L3 based on eval evidence and override-rate history, the owner can point to the basis for that grant; if it was assigned L3 without evidence, that's the actual failure, and it's a governance failure, not a model failure. The discipline this enforces is that autonomy is something a human granted, in writing, for a documented reason — which is precisely what keeps the accountability chain from dead-ending at the model.

**Q12: How do you prevent L2 approval checkpoints from decaying into rubber-stamping once volume ramps up?**

Rubber-stamping is a predictable failure mode of high-volume approval, not a discipline problem — an operator approving 200 items a day will approve everything unless the system is designed against it, so the fix is architectural rather than a reminder to "review carefully." Treat attention as a designed quantity: batch low-risk approvals so reviewers aren't context-switching per item, escalate only genuine exceptions instead of routing everything through the same gate, and rotate reviewers so no one person becomes the permanent rubber stamp. The override rate is the instrument that tells you whether it's working — 0% means the checkpoint has already become decorative and needs removing or enriching with better evidence, while something like 40% means the underlying agent isn't ready for the autonomy level it's been given. Reviewed on a cadence, that number is also the evidence base for moving an action class up the ladder to L3, so the same metric that catches decorative approvals is what lets you responsibly retire them.
