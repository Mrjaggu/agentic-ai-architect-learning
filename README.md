# Agentic AI Architect

A complete, architect-level curriculum for designing **enterprise agentic AI systems** — written from the perspective of building an agent platform for a regulated bank.

Not another framework tutorial. Every chapter asks the questions an architect must answer: who owns control flow, what are the trade-offs, how does it fail, how is it governed, and what does a risk review ask.

## What's inside

| Section | Files |
|---|---|
| Curriculum index & progress tracker | `00-CURRICULUM.md` |
| **A — Foundations & Agent Design** | `ch01`–`ch03`: evolution of AI systems, agent anatomy & reasoning, design patterns |
| **B — Orchestration, Harness & Backend** | `ch04`–`ch09`: graphs & state machines, harness engineering, backend system design, IaC/CI-CD deployment, context engineering, memory architecture |
| **C — Knowledge Architecture** | `ch10`–`ch12`: enterprise RAG, knowledge graphs & Graph RAG, agentic retrieval & knowledge routing |
| **D — Tools, Skills, MCP & Multi-Agent** | `ch13`–`ch15`: tools & Agent Skills, MCP/A2A protocol stack, multi-agent systems |
| **E — Production AI** | `ch16`–`ch18`: observability, evals, reliability & cost engineering |
| **F — Governance, Security & Platform** | `ch19`–`ch21`: security & guardrails, autonomy & HITL governance (incl. RBI FREE-AI mapping), the enterprise reference architecture |
| **G — The Architect's Toolkit** | `ch24`–`ch28`: model strategy & multi-model architecture, how agentic systems fail, distributed agent systems, architecture decision frameworks (+ pattern gallery), the 2026 ecosystem landscape |
| Interview Q&A bank | `ch22-interview-qa.md` — real questions with 30-second answers |
| End-to-end case studies | `ch23-case-study.md` — a system-design interview walkthrough, a documented industry full-stack case, plus dedicated Banking Operations Agent and Research Agent cases |
| Browser reader | `Agentic-AI-Reader.html` — open locally; all chapters with prev/next navigation, offline |

## How each chapter is written

Concept → why the industry needed it → architecture (with diagrams and code snippets) → design decisions → trade-offs → industry implementation → hands-on lab → **architect's take for a regulated bank** → **governance & security lens** → interview-ready lines → a full **Interview Questions & Answers** section, researched and dimension-spanning (why / what-if / what-after / cost / data security / guardrails / access control / deployment / scenario-based).

Governance and security are asked in *every* chapter, not parked at the end — because a design that scales but can't be governed doesn't ship.

## Status

Living document. Module A (ch1–3) is at full depth; remaining modules are dense v1 drafts being expanded module by module. Lab code will land in `labs/`.

## Author

Ajay — AVP, working on production AI in regulated financial services.
