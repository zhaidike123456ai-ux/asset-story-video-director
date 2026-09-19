# Schemas and invariants

Machine-readable baseline schemas live in `assets/schemas/`. Runtime checks are stricter where workflow invariants matter.

## Asset Bible

Top-level fields: `schema_version`, `project_id`, `assets`, `checks`, `created_at`, `updated_at`.

Every asset includes:

- `asset_id`: stable `<type>_<NNN>`; never reuse an ID for another identity.
- `asset_type`: `character`, `scene`, `prop`, `product`, `environment`, `style_reference`, or `unknown`.
- `tier`: `A`, `B`, or `C`.
- `description`, `visual_identity`, `must_keep_features`, `flexible_features`.
- `possible_actions`, `possible_story_functions`, `relationships`, `source`.

Character extensions: `appearance`, `costume`, `body_proportions`, `personality_possibilities`, `movement_traits`, `suitable_story_roles`.

Scene/environment extensions: `location`, `time_feel`, `season`, `atmosphere`, `possible_behaviors`, `spatial_constraints`.

Prop/product extensions: `purpose`, `interactions`, `can_drive_plot`, `visual_memory_potential`.

## Story candidate

Required fields:

`story_id`, `title`, `story_type`, `one_sentence_hook`, `story_summary`, `character_goal`, `story_structure`, `emotion_curve`, `visual_highlights`, `ending`, `required_assets`, `new_assets_needed`, `AI_generation_difficulty`, `production_risk`, `feasibility`.

Candidate diversity is evaluated across story type, emotional engine, goal, conflict/obstacle, payoff, ending, and visual hook. Rephrasing one event is not diversity.

For TYPE_02, `payoff.reward_scale` must be greater than `payoff.initial_expectation_scale`.

## Story development

Required fields:

`story_id`, `complete_synopsis`, `protagonist_goal`, `motivation`, `conflict`, `turning_point`, `climax`, `ending`, `emotion_curve`, `core_visual_memory`, `theme`, `asset_usage`, `new_assets_needed`, `production_risks`.

`asset_usage` maps every used asset ID to its story function and identity constraints.

## Director plan

Top level: `story_id`, `target`, `treatment`, `shots`, `checks`.

Each shot contains:

`shot_id`, `segment_id`, `duration`, `shot_size`, `subject`, `action`, `environment_action`, `camera`, `camera_movement`, `composition`, `emotion_function`, `story_function`, `asset_ids`, `sound_effect`, `dialogue`, `subtitle`, `transition`, `generation_notes`.

Invariants:

- Durations are positive and sum exactly to `target.duration`.
- Every shot contains an observable change/action, not only a static pose.
- `asset_ids` resolve in the Asset Bible or are declared in `new_assets_needed`.
- Adjacent shots preserve location, character identity, and prop state unless the transition explains a change.

## Provider capability

Required fields:

`provider`, `available`, `max_duration`, `supported_ratios`, `supported_resolutions`, `text_to_video`, `image_to_video`, `first_frame`, `last_frame`, `multi_image`, `audio_support`, `cancel_supported`.

`max_duration` is provider data. Director and compiler must not replace it with a global constant.

## Generation unit and job

A generation unit is the smallest provider submission. It contains `segment_id`, source `shot_ids`, duration, prompt, negative constraints, assets, and parameters.

A job contains:

`job_id`, `project_id`, `story_id`, `segment_id`, `shot_id`, `provider`, `model`, `prompt`, `assets`, `parameters`, `task_id`, `status`, `attempt`, `created_at`, `updated_at`, `output_path`, `error`.

Allowed job statuses: `created`, `submitted`, `running`, `succeeded`, `failed`, `cancelled`, `provider_unavailable`.
