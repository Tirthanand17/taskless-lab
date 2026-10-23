"""32-second cinematic V2 contract tests. No fake MP4s called cinematic footage."""
from copy import deepcopy
import pytest
from autopilot.flow_episode_compositor import (
    APPROVED_REEXPORTED_OPENING_SHA256, REJECTED_48S_SHA256,
    AssemblyError, check_cinematic_v2_contract, validate_manifest,
)
from scripts.produce_oct24_english_v2_continuous_voice import voice_gap_report


def shot_manifest():
    sha=[APPROVED_REEXPORTED_OPENING_SHA256,"b"*64,"c"*64,"d"*64]
    ids=["asha_jay_opening","cinematic_02","cinematic_03","cinematic_04"]
    return {
        "schema_version":1,"episode_id":"fm_20261024_short_en",
        "creative_revision":"cinematic_v2_32s",
        "segments":[
           {"id":name,"path":f"/real-clip-not-yet-uploaded/{name}.mp4",
            "source_start_ms":0,"duration_ms":8000,"sha256":sha[i]}
            for i,name in enumerate(ids)]
    }


def test_four_real_cinematic_source_slots_have_strict_32s_contract():
    assert check_cinematic_v2_contract(shot_manifest()) == 32000


def test_actual_media_still_required_no_fake_release_from_manifest():
    with pytest.raises(AssemblyError,"Missing, symlinked"):
        validate_manifest(shot_manifest())


@pytest.mark.parametrize("mode",["cinematic_v3_24s","flat_vector_32s","unknown"])
def test_unknown_revision_is_rejected(mode):
    j=shot_manifest();j["creative_revision"]=mode
    with pytest.raises(AssemblyError):
        check_cinematic_v2_contract(j)


def test_three_new_clips_must_exist():
    j=shot_manifest();j["segments"].pop()
    with pytest.raises(AssemblyError,"exactly four"):
        check_cinematic_v2_contract(j)


def test_cannot_use_original_rejected_48_second_export():
    j=shot_manifest();j["segments"][2]["sha256"]=REJECTED_48S_SHA256
    with pytest.raises(AssemblyError,"owner-rejected"):
        check_cinematic_v2_contract(j)


def test_cannot_duplicate_one_8_second_video_as_three_scenes():
    j=shot_manifest();j["segments"][2]["sha256"]=j["segments"][1]["sha256"]
    with pytest.raises(AssemblyError,"Duplicate"):
        check_cinematic_v2_contract(j)


def test_cannot_repeat_clip_path_under_separate_aliases():
    j=shot_manifest();j["segments"][2]["path"]=j["segments"][1]["path"]
    with pytest.raises(AssemblyError,"unique"):
        check_cinematic_v2_contract(j)


def test_cannot_replace_owner_approved_opening_with_random_start():
    j=shot_manifest();j["segments"][0]["sha256"]="e"*64
    with pytest.raises(AssemblyError,"exact approved"):
        check_cinematic_v2_contract(j)


def test_cannot_shuffle_storyboard_scenes():
    j=shot_manifest();j["segments"][2],j["segments"][3]=j["segments"][3],j["segments"][2]
    with pytest.raises(AssemblyError,"Wrong 32s order"):
        check_cinematic_v2_contract(j)


def test_no_padding_from_missing_duration():
    j=shot_manifest();j["segments"][-1]["duration_ms"]=6000
    with pytest.raises(AssemblyError,"eight-second"):
        check_cinematic_v2_contract(j)


def test_no_partial_preview_claimed_as_final_cinematic_32s():
    with pytest.raises(AssemblyError,"refuses synthetic"):
        validate_manifest(shot_manifest(),test_mode=True)


def test_wrong_english_episode_cannot_activate_special_short_target():
    j=shot_manifest();j["episode_id"]="fm_20261024_short_hi"
    with pytest.raises(AssemblyError,"Only the approved English"):
        check_cinematic_v2_contract(j)
