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


## Interview Questions & Answers

**Q1: Why would a bank invest in a standard like MCP instead of just having each agent call the APIs it needs directly?**

Direct integration is N agents × M systems worth of bespoke glue code, and every new agent or every new system multiplies that count again — this chapter opens on that arithmetic for a reason. MCP turns it into N+M: you write the core-banking MCP server once (tools, resources, prompts) and every MCP-capable agent host can use it, the same way the FastMCP example exposes `get_account_balance` once and any host connects to it. The bigger win for a regulated bank isn't the coding time saved, it's governance uniformity — one protocol, one gateway, one audit format means auditors get a single answer to "how do agents reach systems?" instead of N×M different answers. Point-to-point integrations don't disappear entirely — some rich integrations still justify native APIs internally — but even those get fronted with an MCP façade so governance stays uniform.

**Q2: Walk me through what actually happens when an agent host connects to a new MCP server for the first time.**

The host's MCP client opens a session with the server — over stdio if it's local, over HTTP/SSE with OAuth-style auth if it's remote — and the server declares its capabilities at connect time rather than the host hardcoding what it expects. That declaration covers three categories: tools (actions the agent can invoke, like `get_account_balance`), resources (readable data, like a `policy://cards/{product}` lookup), and prompts (reusable templates). Because discovery happens dynamically at connect time, the same server can serve any MCP-capable host without either side needing prior knowledge of the other's internals. In a bank, that connection shouldn't be direct in production — it should terminate at the gateway, which authenticates the calling agent, checks entitlements per tool, and logs the exchange before anything reaches core banking.

**Q3: Suppose a third-party MCP server you've integrated turns out to be malicious or gets compromised after deployment — what's actually at risk?**

The server sees every argument you send it, not just the response it returns, so a compromised card-policy or collections server could be harvesting account IDs, balances, or customer PII passed as tool arguments even while returning perfectly correct-looking results. Tool descriptions themselves are an injection vector — a poisoned description can steer the calling model into unintended actions or into leaking context from earlier in the conversation. This is why the chapter treats MCP servers as supply chain, not as trusted internal code: you vet them like dependencies, pin versions, and prefer an internal registry of approved servers over ad hoc connections. Detection comes from the gateway's audit stream, since every call is logged with arguments masked by classification; if a server starts requesting scopes or data shapes it never asked for before, that's the signal to pull it via the kill switch without taking down the rest of the platform.

**Q4: An MCP server your loan agent depends on silently changes a tool's description or schema after you already approved and registered it — what happens next?**

This is the "rug pull" risk of dynamic capability discovery: because servers declare capabilities at connect time rather than the host hardcoding them, a server is technically free to change what a tool does or how it's described between sessions, and a naive host would just accept the new definition. The fix has to live in the registry and gateway layer, not in trust of the server: pin the exact approved version per server in the internal catalog, and treat any schema or description drift as a change requiring re-vetting, not an automatic pass-through. Practically, the gateway should diff incoming capability manifests against the registered version, alert on mismatch, and refuse the call rather than silently honoring the new definition. That's also where the kill switch earns its keep — one integration gets frozen and investigated while every other agent-to-system path on the gateway keeps running.

**Q5: What are the real cost trade-offs of running an MCP gateway layer versus just letting agents hit banking APIs directly?**

Direct integration looks cheaper on day one — no gateway to build, no registry to maintain — but that cost curve is N×M and gets worse with every agent or system you add, whereas the gateway's cost curve is closer to N+M once it exists. The gateway itself isn't free: you're standing up authN, per-tool authZ, rate/budget policy, and an audit pipeline as permanent infrastructure, plus the ongoing operational cost of vetting and version-pinning every server in the registry. Where it pays off is in incident cost and audit cost — one choke point to investigate, one place to kill a misbehaving integration, one audit format instead of reconciling logs across dozens of bespoke connections when a regulator asks how agents access systems. The trade-off isn't MCP-versus-nothing, either — some integrations are rich enough to justify a native API underneath, but you still pay to wrap it in an MCP façade so it doesn't become a governance blind spot.

**Q6: A vendor's MCP server — say, for a credit bureau pull or a collections platform — has tool access into your systems. What data security exposure does that actually create?**

The exposure isn't just "the vendor can read what the tool returns" — it's that the vendor's server sees every argument the agent sends it, including account identifiers or customer detail that may not even be strictly needed for that call. That makes it a data security problem even when the response the agent gets back is clean and well-scoped. The gateway's job is to bound that exposure by data classification and by entitlement: the vendor server should only be authorized for the specific tools it needs, argument logging should be masked at the classification level in the audit stream, and the user's own entitlements — not a blanket agent credential — should be what's checked on every call, so the agent is never acting as a super-user on the vendor's behalf. Practically this means the vendor server sits in the registry with an explicit, narrow scope, not a general-purpose connection to core banking.

**Q7: How do you vet and sandbox an MCP server before it's allowed anywhere near production banking data?**

