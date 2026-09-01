# Chapter 13: Tools & Function Calling

> Tool design is API design for a consumer that reads documentation perfectly, reasons well, and has no common sense you didn't give it.

## 1. The mechanics, quickly

The model never executes anything. It emits a structured request — `{name, arguments}` conforming to a declared JSON schema — and the harness validates, authorizes, executes, and returns a result into context (Ch2/Ch5). Everything interesting is in the design of the schemas and the results.

## 2. Designing tools an LLM can actually use

- **The description is the interface.** The model chooses tools by reading names and descriptions. Write them like documentation for a bright new hire: what it does, when to use it, when NOT to use it, what it returns. Ambiguous descriptions are the #1 cause of wrong-tool selection.
- **Right-size the surface.** Neither one giga-tool ("do_banking(action, …)") nor forty micro-tools. Group by task intent; keep the active toolset small per agent (selection accuracy degrades as the toolset grows — measured, not folklore). If an agent needs 40 tools, it's usually several agents (Ch3's permission-boundary split).
- **Schemas that prevent errors**: enums over free strings, constrained types, required vs optional made honest, defaults documented. Every degree of freedom you leave open is a decision the model must get right unaided.
- **Idempotency and safety annotations**: mark tools read-only vs mutating vs irreversible. The harness uses this — mutating tools get confirmation policies (Ch20), irreversible ones get HITL. Retries are only safe on idempotent tools (Ch6's redelivery).

## 3. Tool *result* design — the neglected half

What the model sees back determines what it does next:

- Return **structured, compact, decision-relevant** results — not raw dumps. The 200-row query returns stats + samples + row count (Ch8's compression at the source).
- **Errors are prompts.** "ValidationError: date_to before date_from — swap the arguments?" recovers in one turn; a stack trace burns three. Design error messages as instructions to a capable reader.
- **Partial success must be explicit** ("wrote 8 of 10; failed ids: …") or the model will assume completion.
- Include **next-step affordances** where natural ("result truncated; call again with cursor=…").

## 3b. A well-designed tool, visualized

```python
class GetTransactions(BaseModel):
    """Fetch a customer's card transactions for a date range.
    Use for spend questions. NOT for balances (use get_accounts).
    Returns at most 50 rows, newest first."""              # when / when-not / what-back
    customer_id: str
    date_from: date
    date_to: date
    channel: Literal["pos", "online", "atm", "all"] = "all"  # enum beats free string

# and the error a model can RECOVER from — an instruction, not a stack trace:
{"error": "date_to (2026-01-05) is before date_from (2026-03-01) — "
          "swap the arguments and retry."}
```

## 4. Structured outputs at the boundary

The same schema machinery, pointed at final answers: constrain outputs to a typed schema (native structured-output modes or grammar-constrained decoding) so downstream systems consume types, not prose (Ch6's workers persist typed results). Validate at the boundary; on failure, one repair pass with the validation error, then fail closed. Schema-first output design is what makes agents composable with ordinary software.

## 4b. Skills — the other half of capability

Tools give an agent the ability to *act*; **Agent Skills** give it the knowledge of *how to do a job well*. A skill is a folder — `SKILL.md` (instructions, conventions, checklists) plus optional scripts and reference files — that the agent loads **progressively**: at startup it sees only each skill's name and one-line description (a few dozen tokens); when a task matches, it reads the full instructions; scripts run only if needed. Anthropic open-sourced the format in late 2025 and it spread across the ecosystem through 2026 — treat it as a standard, like MCP.

```text
banking-comms-style/
  SKILL.md          # when to use; tone rules; templates; compliance checklist
  templates/        # approved letter formats
  check_tone.py     # optional validation script the agent may run
```

The architect's decision rule — **MCP connects, skills instruct**:

| Need | Build a… | Example |
|---|---|---|
| Access to a system or live data | MCP tool (Ch14) | query core banking, file a case |
| Procedural know-how, house style, a repeatable method | Skill | dispute-handling procedure, RBI-compliant comms style, spreadsheet conventions |
| Both | MCP tool + a skill that teaches when/how to use it | "collections outreach" = CRM tools + the playbook skill |

Why this matters architecturally: skills are **context engineering as packaging** (Ch8's progressive disclosure, productized — capability that costs ~0 tokens until needed); and they make expertise *versionable and shareable* (the dispute playbook is a reviewed, git-tracked artifact, not tribal prompt knowledge). In the bank framing: skills are your SOPs, compiled for agents.

**Using skills well — the practice:**
- **Small and single-purpose.** One job per skill ("draft RBI-compliant collections letters"), with a description written for *triggering* — the agent selects skills by reading descriptions, exactly like tools (§2's rule applies: the description is the interface).
- **Instructions over scripts, scripts over hope.** Put judgment in SKILL.md; put anything deterministic (validation, formatting, calculations) in a bundled script the agent runs — a script can't hallucinate.
- **Treat the skill library like code.** Git-versioned, code-reviewed, released with version pins; changed skills go through the same eval suite as changed prompts (Ch17) because a skill *is* a prompt with privileges.
- **Compose, don't inline.** A skill that teaches when/how to use a set of MCP tools beats stuffing usage guidance into every tool description.

**Skills governance & security — non-negotiable in an enterprise:**
- **Curated internal registry, allowlist-only.** Agents install nothing at runtime; a skill enters the registry through review (does it exfiltrate? over-instruct? conflict with policy?) with a named owner — the same lifecycle as a tool grant or an MCP server (Ch14).
- **A malicious skill is prompt injection with packaging** plus a supply-chain payload (its scripts execute). So: scripts run in the sandbox with the *agent's* grants — a skill must never widen what the agent can do, only how well it does it; skill provenance is pinned (hash/signature), and third-party skills are vetted like third-party libraries.
- **Auditability**: which skill (and version) was loaded into which run lives in the trace (Ch16) — "why did the agent write that letter?" must be answerable with "collections-comms v2.3, this checklist."

## 5. Trade-offs

Rich schemas and results cost context tokens (every tool schema rides in every call — another Ch8 budget line; load tools dynamically per phase if the set is large). Tight enums prevent errors but require maintenance as systems evolve. Fine-grained tools improve auditability but multiply calls; coarse tools save latency but blur the audit trail. Decide per tool with the trade named.

## 6. Industry implementation

Converged practice: schemas generated from typed code (Pydantic/Zod) so tool and implementation cannot drift; tool registries with ownership and versioning; "tool use" quality tracked as its own eval suite (selection accuracy, argument validity, recovery rate — Ch17). The best public examples of tool-description craft are MCP servers from major vendors — read them like literature.

## 7. Hands-on lab

Build 6 tools for the banking agent (get_customer, get_accounts, get_transactions, search_policy, create_case, send_notification — the last one marked irreversible). Write two versions of each description: lazy and crafted. Run 30 tasks against both; measure wrong-tool selection and argument errors. Then break a result deliberately (raw dump vs shaped) and watch downstream reasoning degrade. Two portfolio tables: description quality → selection accuracy; result design → recovery rate.

## 8. Architect's take: the banking read

Every tool is a *capability grant* and should be treated like an API product in a bank: owner, version, entitlement mapping (which agent/user/purpose may call it), rate class, and audit logging of arguments and results (with PII masking in the log pipeline). The tool registry becomes the bank's inventory of "what agents can actually do" — the first artifact risk asks for, and the one that makes Ch19's least-privilege real rather than aspirational.

## Governance & security lens

Tools and skills are the two capability classes, and both get identical lifecycle treatment: registry with named owners, review before availability, version pinning, entitlement mapping, and per-call audit with PII-masked arguments. Tool annotations (read-only/mutating/irreversible) are what let the harness apply graded policy; skills add supply-chain review because their scripts execute and their instructions steer. Governing questions: **is there a single inventory of everything agents can do and know how to do, who approved each entry, and can any capability reach an agent without passing through it?** The registry is the answer to the auditor's first question.

## Interview-ready lines

- "The description is the interface — wrong-tool selection is usually a documentation bug."
- "Errors are prompts: a good error message recovers in one turn."
- "Mark tools read-only / mutating / irreversible; the harness turns those annotations into policy."
- "The tool registry is the bank's inventory of what agents can actually do."


## Interview Questions & Answers

**Q1: Why does tool description quality matter as much as the underlying model's capability?**

Because the model chooses which tool to call by reading names and descriptions the same way a new hire reads documentation — a frontier model handed two ambiguously-described tools (say `get_accounts` vs `get_transactions` with overlapping wording) will still guess wrong, and no amount of raw capability fixes a documentation bug. The chapter's `GetTransactions` example makes this concrete: the docstring earns its keep by stating what it does, when to use it, when NOT to use it ("NOT for balances"), and what comes back — that's the actual interface the model reasons against, not the Python signature underneath it. Swapping in a bigger model without fixing the description just gets you a smarter model making the same wrong call, faster and with more confidence. In a bank's tool registry, description quality is therefore a reviewable, testable artifact, not a nice-to-have.

**Q2: What happens if the model picks the wrong tool, or calls the right tool with a bad or hallucinated argument?**

The harness's validate-authorize-execute pipeline is the first line of defense — enums and constrained types (channel: "pos"|"online"|"atm"|"all" rather than a free string) reject a malformed argument before anything executes. Wrong-tool selection itself is usually traceable to ambiguous or overlapping descriptions, or simply too many active tools crowding the decision (selection accuracy measurably degrades as the toolset grows) — so the fix is narrowing the grant or sharpening the docs, not patching after the fact. On the result side, a well-designed error is written as an instruction a capable reader can act on — "date_to before date_from — swap the arguments and retry" — which recovers in one turn, versus a raw stack trace that burns two or three. This is exactly what the chapter's lab measures directly: run 30 tasks against lazy vs crafted tool descriptions and track wrong-tool selection and argument-error rates as numbers, not impressions.

**Q3: Walk through what happens downstream when a tool returns a raw, unshaped result instead of a designed one.**

A tool result is the next thing the model reasons over, so an unshaped 200-row transaction dump forces the model to do compression work it should never have had to do — versus a result pre-shaped into stats, a few representative samples, and a row count, which hands the model exactly what it needs to decide the next step. If a mutating tool's partial success isn't stated explicitly — "wrote 8 of 10, failed ids: [...]" — the model has no signal that anything went wrong and will proceed as though the operation fully completed, which in a case-management flow could mean a dispute case gets marked resolved when two of its updates actually failed. The chapter's lab is built to make this visible: break a result deliberately (raw vs shaped) on an otherwise-identical tool and watch downstream reasoning quality drop in the transcript. That's the practical argument for treating result design as half the tool-design problem, not an afterthought once the schema is done.

**Q4: What are the cost trade-offs of granting an agent a wide tool surface versus a narrow one?**

Every declared tool schema rides in every single call to the model, so a large toolset is a direct, recurring line item against the context budget — tokens spent on schemas the current task doesn't need are tokens not spent on the task itself. The behavioral cost compounds the financial one: selection accuracy degrades as the number of active tools grows, so a wide grant doesn't just cost more per call, it makes the agent measurably worse at picking the right tool. The architect's answer is rarely "add tools" — it's to group tools by task intent, keep the active set small per agent, and if an agent genuinely needs 40 tools, split it into several agents along permission boundaries instead, or load tools dynamically per phase so the full schema library never sits in context at once.

**Q5: What data security risks arise specifically from tool results entering the model's context?**

Once a tool result lands in context it becomes input the model reasons over on the next turn, exactly like any other untrusted content — a fetched document, a customer's free-text complaint, or a query result can carry instructions or sensitive data the model wasn't meant to see or act on. For a bank this means the audit and log pipeline that captures tool arguments and results for every call must mask PII before it's written down, because "what did the agent read and send" is the question a regulator asks first. It also means the registry's entitlement mapping — which agent, user, or purpose may call a given tool — is a data-security control, not just an access-control one: a tool that can pull core-banking data has effectively decided what sensitive data can enter that agent's context at all. Treat any tool whose result could carry both private data and instructable content as a heightened-review case, the same combination that makes prompt injection dangerous.

**Q6: Beyond schema validation, what guardrails should sit around actual tool execution?**

The read-only / mutating / irreversible annotation on every tool is the load-bearing guardrail — the harness turns that annotation directly into policy, so a mutating tool can carry a confirmation step and an irreversible one (like `send_notification` in the chapter's six-tool lab) routes to human-in-the-loop before it fires. Idempotency matters here too: retries on redelivery are only safe for tools marked idempotent, so a non-idempotent mutating call needs its own dedupe or confirmation logic rather than a blind retry. At the output boundary, structured-output validation with one bounded repair pass and a fail-closed default prevents a malformed final answer from silently propagating into a downstream system. And for skills specifically, bundled scripts must execute inside the sandbox with only the agent's own existing grants — a skill can make the agent better at a job, never wider in what it's allowed to do.

**Q7: How do you apply least-privilege thinking to tool grants for a banking agent, concretely?**

Treat every tool exactly like an API product: named owner, version, an entitlement mapping stating which agent, user, or purpose may call it, a rate class, and audit logging of both arguments and results with PII masked in the pipeline. That registry is the artifact that makes least privilege real rather than aspirational — it's the first thing a risk or audit function asks for, because it's the bank's actual inventory of what agents can do, not a policy document describing what they're supposed to be able to do. Practically, this pushes toward narrow, task-scoped agents rather than one broad agent holding every tool — splitting along permission boundaries (a collections agent doesn't need the KYC-onboarding tools) shrinks blast radius on compromise and improves tool-selection accuracy as a side effect, since a smaller relevant toolset is easier for the model to reason over correctly.

**Q8: How do you manage tool schemas and Agent Skills through a production lifecycle — versioning, evals, drift?**

Generate schemas from typed code — Pydantic or Zod models — so the declared interface and the actual implementation cannot silently drift apart, and track tool-use quality as its own standing eval suite: selection accuracy, argument validity, and recovery rate, run the same way any other regression suite runs. Skills get the identical discipline because a skill is a prompt with privileges — git-versioned, code-reviewed, released with explicit version pins, and any change to a skill goes through the same eval gate as a changed prompt before it ships. In production, which tool version and which skill version (e.g., "collections-comms v2.3") executed in a given run needs to be recoverable from the trace, because "why did the agent write that letter" has to be answerable with a specific, versioned artifact, not "the model decided to."

**Q9: Design the tool-versus-skill boundary for a collections/dispute-handling agent at a bank.**

Apply the chapter's rule directly — MCP tools for anything that touches a live system (query the core banking platform for account status, `create_case` to open a dispute, `send_notification` to reach the customer), and a skill for the procedural know-how: an RBI-compliant tone, an escalation checklist, and the bank's approved letter templates, bundled as a `collections-comms` skill the agent loads only when the task matches. The two compose rather than substitute for each other — the skill teaches when and how to use the CRM tools correctly, which is a better design than stuffing that same usage guidance into every tool's description. `send_notification` stays annotated irreversible, so an actual customer-facing letter routes through a confirmation or human-in-the-loop step before it sends, while the skill itself only enters the agent's toolkit after it clears the curated internal skills registry with a named owner and pinned provenance.

**Q10: What do "excessive agency" and "tool poisoning" mean in agent security, and how does a tool/skill registry defend against them?**

Excessive agency is an agent holding more capability than a given task needs, so a single bad turn — a hallucinated argument, an injected instruction from a tool result — can do damage well beyond the task's actual scope; it's the direct argument for the chapter's narrow-tools-per-agent stance rather than one agent with every capability. Tool poisoning is the supply-chain version of the same risk: a malicious or subtly altered tool or skill description that steers the model into calling it when it shouldn't, or a skill's bundled script carrying a payload that runs with whatever the agent is entitled to. The defense is the same registry discipline the chapter already prescribes for tools — allowlist-only, review before availability, a named owner, and pinned provenance (hash or signature) — extended explicitly to skills, since a skill's script is code that executes, not just text the model reads.

**Q11: An agent's toolset has grown past 40 tools and selection accuracy has dropped — how do you diagnose and fix it?**

The first suspect is the toolset size itself, not the model — selection accuracy degrades measurably as the number of active tools grows, so before reaching for a stronger model, check whether this agent is really several agents wearing one hat. The chapter's fix is to split by task intent along permission boundaries — a 40-tool agent is "usually several agents" — and, where the full set genuinely needs to stay together, load tools dynamically per phase so the model only ever sees the schemas relevant to where it is in the task. Confirm the fix the same way you'd confirm any regression fix: rerun a selection-accuracy eval (the chapter's lazy-vs-crafted-description, 30-task pattern generalizes directly to lazy-vs-scoped toolset) before and after, rather than assuming a smaller list helped.

**Q12: Why constrain an agent's final output to a typed schema instead of letting it answer in prose?**

Structured output at the boundary uses the identical machinery as tool-call schemas, pointed at the final answer instead of an intermediate action, so downstream systems can consume types directly rather than parsing free text — a typed case-closure object a case-management system ingests as-is, instead of a paragraph a second process has to interpret. The discipline is the same as any tool boundary: validate against the schema, allow exactly one repair pass fed the validation error if it fails, and fail closed rather than pass through something malformed. This is precisely what makes an agent composable with ordinary bank software rather than a chatbot bolted awkwardly onto a workflow — the contract at the boundary is a schema, not a hope that the prose parses.
