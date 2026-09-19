from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import VideoProvider
from .jimeng_cli import JimengCLIProvider
from .mock import MockProvider


def make_provider(name: str, config_path: str | Path | None = None) -> VideoProvider:
    if name == "mock":
        return MockProvider()
    if name == "jimeng":
        if not config_path:
            raise ValueError("jimeng requires --provider-config")
        return JimengCLIProvider(json.loads(Path(config_path).read_text(encoding="utf-8")))
    raise ValueError(f"unknown provider: {name}")


def provider_info(name: str, config_path: str | Path | None = None) -> dict[str, Any]:
    try:
        provider = make_provider(name, config_path)
        return provider.get_capabilities()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"provider": name, "available": False, "error": str(exc)}


__all__ = ["VideoProvider", "MockProvider", "JimengCLIProvider", "make_provider", "provider_info"]
