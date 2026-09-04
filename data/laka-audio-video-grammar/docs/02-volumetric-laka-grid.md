# 2. The volumetric LAKA grid

A normal template system makes a one-dimensional choice:

```text
sentence → template
```

LAVC treats every scene as a coordinate inside a multidimensional production space. The output is selected by intersecting meaning, time, visual structure, motion, format, and quality constraints.

## 2.1 The seven production volumes

### Volume A — Source

| Dimension | States |
|---|---|
| Audio | voice, music, interview, lecture, mixed program, silence |
| Transcript | none, cue timed, phrase timed, word timed |
| Data | none, scalar, series, categories, table, graph |
| Assets | none, logo, portrait, photograph, product, icon, diagram |
| Brand | default, project preset, client preset |
| Intent | explain, persuade, document, teach, announce, reflect, sell |

### Volume B — Meaning

| Dimension | States |
|---|---|
| Speech act | statement, question, instruction, invitation, warning, claim |
| Relation | definition, list, sequence, timeline, cause, contrast, comparison, transformation, hierarchy, network, cycle, quantity, problem/solution, call to action |
| Cardinality | one, pair, small set, large set, continuous series |
| Certainty | fact, estimate, possibility, opinion, question |
| Emotional force | neutral, reflective, urgent, celebratory, sensitive |
| Reference | person, organization, place, object, concept, event, metric |

### Volume C — Time

| Dimension | States |
|---|---|
| Scale | composition, chapter, scene, beat, phrase, word, frame |
| Boundary | hard cut, pause, punctuation, topic shift, energy change |
| Pace | spacious, normal, dense |
| Synchronization | free, cue-locked, phrase-locked, word-locked, onset-locked |
| Persistence | transient, scene hold, chapter hold, cumulative |

### Volume D — Visual structure

| Dimension | States |
|---|---|
| Infographic family | title, quote, list, steps, timeline, comparison, process, hierarchy, network, cycle, chart, map, matrix, equation, call to action |
| Geometry | point, line, path, container, axis, ring, branch, grid, field |
| Layout | centered, split, rail, stack, radial, grid, diagonal, full-bleed |
| Hierarchy | headline, support, label, item, annotation, caption |
| Density | sparse, low, medium, high |
| Image role | none, evidence, identity, context, texture, background |

### Volume E — Motion

| Dimension | States |
|---|---|
| Function | enter, reveal, build, connect, compare, traverse, emphasize, resolve, exit |
| Mechanism | fade, translate, scale, wipe, draw, mask, count, stagger, morph-state, camera |
| Synchronization | scene, beat, phrase, word, onset |
| Continuity | cut, match, carry, transform, dissolve |
| Attention | global, focal, sequential, distributed |

### Volume F — Output

| Dimension | States |
|---|---|
| Aspect | 9:16, 16:9, 1:1, 4:5, custom |
| Resolution | draft, HD, full HD, UHD, custom |
| Platform | reel, short, presentation, course, website, signage |
| Captions | none, block, karaoke, lower third, burned-in |
| Duration behavior | exact audio, padded close, loop, chapter export |

### Volume G — Quality

| Dimension | States |
|---|---|
| Legibility | fail, warning, pass |
| Semantic truth | decorative, approximate, direct |
| Repetition | repetitive, controlled, varied |
| Continuity | broken, acceptable, coherent |
| Accessibility | fail, warning, pass |
| Determinism | untracked, seeded, exact |

## 2.2 The ten LAKA internal variables

Every scene and every visual object is specified through the ten internal variables.

| Variable | Video-system question |
|---|---|
| Object | What is being represented or animated? |
| Conditions | What timing, semantic, format, and density conditions apply? |
| Actions | What transformation occurs? |
| Tools | Which parser, template, SVG primitive, renderer, or codec performs it? |
| Resources | Which text, data, audio features, colors, fonts, and assets are required? |
| Outcomes | What should the viewer understand or do? |
| Feedback | What linter or playback evidence changes the plan? |
| Constraints | What limits time, space, readability, truth, or platform safety? |
| Value | For whom is the scene useful, and what cognitive work does it remove? |
| Failure mode | How can the scene mislead, overload, collide, repeat, or desynchronize? |

