# 10. Extension guide

LAVC is designed so most extensions are data changes rather than compiler rewrites.

## 10.1 Add a relation

1. Add patterns to `grammar/lexicon.yml`.
2. Add a relation definition to `grammar/relations.yml`.
3. Add relation weights to compatible templates in `grammar/templates.yml`.
4. Add payload extraction logic only when the relation requires new roles.
5. Add tests with positive and negative examples.

Example relation:

```yaml
tradeoff:
  description: Gain in one dimension accompanied by loss in another
  patterns:
    - "trade[- ]?off"
    - "at the cost of"
    - "gain .+ but lose"
  base_weight: 5
```

Compatible template:

```yaml
relations:
  tradeoff: 100
  comparison: 70
```

## 10.2 Add an infographic template

Declare capabilities:

```yaml
- id: balance_scale
  relations:
    tradeoff: 100
    comparison: 65
  required_all: [left, right]
  item_range: [2, 2]
  duration_range: [5.0, 12.0]
  layouts: [centered_scale, wide_scale]
  motion_family: compare
  semantic_risk: medium
```

Then add a renderer function named for the template in `templates/player.html.j2`.

The function must:

- render at any arbitrary time `t`;
- use only storyboard data and brand tokens;
- keep reading-critical state stable;
- support seeking and export;
- expose no randomness;
- provide a reduced-motion state.

## 10.3 Add a motion family

Declare the fourteen LAKA variables in `grammar/motion.yml`:

```yaml
unfold:
  function: build
  mechanisms: [mask, rotate_panel, reveal]
  magnitude: medium
  rate: medium
  direction: outward
  scope: group
  depth: structural
  duration: scene
  frequency: per_item
  acceleration: ease_in_out
  variability: fixed
  detectability: clear
  reversibility: none
  propagation: sequential
  amplification: final_item
  accumulation: build
```

Then implement its normalized phase behavior in the player. Motion families should be reusable across templates.

## 10.4 Add a layout

A layout declares:

```yaml
id: diagonal_split
aspects: ["9:16", "4:5"]
regions:
  left:  {x: 0.06, y: 0.10, w: 0.72, h: 0.36}
  right: {x: 0.22, y: 0.48, w: 0.72, h: 0.30}
caption_exclusion: true
capacity:
  max_items: 2
  max_words: 22
```

Coordinates are normalized from zero to one so the layout can scale to output resolution.

## 10.5 Add a brand preset

Copy `grammar/brand.example.yml`, then change role tokens. Do not edit every template.

A brand preset may restrict:

```yaml
allowed_templates: [title_card, list_stack, timeline, process_flow]
denied_motion: [overshoot, pulse]
max_radius: 12
motion_character: restrained
```

## 10.6 Add a data adapter

Adapters convert explicit source data into the standard payload schema.

Examples:

```text
CSV rows → chart.series
JSON graph → network.nodes + edges
calendar export → timeline.events
survey results → comparison or bars
website audit → problem/solution cards
```

Adapters must preserve source values and include provenance fields.

## 10.7 Add an exporter

The storyboard is renderer-independent. Alternative exporters can target:

```text
Remotion
After Effects JSON
SVG frame sequences
PowerPoint
Keynote-compatible images
web components
interactive scrollytelling
```

An exporter must honor:

```text
scene timing
motion phases
brand roles
safe zones
caption timing
asset paths
```

## 10.8 Versioning

Grammar changes can alter output. Record versions in every storyboard:

```yaml
engine_version: 0.1.0
grammar_version: 1.0.0
brand_version: 1.0.0
```

For reproducible client work, archive:

```text
project YAML
source transcript
grammar files
brand preset
assets manifest
storyboard JSON
engine version
render command
```

## 10.9 Testing philosophy

Every extension needs three kinds of tests:

```text
positive: relation should select template
negative: similar wording must not select template
boundary: minimum/maximum duration, items, and text length
```

A grammar becomes powerful through exclusions as much as inclusions.
