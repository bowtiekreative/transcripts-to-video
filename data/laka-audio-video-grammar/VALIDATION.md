# Validation record

This release was validated as a deterministic local compiler.

## Automated checks

- Python source compilation: pass
- Unit and integration tests: 11 passed
- Project JSON Schema validation: pass
- Storyboard JSON Schema validation: pass for all included examples
- YAML and JSON grammar parsing: pass
- Generated player JavaScript syntax: pass
- Wheel build with packaged grammar and player: pass
- Wheel install and compile from outside the repository: pass

## Included example results

| Example | Mode | Scenes | Lint score |
|---|---|---:|---:|
| `examples/audio-only` | DSP-only audio | 5 | 99.5/100 |
| `examples/demo` | directed SRT | 5 | 100/100 |
| `examples/ryan-reintroduction` | transcript | 29 | 99.75/100 |

The Ryan example selects title, list, contrast, question, big-number, quote, problem/response, steps, transformation, network, conditional, and call-to-action structures without a language model.

## Rendering checks

- Browser seek-and-render at arbitrary timestamps: pass
- Short MP4 smoke render: 1.5 seconds, H.264/AAC, 270×480 at 12 fps
- Included demo MP4: 32.5 seconds, H.264/AAC, 270×480 at 12 fps

## No-AI boundary

The source tree was checked for network clients and model integrations. It contains no OpenAI, Anthropic, Gemini, Ollama, PyTorch, TensorFlow, transformer, or remote inference dependency. Semantic results are produced by explicit dictionaries, regular expressions, author tags, data constraints, and deterministic scoring. Audio-only results use local DSP and do not claim to understand spoken meaning.
