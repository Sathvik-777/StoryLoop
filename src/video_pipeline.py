from pathlib import Path
from urllib.request import Request, urlopen

from subtitle_generator import SubtitleGenerator
from audio_narrator import NarrationEngine
from video_assembler import VideoAssembler


class StoryVideoPipeline:
    def __init__(self, client=None, output_dir: str | Path | None = None):
        self.client = client
        self.output_dir = (
            Path(output_dir)
            if output_dir
            else Path(__file__).resolve().parent.parent / "output" / "rendered"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.narrator = (
            NarrationEngine(client=client)
            if client
            else NarrationEngine()
        )

        self.assembler = VideoAssembler(output_dir=self.output_dir)

        self.subtitle_generator = SubtitleGenerator()

    @staticmethod
    def _reset_render_cache(
        target_dir: str | Path,
        preserve_audio: bool = False,
    ) -> None:
        target_dir = Path(target_dir)

        if not target_dir.exists():
            return

        # When a narration plan is supplied by the replay system,
        # preserve the existing narration audio files.
        directories = (
            ("images",)
            if preserve_audio
            else ("images", "audio")
        )

        for directory_name in directories:
            directory = target_dir / directory_name

            if directory.exists():
                for file in directory.iterdir():
                    if file.is_file():
                        file.unlink()

        for file in target_dir.glob("scene_*.mp4"):
            file.unlink()

        for file in target_dir.glob("*.mp4"):
            if file.name != "story_video.mp4":
                file.unlink()

        for file in target_dir.glob("concat_list.txt"):
            file.unlink()

    @staticmethod
    def _download_image_to_local(
        image_url: str,
        cache_dir: Path,
        scene_number: int,
    ) -> str:
        cache_dir.mkdir(parents=True, exist_ok=True)

        local_path = (
            cache_dir / f"scene_{scene_number}_selected_image.jpg"
        )

        if local_path.exists():
            return str(local_path)

        request = Request(
            image_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"
                ),
                "Accept": (
                    "image/avif,image/webp,image/apng,image/svg+xml,"
                    "image/*,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.pexels.com/",
            },
        )

        with urlopen(request, timeout=30) as response:
            data = response.read()

        local_path.write_bytes(data)

        return str(local_path)

    def render_story_video(
        self,
        story: str,
        final_media_plan: list[dict],
        output_dir: str | Path | None = None,
        narration_plan: list[dict] | None = None,
    ):
        target_dir = (
            Path(output_dir)
            if output_dir
            else self.output_dir
        )

        target_dir.mkdir(parents=True, exist_ok=True)

        self._reset_render_cache(
            target_dir,
            preserve_audio=narration_plan is not None,
        )

        if not self.assembler.ffmpeg_available():
            return {
                "status": "skipped",
                "reason": (
                    "ffmpeg is not installed or not on PATH; "
                    "video rendering was skipped."
                ),
                "output_dir": str(target_dir),
                "narration_plan": narration_plan or [],
            }

        # If a narration plan was supplied by the pipeline or replay
        # system, reuse it instead of generating narration again.
        if narration_plan is None:
            scene_count = max(
                1,
                len(final_media_plan),
            )

            narration_plan = self.narrator.build_scene_narration(
                story=story,
                scene_count=scene_count,
                output_dir=target_dir / "audio",
            )

        # ---------------------------------------------------------
        # Generate subtitles from the narration
        # ---------------------------------------------------------

        subtitle_path = (
            target_dir.parent.parent
            / "09_subtitles.srt"
        )

        self.subtitle_generator.generate_srt(
            narration_plan=narration_plan,
            output_path=subtitle_path,
        )

        # ---------------------------------------------------------
        # Build individual scene videos
        # ---------------------------------------------------------

        final_video_clips = []

        for scene_result in final_media_plan:
            scene_number = int(
                scene_result.get("scene_number")
            )

            selected = scene_result.get(
                "selected_image"
            )

            if not selected:
                continue

            image_url = selected.get(
                "image_url"
            )

            if not image_url:
                continue

            narration = next(
                (
                    item
                    for item in narration_plan
                    if item["scene_number"] == scene_number
                ),
                None,
            )

            if narration is None:
                continue

            local_image_path = (
                self._download_image_to_local(
                    image_url=image_url,
                    cache_dir=target_dir / "images",
                    scene_number=scene_number,
                )
            )

            clip_path = (
                target_dir
                / f"scene_{scene_number}.mp4"
            )

            self.assembler.build_scene_video(
                image_path=local_image_path,
                narration_audio=narration["audio_path"],
                output_path=clip_path,
                duration=narration["duration_seconds"],
            )

            final_video_clips.append(
                str(clip_path)
            )

        # ---------------------------------------------------------
        # Stop if no valid scenes were produced
        # ---------------------------------------------------------

        if not final_video_clips:
            return {
                "status": "skipped",
                "reason": (
                    "No valid scene images or "
                    "narration were produced."
                ),
                "output_dir": str(target_dir),
                "narration_plan": narration_plan,
            }

        # ---------------------------------------------------------
        # Assemble all scene clips into the final video
        # ---------------------------------------------------------

        final_video = (
            target_dir / "story_video.mp4"
        )

        self.assembler.assemble_video(
            final_video_clips,
            final_video,
        )

        # ---------------------------------------------------------
        # Burn subtitles into the assembled video
        # ---------------------------------------------------------

        subtitle_video = (
            target_dir / "story_video_subtitled.mp4"
        )

        self.assembler.burn_subtitles(
            video_path=final_video,
            subtitle_path=subtitle_path,
            output_path=subtitle_video,
        )

        # Replace the original final video with the subtitled version.
        subtitle_video.replace(final_video)

        # ---------------------------------------------------------
        # Return render result
        # ---------------------------------------------------------

        return {
            "status": "rendered",
            "output_file": str(final_video),
            "clip_count": len(final_video_clips),
            "output_dir": str(target_dir),
            "subtitle_file": str(subtitle_path),
            "narration_plan": narration_plan,
        }