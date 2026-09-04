# Repository Guidelines

## Project Structure & Module Organization

The working Python package is in `data/laka-audio-video-grammar/`. Production code lives under `src/laka_video/`; keep compiler stages focused (for example, parsing in `srt.py`, deterministic selection in `selector.py`, and MP4 output in `render_mp4.py`). Canonical grammar data is stored in `grammar/` and packaged copies live in `src/laka_video/data/grammar/`. Update both locations when changing shipped grammar rules. `grammar/studio-library.yml` owns Studio review, wildcard, and image-slot policy. The shipped browser renderer is under `src/laka_video/data/templates/`; `templates/` is retained as a legacy source copy.

Tests are in `tests/`, documentation in `docs/`, and runnable fixtures in `examples/`. Generated `build/` directories are outputs, not source files.

## Build, Test, and Development Commands

Run commands from `data/laka-audio-video-grammar/`:

```bash
python -m venv .venv && source .venv/bin/activate
make install       # install the package in editable mode
make test          # run the pytest suite with src on PYTHONPATH
make demo          # compile the deterministic demo in strict mode
make render-demo   # render a draft MP4; requires FFmpeg and Chromium
make serve         # run the local drag-and-drop compiler at port 8765
laka-video doctor  # verify local rendering dependencies
```

Use `make clean` only to remove Python bytecode caches.

## Coding Style & Naming Conventions

Target Python 3.10+ and use four-space indentation, type hints for public APIs, and `pathlib.Path` for filesystem work. Follow existing naming: `snake_case` for modules, functions, and variables; `PascalCase` for classes; `UPPER_CASE` for constants. Keep grammar identifiers lowercase and descriptive, such as `transformation_arrow`. Preserve determinism: do not introduce remote inference, unseeded randomness, or hidden selection behavior.

## Design System Contract

Rendered frames are governed by the Ryan Perez / LAKA design system (`studio/_ds/.../readme.md` and `tokens/`). `src/laka_video/data/templates/studio-renderer.js` is the design authority; `player.html.j2` owns the frame chrome (canvas, backlight, grain, camera drift, caption band) and each scene renderer returns content only, in raw `W x H` coordinates. Do not repaint the chrome inside a scene, and do not add a second inset or drift layer — that shifts every composition off its left rail.

Non-negotiables, each enforced by `tests/test_design_system.py`:

- **Typeface.** Inter 400/600 only. The two licensed weights ship in `src/laka_video/data/fonts/` and are inlined as base64 `@font-face` rules by `utils.inline_font_face_css()`. Never reference a font by family name alone and never load one over the network — a render box has no fonts installed and would silently fall back.
- **Colour.** `grammar/brand.example.yml` mirrors `tokens/colors.css` and `tokens/semantic.css` exactly. Change a colour in the tokens first, then here. Blue is the accent, not a decoration: the full-bleed CTA is the only saturated frame.
- **Motion.** One curve, `cubic-bezier(0.16, 1, 0.3, 1)`, with a 24px rise and a 90ms stagger, timed in real milliseconds against scene duration. No overshoot, bounce, blink, pulse, rotation or particle field. Numbers are revealed at their exact value — a count-up puts wrong figures on screen for most of a scene, and precision is the brand.
- **Type fitting.** Text is fitted by measurement (`fitText` / `fitTogether`), never truncated. A frame that ends in `…` is a bug. Related strings in one figure share one size.
- **Composition.** One left rail. Statements are seated on the lower third with the micro-label holding the top of the safe area; figures get an exactly measured band under the head. Air belongs above the type or in the right-hand column, never as a dead strip under a bottom-heavy block.
- **Repetition.** A headline that restates the figure below it, or a supporting line that restates the headline, is suppressed (`dropEchoes`). Captions that repeat the headline already on screen are dropped too.

Text extraction has the same standard. Headlines are complete phrases (`text_rules._headline_span`), keep their subject, and never stop on a function word. Spoken web addresses are folded into real domains at transcript ingest (`utils.normalize_spoken_domains`), so "Ryan Perez dot c a" reaches the frame as `ryanperez.ca`.

## Perception and Semantics Contract

`grammar/perception.yml` holds every published threshold the compiler reasons with — reading rate, fixation cost, Cowan's ceiling of 4, Stevens exponents, the Cleveland–McGill ranking, the Weber floor, motion timing, the AV-sync window, type floors, safe areas, the density ladder and the composition rhythm. Nothing downstream may carry a numeric literal: change the number here, and the selector, the budget and the linter all follow.

`grammar/lexicon/` holds the language-to-form mapping. **The noun never chooses the graphic.** The relation does, and the relation lives in the verb, the preposition, the frame and the aspect. Adding a keyword-to-template rule is the one change that is always wrong.

- `image_schemas.yml` — prepositions and verb classes to diagram family, in precedence order. Ambiguous triggers belong lower, or not at all: bare `into` was removed because "turns into", "divided into" and "feeds into" are three different schemas.
- `frames.yml` — evoking verbs to role structure to visual slots, plus `constraints`, which gate ambiguous lemmas on the construction that makes them that verb ("leads TO", not "potential leads").
- `aspect.yml` — Vendler class to motion operator. Achievements cut, accomplishments build and settle, activities loop, states hold.
- `modality.yml` / `negation.yml` — certainty to stroke, opacity and label precision; negation shows the object and then strikes it, never renders it as absence, and preserves quantifier scope.
- `concreteness_core.yml` — the depiction gate. An unrated word makes the gate abstain; it never licenses a depiction on a guess.

