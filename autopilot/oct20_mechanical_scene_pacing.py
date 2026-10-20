"""Original FlowMinute October-20 SHORT pacing benchmark and retime proposal.

Measures the ACTUAL generated PCM samples of all 7 EN or 7 HI original scenes
using ONLY an already-installed offline eSpeak CLI. The output is always
MECHANICAL-VOICE REJECTED, never publishable or evidence of natural narration.

Important implementation subtlety: eSpeak --stdout writes an unseekable WAV
RIFF header with a SENTINEL frame/data size (~2 GiB). Do NOT use WAV header
getnframes() to infer the real length. Decode the actual bounded emitted PCM
bytes and calculate frame count from the bytes successfully read.

Retiming is a separate nonbinding visual edit PROPOSAL: exact 24-fps 42/44s
length preserved; earlier scenes may borrow slack from later ones. Human
narration must independently dictate the production edit, not this reference.

No model download, new provider, external service, user laptop, new accounts,
full speech mux, Google/YouTube OAuth, upload or publish.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from math import ceil
import shutil
import subprocess
import wave

from .agent_org import WorkflowError
from .oct20_owned_voice_handoff import create_oct20_voice_session_packet

FRAME_RATE=24
BREATH_PADDING_MS=250
MAX_RAW_WAV_BYTES=1_500_000
MAX_SCENE_SECONDS=120
VOICE_CONFIG={
    "fm_20261020_short_en":("en-us",150,"en",42),
    "fm_20261020_short_hi":("hi",135,"hi",44),
}


def _hold():
    raise WorkflowError("Mechanical scene pacing benchmark HOLD; never production narration")


@dataclass(frozen=True)
class SceneBenchmark:
    index:int
    script_sha256:str
    planned_frames:int
    measured_pcm_frames:int
    pcm_sample_rate:int
    measured_ms:int
    voice_sample_sha256:str


def propose_scene_frame_retime(
    *, planned_frames:tuple[int,...],
    actual_observed_ms:tuple[int,...],
    frame_rate:int=FRAME_RATE,
    breath_padding_ms:int=BREATH_PADDING_MS,
)->tuple[int,...]:
    """Deterministically borrow spare video frames without changing runtime.

    Does NOT require audio input: the proposed observations are caller claims
    and are never verified natural voices, rights or speech timing.
    """
    if (type(planned_frames) is not tuple
            or type(actual_observed_ms) is not tuple
            or len(planned_frames)!=7 or len(actual_observed_ms)!=7
            or type(frame_rate) is not int or frame_rate!=24
            or type(breath_padding_ms) is not int
            or breath_padding_ms!=250
            or any(type(x) is not int or x<=0 or x>24*120 for x in planned_frames)
            or any(type(x) is not int or not 250<=x<=120_000
                   for x in actual_observed_ms)):
        _hold()
    minimum=[
        ceil((ms+breath_padding_ms)*frame_rate/1000)
        for ms in actual_observed_ms
    ]
    total=sum(planned_frames)
    if total not in (42*frame_rate,44*frame_rate) or sum(minimum)>total:
        _hold()
    result=[max(frame,minim) for frame,minim in zip(planned_frames,minimum)]
    borrowed=sum(result)-total
    while borrowed>0:
        # Equalize residual headroom among donors; avoid stealing below
        # measured mechanical audio + 250ms cue pause allowance.
        donor=max(range(7),key=lambda i:(result[i]-minimum[i],i))
        if result[donor]<=minimum[donor]:
            _hold()
        result[donor]-=1
        borrowed-=1
    if (sum(result)!=total or
            any(size<lower for size,lower in zip(result,minimum))):
        _hold()
    return tuple(result)


def _decode_actual_espeak_stdout(raw:bytes)->tuple[int,int]:
    """Do not trust unseekable RIFF size sentinels. Count actual decoded PCM."""
    if (type(raw) is not bytes or not 60<=len(raw)<=MAX_RAW_WAV_BYTES
            or not raw.startswith(b"RIFF")
            or raw[8:12]!=b"WAVE"):
        _hold()
    try:
        with wave.open(BytesIO(raw),"rb") as reader:
            if (reader.getnchannels()!=1 or reader.getsampwidth()!=2
                    or reader.getcomptype()!="NONE"
                    or reader.getframerate() not in (22050,24000)):
                _hold()
            # Bound the actually consumed PCM rather than getnframes(),
            # which has a placeholder value in streaming WAV output.
            pcm=reader.readframes(MAX_RAW_WAV_BYTES//2)
            if (not pcm or len(pcm)%2
                    or len(pcm)>MAX_RAW_WAV_BYTES-44):
                _hold()
            frames=len(pcm)//2
            if not 250<=round(frames*1000/reader.getframerate())<=120_000:
                _hold()
            return frames,reader.getframerate()
    except (OSError,EOFError,ValueError,wave.Error):
        _hold()


def measure_oct20_mechanical_scene_pacing(*,episode_id:str)->dict:
    """Generate 7 real offline eSpeak snippets only if already installed."""
    if type(episode_id) is not str or episode_id not in VOICE_CONFIG:
        _hold()
    tool=shutil.which("espeak")
    if not tool:
        _hold()
    voice,speed,language,total_seconds=VOICE_CONFIG[episode_id]
    packet=create_oct20_voice_session_packet()
    matches=[lane for lane in packet["lanes"] if lane["episode_id"]==episode_id]
    if (len(matches)!=1 or matches[0]["language"]!=language
            or matches[0]["target_seconds"]!=total_seconds
            or matches[0]["cue_count"]!=7):
        _hold()
    observations=[]
    preceding=0
    for i,cue in enumerate(matches[0]["cues"],1):
        if (cue["scene"]!=i or cue["editorial_start_second"]!=preceding
                or cue["editorial_end_second"]<=preceding
                or cue["recording_text_sha256"]!=
                    sha256(cue["recording_text"].encode("utf-8")).hexdigest()):
            _hold()
        preceding=cue["editorial_end_second"]
        try:
            result=subprocess.run(
                [tool,"--stdin","-v",voice,"-s",str(speed),"-a","140",
                 "--stdout"],
                input=cue["recording_text"].encode("utf-8"),
                capture_output=True,check=False,timeout=15,
            )
        except (OSError,subprocess.TimeoutExpired):
            _hold()
        if result.returncode!=0:
            _hold()
        sample_frames,rate=_decode_actual_espeak_stdout(result.stdout)
        observed_ms=round(sample_frames*1000/rate)
        observations.append(SceneBenchmark(
            index=i,script_sha256=cue["recording_text_sha256"],
            planned_frames=cue["target_scene_seconds"]*FRAME_RATE,
            measured_pcm_frames=sample_frames,
            pcm_sample_rate=rate,measured_ms=observed_ms,
            voice_sample_sha256=sha256(result.stdout).hexdigest(),
        ))
    if preceding!=total_seconds or len(observations)!=7:
        _hold()
    plans=tuple(x.planned_frames for x in observations)
    durations=tuple(x.measured_ms for x in observations)
    retimed=propose_scene_frame_retime(
        planned_frames=plans,actual_observed_ms=durations,
    )
    starts=[0]
    for count in retimed:
        starts.append(starts[-1]+count)
    if starts[-1]!=total_seconds*FRAME_RATE:
        _hold()
    return {
        "status":"ACTUAL_SEVEN_SCENE_ESPEAK_MECHANICAL_BASELINE_REJECTED",
        "episode_id":episode_id,
        "measured_from_actual_pcm_bytes_not_header_sentinel":True,
        "audition_voice":voice,
        "audition_speed_wpm_setting":speed,
        "planned_video_frames":sum(plans),
        "planned_total_ms":total_seconds*1000,
        "mechanical_total_ms":sum(durations),
        "measured_opening_scene_ms":durations[0],
        "opening_scene_overrun_ms":durations[0]-
            observations[0].planned_frames*1000//FRAME_RATE,
        "mechanical_scene_overrun_count":sum(
            ms>frame*1000//FRAME_RATE
            for frame,ms in zip(plans,durations)),
        "actual_audio_wave_sha256s":tuple(
            x.voice_sample_sha256 for x in observations),
        "script_scene_sha256s":tuple(x.script_sha256 for x in observations),
        "original_scene_frames":plans,
        "mechanical_scene_ms":durations,
        "proposed_silent_visual_scene_frames":retimed,
        "proposed_silent_visual_scene_boundaries_frames":tuple(starts),
        "is_nonbinding_visual_editor_retime_proposal":True,
        "proposed_actual_narration_timing_verified":False,
        "natural_sounding_voice_verified":False,
        "hindi_native_pronunciation_verified":False,
        "commercial_voice_rights_verified":False,
        "separate_speakers_authenticated":False,
        "ready_for_mux":False,
        "audio_files_persisted":0,
        "youtube_upload_authorized":False,
        "youtube_publishing_authorized":False,
        "external_network_calls":0,
        "new_models_downloaded":0,
        "monthly_recurring_infrastructure_inr":0,
    }
