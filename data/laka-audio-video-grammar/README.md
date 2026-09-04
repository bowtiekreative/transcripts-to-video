# LAVC — LAKA Audio-to-Visual Compiler

A deterministic grammar and starter engine that turns audio into a timed video presentation **without generative AI**.

LAVC treats a video as a compiled program:

```text
audio + optional transcript + optional data + brand rules
→ timed meaning units
→ infographic candidates
→ deterministic scoring
→ motion plan
→ storyboard JSON
→ HTML/SVG presentation
→ MP4
```

The system is based on the production pattern in the supplied Ryan Perez reel: the narration is the master clock, the transcript supplies meaning, scenes are React/HTML/SVG compositions, and every visual property is calculated from time. LAVC generalizes that pattern into a reusable LAKA grammar.

## What “without AI” means

LAVC does not call a language model, image generator, recommendation model, or cloud service. It uses:

- digital signal processing for energy, silence, onset, tempo, and section changes;
- explicit dictionaries and regular expressions for meaning classification;
- author tags when exact semantic control is required;
- deterministic template scoring and tie-breaking;
- HTML, CSS, SVG, Chromium, and FFmpeg for rendering.

There are three operating modes:

| Mode | Required input | What it can choose |
|---|---|---|
| `audio` | Audio only | rhythm, pacing, chapter boundaries, waveform and abstract diagrams |
| `transcript` | Audio + SRT | semantic infographics, key phrases, lists, timelines, comparisons, processes, condition-response rules, calls to action |
| `directed` | Audio + SRT + LAKA tags/sidecar data | exact infographic, headline, items, motion, assets, and layout |

Audio by itself contains timing and acoustic structure, but not reliable semantic meaning. Therefore, a semantic presentation requires an SRT transcript or simple author tags. This is a physical information constraint, not a software limitation.

## Install

Requirements:

- Python 3.10+
- FFmpeg and FFprobe
- Chromium for MP4 rendering

```bash
cd laka-audio-video-grammar
python -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium   # only needed when no system Chromium is available
```

## Start a new project

```bash
laka-video init my-video --audio narration.mp3 --transcript narration.srt --mode directed
cd my-video
```

The scaffold includes `project.yml`, an editable brand preset, an override file, and a data file for truthful charts. Run `laka-video doctor` to check FFmpeg, FFprobe, Chromium, and Playwright.

## Compile a presentation

```bash
laka-video compile examples/demo/project.yml
```

Outputs:

```text
examples/demo/build/storyboard.json
examples/demo/build/preview.html
examples/demo/build/lint-report.json
examples/demo/build/decision-report.md
```

Open `preview.html`, press Play, and the HTML/SVG presentation follows the audio clock. The decision report records the detected relationship, payload, winning template, rejected alternatives, score components, and all fourteen LAKA motion variables for every scene.

## Run the drag-and-drop app

Start the local **LAKA Transcribe** surface:

```bash
laka-video doctor
laka-video serve
```

Open `http://127.0.0.1:8765`, then drop one narration file and, optionally, a matching SRT. The app queues the work locally, exposes compile/render progress, previews the completed MP4, and provides the decision report. Uploaded source files and job outputs are stored under `.laka/jobs/` by default; override that location with `--job-root`.

Compile the audio-only example without a transcript:

```bash
laka-video compile examples/audio-only/project.yml
```

Audio-only mode uses measured silence, energy, onset density, tempo, and section boundaries. It deliberately avoids semantic claims.

## Inspect a compilation

```bash
laka-video explain examples/demo/build/storyboard.json
```

## Render MP4

```bash
laka-video render examples/demo/project.yml --quality draft
```

Quality presets:

- `draft`: 12 fps and half resolution
- `standard`: project fps and full resolution
- `high`: project fps, full resolution, lower H.264 CRF

## Add deterministic author control

Place a tag inside an SRT cue. The tag is removed from the visible caption.

```text
[[LAKA relation=quantity infographic=big_number number=41 label="Diagnosed with autism and ADHD" headline="Diagnosed at 41" motion=reveal]]
At forty-one, I was diagnosed with autism and ADHD.
```

Available overrides include:

```text
relation infographic headline label motion layout density emphasis asset left right items data
```

A sidecar override file can be used instead when the transcript must remain clean.

## Key files

- `docs/01-first-principles.md` — the compiler model and information boundary
- `docs/02-volumetric-laka-grid.md` — the full volumetric LAKA system
- `docs/03-semantic-grammar.md` — deterministic language relations
- `docs/04-infographic-grammar.md` — visual template selection
- `docs/05-motion-grammar.md` — animation production rules
- `docs/06-layout-style-accessibility.md` — format, grid, type, contrast, captions
- `docs/07-selection-algorithm.md` — scoring, constraints, and tie-breaking
- `docs/08-authoring-workflow.md` — practical production workflow
- `docs/09-linter-and-failure-modes.md` — automatic quality control
- `docs/10-extension-guide.md` — how to add templates and rules
- `grammar/laka-video.ebnf` — formal grammar
- `grammar/templates.yml` — infographic capabilities and compatibility weights
- `grammar/motion.yml` — motion families expressed with LAKA variables
- `src/laka_video/` — deterministic compiler, linter, browser renderer, MP4 encoder, project scaffold, and decision reporter
- `examples/audio-only/` — DSP-only operation with no transcript
- `examples/ryan-reintroduction/` — the supplied reintroduction audio generalized through the grammar

## Core design law

The engine never asks, “What looks creative?” It asks:

```text
What relationship is present?
What visual structure can truthfully represent that relationship?
What motion reveals that structure in the order the listener can understand it?
```

That makes results reproducible, inspectable, and editable.
