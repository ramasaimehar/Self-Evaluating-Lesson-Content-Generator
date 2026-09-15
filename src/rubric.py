"""
rubric.py
---------
Defines the hard pass/fail checkpoints a generated lesson must clear.

Design principle from the assignment: "no partial credit, each check
clearly passes or fails." So every rubric item is phrased as a yes/no
question with a crisp, checkable definition of what a PASS looks like.
This keeps the evaluator's job binary instead of asking it to produce
a fuzzy 1-10 score (which is much harder to act on programmatically).
"""

RUBRIC = [
    {
        "id": "accurate_grounded",
        "name": "Accurate & Grounded",
        "description": (
            "Every factual claim in the lesson is technically correct and "
            "not invented. No hallucinated APIs, numbers, or mechanisms."
        ),
    },
    {
        "id": "beginner_friendly_language",
        "name": "Beginner-Friendly Language",
        "description": (
            "Sentences are short and plain. Written for a 12th-grade "
            "graduate with limited English vocabulary and a non-English-"
            "medium background — no complex sentence structures, no idioms."
        ),
    },
    {
        "id": "teaches_by_example",
        "name": "Teaches By Example",
        "description": (
            "The lesson includes at least one concrete, worked example "
            "(a scenario, analogy, or walk-through) — not definitions alone."
        ),
    },
    {
        "id": "no_unexplained_jargon",
        "name": "No Unexplained Jargon",
        "description": (
            "Every technical term used (e.g. embedding, vector, retrieval, "
            "token) is defined in plain language the first time it appears."
        ),
    },
    {
        "id": "covers_key_points",
        "name": "Covers the Key Points",
        "description": (
            "The lesson answers three things for the given topic: what it "
            "is, why it matters, and how it works — someone with zero "
            "background should finish it and 'get it'."
        ),
    },
    {
        "id": "coherent_teaching_flow",
        "name": "Coherent Teaching Flow",
        "description": (
            "Ideas build in a logical order (simple -> complex). No topic "
            "is referenced before it's introduced. The lesson reads as one "
            "connected explanation, not disjointed bullet facts."
        ),
    },
]


def rubric_as_prompt_block() -> str:
    """Render the rubric as a numbered list for injection into the
    evaluator prompt."""
    lines = []
    for i, item in enumerate(RUBRIC, start=1):
        lines.append(f"{i}. [{item['id']}] {item['name']}: {item['description']}")
    return "\n".join(lines)
