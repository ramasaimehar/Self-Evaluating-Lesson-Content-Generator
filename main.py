"""
main.py
-------
CLI entry point.

Usage:
    python main.py --topic "RAG (Retrieval-Augmented Generation)"
"""

import argparse
import os
import sys

from src.orchestrator import LessonPipeline

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def main():
    parser = argparse.ArgumentParser(description="Self-evaluating lesson content generator")
    parser.add_argument(
        "--topic",
        default="RAG (Retrieval-Augmented Generation)",
        help="The topic to generate a beginner lesson for",
    )
    args = parser.parse_args()

    pipeline = LessonPipeline()
    result = pipeline.run(args.topic)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "lesson_final.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result["final_lesson"])

    status = "PASSED" if result["passed"] else "SHIPPED BEST-EFFORT (did not fully pass)"
    print(f"\n=== {status} after {result['attempts']} attempt(s) ===")
    print(f"Lesson saved to: {out_path}")
    print(f"Rejection log:   {os.path.join('logs', 'rejection_log.jsonl')}")

    if not result["passed"]:
        last = result["history"][-1]
        failed = [cid for cid, v in last["checks"].items() if not v["pass"]]
        print(f"Still failing: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
