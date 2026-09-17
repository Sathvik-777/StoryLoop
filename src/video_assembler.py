import os
import shutil
import subprocess
from pathlib import Path


class VideoAssembler:
    def __init__(
        self, output_dir: str | Path | None = None, ffmpeg_path: str | None = None
    ):
        self.output_dir = (
            Path(output_dir).resolve()
            if output_dir
            else (Path(__file__).resolve().parent.parent / "output").resolve()
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = ffmpeg_path or os.getenv("FFMPEG_PATH", "ffmpeg")

    def ffmpeg_available(self) -> bool:
        return shutil.which(self.ffmpeg_path) is not None

    @staticmethod
    def _ensure_image_ready(image_path: str | Path) -> str:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        return str(path)

    def _create_scene_clip(
        self,
        image_path: str | Path,
        narration_audio: str | Path,
        output_path: str | Path,
        duration: float,
    ) -> Path:
        if not self.ffmpeg_available():
            raise RuntimeError(
                "ffmpeg is required to render video clips but is not installed or not on PATH."
            )

        image_source = self._ensure_image_ready(image_path)
        audio_source = str(narration_audio)
        output_target = Path(output_path)
        output_target.parent.mkdir(parents=True, exist_ok=True)

        safe_duration = max(1.0, min(float(duration or 1.0), 20.0))
        command = [
            self.ffmpeg_path,
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            image_source,
            "-i",
            audio_source,
            "-t",
            str(safe_duration),
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p,fps=30",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(output_target),
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        return output_target

    def _build_concat_file(self, clip_paths: list[Path]) -> Path:
        concat_path = self.output_dir / "concat_list.txt"
        entries = "\n".join(f"file '{clip_path.resolve()}'" for clip_path in clip_paths)
        concat_path.write_text(entries + "\n", encoding="utf-8")
        return concat_path

    def assemble_video(
        self, clip_paths: list[str | Path], output_file: str | Path
    ) -> Path:
        if not self.ffmpeg_available():
            raise RuntimeError(
                "ffmpeg is required to assemble the final video but is not installed or not on PATH."
            )

        output_file = Path(output_file).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        resolved_clips = [Path(clip) for clip in clip_paths]
        concat_file = self._build_concat_file(resolved_clips)

        command = [
            self.ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(output_file),
        ]
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("\n===== FFMPEG ERROR =====\n")
            print(result.stderr)
            raise RuntimeError("FFmpeg failed while assembling the final video.")
        return output_file

    def burn_subtitles(
        self,
        video_path: str | Path,
        subtitle_path: str | Path,
        output_path: str | Path,
    ):
        video_path = Path(video_path)
        subtitle_path = Path(subtitle_path)
        output_path = Path(output_path)

        subtitle_filter_path = (
            str(subtitle_path)
            .replace("\\", "/")
            .replace(":", "\\:")
        )

        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(video_path),
            "-vf",
            (
                f"subtitles='{subtitle_filter_path}':"
                "force_style="
                "'FontName=Arial,"
                "FontSize=18,"
                "PrimaryColour=&H00FFFFFF,"
                "OutlineColour=&H00000000,"
                "BorderStyle=1,"
                "Outline=3,"
                "Shadow=1,"
                "Alignment=2,"
                "MarginV=100'"
            ),
            "-c:v",
            "libx264",
            "-crf",
            "23",
            "-preset",
            "medium",
            "-c:a",
            "copy",
            str(output_path),
        ]

        subprocess.run(command, check=True)
        return str(output_path)

    def build_scene_video(self, image_path, narration_audio, output_path, duration):
        return self._create_scene_clip(
            image_path=image_path,
            narration_audio=narration_audio,
            output_path=output_path,
            duration=duration,
        )
