from pathlib import Path
import json
import whisperx


PROJECT_ROOT = Path(__file__).resolve().parents[2]

AUDIO_DIR = (
    PROJECT_ROOT
    / "output"
    / "current_run"
    / "rendered"
    / "audio"
)

NARRATION_PLAN = (
    PROJECT_ROOT
    / "output"
    / "current_run"
    / "08_narration_plan.json"
)

OUTPUT_SRT = (
    PROJECT_ROOT
    / "output"
    / "current_run"
    / "subtitle_test.srt"
)


def format_timestamp(seconds: float) -> str:
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


def main():
    print("=== Subtitle Gate ===")

    with open(NARRATION_PLAN, "r", encoding="utf-8") as f:
        narration_plan = json.load(f)

    scene = narration_plan[0]

    audio_path = Path(scene["audio_path"])
    narration_text = scene["narration_text"]

    if not audio_path.is_absolute():
        audio_path = PROJECT_ROOT / audio_path

    print(f"Audio: {audio_path}")
    print(f"Text: {narration_text}")
    print()

    print("Loading WhisperX model...")

    device = "cpu"
    compute_type = "int8"

    model = whisperx.load_model(
        "base",
        device=device,
        compute_type=compute_type,
    )

    print("Model loaded.")
    print("Transcribing audio...")

    audio = whisperx.load_audio(str(audio_path))

    result = model.transcribe(
        audio,
        batch_size=4,
    )

    print("Transcription complete.")
    print("Loading alignment model...")

    language = result["language"]

    model_a, metadata = whisperx.load_align_model(
        language_code=language,
        device=device,
    )

    print("Alignment model loaded.")
    print("Aligning narration...")

    aligned = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    print("Alignment complete.")

    words = aligned.get("word_segments", [])

    if not words:
        print()
        print("FAIL: No word timestamps produced.")
        return

    print(f"Word timestamps produced: {len(words)}")

    with open(OUTPUT_SRT, "w", encoding="utf-8") as f:
        subtitle_number = 1

        for word in words:
            start = word.get("start")
            end = word.get("end")
            text = word.get("word", "").strip()

            if start is None or end is None or not text:
                continue

            f.write(f"{subtitle_number}\n")
            f.write(
                f"{format_timestamp(start)} --> "
                f"{format_timestamp(end)}\n"
            )
            f.write(f"{text}\n\n")

            subtitle_number += 1

    print()
    print("=== RESULT ===")
    print(f"PASS: {len(words)} word timestamps generated.")
    print(f"SRT: {OUTPUT_SRT}")


if __name__ == "__main__":
    main()