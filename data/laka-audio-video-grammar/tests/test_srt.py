from pathlib import Path

from laka_video.srt import extract_laka_tags, parse_srt


def test_extract_laka_tag_removes_control_text():
    clean, tags = extract_laka_tags(
        '[[LAKA relation=transformation left="Pain" right="Project"]] Turn pain into projects.'
    )
    assert clean == 'Turn pain into projects.'
    assert tags == {"relation": "transformation", "left": "Pain", "right": "Project"}


def test_parse_demo_srt_keeps_timing_and_tags():
    path = Path(__file__).parents[1] / "examples" / "demo" / "subtitles.srt"
    cues = parse_srt(path)
    assert len(cues) == 5
    assert cues[0].start == 0.0
    assert cues[0].end == 4.0
    assert cues[0].tags["relation"] == "transformation"
    assert "[[LAKA" not in cues[0].text
