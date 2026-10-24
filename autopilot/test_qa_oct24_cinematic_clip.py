"""Unit tests of real-clip quality gates; never assert synthetic footage is creative output."""
from pathlib import Path
import pytest
from scripts.qa_oct24_cinematic_clip import freeze_periods, inspect


def test_parse_freeze_interval_and_trailing_unclosed_end():
    log="freeze_start: 1.2\nfreeze_end: 2.6\nfreeze_start: 5.1\n"
    assert freeze_periods(log,8)==[(1.2,2.6),(5.1,8)]


def test_missing_actual_scene_is_rejected(tmp_path):
    result=inspect(tmp_path/"scene_02_real.mp4","cinematic_02")
    assert result["status"]=="BLOCKED"
    assert "MISSING_OR_UNSAFE_MP4" in result["issues"]
    assert result["ready_to_publish"] is False


def test_fake_tiny_mp4_is_rejected(tmp_path):
    p=tmp_path/"scene_02_real.mp4";p.write_bytes(b"not-a-video")
    result=inspect(p,"cinematic_02")
    assert "MEDIA_SIZE_NOT_VALID" in result["issues"]


def test_unknown_source_is_not_assumed_to_be_3d(tmp_path):
    with pytest.raises(ValueError,match="Unknown"):
        inspect(tmp_path/"video.mp4","flat_vector_slide")


def test_symlinked_file_is_rejected(tmp_path):
    target=tmp_path/"shot_real.mp4";target.write_bytes(b"data")
    link=tmp_path/"scene_04_real.mp4"
    try:link.symlink_to(target)
    except OSError:pytest.skip("Symlinks not permitted")
    assert "MISSING_OR_UNSAFE_MP4" in inspect(link,"cinematic_04")["issues"]
