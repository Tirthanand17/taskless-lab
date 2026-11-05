"""Whole-AAC per-subtitle-cue TECHNICAL sound activity, not ASR.

The older five-window AAC screen can miss a silent middle cue. Here FFmpeg
decodes the ENTIRE existing final MP4 soundtrack at 8 kHz mono PCM16 and
every authored cue is checked against actual PCM energy. Sound/noise/music
can all pass; words, accent, speaker, licensing, ASR and publishing remain
UNVERIFIED and can never be promoted by this module.

This read-only offline check receives no network/provider/upload credentials.
"""
from __future__ import annotations

from array import array
from dataclasses import dataclass
from hashlib import sha256
from math import sqrt
from pathlib import Path
import subprocess
import sys

from .agent_org import WorkflowError
from .cloud_capacity_admission import LANES,FPS
from .cloud_full_media_evidence import (
    TechnicalFullHDObservation,_sha_file,MAX_SHORT_BYTES,MAX_LONG_BYTES,
)
from .cloud_muxed_audio_screen import MuxedAudioScreen,POSITIONS
from .cloud_transcript_alignment_intake import (
    CandidateWordTranscript,_draft_cues,validate_candidate_word_alignment,
    LANE_EPISODE,
)

RATE=8000
WINDOW_MS=200
WINDOW_SAMPLES=RATE*WINDOW_MS//1000
ENERGY_FLOOR=.003
MIN_ACTIVE_PER_CUE=.25
MAX_DURATION_SLACK_MS=400
SPEC={x.lane:x for x in LANES}


@dataclass(frozen=True)
class CueAcousticCoverage:
    lane:str
    media_sha256:str
    candidate_transcript_sha256:str
    authored_srt_sha256:str
    cue_count:int
    activity_windows_scanned:int
    cue_count_with_acoustic_activity:int
    acoustically_sparse_cues:int
    lowest_cue_active_percent:int
    entire_audio_decoded:bool
    technical_cue_activity_pass:bool
    blockers:tuple[str,...]
    real_spoken_words_verified:bool=False
    actual_subtitle_alignment_verified:bool=False
    narrator_identity_verified:bool=False
    language_verified:bool=False
    commercial_rights_verified:bool=False
    publishing_authorized:bool=False


def _active_flags(raw:bytes)->tuple[bool,...]:
    if (type(raw) is not bytes or not raw or len(raw)%2
            or len(raw)>RATE*2*(max(x.duration_s for x in LANES)+1)):
        raise WorkflowError("Unbounded or malformed full AAC PCM")
    samples=array("h")
    samples.frombytes(raw)
    if sys.byteorder!="little":
        samples.byteswap()
    flags=[]
    # Exact conservative 200ms mono chunks. A short tail is ignored only
    # when it is <1 complete energy frame, never used to claim coverage.
    for offset in range(0,len(samples)-WINDOW_SAMPLES+1,WINDOW_SAMPLES):
        group=samples[offset:offset+WINDOW_SAMPLES]
        rms=sqrt(sum(int(n)*int(n) for n in group)/WINDOW_SAMPLES)/32768
        flags.append(rms>=ENERGY_FLOOR)
    if not flags:
        raise WorkflowError("PCM too short for cue activity audit")
    return tuple(flags)


