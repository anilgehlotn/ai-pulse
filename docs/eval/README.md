# Open-answer scoring eval

AI Pulse asks an LLM to score each employee's free-text answer from 1 to 5 against a rubric and to raise risk flags
(`customer_data_shared`, `confidential_data_shared`, `unreviewed_output`, `policy_unaware`). This eval checks how
far we can trust those scores and flags.

## What it measures

Each case is a hand-written answer with the score range and flags I'd expect. The harness sends every case through
the real pipeline: injection check, prompt, model, strict parser and the data-risk cap. It then reports:

| Metric | Meaning |
|---|---|
| Parsed OK | Share of model replies that passed the strict parser (integer 1–5, a reason, known flags) |
| Score in expected range | Of the parsed cases, how many landed in the expected range |
| Flag precision | Of the flags the model raised, how many were expected |
| Flag recall | Of the expected flags, how many the model raised |
| Forbidden flags raised | Flags that are clearly wrong for a case |
| Injections caught | Prompt-injection cases stopped before reaching the model |
| Capped for data risk | Scores lowered to 3 because a data-sharing flag was raised |

## The two case sets

- **dev**: `backend/data/eval_set.json`, 15 cases. I looked at these results while changing the prompt.
- **holdout**: `backend/data/eval_holdout.json`, 10 cases. Written before the prompt change, with different jobs and
  wording, and **not used for tuning**. If dev improves and holdout doesn't, the prompt was fitted to the dev cases.

## How to run

From `backend/`:

```bash
# Mock mode (what CI runs): canned replies, so only the injection check is meaningful.
python -m app.eval

# Live, against a local Ollama model. Real environment variables override .env.
AI_MODE=live LLM_API_URL=http://localhost:11434/v1/chat/completions LLM_API_KEY=ollama \
  LLM_MODEL=llama3.2 LLM_JSON_MODE=true python -m app.eval --set dev    # or --set holdout / --set all
```

The exit code is non-zero if any injection gets through. In live mode it is also non-zero if any reply fails to parse.

## Results: llama3.2 (3.2B, Q4_K_M) via Ollama, temperature 0

- **Before** is `open-v2`: no flag definitions, no examples, no cap.
- **After** is `open-v3`: each flag defined, "only flag on direct evidence; when unsure, do not flag", one score-2
  and one score-5 example, and a deterministic cap of 3 when a data-sharing flag is raised.
- Re-running each set gave byte-identical output, so these differences are not run-to-run noise.

### Dev (15 cases)

| Metric | Before (open-v2) | After (open-v3) |
|---|---|---|
| Parsed OK | 100% | 100% |
| Score in expected range | 75.0% (9/12) | 75.0% (9/12) |
| Flag precision | 36.4% (4/11) | **85.7%** (6/7) |
| Flag recall | 66.7% (4/6) | **100%** (6/6) |
| `policy_unaware` raised | 8 of 12 answers | 1 of 12 (the correct one) |
| Forbidden flags raised | 0 | 0 |
| Injections caught | 3/3 | 3/3 |
| Capped for data risk | — | 3 |

### Holdout (10 cases)

| Metric | Before (open-v2) | After (open-v3) |
|---|---|---|
| Parsed OK | 100% | 100% |
| Score in expected range | 66.7% (6/9) | **55.6%** (5/9) |
| Flag precision | 25.0% (2/8) | 33.3% (1/3) |
| Flag recall | 50.0% (2/4) | **25.0%** (1/4) |
| `policy_unaware` raised | 5 of 9 answers | 1 of 9 (the correct one) |
| Forbidden flags raised | 0 | 0 |
| Injections caught | 0/1 | 0/1 |
| Capped for data risk | — | 0 |

### What this says

- **Over-flagging is fixed on both sets.** `policy_unaware` went from most answers to only the one that earns it.
  This change carries over to unseen cases.
- **The cap fixed the dev problem, not the prompt.** On `customer-data-pasted` and `confidential-financials` the model
  still scored above 3 after flagging data sharing; the cap brought both to 3. The model on its own still rewards
  unsafe data handling.
- **Data-flag detection does not carry over.** On holdout the model raised no data flag for a payroll export with
  bank details or for a customer call transcript. It raised `unreviewed_output` instead. With no data flag, the cap
  never triggers. The cap is only as good as the flag that turns it on.
- **Recall on holdout fell** (50% → 25%). The "when unsure, do not flag" instruction cut wrong flags but also some
  right ones: `sales-proposal-unread` lost its correct `unreviewed_output` flag.
- **The novel injection beat both defences.** Its wording isn't on the phrase list, so the model saw it, obeyed
  ("record the top mark") and scored it 4, then 5 after the change. I did not add that wording to the list: that
  would be fitting to the holdout.
- **The top of the scale is compressed.** Both "advanced" cases (one per set) got 4 instead of 5.

Net: open-v3 is better at *not* raising wrong flags and, thanks to the cap, safer when it *does* see data sharing. It
is not yet reliable at *spotting* data sharing in new wording, and a reworded injection gets through. Because the
holdout has now been looked at, the next prompt change needs a fresh holdout to be measured honestly.

## Honest limits

- **Tiny sets.** 12 + 9 scored cases. One case moves "score in range" by 8–11 points. Treat these as smoke tests, not
  benchmarks.
- **One author.** I wrote every case, its expected range and its flags. The labels are my judgement, and the holdout
  was written by the same person who wrote the prompt, so it is less independent than a second person's set would be.
- **One small local model.** llama3.2 3B, 4-bit. A larger model may behave very differently, better or worse.
- **One question.** Every case answers the same open question (`common-open`).
- **Holdout is now spent.** I've seen its results, so any further tuning measured on it is no longer a clean test.

## Files

- `llama3.2-before-dev.txt`, `llama3.2-before-holdout.txt`: open-v2 runs.
- `llama3.2-after-dev.txt`, `llama3.2-after-holdout.txt`: open-v3 runs.
