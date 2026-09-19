"""Installation and project health checks for the ASVD skill."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .project import PROJECT_DIRS, load_project, require_project


REQUIRED_FILES = (
    "SKILL.md",
    "scripts/asvd.py",
    "scripts/asvd/assets.py",
    "scripts/asvd/compiler.py",
    "scripts/asvd/director.py",
    "scripts/asvd/jobs.py",
    "scripts/asvd/providers/base.py",
    "scripts/asvd/providers/mock.py",
    "scripts/asvd/providers/jimeng_cli.py",
)


def _skill_root() -> Path:
    # .../asset-story-video-director/scripts/asvd/doctor.py
    return Path(__file__).resolve().parents[2]


def _check_files(root: Path) -> list[str]:
    return [relative for relative in REQUIRED_FILES if not (root / relative).is_file()]


def _repair_project(root: Path) -> list[str]:
    created: list[str] = []
    for relative in PROJECT_DIRS:
        path = root / relative
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(relative)
    return created


def inspect(skill_root: str | Path | None = None, project: str | Path | None = None,
            repair: bool = False) -> dict[str, Any]:
    """Return actionable health information without inventing story state."""
    root = Path(skill_root).expanduser().resolve() if skill_root else _skill_root()
    missing_files = _check_files(root)
    result: dict[str, Any] = {
        "skill_root": str(root),
        "skill_status": "ok" if not missing_files else "incomplete",
        "missing_skill_files": missing_files,
        "project": None,
        "repairable": ["project directories"] if project else [],
        "next_actions": [],
    }
    if missing_files:
        result["next_actions"].append(
            "Restore missing skill files from the published repository before running the workflow."
        )
    if project:
        project_root = Path(project).expanduser().resolve()
        project_info: dict[str, Any] = {"path": str(project_root)}
        try:
            state = load_project(project_root)
            missing_dirs = [relative for relative in PROJECT_DIRS if not (project_root / relative).is_dir()]
            created = _repair_project(project_root) if repair else []
            if created:
                missing_dirs = [relative for relative in missing_dirs if relative not in created]
            project_info.update({
                "status": "ok" if not missing_dirs else "incomplete",
                "stage": state.get("stage"),
                "missing_directories": missing_dirs,
                "created_directories": created,
            })
            if missing_dirs and not repair:
                result["next_actions"].append(
                    "Run doctor again with --repair to recreate only missing project directories."
                )
        except (FileNotFoundError, ValueError) as exc:
            project_info.update({"status": "invalid", "error": str(exc)})
            result["next_actions"].append(
                "Initialize a project with: python3 scripts/asvd.py init --projects-root ... --project-id ..."
            )
        result["project"] = project_info
    return result


def doctor(skill_root: str | Path | None = None, project: str | Path | None = None,
           repair: bool = False) -> dict[str, Any]:
    return inspect(skill_root, project, repair)
