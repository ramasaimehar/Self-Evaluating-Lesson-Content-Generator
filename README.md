Project structure is:

```text
rag-lesson-generator/
├── README.md
├── requirements.txt
├── .env
├── main.py
├── list_models.py
├── src/
│   ├── __init__.py
│   ├── llm_client.py
│   ├── generator.py
│   ├── evaluator.py
│   ├── rubric.py
│   ├── memory.py
│   └── orchestrator.py
├── tests/
│   └── test_pipeline.py
├── logs/
│   ├── rejection_log.jsonl
│   └── memory.json
└── output/
    └── lesson_final.md
```

# README.md

````markdown
# Self-Evaluating Lesson Content Generator

An agentic GenAI system that generates beginner-friendly educational content, evaluates its own output against a strict PASS/FAIL rubric, regenerates failed content using targeted feedback, and remembers recurring failures across runs.

Built for the **GenAI Engineer – Content Systems** take-home assessment.

### Demonstration Topic

**Introduction to RAG (Retrieval-Augmented Generation)**

---

## 🚀 What This Project Does

This project is more than a simple LLM-based content generator.

It implements a feedback-driven agentic workflow:

```text
                    INPUT
                      │
                      ▼
          "Introduction to RAG"
                      │
                      ▼
              ┌──────────────┐
              │   GENERATE   │
              │  Lesson Draft│
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │   EVALUATE   │
              │  PASS / FAIL │
              └──────┬───────┘
                     │
                ┌────┴────┐
                │         │
              PASS       FAIL
                │         │
                ▼         ▼
              Finish   Record Failure
                          │
                          ▼
                  Build Targeted
                     Feedback
                          │
                          ▼
                    REGENERATE
                          │
                          └──────────► EVALUATE
````
## 📊 Example Runs

The following screenshot shows two possible outcomes:

1. **First-attempt success:** the generated lesson passes all rubric
   checkpoints immediately.

2. **Self-correction:** the first attempt fails a rubric checkpoint,
   the evaluator identifies the problem, targeted feedback is sent to
   the generator, and the regenerated lesson passes on the second attempt.

<img width="1262" height="356" alt="image" src="https://github.com/user-attachments/assets/8d5788c5-e390-40f4-8731-90233b684f7b" />


The system terminates when:

* All rubric checkpoints PASS, or
* The maximum retry limit is reached.

---

# 🎯 Problem Statement

Large Language Models can generate educational content quickly, but a generated lesson may contain:

* Incorrect information
* Unexplained technical terms
* Complex language
* Missing examples
* Poor teaching flow
* Missing important concepts

Instead of blindly accepting the first LLM response, this project introduces a **self-evaluation and refinement loop**.

The system asks:

> "Does this generated lesson actually satisfy the requirements?"

If the answer is no, the evaluator explains what failed and the generator receives that feedback to create an improved version.

---

# 👨‍🎓 Target Learner

The generated lesson is designed for:

* A 12th-grade graduate from India
* Limited English vocabulary
* Non-English-medium educational background
* No previous technical knowledge
* Interested in starting a career in AI

The generator therefore prioritizes simple language, short sentences, clear explanations, examples, and a gradual teaching flow.

---

# 🧠 Agentic Workflow

The project follows a **Generate → Evaluate → Decide → Regenerate** pattern.

### 1. Generate

The LLM generates a beginner-friendly lesson for the requested topic.

### 2. Evaluate

A separate evaluation step checks the lesson against six hard PASS/FAIL checkpoints.

### 3. Decide

The orchestrator checks the evaluation result.

```text
All checks PASS
      ↓
Accept lesson

Any check FAIL
      ↓
