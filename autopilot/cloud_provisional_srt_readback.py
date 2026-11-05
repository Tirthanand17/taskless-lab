"""Read-only offline revalidation of a previously exported provisional SRT.

Do not use initial export metadata as proof a subtitle remains intact/current.
Re-open the private directory/file without final-symlink following, hash the
exact on-disk UTF-8 file, re-audit the journal and reject superseded reviews.
This does NOT approve source-language speech or allow any YouTube action.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import os
import stat

from .agent_org import WorkflowError
from .cloud_provisional_signed_srt import (
    _open_owned_directory,stage_provisional_srt,EXPORT_SUFFIX,MAX_RENDER_BYTES,
)
from .cloud_transcript_replay_ledger import OfflineTranscriptReviewLedger
from .cloud_transcript_alignment_intake import CandidateWordTranscript
from .cloud_full_media_evidence import TechnicalFullHDObservation
from .cloud_muxed_audio_screen import MuxedAudioScreen
from .cloud_cue_audio_activity import CueAcousticCoverage


def verify_current_provisional_srt(
    *, ledger:OfflineTranscriptReviewLedger,
    candidate:CandidateWordTranscript,
    media:TechnicalFullHDObservation,
    audio_screen:MuxedAudioScreen,
    cue_report:CueAcousticCoverage,
    expected_event_sha256:str,
    source_directory:Path,
)->dict:
    """Check event-pinned exported bytes, not merely the earlier export receipt."""
    if not isinstance(source_directory,Path):
        raise WorkflowError("Explicit local editor-output folder required")
    # Freshly recompute the exact expected artifact and all inputs, without
    # writing. This alone is NOT enough: journal head may change afterwards.
    expected=stage_provisional_srt(
        ledger=ledger,candidate=candidate,media=media,
        audio_screen=audio_screen,cue_report=cue_report,
        expected_event_sha256=expected_event_sha256,
    )
    if expected["exclusive_file_created"]:
        raise WorkflowError("Unexpected provisional subtitle write")
    filename=(candidate.episode_id+"."+expected_event_sha256[:16]+
              EXPORT_SUFFIX)
    root_fd=_open_owned_directory(source_directory)
    try:
        root_before=os.fstat(root_fd)
        try:
            file_fd=os.open(
                filename,os.O_RDONLY|getattr(os,"O_CLOEXEC",0)|
                    getattr(os,"O_NOFOLLOW",0),dir_fd=root_fd,
            )
        except OSError as exc:
            raise WorkflowError("Provisional subtitle missing or unsafe") from exc
        try:
            before=os.fstat(file_fd)
            if (not stat.S_ISREG(before.st_mode)
                    or before.st_uid!=os.geteuid()
                    or stat.S_IMODE(before.st_mode)!=0o600
                    or not 100<=before.st_size<=MAX_RENDER_BYTES):
                raise WorkflowError("Provisional subtitle file has unsafe attributes")
            with os.fdopen(file_fd,"rb",closefd=False) as reader:
                raw=reader.read(MAX_RENDER_BYTES+1)
            after=os.fstat(file_fd)
            if (len(raw)!=before.st_size
                    or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=
                        (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
                    or sha256(raw).hexdigest()!=expected["provisional_srt_sha256"]):
                raise WorkflowError("Provisional subtitle bytes changed or are stale")
        finally:
            os.close(file_fd)
        # A second same-lock check must be made after the read, since an
        # independent signed review may supersede an event at any moment.
        with ledger._transaction() as db:
            _,_,heads=ledger._audit(db)
            if heads.get(candidate.episode_id)!=expected_event_sha256:
                raise WorkflowError("Review head superseded this subtitle")
            on_disk=os.stat(filename,dir_fd=root_fd,follow_symlinks=False)
            directory_now=source_directory.lstat()
            if (not stat.S_ISREG(on_disk.st_mode)
                    or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=
                        (on_disk.st_dev,on_disk.st_ino,on_disk.st_size,
                         on_disk.st_mtime_ns)
                    or (root_before.st_dev,root_before.st_ino)!=
                        (directory_now.st_dev,directory_now.st_ino)):
                raise WorkflowError("Provisional subtitle or directory replaced")
        return {
            "status":"CURRENT_PROVISIONAL_SRT_BYTES_MATCH_EDITOR_ONLY",
            "journal_event_sha256":expected_event_sha256,
            "provisional_srt_sha256":expected["provisional_srt_sha256"],
            "cue_count":expected["cue_count"],
            "current_review_head_rechecked":True,
            "file_reopened_hash_compared":True,
            "genuine_voice_speech_verified":False,
            "actual_spoken_word_timing_verified":False,
            "rights_or_consent_verified":False,
            "approved_for_mux_or_publish":False,
            "youtube_upload_authorized":False,
            "publishing_authorized":False,
            "recurring_infrastructure_inr":0,
        }
    finally:
        os.close(root_fd)
