# 6. Layout, style, and accessibility grammar

## 6.1 Canvas model

The layout engine works in design coordinates and scales the final stage to the viewport.

Default canvases:

```yaml
vertical:
  width: 1080
  height: 1920
square:
  width: 1080
  height: 1080
portrait:
  width: 1080
  height: 1350
wide:
  width: 1920
  height: 1080
```

All layout values are derived from a base unit:

```text
u = min(width, height) / 108
```

For 1080-wide formats, `u = 10`. Spacing, line thickness, radius, and type sizes can be expressed as multiples of `u`.

## 6.2 Safe regions

The stage contains named regions:

```text
edge-safe       outer protection from cropping
identity-safe   logos, names, persistent labels
content-safe    main infographic region
caption-safe    burned-in caption region
control-safe    platform UI avoidance region
```

Default vertical zones:

```yaml
edge_safe: 6% of width
content_top: 8% of height
content_bottom: 24% of height
caption_zone: bottom 12–24% of height
```

Project presets can change these values for known platforms. The compiler lays out the infographic before captions, then subtracts the caption zone from available geometry.

## 6.3 Grid grammar

### Single rail

Use for:

```text
titles, quotes, lists, vertical timelines, calls to action
```

```text
left rail + flexible text width + optional right visual field
```

### Split

Use for:

```text
comparison, before/after, cause/effect, problem/solution
```

```text
panel A + relation gutter + panel B
```

### Stack

Use for:

```text
ordered steps, evidence, cards
```

### Radial

Use for:

```text
network, cycle, centered identity
```

### Grid

Use for:

```text
peer items, categories, data cards
```

### Full bleed

Use for:

```text
portrait, photograph, product, environmental context
```

Text overlays require a contrast field or protected surface.

## 6.4 Typographic hierarchy

Roles are semantic rather than hard-coded sizes:

```yaml
hero: dominant claim or number
headline: scene proposition
subhead: clarifying relationship
body: supporting sentence
label: category, time, speaker, unit
caption: spoken transcript
annotation: source, qualifier, exception
```

Default size ratios:

```text
hero      1.00
headline  0.62
subhead   0.40
body      0.28
label     0.18
caption   0.30
annotation 0.15
```

The actual base is calculated from canvas width, aspect, line count, and language length.

## 6.5 Text-fit order

When a text block exceeds its region:

1. use a shorter source span selected by the deterministic extractor;
2. reduce the number of simultaneous items;
3. paginate within the scene;
4. select a more spacious layout;
5. extend the scene if audio timing permits;
6. reduce type within configured limits;
7. emit a linter failure.

The engine does not silently crop meaningful text.

## 6.6 Caption grammar

Caption modes:

### Block

One phrase block at a time. Best for broad compatibility.

### Karaoke

Words are highlighted from timed words. When only cue timing exists, LAVC distributes time by word-length weight. This is approximate but deterministic.

### Lower third

Useful for interviews and names. Not intended for full narration.

Caption rules:

- captions remain in a stable zone;
- no more than the configured words per caption chunk;
- line breaks prefer grammatical boundaries;
- active-word emphasis changes contrast, not position by default;
- captions never cover required labels or chart axes;
- author tags are removed from visible text.

## 6.7 Brand tokens

Branding is a role-based token system:

```yaml
colors:
  canvas: "#07090D"
  surface: "#1A1D24"
  raised: "#23262F"
  text: "#F5F7FA"
  body: "#C5C7CE"
  muted: "#8A8D96"
  accent: "#3F6EE9"
  danger: "#D64A4A"
type:
  family: "Inter, system-ui, sans-serif"
  weight_head: 650
  weight_body: 420
shape:
  radius_small: 8
  radius_large: 28
  line_width: 3
motion:
  character: restrained
```

Templates use roles, never literal brand colors. This allows the same grammar to compile multiple client presentations.

## 6.8 Contrast and sensory safety

LAVC includes configurable conservative checks:

- minimum text/background contrast target;
- minimum font sizes by output class;
- maximum line length;
- maximum simultaneous text blocks;
- no rapid full-frame flashes;
- no unbounded oscillation of reading-critical elements;
- reduced-motion preset;
- optional no-camera-motion preset;
- caption background or shadow when footage changes contrast.

The linter records measured values and warns rather than assuming a design is accessible because it uses a preset.

## 6.9 Asset roles

Assets are selected by explicit metadata, filename rules, or author tags—not semantic image generation.

```yaml
assets:
  - id: portrait
    path: assets/portrait.jpg
    roles: [identity, speaker]
    crop_focus: [0.50, 0.25]
  - id: bowtie_logo
    path: assets/bowtie.svg
    roles: [organization, Bow_Tie_Kreative]
  - id: qr_clarity
    path: assets/clarity-qr.png
    roles: [cta, clarity_session]
```

Asset selection order:

```text
exact author tag
→ exact entity role
→ scene role
→ project default
→ no asset
```

The engine does not use an unrelated image merely to fill space.

## 6.10 Aspect-ratio adaptation

Adaptation changes layout, not merely scale.

```text
9:16  vertical rail, stacked comparison, vertical timeline
16:9  horizontal process, side-by-side comparison, wider data charts
1:1   compact radial or balanced grid
4:5   stacked or offset split
```

The semantic payload and timing remain identical. Each output can select a different compatible layout while retaining the same template family and motion sentence.
