# Image Label Guidelines

## Label: no_flood
Definition:
- Scene has no visible floodwater affecting roads, homes, or evacuation movement.

Positive examples:
- Dry roads and alleys.
- Normal river level with no overflow signs.

Hard negatives:
- Wet roads after rain without flooding.

## Label: low_flood
Definition:
- Floodwater present but below life-threatening level.

Positive examples:
- Water on roads around ankle-to-knee level.
- Motorbikes partially submerged but movement still possible.

Hard negatives:
- Puddles or localized waterlogging that is not flood event.

## Label: high_flood
Definition:
- Severe flooding with major obstruction or direct danger.

Positive examples:
- Water near waist level or higher.
- Homes submerged to windows or roof level.
- Rescue boats operating in residential streets.

Hard negatives:
- Deep perspective illusion where water seems high but is not.

## Decision rules

1. Prefer safety-first: if uncertain between low_flood and high_flood, mark high_flood and flag for review.
2. If image quality is too poor, label as unusable in metadata and exclude from split.
3. Keep one event-specific visual style in one split only when near-duplicate risk is high.
