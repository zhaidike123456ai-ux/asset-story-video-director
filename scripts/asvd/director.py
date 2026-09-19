from __future__ import annotations

from pathlib import Path
from typing import Any

from .project import artifact_path, load_project, require_project, set_artifact
from .utils import atomic_write_json, now_iso, read_json


def _durations(total: int, count: int) -> list[int]:
    if total < 1:
        raise ValueError("duration must be positive")
    count = min(max(1, count), total)
    base, remainder = divmod(total, count)
    return [base + (1 if i < remainder else 0) for i in range(count)]


def create_plan(project_path: str | Path, target: dict[str, Any]) -> dict[str, Any]:
    root = require_project(project_path)
    developed = read_json(artifact_path(root, "developed_story"))
    bible = read_json(artifact_path(root, "asset_bible"))
    duration = int(target.get("duration", 0))
    structure = list(developed.get("story_structure") or ["开始", "发展", "完成"])
    durations = _durations(duration, len(structure))
    primary_assets = [a["asset_id"] for a in bible.get("assets", []) if a.get("tier") == "A"]
    shots: list[dict[str, Any]] = []
    for index, (beat, shot_duration) in enumerate(zip(structure, durations), 1):
        action = f"围绕“{beat}”完成一个可观察的动作变化"
        shots.append({
            "shot_id": f"shot_{index:03d}",
            "segment_id": f"segment_{index:03d}",
            "duration": shot_duration,
            "shot_size": "特写" if index in {1, len(structure)} else "中景",
            "subject": developed.get("protagonist_goal", "主角"),
            "action": action,
            "environment_action": "环境对动作给出可见回应，例如光线、材质、蒸汽、风或状态变化",
            "camera": "保持主资产可辨识，优先稳定视线和连续空间",
            "camera_movement": "缓慢推进" if index == 1 else "轻微跟随或静稳观察",
            "composition": "主体清晰，动作方向明确，保留前后状态对照",
            "emotion_function": (developed.get("emotion_curve") or ["投入"])[min(index - 1, len(developed.get("emotion_curve") or ["投入"]) - 1)],
            "story_function": beat,
            "asset_ids": primary_assets,
            "sound_effect": "动作同步的轻微环境声" if target.get("action_sfx") else "",
            "dialogue": "" if not target.get("voice") else "可选旁白，解释当前微小目标",
            "subtitle": "" if not target.get("subtitles") else beat,
            "transition": "自然连续切换",
            "generation_notes": [target.get("style", ""), "避免新增未声明关键资产"],
        })
    plan = {
        "schema_version": "1.0",
        "project_id": load_project(root)["project_id"],
        "story_id": developed["story_id"],
        "target": target,
        "treatment": {
            "title": developed.get("complete_synopsis", ""),
            "style": target.get("style", ""),
            "platform": target.get("platform", ""),
            "visual_memory": developed.get("core_visual_memory", []),
            "continuity_rules": ["保持角色、场景和关键道具身份一致", "每个镜头必须有状态变化"],
        },
        "shots": shots,
        "checks": {
            "passed": sum(s["duration"] for s in shots) == duration and all(s["action"] for s in shots),
            "duration_sum": sum(s["duration"] for s in shots),
            "target_duration": duration,
            "all_shots_have_action": all(s["action"] for s in shots),
            "asset_ids_resolve": all(a in {x["asset_id"] for x in bible.get("assets", [])} for s in shots for a in s["asset_ids"]),
        },
        "created_at": now_iso(),
    }
    atomic_write_json(root / "director" / "plan.json", plan)
    set_artifact(root, "director_plan", "director/plan.json", "directed")
    return plan
