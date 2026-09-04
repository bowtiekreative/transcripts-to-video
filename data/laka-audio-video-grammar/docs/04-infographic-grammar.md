# 4. Infographic grammar

The infographic layer converts a semantic relationship into visible geometry. Every template declares what it can truthfully represent, which payload fields it requires, how much time and space it needs, and which motion families can reveal it.

## 4.1 Visual primitives

All infographics are constructed from a small set of primitives:

| Primitive | Semantic role | Typical SVG/HTML form |
|---|---|---|
| Point | item, event, person, state | dot, chip, card, icon |
| Line | relation, duration, boundary | rule, connector, axis |
| Arrow | direction or causality | line + arrowhead |
| Path | sequence, journey, process | polyline, curve, stepped rail |
| Container | group, category, context | card, frame, circle, region |
| Axis | comparison or measurement | baseline, scale, grid |
| Ring | cycle, enclosure, recurrence | circle, arc |
| Branch | hierarchy or divergence | tree connector |
| Field | many related items | grid, constellation, map area |
| Void | exclusion, missing access, separation | gap, cut, masked region |

A template is a grammar rule over these primitives.

```text
TIMELINE = axis + ordered(event_point + label)
NETWORK  = center_node + repeated(edge + satellite_node)
CYCLE    = ring_path + ordered(stage_node) + return_connection
COMPARE  = aligned(container_A, container_B) + shared_criterion
```

## 4.2 Template families

### 1. Title card

Use when:

- introducing a person, chapter, topic, or claim;
- the scene contains one dominant phrase;
- no multi-part relation must be explained.

Required payload:

```yaml
headline: string
```

Optional:

```yaml
label: string
supporting: string
asset: portrait_or_logo
```

Default motion:

```text
label reveal → headline enter → support enter → hold
```

Do not use when a sentence contains a relationship that another template can show more directly.

### 2. Quote focus

Use when:

- a sentence is reflective, declarative, or emotionally central;
- exact wording is more important than structure.

Required:

```yaml
headline: exact phrase
```

Motion:

```text
phrase reveal → key-word amplification → quiet hold
```

### 3. Big number

Use when:

- one number carries the scene;
- the number has a clear label or unit.

Required:

```yaml
number: string
label: string
```

Optional:

```yaml
unit: string
context: string
```

Motion:

```text
number count or scale → label resolve → context enter
```

Do not animate a count when the number is an identifier, year, phone number, or URL.

### 4. List stack

Use when:

- items are peers;
- order is not meaningful;
- there are two to six concise items.

Required:

```yaml
items: [string, ...]
```

Motion:

```text
items stagger in speech order
```

When more than six items exist, paginate or use a grid. Never reduce font size until all items fit.

### 5. Steps or process flow

Use when:

- order matters;
- the narration describes a procedure or progression;
- there are two to six stages.

Required:

```yaml
items: [step_1, step_2, ...]
ordered: true
```

Motion:

```text
path draws → current step enters → connector extends → next step enters
```

### 6. Timeline

Use when:

- events are anchored by time, age, before/after, or milestones;
- the relationship is chronological.

Required:

```yaml
events:
  - time: string
    event: string
```

Motion:

```text
axis draws in chronological direction → nodes appear in order → latest event amplifies
```

### 7. Before/after

Use when:

- there are two states separated by time or transformation;
- the distinction can be represented as a pair.

Required:

```yaml
left: string
right: string
```

Optional:

```yaml
left_label: Before
right_label: After
```

Motion:

```text
first state enters → dividing transition → second state enters → contrast hold
```

### 8. Comparison split

Use when:

- two entities are evaluated side by side;
- chronology is not the primary relationship.

Required:

```yaml
left: string
right: string
```

Optional:

```yaml
criterion: string
left_points: []
right_points: []
```

Motion:

```text
shared criterion appears → two panels enter from opposite directions → differences highlight
```

### 9. Transformation arrow

Use when:

- one state becomes another;
- direction is explicit.

Required:

```yaml
left: source_state
right: destination_state
```

Motion:

```text
source appears → arrow draws → destination appears → destination amplifies
```

### 10. Cause and effect

Use when:

- the narration makes a causal claim;
- both cause and outcome are present.

Required:

```yaml
left: cause
right: effect
```

Motion:

```text
cause enters → connector propagates → effect enters
```

A connector must not imply certainty stronger than the language. Possibility language uses a dotted or lower-detectability connector.

### 11. Problem and solution

Use when:

