# Hi there 👋 I'm Ajay Jangid

### 🚀 AI Architect | GenAI | Agentic AI | Enterprise AI Systems

An **AI Architect** with **7+ years of experience** across Artificial Intelligence, Machine Learning, NLP, Search, and Information Retrieval. Specializing in designing, architecting, and scaling production-grade **Generative AI, Agentic Workflows, and Multi-Agent Systems** for enterprise platforms.

* 🧠 **Core Focus:** Agentic AI Systems, Multi-Agent Orchestration, RAG Architecture, Knowledge Graphs, Model Context Protocol (MCP), and LLM Observability & Evals.
* 🎯 **Mission:** Building deterministic, reliable, and enterprise-ready AI platforms that solve real-world problems.

📫 **Let's Connect:** [LinkedIn](https://www.linkedin.com/in/ajayjangid21/) | [Medium](https://medium.com/@jangidajay271) | [Email](mailto:jangidajay271@gmail.com)

---

📖 **Read the Chapters in the Interactive Reader:**  
👉 **[Click Here to Open the Live Reader on GitHub Pages](https://mrjaggu.github.io/agentic-ai-architect-learning/)**

---

# 📚 Agentic AI Architect Curriculum

Welcome to the **Agentic AI Architect Curriculum**! This repository features a comprehensive, 28-chapter learning program designed to train Enterprise Agentic AI and AI Platform Architects.

---

## 🎯 Positioning Goal
Become an **Enterprise Agentic AI / AI Platform Architect**—someone who designs the complete enterprise ecosystem, not just another framework developer.

Throughout the chapters, we build and refine one evolving design: **"An Enterprise Agentic AI Platform for a Bank."** By the end, you will possess deep conceptual confidence and a robust reference architecture you can defend in technical interviews, leadership discussions, and on LinkedIn.

---

## 🗂️ Repository Structure

```
index.html                # Built reader -- what GitHub Pages serves
Agentic-AI-Reader.html    # Identical copy, for opening locally/offline
chapters/                 # All 28 chapters + the curriculum index (source of truth, plain Markdown)
  00-CURRICULUM.md
  ch01-evolution.md
  ...
  ch28-ecosystem-landscape.md
reader/                   # Build tooling for the interactive reader
  build_reader_v2.py      # python3 reader/build_reader_v2.py regenerates index.html
  reader-base.css
  reader-shell.js
.github/workflows/        # Auto-deploys index.html to GitHub Pages on push to main
```

Read the chapters as plain Markdown right here on GitHub, or open the built reader above for diagrams, search, and progress tracking.

---

## 📚 Curriculum Modules

### 🧱 Module A — Foundations & Agent Design
* **Chapter 1: The Evolution of AI Systems** – GenAI, LLM apps, RAG, and the rise of Agentic Workflows.
* **Chapter 2: Anatomy of an AI Agent** – Reasoning, planning, tool selection, action, observation, and reflection.
* **Chapter 3: Agent Design Patterns** – ReAct, Plan-and-Execute, Reflection, Router, Supervisor, and when NOT to use them.

### ⚙️ Module B — Orchestration, Harness & Backend Systems
* **Chapter 4: Agent Graphs & State Machines** – Nodes, edges, loops, interrupts, and durable execution (LangGraph, CrewAI, OpenAI Agents SDK).
* **Chapter 5: Agent Harness Engineering** – Building reliable scaffolds (context assembly, tool policies, sandboxing, cost control).
* **Chapter 6: Backend & System Design for Agent Services** – Async job submission APIs, streaming (SSE/WebSockets), worker pools, and checkpointing.
* **Chapter 7: Deploying Agent Systems** – Infrastructure as Code (Terraform), CI/CD (GitHub Actions), and secure cloud runtimes (ECS/Fargate).
* **Chapter 8: Context Engineering** – Context selection, token budgets, compression, and sub-agent context isolation.
* **Chapter 9: Memory Architecture** – Short-term, working, episodic, and semantic memory under privacy and security constraints (DPDP/RBI).

### 🧠 Module C — Knowledge Architecture
* **Chapter 10: Enterprise RAG, Properly** – Hybrid search, reranking, metadata filtering, and zero-downtime reindexing.
* **Chapter 11: Knowledge Graphs & Graph RAG** – Entity relationships, graph databases, and combining vector & graph retrieval.
* **Chapter 12: Agentic Retrieval & Knowledge Routing** – Intelligent, self-correcting query planning across multi-hop data sources.

### 🔌 Module D — Tools, MCP & Multi-Agent
* **Chapter 13: Tools, Function Calling & Agent Skills** – Tool schema design, structured outputs, idempotency, and the `SKILL.md` standard.
* **Chapter 14: MCP, A2A & the Agent Protocol Stack** – Model Context Protocol (MCP), agent-to-agent (A2A) integration, and enterprise gateways.
* **Chapter 15: Multi-Agent Systems** – Specialization, collaboration, state management, and framework comparisons.

### 📈 Module E — Production AI
* **Chapter 16: Agent Observability** – Trajectory tracing, token/cost tracking, and OpenTelemetry instrumentation.
* **Chapter 17: Evals** – Outcome vs. trajectory evaluations, LLM-as-judge design, regression gating, and evaluation datasets.
* **Chapter 18: Reliability & Cost Engineering** – Output validation, model routing, caching economics, SRE metrics, and fail-closed circuits.

### 🛡️ Module F — Governance, Security & the Platform
* **Chapter 19: Security & Guardrails** – Prompt injection, tool poisoning, and Non-Human Identity (NHI) governance (OWASP Top 10 for LLMs).
* **Chapter 20: Autonomy Levels, Human-in-the-Loop & Governance** – Human gatekeepers, kill-switches, and risk compliance.
* **Chapter 21: The Enterprise Agentic AI Reference Architecture** – Designing the complete Blueprint for a regulated banking environment.
* **Chapter 22: Interview Q&A Bank** – What leadership and engineering panels actually ask during architect interviews.
* **Chapter 23: End-to-End Case Studies** – Real-world system design interview blueprints and production stacks.

### 🧰 Module G — The Architect's Toolkit
* **Chapter 24: Model Strategy & Multi-Model Architecture** – Model routing, fallback models, small vs. large, cost/latency/quality trade-offs, and data residency.
* **Chapter 25: How Agentic Systems Fail** – A unified failure taxonomy indexing every failure story in the curriculum, plus the mitigation pattern for each.
* **Chapter 26: Distributed Agent Systems** – Event-driven coordination, distributed state, message queues, saga patterns, and eventual consistency across services.
* **Chapter 27: Architecture Decision Frameworks** – Nine "when do I use X vs. Y" decisions, plus a reference-architecture pattern gallery.
* **Chapter 28: The 2026 Agentic AI Ecosystem** – A technology-landscape map, explicitly framed as the fastest-aging chapter in the course.
