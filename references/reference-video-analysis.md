# Reference Video Analyzer

Use this only when a reference video is part of the request.

## Inspection

Inspect representative frames and, when tools permit, the complete temporal sequence and audio/transcript. Separate observed facts from inference. Record uncertain fields explicitly instead of inventing details.

Extract:

- `story_type`
- `character_role`
- `character_goal`
- `conflict`
- `obstacle`
- `turning_point`
- `emotion_curve`
- `payoff`
- `visual_reward`
- `pacing`
- `hook`
- `ending_method`
- `dialogue_dependency`
- `asset_complexity`
- `AI_generation_difficulty`

## Abstraction test

The resulting archetype must remain valid after replacing every proper noun, specific species/person, branded object, location, and signature incident. If it no longer makes sense, it is still a plot copy rather than Story DNA.

Store observations and the abstract archetype separately:

```json
{
  "reference_id": "reference_001",
  "source": "/path/to/reference.mp4",
  "observations": {},
  "story_dna": {},
  "abstract_archetype": "A small desire meets escalating setbacks before unexpected kindness creates an outsized emotional reward.",
  "do_not_copy": ["specific cast", "signature prop", "exact setting", "event sequence"]
}
```

Use the archetype as a routing signal, not as a command to override the user's assets or requested mood.
