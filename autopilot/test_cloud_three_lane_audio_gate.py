"""Offline fabricated three-lane aggregate audio QA; NEVER real speaker proof."""
from dataclasses import replace
from hashlib import sha256
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_cue_audio_activity import CueAcousticCoverage
from autopilot.cloud_short_voice_collision_screen import (
    _sign_bits,ShortAudioFingerprint,
)
from autopilot.cloud_three_lane_audio_gate import evaluate_three_lane_audio_handoff
from autopilot.cloud_transcript_alignment_intake import _draft_cues,LANE_EPISODE
from autopilot.phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv
from autopilot.test_cloud_short_voice_collision_screen import fake_pcm

MEDIA={
    "short_en":"a"*64,
    "short_hi":"c"*64,
    "long_hi":"d"*64,
}


def synthetic_cues():
    result=[]
    for lane,digest in MEDIA.items():
        episode,_=LANE_EPISODE[lane]
        n=len(_draft_cues(episode))
        result.append(CueAcousticCoverage(
            lane=lane,media_sha256=digest,
            candidate_transcript_sha256="e"*64,
            authored_srt_sha256=build_subtitles_from_authored_csv()[episode]["srt_sha256"],
            cue_count=n,activity_windows_scanned=210 if lane.startswith("short") else 2160,
            cue_count_with_acoustic_activity=n,acoustically_sparse_cues=0,
            lowest_cue_active_percent=100,entire_audio_decoded=True,
            technical_cue_activity_pass=True,blockers=(),
        ))
    return tuple(result)


def synthetic_fingerprints(*,duplicate=False):
    result=[]
    captions=build_subtitles_from_authored_csv()
    for lane,seed in (("short_en",11),("short_hi",11 if duplicate else 19)):
        pcm=fake_pcm(seed=seed)
        bits,count=_sign_bits(pcm)
        episode,_=LANE_EPISODE[lane]
        result.append(ShortAudioFingerprint(
            lane=lane,media_sha256=MEDIA[lane],
            pcm_sha256=sha256(pcm).hexdigest(),
            narrator_plan_id=captions[episode]["narrator_plan_id"],
            count=count,_signs=bits,
        ))
    return tuple(result)


class ThreeLaneAudioHandoffTests(unittest.TestCase):
    def test_three_technical_audio_lanes_can_still_never_publish(self):
        report=evaluate_three_lane_audio_handoff(
            synthetic_cues(),synthetic_fingerprints()
        )
        self.assertTrue(report["three_language_lane_shapes_present"])
        self.assertTrue(report["technical_audio_handoff_unblocked"])
        self.assertFalse(report["natural_human_voice_quality_verified"])
        self.assertFalse(report["distinct_short_narrator_identity_verified"])
        self.assertFalse(report["commercial_voice_and_media_rights_verified"])
        self.assertFalse(report["spoken_subtitle_alignment_verified"])
        self.assertFalse(report["upload_authorized"])
        self.assertFalse(report["publishing_authorized"])
        self.assertNotIn("media_sha256",report)
        self.assertNotIn("pcm_sha256",report)

    def test_duplicate_audio_in_otherwise_complete_lanes_is_quarantined(self):
        report=evaluate_three_lane_audio_handoff(
            synthetic_cues(),synthetic_fingerprints(duplicate=True)
        )
        self.assertFalse(report["technical_audio_handoff_unblocked"])
        self.assertTrue(any(
            value.startswith("SHORT_AUDIO_COLLISION:")
            for value in report["technical_blocking_reasons"]
        ))
        self.assertFalse(report["distinct_short_narrator_identity_verified"])

    def test_one_unchecked_or_silent_cue_blocks_technical_handoff(self):
        original=list(synthetic_cues())
        for changed in (
            replace(original[0],cue_count_with_acoustic_activity=
                    original[0].cue_count-1),
            replace(original[0],technical_cue_activity_pass=False,
                    blockers=("SILENT_OR_NEAR_SILENT_SUBTITLE_CUES",)),
            replace(original[0],entire_audio_decoded=False),
        ):
            with self.subTest(checked=changed.entire_audio_decoded):
                records=tuple([changed,*original[1:]])
                report=evaluate_three_lane_audio_handoff(
                    records,synthetic_fingerprints()
                )
                self.assertFalse(report["technical_audio_handoff_unblocked"])
                self.assertFalse(report["publishing_authorized"])

    def test_missing_duplicate_and_unbound_short_mp4_are_refused(self):
        all_cues=synthetic_cues()
        fingerprints=synthetic_fingerprints()
        for cue,bits in (
            (all_cues[:-1],fingerprints),
            ((all_cues[0],all_cues[0],all_cues[2]),fingerprints),
            (all_cues,(replace(fingerprints[0],media_sha256="f"*64),
                       fingerprints[1])),
        ):
            with self.subTest(count=len(cue)),self.assertRaises(WorkflowError):
                evaluate_three_lane_audio_handoff(cue,bits)

    def test_forged_publish_rights_voice_or_unknown_fingerprint_denied(self):
        original=synthetic_cues()
        bits=synthetic_fingerprints()
        for record in (
            replace(original[0],publishing_authorized=True),
            replace(original[0],language_verified=True),
            replace(original[0],commercial_rights_verified=True),
        ):
            with self.subTest(name=record.lane),self.assertRaises(WorkflowError):
                evaluate_three_lane_audio_handoff(
                    (record,*original[1:]),bits
                )
        with self.assertRaises(WorkflowError):
            evaluate_three_lane_audio_handoff(
                original,(replace(bits[0],upload_authorized=True),bits[1])
            )


if __name__=="__main__":
    unittest.main()
