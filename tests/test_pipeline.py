"""
Lightweight tests that don't require an API key — they check the
prompt-building and control-flow logic, mocking out the LLM calls.
Run with: python -m pytest tests/
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from src.generator import build_generation_prompt
from src.rubric import RUBRIC, rubric_as_prompt_block
from src.orchestrator import LessonPipeline


def test_generation_prompt_includes_feedback():
    prompt = build_generation_prompt("RAG", feedback=["fix jargon"])
    assert "fix jargon" in prompt
    assert "RAG" in prompt


def test_generation_prompt_includes_memory_notes():
    prompt = build_generation_prompt("RAG", memory_notes=["(covers_key_points) missed 'why it matters'"])
    assert "why it matters" in prompt


def test_rubric_prompt_block_has_all_ids():
    block = rubric_as_prompt_block()
    for item in RUBRIC:
        assert item["id"] in block


def test_pipeline_terminates_on_repeated_failure():
    """Even if every attempt fails, the loop must terminate at max_retries + 1."""
    fail_eval = {
        "all_passed": False,
        "checks": {item["id"]: {"pass": False, "reason": "nope"} for item in RUBRIC},
        "failed_ids": [item["id"] for item in RUBRIC],
    }
    with patch("src.orchestrator.generate_lesson", return_value="draft"), \
         patch("src.orchestrator.evaluate_lesson", return_value=fail_eval), \
         patch("src.orchestrator.memory.get_top_failure_notes", return_value=[]), \
         patch("src.orchestrator.memory.record_failures"), \
         patch.object(LessonPipeline, "_append_log"):
        pipeline = LessonPipeline(max_retries=2)
        result = pipeline.run("test topic")
        assert result["attempts"] == 3  # 1 initial + 2 retries
        assert result["passed"] is False


def test_pipeline_stops_early_on_pass():
    pass_eval = {
        "all_passed": True,
        "checks": {item["id"]: {"pass": True, "reason": "ok"} for item in RUBRIC},
        "failed_ids": [],
    }
    with patch("src.orchestrator.generate_lesson", return_value="draft"), \
         patch("src.orchestrator.evaluate_lesson", return_value=pass_eval), \
         patch("src.orchestrator.memory.get_top_failure_notes", return_value=[]), \
         patch.object(LessonPipeline, "_append_log"):
        pipeline = LessonPipeline(max_retries=2)
        result = pipeline.run("test topic")
        assert result["attempts"] == 1
        assert result["passed"] is True


def test_demo_mode_forces_fail_then_pass():
    """With DEMO_FORCE_FIRST_FAIL on, a lesson that would have passed on
    attempt 1 is forced to fail once, then genuinely passes on attempt 2."""
    def fresh_pass_eval(*args, **kwargs):
        return {
            "all_passed": True,
            "checks": {item["id"]: {"pass": True, "reason": "ok"} for item in RUBRIC},
            "failed_ids": [],
        }

    with patch("src.orchestrator.generate_lesson", return_value="draft"), \
         patch("src.orchestrator.evaluate_lesson", side_effect=fresh_pass_eval), \
         patch("src.orchestrator.memory.get_top_failure_notes", return_value=[]), \
         patch("src.orchestrator.memory.record_failures"), \
         patch("src.orchestrator.DEMO_FORCE_FIRST_FAIL", True), \
         patch.object(LessonPipeline, "_append_log"):
        pipeline = LessonPipeline(max_retries=2)
        result = pipeline.run("test topic")
        assert result["attempts"] == 2
        assert result["passed"] is True
        assert result["history"][0]["passed"] is False
        assert result["history"][1]["passed"] is True
