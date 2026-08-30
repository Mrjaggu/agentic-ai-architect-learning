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
