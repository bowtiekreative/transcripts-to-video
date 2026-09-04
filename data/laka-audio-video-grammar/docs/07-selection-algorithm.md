# 7. Deterministic selection algorithm

## 7.1 Overview

For each scene, LAVC generates all compatible template candidates, removes impossible candidates, scores the remainder, and chooses the highest result using a stable tie-break.

```text
relations + payload + time + audio + aspect + history + brand
→ candidate set
→ hard constraints
→ weighted score
→ deterministic tie-break
→ motion plan
```

## 7.2 Hard constraints

A candidate is rejected when any required condition fails.

Examples:

```text
timeline requires at least two events/items
comparison requires two sides
chart requires numeric values and labels
matrix requires axis definitions and coordinates
network requires center plus at least two nodes
scene duration must intersect template duration range
a required asset must exist
layout must support target aspect
text estimate must fit maximum density after pagination rules
```

Hard constraints prevent a visually attractive but false representation from entering scoring.

## 7.3 Score components

Default 100-point model:

| Component | Maximum | Question |
|---|---:|---|
| Semantic fit | 35 | Does the template directly encode detected relations? |
| Payload fit | 15 | Are all visual roles present and appropriately sized? |
| Timing fit | 10 | Can the structure be understood in available time? |
| Density fit | 10 | Will text and items fit without overload? |
| Aspect fit | 8 | Is a strong layout available for this format? |
| Audio fit | 5 | Does motion complexity suit energy and speech rate? |
| Continuity | 7 | Does it connect coherently to adjacent scenes? |
| Variation | 5 | Does it avoid recent template repetition? |
| Brand fit | 3 | Is it permitted by the chosen style preset? |
| Author preference | 2 | Is it preferred but not forced? |

Penalties are subtracted after positive scores.

## 7.4 Semantic fit

Each template declares relation weights from zero to one hundred. Relation evidence is normalized.

Simplified calculation:

```text
semantic_fit = 35 × max_over_relations(
  normalized_relation_score × template_relation_weight
)
```

Secondary relations can add a bounded bonus. This allows a sentence scored as both `timeline` and `contrast` to choose `before_after` when the payload is a clean pair.

## 7.5 Payload fit

Payload fit considers:

- all required fields present;
- item count within preferred range;
- item lengths;
- labels available;
- numeric units available;
- whether extracted pairs are complete clauses;
- whether an author tag supplied exact values.

Author-supplied payload receives higher confidence than heuristic extraction.

## 7.6 Timing fit

Each template declares a preferred duration range. Score is highest near the center and declines toward the edges.

```text
preferred: 6–12 seconds
scene: 8.5 seconds → high score
scene: 3.6 seconds → low but possible
scene: 20 seconds → paginate, split, or reject
```

Timing also estimates reveal count:

```text
available_build_time / reveal_count >= minimum_reveal_seconds
```

## 7.7 Density fit

Estimated reading demand:

```text
visible_words
+ 0.6 × label_words
+ 1.5 × numeric_annotations
+ caption_overlap_cost
```

Speech rate adds a cognitive-load multiplier. A dense transcript makes a dense infographic less likely.

## 7.8 Continuity and variation

The selector tracks a rolling history:

```yaml
recent_templates: [title_card, list_stack, list_stack]
recent_layouts: [rail, stack, stack]
recent_motion: [reveal, stagger, stagger]
continuity_keys: [identity, projects, projects]
```

Rules:

- repeated template inside the configured window receives a penalty;
- repetition is allowed when it communicates a deliberate series;
- a shared topic or object can earn continuity points;
- variation never overrides semantic truth.

## 7.9 Penalties

Default penalties:

| Condition | Penalty |
|---|---:|
| Same template as previous scene | 8 |
| Same template three times in window | 14 |
| Text exceeds soft capacity | 5–20 |
| More than two dominant motions | 10 |
| Weak or incomplete extracted pair | 12 |
| Asset missing | hard reject or 20 |
| Semantic risk medium/high | 4/10 |
| Caption collision risk | 8 |
| Scene too short for reveals | 5–25 |

## 7.10 Deterministic tie-break

When candidate scores are equal within the configured epsilon, LAVC uses a stable hash:

```text
SHA-256(project_seed | scene_id | template_id | layout_id)
```

The smallest lexical hash wins. This creates variety across projects while guaranteeing repeatability.

There is no call to a random number generator during compilation unless the user explicitly selects seeded variation. Seeded variation still produces the same output for the same seed.

## 7.11 Selection trace

Every scene stores a trace:

```json
{
  "candidates": [
    {
      "template": "transformation_arrow",
      "score": 91.2,
      "positive": {
        "semantic": 34.0,
        "payload": 15.0,
        "timing": 9.1,
        "density": 9.0,
        "aspect": 8.0,
        "variation": 5.0
      },
      "penalties": {"repeat": 0}
    },
    {
      "template": "before_after",
      "score": 86.8,
      "positive": {"semantic": 31.5, "payload": 14.0},
      "penalties": {"weak_time_labels": 4}
    }
  ],
  "selected": "transformation_arrow"
}
```

This trace is the foundation for debugging and manual tuning.

## 7.12 Pseudocode

```text
for scene in scenes:
    analysis = classify_and_extract(scene.text)
    candidates = []

    for template in template_library:
        if not hard_constraints_pass(template, scene, analysis, output):
            continue

        layouts = compatible_layouts(template, output.aspect)
        for layout in layouts:
            score = semantic_score(template, analysis)
            score += payload_score(template, analysis.payload)
            score += timing_score(template, scene.duration)
            score += density_score(template, scene, layout)
            score += aspect_score(layout, output.aspect)
            score += audio_score(template.motion, scene.audio_features)
            score += continuity_score(template, history)
            score += variation_score(template, history)
            score += brand_score(template, brand)
            score -= penalties(template, scene, analysis, history)
            candidates.append(candidate(template, layout, score))

    selected = stable_max(candidates, seed, scene.id)
    motion = compile_motion(selected, scene, analysis, audio_features)
    history.record(selected)
```
