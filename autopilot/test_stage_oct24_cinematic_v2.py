"""Sanity checks for user-supplied cinematic media intake. No stock test video is released."""
from pathlib import Path
import pytest
from scripts.stage_oct24_cinematic_v2 import FILES,make_manifest
from autopilot.flow_episode_compositor import AssemblyError


def test_exact_3_new_flow_clips_required():
    assert [name for name,_ in FILES]==[
        "asha_jay_opening","cinematic_02","cinematic_03","cinematic_04"]


def test_media_intake_refuses_empty_directory(tmp_path):
    with pytest.raises(AssemblyError,match="Actual original/new video missing"):
        make_manifest(tmp_path)


def test_media_intake_refuses_nonexistent_directory(tmp_path):
    with pytest.raises(AssemblyError,match="Existing real"):
        make_manifest(tmp_path/"not_yet")


def test_media_intake_refuses_tiny_fake_mp4(tmp_path):
    p=tmp_path/"Asha_Jay_Approved_8s_Reference.mp4"
    p.write_bytes(b"pretend-media")
    with pytest.raises(AssemblyError,match="Actual original"):
        make_manifest(tmp_path)


def test_media_intake_refuses_forged_approved_opener(tmp_path):
    p=tmp_path/"Asha_Jay_Approved_8s_Reference.mp4"
    p.write_bytes(b"x"*120000)
    with pytest.raises(AssemblyError,match="Approved original opening"):
        make_manifest(tmp_path)
