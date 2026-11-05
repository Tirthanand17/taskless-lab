"""Offline duplicate-track screen for the two SHORT narrated video lanes.

An existing pair of original full-length MP4 files is decoded to fixed
mono PCM16 samples. Identical soundtracks and near-identical sample-sign
patterns (including gain-only changes) are quarantined. This detects a
narrow class of accidental reuse; it CANNOT establish different speakers,
genuine speech, correct language, pronunciation, consent or licensing.

All audio fingerprints remain IN MEMORY; returned status has no raw samples,
media SHA, narrator names, private paths or upload ability. Read-only.
"""
from __future__ import annotations

from dataclasses import dataclass,field
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import sys
from array import array

from .agent_org import WorkflowError
from .cloud_capacity_admission import LANES,FPS
from .cloud_full_media_evidence import (
    TechnicalFullHDObservation,_sha_file,MAX_SHORT_BYTES,
)
from .cloud_muxed_audio_screen import MuxedAudioScreen,POSITIONS
from .cloud_transcript_alignment_intake import (
    CandidateWordTranscript,validate_candidate_word_alignment,_draft_cues,
    LANE_EPISODE,
)
from .cloud_cue_audio_activity import (
    CueAcousticCoverage,RATE,MAX_DURATION_SLACK_MS,
)
from .cloud_signed_transcript_reviews import transcript_digest
from .phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv

SHORTS=frozenset(("short_en","short_hi"))
RATE_16K=RATE
STRIDE=32
MAX_FINGERPRINT_SAMPLES=15000
MIN_MATCH_RATIO=0.995
SHA=re.compile(r"[0-9a-f]{64}\Z")
SPECS={x.lane:x for x in LANES}


@dataclass(frozen=True)
class ShortAudioFingerprint:
    """Technical private in-process bytes only; not voice biometric identity."""
    lane:str
    media_sha256:str
    pcm_sha256:str
    narrator_plan_id:str
    count:int
    # These bits summarize signal signs, NOT raw voice. Avoid logs/exports.
    _signs:bytes=field(repr=False)
    whole_audio_decode_passed:bool=True
    real_speech_verified:bool=False
    distinct_narrator_identity_verified:bool=False
    upload_authorized:bool=False
    publishing_authorized:bool=False


def _sign_bits(raw:bytes)->tuple[bytes,int]:
    """Quantized ± sample signs; gain scaling preserves the comparison."""
    if (type(raw) is not bytes or not raw or len(raw)%2
            or len(raw)>2*RATE_16K*43):
        raise WorkflowError("Full-length signed PCM input invalid")
    samples=array("h")
    samples.frombytes(raw)
    if sys.byteorder!="little":
        samples.byteswap()
    pattern=bytearray()
    count=0
    byte=0
    for idx in range(0,len(samples),STRIDE):
        sample=samples[idx]
        if sample==0:
            # Silent sample matches neither positive nor negative by default:
            # all-zero data cannot certify independent voices.
            bit=0
        else:
            bit=1 if sample>0 else 0
        byte=(byte<<1)|bit
        count+=1
        if count%8==0:
            pattern.append(byte)
            byte=0
    if count%8:
        pattern.append(byte<<(8-count%8))
    if not 2500<=count<=MAX_FINGERPRINT_SAMPLES:
        raise WorkflowError("Full short audio fingerprint coverage invalid")
    return bytes(pattern),count


def inspect_short_audio_fingerprint(
    mp4:Path,candidate:CandidateWordTranscript,
    media:TechnicalFullHDObservation,
    screen:MuxedAudioScreen,
    cue_report:CueAcousticCoverage,
)->ShortAudioFingerprint:
    """Decode whole existing short AAC and pin it to all preceding observations."""
    if not isinstance(candidate,CandidateWordTranscript) or candidate.lane not in SHORTS:
        raise WorkflowError("Only full English and Hindi short audio is comparable")
    validate_candidate_word_alignment(candidate,media,screen)
    if (not isinstance(cue_report,CueAcousticCoverage)
            or cue_report.lane!=candidate.lane
            or cue_report.media_sha256!=media.video_sha256
            or cue_report.candidate_transcript_sha256!=transcript_digest(candidate)
            or cue_report.authored_srt_sha256!=candidate.authored_draft_srt_sha256
            or cue_report.cue_count!=len(_draft_cues(candidate.episode_id))
            or cue_report.entire_audio_decoded is not True
            or cue_report.technical_cue_activity_pass is not True
            or cue_report.blockers
            or any(getattr(cue_report,key) is not False for key in (
                "real_spoken_words_verified","actual_subtitle_alignment_verified",
                "narrator_identity_verified","language_verified",
                "commercial_rights_verified","publishing_authorized",
            ))
            or media.frames_decoded_or_counted!=SPECS[candidate.lane].duration_s*FPS
            or media.video_codec!="h264" or media.audio_codec!="aac"
            or screen.samples_checked!=len(POSITIONS)
            or screen.technical_signal_pass is not True
            or screen.blockers):
        raise WorkflowError("Unbound or falsely promoted cue AAC evidence")
    captions=build_subtitles_from_authored_csv()
    episode,lang=LANE_EPISODE[candidate.lane]
    draft=captions[episode]
    if (candidate.episode_id!=episode or candidate.declared_language!=lang
            or draft["language"]!=lang
            or draft["srt_sha256"]!=candidate.authored_draft_srt_sha256
            or draft["actual_voice_alignment_verified"] is not False
            or draft["ready_for_upload"] is not False):
        raise WorkflowError("Source-locked narrator profile or language changed")
    file=Path(mp4)
    if not file.is_absolute() or file.is_symlink():
        raise WorkflowError("Original absolute MP4 path required")
    before,length,dev,inode=_sha_file(file,limit=MAX_SHORT_BYTES)
    if (before,length)!=(media.video_sha256,media.video_bytes):
        raise WorkflowError("Original MP4 changed since full-length intake")
    duration=SPECS[candidate.lane].duration_s
    cmd=[
        "ffmpeg","-nostdin","-v","error","-xerror",
        "-i",str(file),"-map","0:a:0","-vn","-sn","-dn",
        "-ac","1","-ar",str(RATE_16K),"-t",str(duration),
        "-f","s16le","pipe:1",
    ]
    try:
        result=subprocess.run(cmd,stdin=subprocess.DEVNULL,
                              capture_output=True,check=False,timeout=100)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise WorkflowError("Unable to decode bounded original AAC") from exc
    expected=duration*RATE_16K*2
    slack=MAX_DURATION_SLACK_MS*RATE_16K*2//1000
    if (result.returncode!=0 or result.stderr
            or type(result.stdout) is not bytes
            or not expected-slack<=len(result.stdout)<=expected
            or len(result.stdout)%2):
        raise WorkflowError("Short track AAC decode truncated or malformed")
    fingerprint,count=_sign_bits(result.stdout)
    after,size,dev2,inode2=_sha_file(file,limit=MAX_SHORT_BYTES)
    if (before,length,dev,inode)!=(after,size,dev2,inode2):
        raise WorkflowError("MP4 mutated during fingerprint inspection")
    return ShortAudioFingerprint(
        lane=candidate.lane,media_sha256=before,
        pcm_sha256=sha256(result.stdout).hexdigest(),
        narrator_plan_id=draft["narrator_plan_id"],
        count=count,_signs=fingerprint,
    )


