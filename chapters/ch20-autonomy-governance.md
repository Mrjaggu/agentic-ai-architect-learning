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
