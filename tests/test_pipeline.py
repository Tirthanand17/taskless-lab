import json
from scripts.generate_srt import build_srt
from scripts.validate_release import validate


def test_srt_generation():
    text = build_srt([
        {"start": 0, "end": 1.5, "text": "Hook"},
        {"start": 1.5, "end": 3, "text": "Payoff"},
    ])
    assert "00:00:00,000 --> 00:00:01,500" in text
    assert "Hook" in text


def test_privacy_blocks_email():
    data = {
        "title": "Safe title",
        "description": "contact me at person@example.com",
        "captions": [{"start": 0, "end": 1, "text": "hello"}],
    }
    assert any("email" in e for e in validate(data, []))


def test_valid_manifest_passes():
    data = {
        "title": "A useful automation tutorial",
        "description": "Brand-only educational content.",
        "captions": [{"start": 0, "end": 1, "text": "hello"}],
    }
    assert validate(data, []) == []
