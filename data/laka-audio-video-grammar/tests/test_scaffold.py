from pathlib import Path

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