def compare_short_audio_fingerprints(
    records:tuple[ShortAudioFingerprint,...],
)->dict:
    """Reject exact/near-identical *tracks*, never claim distinct speakers."""
    if type(records) is not tuple or len(records)!=2:
        raise WorkflowError("One English and one Hindi short required")
    rows={}
    for r in records:
        if (not isinstance(r,ShortAudioFingerprint)
                or r.lane not in SHORTS or r.lane in rows
                or type(r.count) is not int or not 2500<=r.count<=MAX_FINGERPRINT_SAMPLES
                or not isinstance(r.media_sha256,str) or SHA.fullmatch(r.media_sha256) is None
                or not isinstance(r.pcm_sha256,str) or SHA.fullmatch(r.pcm_sha256) is None
                or not isinstance(r._signs,bytes)
                or len(r._signs)!=(r.count+7)//8
                or r.whole_audio_decode_passed is not True
                or any(getattr(r,k) is not False for k in (
                    "real_speech_verified","distinct_narrator_identity_verified",
                    "upload_authorized","publishing_authorized",
                ))):
            raise WorkflowError("Tampered or duplicate short fingerprint evidence")
        rows[r.lane]=r
    if set(rows)!=SHORTS:
        raise WorkflowError("English or Hindi video fingerprint missing")
    a,b=rows["short_en"],rows["short_hi"]
    captions=build_subtitles_from_authored_csv()
    if (a.narrator_plan_id!=captions[LANE_EPISODE["short_en"][0]]["narrator_plan_id"]
            or b.narrator_plan_id!=captions[LANE_EPISODE["short_hi"][0]]["narrator_plan_id"]):
        raise WorkflowError("Untrusted narrator label substituted")
    # Cross-kind video content hash collision is always suspicious.
    identical_media=a.media_sha256==b.media_sha256
    identical_pcm=a.pcm_sha256==b.pcm_sha256
    # Sign similarity is meaningful only when all sample positions correspond,
    # including sample length. Gain scaling preserves signs. Exact polarity
    # inversion is a simple transformation of a reused narration track.
    fraction=None
    if a.count==b.count:
        equal=0
        inverse=0
        total=a.count
        for i,(left,right) in enumerate(zip(a._signs,b._signs)):
            bits=8 if i<(total//8) else total%8
            if bits==0:
                bits=8
            mask=((1<<bits)-1)<<(8-bits)
            different=((left^right)&mask).bit_count()
            equal+=bits-different
            inverse+=different
        fraction=max(equal,inverse)/total
    near_duplicate=bool(fraction is not None and fraction>=MIN_MATCH_RATIO)
    reasons=[]
    if identical_media:
        reasons.append("IDENTICAL_ENGLISH_HINDI_MP4_MEDIA")
    if identical_pcm:
        reasons.append("IDENTICAL_FINAL_SHORT_AUDIO_TRACK")
    if near_duplicate:
        reasons.append("NEAR_IDENTICAL_SHORT_PCM_SIGN_PATTERN")
    reasons=tuple(sorted(reasons))
    return {
        "status":"SHORT_AUDIO_COLLISION_SCREEN_ONLY",
        "short_languages_present":("en","hi"),
        "audio_collision_blockers":reasons,
        "technical_collision_not_detected":not reasons,
        "declared_narrator_plans_differ":a.narrator_plan_id!=b.narrator_plan_id,
        "acoustic_voice_identity_verified":False,
        "two_audibly_distinct_natural_speakers_verified":False,
        "correct_spoken_languages_verified":False,
        "commercial_rights_independently_verified":False,
        "spoken_subtitle_alignment_verified":False,
        "upload_authorized":False,
        "publishing_authorized":False,
        "monthly_recurring_infrastructure_inr":0,
    }
