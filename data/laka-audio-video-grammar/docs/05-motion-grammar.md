# 5. Motion grammar

Motion is not decoration. It controls the order in which a visual relationship becomes understandable.

## 5.1 Motion sentence

Every scene is choreographed as a motion sentence:

```text
ESTABLISH → BUILD → EMPHASIZE → RESOLVE → TRANSITION
```

- **Establish** gives the viewer an anchor.
- **Build** reveals the relationship.
- **Emphasize** identifies the active or concluding idea.
- **Resolve** gives enough time to understand the complete state.
- **Transition** changes scenes without confusing continuity.

Not every scene needs all five phases, but the order is preserved.

## 5.2 Motion functions

| Function | Cognitive job | Common mechanisms |
|---|---|---|
| Enter | Introduce an object | fade, translate, scale |
| Reveal | Expose hidden information | wipe, mask, crop, word highlight |
| Build | Construct a structure | draw, grow, stagger, count |
| Connect | Show a relation | line draw, bridge, arrow propagation |
| Compare | Establish alignment and difference | opposed slide, shared baseline, alternating emphasis |
| Traverse | Move through a sequence | path progress, camera follow, active-node movement |
| Emphasize | Mark importance | contrast, scale, underline, glow, isolation |
| Resolve | Hold complete meaning | settle, reduce motion, final highlight |
| Exit | Remove or transform state | fade, wipe, carry, collapse |

## 5.3 Motion families

### Reveal

Best for:

```text
title, quote, definition, question
```

Grammar:

```text
anchor fade → headline rise → supporting text fade → key phrase amplify
```

### Stagger

Best for:

```text
list, cards, labels, peers
```

Grammar:

```text
container establishes → item[i] enters after item[i-1] → active item brightens
```

### Trace

Best for:

```text
timeline, path, network, hierarchy, process
```

Grammar:

```text
origin enters → line length grows → connected node enters → repeat
```

### Transform

Best for:

```text
before/after, from/to, problem/solution
```

Grammar:

```text
source establishes → transition boundary activates → destination replaces or opposes source
```

### Compare

Best for:

```text
comparison, alternatives, two-sided argument
```

Grammar:

```text
shared criterion establishes → sides enter symmetrically → one difference at a time amplifies
```

### Accumulate

Best for:

```text
steps, evidence, argument, layered system
```

Grammar:

```text
item enters and persists → next item adds → final complete structure holds
```

### Pulse

Best for:

```text
audio-only, ambient backgrounds, active node
```

Grammar:

```text
measured energy → bounded scale/opacity change
```

Pulse must not control reading-critical text.

## 5.4 Timing grammar

A scene duration is divided into normalized phases. Defaults:

```yaml
establish: [0.00, 0.18]
build:     [0.12, 0.65]
emphasize: [0.55, 0.82]
resolve:   [0.75, 0.94]
exit:      [0.90, 1.00]
```

Phases overlap intentionally. Exact values are modified by speech rate and payload size.

### High speech density

Condition:

```text
words_per_second > configured dense threshold
```

Response:

```yaml
magnitude: small
rate: medium
variability: low
frequency: once_or_per_group
camera: none_or_subtle
resolve: longer
```

The engine simplifies movement because the narration is already consuming attention.

### Low speech density or pause

Response:

```yaml
magnitude: medium_or_large
rate: slow_or_medium
propagation: sequential
camera: subtle_drift_allowed
resolve: spacious
```

### Strong acoustic onset

When an onset falls close to a planned non-reading event, the event may snap to the onset within a bounded tolerance. Text does not jump merely to match a beat.

```text
allowed snap window: ±80–150 ms
```

### Silence

A pause longer than the scene-boundary threshold is preferred for:

```text
hard cut, chapter card, complete layout change, visual reset
```

A shorter pause can trigger:

```text
item emphasis, connector completion, camera settle
```

## 5.5 Semantic-to-motion rules

```text
definition      → reveal term, then meaning
list            → stagger peers
sequence        → trace path in order
chronology      → draw time axis forward
contrast        → oppose directions or replace state
comparison      → aligned simultaneous reveal
transformation  → source, transition, destination
cause/effect    → causal propagation
hierarchy       → parent before children
network         → center before edges before nodes
cycle           → sequential ring and visible return
quantity        → establish scale before value growth
question        → reveal and hold; do not answer visually early
call to action  → value before action before destination
```

## 5.6 LAKA motion matrix

A motion preset is generated from the fourteen variables.

### Subtle explanation

```yaml
magnitude: small
rate: medium
direction: forward
scope: element
depth: property
duration: phrase
frequency: once
acceleration: ease_out
variability: fixed
detectability: clear
reversibility: none
propagation: sequential
amplification: active_item
accumulation: build
```

### Reflective statement

```yaml
magnitude: small
rate: slow
direction: inward
scope: group
depth: property
duration: scene
frequency: once
acceleration: ease_in_out
variability: low
detectability: subtle
reversibility: none
propagation: simultaneous
amplification: key_phrase
accumulation: persist
```

### Energetic announcement

```yaml
magnitude: large
rate: fast
direction: outward
scope: scene
depth: layout
duration: beat
frequency: once
acceleration: overshoot
variability: low
detectability: dominant
reversibility: reset_on_scene
propagation: simultaneous
amplification: headline
accumulation: replace
```

### System build

```yaml
magnitude: medium
rate: medium
direction: forward
scope: group
depth: structural
duration: scene
frequency: per_item
acceleration: ease_out
variability: fixed
detectability: clear
reversibility: none
propagation: hierarchical_or_sequential
amplification: conclusion
accumulation: build
```

## 5.7 Transition rules

Transitions are selected from the relationship between adjacent scenes.

| Adjacency | Transition |
|---|---|
| Same topic, new detail | carry headline or shared anchor |
| Same structure, next item set | match layout and replace content |
| Contrast | opposing wipe or state replacement |
| Chronological jump | directional cut or axis continuation |
| New chapter | pause-aligned hard cut and reset |
| Emotional shift | dissolve with reduced motion |
| Call to action | settle into stable closing frame |

The engine tracks a `continuity_key` such as topic, asset, axis, or geometry. A match transition is only used when a real key exists.

## 5.8 Camera grammar

Camera motion is an optional wrapper, not a substitute for object animation.

Allowed:

```text
subtle scale drift, slow pan within an oversized asset, path-following camera for a process
```

Rules:

- disable or reduce camera motion during dense captions;
- never move the camera and all reading-critical text in different directions at once;
- keep motion continuous within a scene;
- reset on a chapter boundary unless a match transition carries it;
- default scale drift should remain visually subordinate to information motion.

## 5.9 Motion conflict rules

The linter rejects or warns when:

- more than two dominant motions occur simultaneously;
- captions and the infographic move in opposing directions during reading;
- a causal line draws before the cause appears;
- child nodes appear before a hierarchy parent;
- a chart grows before its baseline or unit appears;
- a scene exits before its final state is readable;
- an infinite pulse affects body text;
- a transition implies continuity between unrelated topics.
