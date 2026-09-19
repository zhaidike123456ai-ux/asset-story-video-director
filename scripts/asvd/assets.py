from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .project import load_project, require_project, set_artifact
from .utils import atomic_write_json, now_iso, read_json, require_fields


ASSET_TYPES = {
    "character",
    "scene",
    "prop",
    "product",
    "environment",
    "style_reference",
    "unknown",
}

TYPE_KEYWORDS = {
    "character": ("角色", "人物", "小熊", "小猫", "character", "person"),
    "scene": ("场景", "庭院", "厨房", "scene", "room"),
    "prop": ("道具", "篮", "锅", "勺", "prop", "tool"),
    "product": ("产品", "product", "package", "包装"),
    "environment": ("环境", "花园", "environment", "landscape"),
    "style_reference": ("风格", "style", "reference"),
}


def infer_asset_type(descriptor: dict[str, Any]) -> str:
    explicit = str(descriptor.get("asset_type", "")).strip().lower()
    if explicit in ASSET_TYPES:
        return explicit
    haystack = " ".join(
        str(descriptor.get(key, "")) for key in ("description", "source", "name")
    ).lower()
    matches = [
        asset_type
        for asset_type, keywords in TYPE_KEYWORDS.items()
        if any(keyword.lower() in haystack for keyword in keywords)
    ]
    return matches[0] if len(matches) == 1 else "unknown"


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    raise ValueError("expected string or list of strings")


def _normalize_asset(
    descriptor: dict[str, Any], asset_id: str, asset_type: str
) -> dict[str, Any]:
    source = str(descriptor.get("source", "")).strip()
    description = str(descriptor.get("description", "")).strip()
    asset = {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "tier": str(descriptor.get("tier", "A")).upper(),
        "description": description,
        "visual_identity": _as_string_list(descriptor.get("visual_identity")),
        "must_keep_features": _as_string_list(descriptor.get("must_keep_features")),
        "flexible_features": _as_string_list(descriptor.get("flexible_features")),
        "possible_actions": _as_string_list(descriptor.get("possible_actions")),
        "possible_story_functions": _as_string_list(
            descriptor.get("possible_story_functions")
        ),
        "relationships": descriptor.get("relationships", []),
        "source": source,
        "needs_visual_review": bool(
            descriptor.get("needs_visual_review", asset_type == "unknown" or not description)
        ),
    }
    if asset["tier"] not in {"A", "B", "C"}:
        raise ValueError(f"invalid asset tier for {asset_id}: {asset['tier']}")

    extension_fields = {
        "character": (
            "appearance",
            "costume",
            "body_proportions",
            "personality_possibilities",
            "movement_traits",
            "suitable_story_roles",
        ),
        "scene": (
            "location",
            "time_feel",
            "season",
            "atmosphere",
            "possible_behaviors",
            "spatial_constraints",
        ),
        "environment": (
            "location",
            "time_feel",
            "season",
            "atmosphere",
            "possible_behaviors",
            "spatial_constraints",
        ),
        "prop": (
            "purpose",
            "interactions",
            "can_drive_plot",
            "visual_memory_potential",
        ),
        "product": (
            "purpose",
            "interactions",
            "can_drive_plot",
            "visual_memory_potential",
        ),
    }
    for field in extension_fields.get(asset_type, ()):
        default: Any = False if field == "can_drive_plot" else []
        if field in {"location", "time_feel", "season", "atmosphere", "purpose"}:
            default = ""
        asset[field] = descriptor.get(field, default)
    return asset


def analyze_assets(project_path: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    root = require_project(project_path)
    project = load_project(root)
    descriptors = read_json(manifest_path)
    if not isinstance(descriptors, list) or not descriptors:
        raise ValueError("asset manifest must be a non-empty JSON array")
    for index, descriptor in enumerate(descriptors, 1):
        if not isinstance(descriptor, dict):
            raise ValueError(f"asset descriptor {index} must be an object")
        require_fields(descriptor, ["source"], f"asset descriptor {index}")

    current_path = root / "assets" / "asset_bible.json"
    existing = read_json(current_path) if current_path.exists() else {"assets": []}
    existing_by_source = {
        item["source"]: item["asset_id"]
        for item in existing.get("assets", [])
        if item.get("source") and item.get("asset_id")
    }
    counters = Counter()
    for item in existing.get("assets", []):
        try:
            prefix, number = item["asset_id"].rsplit("_", 1)
            counters[prefix] = max(counters[prefix], int(number))
        except (KeyError, ValueError):
            continue

    normalized: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    for descriptor in descriptors:
        source = str(descriptor["source"]).strip()
        if not source:
            raise ValueError("asset source cannot be empty")
        if source in seen_sources:
            raise ValueError(f"duplicate asset source: {source}")
        seen_sources.add(source)
        asset_type = infer_asset_type(descriptor)
        asset_id = existing_by_source.get(source)
        if not asset_id:
            counters[asset_type] += 1
            asset_id = f"{asset_type}_{counters[asset_type]:03d}"
        normalized.append(_normalize_asset(descriptor, asset_id, asset_type))

    ids = [item["asset_id"] for item in normalized]
    checks = {
        "passed": not any(item["needs_visual_review"] for item in normalized),
        "asset_count": len(normalized),
        "unknown_asset_ids": [
            item["asset_id"] for item in normalized if item["asset_type"] == "unknown"
        ],
        "needs_visual_review": [
            item["asset_id"] for item in normalized if item["needs_visual_review"]
        ],
        "duplicate_ids": sorted({asset_id for asset_id in ids if ids.count(asset_id) > 1}),
    }
    timestamp = now_iso()
    bible = {
        "schema_version": "1.0",
        "project_id": project["project_id"],
        "assets": normalized,
        "checks": checks,
        "created_at": existing.get("created_at", timestamp),
        "updated_at": timestamp,
    }
    atomic_write_json(current_path, bible)
    set_artifact(root, "asset_bible", "assets/asset_bible.json", "assets_analyzed")
    return bible
