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
