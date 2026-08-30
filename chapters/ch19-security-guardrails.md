# Chapter 19: Security & Guardrails

> The unfixable premise: the model cannot reliably distinguish instructions from data. All real agent security is designed around that fact, not against it.

## 1. The threat model (anchored to OWASP Agentic Top 10, 2026)

The named risks worth internalizing as *categories*:

- **Prompt injection** — instructions smuggled through content the agent reads (documents, emails, web pages, tool results). Not a bug to patch; a permanent property to architect around.
- **Tool poisoning / supply chain** — a compromised or malicious tool (or MCP server) feeding lies or exfiltrating arguments; tool *descriptions* themselves are an injection vector.
- **Excessive agency / privilege compromise** — the agent can do more than its task needs, so a hijacked agent does more damage than its task could.
- **Data exfiltration** — sensitive context leaking out through tool calls, URLs, or generated content (the classic: injected instructions telling the agent to send what it knows somewhere).
- **Memory poisoning** — injected content that persists across sessions via the memory layer (Ch9) — worse than context poisoning because it survives.
- **Identity abuse & impersonation** — unclear whose authority an agent acts under; agent-to-agent trust gamed (Ch14).
- **Cascading failures** — one compromised agent's output becoming another's trusted input (Ch15 topologies propagate compromise).

## 2. The layered defense

```text
USER/CONTENT ──► INPUT GUARDRAILS ──► AGENT ──► AUTHZ ──► TOOLS ──► OUTPUT GUARDRAILS
                 (injection/policy      │        (per-call,   │        (leakage, policy,
                  classifiers,          │         user-scoped) │         grounding checks)
                  content marking)      │                      │
                          harness bounds (Ch5) · sandbox · audit (Ch16)
```

The load-bearing principle: **guardrail models filter; architecture prevents.** Classifiers catch much injection and policy violation — deploy them — but they are probabilistic, so the damage ceiling must be set by things that are *facts*:

- **Least-privilege tool grants** (Ch13's registry): the agent processing inbound documents has no send-anything tool; then injected "email this to…" instructions fail on *absence of capability*, not on detection.
- **User-scoped authorization on every tool call** (Ch14's gateway): the agent is never a super-user; it can only touch what the on-behalf-of user could.
- **Sandboxed execution** (Ch5): generated code and untrusted-content processing run with no default network and allowlisted egress — exfiltration needs a *route*, deny it one.
- **Trust labeling in context** (Ch8): the assembler marks content by origin (user instruction vs retrieved data vs tool result); policies key off labels — e.g., mutating tools cannot be triggered by goals originating in retrieved content without HITL.
- **Egress control on outputs**: URLs, recipients, and destinations in agent output validated against allowlists before any send/render.

## 2b. Blast radius as configuration, visualized

```yaml
# What a fully hijacked doc-processing agent can do — the SHORT LIST, by construction
agent: document-intake
identity: arn:...:role/doc-intake-agent          # its own NHI, owned by a human
tools:                                           # injected "email this to X" fails on
  read_document:   allow                         #   ABSENCE of capability, not detection
  extract_fields:  allow
  create_case:     allow(scope: dept=ops)
sandbox:
  network_egress:  [core-banking.internal]       # exfiltration needs a route — denied
context_policy:
  retrieved_content: {label: untrusted,          # trust labels from the assembler (Ch8)
                      may_trigger_mutations: never}
```

## 3. Agent identity: the NHI problem

Agents are **non-human identities** at scale — each needs: its own identity (never a shared service account), short-lived scoped credentials (the Ch7 task-role pattern generalized; workload identity, zero static keys), an owner (a human accountable for each agent), lifecycle management (provision → rotate → *decommission* — orphaned agent identities are the new orphaned service accounts), and delegation records ("agent A, on behalf of user U, for purpose P" travels with every call and lands in the audit log). Identity is also the kill switch's handle: revoke the identity, the agent stops everywhere (Ch20).

## 4. Design decisions & trade-offs

Guardrail strictness vs task success is a tunable, evaluable trade — red-team suites (Ch17) measure catch-rate while golden suites measure the false-positive tax; tune with both on the table. Defense-in-depth costs latency (input + output classifiers on every turn) — tier it by risk class: read-only internal Q&A gets lighter gates than anything mutating or customer-facing. And accept the residual: with injection unfixable, your objective is a *bounded blast radius* you can state — "worst case, a fully hijacked agent can do exactly X" — and X is set by grants, not by hope.

## 5. Industry implementation

Converged stack: guardrail classifier layer (prompt-injection, PII, policy — vendor or open models) + gateway authorization + sandboxing + red-team automation (DeepTeam-class tooling against the OWASP list) + NHI governance products entering the identity stack. The maturity marker: security reviews that ask "what can it do when compromised?" rather than "how good is the filter?"

## 6. Hands-on lab

Attack your own banking agent: build a 20-case injection suite (poisoned policy doc, malicious tool description, exfiltration lures, memory-poisoning attempt). Run it against three configurations: (a) prompt-only defenses, (b) + guardrail classifiers, (c) + least-privilege grants, egress allowlists, and trust labels. Publish the catch/damage matrix. The expected result — (a) fails, (b) helps, (c) bounds — is the whole chapter in one table, and a superb portfolio artifact.

## 7. Architect's take: the banking read

Present agent security to a bank in the bank's own control language: capability grants = entitlement management; delegation records = maker-checker audit trails; sandbox egress = data-loss prevention; NHI lifecycle = the same IAM governance applied to a new identity class; blast-radius statements = the risk-acceptance memo. The sentence that wins the CISO meeting, from Ch7, generalized: **"Restricting the agent in the prompt is a request; restricting it in identity, grants, and egress is a fact — and we built the facts."**

## Interview-ready lines

- "Prompt injection is a property, not a bug — architect for bounded blast radius, don't promise detection."
- "Guardrails filter; grants, identity, and egress prevent."
- "An agent is a non-human identity with an owner, a scope, a lifecycle, and a kill handle."
- "The security review question is 'what can it do when compromised?' — and the answer must be a short list."
