# Chapter 14: MCP, A2A & the Agent Protocol Stack

> Before protocols: N agents × M systems = N×M custom integrations. After: N + M. That arithmetic is the entire reason this chapter exists.

## 1. MCP — the tool-side standard

The Model Context Protocol standardizes how an agent host connects to capability providers:

```text
HOST (agent app) ──► MCP CLIENT ──► MCP SERVER ──► actual system
                       (1 per server)   exposes:
                                        - tools      (actions)
                                        - resources  (readable data)
                                        - prompts    (reusable templates)
```

Key properties an architect should be able to state: servers *declare* their capabilities (discovery at connect time, no hardcoding); the same server serves any MCP-capable host (write the core-banking server once; every agent platform uses it); transports are local (stdio) or remote (HTTP/SSE); auth on remote servers rides OAuth-style flows. MCP won the tool-integration layer in 2025–26 — it is infrastructure now, not a bet.

## 2. The enterprise pattern: the MCP gateway

Direct agent→server sprawl recreates the mess with extra steps. The deployable pattern:

```text
Agent platform ──► MCP GATEWAY ──► CRM │ Core banking │ Data platform
                     │
                     ├─ authN (which agent, on behalf of which user?)
                     ├─ authZ (entitlement check per tool call)
                     ├─ policy (rate, budget, data classification)
                     └─ audit (every call, argument-masked, logged)
```

The gateway is where Ch13's "tool as capability grant" gets enforced platform-wide: one choke point for identity propagation (the *user's* entitlements travel with the call — the agent must not be a super-user), one audit stream, one place to kill a misbehaving integration. This is the single most defensible piece of enterprise agent architecture you can put on a whiteboard.

## 2b. A minimal MCP server, visualized

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("core-banking")

@mcp.tool()
def get_account_balance(account_id: str) -> dict:
    """Current balance and status for one account."""
    return core_banking_api.balance(account_id)     # write once...

@mcp.resource("policy://cards/{product}")
def card_policy(product: str) -> str:
    return policy_store.latest(product)

mcp.run()   # ...every MCP-capable host (any agent platform) can now use it
```

The gateway (below) is what stands between this server and production.

## 3. A2A — the agent-side standard

Where MCP connects agents to *systems*, A2A (Agent2Agent, now a Linux Foundation project) connects agents to *agents* — including across vendors and organizations. Core concepts: an **Agent Card** (a discoverable manifest of identity, capabilities, endpoints, auth requirements), **tasks** with lifecycle (submitted → working → input-required → completed/failed — note the same async job shape as Ch6), and message/artifact exchange, with agents remaining *opaque* to each other (no shared memory or internal state — a security feature, not a limitation).

The architect's mapping: **MCP = vertical** (agent↔capability), **A2A = horizontal** (agent↔agent). They compose: your loan agent uses MCP to reach the LOS, and A2A to answer a query from a partner's procurement agent.

## 4. The rest of the 2026 stack — signal vs noise

Worth tracking: **AG-UI / A2UI** (standardizing agent↔user-interface event streams — the Ch6 progress-streaming problem, standardized), **WebMCP** (websites exposing MCP endpoints so agents use sites without scraping), and payment-oriented protocols (agentic commerce). Historical/merging: ACP, ANP. The architect's posture: adopt MCP now; design A2A-*ready* (your agents already have clean task lifecycles if you built Ch6 properly); track the rest without coupling to them. Protocol churn is real — depend on shapes (discovery, task lifecycle, capability manifest), which are stable, not on specific specs' details.

## 5. Trade-offs

Standards trade expressiveness for interoperability — MCP tools are a lowest-common-denominator interface, and some rich integrations still justify native APIs internally (expose them *through* an MCP façade anyway for uniform governance). A2A's opacity means trust must be established at the identity/contract level, not by inspecting the other agent — which is exactly how inter-organization integration already works, and why banks will be comfortable with it eventually, and slowly.

## 6. Industry implementation

MCP server ecosystems now exist for most major SaaS; enterprises are converging on registry + gateway (an internal catalog of approved MCP servers with owners and entitlements). A2A adoption is early-majority in 2026 with big-vendor backing; the realistic near-term enterprise use is *internal* agent-to-agent (across departmental platforms) before cross-organization.

## 7. Hands-on lab

Build an MCP server for the mock core-banking API from Ch13 (tools + a couple of resources). Connect it to two different hosts to feel the write-once property. Then build a minimal gateway: a proxy that authenticates the calling agent, checks a static entitlement table per tool, enforces a rate limit, and writes an audit line per call. Finally, write A2A Agent Cards (paper design is fine) for your loan/account/card agents and specify which cross-agent tasks they'd accept.

## 8. Architect's take: the banking read

For a bank, MCP's win is *governance uniformity*: every system an agent can touch goes through one protocol, one gateway, one audit format — auditors get a single answer to "how do agents access systems?" The gateway is also where RBI-style requirements land naturally (access logging, purpose limitation, kill switch per integration — Ch20). Treat A2A as the future shape of bank↔fintech-partner integration and design your task lifecycles to be A2A-compatible, but let identity and liability frameworks mature before crossing organizational boundaries with it.

## Governance & security lens

The gateway is the single governed choke point — authN (which agent, on behalf of whom), authZ per tool call, rate/budget policy, and one audit stream — and that consolidation is the whole enterprise argument for MCP. Third-party MCP servers are *supply chain*: vet them like dependencies (tool descriptions are an injection vector; a server sees every argument you send it), pin versions, and prefer an internal registry of approved servers. A2A adds inter-organizational trust: agent identity verification, contract-level trust, and liability boundaries before any cross-org autonomy. Governing question: **can any agent reach any system except through the gateway — and if a server misbehaves, how fast can one integration be killed without killing the platform?**

## Interview-ready lines

- "MCP turns N×M integrations into N+M — and the gateway turns N+M into one governed choke point."
- "MCP is vertical (agent↔system); A2A is horizontal (agent↔agent); they compose."
- "The agent must not be a super-user: user entitlements travel with every tool call through the gateway."
- "Depend on protocol shapes — discovery, task lifecycle, capability manifests — not on spec details."