def inspect_cue_audio_activity(
    mp4:Path,candidate:CandidateWordTranscript,
    observation:TechnicalFullHDObservation,
    audio_screen:MuxedAudioScreen,
)->CueAcousticCoverage:
    """Full-time PCM and every authored estimated cue; no speech approval."""
    validate_candidate_word_alignment(candidate,observation,audio_screen)
    spec=SPEC[candidate.lane]
    if (observation.frames_decoded_or_counted!=spec.duration_s*FPS
            or observation.video_codec!="h264" or observation.audio_codec!="aac"
            or observation.whole_media_ffmpeg_decode_passed is not True
            or observation.original_file_unchanged_after_inspection is not True
            or audio_screen.technical_signal_pass is not True
            or audio_screen.samples_checked!=len(POSITIONS)
            or audio_screen.blockers
            or candidate.episode_id!=LANE_EPISODE[candidate.lane][0]):
        raise WorkflowError("Full-media AAC evidence missing or inconsistent")
    file=Path(mp4)
    if not file.is_absolute() or file.is_symlink():
        raise WorkflowError("Existing absolute ordinary source MP4 required")
    limit=(MAX_SHORT_BYTES if candidate.lane.startswith("short_")
           else MAX_LONG_BYTES)
    before,n,dev,inode=_sha_file(file,limit=limit)
    if (before,n)!=(observation.video_sha256,observation.video_bytes):
        raise WorkflowError("Original media not identical to AAC cue source")
    command=[
        "ffmpeg","-nostdin","-v","error","-xerror",
        "-i",str(file),"-map","0:a:0","-vn","-sn","-dn",
        "-ac","1","-ar",str(RATE),"-t",str(spec.duration_s),
        "-f","s16le","pipe:1",
    ]
    try:
        got=subprocess.run(command,stdin=subprocess.DEVNULL,
                           capture_output=True,check=False,
                           timeout=100 if spec.duration_s<=60 else 900)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise WorkflowError("Whole-AAC cue coverage decode unavailable") from exc
    expected=spec.duration_s*RATE*2
    slack=MAX_DURATION_SLACK_MS*RATE*2//1000
    if (got.returncode!=0 or got.stderr
            or type(got.stdout) is not bytes
            or not expected-slack<=len(got.stdout)<=expected
            or len(got.stdout)%2):
        raise WorkflowError("Whole-AAC PCM incomplete or decoder failed")
    flags=_active_flags(got.stdout)
    again,m,newdev,newinode=_sha_file(file,limit=limit)
    if (again,m,newdev,newinode)!=(before,n,dev,inode):
        raise WorkflowError("MP4 modified or replaced during full audio scan")
    cues=_draft_cues(candidate.episode_id)
    active_cues=0
    sparse=0
    lowest=100
    for start_ms,end_ms,_ in cues:
        # Count all 200ms windows whose centers lie in this cue. Cues
        # shorter than one window use their closest window if available.
        first=max(0,(start_ms-WINDOW_MS//2+WINDOW_MS-1)//WINDOW_MS)
        last=min(len(flags),(end_ms-WINDOW_MS//2+WINDOW_MS-1)//WINDOW_MS)
        if last<=first:
            first=min(len(flags)-1,max(0,(start_ms+end_ms)//(2*WINDOW_MS)))
            last=first+1
        observed=flags[first:last]
        good=sum(observed)
        fraction=good/len(observed)
        pct=int(fraction*100)
        lowest=min(lowest,pct)
        if good>0:
            active_cues+=1
        if fraction<MIN_ACTIVE_PER_CUE:
            sparse+=1
    blockers=() if sparse==0 else ("SILENT_OR_NEAR_SILENT_SUBTITLE_CUES",)
    from .cloud_signed_transcript_reviews import transcript_digest
    return CueAcousticCoverage(
        lane=candidate.lane,media_sha256=before,
        candidate_transcript_sha256=transcript_digest(candidate),
        authored_srt_sha256=candidate.authored_draft_srt_sha256,
        cue_count=len(cues),activity_windows_scanned=len(flags),
        cue_count_with_acoustic_activity=active_cues,
        acoustically_sparse_cues=sparse,lowest_cue_active_percent=lowest,
        entire_audio_decoded=True,
        technical_cue_activity_pass=not blockers,blockers=blockers,
    )


def summarize_cue_activity(
    reports:tuple[CueAcousticCoverage,...],
)->dict:
    """Only inventory technical acoustic coverage; NEVER approve release."""
    if not isinstance(reports,tuple) or len(reports)>len(SPEC):
        raise WorkflowError("Bounded cue-acoustic report tuple required")
    seen=set()
    issues=[]
    for r in reports:
        if (not isinstance(r,CueAcousticCoverage)
                or r.lane not in SPEC or r.lane in seen
                or not isinstance(r.media_sha256,str)
                or len(r.media_sha256)!=64
                or not isinstance(r.candidate_transcript_sha256,str)
                or len(r.candidate_transcript_sha256)!=64
                or any(getattr(r,k) is not False for k in (
                    "real_spoken_words_verified","actual_subtitle_alignment_verified",
                    "narrator_identity_verified","language_verified",
                    "commercial_rights_verified","publishing_authorized",
                ))):
            raise WorkflowError("Forged or duplicate cue-acoustic result")
        seen.add(r.lane)
        if not r.technical_cue_activity_pass or r.blockers:
            issues.append(r.lane+":CUE_AUDIO_ACTIVITY_FAILED")
    for lane in SPEC:
        if lane not in seen:
            issues.append(lane+":CUE_AUDIO_NOT_INSPECTED")
    return {
        "status":"FULL_AAC_CUE_ACTIVITY_TECHNICAL_ONLY",
        "audited_lanes":tuple(sorted(seen)),
        "blocking_reasons":tuple(sorted(issues))+
            ("REAL_SPEECH_ALIGNMENT_NARRATOR_RIGHTS_NOT_VERIFIED",),
        "actual_spoken_words_verified":False,
        "actual_subtitle_sync_verified":False,
        "two_distinct_short_narrators_verified":False,
        "commercial_rights_verified":False,
        "upload_authorized":False,
        "publishing_authorized":False,
        "recurring_infrastructure_cost_inr":0,
    }
