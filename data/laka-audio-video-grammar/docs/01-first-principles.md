# 1. First principles: audio is a clock, not a picture

## 1.1 The transformation

A deterministic audio-to-video system has five distinct jobs:

```text
measure → interpret → represent → choreograph → render
```

1. **Measure** the audio timeline: duration, pauses, energy, attacks, tempo, and section changes.
2. **Interpret** the transcript using explicit language rules.
3. **Represent** each detected relationship with a truthful infographic structure.
4. **Choreograph** the structure so information appears in listening order.
5. **Render** every frame from a known time value and mux the frames with the audio.

The narration is the master clock. A scene is not a clip placed near the audio; it is a function of the audio time:

```text
frame = render(storyboard, audio_time)
```

This gives deterministic seeking, revision, aspect-ratio adaptation, and export.

## 1.2 The information boundary

Audio contains two different classes of information.

### Acoustic information

Available without a transcript:

- beginning and ending;
- silence and pause locations;
- loudness and change in loudness;
- onset density;
- approximate tempo;
- spectral brightness;
- section changes;
- duration available for each visual event.

### Semantic information

Not reliably available from the waveform alone:

- whether a sentence is a definition, list, comparison, warning, or call to action;
- which noun is the topic;
- which two concepts are being contrasted;
- what number means;
- whether an event happened before or after another event;
- what should be emphasized.

LAVC therefore separates three modes:

```text
AUDIO MODE      = acoustic structure → nonsemantic visuals
TRANSCRIPT MODE = acoustic structure + language rules → semantic visuals
DIRECTED MODE   = acoustic structure + language rules + author intent → exact visuals
```

A manually created SRT is fully compatible with the no-AI requirement. A transcript can also come from any external process, but the compiler itself does not require or call AI.

## 1.3 Atomic units

The system compiles from large units to small units:

| Unit | Meaning | Typical duration |
|---|---|---:|
| Composition | Entire presentation | 15 seconds to hours |
| Chapter | Major subject or argument | 20–180 seconds |
| Scene | One visual proposition | 3.5–12 seconds |
| Beat | One reveal or state change | 0.4–3 seconds |
| Phrase | Caption or spoken clause | 0.8–5 seconds |
| Word | Caption highlight | 0.12–1 second |
| Frame | Final deterministic state | 1 / fps |

A scene should normally make one visual claim. A single SRT cue can become several scenes when it contains several relationships.

## 1.4 The truth-preserving rule

The infographic must encode the same relationship as the sentence.

```text
definition      → term + meaning
sequence        → ordered path
comparison      → aligned alternatives
cause/effect    → directional connection
part/whole      → hierarchy
change over time→ timeline
feedback        → cycle
many connections→ network
quantity        → scale or chart
problem/answer  → problem-to-solution bridge
```

A visual is rejected when it is merely decorative or implies a relationship that the narration does not claim. For example, a Venn diagram implies overlapping sets. It must not be selected just because two nouns appear in the same sentence.

## 1.5 The deterministic contract

Given the same:

- audio bytes;
- transcript text and timestamps;
- project configuration;
- grammar files;
- engine version;
- seed;

LAVC produces the same storyboard and the same frames.

All choices are inspectable. Each scene records:

```json
{
  "detected_relations": {"contrast": 8.0, "timeline": 4.0},
  "candidate_scores": {"before_after": 87.4, "comparison_split": 82.0},
  "selected_template": "before_after",
  "selection_reason": ["contrast match", "two-part payload", "duration fit"]
}
```

No hidden model weights or probabilistic service determine the result.

## 1.6 Compilation stages

```text
SOURCE
  audio, transcript, data, assets, brand, output target

NORMALIZATION
  audio decode, timestamp normalization, text cleanup, author-tag extraction

ANALYSIS
  acoustic features, sentence units, relation scores, payload extraction

SEGMENTATION
  chapters, scenes, beats, captions

CANDIDATE GENERATION
  compatible infographic and motion combinations

CONSTRAINT FILTERING
  duration, item count, density, format, asset availability, accessibility

SCORING
  relation fit, payload fit, timing fit, variation, continuity, brand fit

PLANNING
  layout tokens, LAKA motion variables, transition, camera, caption behavior

VALIDATION
  linter, collision checks, timing coverage, repetition checks

OUTPUT
  storyboard JSON, preview HTML, optional MP4
```
