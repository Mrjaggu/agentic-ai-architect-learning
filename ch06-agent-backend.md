# Chapter 6: Backend & System Design for Agent Services

> A web app answers in milliseconds. An agent thinks for minutes. That one difference drives the entire backend design.

*Source: Karan Shingde, "Designing the Backend for Agent Systems (Part 2)," AI That Ships.*

## 1. The anti-pattern everyone writes first

```python
@app.post("/agent")
def run(req: Request):
    return agent.run(req.prompt)   # DO NOT ship this
```

Six ways it fails, worth memorizing because each maps to a component of the fix:

1. Holds a connection open for 90–120s (browsers and load balancers time out)
2. Client disconnect = job lost
3. Network retry = the whole expensive run re-executes
4. User sees a spinner with zero information
5. No way to cancel mid-run
6. Failure at step 9 of 10 loses everything

## 2. The workload properties that drive the design

Agent workloads are **long-running, asynchronous, iterative, and expensive to retry**. Therefore: split the fast path from the slow path.

```text
Client ──► API (fast: validate, enqueue, return job_id)
                 │
                 ▼
              QUEUE
                 │
                 ▼
             WORKER (slow: runs the agent loop)
                 │
     progress events ──► stream to client
                 │
                 ▼
        results + state store
```

## 3. The components

- **Submission API** — `POST /jobs` returns a `job_id` in milliseconds. Idempotency keys so a retried submit doesn't create duplicate expensive runs.
- **Queue** (Redis/SQS/RabbitMQ) — decouples acceptance from execution; absorbs bursts; enables priority tiers and per-tenant fairness.
- **Worker pool** — consumes jobs, runs the harness (Ch5) and graph (Ch4). Scales independently of the API. Holds entire agent runs in memory — size it ~2x the API (Ch7).
- **Progress streaming** — SSE (simpler, one-way, usually right) or WebSockets (bidirectional, needed only if the user talks back mid-run). Stream *events* (step started, tool called, tokens) not just final output — this is the spinner fix.
- **State & results store** — Postgres for jobs/results/sessions; checkpoints (Ch4) make failure at step 9 resume at step 9.
- **Cancellation** — a flag the worker checks between nodes; graphs make this clean (finish current node, stop at the edge).
- **Session management** — conversations span jobs; session state lives in the store, never in worker memory.
- **Rate limiting & cost control** — per-user job quotas, per-run token budgets, queue-depth backpressure. An agent endpoint without rate limits is a blank check.

## 3b. The fix, visualized (~15 lines)

```python
@app.post("/jobs")                                    # FAST PATH: milliseconds
async def submit(req: JobRequest, idem_key: str = Header(...)):
    if existing := await store.by_idempotency(idem_key):
        return existing                               # retried submit ≠ second run
    job = await store.create(req, status="queued")
    await queue.push(job.id)
    return {"job_id": job.id}

@app.get("/jobs/{id}/events")                         # progress, not spinners
async def events(id: str):
    return EventSourceResponse(store.stream_events(id))   # SSE

# worker.py — SLOW PATH, separate process, no HTTP anywhere
while True:
    job_id = queue.pop()
    run_graph(job_id, checkpointer=saver)             # crash → resume at last node
```

## 4. Design decisions

- **Sync façade where products need it**: you can still offer "wait up to 30s then return or hand back job_id" — but built *on* the async core, never instead of it.
- **Structured outputs at the boundary**: workers persist typed results (validated JSON), not prose; downstream systems consume the type, and the UI renders from it.
- **One image, two commands**: API and worker run the same container image with different entrypoints, so they can never run different code (this becomes a deploy invariant in Ch7).
- **Queue semantics**: at-least-once delivery + idempotent job handling beats exactly-once promises. Design the job, not the queue, for redelivery.

## 5. Trade-offs

The async architecture costs you: more moving parts, eventual consistency in UX ("queued… running…"), and an operational surface (queue depth, worker health). It buys you: survivable disconnects, resumable failures, backpressure, cancellation, and honest progress. For anything beyond a demo, the trade is not close.

## 6. Industry implementation

This is the shape underneath every serious agent product: ChatGPT-style deep research, coding agents, document processors — all job-queue-worker with streamed progress. FastAPI + Celery/RQ + Redis + Postgres is the common self-hosted stack; managed equivalents (SQS + ECS workers) appear in Ch7. LangGraph Platform and similar sell exactly this layer — evaluate them as "backend-in-a-box" against building it.

## 7. Hands-on lab

Convert your Ch4 graph into a service: FastAPI submission endpoint (idempotency key), Redis queue, a worker process running the graph with checkpoints, SSE progress streaming, `DELETE /jobs/{id}` for cancellation, and a per-user limit of 3 concurrent jobs. Kill the worker mid-job; prove the job resumes. Disconnect the client mid-stream; prove the job finishes anyway.

## 8. Architect's take: the banking read

Bank infrastructure reviews will ask exactly these questions — timeout behavior, retry semantics, idempotency, backpressure, DR — because they're the same questions asked of any transaction system. Answering them fluently for agents is how you establish that agentic AI is an engineering discipline, not an experiment. Extra banking notes: idempotency is non-negotiable where a duplicated job could duplicate a customer action; per-tenant fairness matters when one branch's batch upload must not starve the contact center; and the queue is an audit point — every job's submission, ownership, and outcome is a record.

## Governance & security lens

The job system is an audit and safety layer, not just plumbing: every job records who submitted it, under what identity, with what outcome — the queue is a ledger. Idempotency keys are a *customer-protection* control (a network retry must never duplicate a real-world action); per-tenant quotas and backpressure are availability controls; cancellation is the operational kill lever for a single run. Governing questions: **can we reconstruct any job end-to-end from records, are all payloads encrypted in transit and at rest, and does a replayed message ever cause a second side effect?**

## Interview-ready lines

- "Agent workloads are long, async, iterative, and expensive to retry — so split the fast path from the slow path."
- "Return a job_id in milliseconds; stream events, not spinners."
- "At-least-once delivery plus idempotent jobs beats exactly-once promises."
- "The API accepts, the queue absorbs, the worker thinks, the store remembers."
