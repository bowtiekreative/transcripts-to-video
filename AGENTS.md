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

## Testing Guidelines

Tests use `pytest` and follow `tests/test_<area>.py` with functions named `test_<behavior>`. Add focused unit tests for parser or rule changes and an integration assertion when generated storyboard behavior changes. Verify repeatability, schema validity, and lint scores where applicable. Run `make test` before submitting changes; use `make demo` for compiler or grammar edits.

## Commit & Pull Request Guidelines

History currently contains only `first commit`, so no mature convention exists. Use short, imperative subjects such as `Add timeline selection rule`. Keep commits narrowly scoped. Pull requests should explain the behavioral change, list validation commands, and identify affected grammar, examples, or generated output. Include preview screenshots or a short rendered sample when visual behavior changes, and link relevant issues.

## Security & Configuration

Keep `.env`, media credentials, and machine-specific paths untracked. The compiler is intentionally local and deterministic; document and justify any new network-facing dependency before adding it.
