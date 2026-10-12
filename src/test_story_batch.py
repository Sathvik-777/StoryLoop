import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from api_cost_tracker import start_cost_tracking
from tracked_openai import TrackedOpenAIClient

from story_generator import StoryGenerator
from story_evaluator import StoryEvaluator
from story_rewriter import StoryRewriter

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")
BATCH_SIZE = 10
MAX_REWRITES = 1
OUTPUT_DIR = ROOT_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = OUTPUT_DIR / f"story_batch_{timestamp}.txt"


def results_stories(results):
    return [item["final_story"] for item in results]


def write_section(file, title, value):
    file.write(f"{title}:\n")
    file.write(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2))
    file.write("\n\n")


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set. Configure it before running.")

    cost_tracker = start_cost_tracking(ROOT_DIR / "output" / "current_run")
    client = TrackedOpenAIClient()
    generator = StoryGenerator(client)
    evaluator = StoryEvaluator(client)
    rewriter = StoryRewriter(client)
    results = []
    errors = 0

    with output_file.open("w", encoding="utf-8") as file:
        file.write("STORYLOOP - STORY BATCH TEST\n")
        file.write(f"Generated: {datetime.now()}\n")
        file.write(f"Stories requested: {BATCH_SIZE}\n")
        file.write("=" * 80 + "\n\n")

        for index in range(1, BATCH_SIZE + 1):
            print(f"[{index}/{BATCH_SIZE}] Generating story...")
            try:
                story = generator.generate_story()
                metadata = dict(generator.last_metadata)
                initial_story = story

                evaluation = evaluator.evaluate_story(
                    story,
                    metadata=metadata,
                    previous_stories=results_stories(results),
                )
                initial_evaluation = dict(evaluation)
                rewritten = False
                acceptance = None
                revision = None

                if evaluation["verdict"] == "REWRITE" and MAX_REWRITES:
                    print(f"[{index}/{BATCH_SIZE}] Rewriting diagnosed weakness...")
                    revision = rewriter.rewrite_story(story, evaluation, metadata=metadata)
                    rewritten = True
                    acceptance = rewriter.choose_better(
                        original=initial_story, revision=revision, metadata=metadata
                    )
                    story = acceptance["selected_story"]
                    evaluation = evaluator.evaluate_story(
                        story,
                        metadata=metadata,
                        previous_stories=results_stories(results),
                    )

                word_count = len(story.split())
                result = {
                    "story": story,
                    "final_story": story,
                    "original_story": initial_story,
                    "revision_candidate": revision,
                    "metadata": metadata,
                    "initial_evaluation": initial_evaluation,
                    "final_evaluation": evaluation,
                    "rewritten": rewritten,
                    "acceptance": ({k: v for k, v in acceptance.items() if k != "selected_story"}
                                   if acceptance else None),
                    "original_word_count": len(initial_story.split()),
                    "revision_word_count": len(revision.split()) if revision else None,
                    "word_count": word_count,
                }
                results.append(result)

                file.write(f"STORY {index}\n")
                file.write("-" * 80 + "\n")
                write_section(file, "METADATA", metadata)
                write_section(file, "ORIGINAL STORY", initial_story)
                write_section(file, "INITIAL EVALUATION", initial_evaluation)
                if revision is not None:
                    write_section(file, "REVISION CANDIDATE", revision)
                    write_section(file, "REVISION WORD COUNT", str(len(revision.split())))
                write_section(file, "REWRITE ATTEMPTED", str(rewritten))
                if acceptance:
                    write_section(file, "ACCEPTANCE DECISION", result["acceptance"])
                write_section(file, "FINAL EVALUATION", evaluation)
                write_section(file, "FINAL STORY", story.strip())
                write_section(file, "ORIGINAL WORD COUNT", str(result["original_word_count"]))
                write_section(file, "FINAL WORD COUNT", str(word_count))
                file.write("=" * 80 + "\n\n")
                file.flush()

                print(
                    f"[{index}/{BATCH_SIZE}] Done | {metadata.get('genre', 'unknown genre')} | "
                    f"{word_count} words | {evaluation['verdict']} | "
                    f"rewrite attempted={rewritten} | "
                    f"accepted revision={bool(acceptance and acceptance.get('winner') == 'B')}"
                )
            except Exception as error:
                errors += 1
                message = f"ERROR on story {index}: {type(error).__name__}: {error}"
                print(message)
                file.write(message + "\n\n")
                file.flush()

        summary = {
            "requested": BATCH_SIZE,
            "completed": len(results),
            "errors": errors,
            "pass_count": sum(r["final_evaluation"]["verdict"] == "PASS" for r in results),
            "rewrite_attempts": sum(r["rewritten"] for r in results),
            "rewrites_accepted": sum(bool(r["acceptance"] and r["acceptance"]["winner"] == "B") for r in results),
            "word_count_range_failures": sum(
                not 120 <= r["word_count"] <= 150 for r in results
            ),
            "quality_scores": [
                {
                    "clarity": r["final_evaluation"].get("clarity"),
                    "introduction_context": r["final_evaluation"].get("introduction_context"),
                    "development": r["final_evaluation"].get("development"),
                    "payoff": r["final_evaluation"].get("payoff"),
                }
                for r in results
            ],
            "word_counts": [
                {
                    "original": r["original_word_count"],
                    "revision": r["revision_word_count"],
                    "final": r["word_count"],
                }
                for r in results
            ],
            "api_calls": {
                "story_generator": generator.api_calls,
                "evaluator": evaluator.api_calls,
                "rewriter_and_acceptance_judge": rewriter.api_calls,
                "total": generator.api_calls + evaluator.api_calls + rewriter.api_calls,
            },
        }
        write_section(file, "BATCH SUMMARY", summary)

    print(f"\nBatch complete. Results saved to:\n{output_file}")
    print(f"API cost report: {cost_tracker.write_report()}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
