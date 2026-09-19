from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MockProvider:
    def get_capabilities(self) -> dict[str, Any]:
        return {
            "provider": "mock", "available": True, "max_duration": 8,
            "supported_ratios": ["9:16", "16:9", "1:1"],
            "supported_resolutions": ["720p", "1080p"], "text_to_video": True,
            "image_to_video": True, "first_frame": True, "last_frame": True,
            "multi_image": True, "audio_support": False, "cancel_supported": True,
        }

    def submit_generation(self, prompt: str, assets: list[str], parameters: dict[str, Any]) -> str:
        return "mock_" + str(abs(hash((prompt, tuple(assets), tuple(sorted(parameters.items()))))))

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        return {"task_id": task_id, "status": "succeeded"}

    def download_result(self, task_id: str, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"provider": "mock", "task_id": task_id, "note": "mock artifact; no video credits spent"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return str(path)

    def cancel_task(self, task_id: str) -> bool:
        return True
