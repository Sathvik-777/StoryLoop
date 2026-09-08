import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from clip_ranker import ClipRanker
from content_strategist import ContentStrategist
from pexels_media import PexelsMediaGetter
from scene_designer import SceneDesigner
from story_evaluator import StoryEvaluator
from story_generator import StoryGenerator
from story_rewriter import StoryRewriter
from story_storage import save_story_record
from youtube_researcher import YouTubeResearcher

load_dotenv()

client = OpenAI()

pexels = PexelsMediaGetter()
clip_ranker = ClipRanker()
generator = StoryGenerator(client)
evaluator = StoryEvaluator(client)
rewriter = StoryRewriter(client)
researcher = YouTubeResearcher()
strategist = ContentStrategist(client)
scene_designer = SceneDesigner(client)

PASS_THRESHOLD = 7
MAX_REVISIONS = 3


def story_passes(evaluation):
    return (
        evaluation["overall_score"] >= PASS_THRESHOLD
        and evaluation["hook"] >= PASS_THRESHOLD
        and evaluation["payoff"] >= PASS_THRESHOLD
        and evaluation["pacing"] >= 6
    )


research = researcher.research(
    query=os.getenv("YOUTUBE_SEARCH_QUERY", "short form storytelling")
)
strategy = strategist.create_strategy(research)

print("\n===== CONTENT STRATEGY =====\n")
print(json.dumps(strategy, indent=2))

story = generator.generate_story(strategy)

revision_history = []
passed = False

for revision in range(MAX_REVISIONS + 1):

    print(f"\n===== VERSION {revision + 1} =====\n")
    print(story)

    evaluation = evaluator.evaluate_story(story)

    revision_history.append(
        {"version": revision + 1, "story": story, "evaluation": evaluation}
    )

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

    print(f"\n🔄 Story failed. " f"Rewriting... ({revision + 1}/{MAX_REVISIONS})")

    story = rewriter.rewrite_story(story, evaluation)

if passed:
    scene_plan = scene_designer.design_scenes(story)

    print("\n===== VISUAL SCENE PLAN =====\n")
    print(json.dumps(scene_plan, indent=2))

    media_plan = []

    for scene in scene_plan["scenes"]:
        scene_media = pexels.get_images_for_scene(scene)
        media_plan.append(scene_media)

    print("\n===== PEXELS MEDIA RESULTS =====\n")
    print(json.dumps(media_plan, indent=2))

    ranked_media_plan = []
    for scene, scene_media in zip(scene_plan["scenes"], media_plan):
        ranked_media_plan.append(
            clip_ranker.rank_scene_images(scene, scene_media["images"])
        )

    print("\n===== CLIP RANKED MEDIA =====\n")
    print(json.dumps(ranked_media_plan, indent=2))

    memory_file, published_file = save_story_record(revision_history, story, evaluation)

    print("\n===== STORYLOOP STORAGE =====")
    print(f"Memory record: {memory_file}")
    print(f"Published story: {published_file}")

else:
    print("\n❌ Story was not published.")
