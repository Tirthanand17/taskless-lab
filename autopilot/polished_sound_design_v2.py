"""B4e1 ORIGINAL minimal programmatic micro-SFX, NOT copied reference audio.

Created mathematically using bounded deterministic oscillators/noise only;
no music/notification recording, no copyrighted jingle, no branded sound,
no owner data, no network or paid model. Speech remains original Kokoro
narration and production still needs human listening, rights and consent.

Use <=8 short UI accents for a 20-scene long and <=5 for a 6-scene Short:
soft click, gentle notification ping, whoosh, and numerical reveal pulse.
The effects map to storyboard beats with precise PCM timestamps. Their
peak amplitudes are limited; the final FFmpeg audio will still be mastered.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path

STATUS="ORIGINAL_LOW_LEVEL_SFX_TIMED_TO_SCENE_CHANGES_NOT_RIGHTS_APPROVED"
SCHEDULE={
    "lunar_signal":((0,"soft_tick"),(1,"soft_ping"),(2,"soft_sweep"),
                    (3,"soft_tick"),(4,"reveal_pulse")),
    "quake_energy":((0,"soft_tick"),(1,"soft_sweep"),(2,"reveal_pulse"),
                    (3,"soft_tick"),(4,"soft_ping")),
    "file_transfer":((0,"soft_tick"),(2,"soft_ping"),(4,"soft_sweep"),
                     (7,"soft_tick"),(10,"reveal_pulse"),(13,"soft_sweep"),
                     (16,"soft_ping"),(19,"soft_tick")),
}


class AudioPolishRejected(ValueError):
    """Cannot modify a missing, unsafe or inconsistent narration file."""


def _sfx(name:str,sample_rate:int,seed:int):
    import numpy as np
    sizes={
        "soft_tick":.095,"soft_ping":.21,
        "soft_sweep":.29,"reveal_pulse":.25,
    }
    if name not in sizes or sample_rate not in (22050,24000,44100,48000):
        raise AudioPolishRejected("Unexpected user audio waveform recipe")
    n=int(sample_rate*sizes[name])
    t=np.arange(n,dtype=np.float64)/sample_rate
    if name=="soft_tick":
        rng=np.random.default_rng(seed)
        raw=rng.normal(0,1,n)
        raw=np.diff(np.pad(raw,(1,0)))
        raw=raw/(max(1e-9,np.max(abs(raw))))
        env=(1-np.exp(-t/.003))*np.exp(-t/.022)
        wave=.019*raw*env
    elif name=="soft_ping":
        chirp=np.sin(2*np.pi*(660*t+150*t*t))
        harmon=.22*np.sin(2*np.pi*990*t)
        env=(1-np.exp(-t/.010))*np.exp(-t/.087)
        wave=.028*(chirp+harmon)*env
    elif name=="soft_sweep":
        rng=np.random.default_rng(seed+7919)
        noise=rng.normal(0,1,n)
        # Moving average removes rough low body, retaining very gentle air.
        filt=noise-np.convolve(noise,np.ones(80)/80,mode="same")
        filt/=max(1e-9,np.max(abs(filt)))
        env=np.sin(np.pi*np.clip(t/sizes[name],0,1))**2
        wave=.016*filt*env
    else:
        bass=np.sin(2*np.pi*(138*t-110*t*t))
        overtone=.22*np.sin(2*np.pi*(275*t-90*t*t))
        env=(1-np.exp(-t/.006))*np.exp(-t/.075)
        wave=.031*(bass+overtone)*env
    if np.max(abs(wave))>.05 or not np.isfinite(wave).all():
        raise AudioPolishRejected("SFX too loud or invalid")
    return wave.astype(np.float32)


def enrich_original_wav(wav:Path,theme:str,timings:list[dict])->dict:
    import numpy as np
    import soundfile as sf
    if theme not in SCHEDULE or type(timings) is not list:
        raise AudioPolishRejected("Unknown educational story beat sequence")
    if wav.is_symlink() or not wav.is_file():
        raise AudioPolishRejected("Original narration does not exist")
    y,sr=sf.read(str(wav),dtype="float32",always_2d=False)
    if (y.ndim!=1 or y.size<sr*18
        or sr not in (22050,24000,44100,48000)
        or not np.isfinite(y).all()):
        raise AudioPolishRejected("Unexpected raw mono narration WAV")
    spec=SCHEDULE[theme]
    if len(timings)<max(i for i,_ in spec)+1:
        raise AudioPolishRejected("Incomplete original measured narration scenes")
    prev=0.0
    duration=y.size/sr
    for row in timings:
        if (type(row) is not dict or type(row.get("start")) not in (float,int)
            or type(row.get("duration")) not in (float,int)
            or not math.isfinite(row["start"])
            or not math.isfinite(row["duration"])
            or abs(row["start"]-prev)>.009 or row["duration"]<=0):
            raise AudioPolishRejected("Voice and scene boundaries desynchronized")
        prev=row["start"]+row["duration"]
    if abs(prev-duration)>.09:
        raise AudioPolishRejected("Voice WAV duration differs from story scene timeline")
    enhanced=np.asarray(y,dtype=np.float64).copy()
    sample_count=0
    shots=[]
    for seq,(scene,kind) in enumerate(spec):
        # Offset 0.10 s from spoken scene start to prevent harsh attack at
        # a cut. Full WAV is unchanged outside short sparse accents.
        t=timings[scene]["start"]+.1
        start=round(t*sr)
        effect=_sfx(kind,sr,seed=991+scene*71+seq)
        if start+len(effect)>=enhanced.size:
            raise AudioPolishRejected("Effect extends past voice speech timeline")
        enhanced[start:start+len(effect)]+=effect
        sample_count+=len(effect)
        shots.append({"scene":scene,"effect":kind,"at_ms":round(t*1000)})
    if np.max(abs(enhanced))>1.0:
        raise AudioPolishRejected("Clipping after sound-design layer")
    if (len(shots)>8 or sample_count>sr*3.0
        or max(abs(enhanced-y))>.051):
        raise AudioPolishRejected("Unbounded or intrusive UI sound effects")
    sf.write(str(wav),enhanced.astype(np.float32),sr,subtype="PCM_16")
    descriptor={"recipe_version":"flowminute-original-soft-ui-fx-v2",
                "theme":theme,"sample_rate":sr,
                "duration_samples":len(y),"effects":shots}
    digest=sha256(json.dumps(descriptor,sort_keys=True,
                             separators=(",",":")).encode()).hexdigest()
    return {
        "status":STATUS,
        "original_programmatic_effects":len(shots),
        "seconds_original_ui_sfx_total":round(sample_count/sr,3),
        "sound_design_recipe_sha256":digest,
        "external_sound_effects_or_music_imported":False,
        "actual_human_listening_and_license_review":False,
        "release_authorized":False,
    }
