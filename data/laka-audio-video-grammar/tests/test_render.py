import base64

import pytest

from laka_video.render_mp4 import _image_sources


def test_local_scene_images_are_embedded_for_deterministic_export(tmp_path):
    image = tmp_path / "assets" / "scene-001.png"
    image.parent.mkdir()
    image.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
    story = {
        "scenes": [
            {
                "asset": "assets/scene-001.png",
                "payload": {},
            }
        ]
    }

    sources = _image_sources(story, tmp_path)

    prefix, encoded = sources["assets/scene-001.png"].split(",", 1)
    assert prefix == "data:image/png;base64"
    assert base64.b64decode(encoded) == image.read_bytes()


def test_missing_scene_image_fails_before_export(tmp_path):
    story = {"scenes": [{"asset": "assets/missing.png", "payload": {}}]}

    with pytest.raises(FileNotFoundError, match="assets/missing.png"):
        _image_sources(story, tmp_path)
