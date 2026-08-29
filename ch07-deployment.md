# Chapter 7: Deploying Agent Systems — IaC, CI/CD & Cloud Runtime

> A green pipeline is not proof. Nothing before a real job ever calls the model.

*Source: Karan Shingde, "Deployment of Agent Systems to AWS ECS (Part 3)," AI That Ships.*

## 1. The deployment shape

The Ch6 fast-path/slow-path split, made physical — three containers on ECS/Fargate behind a load balancer:

```text
Internet ──► ALB ──► frontend (UI, forwards /api/*)
                        │
                        ▼
                       api  (accepts, enqueues)
                        │
                     queue (Redis/ElastiCache)
                        │
                        ▼
                     worker (runs the agent)
                        │
              Postgres (RDS) · Secrets Manager · Bedrock
```

Three properties of this shape matter more than any AWS detail:

- **Only the frontend is internet-reachable.** The worker has *no address at all* — no load balancer, no health check. It only pulls from the queue. Slow work sits nowhere near the request path, so a two-minute job cannot time out a web request.
- **API and worker run the same image** with different start commands — the worker can never run different code than the API.
- **No model API key exists anywhere.** The worker calls the model service (Bedrock) using an identity attached to the container itself.
- Sizing: worker ≈ 2× the API's CPU/memory — the API holds a request for milliseconds; the worker holds an entire agent run for the life of the job.

## 2. Infrastructure as Code: Terraform with workspaces

One folder of ~15 single-purpose files (network, security, ecr, rds, iam, ecs, alb, logs, monitoring…), **never copied per environment**. Workspaces produce isolated dev and prod stacks from identical code:

```hcl
locals {
  name_prefix = "${var.stack}-${terraform.workspace}"
  workspace_config = {
    dev  = { db_instance_class = "db.t4g.micro", log_retention_days = 7 }
    prod = { db_instance_class = "db.t4g.micro", log_retention_days = 30 }
  }
}
```

The only difference between environments is that small table. States live separately (`env:/dev/`, `env:/prod/`), so destroying dev cannot touch prod. Two copied folders drift apart, and the drift is always discovered during an incident.

Remote state (S3) + a lock (DynamoDB) let laptop and CI see the same picture. A **run-once bootstrap** (state bucket, lock table, GitHub OIDC provider, deploy role) is the only hand-created infrastructure; everything after happens on `git push`. Teardown order is sacred: environments first, foundations second — delete the state bucket early and Terraform forgets what it made while the resources keep billing.

## 3. CI/CD: OIDC, gates, and the identity trap

**No cloud password exists anywhere.** GitHub Actions gets an hourly credential by presenting a signed token ("this is repo X, environment Y") that AWS checks against the deploy role's trust rules — OIDC. The trap that costs an afternoon: a job with `environment: dev` presents subject `environment:dev`, a job without presents `ref:refs/heads/main` — *one commit, two identities*, and the role must trust both. Untestable locally; the only symptom is `Not authorized to perform sts:AssumeRoleWithWebIdentity`.

Pipeline structure: checks on every push/PR (lint, secret scan, terraform validate, unit tests, compose smoke test); deploy only on push, only after checks. Promotion policy in one line: `environment: prod` + a required reviewer = every prod deploy pauses for a human. `main` → dev automatically; a `prod-*` tag → prod with approval. Same commit, same Terraform, only the workspace differs. And never `cancel-in-progress` on deploys — a cancelled Terraform leaves a stuck lock. (Never save the plan as an artifact either: it contains generated secrets in plaintext.)

Two agent-specific CI rules: **don't test what the model says** (non-deterministic → flaky → ignored suite; test the machinery — state transitions, parsing, truncation), and **check SDK imports inside the built image** — agent apps load model libraries lazily, so a missing one survives startup and the health check, then fails on the first real job.

## 4. The two roles — where agent security becomes real

Every container has two identities:

- **Execution role** — AWS's, used *before* your code runs: pull image, create log stream, read secrets. Rule of thumb: failure before the first log line = execution role; look at ECS service events.
- **Task role** — your code's, used *while* it runs: model calls, S3, everything the agent does.

The task role is where agent security actually happens. If a tool should read one S3 folder, grant the task role exactly that folder — then a crafted prompt cannot reach anything else. **Restricting an agent in the prompt is a request. Restricting it in the task role is a fact.** (Generalized in Ch19.)

Secrets: Terraform creates placeholders with `lifecycle { ignore_changes = [secret_string] }` (without it, every deploy resets your real key to REPLACE_ME); real values set once via CLI, never in repo or image.

## 5. Model access & model choice

Workload identity → zero API keys: the SDK finds credentials automatically (local profile on laptop, task role in cloud). Know the Bedrock ID trap: foundation model IDs vs inference profile IDs (`us.` prefix) — permit both forms or get misleading AccessDenied errors; prompt-cache markers on unsupported models also surface as AccessDenied that isn't a permissions problem. And choose models that **converge** in long tool loops: one model passed every quick test, then listed the same directory forty times without moving on — not erroring, just not finishing. Test with a real end-to-end job, never a single call.