Regenerate
```

### 4. Regenerate

The failed checkpoint and its reason are converted into targeted feedback.

Instead of simply telling the model:

> "Try again."

the system provides:

```text
Failed Check
+
Exact Requirement
+
Reason for Failure
```

This allows the next generation to focus specifically on the detected problem.

### 5. Remember

Failures are stored in persistent memory.

Recurring failures are then supplied to future generation prompts as warnings.

---

# 📋 Evaluation Rubric

The evaluator uses six binary checkpoints.

There is **no partial credit**.

## 1. Accurate & Grounded

The lesson must contain technically correct information and should not invent facts, numbers, APIs, or mechanisms.

## 2. Beginner-Friendly Language

The lesson should use short sentences and simple vocabulary suitable for the target learner.

## 3. Teaches By Example

The lesson must contain at least one concrete example, analogy, scenario, or walkthrough.

## 4. No Unexplained Jargon

Technical terms must be explained in simple language when they are first introduced.

## 5. Covers the Key Points

The lesson must explain:

* What it is
* Why it matters
* How it works

## 6. Coherent Teaching Flow

The lesson should move logically from simple concepts to more complex concepts without introducing unexplained ideas too early.

---

# 🏗️ Project Architecture

```text
                         USER
                           │
                           ▼
                   Topic / Input
                           │
                           ▼
                ┌──────────────────┐
                │  orchestrator.py │
                │  Agent Controller│
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │   generator.py   │
                │  Generate Lesson │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │  llm_client.py   │
                │    Groq / LLM    │
                └────────┬─────────┘
                         │
                         ▼
                    Lesson Draft
                         │
                         ▼
                ┌──────────────────┐
                │   evaluator.py   │
                │    LLM-as-Judge  │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │    rubric.py     │
                │   6 PASS/FAIL    │
                │    Checkpoints   │
                └────────┬─────────┘
                         │
                    PASS / FAIL
                     ↙       ↘
                  PASS       FAIL
                   │           │
                   │           ▼
                   │     ┌────────────┐
                   │     │ memory.py  │
                   │     │ Store Fail │
                   │     └─────┬──────┘
                   │           │
                   │           ▼
                   │     Targeted Feedback
                   │           │
                   │           ▼
                   │       Regenerate
                   │           │
                   │           └──────► Evaluate
                   │
                   ▼
               Final Lesson
```

---

# 📁 File-by-File Explanation

## `main.py`

The CLI entry point of the application.

It:

1. Accepts the topic from the command line.
2. Creates the lesson pipeline.
3. Runs the agentic workflow.
4. Saves the final lesson.
5. Displays the final status.
6. Reports the locations of the output and rejection log.

Example:

```bash
python main.py --topic "RAG (Retrieval-Augmented Generation)"
```

---

## `src/llm_client.py`

The LLM provider abstraction layer.

This is the only component that directly communicates with the LLM provider.

Currently:

```text
Provider: Groq
Model: configured through MODEL_NAME
```

It provides two main interfaces:

### `call_llm()`

Used for normal text generation.

### `call_llm_json()`

Used when the evaluator needs structured JSON output.

Keeping the provider interaction isolated means another model provider can be integrated without rewriting the rest of the pipeline.

---

## `src/generator.py`

Responsible for generating the educational lesson.

The generator prompt defines:

* Target learner
* Simple language requirements
* Technical term explanations
* Example/analogy requirement
* What → Why → How structure
* Simple → Complex teaching flow

It also accepts:

```text
memory_notes
feedback
```

Therefore, regeneration is targeted instead of being a random second generation.

---

## `src/rubric.py`

Contains the six evaluation checkpoints.

The rubric is stored as structured data rather than being duplicated throughout the application.

This makes the evaluation criteria:

* Explicit
* Easy to modify
* Reusable by the evaluator
* Easy to inspect during the walkthrough

---

## `src/evaluator.py`

Acts as the quality-control component.

It uses an **LLM-as-a-Judge** approach.

The evaluator receives:

```text
Topic
+
Generated Lesson
+
Rubric
```

and returns structured results:

```json
{
  "checks": {
    "accurate_grounded": {
      "pass": true,
      "reason": "..."
    },
    "teaches_by_example": {
      "pass": false,
      "reason": "..."
    }
  }
}
```

Every checkpoint must be evaluated.

If the model accidentally omits a checkpoint, the implementation treats that missing checkpoint as a FAIL rather than allowing an incomplete evaluation to pass.

---

## `src/orchestrator.py`

This is the main controller of the agentic workflow.

It coordinates:

```text
Generate
   ↓
