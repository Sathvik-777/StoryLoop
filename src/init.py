from dotenv import load_dotenv
from openai import OpenAI

from story_generator import StoryGenerator
from story_evaluator import StoryEvaluator
from story_rewriter import StoryRewriter
from story_storage import save_story_record

load_dotenv()

client = OpenAI()

generator = StoryGenerator(client)
evaluator = StoryEvaluator(client)
rewriter = StoryRewriter(client)

PASS_THRESHOLD = 7.5
MAX_REVISIONS = 3


def story_passes(evaluation):
    return (
        evaluation["overall_score"] >= PASS_THRESHOLD
        and evaluation["hook"] >= PASS_THRESHOLD
        and evaluation["payoff"] >= PASS_THRESHOLD
        and evaluation["pacing"] >= 6.5
    )


story = generator.generate_story(
    genre="mystery",
    theme="a man discovers that his apartment has a hidden room",
    duration_seconds=45,
    tone="suspenseful"
)

revision_history = []
passed = False

for revision in range(MAX_REVISIONS + 1):

    print(f"\n===== VERSION {revision + 1} =====\n")
    print(story)

    evaluation = evaluator.evaluate_story(story)

    revision_history.append({
        "version": revision + 1,
        "story": story,
        "evaluation": evaluation
    })

    print("\n===== EVALUATION =====\n")

    for key, value in evaluation.items():
        print(f"{key}: {value}")

    if story_passes(evaluation):

        print("\n✅ STORY PASSED")
        print(f"Final version: {revision + 1}")
        passed = True
        break

    if revision == MAX_REVISIONS:

        print("\n❌ STORY FAILED AFTER MAXIMUM REVISIONS")
        break

    print(
        f"\n🔄 Story failed. "
        f"Rewriting... ({revision + 1}/{MAX_REVISIONS})"
    )

    story = rewriter.rewrite_story(
        story,
        evaluation
    )

if passed:
    memory_file, published_file = save_story_record(
        revision_history,
        story,
        evaluation
    )

    print("\n===== STORYLOOP STORAGE =====")
    print(f"Memory record: {memory_file}")
    print(f"Published story: {published_file}")

else:
    print("\n❌ Story was not published.")