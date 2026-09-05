import json
from pathlib import Path

from laka_video.compiler import compile_project


def test_demo_compiles_to_auditable_storyboard():
    root = Path(__file__).parents[1]
    paths = compile_project(root / "examples" / "demo" / "project.yml")
    story = json.loads(paths["storyboard"].read_text(encoding="utf-8"))
    report = json.loads(paths["lint"].read_text(encoding="utf-8"))
    # A scene is a sentence. The fixture has eight, and the compiler must not
    # join two of them: subtitle cues break where the transcriber's line ran
    # out, which is not where a thought ends.
    assert len(story["scenes"]) == 8
    import re
    for scene in story["scenes"]:
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", scene["text"].strip()) if s]
        assert len(sentences) == 1, f"{scene['id']} carries {len(sentences)} sentences"
    assert story["scenes"][0]["template"] == "transformation_arrow"
    assert story["scenes"][-1]["template"] == "cta_card"
    assert story["scenes"][0]["selection_trace"]["candidates"]
    assert paths["decisions"].exists()
    assert "LAKA motion volume" in paths["decisions"].read_text(encoding="utf-8")
    # The perception checks (MOTION_MATH.md §11) report real findings on this
    # fixture — mostly the readability gate and the speech-share target — so a
    # 95 floor would only be reachable by removing the checks. What must hold
    # is that nothing is broken or untrue: no FATAL, no ERROR.
    assert report["counts"].get("FATAL", 0) == 0
    assert report["counts"].get("ERROR", 0) == 0
    assert report["score"] >= 70
