# 8. Authoring workflow

## 8.1 Fastest deterministic workflow

```text
1. Record or supply audio.
2. Supply an SRT transcript.
3. Choose a brand preset and output format.
4. Compile.
5. Review the generated storyboard and linter report.
6. Add LAKA tags only where the automatic relationship is wrong or too generic.
7. Compile again.
8. Render MP4.
```

The purpose of authoring is not to hand-animate every frame. It is to correct meaning and intent at the smallest useful level.

## 8.2 Project file

```yaml
project:
  id: ryan-reintroduction
  title: Ryan Perez — Reintroduction
  seed: 33

source:
  audio: audio.mp3
  transcript: subtitles.srt
  mode: transcript
  music: null

content:
  speaker: Ryan Perez
  organization: Bow Tie Kreative
  destination: ryanperez.ca

brand:
  preset: ../../grammar/brand.example.yml

output:
  directory: build
  aspect: "9:16"
  width: 1080
  height: 1920
  fps: 30
  tail_seconds: 2.5
  captions: karaoke

rules:
  min_scene_seconds: 3.5
  target_scene_seconds: 7.5
  max_scene_seconds: 12.0
  max_words_on_screen: 18
  repeat_window: 3
```

All paths are resolved relative to the project file.

## 8.3 Audio-only workflow

Use when no transcript exists.

```yaml
source:
  audio: music.wav
  transcript: null
  mode: audio

content:
  title: Project title
  chapters:
    - Introduction
    - Development
    - Resolution
```

The engine will:

- find silence and energy boundaries;
- estimate tempo and onset density;
- create measured sections;
- use title cards, chapter cards, waveform fields, progress paths, and supplied metadata;
- synchronize motion to acoustic events.

It will not invent semantic labels.

## 8.4 Transcript workflow

An SRT cue can be broad. LAVC splits cue text into timed sentences and clauses by weighted duration. For precise scene boundaries, create shorter cues.

Better SRT:

```text
1
00:00:00,000 --> 00:00:05,200
The problem is information that goes stale.

2
00:00:05,200 --> 00:00:11,600
DigitalStemCell creates living documents that show what changed.
```

Less controllable SRT:

```text
1
00:00:00,000 --> 00:00:11,600
The problem is information that goes stale. DigitalStemCell creates living documents that show what changed.
```

Both compile, but explicit cue boundaries carry stronger author intent.

## 8.5 Directed workflow with inline tags

### Force only the relation

```text
[[LAKA relation=contrast]]
A place can look welcoming in a photograph and feel completely different when you are there.
```

### Force the template

```text
[[LAKA infographic=comparison_split]]
A place can look welcoming in a photograph and feel completely different when you are there.
```

### Supply exact roles

```text
[[LAKA relation=contrast infographic=comparison_split
left="Looks welcoming" right="Feels inaccessible"
left_label=Photograph right_label=Experience]]
```

### Force motion

```text
[[LAKA motion=compare]]
```

### Choose an asset

```text
[[LAKA asset=portrait crop_focus="0.50,0.22"]]
```

## 8.6 Sidecar overrides

For clean transcripts, use a YAML file:

```yaml
overrides:
  - cue: 3
    relation: timeline
    infographic: timeline
    headline: Diagnosed at 41
    events:
      - time: Before
        event: Building workarounds
      - time: After
        event: Designing systems differently

  - time: [60.56, 68.20]
    relation: transformation
    infographic: transformation_arrow
    left: Attention
    right: Action
```

Matching priority:

```text
scene id → cue id → exact time interval → text phrase
```

## 8.7 Data-driven scenes

Add a data sidecar:

```yaml
data:
  lead_conversion:
    unit: percent
    series:
      - label: Visitors
        value: 100
      - label: Leads
        value: 12
      - label: Qualified
        value: 4
```

Reference it from a tag:

```text
[[LAKA infographic=funnel data=lead_conversion]]
```

The engine renders only supplied values. It does not infer or fabricate data.

## 8.8 Review the storyboard

The most important fields to inspect:

```text
start/end
headline
primary_relation
selected_template
payload
motion
selection_trace
lint warnings
```

Typical corrections:

```text
wrong relationship → set relation
right relationship, wrong visual → set infographic
weak headline → set headline
bad split → set left/right or items
motion too strong → set motion or reduced_motion
scene too dense → split SRT cue or paginate
```

## 8.9 Batch production

A production folder can contain many project files:

```text
projects/
  episode-001.yml
  episode-002.yml
  episode-003.yml
```

Compile deterministically:

```bash
for f in projects/*.yml; do
  laka-video compile "$f"
done
```

Brand, template, and motion grammar remain shared. Only source files and project-specific overrides change.

## 8.10 Human effort model

The system moves effort away from frame-by-frame animation and toward explicit decisions:

```text
transcript quality
semantic corrections
brand rules
asset metadata
exception handling
```

Once those rules exist, repeated production becomes compilation rather than reinvention.
