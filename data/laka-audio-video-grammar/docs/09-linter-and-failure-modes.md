# 9. Linter and failure modes

The linter validates the compiled storyboard before expensive rendering.

## 9.1 Timing checks

- audio file exists and has measurable duration;
- scenes have positive duration;
- scenes stay within composition duration;
- gaps and overlaps are reported;
- scene duration stays within configured bounds or has an explicit exception;
- reveal count fits available build time;
- final resolve time meets the minimum;
- caption words remain inside their cue interval;
- tail duration does not accidentally truncate audio.

## 9.2 Semantic checks

- selected template supports the primary relation;
- required payload fields exist;
- chart, matrix, map, and funnel data are explicit;
- a causal template is not selected from mere sequence language;
- a cycle includes an explicit return or feedback signal;
- a hierarchy has a parent and children;
- comparisons have aligned sides or criteria;
- author overrides point to valid templates and fields.

## 9.3 Layout checks

- text estimate fits region capacity;
- caption and infographic regions do not collide;
- safe margins are respected;
- line count and line length stay within thresholds;
- item count fits template range;
- required axes and labels are visible;
- asset crop focus remains within image bounds;
- QR codes meet configured minimum rendered size;
- no element is intentionally placed outside canvas unless marked as overscan.

## 9.4 Motion checks

- no more than configured dominant motions overlap;
- motion order matches semantic order;
- enter and exit do not overlap destructively;
- active text remains stable long enough to read;
- line propagation begins after its origin appears;
- hierarchy and process nodes reveal in valid order;
- camera movement is reduced during dense captions;
- no rapid full-frame flashing or high-frequency opacity oscillation;
- reduced-motion mode has a valid substitute for every animation family.

## 9.5 Variation checks

- repeated template inside rolling window;
- repeated layout inside rolling window;
- repeated transition without continuity reason;
- too many consecutive title/quote scenes;
- abrupt style changes not tied to a chapter boundary;
- excessive novelty that breaks the design system.

## 9.6 Failure-mode table

| Failure mode | Cause | Deterministic response |
|---|---|---|
| Audio but no meaning | No transcript or tags | Use audio-only mode; do not claim semantic visualization |
| Wrong infographic | Ambiguous language pattern | Show selection trace; add relation/template override |
| Fabricated relationship | Decorative template chosen | Hard semantic constraints reject it |
| Text overload | Long sentence or too many items | Split, paginate, lower density, or fail lint |
| Captions cover graphic | Layout ignored caption zone | Recompute available region or switch layout |
| Repetitive video | Same high-scoring template repeatedly wins | Rolling repetition penalty with semantic override |
| Random inconsistency | Unseeded choice | Stable hash tie-break and recorded engine version |
| Motion fights narration | High speech rate plus complex animation | Reduce magnitude/frequency and extend resolve |
| Inaccurate word highlight | Cue-level timing only | Mark alignment as estimated; accept word-timed input for exactness |
| Missing image | Asset role has no file | Fall back to no-asset layout or fail when asset is required |
| Misleading chart | Values or units missing | Reject chart candidate |
| Scene too short | Too many reveals | Merge, simplify, or select title/quote template |
| Scene too long | Broad SRT cue | Split into timed sentence units or paginate |
| Export desync | Browser and audio clocks drift | Frame rendering uses explicit time; FFmpeg mux uses exact duration |

## 9.7 Severity levels

```text
INFO    explanation or optimization opportunity
WARNING output remains valid but quality may suffer
ERROR   scene cannot be truthfully or safely rendered
FATAL   composition cannot compile or export
```

Compilation can be configured to fail on warnings for strict production pipelines.

## 9.8 Quality score

The report calculates a transparent score rather than a model judgment.

```yaml
semantic_integrity: 0..25
legibility: 0..20
timing: 0..20
motion_order: 0..15
continuity: 0..10
variation: 0..5
asset_integrity: 0..5
```

A score is useful for batch triage, not a substitute for review.

## 9.9 Fix priority

Use this order:

```text
semantic truth
→ missing data/assets
→ timing and synchronization
→ legibility and captions
→ motion order
→ continuity
→ variation and polish
```

A beautifully varied video with an inaccurate infographic is still a failed compilation.
