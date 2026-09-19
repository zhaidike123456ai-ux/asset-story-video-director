from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import atomic_write_json, now_iso, read_json, validate_project_id


PROJECT_DIRS = (
    "assets/source",
    "references",
    "stories",
    "director",
    "prompts",
    "jobs",
    "outputs",
)


def init_project(projects_root: str | Path, project_id: str, title: str = "") -> Path:
    project_id = validate_project_id(project_id)
    root = Path(projects_root).expanduser().resolve() / project_id
    if (root / "project.json").exists():
        raise FileExistsError(f"project already exists: {root}")
    for relative in PROJECT_DIRS:
        (root / relative).mkdir(parents=True, exist_ok=True)
    timestamp = now_iso()
    state = {
        "schema_version": "1.0",
        "project_id": project_id,
        "title": title or project_id,
        "stage": "initialized",
        "created_at": timestamp,
        "updated_at": timestamp,
        "story_order": [],
        "selected_story_id": None,
        "target": {},
        "artifacts": {},
    }
    atomic_write_json(root / "project.json", state)
    return root


def require_project(project_path: str | Path) -> Path:
    root = Path(project_path).expanduser().resolve()
    if not (root / "project.json").is_file():
        raise FileNotFoundError(f"not an ASVD project: {root}")
    return root


def load_project(project_path: str | Path) -> dict[str, Any]:
    root = require_project(project_path)
    state = read_json(root / "project.json")
    if state.get("project_id") != root.name:
        raise ValueError("project_id does not match project folder name")
    return state


def update_project(project_path: str | Path, **changes: Any) -> dict[str, Any]:
    root = require_project(project_path)
    state = load_project(root)
    state.update(changes)
    state["updated_at"] = now_iso()
    atomic_write_json(root / "project.json", state)
    return state


def set_artifact(
    project_path: str | Path, key: str, relative_path: str, stage: str | None = None
) -> dict[str, Any]:
    root = require_project(project_path)
    state = load_project(root)
    artifacts = dict(state.get("artifacts", {}))
    artifacts[key] = relative_path
    changes: dict[str, Any] = {"artifacts": artifacts}
    if stage:
        changes["stage"] = stage
    return update_project(root, **changes)


def artifact_path(project_path: str | Path, key: str) -> Path:
    root = require_project(project_path)
    state = load_project(root)
    relative = state.get("artifacts", {}).get(key)
    if not relative:
        raise FileNotFoundError(f"project has no {key} artifact")
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f"missing artifact for {key}: {path}")
    return path
