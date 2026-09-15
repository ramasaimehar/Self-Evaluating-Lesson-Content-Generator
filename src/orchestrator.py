"""
orchestrator.py
----------------
The core agentic loop: generate -> evaluate -> regenerate.

Terminates in at most (1 + MAX_RETRIES) generation attempts, guaranteed,
because the retry counter is decremented unconditionally on every failed
pass. Every attempt (pass or fail) is written to the rejection log, so
the final artifact carries a full audit trail of what changed and why.
"""

import os
import json
import datetime

from src.generator import generate_lesson
from src.evaluator import evaluate_lesson
from src.rubric import RUBRIC
from src import memory

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "rejection_log.jsonl")
RUBRIC_BY_ID = {item["id"]: item for item in RUBRIC}

# --- Demo mode -------------------------------------------------------
# Set DEMO_FORCE_FIRST_FAIL=true (in .env or the shell) to GUARANTEE
# attempt 1 fails on one named check and attempt 2 passes, regardless
# of what the model actually writes. Only for recording a clean
# fail -> regenerate -> pass demonstration of the control flow. It only
# overrides the outcome when the real evaluation would otherwise have
# passed — a genuine failure is never hidden or altered. Leave this
# unset (or "false") for your real submission run.
DEMO_FORCE_FIRST_FAIL = os.getenv("DEMO_FORCE_FIRST_FAIL", "false").lower() == "true"
DEMO_FORCE_CHECK_ID = os.getenv("DEMO_FORCE_CHECK_ID", "teaches_by_example")
DEMO_FORCE_REASON = (
    "Forced fail for demonstration purposes (DEMO_FORCE_FIRST_FAIL=true) "
    "to show the regenerate loop reacting to a failed checkpoint."
)


class LessonPipeline:
    def __init__(self, max_retries: int = MAX_RETRIES):
        self.max_retries = max_retries

    def run(self, topic: str, verbose: bool = True) -> dict:
        attempt = 0
        feedback = None
        memory_notes = memory.get_top_failure_notes()
        history = []

        while True:
            attempt += 1
            if verbose:
                print(f"\n--- Attempt {attempt} : generating lesson for \"{topic}\" ---")

            lesson = generate_lesson(topic, feedback=feedback, memory_notes=memory_notes)

            if verbose:
                print(f"--- Attempt {attempt} : evaluating against rubric ---")

            evaluation = evaluate_lesson(topic, lesson)

            # Demo override: only fires on attempt 1, only if it would
            # otherwise have passed, and only when explicitly enabled.
            if attempt == 1 and DEMO_FORCE_FIRST_FAIL and evaluation["all_passed"]:
                evaluation["checks"][DEMO_FORCE_CHECK_ID] = {
                    "pass": False,
                    "reason": DEMO_FORCE_REASON,
                }
                evaluation["failed_ids"] = [DEMO_FORCE_CHECK_ID]
                evaluation["all_passed"] = False

            record = {
                "attempt": attempt,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "topic": topic,
                "passed": evaluation["all_passed"],
                "checks": evaluation["checks"],
            }
            history.append(record)
            self._append_log(record)

            if verbose:
                if evaluation["all_passed"]:
                    print(f"--- Attempt {attempt} : PASSED — every checkpoint cleared ---")
                else:
                    print(f"--- Attempt {attempt} : FAILED ---")
                    for cid in evaluation["failed_ids"]:
                        reason = evaluation["checks"][cid]["reason"]
                        print(f"    [FAIL] {cid}: {reason}")

            if not evaluation["all_passed"]:
                memory.record_failures(topic, evaluation["checks"])

            if evaluation["all_passed"] or attempt > self.max_retries:
                return {
                    "topic": topic,
                    "final_lesson": lesson,
                    "passed": evaluation["all_passed"],
                    "attempts": attempt,
                    "history": history,
                }

            # Build targeted feedback for the next attempt from failed checks only.
            # Include the EXACT rubric requirement, not just the judge's
            # paraphrased reason — otherwise the model has to re-guess precise
            # formatting rules (exact bullet counts, exact headings, etc.)
            # from a short summary instead of being told the literal spec.
            feedback = [
                f"{cid} — REQUIREMENT: {RUBRIC_BY_ID[cid]['description']} "
                f"| WHY YOUR LAST DRAFT FAILED: {evaluation['checks'][cid]['reason']}"
                for cid in evaluation["failed_ids"]
            ]
            if verbose:
                print(f"--- Regenerating with targeted feedback from {len(feedback)} failed check(s) ---")

    @staticmethod
    def _append_log(record: dict) -> None:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
