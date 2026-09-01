# Chapter 17: Evals

> You can't unit-test a distribution. Evals are how agentic systems get the regression safety that test suites give ordinary software — and they're the biggest missing skill in the market.

## 1. Why testing breaks and evals replace it

Traditional testing assumes `input → expected output`. Agents give you: many valid paths, many valid answers, non-determinism at every step. So CI tests only the machinery (Ch7: state transitions, parsing, truncation — never what the model says), and *quality* is measured statistically over datasets: run N cases, score them, compare against baseline, gate on the delta. An eval is: **dataset + scoring method + baseline + decision rule.** Missing any of the four, you have a demo, not an eval.

## 2. The eval stack for agents

| Layer | Question | Method |
|---|---|---|
| **Outcome** | Did it achieve the goal? | Ground truth where it exists; rubric/judge where it doesn't |
| **Trajectory** | Was the path reasonable? | Expected-step matching, efficiency vs reference, judge-over-trace |
| **Tool use** | Right tool, right args, recovered from errors? | Deterministic checks against tool logs |
| **Routing** | Right source/agent chosen? (Ch12/15) | Labeled classification accuracy — cheapest, highest-leverage |
| **Safety/policy** | Violations, leakage, injection resistance? | Red-team suites, policy classifiers (Ch19) |
| **Efficiency** | Tokens, latency, turns vs budget | Pure telemetry (Ch16) |

Trajectory evals are the agent-specific novelty: a right answer via a wasteful or lucky path is a latent failure — score the path, not just the destination.

## 3. LLM-as-judge, done properly

Where ground truth doesn't exist (most agent outputs), a judge model scores against a rubric. Your Siddhi quality-scoring work *is* this discipline — the transferable rules: **decompose** into narrow binary/scalar criteria (never "rate 1–10 overall"); **calibrate against humans** on a labeled sample and report agreement — an uncalibrated judge is a random-number generator with gravitas; know the biases (position, verbosity, self-preference — judge ≠ generator model family where possible); force **evidence-cited verdicts** (quote the span that justifies the score); and re-calibrate when the judge model changes, because judge drift silently invalidates your history.

## 4. Traces → test suites: the flywheel

The 2026 working method: **production traces are the eval dataset factory.** Every interesting failure in Ch16's traces becomes a case; every HITL correction becomes a labeled example; sample successes keep the set honest. Curate into versioned suites (golden set for regression, hard set for progress, red-team set for safety). This is **eval-driven development**: change a prompt/model/tool → run suites → compare → ship or revert. Config fingerprints (Ch16) tie every score to the exact system version that earned it.

## 4b. An eval case and a decomposed judge, visualized

```python
case = EvalCase(                                   # from a production trace (Ch16)
    input="Customer disputes ₹4,300 POS charge from 12 Aug",
    expected_tools=["get_transactions", "create_case"],   # tool eval: deterministic
    max_turns=6,                                          # trajectory: efficiency
    rubric={                                              # outcome: judge, decomposed
      "identified_txn":   "Did it cite the exact transaction? (yes/no + quote)",
      "correct_category": "Dispute category per policy 4.2? (yes/no + quote)",
      "no_commitments":   "Did it avoid promising refund timelines? (yes/no)",
    })                                             # never "rate 1-10 overall"

run = agent(case.input)
scores = {k: judge(rubric=v, trace=run.trace) for k, v in case.rubric.items()}
gate: pass_rate(suite) >= baseline - 0.02          # statistical, versioned, in CI
```

## 5. Gates and decision rules

- **CI gate**: golden-suite pass rate must not regress > x% (statistical, not single-case — flaky thresholds kill trust; use enough N).
- **Release gate**: hard-suite + safety-suite review before model or prompt upgrades (a model upgrade is a *change*, evals are how you accept it).
- **Production canary**: online evals on sampled live traffic (judge scoring a % of runs) catching drift between releases.

## 6. Trade-offs