Evaluate
   ↓
Decision
   ↓
Record failure
   ↓
Create feedback
   ↓
Regenerate
   ↓
Evaluate again
```

It also:

* Controls the retry limit
* Maintains attempt history
* Writes the rejection log
* Sends targeted feedback to the generator
* Stops when the lesson passes
* Stops when the retry limit is reached

### Demo Mode

The project also contains a demo-only mechanism:

```text
DEMO_FORCE_FIRST_FAIL=true
```

This is used to reliably demonstrate the retry workflow during a walkthrough.

The real evaluator still runs first.

The demo mechanism only forces a first-attempt failure when the real evaluator would otherwise have passed, allowing the video to demonstrate:

```text
Attempt 1 → FAIL
             ↓
        Regenerate
             ↓
Attempt 2 → PASS
```

This mechanism is intended only for demonstrating the control flow.

---

## `src/memory.py`

Implements cross-run persistent memory.

Whenever a rubric checkpoint fails, the system stores:

```text
Topic
Check ID
Failure Reason
```

in:

```text
logs/memory.json
```

The most frequent previous failure patterns are then surfaced to the generator before a new lesson is created.

This creates two levels of learning:

### Within a run

```text
FAIL → Feedback → Regenerate
```

### Across runs

```text
Past failures
      ↓
Persistent memory
      ↓
Future generation warnings
      ↓
Better first drafts
```

This cross-run behavior is the **self-evolving** component of the system.

---

# 📄 Output Files

The system produces three important artifacts.

## `output/lesson_final.md`

Contains the final accepted lesson.

For this assignment, the lesson covers:

**Retrieval-Augmented Generation (RAG)**

The generated lesson explains:

* What RAG is
* Why it matters
* How retrieval and generation work
* Simple examples and analogies

---

## `logs/rejection_log.jsonl`

Contains an audit trail of generation attempts.

Each line represents one attempt.

It records information such as:

```json
{
  "attempt": 1,
  "timestamp": "...",
  "topic": "RAG",
  "passed": false,
  "checks": {
    "...": "..."
  }
}
```

This makes it possible to see:

```text
Attempt 1
   ↓
What failed?
   ↓
Why did it fail?
   ↓
Attempt 2
   ↓
Did it pass?
```

---

## `logs/memory.json`

Contains persistent failure memory across runs.

Example:

```json
{
  "failures": [
    {
      "topic": "RAG",
      "check_id": "accurate_grounded",
      "reason": "Contains a made-up fact."
    }
  ]
}
```

The memory is then used to warn the generator about recurring mistakes.

---

# 🔍 Example Demonstrations

The project can demonstrate two different outcomes.

## Case 1 — Passes on First Attempt

```text
INPUT
  ↓
Generate
  ↓
Evaluate
  ↓
All 6 checks PASS
  ↓
FINAL LESSON
```

Example:

```text
Attempt 1 → PASS ✅
```

This is the ideal path when the first generated lesson already satisfies the rubric.

---

## Case 2 — Fails First, Then Passes

```text
INPUT
  ↓
Generate
  ↓
Evaluate
  ↓
❌ FAIL
  ↓
Failure reason recorded
  ↓
Targeted feedback
  ↓
Regenerate
  ↓
Evaluate
  ↓
✅ PASS
  ↓
FINAL LESSON
```

Example:

```text
Attempt 1 → FAIL ❌
              ↓
       Targeted feedback
              ↓
         Regeneration
              ↓
