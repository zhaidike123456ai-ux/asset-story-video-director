from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import read_json


def default_story_type_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / "story_types"


def load_story_types(directory: str | Path | None = None) -> dict[str, dict[str, Any]]:
    root = Path(directory) if directory else default_story_type_dir()
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*.json")):
        item = read_json(path)
        story_type = item.get("story_type")
        if not story_type:
            raise ValueError(f"story type missing story_type: {path}")
        if story_type in result:
            raise ValueError(f"duplicate story type: {story_type}")
        result[story_type] = item
    if not result:
        raise FileNotFoundError(f"no story types found in {root}")
    return result
