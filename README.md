# Self-Evaluating Lesson Content Generator

An agentic system that generates a beginner lesson on a given topic,
judges its own output against a hard pass/fail rubric, and regenerates
until it clears the bar — or gives up after a bounded number of retries
and ships its best attempt with a full log of what it tried.

Built for: **GenAI Engineer – Content Systems** take-home assessment.
Submission topic: **Introduction to RAG (Retrieval-Augmented Generation)**.

---

## 1. Architecture

```
            ┌────────────┐
   topic ─▶ │  GENERATE  │◀───────────────┐
            └─────┬──────┘                │
                   │ lesson draft         │ targeted feedback
                   ▼                      │ (which checks failed + why)
            ┌────────────┐                │
            │  EVALUATE  │────fail────────┘
            └─────┬──────┘
                   │ pass, OR retries exhausted
                   ▼
            ┌────────────┐
            │   OUTPUT    │ → final lesson + rejection_log.jsonl
            └────────────┘

            Cross-run: every failure is written to logs/memory.json.
            The next GENERATE call for ANY topic is pre-warned with the
            most common past failure reasons, so the system gets sharper
            over time without hand-editing prompts.
```

**Components** (`src/`):

| File | Responsibility |
|---|---|
| `rubric.py` | The 6 hard pass/fail checkpoints, as data (not hardcoded into prompts) |
| `generator.py` | Builds the generation prompt (fresh or with retry feedback + memory notes) and calls the LLM |
| `evaluator.py` | LLM-as-judge: scores the lesson against every rubric item, PASS/FAIL + one-line reason each, no partial credit |
| `memory.py` | Persists failure patterns across runs (`logs/memory.json`) and surfaces the top recurring ones |
| `orchestrator.py` | The generate → evaluate → regenerate loop; guarantees termination at `1 + MAX_RETRIES` attempts |
| `llm_client.py` | Only place that talks to the LLM provider — swap providers/models here only |

`main.py` is the CLI entry point. `tests/test_pipeline.py` covers the
prompt-building and loop-termination logic with the LLM mocked out (no
API key needed to run tests).

## 2. Design decisions & trade-offs

**Why hard pass/fail per checkpoint instead of a 1–10 score?**
A score is ambiguous to act on ("6/10 — good enough?"). A checklist of
booleans is directly actionable: a FAIL tells the generator exactly
which sentence-level habit to fix next, and the loop has an
unambiguous stopping condition (`all_passed`).

**Why LLM-as-judge instead of regex/heuristics?**
Every checkpoint here is semantic ("is this jargon explained in plain
language?", "is this example concrete?"). These don't reduce to string
matching. The trade-off is judge reliability — mitigated by: (a) a
strict system prompt with an explicit "no partial credit" instruction,
(b) forcing structured JSON output so failures can't hide in prose,
and (c) treating a missing/omitted check_id as an automatic FAIL so a
judge that silently drops a checkpoint can never let a bad lesson
through.

**Why max 1–2 retries, not unbounded?**
The assignment requires the loop to always terminate. Unbounded
regeneration also risks the generator overfitting to the judge's exact
phrasing rather than genuinely improving. Two retries is enough to fix
concrete, named failures without spiraling.

**Why memory across runs, not just within a run?**
Within-run feedback fixes *this* lesson. Cross-run memory
(`logs/memory.json`) fixes the *system*: if "unexplained jargon" is the
most common failure across many topics, every future first draft gets
pre-warned about it — this is the self-evolving piece, separate from
the single-run retry loop.

**Why a flat JSON file for memory/logs, not a DB or vector store?**
Right-sized for a single-user take-home. The interfaces
(`memory.record_failures` / `memory.get_top_failure_notes`) are the
seam — swapping in SQLite or a vector store for semantic similarity
search over past failures (instead of exact check_id counting) is a
contained change, not a rewrite.

## 3. Setup

```bash
git clone <your-repo-url>
cd rag-lesson-generator
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your ANTHROPIC_API_KEY
```

### Where to get an LLM / API key
- **Groq (default, used by this project, free):** create a free key at
  https://console.groq.com/keys — no credit card required. Groq hosts
  open models (Llama 3.3, etc.) and serves them free with generous
  rate limits. Check https://console.groq.com/docs/models for the
  current free model list if `llama-3.3-70b-versatile` in
  `.env.example` has changed by the time you read this.
- **Alternative providers:** the system only touches the LLM through
  `src/llm_client.py`, so swapping to Anthropic, OpenAI, Gemini, or a
  local model via Ollama means rewriting just that one file's
  `call_llm` / `call_llm_json` functions — nothing else in the
  pipeline needs to change.

## 4. Run it

```bash
python main.py --topic "RAG (Retrieval-Augmented Generation)"
```

Outputs:
- `output/lesson_final.md` — the passing lesson (or best-effort if retries ran out)
- `logs/rejection_log.jsonl` — one JSON line per attempt: what failed, why, timestamp
- `logs/memory.json` — accumulating cross-run failure memory

Run tests (no API key required — LLM calls are mocked):
```bash
python -m pytest tests/ -v
```

## 5. Project structure

```
rag-lesson-generator/
├── README.md
├── requirements.txt
├── .env.example
├── main.py                    # CLI entry point
├── src/
│   ├── __init__.py
│   ├── llm_client.py          # provider wrapper (only file that calls the LLM API)
│   ├── rubric.py               # the 6 pass/fail checkpoints, as data
│   ├── generator.py            # builds prompts + generates lesson drafts
│   ├── evaluator.py             # LLM-as-judge against the rubric
│   ├── memory.py                 # cross-run failure memory
│   └── orchestrator.py           # generate → evaluate → regenerate loop
├── tests/
│   └── test_pipeline.py        # mocked unit tests, no API key needed
├── logs/                        # created at runtime
│   ├── rejection_log.jsonl
│   └── memory.json
└── output/                      # created at runtime
    └── lesson_final.md
```

## 6. What's still needed from you for the submission

The assignment asks for 3 deliverables — this repo covers #1:

1. **GitHub repo** ✅ this project — push it, this README doubles as setup docs.
2. **Document (Google Doc / Notion)** — paste the final `output/lesson_final.md`
   content plus a short "how I designed the rubric and why" section (you can
   lift straight from "Design decisions & trade-offs" above and adapt in
   your own words).
3. **Loom video (15–20 min)** — walk through: this architecture diagram,
   one live run showing a FAIL → regenerate → PASS cycle (deliberately
   loosen a rubric wording first if your first real run passes on attempt
   1, so the retry path is visible on camera), then `rejection_log.jsonl`
   and `memory.json` to show the audit trail and cross-run learning.
