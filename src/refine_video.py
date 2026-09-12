import argparse
import subprocess
from pathlib import Path

from video_assembler import VideoAssembler


def narration_duration(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def refine_videos(source_dir: Path, output_dir: Path) -> Path:
    image_dir = source_dir / "images"
    audio_dir = source_dir / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    assembler = VideoAssembler(output_dir=output_dir)
    scene_clips = []

    image_paths = sorted(image_dir.glob("scene_*_selected_image.jpg"))
    if not image_paths:
        raise FileNotFoundError(f"No selected images found in {image_dir}")

    for image_path in image_paths:
        scene_number = image_path.name.split("_", 2)[1]
        audio_path = audio_dir / f"scene_{scene_number}_narration.wav"
        if not audio_path.exists():
            print(
                f"Warning: skipping scene {scene_number}; "
                f"narration file not found: {audio_path}"
            )
            continue

        clip_path = output_dir / f"scene_{scene_number}.mp4"
        assembler.build_scene_video(
            image_path=image_path,
            narration_audio=audio_path,
            output_path=clip_path,
            duration=narration_duration(audio_path),
        )
        scene_clips.append(clip_path)

    final_video = output_dir / "story_video.mp4"
    assembler.assemble_video(scene_clips, final_video)
    return final_video


def main() -> None:
    project_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Rebuild videos from existing selected images and narration audio."
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=project_dir / "output" / "current_run" / "rendered",
        help="Directory containing images/ and audio/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_dir / "output" / "current_run" / "rendered",
        help="Directory for rebuilt scene and final videos.",
    )
    args = parser.parse_args()

    final_video = refine_videos(args.source_dir, args.output_dir)
    print(f"Created {final_video}")


if __name__ == "__main__":
    main()