Attempt 2 → PASS ✅
```

This demonstrates the main self-evaluation and regeneration capability of the system.

---

# 🧠 Why These Design Decisions?

## Why PASS/FAIL instead of a 1–10 score?

A score such as `7/10` is ambiguous.

The system needs an actionable decision:

```text
PASS → Accept
FAIL → Fix
```

Binary checkpoints make the workflow easier to automate.

---

## Why LLM-as-a-Judge?

The rubric contains semantic requirements.

For example:

> "Is the technical term properly explained?"

or:

> "Is the example concrete and useful?"

These are difficult to reliably evaluate using simple keyword matching or regular expressions.

The LLM can evaluate the meaning and context of the lesson.

---

## Why targeted feedback?

Instead of regenerating blindly, the system provides:

```text
Failed checkpoint
+
Required behavior
+
Reason for failure
```

This gives the generator a specific correction to make.

---

## Why bounded retries?

The pipeline uses a maximum retry count.

This prevents:

* Infinite LLM calls
* Uncontrolled API usage
* Endless regeneration
* Overfitting to evaluator wording

The system eventually terminates even if every attempt fails.

---

## Why persistent memory?

Retry feedback fixes the current lesson.

Persistent memory helps future lessons.

For example:

```text
Run 1:
"Unexplained jargon" → FAIL

Run 2:
Generator receives a warning about jargon

Run 3:
Same warning remains available
```

This allows the system to improve its behavior across runs without manually editing the generation prompt.

---

## Why JSON memory instead of a database?

This project is designed as a focused take-home implementation.

A flat JSON file is simple and sufficient for a single-user workflow.

For a production system, the memory layer could be replaced with:

* SQLite
* PostgreSQL
* Vector database
* Semantic similarity search

without changing the overall agent architecture.

---

# 🤖 LLM / Groq

This project uses **Groq** as the LLM API provider.

The Groq API key is stored in the local `.env` file:

```text
GROQ_API_KEY=your_key_here
```

The model is configured using:

```text
MODEL_NAME=your_available_model
```

The application loads these values using environment variables.

### Important

The real API key should **never be committed to GitHub**.

Use:

```text
.env
```

locally and provide:

```text
.env.example
```

for other users.

---

# ⚙️ Installation

Clone the repository:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd rag-lesson-generator
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

On Windows PowerShell, you can also create the `.env` file manually.

Add your Groq API key:

```text
GROQ_API_KEY=your_groq_api_key
MODEL_NAME=your_available_groq_model
MAX_RETRIES=2
```

---

# ▶️ Run the Project

Run with the default topic:

```bash
python main.py
```

Or provide a topic:

```bash
python main.py --topic "RAG (Retrieval-Augmented Generation)"
```

The final lesson will be saved to:

```text
output/lesson_final.md
```

The rejection history will be saved to:

```text
logs/rejection_log.jsonl
```

Persistent failure memory will be saved to:

```text
logs/memory.json
```

---

# 🧪 Run Tests

The project includes lightweight tests that mock the LLM calls.

This means the control-flow tests do not require an API key.

Run:

```bash
python -m pytest tests/ -v
```

The tests cover:

* Generation prompt feedback
* Memory notes
* Rubric completeness
* Retry termination
* Early termination on PASS
* Demo FAIL → PASS behavior

---

# 🔐 Security

Do not commit:

```text
.env
```

or any file containing your real Groq API key.

Use `.env.example` to show the required configuration without exposing credentials.

---

# 📌 Technology Stack

| Component            | Technology                        |
| -------------------- | --------------------------------- |
| Programming Language | Python                            |
| LLM Provider         | Groq                              |
| LLM                  | Configurable through `MODEL_NAME` |
| Agent Pattern        | Generate → Evaluate → Regenerate  |
| Evaluation           | LLM-as-a-Judge                    |
| Rubric               | Binary PASS/FAIL                  |
| Memory               | JSON                              |
| Rejection Log        | JSONL                             |
| Lesson Output        | Markdown                          |
| Testing              | Pytest with mocked LLM calls      |
| Configuration        | Python dotenv                     |

---

# 🔮 Future Improvements

If this system were taken toward production, possible improvements would include:

* Replace JSON memory with a database
* Add semantic similarity search over previous failures
* Use separate models for generation and evaluation
* Add evaluator confidence and consistency checks
* Add a web UI
* Add observability and token/cost tracking
* Add versioning for prompts and rubrics
* Add human review for low-confidence evaluations
* Support multiple lesson formats and learner profiles

---

# 👤 Author

**Rama Sai Mehar Sreerama**

GenAI / AI-ML Engineer
