from dotenv import load_dotenv
from openai import OpenAI

from story_generator import StoryGenerator
from story_evaluator import StoryEvaluator


load_dotenv()

client = OpenAI()

generator = StoryGenerator(client)
evaluator = StoryEvaluator(client)

story = generator.generate_story(
    genre="mystery",
    theme="a man discovers that his apartment has one room that shouldn't exist",
    duration_seconds=45,
    tone="suspenseful"
)

print("\n===== GENERATED STORY =====\n")
print(story)

evaluation = evaluator.evaluate_story(story)


print("\n===== STORY EVALUATION =====\n")

for key, value in evaluation.items():
    print(f"{key}: {value}")

if evaluation["verdict"] == "PASS":
    print("\nThe story has passed the evaluation.")
else:
    print("\nThe story needs to be rewritten based on the evaluation feedback.")