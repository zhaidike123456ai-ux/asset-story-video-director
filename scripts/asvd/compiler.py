from __future__ import annotations

from pathlib import Path
from typing import Any

from .project import artifact_path, load_project, require_project, set_artifact
from .providers import provider_info
from .utils import atomic_write_json, now_iso, read_json


def _prompt(shot: dict[str, Any], style: str) -> str:
    return (
        f"{style}. Subject: {shot['subject']}. Action: {shot['action']}. "
        f"Environment response: {shot['environment_action']}. Camera: {shot['camera']}; "
        f"movement: {shot['camera_movement']}; composition: {shot['composition']}. "
        "Preserve the identity of every referenced asset and show a clear beginning-to-end change."
    )


def compile_prompts(project_path: str | Path, provider: str = "mock", config_path: str | Path | None = None) -> dict[str, Any]:
    root = require_project(project_path)
    plan = read_json(artifact_path(root, "director_plan"))
    capabilities = provider_info(provider, config_path)
    if not capabilities.get("available") and provider != "mock":
        raise RuntimeError(capabilities.get("error", f"provider unavailable: {provider}"))
    max_duration = capabilities.get("max_duration")
    if not isinstance(max_duration, int) or max_duration < 1:
        raise ValueError("provider max_duration must be a positive integer before compilation")
    units: list[dict[str, Any]] = []
    for shot in plan["shots"]:
        remaining = int(shot["duration"])
        part = 1
        while remaining:
            seconds = min(remaining, max_duration)
            unit_id = f"unit_{len(units) + 1:03d}"
            units.append({
                "unit_id": unit_id,
                "segment_id": shot["segment_id"],
                "shot_ids": [shot["shot_id"]],
                "duration": seconds,
                "prompt": _prompt(shot, plan["target"].get("style", "")),
                "negative_constraints": ["identity drift", "extra characters", "static pose", "unmotivated scene change"],
                "assets": shot.get("asset_ids", []),
                "parameters": {"ratio": plan["target"].get("ratio", "9:16"), "resolution": plan["target"].get("resolution", ""), "model": "mock" if provider == "mock" else "configured"},
                "part": part,
            })
            remaining -= seconds
            part += 1
    payload = {
        "schema_version": "1.0",
        "project_id": load_project(root)["project_id"],
        "story_id": plan["story_id"],
        "provider": provider,
        "capabilities": capabilities,
        "units": units,
        "checks": {"passed": bool(units), "unit_count": len(units), "duration_sum": sum(u["duration"] for u in units)},
        "created_at": now_iso(),
    }
    atomic_write_json(root / "prompts" / "compiled.json", payload)
    set_artifact(root, "compiled_prompts", "prompts/compiled.json", "prompts_compiled")
    return payload
