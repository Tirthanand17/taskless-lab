"""Offline tests for the cinematic narration-gap rejection gate."""
import importlib.util
from pathlib import Path
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"creative_pacing_gate.py"
SPEC=importlib.util.spec_from_file_location("pacing_gate",SCRIPT)
GATE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(GATE)


def test_actual_production_gap_pattern_is_rejected():
    gaps=[(12.644,16.223),(21.143,24.213),(28.375,32.254),
          (36.391,40.223),(45.349,48.021)]
    a=GATE.audit_intervals(gaps,48.021,narration_start=8)
    assert not a["pass"]
    assert len(a["gaps_exceeding_maximum"])==5
    assert a["total_long_gap_seconds"]>17


def test_continuous_explanation_below_threshold_passes():
    a=GATE.audit_intervals([(0,.5),(8,8.2),(15.1,15.8),
        (23.6,24.1),(31.7,32)],32,narration_start=8)
    assert a["pass"]


def test_opening_dialogue_pause_is_exempt():
    assert GATE.audit_intervals([(3.09,4.56)],32,narration_start=8)["pass"]


def test_no_music_based_forged_human_approval():
    assert GATE.audit_intervals([],32,narration_start=8)["human_voice_review"] is False


def test_parse_pair_and_end_of_file():
    log="[silencedetect] silence_start: 9.2\n[silencedetect] silence_end: 10.8 | silence_duration: 1.6\n"
    assert GATE.parse_silence_log(log,32)==[(9.2,10.8)]
    assert GATE.parse_silence_log("silence_start: 28.1",32)==[(28.1,32)]


@pytest.mark.parametrize("log",[
    "silence_end: 5.2","silence_start: 1.0\nsilence_start: 2.0",
    "silence_start: 8.0\nsilence_end: 7.0",
    "silence_start: 8.0\nsilence_end: 100.0"
])
def test_unpaired_or_invalid_audio_intervals_fail(log):
    with pytest.raises(ValueError):
        GATE.parse_silence_log(log,32)
