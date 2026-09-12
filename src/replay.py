import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from openai import OpenAI

from refine_video import refine_videos
from run_artifacts import RUN_DIR, save_json, save_text


STAGES = [
    ("youtube", "YouTube research"),
    ("strategy", "Content strategy"),
    ("generation", "Story generation"),
    ("evaluation", "Story evaluation and revision"),
    ("scene_design", "Scene design"),
    ("pexels", "Pexels image search"),
    ("clip", "CLIP image ranking"),
    ("selection", "Final image selection"),
    ("narration", "Narration generation"),
    ("rendering", "Video rendering"),
]


def load_json(relative_path: str):
    path = RUN_DIR / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Missing checkpoint: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def latest_story() -> str:
    story_dir = RUN_DIR / "03_story_versions"
    candidates = sorted(story_dir.glob("version_*_story.txt"))
    if not candidates:
        candidates = sorted(story_dir.glob("version_*.txt"))
    if not candidates:
        raise FileNotFoundError(f"No story checkpoint found in {story_dir}")
    return candidates[-1].read_text(encoding="utf-8")


def choose_stage(prompt: str, first_index: int = 0) -> int:
    while True:
        print(f"\n{prompt}")
        for index, (_, label) in enumerate(STAGES[first_index:], start=first_index + 1):
            print(f"{index}. {label}")
        answer = input("Choose an option: ").strip()
        if answer.isdigit():
            selected = int(answer) - 1
            if first_index <= selected < len(STAGES):
                return selected
        print("Please choose one of the displayed numbers.")


def download_selected_images(final_media_plan: list[dict], rendered_dir: Path) -> None:
    image_dir = rendered_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    for scene in final_media_plan:
        scene_number = int(scene["scene_number"])
        selected_image = scene.get("selected_image") or {}
        image_url = selected_image.get("image_url")
        if not image_url:
            raise ValueError(f"No selected image URL for scene {scene_number}")

        image_path = image_dir / f"scene_{scene_number}_selected_image.jpg"
        if image_path.exists():
            continue

        request = Request(image_url, headers={"User-Agent": "StoryLoop/0.1"})
        with urlopen(request, timeout=30) as response:
            image_path.write_bytes(response.read())


def run_stage(stage: str, client: OpenAI) -> None:
    if stage == "youtube":
        from youtube_researcher import YouTubeResearcher

        researcher = YouTubeResearcher()
        research = researcher.research(
            query=os.getenv("YOUTUBE_SEARCH_QUERY", "short form storytelling")
        )
        save_json("01_research.json", research)

    elif stage == "strategy":
        from content_strategist import ContentStrategist

        strategy = ContentStrategist(client).create_strategy(load_json("01_research.json"))
        save_json("02_content_strategy.json", strategy)

    elif stage == "generation":
        from story_generator import StoryGenerator

        strategy = load_json("02_content_strategy.json")
        story = StoryGenerator(client).generate_story(strategy)
        save_text("03_story_versions/version_1_generated.txt", story)
        save_text("03_story_versions/version_1_story.txt", story)

    elif stage == "evaluation":
        from story_evaluator import StoryEvaluator
        from story_rewriter import StoryRewriter

        story = latest_story()
        evaluator = StoryEvaluator(client)
        rewriter = StoryRewriter(client)
        revision_history = []

        for revision in range(4):
            evaluation = evaluator.evaluate_story(story)
            revision_history.append(
                {"version": revision + 1, "story": story, "evaluation": evaluation}
            )
            save_text(f"03_story_versions/version_{revision + 1}_story.txt", story)
            save_json(
                f"03_story_versions/version_{revision + 1}_evaluation.json",
                evaluation,
            )

            if (
                evaluation["overall_score"] >= 7
                and evaluation["hook"] >= 7
                and evaluation["payoff"] >= 7
                and evaluation["pacing"] >= 6
            ):
                save_json("03_story_versions/revision_history.json", revision_history)
                save_text("03_story_versions/final_story.txt", story)
                return

            if revision < 3:
                story = rewriter.rewrite_story(story, evaluation)
                save_text(f"03_story_versions/version_{revision + 2}_rewritten.txt", story)

        save_json("03_story_versions/revision_history.json", revision_history)
        raise RuntimeError("Story did not pass after the maximum revisions.")

    elif stage == "scene_design":
        from scene_designer import SceneDesigner

        scene_plan = SceneDesigner(client).design_scenes(latest_story())
        save_json("04_scene_plan.json", scene_plan)

    elif stage == "pexels":
        from pexels_media import PexelsMediaGetter

        scene_plan = load_json("04_scene_plan.json")
        media_plan = [PexelsMediaGetter().get_images_for_scene(scene) for scene in scene_plan["scenes"]]
        save_json("05_pexels_media.json", media_plan)

    elif stage == "clip":
        from clip_ranker import ClipRanker

        scene_plan = load_json("04_scene_plan.json")
        media_plan = load_json("05_pexels_media.json")
        ranker = ClipRanker()
        ranked = [
            ranker.rank_scene_images(scene, media["images"])
            for scene, media in zip(scene_plan["scenes"], media_plan)
        ]
        save_json("06_clip_ranked_media.json", ranked)

    elif stage == "selection":
        from media_selector import MediaSelector

        scene_plan = load_json("04_scene_plan.json")
        ranked_media = load_json("06_clip_ranked_media.json")
        selector = MediaSelector(client)
        selected = [
            selector.select_scene_image(scene, ranked["ranked_images"])
            for scene, ranked in zip(scene_plan["scenes"], ranked_media)
        ]
        save_json("07_final_media_selection.json", selected)

    elif stage == "narration":
        from audio_narrator import NarrationEngine

        final_media = load_json("07_final_media_selection.json")
        narration = NarrationEngine(client).build_scene_narration(
            latest_story(),
            len(final_media),
            RUN_DIR / "rendered" / "audio",
        )
        save_json("08_narration_plan.json", narration)

    elif stage == "rendering":
        final_media = load_json("07_final_media_selection.json")
        rendered_dir = RUN_DIR / "rendered"
        download_selected_images(final_media, rendered_dir)
        refine_videos(rendered_dir, rendered_dir)
        save_json("09_render_result.json", {"status": "rendered", "output": str(rendered_dir / "story_video.mp4")})


def main() -> None:
    load_dotenv()
    print("StoryLoop Replay")
    print("This uses existing checkpoints and does not reset the current run.")

    start = choose_stage("Choose the starting stage:")
    end = choose_stage("Choose the ending stage:", first_index=start)
    selected_stages = STAGES[start : end + 1]

    print("\nReplay plan:")
    print(f"Start: {selected_stages[0][1]}")
    print(f"End:   {selected_stages[-1][1]}")
    print("\nThe following stages will run:")
    for _, label in selected_stages:
        print(f"- {label}")

    if input("\nContinue? [y/N]: ").strip().lower() != "y":
        print("Replay cancelled.")
        return

    client = OpenAI()
    for stage, label in selected_stages:
        print(f"\n===== {label} =====")
        run_stage(stage, client)
        print(f"Completed: {label}")

    print("\nReplay completed.")


if __name__ == "__main__":
    main()