Example:

```yaml
object: "three-part practical method"
conditions:
  relation: sequence
  item_count: 3
  scene_seconds: 8.4
  aspect: "9:16"
actions:
  - reveal_heading
  - draw_path
  - stagger_steps
  - emphasize_final_step
tools:
  - steps_template
  - svg_path
  - motion_family_build
resources:
  - transcript_items
  - brand_tokens
outcomes:
  - viewer_can_recall_three_steps
feedback:
  - max_words_per_frame_linter
constraints:
  - captions_occupy_bottom_safe_zone
value:
  audience: learner
  type: reduced_working_memory
failure_mode:
  - all_steps_appear_at_once
  - path_order_conflicts_with_speech
```

## 2.3 The fourteen LAKA meta-variables

The fourteen variables parameterize change. They apply to typography, layout, motion, camera, transitions, and information accumulation.

| Meta-variable | Video implementation | Example states |
|---|---|---|
| Magnitude | How far, large, bright, or different? | none, micro, small, medium, large, hero |
| Rate | How quickly does state change? | hold, slow, medium, fast, snap |
| Direction | Where does attention or geometry move? | none, forward, backward, up, down, inward, outward, clockwise, counterclockwise |
| Scope | How much of the composition changes? | word, element, group, scene, chapter, composition |
| Depth | How fundamental is the change? | cosmetic, property, layout, structural, metaphor |
| Duration | How long is the state active? | frame, beat, phrase, scene, chapter, persistent |
| Frequency | How often does it occur? | never, once, per item, per phrase, periodic, continuous |
| Acceleration | How does speed change? | linear, ease-in, ease-out, ease-in-out, overshoot, spring |
| Variability | How consistent is the behavior? | fixed, low, medium, high, seeded |
| Detectability | How obvious is the change? | hidden, subtle, clear, dominant |
| Reversibility | Can the visual return? | none, reversible, ping-pong, reset-on-scene |
| Propagation | How does change spread? | simultaneous, sequential, radial, hierarchical, causal, wave |
| Amplification | What becomes more prominent? | none, active word, active item, conclusion, exception |
| Accumulation | What remains after each change? | replace, trail, stack, build, persist, reset |

A motion plan is therefore not merely `fadeIn`. It is a coordinate:

```yaml
function: build
mechanism: draw_and_stagger
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
propagation: sequential
amplification: conclusion
accumulation: build
```

## 2.4 Five levels of change

Each grammar decision can be varied through five levels.

| Level | Meaning in LAVC | Example |
|---|---|---|
| Baseline | Same semantic and visual structure | Change only a word highlight |
| Minor Change | Change a property | Change entrance direction or spacing |
| Major Change | Change layout or motion family | Stack becomes split layout |
| Structural Change | Change infographic family | List becomes process path |
| Paradigm Change | Change representation model | Literal process becomes spatial metaphor or interactive exploration |

The compiler defaults to Baseline–Major changes. Structural changes require a stronger relation score. Paradigm changes require an author tag because they can alter meaning.

## 2.5 The scene coordinate

Every compiled scene receives a coordinate like this:

```yaml
source:
  mode: transcript
  cue_ids: [4]
meaning:
  speech_act: explanation
  primary_relation: sequence
  cardinality: small_set
time:
  start: 44.2
  end: 52.7
  pace: normal
visual:
  infographic: steps
  layout: vertical_rail
  density: low
motion:
  family: build
  propagation: sequential
  accumulation: build
output:
  aspect: "9:16"
quality:
  semantic_truth: direct
  legibility: pass
```

This coordinate is the compiled result of the volumetric intersection. New templates can be added without changing the conceptual model.
