---
name: asset-story-video-director
description: Turn character, scene, prop, product, environment, style, and reference-video assets into production-aware short-video stories, developed treatments, shot plans, provider-specific prompts, and optional generation jobs. Use when a user asks for asset-driven AI story ideation, directing, storyboards, video prompts, or managed video generation; do not use for ordinary prose screenwriting without an asset or AI-video workflow.
---

# Asset Story Video Director

Build the story from the user's assets, then adapt it to the selected video provider. Preserve story/director state on disk so follow-ups such as “我喜欢3号” continue the same project.

## Operating boundary

- Treat user-provided key assets as tier A: prefer them, preserve their identity, and never silently replace them.
- Add ordinary non-story-changing objects as tier B when useful.
- Treat any new character, animal, vehicle, major location, building, or plot-critical prop as tier C. List it under `new_assets_needed` before using it.
- Optimize hook, progression, visual memory, emotional curve, and payoff; never promise popularity.
- Do not force a three-act structure or conflict onto healing/process stories.
- Keep story logic, directing, prompt compilation, and provider invocation separate.
- Do not hard-code a model duration limit. Read provider capabilities before segmenting shots.
- Never place API keys, cookies, or tokens in project files or prompts.
- `story` and `plan` are non-generation modes. Before a real `generate` or `full` run that can spend credits, explain the provider and parameters and obtain explicit user authorization. A prior request to plan does not authorize generation.

## Workflow

1. Create or resume a project. Read [references/workflow.md](references/workflow.md) for commands and state transitions.
2. Inspect every supplied asset. When visual inspection is available, inspect the actual files; do not infer identity from filenames alone. Record an Asset Bible using [references/schemas.md](references/schemas.md).
3. For a reference video, analyze Story DNA and abstract the story archetype. Read [references/reference-video-analysis.md](references/reference-video-analysis.md). Do not copy its cast, props, setting, or event sequence.
4. Route to suitable story types, generate 5–8 genuinely different candidates unless the user specifies another count, and run the production-feasibility check. Load the relevant type definitions from `assets/story_types/`.
5. Persist candidates before presenting them. Resolve selections such as “3号” through the saved display order, not memory.
6. Develop only the selected story. Preserve the selected story's goal, emotional engine, asset assignments, and declared tier-C needs.
7. Once duration, aspect ratio, style, platform, subtitles, voice, BGM, ambience, and effects are known, produce a Director Treatment and Shot Plan. Make every shot a dynamic event with subject action, environmental response, and narrative/emotional purpose.
8. Ask the chosen provider for capabilities, then compile shots into generation units and prompts. Validate duration, ratio, resolution, and supported input modes before submission.
9. In generation mode, create one job per generation unit. Retry failed units only; do not regenerate the whole film by default.
10. Run checks after every stage. Stop with an actionable report when a provider is unavailable; story and plan artifacts must remain usable.

## Tooling

Use the bundled standard-library CLI for deterministic state, validation, planning, prompt compilation, and provider jobs:

```bash
python3 scripts/asvd.py --help
```

The CLI does not replace visual reasoning. Supply its `analyze` command with descriptors produced from actual inspection. It refuses paid/provider execution without the explicit confirmation flag.

- For exact artifact locations, stage contracts, and examples, read [references/workflow.md](references/workflow.md).
- For field definitions and invariants, read [references/schemas.md](references/schemas.md).
- Before configuring or invoking any real provider, read [references/providers.md](references/providers.md).
- For the V1 architecture, scope, and test strategy, read [references/v1-implementation-plan.md](references/v1-implementation-plan.md).

## Output discipline

When responding in chat, lead with the decision or result, then show concise choices and risks. Keep canonical JSON in the project folder; chat summaries are views, not the source of truth. Clearly label `新增资产需求`, production risks, and provider-unavailable states.
