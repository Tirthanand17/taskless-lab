"""Security tests for prepublication editorial metadata vs finished releases."""
from scripts.validate_release import validate


def _draft(description="The announcement is dated 2026-10-07."):
    return {
        "id": "test_episode",
        "title": "A real example about AI automation",
        "description": description,
        "source_script": "motion-v2/script-example.txt",
        "type": "short"
    }


def test_editorial_metadata_does_not_require_already_completed_captions():
    assert validate(_draft(), [], editorial_only=True) == []


def test_release_ready_still_requires_verified_captions():
    assert "captions are required" in validate(_draft(), [])


def test_iso_dates_and_https_urls_arent_private_phone_numbers():
    d = _draft("October 7 2026: https://github.blog/changelog/2026-10-07-example and updated on 2026-10-07.")
    assert not any("phone" in e for e in validate(d, [], editorial_only=True))


def test_real_private_phone_like_number_is_blocked():
    assert "release contains a phone-like number" in validate(
        _draft("Private contact: +91 98765 43210"), [], editorial_only=True
    )


def test_editorial_missing_script_is_not_approved():
    d = _draft()
    del d["source_script"]
    assert "editorial draft requires source_script" in validate(d, [], editorial_only=True)


def test_editorial_path_traversal_blocked():
    d = _draft()
    d["source_script"] = "../secret.txt"
    assert "unsafe source_script path" in validate(d, [], editorial_only=True)
