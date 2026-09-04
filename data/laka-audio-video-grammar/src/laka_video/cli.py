from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .audio import analyze_audio
from .compiler import compile_project
from .render_mp4 import render_mp4
from .report import write_decision_report
from .scaffold import init_project
from .utils import default_grammar_dir, load_yaml, write_json


def _print_paths(paths: dict[str, Path]) -> None:
    for key, value in paths.items():
        print(f"{key:12s} {value}")


def cmd_compile(args: argparse.Namespace) -> int:
    paths = compile_project(args.project, args.grammar, reduced_motion=getattr(args, "reduced_motion", False))
    _print_paths(paths)
    report = json.loads(paths["lint"].read_text(encoding="utf-8"))
    print(f"lint         {report['status']} ({report['score']}/100)")
    if args.strict and report["status"] != "pass":
        return 2
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    paths = compile_project(args.project, args.grammar, reduced_motion=getattr(args, "reduced_motion", False))
    report = json.loads(paths["lint"].read_text(encoding="utf-8"))
    if args.strict and report["status"] != "pass":
        print(f"Refusing render because lint status is {report['status']}.", file=sys.stderr)
        return 2
    last_percent = -1
    def progress(done: int, total: int) -> None:
        nonlocal last_percent
        percent = int(done / max(1, total) * 100)
        if percent >= last_percent + 5 or done == total:
            print(f"render       {percent:3d}% ({done}/{total} frames)", flush=True)
            last_percent = percent
    output = render_mp4(paths["preview"], paths["storyboard"], args.output, args.quality, progress)
    _print_paths(paths)
    print(f"video        {output}")
    return 0


def cmd_inspect_audio(args: argparse.Namespace) -> int:
    grammar = Path(args.grammar).resolve() if args.grammar else default_grammar_dir()
    defaults = load_yaml(grammar / "defaults.yml")
    analysis = analyze_audio(args.audio, defaults.get("audio", {}))
    if args.output:
        write_json(args.output, analysis.public_summary())
        print(args.output)
    else:
        print(json.dumps(analysis.public_summary(), ensure_ascii=False, indent=2))
    return 0




def cmd_init(args: argparse.Namespace) -> int:
    paths = init_project(
        destination=args.directory,
        audio=args.audio,
        transcript=args.transcript,
        title=args.title,
        mode=args.mode,
        aspect=args.aspect,
        seed=args.seed,
        force=args.force,
    )
    _print_paths(paths)
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    output = write_decision_report(args.storyboard, args.output)
    print(f"report       {output}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    browser = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    playwright_state = "NOT INSTALLED"
    try:
        import playwright

        playwright_state = "installed"
        if browser is None:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as runtime:
                bundled = Path(runtime.chromium.executable_path)
                if bundled.exists():
                    browser = str(bundled)
    except Exception:
        pass
    checks = {"ffmpeg": ffmpeg, "ffprobe": ffprobe, "chromium": browser}
    failed = False
    for name, path in checks.items():
        state = path or "NOT FOUND"
        print(f"{name:12s} {state}")
        failed = failed or path is None
    print(f"{'playwright':12s} {playwright_state}")
    failed = failed or playwright_state != "installed"
    return 1 if failed else 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .web import run_server

    run_server(host=args.host, port=args.port, job_root=args.job_root, debug=args.debug)
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="laka-video", description="Deterministic LAKA audio-to-visual compiler")
    parser.add_argument("--grammar", help="Path to an alternate grammar directory")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="Create a reusable no-AI LAVC project scaffold")
    init_p.add_argument("directory")
    init_p.add_argument("--audio", help="Audio file to copy into the project")
    init_p.add_argument("--transcript", help="SRT file to copy into the project")
    init_p.add_argument("--title", default="My LAKA Video")
    init_p.add_argument("--mode", choices=["auto", "audio", "transcript", "directed"], default="auto")
    init_p.add_argument("--aspect", choices=["9:16", "16:9", "1:1", "4:5"], default="9:16")
    init_p.add_argument("--seed", default=33)
    init_p.add_argument("--force", action="store_true")
    init_p.set_defaults(func=cmd_init)

    compile_p = sub.add_parser("compile", help="Compile project YAML to storyboard and preview HTML")
    compile_p.add_argument("project")
    compile_p.add_argument("--strict", action="store_true", help="Return a failure code unless lint passes")
    compile_p.add_argument("--reduced-motion", action="store_true",
                           help="Keep every duration, drop every translation (WCAG 2.3.3)")
    compile_p.set_defaults(func=cmd_compile)

    render_p = sub.add_parser("render", help="Compile and render an MP4")
    render_p.add_argument("project")
    render_p.add_argument("--output", help="MP4 output path")
    render_p.add_argument("--quality", choices=["draft", "standard", "high"], default="standard")
    render_p.add_argument("--strict", action="store_true")
    render_p.add_argument("--reduced-motion", action="store_true",
                          help="Keep every duration, drop every translation (WCAG 2.3.3)")
    render_p.set_defaults(func=cmd_render)

    inspect_p = sub.add_parser("inspect-audio", help="Print deterministic acoustic analysis")
    inspect_p.add_argument("audio")
    inspect_p.add_argument("--output")
    inspect_p.set_defaults(func=cmd_inspect_audio)

    explain_p = sub.add_parser("explain", help="Write a human-readable audit of every compiler decision")
    explain_p.add_argument("storyboard")
    explain_p.add_argument("--output")
    explain_p.set_defaults(func=cmd_explain)

    doctor_p = sub.add_parser("doctor", help="Check local render dependencies")
    doctor_p.set_defaults(func=cmd_doctor)

    serve_p = sub.add_parser("serve", help="Run the local drag-and-drop video compiler")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8765)
    serve_p.add_argument("--job-root", help="Directory for uploaded files and rendered jobs")
    serve_p.add_argument("--debug", action="store_true")
    serve_p.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
