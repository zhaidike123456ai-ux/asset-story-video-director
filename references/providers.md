# Video provider integration

## Selection

Use `mock` for planning, tests, and workflow demonstrations. Use `jimeng` only after a stable CLI/API exists, its terms and fees are understood, login is complete, and the user explicitly authorizes the generation run.

## Jimeng CLI configuration

Copy `assets/providers/jimeng.example.json` outside the skill's tracked files, fill only non-secret command/capability fields, and keep credentials in the external CLI's login store or documented environment variables.

The adapter expects commands as argument arrays, never shell strings. Supported placeholders:

- `{prompt}`
- `{duration}`
- `{ratio}`
- `{resolution}`
- `{model}`
- `{assets_json}`
- `{task_id}`
- `{output_path}`

Submit and status commands must print JSON. Field paths in `response_fields` use dot notation, such as `data.task_id`.

Run diagnostics before generation:

```bash
python3 scripts/asvd.py provider-info --provider jimeng --provider-config ./jimeng.local.json
```

If the executable is missing, config is disabled, a capability is unsupported, or output JSON cannot be parsed, the adapter raises a typed error. The job is recorded as `provider_unavailable` or `failed`; existing story, director, and prompt artifacts remain intact.

## Capability rules

- Reject unsupported ratios/resolutions before submission.
- Split generation units by `max_duration`; do not assume 15 seconds.
- Require at least one valid image asset for image-to-video modes.
- Do not request first/last frame or multi-image unless advertised.
- `cancel_task` may be unsupported and must return a clear result rather than crash the workflow.

## Adding a provider

Implement `VideoProvider` in `scripts/asvd/providers/base.py`, expose it through the provider factory, and add capability/contract tests. Do not add provider-specific branching to the story or director engine.
