import json
from pathlib import Path

from laka_video.compiler import compile_project


def test_demo_compiles_to_auditable_storyboard():
    root = Path(__file__).parents[1]
    paths = compile_project(root / "examples" / "demo" / "project.yml")
    story = json.loads(paths["storyboard"].read_text(encoding="utf-8"))
    report = json.loads(paths["lint"].read_text(encoding="utf-8"))
    assert len(story["scenes"]) == 5
    assert story["scenes"][0]["template"] == "transformation_arrow"
    assert story["scenes"][-1]["template"] == "cta_card"
    assert story["scenes"][0]["selection_trace"]["candidates"]
    assert paths["decisions"].exists()
    assert "LAKA motion volume" in paths["decisions"].read_text(encoding="utf-8")
    assert report["score"] >= 95
