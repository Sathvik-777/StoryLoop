import json
from pathlib import Path


def load_publish_parameter(path: str | Path) -> bool:
    """Read the Publish switch, failing closed when the file/value is invalid."""
    try:
        parameters = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False

    if not isinstance(parameters, dict):
        return False

    value = parameters.get("Publish", False)
    return value if isinstance(value, bool) else False
