"""B4g3: original, subtle PCM-synchronized Flowminute UI sound design.

No downloaded music/FX, voice copying, paid inference, YouTube calls, or
claimed human listening. This uses the *existing* B4e1 original mathematical
soft effects, with exact measured PCM/FFconcat visual cut boundaries. The
background is a quiet synthesized non-melodic tonal layer, not a music track.

The source narrator words, PCM clock, scene IDs, narration cue positions and
caption layout never change. Every effect occurs at one distinct educational
focus reveal; no rhythmic loop, spinner, or false quality approval.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math

from autopilot.one_way_storyboard_timing_b4g2 import (
    OneWayStageRefused, active_focus_sequence, grammar_for_original_scene,
    stage_hold_seconds,
)

STATUS="B4G3_ORIGINAL_SUBTLE_SOUND_ALIGNED_TO_REAL_PCM_NO_PUBLISH"
SFX_PER_GRAMMAR={
    "compare":("soft_tick","soft_ping"),
    "gate":("soft_tick","reveal_pulse"),
    "steps":("soft_tick","soft_ping","soft_tick"),
    "matrix":("soft_tick","soft_sweep","reveal_pulse"),
}
SFX_GAIN=0.34
# The bed is intentionally a barely-audible harmonic texture, not a song.
# Max oscillator sum (before fade): 0.0024 (~ -52.4 dBFS peak).
BED_COMPONENTS=((110.0,0.0012),(164.81,0.0008),(220.0,0.0004))
BED_ATTACK_SECONDS=1.0
BED_RELEASE_SECONDS=1.2


class OriginalSoundRefused(ValueError):
    """Invalid original PCM phase cut, sound budget, or audible peak ceiling."""


def _need(ok:bool,why:str)->None:
    if not ok:
        raise OriginalSoundRefused(why)


def plan_pcm_cut_effects(scene_ids:list[str],scene_lengths:list[float],
                         sample_rate:int,*,reveal_seconds:float=.36)->list[dict]:
    """Produce only deterministic one-way focus transition points.

    Each event's sample index is rounded from the SAME FFconcat segment
    periods used for scene visuals, never estimated from text lengths.
    """
    _need(type(scene_ids) is list and type(scene_lengths) is list
          and len(scene_ids) in (4,9) and len(scene_ids)==len(scene_lengths)
          and type(sample_rate) is int and sample_rate in (
              16000,22050,24000,44100,48000)
          and type(reveal_seconds) in (int,float)
          and math.isfinite(reveal_seconds)
          and .15<=reveal_seconds<=.5,
          "Invalid original narration/visual scene timing source")
    _need(all(type(x) in (int,float) and math.isfinite(x) and
              3<=x<=55 for x in scene_lengths)
          and sum(scene_lengths)<=340,
          "Unbounded or missing measured PCM scenes")
    events=[]
    scene_start=0.0
    for index,(scene_id,length) in enumerate(zip(scene_ids,scene_lengths),1):
        try:
            grammar=grammar_for_original_scene(scene_id)
            focus=active_focus_sequence(grammar)
            holds=stage_hold_seconds(length,len(focus),
                                     min(reveal_seconds,length/6))
        except OneWayStageRefused:
            raise OriginalSoundRefused(
                "Unknown scene or absent real visual staging") from None
        _need(len(SFX_PER_GRAMMAR[grammar])==len(focus)-1,
              "Original sound and picture stage count differs")
        position=scene_start
        for phase,kind in enumerate(SFX_PER_GRAMMAR[grammar],1):
            position+=holds[phase-1]
            samples=round(position*sample_rate)
            _need(samples>=0 and position<scene_start+length-1.0,
                  "Visual accent overlaps scene tail")
            events.append({
                "scene_number":index,
                "phase_number":phase,
                "sample_index":samples,
                "at_seconds":round(samples/sample_rate,3),
                "effect":kind,
            })
        scene_start+=length
    _need(8<=len(events)<=30
          and all(a["sample_index"]<b["sample_index"]
                  for a,b in zip(events,events[1:]))
          and events[-1]["sample_index"]+round(.4*sample_rate)<
              round(scene_start*sample_rate),
          "Audio sound effects cannot be spaced within the original video")
    return events


def mix_original_sound_design(samples, sample_rate:int,
                              scene_ids:list[str],scene_lengths:list[float]):
    """Return unchanged-length original narration plus very quiet original FX.

    Imports NumPy only inside the real physical media worker so pytest's
    dependency-light quality gate can validate the PCM event plan separately.
    """
    import numpy as np
    from autopilot.polished_sound_design_v2 import _sfx
    _need(type(sample_rate) is int and sample_rate in (
        16000,22050,24000,44100,48000), "Unexpected PCM sample rate")
    y=np.asarray(samples)
    _need(y.ndim==1 and y.dtype==np.float32
          and y.size>=sample_rate*20
          and y.size<=sample_rate*340
          and np.isfinite(y).all(),
          "Invalid or unbounded synthesized mono PCM")
    duration=y.size/sample_rate
    _need(abs(sum(scene_lengths)-duration)<=.004,
          "Actual waveform samples and scene timing disagree")
    original_peak=float(np.max(np.abs(y)))
    _need(0.005<original_peak<=1.0,
          "Source narrator is silent, invalid or already clipped")
    events=plan_pcm_cut_effects(scene_ids,scene_lengths,sample_rate)
    _need(events[-1]["sample_index"]<y.size,
          "Effect would land outside original spoken signal")
    # Reduce *only* anomalously hot original PCM to preserve 1 dB of headroom.
    # No automatic loudness/true-peak target is claimed.
    gain=min(1.0,0.88/original_peak)
    output=y.astype(np.float64)*gain
    t=np.arange(y.size,dtype=np.float64)/sample_rate
    fade=np.minimum(
        1.0,np.minimum(t/BED_ATTACK_SECONDS,
                       (duration-t)/BED_RELEASE_SECONDS))
    fade=np.maximum(fade,0.0)
    ambient=np.zeros(y.size,dtype=np.float64)
    for frequency,amplitude in BED_COMPONENTS:
        ambient+=amplitude*np.sin(2*math.pi*frequency*t)
    output+=ambient*fade
    max_effect_peak=0.0
    for seq,event in enumerate(events):
        # These are mathematically synthesized original nonverbal UI notes.
        wave=_sfx(event["effect"],sample_rate,seed=7123+seq*37)
        n=len(wave)
        index=event["sample_index"]
        _need(n<sample_rate*.4 and index+n<y.size,
              "Original focus sound would leave its source video")
        raw=wave.astype(np.float64)*SFX_GAIN
        output[index:index+n]+=raw
        max_effect_peak=max(max_effect_peak,float(np.max(np.abs(raw))))
    peak=float(np.max(np.abs(output)))
    _need(math.isfinite(peak) and peak<.96,
          "Actual narration-plus-effects PCM dangerously close to clipping")
    diff=float(np.max(np.abs(output-y*gain)))
    _need(diff<=.022 and max_effect_peak<=.02,
          "Subtle original sound layer violates speech-first mixing ceiling")
    rendered=output.astype(np.float32)
    _need(np.isfinite(rendered).all()
          and rendered.size==y.size,
          "Audio layer changed sample rate or PCM duration")
    proof={
        "status":STATUS,
        "sample_rate":sample_rate,
        "original_pcm_samples":int(y.size),
        "original_pcm_duration_seconds":round(duration,3),
        "original_physical_scene_count":len(scene_ids),
        "original_programmatic_visual_cut_sound_count":len(events),
        "sound_events":events,
        "quiet_original_tonal_ambience":True,
        "ambient_max_unfaded_peak_dbfs":round(
            20*math.log10(sum(a for _,a in BED_COMPONENTS)),2),
        "original_pcm_peak_before_mix":round(original_peak,5),
        "gain_applied_to_voice":round(gain,6),
        "mixed_peak_below_minus_0_35_dbfs":peak<.96,
        "mixed_pcm_peak":round(peak,5),
        "source_original_narration_words_unchanged":True,
        "measured_integrated_lufs_or_true_peak":False,
        "human_audio_listening_completed":False,
        "third_party_songs_samples_or_effects":0,
        "youtube_release_authorized":False,
    }
    proof["original_programmatic_audio_recipe_sha256"]=sha256(
        json.dumps(proof,sort_keys=True,separators=(",",":")).encode()
    ).hexdigest()
    return rendered,proof
