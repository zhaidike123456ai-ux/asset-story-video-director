from __future__ import annotations

from pathlib import Path
from typing import Any

from .project import artifact_path, load_project, require_project, set_artifact
from .providers import make_provider, provider_info
from .utils import atomic_write_json, now_iso, new_id, read_json


def _save_job(root: Path, job: dict[str, Any]) -> None:
    atomic_write_json(root / "jobs" / f"{job['job_id']}.json", job)


def _run_unit(root: Path, unit: dict[str, Any], provider_name: str, config_path: str | Path | None, confirm: bool, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    if provider_name != "mock" and not confirm:
        raise PermissionError("real provider execution requires --confirm-paid-operation")
    provider = make_provider(provider_name, config_path)
    info = provider.get_capabilities()
    if not info.get("available"):
        raise RuntimeError(info.get("error", f"provider unavailable: {provider_name}"))
    timestamp = now_iso()
    job = existing or {
        "job_id": new_id("job"), "project_id": load_project(root)["project_id"],
        "story_id": unit.get("story_id", ""), "segment_id": unit["segment_id"],
        "shot_id": unit["shot_ids"][0], "provider": provider_name,
        "model": unit.get("parameters", {}).get("model", "configured"),
        "prompt": unit["prompt"], "assets": unit.get("assets", []),
        "parameters": unit.get("parameters", {}), "task_id": "", "status": "created",
        "attempt": 1, "created_at": timestamp, "updated_at": timestamp,
        "output_path": "", "error": "",
    }
    try:
        task_id = provider.submit_generation(job["prompt"], job["assets"], job["parameters"])
        job.update({"task_id": task_id, "status": "submitted", "updated_at": now_iso()})
        _save_job(root, job)
        status = provider.get_task_status(task_id)
        job.update({"status": status.get("status", "running"), "updated_at": now_iso()})
        if job["status"] == "succeeded":
            output = root / "outputs" / f"{job['job_id']}.json"
            job["output_path"] = str(output.relative_to(root))
            provider.download_result(task_id, str(output))
        _save_job(root, job)
    except Exception as exc:
        job.update({"status": "failed" if provider_name == "mock" else "provider_unavailable", "error": str(exc), "updated_at": now_iso()})
        _save_job(root, job)
    return job


def generate_jobs(project_path: str | Path, provider_name: str, config_path: str | Path | None = None, confirm: bool = False) -> dict[str, Any]:
    root = require_project(project_path)
    compiled = read_json(artifact_path(root, "compiled_prompts"))
    units = [{**unit, "story_id": compiled.get("story_id", "")} for unit in compiled.get("units", [])]
    jobs = [_run_unit(root, unit, provider_name, config_path, confirm) for unit in units]
    set_artifact(root, "jobs", "jobs", "generated" if jobs and all(j["status"] == "succeeded" for j in jobs) else "generation_partial")
    return {"project_id": load_project(root)["project_id"], "provider": provider_name, "jobs": jobs}


def list_jobs(project_path: str | Path) -> dict[str, Any]:
    root = require_project(project_path)
    jobs = [read_json(path) for path in sorted((root / "jobs").glob("job_*.json"))]
    return {"project_id": load_project(root)["project_id"], "jobs": jobs}


def retry_job(project_path: str | Path, job_id: str, provider_name: str, config_path: str | Path | None = None, confirm: bool = False) -> dict[str, Any]:
    root = require_project(project_path)
    path = root / "jobs" / f"{job_id}.json"
    job = read_json(path)
    if job.get("status") not in {"failed", "provider_unavailable"}:
        raise ValueError(f"job is not retryable: {job.get('status')}")
    job["attempt"] = int(job.get("attempt", 1)) + 1
    unit = {"segment_id": job["segment_id"], "shot_ids": [job["shot_id"]], "prompt": job["prompt"], "assets": job["assets"], "parameters": job["parameters"]}
    return _run_unit(root, unit, provider_name, config_path, confirm, job)
