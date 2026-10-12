import json
import os
from pathlib import Path

from dotenv import load_dotenv
from run_artifacts import reset_run, save_json, save_text
from api_cost_tracker import start_cost_tracking
from tracked_openai import TrackedOpenAIClient


load_dotenv()

run_dir = reset_run()
cost_tracker = start_cost_tracking(run_dir)

from clip_ranker import ClipRanker
from media_selector import MediaSelector
from pexels_media import PexelsMediaGetter
from scene_designer import SceneDesigner
from story_evaluator import StoryEvaluator
from story_generator import StoryGenerator
from story_rewriter import StoryRewriter
from story_storage import save_story_record
from video_pipeline import StoryVideoPipeline
from script_parameters import load_publish_parameter

client = TrackedOpenAIClient()

pexels = PexelsMediaGetter()
clip_ranker = ClipRanker()
generator = StoryGenerator(client)
evaluator = StoryEvaluator(client)
rewriter = StoryRewriter(client)
media_selector = MediaSelector(client)
scene_designer = SceneDesigner(client)
video_pipeline = StoryVideoPipeline(client)

PASS_THRESHOLD = 7
MAX_REVISIONS = 1
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PARAMETERS_FILE = PROJECT_ROOT / "script_parameters.json"


def story_passes(evaluation):
    return evaluation.get("verdict") == "PASS"


print("\n===== STORY GENERATION =====\n")
story = generator.generate_story()
metadata = dict(generator.last_metadata)
original_story = story
save_text("03_story_versions/version_1_generated.txt", original_story)

initial_evaluation = evaluator.evaluate_story(original_story, metadata=metadata)
save_text("03_story_versions/version_1_story.txt", original_story)
save_json("03_story_versions/version_1_evaluation.json", initial_evaluation)
revision_history = [
    {"version": 1, "story": original_story, "evaluation": initial_evaluation}
]
story = original_story
evaluation = initial_evaluation
acceptance = None
passed = False

if initial_evaluation.get("verdict") == "REWRITE" and MAX_REVISIONS:
    revision = rewriter.rewrite_story(
        original_story, initial_evaluation, metadata=metadata
    )
    save_text("03_story_versions/version_2_rewrite_candidate.txt", revision)
    acceptance = rewriter.choose_better(
        original=original_story, revision=revision, metadata=metadata
    )
    save_json(
        "03_story_versions/version_2_acceptance_decision.json",
        {key: value for key, value in acceptance.items() if key != "selected_story"},
    )
    story = acceptance["selected_story"]
    evaluation = evaluator.evaluate_story(story, metadata=metadata)
    save_text("03_story_versions/version_2_selected_story.txt", story)
    save_json("03_story_versions/version_2_selected_evaluation.json", evaluation)
    revision_history.append(
        {
            "version": 2,
            "story": story,
            "evaluation": evaluation,
            "acceptance": {key: value for key, value in acceptance.items()
                           if key != "selected_story"},
        }
    )

passed = story_passes(evaluation)
print("\n===== FINAL STORY DECISION =====\n")
print(json.dumps(evaluation, indent=2))
print(f"Final story word count: {len(story.split())}")
print(f"Revision accepted: {bool(acceptance and acceptance.get('winner') == 'B')}")
print(
    "Story-stage API calls: "
    f"generator={generator.api_calls}, "
    f"evaluator={evaluator.api_calls}, rewriter/judge={rewriter.api_calls}"
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

    narration_plan = video_pipeline.narrator.build_scene_narration(
        story=story,
        scene_count=len(final_media_plan),
        output_dir=run_dir / "rendered" / "audio",
    )

    save_json("08_narration_plan.json", narration_plan)

    print("\n===== NARRATION PLAN =====\n")
    print(json.dumps(narration_plan, indent=2))

    render_result = video_pipeline.render_story_video(
        story=story,
        final_media_plan=final_media_plan,
        narration_plan=narration_plan,
        output_dir=run_dir / "rendered",
    )

    save_json("10_render_result.json", render_result)

    print("\n===== STORY VIDEO =====")
    print(json.dumps(render_result, indent=2))

    if render_result.get("status") == "rendered":
        if load_publish_parameter(SCRIPT_PARAMETERS_FILE):
            from youtube_publisher import YouTubePublisher

            print("\n===== YOUTUBE PUBLISHING =====")
            upload_result = YouTubePublisher().upload_video(
                video_path=render_result["output_file"],
                title="StoryLoop generated story",
                description=story,
                tags=["StoryLoop", "short story", "storytelling"],
                privacy_status="public",
            )
            save_json("11_youtube_upload.json", upload_result)
            print(json.dumps(upload_result, indent=2))
        else:
            print("\nYouTube publishing skipped (Publish is false or unavailable).")
    else:
        print("\nYouTube publishing skipped (no rendered video was produced).")

    memory_file, published_file = save_story_record(revision_history, story, evaluation)

    print("\n===== STORYLOOP STORAGE =====")
    print(f"Memory record: {memory_file}")
    print(f"Published story: {published_file}")

else:
    print("\n❌ Story was not published.")

print(f"\nAPI cost report: {cost_tracker.write_report()}")