## 6. Production wiring: logs → alarms → traces

Built in this order because each depends on the previous:

1. **Structured JSON logs** with job_id — the only way to follow one job across three containers.
2. **Metric filters → alarms → email** on error patterns, plus a budget alarm (80%/100%) because agent stacks spend quietly. The dependency bites: an alarm matching a JSON field your logs don't emit deploys green and can never fire — you learn during the incident it was meant to catch.
3. **Tracing** (Langfuse-class): the decorator gives the outer span; the *callback* fills in model calls, tools, and cost; the explicit flush is mandatory in a background worker or finished jobs' traces sit unsent. Verify by running a real job and seeing the nested trace — unverified tracing is worse than none, because you'll trust it.

**Deployment verification, the five checks:** all services have running tasks; health endpoint returns ok; *one real job end-to-end* (the one people skip, and the only one that calls the model); that job's trace appears; the alarm email subscription is confirmed.

## 6b. The managed alternative: Amazon Bedrock AgentCore

Everything this chapter builds by hand, AWS now sells as managed services — **Bedrock AgentCore** (GA Oct 2025, expanded through 2026). The service list maps almost one-to-one onto this curriculum, which is worth noticing: it means the concepts here are the industry-converged shape, and AgentCore is one vendor's packaging of them.

| AgentCore service | What it replaces | Our chapter |
|---|---|---|
| Runtime (serverless, session-isolated microVMs, long-running async) | The queue/worker/Fargate stack | Ch6–7 |
| Harness (managed agent loop) | Hand-built loop + harness | Ch2, Ch5 |
| Memory (short-term + long-term, cross-session) | DIY memory layer | Ch9 |
| Gateway (APIs/Lambda → MCP tools, auth) | The MCP gateway | Ch14 |
| Identity (agent IAM, IdP federation) | NHI machinery | Ch19 |
| Policy (Cedar rules intercepting tool calls) | Tool policy enforcement | Ch5, Ch19 |
| Observability (OTel traces) / Evaluations | Langfuse-class stack + eval harness | Ch16–17 |
| Registry (agents/MCP/tools catalog) | Tool & agent registry | Ch13–14 |
| Code Interpreter / Browser | Sandboxed execution | Ch5 |

**The architect's build-vs-buy read:** AgentCore compresses months of Ch6–7 work into configuration and is framework-agnostic (LangGraph, CrewAI, LlamaIndex run inside it) — a strong default for teams already on AWS who want scale without platform engineering. The trade-offs to name in a design review: consumption pricing at scale vs owned infrastructure; region availability and data-residency fit (verify against RBI localisation for each service, not just the headline); portability (Gateway/Policy/Registry are AWS-shaped — keep your tool contracts MCP-standard so you can exit); and the newest services (Policy, Optimization, Payments) being young. The mature posture: *learn* the DIY stack (this chapter — it's what makes you able to evaluate AgentCore), *adopt* managed pieces where they clear governance, and keep the invariants (identity not keys, worker isolation, real-job verification) regardless of who runs the servers.

## 7. Hands-on lab

Deploy the Ch6 stack: bootstrap, Terraform apply via GitHub Actions with OIDC, dev on push to main, prod behind a tag + approval. Then break it on purpose: wrong task-role permission (watch the first real job fail while health stays green), missing JSON log field (watch the alarm never fire), cancelled deploy (clear the stuck lock). The breakage is the education.

## 8. Architect's take: the banking read

Every pattern here has a bank-grade name your infra teams already use: OIDC = federated workload identity; task role = least privilege; approval gate = change management; budget alarm = cost governance; teardown order = state management discipline. Presenting agent deployment in this vocabulary — rather than as "AI magic" — is what gets it through a bank's change advisory board. On-prem/private-cloud variants (your world, given data residency): the shape survives intact — swap Fargate for K8s, Bedrock for on-prem serving, Secrets Manager for Vault; the *invariants* (worker unreachable, one image, identity not keys, real-job verification) are the architecture.

## Governance & security lens

This chapter is largely made of controls — name them as such: OIDC = no standing cloud credentials to steal; task roles = least privilege enforced by the platform; approval gates = change management; the plan-never-in-artifacts rule = secrets hygiene; budget alarms = financial control; teardown order = state integrity. Governing questions: **who can assume the deploy role and from which branches/environments, who approves prod, and is every deployment attributable to a commit, a pipeline run, and a person?** Infrastructure-as-code makes the whole answer reviewable — which is *why* IaC is a governance requirement, not a convenience.

## Interview-ready lines

- "The worker has no address — that's the fast/slow split made physical."
- "One commit can present two identities to the cloud; your trust policy must expect both."
- "Restricting an agent in the prompt is a request; in the task role it's a fact."
- "A green pipeline proves nothing about the model path — run one real job."