Evals cost real money (judge tokens × dataset × every change) — budget them as CI infrastructure, not research. Rubric maintenance is the hidden cost: as the product evolves, stale rubrics measure the wrong thing with great precision. And beware Goodhart: a single blessed metric will be gamed by your own tuning; keep a held-out suite and rotate.

## 7. Industry implementation

Tooling has consolidated around LangSmith, Langfuse, Arize Phoenix, DeepEval, Braintrust — differing mainly in dataset management, judge tooling, and CI integration; all assume the traces→suites flywheel. The maturity marker among teams is not which tool but whether *eval results, not vibes, decide releases* — most teams still ship on vibes, which is precisely why this skill is scarce and senior-signaling.

## 8. Hands-on lab (Portfolio Project 3, completed)

Build the eval layer on your Ch16 traces: 60-case golden suite for the banking agent (outcome + trajectory + tool checks), a calibrated judge (report human-agreement numbers), a CI job that runs the suite on every prompt change and blocks on regression, and one canary eval on sampled runs. Then do the money demo: introduce a plausible "improvement" (a friendlier system prompt) and show the eval suite catching the 8% tool-selection regression it causes. That demo — evals catching what review missed — is the whole argument, live.

## 9. Architect's take: the banking read

Evals are the *evidence layer* for AI governance: RBI-style model risk management asks for documented validation before deployment and monitoring after — your eval suites and canary scores are exactly those artifacts, versioned and reproducible. Frame evals to leadership as "the control that makes model changes auditable," and the budget conversation changes from "testing costs" to "this is how we're allowed to ship." Siddhi already taught you judge calibration at scale; this chapter's work is converting that into the platform-wide discipline — your single strongest differentiator in the market.

## Governance & security lens

Evals are the platform's *evidence factory*: validation-before-deployment and monitoring-after are exactly what model risk management demands, and versioned suites + fingerprinted results are that evidence in reproducible form. Governance of the evals themselves: fairness suites across protected segments for anything touching credit or eligibility; judge calibration documented and re-run on judge changes (an ungoverned judge is an ungoverned control); eval datasets built from production traces inherit the data-handling rules of the traces; and gate thresholds are policy — changed through review, not by the team being gated. Governing question: **when the regulator asks "how do you know this model change was safe?", is the answer a document or a reproducible suite run?**

## Interview-ready lines

- "An eval is dataset + scoring + baseline + decision rule — anything less is a demo."
- "Score the path, not just the destination: right answers via lucky paths are latent failures."
- "An uncalibrated judge is a random-number generator with gravitas."
- "Production traces are the dataset factory; eval-driven development closes the loop."
- "Evals are how a model change becomes an auditable, reversible decision."


## Interview Questions & Answers

**Q1: Why do agentic AI systems need a dedicated evals discipline instead of the unit and integration tests your bank already runs on other software?**

Unit tests assume `input → expected output` — a fixed, checkable answer — while an agent gives you many valid paths and many valid answers, with non-determinism at every LLM call. Ch7-style CI still matters (state transitions, parsing, truncation — the machinery), but it never tells you whether the *answer* was good, because "good" isn't a single expected string anymore. That's why quality has to be measured statistically over a dataset: run N cases, score them against a rubric or ground truth, compare to a baseline, and gate on the delta. An eval is dataset + scoring method + baseline + decision rule — drop any one of those four and what you have is a demo someone ran once before a release, not a control you can point to when a regulator asks how a model change was validated.

**Q2: What if your LLM-as-judge is itself biased or simply wrong — how would you catch that before it silently corrupts your eval history?**

You treat the judge as a model that needs validation like any other: calibrate it against a human-labeled sample and report an explicit agreement number, not a vibe — an uncalibrated judge is a random-number generator with gravitas. Known failure modes to design against are position bias (favoring the first option shown), verbosity bias (rewarding longer answers), and self-preference (a judge scoring outputs from its own model family more favorably) — for the last one, use a judge from a different model family than the generator where possible. Force evidence-cited verdicts, where the judge has to quote the exact span in the trace that justifies its score, so a wrong verdict is at least auditable rather than a bare number. And re-run calibration every time the judge model itself changes — judge drift is invisible in your dashboards but it silently invalidates every score compared against history, so treat a judge upgrade the same way you'd treat a production model upgrade: as a change that needs its own evidence.

