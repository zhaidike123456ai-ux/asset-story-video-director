# Workflow and CLI

Run commands from the skill directory. Every mutating command prints JSON and writes canonical state beneath the project directory.

## State sequence

```text
initialized -> assets_analyzed -> stories_generated -> story_selected
            -> story_developed -> directed -> prompts_compiled
            -> generating -> generated | generation_partial | generation_failed
```

Later stages require earlier artifacts and never silently recreate them. Re-running an earlier stage creates a new timestamped artifact and updates `project.json`; it does not delete older files.

## Create and inspect a project

```bash
python3 scripts/asvd.py init --projects-root ./projects --project-id osmanthus-demo --title "桂花小院"
python3 scripts/asvd.py status --project ./projects/osmanthus-demo
```

## Asset analysis

First inspect the real images/video. Then create a descriptor JSON array. Required input is deliberately semantic, because filenames are not reliable visual analysis:

```json
[
  {
    "source": "/absolute/path/bear.png",
    "asset_type": "character",
    "description": "穿米白围裙的圆润小熊",
    "visual_identity": ["浅棕短毛", "圆耳", "米白围裙"],
    "must_keep_features": ["圆耳", "米白围裙"],
    "possible_actions": ["踮脚", "采花", "搅拌"],
    "possible_story_functions": ["主角", "仪式感动作执行者"]
  }
]
```

```bash
python3 scripts/asvd.py analyze --project ./projects/osmanthus-demo --manifest ./asset-descriptors.json
```

Unknown files may be registered, but the Asset Check will mark them `needs_visual_review`; do not generate final stories until key assets are reviewed.

## Story mode

```bash
python3 scripts/asvd.py stories \
  --project ./projects/osmanthus-demo \
  --request "生成5个45秒治愈系短视频故事" --count 5 --duration 45
python3 scripts/asvd.py select --project ./projects/osmanthus-demo --number 3
python3 scripts/asvd.py develop --project ./projects/osmanthus-demo
```

`select --number 3` resolves through saved `story_order`. `--story-id` is also accepted.

## Plan mode

```bash
python3 scripts/asvd.py plan --project ./projects/osmanthus-demo \
  --duration 45 --ratio 9:16 --style "温暖绘本3D" --platform douyin \
  --subtitles --bgm --ambience --action-sfx
python3 scripts/asvd.py compile --project ./projects/osmanthus-demo --provider mock
```

The plan's shot durations must sum exactly to the target duration. Compilation may split a shot into several generation units if the provider reports a shorter `max_duration`.

## Generate mode

Mock generation is safe and local:

```bash
python3 scripts/asvd.py generate --project ./projects/osmanthus-demo --provider mock
```

A real/provider-backed run requires both a configured provider and explicit paid-operation confirmation:

```bash
python3 scripts/asvd.py generate --project ./projects/osmanthus-demo \
  --provider jimeng --provider-config ./jimeng.local.json --confirm-paid-operation
```

The command creates one job per generation unit. Use `jobs` to inspect them and `retry --job-id ...` to retry only a failed unit.

## Modes

- `story`: analyze/router/story candidate work only; never calls a provider.
- `plan`: development/director/compiler work only; never submits paid generation.
- `generate`: submits previously compiled units; cannot invent missing story or plan state.
- `full`: a conversational workflow label, not permission to spend. Codex still pauses immediately before a real provider submission for explicit authorization.

## Checks

- Asset Check: missing key fields, unknown type, identity conflicts, review needed.
- Story Check: completeness, asset grounding, declared tier-C additions, visible change, diversity, production risks.
- Director Check: exact duration, continuity, identity, repetition, dynamic action, segment mapping.
- Generation Check: capabilities, asset references, status, output existence, optional media-duration probe.
