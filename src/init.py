import json
import os

from dotenv import load_dotenv
from run_artifacts import reset_run, save_json, save_text

load_dotenv()

run_dir = reset_run()

from openai import OpenAI

from clip_ranker import ClipRanker
from content_strategist import ContentStrategist
from media_selector import MediaSelector
from pexels_media import PexelsMediaGetter
from scene_designer import SceneDesigner
from story_evaluator import StoryEvaluator
from story_generator import StoryGenerator
from story_rewriter import StoryRewriter
from story_storage import save_story_record
from video_pipeline import StoryVideoPipeline
from youtube_researcher import YouTubeResearcher

client = OpenAI()

pexels = PexelsMediaGetter()
clip_ranker = ClipRanker()
generator = StoryGenerator(client)
evaluator = StoryEvaluator(client)
rewriter = StoryRewriter(client)
media_selector = MediaSelector(client)
researcher = YouTubeResearcher()
strategist = ContentStrategist(client)
scene_designer = SceneDesigner(client)
video_pipeline = StoryVideoPipeline(client)

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
save_json("01_research.json", research)

print("\n===== CONTENT STRATEGY =====\n")
strategy = strategist.create_strategy(research)
save_json("02_content_strategy.json", strategy)

print(json.dumps(strategy, indent=2))

story = generator.generate_story(strategy)
save_text("03_story_versions/version_1_generated.txt", story)

revision_history = []
passed = False

for revision in range(MAX_REVISIONS + 1):

    print(f"\n===== VERSION {revision + 1} =====\n")
    print(story)

    evaluation = evaluator.evaluate_story(story)
    save_text(
        f"03_story_versions/version_{revision + 1}_story.txt",
        story,
    )
    save_json(
        f"03_story_versions/version_{revision + 1}_evaluation.json",
        evaluation,
    )

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
    save_text(
        f"03_story_versions/version_{revision + 2}_rewritten.txt",
        story,
    )

if passed:
    scene_plan = scene_designer.design_scenes(story)
    save_json("04_scene_plan.json", scene_plan)

    print("\n===== VISUAL SCENE PLAN =====\n")
    print(json.dumps(scene_plan, indent=2))

    media_plan = []

    for scene in scene_plan["scenes"]:
        scene_media = pexels.get_images_for_scene(scene)
        media_plan.append(scene_media)
    save_json("05_pexels_media.json", media_plan)

    print("\n===== PEXELS MEDIA RESULTS =====\n")
    print(json.dumps(media_plan, indent=2))

    ranked_media_plan = []
    for scene, scene_media in zip(scene_plan["scenes"], media_plan):
        ranked_media_plan.append(
            clip_ranker.rank_scene_images(scene, scene_media["images"])
        )
    save_json("06_clip_ranked_media.json", ranked_media_plan)

    print("\n===== CLIP RANKED MEDIA =====\n")
    print(json.dumps(ranked_media_plan, indent=2))

    final_media_plan = []
    for scene, ranked_scene in zip(scene_plan["scenes"], ranked_media_plan):
        final_media_plan.append(
            media_selector.select_scene_image(
                scene,
                ranked_scene["ranked_images"],
            )
        )
    save_json("07_final_media_selection.json", final_media_plan)

    print("\n===== FINAL MEDIA SELECTION =====\n")
    print(json.dumps(final_media_plan, indent=2))

    render_result = video_pipeline.render_story_video(
        story=story,
        final_media_plan=final_media_plan,
        output_dir=run_dir / "rendered",
    )
    save_json("08_render_result.json", render_result)

    print("\n===== STORY VIDEO =====")
    print(json.dumps(render_result, indent=2))

    memory_file, published_file = save_story_record(revision_history, story, evaluation)

    print("\n===== STORYLOOP STORAGE =====")
    print(f"Memory record: {memory_file}")
    print(f"Published story: {published_file}")

else:
    print("\n❌ Story was not published.")