**Q3: A prompt change passes your golden suite but a subtle tool-selection regression only shows up two weeks later in production. What's the actual failure, and what happens next?**

The likely root cause is a golden suite that measured outcome but under-covered trajectory — Ch17's own Portfolio Project 3 demo is built around exactly this: a "friendlier" system prompt that looks like a pure improvement but causes an 8% tool-selection regression the outcome-only eyeball review misses and the eval suite catches. If a regression like that reaches production, the correct next step is the canary layer doing its job — online evals sampling live traffic should flag the drift between releases before it compounds, at which point you roll back to the last config fingerprint that passed baseline, add the failing cases to the golden or hard suite as new regression cases, and re-run before the fix ships again. The deeper fix is structural, not a patch to one prompt: it means your trajectory checks (tool logs, not just final answers) weren't in the gating suite, so you widen the suite's coverage rather than just fixing the one case.

**Q4: How do you size an eval suite and decide how often to run it, given that judge tokens cost real money on every case, on every change?**

Evals are CI infrastructure, so they get budgeted like infrastructure, not treated as a research nicety you run when there's time: judge cost scales as tokens × dataset size × frequency of change, so the lever you actually control is dataset design, not judge quality. A 60-case golden suite that's tightly curated from real production traces (Ch16) and decomposed into narrow binary/scalar criteria — never "rate 1-10 overall" — gives you a cheap, high-signal gate that runs on every prompt or tool-schema change; a larger hard suite and red-team safety suite are reserved for release gates before model or prompt upgrades, where the stakes justify the spend. The cost trap to watch for is rubric maintenance: as the product evolves, a stale rubric keeps burning judge tokens to measure the wrong thing with great precision, so rubric review has to be a recurring line item, not a one-time setup cost.

**Q5: Your eval datasets are built from real production traces — for a bank, what does that mean for data security, and how do you handle it?**

