import json
from pathlib import Path

from laka_video.compiler import compile_project
from laka_video.scaffold import init_project
from laka_video.utils import load_yaml


def test_init_project_copies_audio_and_selects_audio_mode(tmp_path):
    root = Path(__file__).parents[1]
    paths = init_project(
        tmp_path / "new-project",
        audio=root / "examples" / "demo" / "audio.wav",
        title="Test Presentation",
    )
    project = load_yaml(paths["project"])
    assert project["source"]["mode"] == "audio"
    assert (paths["directory"] / project["source"]["audio"]).exists()
    assert paths["brand"].exists()
    assert paths["overrides"].exists()
    assert paths["data"].exists()


def test_selected_aspect_controls_compiled_dimensions(tmp_path):
    root = Path(__file__).parents[1]
    paths = init_project(
        tmp_path / "landscape-project",
        audio=root / "examples" / "demo" / "audio.wav",
        transcript=root / "examples" / "demo" / "subtitles.srt",
        aspect="16:9",
    )

    compiled = compile_project(paths["project"])
    story = json.loads(compiled["storyboard"].read_text(encoding="utf-8"))
    assert story["composition"]["width"] == 1920
    assert story["composition"]["height"] == 1080
    assert story["film"]["engine"] == "cue-film-v1"
    assert story["film"]["scenes"][0]["name"] == "Opening"
    assert story["film"]["scenes"][-1]["name"] == "Close"
    preview = compiled["preview"].read_text(encoding="utf-8")
    assert "window.OM_SCENES" in preview
    assert "window.CAPS" in preview
    assert "microProgress" not in preview