Vetting starts before connection: the server goes into an internal registry with a named owner, an explicit entitlement scope, and a pinned version, and its tool descriptions get reviewed the way you'd review a new dependency's source — because a malicious description is itself an injection vector, not just a malicious tool implementation. Sandboxing depends on transport: a local stdio server runs in an isolated process or container with no direct network egress, while a remote HTTP/SSE server sits behind the gateway's OAuth-style auth and never gets a direct line to core systems. Rate and budget policy at the gateway limits blast radius even for an approved server that starts behaving unexpectedly, and every call still gets logged to the shared audit stream regardless of how trusted the server was at approval time. None of this is a one-time gate — versions get re-vetted on change, which is the same discipline that catches a rug-pull scenario.

**Q8: How does least-privilege access control actually work for MCP tool calls and for A2A messages between agents — is the agent itself the identity that gets checked?**

No — and that's the point the chapter is explicit about: the agent must not be a super-user, so it's the *user's* entitlements that travel with every tool call through the gateway, checked per tool at the authZ layer, not a blanket credential the agent holds on its own. On the MCP side, that means a server like the core-banking one should expose narrowly scoped tools — a read-only balance lookup is a different entitlement than anything that can move money — and the gateway enforces that boundary call by call. On the A2A side, agents stay opaque to each other by design — no shared memory or internal state — so trust has to be established at the identity and contract level via the Agent Card rather than by one agent inspecting another's internals, and any cross-agent task still needs the originating user's entitlement to propagate with it rather than being laundered through the receiving agent's own permissions.

**Q9: How do you handle MCP server versioning and discovery in production without breaking every agent that depends on a given server?**

Because capability discovery happens at connect time, a host will pick up whatever the server currently declares — which is convenient for adding capabilities but dangerous for silently changing or removing them, so production discipline means pinning an approved version per server in the internal registry rather than always resolving to "latest." Roll out a new server version the way you'd roll out any shared dependency: stage it, let a subset of agent traffic exercise it, and watch the gateway's audit stream for behavior or entitlement drift before promoting it broadly. Backward-incompatible changes to a tool's schema or description should be treated as a new registration requiring re-approval, not an in-place update, precisely because that's the same mechanism a compromised or rug-pulled server would exploit. The kill switch is the production safety valve either way — one server version gets pulled and traffic falls back or fails closed, without the rest of the gateway's integrations going down with it.

**Q10: Design the protocol architecture for a bank's loan-servicing agent that needs to pull data from three internal systems and also answer a query from a fintech partner's procurement agent.**

For the internal side, the loan agent talks to the loan-origination system, core banking, and the collateral system each through its own MCP server, all routed through the gateway so the same authN, per-tool authZ, rate/budget policy, and audit stream apply regardless of which internal system is being touched — this is MCP used vertically, agent to system. For the partner query, that's a horizontal, agent-to-agent relationship, so it goes over A2A: the loan agent publishes an Agent Card describing what it can accept, the partner's procurement agent submits a task, and the exchange follows the same submitted → working → input-required → completed lifecycle this course already builds agents around. The two agents stay opaque to each other by design — the partner's agent never sees the loan agent's internal MCP calls or state — so trust with the partner is established at the identity and contract level before any task is accepted, not by inspecting how the loan agent actually works internally. Given that this is a cross-organizational A2A relationship, the architect's honest answer is to design the task lifecycle to be A2A-ready now while keeping actual production autonomy narrow until identity and liability frameworks with that specific partner are mature enough to trust.

**Q11: What's the actual difference between MCP and A2A, and why would an architecture need both instead of picking one?**

MCP is the vertical protocol — it connects an agent to capability providers: systems, tools, resources, and prompts, with the agent host holding one MCP client per server. A2A is the horizontal protocol — it connects agents to other agents, including across vendors and organizations, using an Agent Card for discoverable identity and capabilities and a task lifecycle for the actual exchange, with the two agents remaining opaque to each other rather than sharing memory or internal state. You need both because they solve different problems: a loan agent uses MCP to reach the loan-origination system it's built on top of, and separately uses A2A to answer a task submitted by a partner's procurement agent — swapping one for the other doesn't work, since MCP has no concept of agent-to-agent task lifecycle and A2A has no concept of a tool/resource/prompt capability manifest for a backend system. The two compose cleanly precisely because they're addressing orthogonal axes of the same integration problem, not competing for the same layer.

**Q12: When would you choose a local stdio transport for an MCP server versus a remote HTTP/SSE one, and what changes about authentication when you do?**

Stdio fits a server that runs on the same machine or process boundary as the host — low latency, no network exposure, and typically no separate auth handshake needed because the operating system's process boundary is doing the isolation. Remote HTTP/SSE is what you need the moment the server is meant to be shared — hosted centrally and reused by multiple agent platforms or multiple teams — which is exactly the "write once, any host uses it" property that makes MCP worth adopting for something like a core-banking server. That shift to remote also means auth stops being implicit: remote servers ride OAuth-style flows, and in a bank that connection should terminate at the gateway rather than going host-to-server directly, so authN, per-tool authZ, and the audit stream apply the same way regardless of which internal team's host is calling in. The practical rule is that anything crossing a trust boundary — team, department, or organization — belongs on the remote path through the gateway, and stdio stays reserved for genuinely local, single-host use.
