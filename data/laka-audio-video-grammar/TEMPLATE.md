# Deterministic Film Template

Use this contract to regenerate a film without reverse-engineering the renderer.
The supplied `bullies-film.jsx` and `invisible-film.jsx` examples are the visual
reference: one time value must always produce the same frame.

## Input

Provide narration plus a matching SRT. Each SRT cue becomes one `CAPS` entry:

```js
{ at: 4.2, until: 7.8, text: "Exact caption text." }
```

The compiler groups cues into semantic scenes. Each scene is emitted through
`window.OM_SCENES` with `name`, `at`, `dur`, and `desc`. The first cue is named
`Opening`; the final cue is named `Close`; intermediate names describe the
detected relationship.

## Film function

`window.renderAt(T)` is the public frame function. It selects the active named
scene, normalizes local time, and renders a positioned scene block. Motion uses
only the shared deterministic helpers:

- `enter(T)` reveals type or objects with controlled travel.
- `draw(T)` grows lines and full-frame fields.
- `pop(T)` introduces discrete nodes or numbers.

No timers, random values, generative calls, or stateful transitions belong in a
scene. Scrubbing backward and rendering offline must reproduce the same frame.

## Studio selection contract

`grammar/studio-library.yml` is the composition authority layered over the
semantic template grammar. **Choose in Studio** exposes the selected candidate
and nearby candidates that already passed payload, timing, data, aspect, and
truth constraints. **Deterministic wildcard** selects only inside that valid
score band using `project.seed`; it is varied, not unbounded or random.

An `image_overlay` layout is incomplete without `scene.asset`. The linter emits
blocking code `asset.required`, and the web workflow must collect a PNG, JPG,
or WebP for every selected image scene before it invokes the renderer. Images
use the fixed LAKA grade, tint, grain, and text-protection flood.

## Fixed visual laws

- Default output is 1920×1080; alternate aspect ratios retain full resolution.
- Canvas is `#07090D`; Inter uses only 400 and 600.
- Headlines are short, large, tightly tracked, and aligned to the left rail.
- Captions stay low, plain, and readable without a surrounding UI card.
- Blue `#3F6EE9` is rationed inside the film and becomes a full field only at
  the closing beat.
- Every entry has an exit, and visual density remains below spoken density.

To make a new version, replace the SRT-derived `CAPS`, regenerate the named
scene cue list, select or seed the Studio cut, fill every required image slot,
and supply one deterministic positioned block per scene. Keep the palette,
type scale, left rail, helper behavior, and rationed blue CTA cut unchanged.
