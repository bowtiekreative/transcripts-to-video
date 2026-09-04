# 3. Deterministic semantic grammar

The semantic layer does not attempt open-ended understanding. It recognizes explicit language relationships that can be represented visually.

## 3.1 Processing order

```text
SRT cue
→ remove LAKA tags
→ split into timed sentences/clauses
→ tokenize
→ score relation patterns
→ extract visual payload
→ retain all scores and evidence
```

Patterns are declared in `grammar/lexicon.yml`. A phrase can have several relation scores. The highest score becomes the primary relation unless an author override is present.

## 3.2 Relation families

### Title or identity

Signals:

```text
hello, my name is, I am, introducing, welcome, this is
```

Visual candidates:

```text
title_card, identity_card, image_statement
```

### Definition

Signals:

```text
X means Y
X is a Y
X refers to Y
that means Y
by X, I mean Y
```

Payload:

```yaml
term: X
definition: Y
```

Visual candidates:

```text
definition_card, equation, term_and_description
```

### List or set

Signals:

```text
including, such as, things like, first/second/third,
commas followed by and/or, a repeated grammatical frame
```

Payload:

```yaml
items: [A, B, C]
```

Visual candidates:

```text
list_stack, chips, icon_grid, card_grid
```

### Ordered sequence

Signals:

```text
first, next, then, finally, start with, followed by, step
```

Payload:

```yaml
items: [step 1, step 2, step 3]
ordered: true
```

Visual candidates:

```text
steps, process_flow, path
```

### Timeline

Signals:

```text
before, after, at age, in 2026, years ago, today, later, when
```

Payload:

```yaml
events:
  - time: before
    event: ...
  - time: after
    event: ...
```

Visual candidates:

```text
timeline, milestone, before_after
```

### Contrast

Signals:

```text
but, however, instead, rather than, while, yet, not X but Y
```

Payload:

```yaml
left: X
right: Y
relation: contrast
```

Visual candidates:

```text
before_after, comparison_split, crossed_replacement
```

### Comparison

Signals:

```text
more than, less than, compared with, versus, similar to, different from
```

Payload:

```yaml
left: A
right: B
criterion: optional
```

Visual candidates:

```text
comparison_split, scale, table, paired_bars
```

### Transformation

Signals:

```text
from X to Y, turn X into Y, become, changed into, convert
```

Payload:

```yaml
from: X
to: Y
```

Visual candidates:

```text
transformation_arrow, bridge, before_after, morph_state
```

### Cause and effect

Signals:

```text
because, therefore, so, leads to, results in, creates, causes
```

Payload:

```yaml
cause: X
effect: Y
```

Visual candidates:

```text
cause_effect, causal_chain, branching_effect
```

### Problem and solution

Signals:

```text
problem, challenge, obstacle, pain, issue
combined with solve, build, fix, answer, approach, useful
```

Payload:

```yaml
problem: X
response: Y
```

Visual candidates:

```text
problem_solution, bridge, diagnosis_to_action
```

### Hierarchy or part/whole

Signals:

```text
part of, consists of, includes, contains, under, within, category
```

Payload:

```yaml
parent: X
children: [A, B, C]
```

Visual candidates:

```text
hierarchy_tree, nested_containers, stack
```

### Network

Signals:

```text
connect, together, linked, sources, ecosystem, network, relationships
```

Payload:

```yaml
center: X
nodes: [A, B, C]
```

Visual candidates:

```text
network, constellation, hub_and_spoke
```

### Cycle or feedback

Signals:

```text
cycle, loop, repeat, feedback, again, evolve, continuously
```

Payload:

```yaml
stages: [A, B, C]
closed: true
```

Visual candidates:

```text
cycle, feedback_loop
```

### Conditional or decision rule

Signals:

```text
if X, then Y; when X, do Y; unless X, do Y
```

Payload:

```yaml
left: condition X
right: response Y
```

Multiple condition-response pairs become a bounded list. Visual candidates:

```text
condition_cards, decision_path, steps
```

The engine only uses this relation when the condition and response are explicit. It does not infer a missing consequence.

### Quantity

Signals:

```text
digits, percentages, currency, dates, age, counts, measured values
```

Payload:

```yaml
number: 41
label: diagnosed
unit: years
```

Visual candidates:

```text
big_number, bars, counter, scale
```

A chart is only selected when values and comparable labels exist. A single number becomes a big-number scene instead of a fabricated chart.

### Question

Signals:

```text
question mark, what, why, how, who, where, when at sentence start
```

Visual candidates:

```text
question_card, spotlight, branching_questions
```

### Call to action

Signals:

```text
visit, book, download, join, subscribe, explore, call, bring, let us
```

Payload:

```yaml
action: book
object: clarity session
destination: optional URL
```

Visual candidates:

```text
cta_card, url_card, action_steps
```

## 3.3 Relation scoring

Each matched pattern adds its declared weight. Structural evidence adds bonuses.

Example:

```text
"Instead of only asking how to fit into an existing system,
 I started asking how the system could work differently."
```

Possible scores:

```yaml
contrast:
  pattern_instead_of: 5
  paired_clause: 3
  total: 8
question:
  how_token: 1
transformation:
  changed_state_language: 2
```

The primary relation is `contrast`. Secondary relations remain available to template scoring.

## 3.4 Payload extraction

Classification answers **what relationship exists**. Payload extraction answers **which text occupies the visual roles**.

The extractor uses ordered rules:

1. author-provided payload;
2. explicit connector split (`from X to Y`, `X because Y`);
3. colon split;
4. enumerator split;
5. comma/conjunction list split;
6. sentence clauses;
7. concise headline plus full supporting sentence.

The extractor never invents a missing value. When a required role is absent, templates needing that role are disqualified.

## 3.5 Headline extraction

The deterministic headline selector scores spans using:

- sentence position;
- numbers and named terms;
- relation-bearing phrases;
- repeated topic words;
- author emphasis markers;
- length between two and nine words;
- penalties for stop-word-only starts and unfinished connectors.

It may shorten by deleting leading discourse phrases, but it does not paraphrase. Examples:

```text
"Today, I’m a cognitive architect and innovation strategist."
→ "Cognitive architect and innovation strategist"

"The question isn’t just how to get more people through the door."
→ "More people through the door?"
```

When exact wording matters, use `headline="..."` in an author tag.

## 3.6 Author tags

Inline syntax:

```text
[[LAKA key=value key="value with spaces"]]
```

Example:

```text
[[LAKA relation=transformation infographic=bridge
headline="Attention into action" left=Attention right=Action
motion=connect]]
Through Bow Tie Kreative, I build websites, funnels, and systems
that help businesses turn attention into action.
```

Tags override, but do not erase, automatic analysis. The storyboard retains both:

```json
{
  "automatic_relation": "transformation",
  "selected_relation": "transformation",
  "overrides": {"infographic": "bridge"}
}
```

This makes directed mode editable without making it opaque.