Because the traces→suites flywheel pulls eval cases straight out of production (the ₹4,300 POS dispute in Ch17's worked example is exactly this kind of trace), an eval dataset inherits every data-handling obligation the original conversation carried — customer PII, account numbers, dispute details — it isn't a sanitized synthetic set by default. The governance answer is that eval datasets get the same classification and access controls as the production data they're derived from, not a lighter one just because they're "test data": masking or tokenizing account-identifying fields where the rubric doesn't actually need the real value, and keeping the golden/hard/red-team suites in the same regulated data perimeter as production, not exported to a laptop or a third-party eval SaaS tenant. Judge calls that send case data to an external LLM provider are a specific exposure point — for anything touching real customer financial data, that argues for a judge model deployed inside your own boundary rather than a public API endpoint.

**Q6: How do you use evals as a guardrail — a genuine release gate — rather than a metric people check after the fact?**

The three gates in this chapter are exactly designed to sit in the deployment path, not beside it: a CI gate blocks any prompt/tool/config change where golden-suite pass rate regresses more than a set threshold, using enough N that a flaky single case can't kill trust in the gate; a release gate requires the hard suite and the safety/red-team suite to pass before a model or prompt upgrade ships, because a model upgrade is a change like any other and evals are how you accept it; and a production canary runs online evals — judge scoring a sampled percentage of live runs — to catch drift between releases before it becomes a customer-facing incident. The discipline that makes this a real guardrail rather than theater is that the gate threshold itself is policy: it's set and changed through review, never quietly loosened by the team whose change is currently failing it.

**Q7: Who should have access to your eval datasets and eval results, and how do you apply least privilege there?**

Because eval datasets are built from production traces, they carry the same access-control obligations as the underlying customer data — so the same RBAC/entitlement model that gates access to transaction data and case notes should gate who can read, export, or add cases to the golden and red-team suites, not a separate looser policy just because it's "test infrastructure." Judge outputs and gate results need a narrower but different control: they're evidence for model risk management, so write access (who can approve a case as "passing," who can change a rubric, who can move the pass/fail threshold) should sit with a role distinct from the engineers being evaluated — self-certifying your own change against a suite you can also edit isn't a control, it's paperwork. Red-team and safety suites deserve the tightest access of all, since they typically encode the exact failure modes an adversary would want to know are being tested for, and read access to "what we test against" is itself sensitive.

**Q8: How would you run online evals in production without either drowning yourself in judge cost or missing a real regression between releases?**

You sample rather than score every run — the canary pattern is a judge scoring a defined percentage of live traffic, weighted toward the highest-risk flows (fraud disputes, credit-adjacent decisions) rather than a flat random sample across everything. Each scored run gets tagged with the config fingerprint of the exact system version that produced it, so a drift you catch in the canary can be traced to precisely which prompt, tool schema, or model version is responsible rather than a vague "quality dropped this week." The trigger for action is the same statistical discipline as the CI gate — a sustained drop against baseline over enough sampled cases, not a single bad trace — and a canary alert should route back into the same suites: promote the failing production case into the golden or hard suite so the next CI run catches it before it ever reaches canary again.

**Q9: Design the eval layer for a banking agent that handles transaction disputes end to end — what would you actually build?**

Following the layered stack in this chapter, I'd build outcome checks against ground truth where it exists (was the correct transaction identified, was the dispute category assigned per the actual policy clause) and rubric/judge scoring where it doesn't (was the tone appropriate, did the agent avoid committing to a refund timeline it can't guarantee); trajectory checks scoring whether the path to resolution was reasonable and efficient, not just whether the final answer was right; and deterministic tool-use checks against the tool logs — right tool, right arguments, did it recover cleanly from a failed lookup. On top of that I'd curate a 60-case golden suite sourced from real disputed-transaction traces for regression, a hard suite of edge cases (disputed EMI charges, cross-border POS, duplicate merchant postings) to track real progress, and a red-team suite probing prompt injection and policy-violation attempts, wired into a CI gate on every change and a canary sampling live dispute traffic — with a calibrated judge whose human-agreement rate I can quote to the model risk team, because that number is the actual audit artifact.

**Q10: What's the practical difference between evaluating an agent's final answer and evaluating its trajectory, and why do interviewers keep asking about it?**

This gets asked constantly because it's the single most agent-specific idea in the whole evals discipline — outcome evaluation asks "did it reach the right destination," while trajectory evaluation asks "was the path there reasonable," and the two can diverge in ways a naive eval completely misses. An agent that stumbles into the right refund category after six unnecessary tool calls, a wrong lookup, and a lucky recovery scores identically to a clean, efficient resolution if you only grade the final answer — but that's a latent failure: the next customer with slightly different phrasing may not get lucky. Practically this means trajectory checks — expected-step matching against a reference path, efficiency versus a turn budget, or a judge scoring the trace itself rather than just the output — sit alongside outcome checks in the same eval case, not as an afterthought bolted on later.

**Q11: How do you decide when an eval metric has stopped being useful — the "Goodhart's law" problem interviewers sometimes probe for in eval design?**

A single blessed metric, once it becomes the thing a team is tuned and rewarded against, gets gamed by that same team's own optimization — pass rate on a fixed golden suite creeps up not because the agent got better broadly but because the suite's specific cases got specifically overfit. The defense is structural: keep a held-out suite the team being measured doesn't have write access to and can't see the exact cases in, rotate a portion of it periodically so memorization doesn't accumulate, and treat a suspiciously fast climb in pass rate as a signal to audit, not celebrate. This is also why rubric decomposition matters here too — many narrow, evidence-cited criteria are harder to game wholesale than one blended score, because gaming one sub-criterion (say, "avoided commitments") tends to visibly break another (say, "resolved the case"), which surfaces the gaming instead of hiding it.
