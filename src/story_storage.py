from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MEMORY_DIR = PROJECT_ROOT / "memory"
PUBLISHED_DIR = PROJECT_ROOT / "output" / "published"


def create_directories():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)


def save_story_record(revision_history, final_story, final_evaluation):
    create_directories()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    memory_file = MEMORY_DIR / f"story_{timestamp}.txt"
    published_file = PUBLISHED_DIR / f"story_{timestamp}.txt"

    with open(memory_file, "w", encoding="utf-8") as file:

        file.write("STORYLOOP GENERATION RECORD\n")
        file.write("=" * 60 + "\n\n")

        file.write("FINAL STATUS: PUBLISHED\n")
        file.write(f"TOTAL VERSIONS: {len(revision_history)}\n")
        file.write(f"FINAL SCORE: {final_evaluation['overall_score']}\n\n")

        for record in revision_history:

            file.write(
                f"VERSION {record['version']}\n"
            )
            file.write("-" * 40 + "\n\n")

            file.write("STORY:\n")
            file.write(record["story"])
            file.write("\n\n")

            evaluation = record["evaluation"]

            file.write("EVALUATION:\n")

            for key, value in evaluation.items():
                if key not in ["strengths", "weaknesses", "improvement"]:
                    file.write(f"{key}: {value}\n")

            file.write("\nSTRENGTHS:\n")

            for strength in evaluation["strengths"]:
                file.write(f"- {strength}\n")

            file.write("\nWEAKNESSES:\n")

            for weakness in evaluation["weaknesses"]:
                file.write(f"- {weakness}\n")

            file.write("\nIMPROVEMENT:\n")
            file.write(evaluation["improvement"])
            file.write("\n\n")

        file.write("=" * 60 + "\n")
        file.write("FINAL PUBLISHED STORY\n")
        file.write("=" * 60 + "\n\n")
        file.write(final_story)

    # Published folder contains ONLY the accepted story.
    with open(published_file, "w", encoding="utf-8") as file:
        file.write(final_story)

    return memory_file, published_file