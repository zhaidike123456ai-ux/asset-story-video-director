#!/usr/bin/env python3
"""Command line entry point for Asset Story Video Director."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from asvd.assets import analyze_assets
from asvd.compiler import compile_prompts
from asvd.director import create_plan
from asvd.jobs import generate_jobs, list_jobs, retry_job
from asvd.project import load_project, init_project
from asvd.providers import provider_info
from asvd.stories import develop_story, generate_stories, select_story
from asvd.utils import read_json


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _project_status(path: str) -> dict:
    state = load_project(path)
    return {"project": state, "project_path": str(Path(path).expanduser().resolve())}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Asset Story Video Director")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a project")
    init.add_argument("--projects-root", required=True)
    init.add_argument("--project-id", required=True)
    init.add_argument("--title", default="")

    status = sub.add_parser("status", help="show project state")
    status.add_argument("--project", required=True)

    analyze = sub.add_parser("analyze", help="build an Asset Bible")
    analyze.add_argument("--project", required=True)
    analyze.add_argument("--manifest", required=True)

    stories = sub.add_parser("stories", help="generate story candidates")
    stories.add_argument("--project", required=True)
    stories.add_argument("--request", required=True)
    stories.add_argument("--count", type=int, default=5)
    stories.add_argument("--duration", type=int)

    select = sub.add_parser("select", help="select one saved story")
    select.add_argument("--project", required=True)
    group = select.add_mutually_exclusive_group(required=True)
    group.add_argument("--number", type=int)
    group.add_argument("--story-id")

    develop = sub.add_parser("develop", help="develop the selected story")
    develop.add_argument("--project", required=True)

    plan = sub.add_parser("plan", help="create a director treatment and shot plan")
    plan.add_argument("--project", required=True)
    plan.add_argument("--duration", type=int, required=True)
    plan.add_argument("--ratio", default="9:16")
    plan.add_argument("--style", default="自然、电影感、保持资产身份")
    plan.add_argument("--platform", default="")
    plan.add_argument("--resolution", default="")
    plan.add_argument("--subtitles", action="store_true")
    plan.add_argument("--voice", action="store_true")
    plan.add_argument("--bgm", action="store_true")
    plan.add_argument("--ambience", action="store_true")
    plan.add_argument("--action-sfx", action="store_true")

    compile_cmd = sub.add_parser("compile", help="compile shots into provider units")
    compile_cmd.add_argument("--project", required=True)
    compile_cmd.add_argument("--provider", default="mock")
    compile_cmd.add_argument("--provider-config")

    info = sub.add_parser("provider-info", help="inspect provider capabilities")
    info.add_argument("--provider", default="mock")
    info.add_argument("--provider-config")

    generate = sub.add_parser("generate", help="submit compiled units")
    generate.add_argument("--project", required=True)
    generate.add_argument("--provider", default="mock")
    generate.add_argument("--provider-config")
    generate.add_argument("--confirm-paid-operation", action="store_true")

    jobs = sub.add_parser("jobs", help="list generation jobs")
    jobs.add_argument("--project", required=True)

    retry = sub.add_parser("retry", help="retry one failed job")
    retry.add_argument("--project", required=True)
    retry.add_argument("--job-id", required=True)
    retry.add_argument("--provider", default="mock")
    retry.add_argument("--provider-config")
    retry.add_argument("--confirm-paid-operation", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            _json({"project_path": str(init_project(args.projects_root, args.project_id, args.title))})
        elif args.command == "status":
            _json(_project_status(args.project))
        elif args.command == "analyze":
            _json(analyze_assets(args.project, args.manifest))
        elif args.command == "stories":
            _json(generate_stories(args.project, args.request, args.count, args.duration))
        elif args.command == "select":
            _json(select_story(args.project, args.story_id, args.number))
        elif args.command == "develop":
            _json(develop_story(args.project))
        elif args.command == "plan":
            _json(create_plan(args.project, {
                "duration": args.duration, "ratio": args.ratio, "style": args.style,
                "platform": args.platform, "resolution": args.resolution,
                "subtitles": args.subtitles, "voice": args.voice, "bgm": args.bgm,
                "ambience": args.ambience, "action_sfx": args.action_sfx,
            }))
        elif args.command == "compile":
            _json(compile_prompts(args.project, args.provider, args.provider_config))
        elif args.command == "provider-info":
            _json(provider_info(args.provider, args.provider_config))
        elif args.command == "generate":
            _json(generate_jobs(args.project, args.provider, args.provider_config, args.confirm_paid_operation))
        elif args.command == "jobs":
            _json(list_jobs(args.project))
        elif args.command == "retry":
            _json(retry_job(args.project, args.job_id, args.provider, args.provider_config, args.confirm_paid_operation))
        return 0
    except (FileNotFoundError, ValueError, PermissionError, RuntimeError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
