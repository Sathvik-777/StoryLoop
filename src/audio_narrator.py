import os
import re
import shutil
import subprocess
from pathlib import Path

from openai import OpenAI


class NarrationEngine:
    def __init__(
        self,
        client: OpenAI | None = None,
        model: str | None = None,
        voice: str = "alloy",
    ):
        self.client = client or OpenAI()
        self.model = model or os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        self.voice = voice

    @staticmethod
    def _estimate_duration_seconds(text: str) -> float:
        words = len(text.split())
        if words <= 0:
            return 1.0
        duration = max(1.0, words / 2.8)
        return min(duration, 20.0)

    @staticmethod
    def _split_story_into_segments(story: str, segment_count: int) -> list[str]:
        if not story:
            return []

        clean_story = " ".join(story.strip().split())
        sentence_split = re.split(r"(?<=[.!?])\s+", clean_story)
        sentences = [
            sentence.strip() for sentence in sentence_split if sentence.strip()
        ]

        if not sentences:
            return [clean_story]

        if len(sentences) <= segment_count:
            return sentences

        chunk_sizes = [len(sentences) // segment_count for _ in range(segment_count)]
        for index in range(len(sentences) % segment_count):
            chunk_sizes[index] += 1

        segments = []
        cursor = 0
        for chunk_size in chunk_sizes:
            chunk = sentences[cursor : cursor + chunk_size]
            if not chunk:
                break
            segments.append(" ".join(chunk))
            cursor += chunk_size

        return segments

    def generate_audio(self, text: str, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="wav",
        )
        response.stream_to_file(str(output_path))
        return output_path

    @staticmethod
    def _read_audio_duration(audio_path: Path) -> float:
        ffprobe_path = shutil.which("ffprobe")
        if not ffprobe_path:
            return 0.0

        result = subprocess.run(
            [
                ffprobe_path,
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

    def build_scene_narration(
        self, story: str, scene_count: int, output_dir: str | Path
    ):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        segments = self._split_story_into_segments(story, scene_count)
        narration_plan = []

        for index, segment in enumerate(segments, start=1):
            audio_path = output_dir / f"scene_{index}_narration.wav"
            self.generate_audio(segment, audio_path)

            duration = self._read_audio_duration(audio_path)

            if duration <= 0 or duration > 1000:
                duration = self._estimate_duration_seconds(segment)

            narration_plan.append(
                {
                    "scene_number": index,
                    "narration_text": segment,
                    "audio_path": str(audio_path),
                    "duration_seconds": round(duration, 2),
                }
            )

        return narration_plan
