"""Deterministic transcript-candidate shape checks, no ASR/media/voices."""
from dataclasses import replace
from datetime import datetime,timezone
from hashlib import sha256
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_capacity_admission import FPS,LANES
from autopilot.cloud_full_media_evidence import TechnicalFullHDObservation
from autopilot.cloud_muxed_audio_screen import MuxedAudioScreen
from autopilot.phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv
from autopilot.cloud_transcript_alignment_intake import (
    TimedTranscriptWord,CandidateWordTranscript,_draft_cues,
    validate_candidate_word_alignment,summarize_candidate_transcript_batch,
    LANE_EPISODE,
)

NOW=datetime(2026,10,19,9,tzinfo=timezone.utc)
MP4="b"*64

def packet(lane):
    ep,lang=LANE_EPISODE[lane]
    cues=_draft_cues(ep)
    words=[]
    for start,end,source in cues:
        n=len(source)
        for i,w in enumerate(source):
            a=start+(end-start)*i//n
            b=start+(end-start)*(i+1)//n
            words.append(TimedTranscriptWord(w,a,b))
    candidate=CandidateWordTranscript(
        lane,ep,lang,MP4,
        build_subtitles_from_authored_csv()[ep]["srt_sha256"],
        "synthetic_test",tuple(words),
    )
    spec=next(x for x in LANES if x.lane==lane)
    video=TechnicalFullHDObservation(
        lane,MP4,11000,spec.duration_s*FPS,spec.width,spec.height,
        float(spec.duration_s),"h264","aac",True,20,700,NOW,True,
    )
    sound=MuxedAudioScreen(lane,MP4,5,5,0,0,0,True,())
    return candidate,video,sound

def verify(lane="short_en",*,candidate=None,media=None,sound=None):
    a,b,c=packet(lane)
    return validate_candidate_word_alignment(
        candidate or a,media or b,sound or c
    )


class CandidateWordAlignmentTests(unittest.TestCase):
    def test_synthetic_all_three_lanes_pass_shape_never_speech_verification(self):
        records=[]
        for lane in LANE_EPISODE:
            with self.subTest(lane=lane):
                result=verify(lane)
                self.assertGreater(result["checked_word_count"],20)
                self.assertGreater(result["checked_cue_count"],1)
                self.assertEqual(result["greatest_cue_boundary_overshoot_ms"],0)
                for item in (
                    "actual_audio_words_verified",
                    "spoken_language_verified",
                    "spoken_word_subtitle_sync_verified",
                    "ASR_or_human_transcriber_identity_authenticated",
                    "upload_authorized","publishing_authorized",
                ):
                    self.assertFalse(result[item])
                records.append(result)
        summary=summarize_candidate_transcript_batch(tuple(records))
        self.assertTrue(summary["all_three_candidate_shapes_present"])
        self.assertFalse(summary["actual_spoken_language_and_alignment_verified"])
        self.assertFalse(summary["youtube_publishing_authorized"])

    def test_one_missing_word_and_one_extra_word_both_denied(self):
        a,b,c=packet("short_en")
        for seq in (a.words[:-1],a.words+(a.words[-1],)):
            with self.assertRaises(WorkflowError):
                validate_candidate_word_alignment(
                    replace(a,words=seq),b,c
                )

    def test_substituted_word_or_reordering_cannot_pass(self):
        a,b,c=packet("short_hi")
        changed=list(a.words)
        changed[3]=replace(changed[3],text="अनधिकृत")
        with self.assertRaises(WorkflowError):
            validate_candidate_word_alignment(replace(a,words=tuple(changed)),b,c)
        switched=list(a.words)
        switched[0],switched[1]=switched[1],switched[0]
        with self.assertRaises(WorkflowError):
            validate_candidate_word_alignment(replace(a,words=tuple(switched)),b,c)

    def test_shifted_cue_word_or_overlapping_and_boolean_timestamps_denied(self):
        a,b,c=packet("short_en")
        for updated in (
            replace(a.words[0],start_ms=8000,end_ms=8200),
            replace(a.words[1],start_ms=0),
            replace(a.words[0],start_ms=True),
            replace(a.words[0],end_ms=a.words[0].start_ms),
        ):
            updated_words=(updated,)+a.words[1:] if updated==a.words[0] or updated.text==a.words[0].text else (
                a.words[0],updated,*a.words[2:]
            )
            with self.subTest(change=updated),self.assertRaises(WorkflowError):
                validate_candidate_word_alignment(
                    replace(a,words=tuple(updated_words)),b,c
                )

    def test_changed_srt_hash_mp4_hash_or_wrong_language_lane_denied(self):
        a,b,c=packet("long_hi")
        for modified in (
            replace(a,authored_draft_srt_sha256="a"*64),
            replace(a,media_sha256="c"*64),
            replace(a,declared_language="en"),
            replace(a,episode_id="csv_tutorial_short_hi"),
            replace(a,claimed_method="not_a_provider"),
        ):
            with self.subTest(edit=modified.claimed_method),self.assertRaises(WorkflowError):
                validate_candidate_word_alignment(modified,b,c)

    def test_audio_screen_failure_or_reused_other_media_blocks_transcript(self):
        a,b,c=packet("short_en")
        for bad in (
            replace(c,video_sha256="c"*64),
            replace(c,technical_signal_pass=False),
            replace(c,samples_checked=0),
            replace(c,spoken_caption_alignment_verified=True),
        ):
            with self.subTest(status=bad.technical_signal_pass),self.assertRaises(WorkflowError):
                validate_candidate_word_alignment(a,b,bad)
        with self.assertRaises(WorkflowError):
            validate_candidate_word_alignment(a,replace(b,publishing_authorized=True),c)

    def test_long_hindi_combining_marks_remain_distinct_from_forged_glyph(self):
        a,b,c=packet("long_hi")
        selected=next(
            (i for i,w in enumerate(a.words) if any(
                ord(ch)>=0x900 and ord(ch)<=0x97f for ch in w.text
            )),None
        )
        self.assertIsNotNone(selected)
        words=list(a.words)
        words[selected]=replace(words[selected],text="हिन्दीबदला")
        with self.assertRaises(WorkflowError):
            validate_candidate_word_alignment(replace(a,words=tuple(words)),b,c)

    def test_partial_batch_rejected_as_complete_and_forged_approval_refused(self):
        result=verify()
        summary=summarize_candidate_transcript_batch((result,))
        self.assertFalse(summary["all_three_candidate_shapes_present"])
        self.assertEqual(len(summary["missing_lanes"]),2)
        with self.assertRaises(WorkflowError):
            summarize_candidate_transcript_batch((result,result))
        altered=dict(result,publishing_authorized=True)
        with self.assertRaises(WorkflowError):
            summarize_candidate_transcript_batch((altered,))

    def test_script_subtitle_hash_changes_invalidate_previous_candidate(self):
        a,b,c=packet("short_en")
        stale=replace(a,authored_draft_srt_sha256=sha256(b"older script").hexdigest())
        with self.assertRaises(WorkflowError):
            validate_candidate_word_alignment(stale,b,c)

    def test_unknown_or_non_tuple_unbounded_words_are_refused(self):
        a,b,c=packet("short_en")
        for words in (
            list(a.words),
            (),
            tuple(a.words)*(4501//len(a.words)+1),
        ):
            with self.subTest(type=type(words)),self.assertRaises(WorkflowError):
                validate_candidate_word_alignment(replace(a,words=words),b,c)


if __name__=="__main__":
    unittest.main()
