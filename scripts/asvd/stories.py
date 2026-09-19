from __future__ import annotations

from pathlib import Path
from typing import Any

from .project import artifact_path, load_project, require_project, set_artifact, update_project
from .story_types import load_story_types
from .utils import atomic_write_json, now_iso, read_json


HEALING_TERMS = ("治愈", "温暖", "放松", "生活", "healing", "cozy")
SETBACK_TERMS = ("受挫", "善意", "补偿", "弱小", "保护欲", "kindness", "setback")


def _asset_groups(asset_bible: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for asset in asset_bible.get("assets", []):
        groups.setdefault(asset["asset_type"], []).append(asset)
    return groups


def route_story_types(
    asset_bible: dict[str, Any], request: str, duration: int | None = None
) -> dict[str, Any]:
    library = load_story_types()
    groups = _asset_groups(asset_bible)
    request_lower = request.lower()
    scores: dict[str, int] = {story_type: 0 for story_type in library}
    reasons: dict[str, list[str]] = {story_type: [] for story_type in library}

    if "TYPE_01" in scores:
        if groups.get("character"):
            scores["TYPE_01"] += 2
            reasons["TYPE_01"].append("有可持续执行动作的角色")
        if groups.get("prop") or groups.get("product"):
            scores["TYPE_01"] += 3
            reasons["TYPE_01"].append("有可展示过程的道具/产品")
        if groups.get("scene") or groups.get("environment"):
            scores["TYPE_01"] += 2
            reasons["TYPE_01"].append("有稳定的生活场景")
        if any(term in request_lower for term in HEALING_TERMS):
            scores["TYPE_01"] += 5
            reasons["TYPE_01"].append("用户要求治愈/生活情绪")

    if "TYPE_02" in scores:
        characters_text = " ".join(
            asset.get("description", "")
            + " "
            + " ".join(asset.get("personality_possibilities", []))
            for asset in groups.get("character", [])
        ).lower()
        if any(term in request_lower for term in SETBACK_TERMS):
            scores["TYPE_02"] += 5
            reasons["TYPE_02"].append("用户明确要求受挫/善意结构")
        if any(term in characters_text for term in ("弱小", "丑萌", "胆小", "保护", "tiny", "shy")):
            scores["TYPE_02"] += 4
            reasons["TYPE_02"].append("角色气质适合保护欲与情绪反转")
        if len(groups.get("character", [])) >= 2:
            scores["TYPE_02"] += 2
            reasons["TYPE_02"].append("已有可承担善意功能的角色")
        elif groups.get("character"):
            reasons["TYPE_02"].append("可用，但善意角色需声明为新资产")

    if duration and duration <= 20:
        scores["TYPE_01"] = scores.get("TYPE_01", 0) + 1
        reasons.setdefault("TYPE_01", []).append("短时长更适合单任务可视化")

    ranked = sorted(scores, key=lambda key: (-scores[key], key))
    return {
        "request": request,
        "duration": duration,
        "ranked_story_types": [
            {
                "story_type": story_type,
                "score": scores[story_type],
                "reasons": reasons[story_type],
            }
            for story_type in ranked
        ],
        "recommended": ranked[0] if ranked else None,
        "created_at": now_iso(),
    }


def _pick_context(asset_bible: dict[str, Any]) -> dict[str, Any]:
    groups = _asset_groups(asset_bible)
    character = (groups.get("character") or groups.get("unknown") or [{}])[0]
    scene = (groups.get("scene") or groups.get("environment") or [{}])[0]
    props = groups.get("prop", []) + groups.get("product", [])
    prop = props[0] if props else {}
    all_primary = [asset for asset in asset_bible.get("assets", []) if asset.get("tier") == "A"]
    return {
        "character": character,
        "scene": scene,
        "prop": prop,
        "character_name": character.get("description") or "主角",
        "scene_name": scene.get("description") or "现有场景",
        "prop_name": prop.get("description") or "现有材料与道具",
        "required_assets": [asset["asset_id"] for asset in all_primary],
        "character_count": len(groups.get("character", [])),
        "has_helper": len(groups.get("character", [])) >= 2,
    }


def _production_feasibility(
    character_count: int, new_assets: list[dict[str, Any]], complexity: str, structure: list[str]
) -> dict[str, Any]:
    score = 100
    risks: list[str] = []
    if character_count > 2:
        score -= 15 * (character_count - 2)
        risks.append("多角色一致性与交互难度上升")
    if new_assets:
        score -= 8 * len(new_assets)
        risks.append("需先补齐新的关键资产")
    if complexity == "medium":
        score -= 12
    elif complexity == "high":
        score -= 30
        risks.append("包含高复杂度动作或空间连续性")
    if len(structure) > 9:
        score -= 8
        risks.append("节点较多，短时长中易信息过载")
    score = max(0, score)
    return {
        "score": score,
        "level": "high" if score >= 80 else "medium" if score >= 60 else "low",
        "checks": {
            "character_count": character_count,
            "new_key_asset_count": len(new_assets),
            "structure_node_count": len(structure),
            "complex_action_risk": complexity == "high",
            "hand_precision_risk": complexity != "low",
            "identity_consistency_risk": character_count > 1,
        },
        "mitigations": risks or ["保持单场景、单主角与清晰动作链"],
    }


def _blueprints(context: dict[str, Any]) -> list[dict[str, Any]]:
    char = context["character_name"]
    scene = context["scene_name"]
    prop = context["prop_name"]
    helper_need = [] if context["has_helper"] else [
        {
            "asset_id": "character_helper_001",
            "asset_type": "character",
            "description": "承担善意反转的辅助角色",
            "reason": "TYPE_02 的善意需要可视化来源",
        }
    ]
    return [
        {
            "title": "一件小事的仪式",
            "story_type": "TYPE_01",
            "hook": f"{char}的第一个细微动作，让{scene}慢慢醒来。",
            "goal": f"用{prop}完成一件期待已久的小事",
            "summary": f"{char}在{scene}从准备、执行到完成，一步步把{prop}转化成可见的成果。",
            "structure": ["小愿望", "准备", "获取材料", "行动 / 制作", "变化过程", "完成", "享受成果"],
            "emotion": ["平静", "投入", "连续反馈", "满足"],
            "visual": ["细节动作链", "材料状态变化", "完成瞬间的质感揭示"],
            "ending": "主角放慢动作，在原场景中安静享受成果。",
            "new_assets": [],
            "difficulty": "low",
            "risk": ["手部精细操作需拆成简短动作"],
        },
        {
            "title": "被忽略的角落",
            "story_type": "ASSET_ORIGINAL",
            "hook": f"{char}发现{scene}里有一处细小变化，决定用行动回应它。",
            "goal": "照料一个容易被忽略的小角落",
            "summary": f"{char}在{scene}循着一个微小迹象，用{prop}进行检查、整理和照料，最终让环境出现柔和的前后变化。",
            "structure": ["异常细节", "好奇靠近", "试探照料", "连续变化", "整体焕新", "安静守望"],
            "emotion": ["好奇", "专注", "温柔责任", "焕新"],
            "visual": ["微小迹象特写", "局部状态逐步变化", "前后对照"],
            "ending": "环境的回应成为奖励，主角没有占有它，只是笑着守望。",
            "new_assets": [],
            "difficulty": "low",
            "risk": ["变化需设计为模型可稳定表达的局部状态"],
        },
        {
            "title": "只差一点点",
            "story_type": "TYPE_02",
            "hook": f"{char}的愿望小得只需一点{prop}，却两次和它擦肩而过。",
            "goal": "获得一份很小、很具体的满足",
            "summary": f"{char}在{scene}为一个微小愿望尝试两次，第二次的失败让它跌到情绪最低点；一份被看见的善意带来远超最初期待的回报。",
            "structure": ["小愿望", "第一次尝试", "第一次失败", "再次尝试", "更大挫折", "情绪最低点", "善意出现", "超预期奖励", "温暖结尾"],
            "emotion": ["期待", "失落", "希望", "更大失落", "最低点", "温暖", "释放"],
            "visual": ["愿望物特写", "两次不同的失败", "超预期奖励揭示"],
            "ending": "主角把超出所需的那一部分分享出去，善意形成闭环。",
            "new_assets": helper_need,
            "difficulty": "medium",
            "risk": ["需避免复杂多角色肢体交互", "两次挫折要在视觉上有差异"],
            "payoff": {"initial_expectation_scale": 1, "reward_scale": 3},
        },
        {
            "title": "一份不说出口的礼物",
            "story_type": "TYPE_01",
            "hook": f"{char}一直把快完成的成果藏到画面边缘，直到最后才揭示用途。",
            "goal": "为现有世界中的某个对象准备一份惊喜",
            "summary": f"{char}在{scene}悄悄整理{prop}，制作过程不断给出线索，最终通过摆放位置和角色反应揭示这是一份礼物。",
            "structure": ["藏住目的", "挑选材料", "耐心制作", "小意外修正", "悄悄摆放", "用途揭示"],
            "emotion": ["秘密感", "投入", "轻微紧张", "温暖揭示"],
            "visual": ["画外藏物", "过程线索", "最终摆放构图"],
            "ending": "不用台词，仅用对象的动作反应完成情绪回报。",
            "new_assets": [],
            "difficulty": "low",
            "risk": ["礼物对象必须是现有资产，否则需降级为留言/摆放结尾"],
        },
        {
            "title": "跟着光走一圈",
            "story_type": "ASSET_ORIGINAL",
            "hook": f"一束移动的光成为镜头向导，带{char}重新发现{scene}。",
            "goal": "在熟悉场景里找到一个新的观察方式",
            "summary": f"{char}被{scene}中光影的缓慢移动吸引，带着{prop}经过三个不同局部，每一处都触发一个小动作和一次新发现。",
            "structure": ["光影钩子", "第一次跟随", "第二处发现", "第三处变化", "光影回到起点", "形成环形结尾"],
            "emotion": ["被吸引", "好奇", "小惊喜累积", "宁静完整"],
            "visual": ["光影移动", "同场景多局部探索", "首尾构图呼应"],
            "ending": "镜头回到开场构图，但场景已多了主角留下的细小痕迹。",
            "new_assets": [],
            "difficulty": "low",
            "risk": ["需固定场景布局，以光影变化替代大幅空间跳转"],
        },
        {
            "title": "小小的失败展览",
            "story_type": "ASSET_ORIGINAL",
            "hook": f"{char}不把失败藏起来，反而把它们排成一列。",
            "goal": "把一次不完美的过程变成可爱的成果",
            "summary": f"{char}在{scene}使用{prop}时连续得到几个不完美的结果，它不重来清零，而是通过排列、命名和布置把缺陷变成一次小展览。",
            "structure": ["第一个小失败", "试着修正", "出现另一种缺陷", "改变目标", "排列布置", "重新理解完成"],
            "emotion": ["小尴尬", "认真", "释然", "自得其乐"],
            "visual": ["不同缺陷的形状", "排列过程", "展览式全景"],
            "ending": "主角给最不完美的那一个留出画面中心。",
            "new_assets": [],
            "difficulty": "low",
            "risk": ["失败结果应是视觉可控的形变，不设计破坏性灾难"],
        },
        {
            "title": "等候变成了故事",
            "story_type": "TYPE_01",
            "hook": f"{char}需要等待一个变化，于是把空白时间变成一组小任务。",
            "goal": "耐心完成一个需要时间的过程",
            "summary": f"{char}在{scene}完成第一步后需要等待；它转而整理{prop}、观察光影、记录细小变化，等待本身变成富有节奏的生活。",
            "structure": ["启动过程", "第一次等待", "小任务一", "变化提示", "小任务二", "最终变化", "放慢享受"],
            "emotion": ["期待", "耐心", "生活感累积", "如期而至"],
            "visual": ["等待中的环境变化", "平行小动作", "最终状态揭示"],
            "ending": "主角没有立刻消耗成果，而是先坐下看了它一会儿。",
            "new_assets": [],
            "difficulty": "low",
            "risk": ["通过明确环境变化避免等待镜头静态化"],
        },
        {
            "title": "反过来用一次",
            "story_type": "ASSET_ORIGINAL",
            "hook": f"{char}把{prop}的常见用法反过来，意外解决了{scene}里的小难题。",
            "goal": "用现有资产发现一种非预期但合理的交互",
            "summary": f"{char}先按常规方式使用{prop}，发现无法达成目标；它观察形状和环境后换一个方向，让同一资产显示新功能。",
            "structure": ["常规用法", "轻微阻碍", "观察形状", "反向试用", "新功能生效", "幽默收尾"],
            "emotion": ["熟悉", "疑惑", "灵光", "轻快满足"],
            "visual": ["同道具的两种方向", "角色思考动作", "结果的反差"],
            "ending": "主角看一眼镜头，把道具留在新用法的位置上。",
            "new_assets": [],
            "difficulty": "medium",
            "risk": ["新用法必须符合物体形状和基本物理，不做超复杂变形"],
        },
    ]


def generate_stories(
    project_path: str | Path, request: str, count: int = 5, duration: int | None = None
) -> dict[str, Any]:
    if not 1 <= count <= 8:
        raise ValueError("story count must be between 1 and 8")
    root = require_project(project_path)
    asset_bible = read_json(artifact_path(root, "asset_bible"))
    if asset_bible.get("checks", {}).get("needs_visual_review"):
        raise ValueError("key assets still need visual review; update the Asset Bible first")
    router = route_story_types(asset_bible, request, duration)
    atomic_write_json(root / "stories" / "router.json", router)
    context = _pick_context(asset_bible)
    candidates: list[dict[str, Any]] = []
    for index, blueprint in enumerate(_blueprints(context)[:count], 1):
        feasibility = _production_feasibility(
            context["character_count"] + len(blueprint["new_assets"]),
            blueprint["new_assets"],
            blueprint["difficulty"],
            blueprint["structure"],
        )
        candidate = {
            "story_id": f"story_{index:03d}",
            "title": blueprint["title"],
            "story_type": blueprint["story_type"],
            "one_sentence_hook": blueprint["hook"],
            "story_summary": blueprint["summary"],
            "character_goal": blueprint["goal"],
            "story_structure": blueprint["structure"],
            "emotion_curve": blueprint["emotion"],
            "visual_highlights": blueprint["visual"],
            "ending": blueprint["ending"],
            "required_assets": context["required_assets"],
            "new_assets_needed": blueprint["new_assets"],
            "AI_generation_difficulty": blueprint["difficulty"],
            "production_risk": blueprint["risk"],
            "feasibility": feasibility,
        }
        if "payoff" in blueprint:
            candidate["payoff"] = blueprint["payoff"]
        candidates.append(candidate)

    signatures = {
        (item["story_type"], item["character_goal"], item["ending"], item["one_sentence_hook"])
        for item in candidates
    }
    checks = {
        "passed": len(signatures) == len(candidates),
        "candidate_count": len(candidates),
        "distinct_signature_count": len(signatures),
        "undeclared_key_assets": [],
        "has_visual_change": all(item["visual_highlights"] for item in candidates),
    }
    payload = {
        "schema_version": "1.0",
        "project_id": load_project(root)["project_id"],
        "request": request,
        "target_duration": duration,
        "router": router,
        "stories": candidates,
        "checks": checks,
        "created_at": now_iso(),
    }
    atomic_write_json(root / "stories" / "candidates.json", payload)
    order = [item["story_id"] for item in candidates]
    update_project(root, story_order=order, selected_story_id=None)
    set_artifact(root, "story_candidates", "stories/candidates.json", "stories_generated")
    set_artifact(root, "story_router", "stories/router.json")
    return payload


def select_story(
    project_path: str | Path, story_id: str | None = None, number: int | None = None
) -> dict[str, Any]:
    root = require_project(project_path)
    project = load_project(root)
    candidates_payload = read_json(artifact_path(root, "story_candidates"))
    by_id = {item["story_id"]: item for item in candidates_payload["stories"]}
    if number is not None:
        if number < 1 or number > len(project.get("story_order", [])):
            raise ValueError(f"story number out of range: {number}")
        story_id = project["story_order"][number - 1]
    if not story_id or story_id not in by_id:
        raise ValueError(f"unknown story_id: {story_id}")
    selected = by_id[story_id]
    atomic_write_json(root / "stories" / "selected.json", selected)
    update_project(root, selected_story_id=story_id)
    set_artifact(root, "selected_story", "stories/selected.json", "story_selected")
    return selected


def develop_story(project_path: str | Path) -> dict[str, Any]:
    root = require_project(project_path)
    story = read_json(artifact_path(root, "selected_story"))
    asset_bible = read_json(artifact_path(root, "asset_bible"))
    assets_by_id = {asset["asset_id"]: asset for asset in asset_bible["assets"]}
    asset_usage = {
        asset_id: {
            "story_function": (
                assets_by_id[asset_id].get("possible_story_functions") or ["故事中的核心可视资产"]
            )[0],
            "must_keep_features": assets_by_id[asset_id].get("must_keep_features", []),
        }
        for asset_id in story["required_assets"]
        if asset_id in assets_by_id
    }
    type_01 = story["story_type"] == "TYPE_01"
    conflict = (
        "非对抗性阻力：时间、材料状态和动作顺序推动观看，过程本身就是故事。"
        if type_01
        else story["story_structure"][2] if len(story["story_structure"]) > 2 else "目标遇到可视化阻力。"
    )
    development = {
        "schema_version": "1.0",
        "story_id": story["story_id"],
        "complete_synopsis": f"{story['one_sentence_hook']} {story['story_summary']} {story['ending']}",
        "protagonist_goal": story["character_goal"],
        "motivation": "将一个微小而具体的愿望变成可见的行动。",
        "conflict": conflict,
        "turning_point": story["story_structure"][len(story["story_structure"]) // 2],
        "climax": story["story_structure"][-2],
        "ending": story["ending"],
        "emotion_curve": story["emotion_curve"],
        "core_visual_memory": story["visual_highlights"],
        "theme": "微小行动与对世界的认真回应会积累成情绪奖励。",
        "asset_usage": asset_usage,
        "new_assets_needed": story["new_assets_needed"],
        "production_risks": story["production_risk"],
        "story_structure": story["story_structure"],
        "payoff": story.get("payoff"),
        "checks": {
            "asset_ids_resolved": len(asset_usage) == len(story["required_assets"]),
            "type_02_reward_valid": (
                story.get("story_type") != "TYPE_02"
                or story.get("payoff", {}).get("reward_scale", 0)
                > story.get("payoff", {}).get("initial_expectation_scale", 0)
            ),
            "new_key_assets_declared": True,
        },
        "created_at": now_iso(),
    }
    atomic_write_json(root / "stories" / "developed.json", development)
    set_artifact(root, "developed_story", "stories/developed.json", "story_developed")
    return development
