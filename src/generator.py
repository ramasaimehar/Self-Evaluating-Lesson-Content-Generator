"""
generator.py
------------
Turns a topic into a standalone beginner lesson. On retries, it is fed
the specific reasons the previous draft failed so the regeneration is
targeted, not a random re-roll.
"""

from src.llm_client import call_llm

SYSTEM_PROMPT = """You are a patient teacher writing a first lesson for a
complete beginner: a 12th-grade graduate from India, limited English
vocabulary, non-English-medium school background, who wants to start a
career in AI. They have never seen this topic before.

Rules for every lesson you write:
- Use short sentences and common, everyday words.
- Define every technical term the first time you use it, in plain language.
- Include at least one concrete example or analogy — never definitions alone.
- Cover three things, in this order: what it is, why it matters, how it works.
- Build ideas from simple to complex. Never use a term before introducing it.
- Do not invent facts, numbers, or mechanisms you are not sure about.
- Output plain Markdown: a title, then the lesson body. No meta-commentary
  about the lesson itself, just the lesson content.
"""


def build_generation_prompt(topic: str, feedback: list[str] | None = None,
                             memory_notes: list[str] | None = None) -> str:
    prompt = f'Write a beginner lesson on: "{topic}"\n\n'
    prompt += "Assume the learner starts from zero knowledge of this topic."

    if memory_notes:
        prompt += (
            "\n\nBefore you start, here are mistakes past lessons on similar "
            "topics have made — avoid repeating them:\n"
            + "\n".join(f"- {note}" for note in memory_notes)
        )

    if feedback:
        prompt += (
            "\n\nYour previous draft of THIS lesson failed review for these "
            "specific reasons. Fix every one of them in this rewrite:\n"
            + "\n".join(f"- {f}" for f in feedback)
        )

    return prompt


def generate_lesson(topic: str, feedback: list[str] | None = None,
                     memory_notes: list[str] | None = None) -> str:
    user_prompt = build_generation_prompt(topic, feedback, memory_notes)
    return call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=1800)
