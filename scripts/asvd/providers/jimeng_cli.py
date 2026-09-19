from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from ..utils import deep_get


class JimengCLIProvider:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.capabilities = dict(config.get("capabilities") or {})
        self.commands = config.get("commands") or {}
        self.fields = config.get("response_fields") or {}
        self.status_map = config.get("status_map") or {}

    def get_capabilities(self) -> dict[str, Any]:
        caps = {"provider": "jimeng", "available": False, **self.capabilities}
        executable = self.config.get("executable")
        if self.config.get("enabled") and executable and not str(executable).startswith("REPLACE_WITH"):
            caps["available"] = bool(Path(str(executable)).exists() or os.path.sep not in str(executable))
        if not caps["available"]:
            caps["error"] = "Jimeng adapter is disabled or executable is not configured"
        return caps

    def _run(self, command_name: str, values: dict[str, Any]) -> dict[str, Any]:
        executable = self.config.get("executable")
        command = self.commands.get(command_name) or []
        if not executable or not command:
            raise RuntimeError(f"Jimeng {command_name} command is not configured")
        args = [str(executable)] + [str(item).format(**values) for item in command]
        completed = subprocess.run(args, check=False, capture_output=True, text=True, env=os.environ.copy())
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip() or f"Jimeng {command_name} exited {completed.returncode}")
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Jimeng {command_name} did not return JSON") from exc

    def submit_generation(self, prompt: str, assets: list[str], parameters: dict[str, Any]) -> str:
        response = self._run("submit", {"prompt": prompt, "assets_json": json.dumps(assets), **parameters})
        task_id = deep_get(response, self.fields.get("task_id", "task_id"))
        if not task_id:
            raise RuntimeError("Jimeng response did not contain task_id")
        return str(task_id)

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        response = self._run("status", {"task_id": task_id})
        raw = deep_get(response, self.fields.get("status", "status"), "unknown")
        return {"task_id": task_id, "status": self.status_map.get(str(raw), str(raw)), "response": response}

    def download_result(self, task_id: str, output_path: str) -> str:
        response = self._run("download", {"task_id": task_id, "output_path": output_path})
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return output_path

    def cancel_task(self, task_id: str) -> bool:
        if not self.commands.get("cancel"):
            return False
        self._run("cancel", {"task_id": task_id})
        return True
