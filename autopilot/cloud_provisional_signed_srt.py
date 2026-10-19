"""Version-pinned OFFLINE subtitle handoff from a strict signed review journal.

Produces an editor-only SRT for the CURRENT journal head, NEVER a caption
approval. Requires two journaled reviewer evidence files, a durable signed
command nonce, an exact candidate/video hash and a complete cue sound-activity
inspection. The new cue times are still caller-asserted transcript positions;
cryptographic signatures and waveform energy DO NOT prove spoken words.

Only the optional export writes an exclusive 0600 file in an existing local
directory, NEVER a media upload, Google/Cloudflare call or publication.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import os
import re
import stat

from .agent_org import WorkflowError
from .cloud_transcript_replay_ledger import OfflineTranscriptReviewLedger
from .cloud_transcript_alignment_intake import (
    CandidateWordTranscript,_draft_cues,validate_candidate_word_alignment,
    LANE_EPISODE,
)
from .cloud_full_media_evidence import TechnicalFullHDObservation
from .cloud_muxed_audio_screen import MuxedAudioScreen
from .cloud_cue_audio_activity import CueAcousticCoverage
from .cloud_signed_transcript_reviews import transcript_digest
from .phase3_voice_subtitle_handoff import (
    build_subtitles_from_authored_csv,MAX_CUE_CHARS,MAX_CUE_DURATION_MS,
)

HEX64=re.compile(r"[0-9a-f]{64}\Z")
MAX_RENDER_BYTES=250_000
EXPORT_SUFFIX=".reviewed_claim_unverified_speech.srt"


def _open_owned_directory(folder:Path)->int:
    """Pin the destination inode; don't follow a substituted final symlink.

    This does not make a same-UID local filesystem adversary trustworthy.
    """
    if (not isinstance(folder,Path) or not folder.is_absolute()
            or folder.is_symlink()):
        raise WorkflowError("Private subtitle output must be absolute directory")
    flags=os.O_RDONLY|getattr(os,"O_DIRECTORY",0)
    flags|=getattr(os,"O_CLOEXEC",0)|getattr(os,"O_NOFOLLOW",0)
    try:
        fd=os.open(folder,flags)
        info=os.fstat(fd)
        if (not stat.S_ISDIR(info.st_mode)
                or info.st_uid!=os.geteuid()
                or (stat.S_IMODE(info.st_mode)&0o022)):
            raise WorkflowError("Subtitle output directory not owner protected")
        return fd
    except BaseException:
        if "fd" in locals():
            os.close(fd)
        raise


def _write_exclusive_owned(folder:Path,name:str,raw:bytes)->None:
    """Export relative to pinned directory FD and verify its identity."""
    fd=_open_owned_directory(folder)
    opened=None
    try:
        info=os.fstat(fd)
        flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
        flags|=getattr(os,"O_CLOEXEC",0)|getattr(os,"O_NOFOLLOW",0)
        try:
            opened=os.open(name,flags,0o600,dir_fd=fd)
        except OSError as exc:
            raise WorkflowError("Safe exclusive provisional SRT export denied") from exc
        file_info=os.fstat(opened)
        try:
            with os.fdopen(opened,"wb") as writer:
                opened=None
                writer.write(raw)
                writer.flush()
                os.fsync(writer.fileno())
                file_info=os.fstat(writer.fileno())
            directory_now=folder.lstat()
            target_now=os.stat(name,dir_fd=fd,follow_symlinks=False)
            if ((info.st_dev,info.st_ino)!=(directory_now.st_dev,directory_now.st_ino)
                    or not stat.S_ISREG(target_now.st_mode)
                    or (target_now.st_dev,target_now.st_ino,target_now.st_size)!=
                        (file_info.st_dev,file_info.st_ino,len(raw))):
                raise WorkflowError("Provisional SRT output was swapped")
        except BaseException:
            try:
                target_now=os.stat(name,dir_fd=fd,follow_symlinks=False)
                if (target_now.st_dev,target_now.st_ino)==(file_info.st_dev,file_info.st_ino):
                    os.unlink(name,dir_fd=fd)
            except OSError:
                pass
            raise
    finally:
        if opened is not None:
            os.close(opened)
        os.close(fd)


def _timecode(milliseconds:int)->str:
    if type(milliseconds) is not int or not 0<=milliseconds<=3_600_000:
        raise WorkflowError("Provisional SRT timecode out of bounds")
    hours,remaining=divmod(milliseconds,3_600_000)
    minutes,remaining=divmod(remaining,60_000)
    seconds,ms=divmod(remaining,1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"


def _candidate_cues(candidate:CandidateWordTranscript)->tuple[tuple[int,int,str],...]:
    """Claimed word positions collapsed to their authored cue groups."""
    original=_draft_cues(candidate.episode_id)
    words=candidate.words
    index=0
    result=[]
    last=0
    for _,_,text_words in original:
        segment=words[index:index+len(text_words)]
        index+=len(text_words)
        if not segment or len(segment)!=len(text_words):
            raise WorkflowError("Provisional SRT cue lost transcript words")
        start,end=segment[0].start_ms,segment[-1].end_ms
        line=" ".join(text_words)
        if (type(start) is not int or type(end) is not int
                or start<last or end<=start
                or end-start>MAX_CUE_DURATION_MS+1800
                or len(line)>MAX_CUE_CHARS
                or "\n" in line or "\r" in line
                or "<" in line or ">" in line):
            raise WorkflowError("Provisional SRT cue is not display/timing safe")
        last=end
        result.append((start,end,line))
    if index!=len(words):
        raise WorkflowError("Provisional SRT has unassigned transcript words")
    return tuple(result)


def _check_cue_report(candidate:CandidateWordTranscript,
                      report:CueAcousticCoverage)->None:
    if (not isinstance(report,CueAcousticCoverage)
            or report.lane!=candidate.lane
            or report.media_sha256!=candidate.media_sha256
            or report.candidate_transcript_sha256!=transcript_digest(candidate)
            or report.authored_srt_sha256!=candidate.authored_draft_srt_sha256
            or report.cue_count!=len(_draft_cues(candidate.episode_id))
            or report.entire_audio_decoded is not True
            or report.technical_cue_activity_pass is not True
            or report.blockers
            or type(report.acoustically_sparse_cues) is not int
            or report.acoustically_sparse_cues!=0
            or type(report.cue_count_with_acoustic_activity) is not int
            or report.cue_count_with_acoustic_activity!=report.cue_count
            or type(report.lowest_cue_active_percent) is not int
            or not 25<=report.lowest_cue_active_percent<=100
            or any(getattr(report,key) is not False for key in (
                "real_spoken_words_verified","actual_subtitle_alignment_verified",
                "narrator_identity_verified","language_verified",
                "commercial_rights_verified","publishing_authorized",
            ))):
        raise WorkflowError("Required cue-acoustic technical claim missing")


def stage_provisional_srt(
    *,ledger:OfflineTranscriptReviewLedger,
    candidate:CandidateWordTranscript,
    media:TechnicalFullHDObservation,
    audio_screen:MuxedAudioScreen,
    cue_report:CueAcousticCoverage,
    expected_event_sha256:str,
    destination_directory:Path|None=None,
)->dict:
    """Build one event-bound *unverified* SRT, with optional exclusive export.

    SQLite BEGIN IMMEDIATE and a complete chain audit guard the head and
    optional artifact write. A superseded/weak detached-only transcript can
    never be staged as the current strict reviewing evidence.
    """
    if (not isinstance(ledger,OfflineTranscriptReviewLedger)
            or not isinstance(expected_event_sha256,str)
            or HEX64.fullmatch(expected_event_sha256) is None
            or not isinstance(candidate,CandidateWordTranscript)):
        raise WorkflowError("Known original journal event and transcript required")
    validate_candidate_word_alignment(candidate,media,audio_screen)
    _check_cue_report(candidate,cue_report)
    cues=_candidate_cues(candidate)
    if candidate.lane not in LANE_EPISODE:
        raise WorkflowError("Unsupported provisional transcript lane")
    ep,language=LANE_EPISODE[candidate.lane]
    if candidate.episode_id!=ep or candidate.declared_language!=language:
        raise WorkflowError("Provisional language lane mismatch")
    draft=build_subtitles_from_authored_csv()[ep]
    if draft["srt_sha256"]!=candidate.authored_draft_srt_sha256:
        raise WorkflowError("Canonical author subtitle plan changed")
    parts=[]
    for number,(start,end,line) in enumerate(cues,1):
        parts.append(f"{number}\n{_timecode(start)} --> {_timecode(end)}\n{line}\n")
    srt="\n".join(parts)+"\n"
    raw=srt.encode("utf-8")
    if not 100<=len(raw)<=MAX_RENDER_BYTES:
        raise WorkflowError("Unbounded or empty provisional subtitle")
    digest=sha256(raw).hexdigest()
    name=ep+"."+expected_event_sha256[:16]+EXPORT_SUFFIX
    folder=None
    target=None
    if destination_directory is not None:
        if not isinstance(destination_directory,Path):
            raise WorkflowError("Existing explicit destination directory required")
        folder=destination_directory
        if (not folder.is_absolute() or folder.is_symlink()
                or not folder.is_dir()):
            raise WorkflowError("Refusing nonabsolute, symlink or missing output folder")
        target=folder/name
        if target.exists() or target.is_symlink():
            raise WorkflowError("Provisional SRT may not overwrite another file")

    # Same-lock read of current head plus both role-file digests and
    # committed signed-command nonce. This does not authenticate any human.
    with ledger._transaction() as db:
        _,_,heads=ledger._audit(db)
        if heads.get(ep)!=expected_event_sha256:
            raise WorkflowError("Transcript review superseded; stale SRT blocked")
        row=db.execute(
            "SELECT lane,media_sha,transcript_sha,srt_sha "
            "FROM transcript_review_events WHERE event_sha=? AND episode=?",
            (expected_event_sha256,ep),
        ).fetchone()
        if (row!=(candidate.lane,candidate.media_sha256,
                  transcript_digest(candidate),
                  candidate.authored_draft_srt_sha256)
                or db.execute(
                    "SELECT count(*) FROM transcript_review_sidecars "
                    "WHERE event_sha=?",(expected_event_sha256,),
                ).fetchone()[0]!=2
                or db.execute(
                    "SELECT count(*) FROM transcript_review_command_nonces "
                    "WHERE event_sha=?",(expected_event_sha256,),
                ).fetchone()[0]!=1):
            raise WorkflowError("Current signed acoustic review bundle is incomplete")
        if target is not None:
            _write_exclusive_owned(folder,name,raw)

    return {
        "status":"SIGNED_REVIEW_PROVISIONAL_SUBTITLE_FOR_EDITOR_ONLY",
        "episode_id":ep,
        "lane":candidate.lane,
        "journal_event_sha256":expected_event_sha256,
        "source_media_sha256":candidate.media_sha256,
        "reviewed_candidate_sha256":transcript_digest(candidate),
        "authored_draft_srt_sha256":candidate.authored_draft_srt_sha256,
        "provisional_srt_sha256":digest,
        "cue_count":len(cues),
        "exclusive_file_created":target is not None,
        "export_basename":name if target is not None else None,
        "real_audio_words_independently_verified":False,
        "timings_authenticated_to_actual_speech":False,
        "reviewers_real_world_identity_verified":False,
        "commercial_rights_verified":False,
        "approved_for_media_mux":False,
        "youtube_upload_authorized":False,
        "publishing_authorized":False,
        "recurring_infrastructure_inr":0,
    }