Selection is **lexicographic**, not a weighted sum (`ordering.py`). Truth terms — semantic loss, false-implication risk, relation mismatch — are compared first and the comparison stops the moment they differ, so no amount of economy can reach past them. When adding a term, its position in the tuple is the entire design decision.

Two failure modes to hold in mind, because both have already happened here:

- **Too sparse.** Scoring only frame roles made every template tie at zero loss and selection collapsed to whichever was sparsest — 22 of 29 scenes became title cards. Loss must also count the relation and the structure already extracted into the payload.
- **Fragmenting to hit a number.** The reading budget (`budget.py`) trims supporting copy, then list length, then spans — and stops. It never cuts a headline except at a clause boundary, because a frame reading "I'm a cognitive" is a defect and going over budget is only a warning. If a metric can only be satisfied by breaking a sentence, report the gap instead.

`composition.py` runs after selection, because rhythm, accent budget, carrier persistence and the ending are properties of the whole piece. Demotions there are ranked by relation fit: rhythm is a presentation concern and must never buy a worse claim.

## EventMath

The compiler speaks **EventMath 2.0**, the same event vocabulary as the Second Brain, so a storyboard scene and a brain node describe the world identically. `grammar/lexicon/eventmath.yml` holds it and `semantics/eventmath.py` extracts it — pure pattern matching, no model, no lookup, matching the brain's own engine.

Every scene emits an event: who + what + where + when + why + how, the seven universal elements, and a **LENS × DIRECTION × QUANTIFIER** triple. Three knobs, the whole grammar.

- **DIRECTION** is the motion: `direct`, `indirect_opposite`, `indirect_other`, `keep_same`, `more_same`, `less_same`. It says what the sentence is doing, which is upstream of what shape draws it.
- **QUANTIFIER** is scope: `none`, `partial`, `one`, `many`, `all`, `any`. Cardinality anchors it — four peers on screen is `many` whatever the words say — but a scope word outranks a count, because "not all of them" stays partial with four names drawn. Reading "not all" as `none` negates a group the speaker left standing.
- **The seven elements** map to template families: begin/end state to the pair, actions to steps and timelines, objects to lists, conditions to if/then, resources to quantity, tools to networks. A begin state with no end state is dropped rather than drawn as a pair, because the missing half would be invented.

**Gaps are reported, never filled.** A 5W+H field the speaker did not state is listed in `gaps` and no mark may stand in for it. `gap_policy.fill_from_model` is `false` and must stay false: an invented actor or a fabricated date is the same class of failure as a fabricated baseline on a bar chart. First person resolving to the project's known speaker is not gap-filling — that is stated context.

**`signal: false` forces D0.** Discourse filler carries a caption and nothing else. This is the coherence principle with a switch on it.

Where EventMath and `image_schemas.yml` disagree, EventMath wins: the schema says what shape a relation has, the triple says what the sentence is doing, and the triple is the vocabulary the rest of the stack already speaks.

## Accessibility

This compiler puts a neurodivergent speaker's own words on screen, so "reduce cognitive load first" is the brief, not a compliance checkbox (`nd-ux`; MOTION_MATH §7). `accessibility.py` enforces four things the rest of the pipeline could only measure.

- **Contrast is computed, not assumed.** `audit_contrast` runs WCAG arithmetic over the pairs the renderer actually draws, not over the palette in the abstract — that would pass colours that never touch each other. A translucent colour is composited over its background first: a hairline at 8% alpha does not have the contrast of white, and scoring it as white passes a line nobody can see.
- **Vestibular limits are checked per scene** — camera scale rate, total scale change, and a flicker check on very short scenes.
- **`--reduced-motion` is a cut, not a second edit.** Same scenes, same boundaries, same words, every duration kept and every translation dropped (WCAG 2.3.3). The dolly goes too; a loop operator becomes static. Verified by comparing both cuts at the same timestamp: identical element count, identical text, transforms 1 → 0.
- **Plain language** is measured with Flesch-Kincaid against the grade 6-8 target.

A gap is only reported where it is a hole rather than unstated context. A spoken monologue has no `where`, and saying so on every scene buries the findings that matter; the sharp case is a scene whose own LENS is the missing field — it is *about* the when, and the when was never said.

## Testing Guidelines

Tests use `pytest` and follow `tests/test_<area>.py` with functions named `test_<behavior>`. Add focused unit tests for parser or rule changes and an integration assertion when generated storyboard behavior changes. Visual or brand changes must also satisfy `tests/test_design_system.py`; if a guard there is wrong, change the guard deliberately and say why in the commit. Verify repeatability, schema validity, and lint scores where applicable. Run `make test` before submitting changes; use `make demo` for compiler or grammar edits.

## Commit & Pull Request Guidelines

History currently contains only `first commit`, so no mature convention exists. Use short, imperative subjects such as `Add timeline selection rule`. Keep commits narrowly scoped. Pull requests should explain the behavioral change, list validation commands, and identify affected grammar, examples, or generated output. Include preview screenshots or a short rendered sample when visual behavior changes, and link relevant issues.

## Security & Configuration

Keep `.env`, media credentials, and machine-specific paths untracked. The compiler is intentionally local and deterministic; document and justify any new network-facing dependency before adding it.
