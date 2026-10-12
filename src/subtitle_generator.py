
from pathlib import Path

import whisperx


class SubtitleGenerator:
    def __init__(
        self,
        device: str = "cpu",
        compute_type: str = "int8",
        model_name: str = "base",
    ):
        self.device = device
        self.compute_type = compute_type
        self.model_name = model_name

        self.model = None
        self.align_model = None
        self.metadata = None

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        centiseconds = max(0, round(seconds * 100))

        hours = centiseconds // 360000
        centiseconds %= 360000

        minutes = centiseconds // 6000
        centiseconds %= 6000

        whole_seconds = centiseconds // 100
        centiseconds %= 100

        return (
            f"{hours}:{minutes:02d}:"
            f"{whole_seconds:02d}.{centiseconds:02d}"
        )

    @staticmethod
    def _escape_ass_text(text: str) -> str:
        return (
            text.replace("\\", r"\\")
            .replace("{", r"\{")
            .replace("}", r"\}")
            .replace("\n", " ")
        )

    def _load_models(self, language: str):
        if self.model is None:
            self.model = whisperx.load_model(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )

        if self.align_model is None:
            self.align_model, self.metadata = (
                whisperx.load_align_model(
                    language_code=language,
                    device=self.device,
                )
            )

    @staticmethod
    def _group_words(
        words: list[dict],
        max_words: int = 4,
        max_duration: float = 1.8,
    ) -> list[dict]:
        groups = []
        current = []

        for word in words:
            if not word.get("word", "").strip():
                continue

            if not current:
                current.append(word)
                continue

            current_duration = (
                word["end"] - current[0]["start"]
            )

            previous_text = current[-1]["word"].strip()
            ends_sentence = previous_text.endswith(
                (".", "!", "?", "…")
            )

            if (
                len(current) >= max_words
                or current_duration > max_duration
                or ends_sentence
            ):
                groups.append(current)
                current = [word]
            else:
                current.append(word)

        if current:
            groups.append(current)

        return [
            {
                "start": group[0]["start"],
                "end": group[-1]["end"],
                "words": [
                    {
                        "word": item["word"].strip(),
                        "start": item["start"],
                        "end": item["end"],
                    }
                    for item in group
                ],
            }
            for group in groups
        ]

    @staticmethod
    def _karaoke_text(words: list[dict]) -> str:
        parts = []

        for index, word in enumerate(words):
            duration = max(
                1,
                round(
                    (word["end"] - word["start"]) * 100
                ),
            )

            text = SubtitleGenerator._escape_ass_text(
                word["word"]
            )

            # Highlight each word as it is spoken.
            parts.append(f"{{\\kf{duration}}}{text}")

            if index < len(words) - 1:
                parts.append(" ")

        return "".join(parts)

    @staticmethod
    def _ass_header() -> str:
        return """[Script Info]
Title: StoryLoop Animated Captions
ScriptType: v4.00+
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,68,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,90,90,310,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def generate_ass(
        self,
        narration_plan: list[dict],
        output_path: str | Path,
    ) -> str:
        output_path = Path(output_path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        all_subtitles = []
        scene_offset = 0.0

        for scene in narration_plan:
            audio_path = Path(scene["audio_path"])

            if not audio_path.exists():
                raise FileNotFoundError(
                    f"Narration audio not found: {audio_path}"
                )

            audio = whisperx.load_audio(str(audio_path))

            if self.model is None:
                self.model = whisperx.load_model(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                )

            result = self.model.transcribe(
                audio,
                language="en",
                batch_size=4,
            )

            language = result["language"]
            self._load_models(language)

            aligned = whisperx.align(
                result["segments"],
                self.align_model,
                self.metadata,
                audio,
                self.device,
                return_char_alignments=False,
            )

            words = aligned.get("word_segments", [])
            grouped = self._group_words(words)

            for subtitle in grouped:
                all_subtitles.append(
                    {
                        "start": (
                            subtitle["start"] + scene_offset
                        ),
                        "end": (
                            subtitle["end"] + scene_offset
                        ),
                        "words": subtitle["words"],
                    }
                )

            scene_offset += float(
                scene["duration_seconds"]
            )

        with output_path.open(
            "w",
            encoding="utf-8-sig",
            newline="\n",
        ) as file:
            file.write(self._ass_header())

            for subtitle in all_subtitles:
                start = self._format_timestamp(
                    subtitle["start"]
                )
                end = self._format_timestamp(
                    subtitle["end"]
                )
                
                text = (
                    r"{\fad(120,100)\fscx85\fscy85"
                    r"\t(0,140,\fscx100\fscy100)}"
                    + self._karaoke_text(subtitle["words"])
                )
                
                file.write(
                    "Dialogue: 0,"
                    f"{start},{end},Default,,"
                    "0,0,0,,"
                    f"{text}\n"
                )

        return str(output_path)
