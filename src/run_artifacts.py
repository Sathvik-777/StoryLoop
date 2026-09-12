import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_DIR = PROJECT_ROOT / "output" / "current_run"
GENERATED_DIRS = (
    RUN_DIR,
    PROJECT_ROOT / "output" / "rendered",
    PROJECT_ROOT / "output" / "published",
    PROJECT_ROOT / "memory",
)


def _clear_contents(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for child in directory.iterdir():
        if child.is_dir():
            _clear_contents(child)
        else:
            child.unlink()


def reset_run() -> Path:
    for directory in GENERATED_DIRS:
        _clear_contents(directory)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    return RUN_DIR


def save_json(relative_path: str, value: Any) -> Path:
    path = RUN_DIR / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    return path


def save_text(relative_path: str, value: str) -> Path:
    path = RUN_DIR / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return path