- a problem is named and a response is offered;
- the scene should move from friction to constructive action.

Required:

```yaml
left: problem
right: response
```

Motion:

```text
problem state establishes → bridge/path builds → response resolves
```

### 12. Definition card

Use when:

- a term and its meaning are explicitly stated.

Required:

```yaml
term: string
definition: string
```

Motion:

```text
term appears → equals/connector appears → definition unfolds
```

### 13. Hierarchy tree

Use when:

- one parent contains or governs several child items;
- there is a part/whole relationship.

Required:

```yaml
parent: string
children: [string, ...]
```

Motion:

```text
parent enters → trunk draws → branches propagate → children enter
```

### 14. Network

Use when:

- multiple things connect to a shared center or each other;
- the point is relationship rather than order.

Required:

```yaml
center: string
nodes: [string, ...]
```

Motion:

```text
center enters → edges radiate → nodes appear → active edge pulses once
```

### 15. Cycle

Use when:

- a return path, feedback loop, or recurrence is explicit.

Required:

```yaml
items: [stage_1, stage_2, ...]
closed: true
```

Motion:

```text
arc draws → stages propagate around ring → return connection closes
```

### 16. Funnel

Use when:

- a quantity narrows through stages;
- the concept is filtering, qualification, or conversion.

Required:

```yaml
items: [stage_1, stage_2, ...]
```

Recommended data:

```yaml
values: [number, ...]
```

A funnel is not selected merely because the word “marketing” appears.

### 17. Matrix

Use when:

- two explicit dimensions classify several items;
- each axis has meaningful poles.

Required:

```yaml
x_axis: [low_label, high_label]
y_axis: [low_label, high_label]
points:
  - label: string
    x: number
    y: number
```

Matrix selection is directed or data-driven only. The engine does not invent coordinates.

### 18. Chart

Use when:

- numeric values share a comparable unit;
- labels and values are supplied.

Required:

```yaml
series:
  - label: string
    value: number
unit: string
```

Chart types are chosen by data relationship:

```text
categories → bars
change over ordered time → line
part of whole → stacked bar or donut only when totals are valid
single metric → big number or gauge
```

### 19. Question card

Use when:

- the narration asks a genuine framing question;
- the next scene will answer or investigate it.

Motion:

```text
question enters → key term underlines → hold or branch paths appear
```

### 20. Call-to-action card

Use when:

- the narration invites a specific action;
- the action and destination are clear.

Required:

```yaml
action: string
headline: string
```

Optional:

```yaml
destination: URL or handle
qr_asset: path
```

Motion:

```text
value statement → action button → destination → closing hold
```

### 21. Audio-reactive field

Use when:

- no transcript is available;
- the purpose is atmosphere, music visualization, or chapter pacing.

Payload:

```yaml
energy_bars: [0..1]
tempo_bpm: number
section_index: number
```

Motion:

```text
bars follow measured energy; labels follow known metadata
```

It must not pretend to visualize semantic content.

## 4.3 Layout selection

Template and layout are separate choices.

```text
TIMELINE + vertical_rail  → 9:16
TIMELINE + horizontal_axis→ 16:9
LIST + single_stack       → sparse 9:16
LIST + two_column_grid    → 16:9 or high item count
NETWORK + radial          → square or spacious scene
NETWORK + offset_hub      → portrait with caption-safe bottom
```

Layout scoring considers:

- aspect ratio;
- caption safe zone;
- number and length of items;
- presence and crop behavior of assets;
- direction implied by language;
- continuity with adjacent scenes.

## 4.4 Density rules

```text
sparse: 1 dominant idea, 0–2 supporting items
low:    1 headline, 2–4 items
medium: 1 headline, 4–7 items
high:   data table, map, or directed scene only
```

Automatic scenes default to sparse or low density. High density requires data or an author override.

If text does not fit, the resolution order is:

```text
shorten through source-preserving extraction
→ paginate
→ extend scene when timing allows
→ choose a lower-density template
→ lint failure
```

Font size reduction is the last resort, not the first.

## 4.5 Template contract

Every entry in `grammar/templates.yml` declares:

```yaml
id: timeline
relations:
  timeline: 100
  sequence: 55
required_any:
  - [events]
  - [items]
item_range: [2, 6]
duration_range: [5.0, 16.0]
density: low
layouts: [vertical_rail, horizontal_axis]
motion_family: trace
semantic_risk: low
```

This metadata lets the selector reason about compatibility without hard-coding every combination.
