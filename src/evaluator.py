"""
evaluator.py
------------
Judges a lesson draft against the rubric. Each checkpoint is scored
PASS or FAIL only (no partial credit) with a one-line reason, so a
failure can be fed straight back into the generator as an actionable
instruction.

Using the LLM itself as the judge (an "LLM-as-judge" pattern) rather
than hand-written heuristics/regex, because the checks here are
semantic (is this jargon explained? is this example concrete?) and
don't reduce to string matching.
"""

from src.llm_client import call_llm_json
from src.rubric import RUBRIC, rubric_as_prompt_block

SYSTEM_PROMPT = """You are a strict but fair content reviewer for beginner
lessons aimed at a 12th-grade graduate with limited English vocabulary and
no technical background. You do not give partial credit: every checkpoint
is either a clear PASS or a clear FAIL.

Respond with ONLY valid JSON (no markdown fences, no commentary) in this
exact shape:
{
  "checks": {
    "<check_id>": {"pass": true|false, "reason": "one short sentence"}
  }
}
Include every check_id given to you, in the same order.
"""


def build_evaluation_prompt(topic: str, lesson: str) -> str:
    return (
        f'Topic being taught: "{topic}"\n\n'
        f"Rubric checkpoints:\n{rubric_as_prompt_block()}\n\n"
        f"Lesson to review:\n---\n{lesson}\n---\n\n"
        "Evaluate the lesson against every checkpoint above. Be strict: "
        "if a term is used without being explained, that's a FAIL on "
        "no_unexplained_jargon even if the rest of the lesson is good."
    )


def evaluate_lesson(topic: str, lesson: str) -> dict:
    """Returns:
    {
        "all_passed": bool,
        "checks": {check_id: {"pass": bool, "reason": str}, ...},
        "failed_ids": [check_id, ...],
    }
    """
    user_prompt = build_evaluation_prompt(topic, lesson)
    result = call_llm_json(SYSTEM_PROMPT, user_prompt, max_tokens=1200)

    checks = result.get("checks", {})
    failed_ids = [cid for cid, v in checks.items() if not v.get("pass", False)]

    # Guard against the model omitting a check_id: treat missing as fail
    # so a silently-dropped checkpoint can never smuggle a bad lesson through.
    expected_ids = {item["id"] for item in RUBRIC}
    for cid in expected_ids - checks.keys():
        checks[cid] = {"pass": False, "reason": "Evaluator did not return this check."}
        failed_ids.append(cid)

    return {
        "all_passed": len(failed_ids) == 0,
        "checks": checks,
        "failed_ids": failed_ids,
    }
