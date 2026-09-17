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
        milliseconds = int(round(seconds * 1000))

        hours = milliseconds // 3_600_000
        milliseconds %= 3_600_000

        minutes = milliseconds // 60_000
        milliseconds %= 60_000

        seconds = milliseconds // 1000
        milliseconds %= 1000

        return (
            f"{hours:02d}:{minutes:02d}:{seconds:02d},"
            f"{milliseconds:03d}"
        )

    def _load_models(self, language: str):
        if self.model is None:
            self.model = whisperx.load_model(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )

        if self.align_model is None:
            (
                self.align_model,
                self.metadata,
            ) = whisperx.load_align_model(
                language_code=language,
                device=self.device,
            )

    @staticmethod
    def _group_words(
        words: list[dict],
        max_words: int = 6,
        max_duration: float = 3.0,
    ) -> list[dict]:
        groups = []
        current = []

        for word in words:
            if not current:
                current.append(word)
                continue

            current_duration = (
                word["end"] - current[0]["start"]
            )

            if (
                len(current) >= max_words
                or current_duration > max_duration
            ):
                groups.append(
                    {
                        "start": current[0]["start"],
                        "end": current[-1]["end"],
                        "text": " ".join(
                            item["word"].strip()
                            for item in current
                        ),
                    }
                )

                current = [word]
            else:
                current.append(word)

        if current:
            groups.append(
                {
                    "start": current[0]["start"],
                    "end": current[-1]["end"],
                    "text": " ".join(
                        item["word"].strip()
                        for item in current
                    ),
                }
            )

        return groups

    def generate_srt(
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

            audio = whisperx.load_audio(
                str(audio_path)
            )

            if self.model is None:
                self.model = whisperx.load_model(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                )

            result = self.model.transcribe(
                
                audio,
                language = "en",
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

            words = aligned.get(
                "word_segments",
                [],
            )

            grouped = self._group_words(words)

            for subtitle in grouped:
                all_subtitles.append(
                    {
                        "start": (
                            subtitle["start"]
                            + scene_offset
                        ),
                        "end": (
                            subtitle["end"]
                            + scene_offset
                        ),
                        "text": subtitle["text"],
                    }
                )

            scene_offset += float(
                scene["duration_seconds"]
            )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as f:
            for index, subtitle in enumerate(
                all_subtitles,
                start=1,
            ):
                f.write(
                    f"{index}\n"
                    f"{self._format_timestamp(subtitle['start'])}"
                    f" --> "
                    f"{self._format_timestamp(subtitle['end'])}\n"
                    f"{subtitle['text']}\n\n"
                )

        return str(output_path)