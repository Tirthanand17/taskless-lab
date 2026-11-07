"""B4h4 numerical AAC readback is not an upload or human approval."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from autopilot.full_original_rehearsal_media_b4e1 import STATUS as FULL_STATUS
from autopilot.verified_aac_mastering_b4g5 import STATUS as AAC_STATUS
from autopilot.ephemeral_final_aac_evidence_summary_b4h4 import (
    STATUS, REPORT_PATH, MasterEvidenceRefused,
    summarize_measured_ephemeral_masters, main,
)


def fixture() -> dict:
    rows=[]
    for index,(slot,n,lufs) in enumerate((
            ("short_am",4,-18.0),("long",9,-18.4),
            ("short_pm",4,-17.8))):
        digest=f"{index+1:064x}"
        master={
            "status":AAC_STATUS,
            "exact_original_mp4_sha256":digest,
            "source_pcm_duration_seconds_unchanged":58.0 if slot!="long" else 240.0,
            "measured_final_encoded_integrated_lufs":lufs,
            "measured_final_encoded_oversampled_true_peak_dbtp":-1.4,
            "measured_final_encoded_loudness_range_lu":4.5,
            "post_encode_measurement_source":"FINAL_ORIGINAL_AAC_INPUT_EBU_R128",
            "integrated_lufs_and_true_peak_within_internal_band":True,
            "human_listening_and_mobile_playback_verified":False,
            "rights_and_facts_approved":False,
            "youtube_upload_or_release_authorized":False,
            "source_narration_words_and_caption_cue_times_unchanged":True,
            "original_procedural_sound_effect_timing_unchanged":True,
        }
        rows.append({
            "slot":slot,"original_full_scene_count":n,
            "actual_full_ffmpeg_decode_passed":True,
            "b4g5_post_encode_aac_lufs_true_peak_verified":True,
            "release_authorized":False,
            "youtube_uploaded":False,
            "human_full_audio_visual_watch_completed":False,
            "fully_release_ready_for_youtube":False,
            "encoded_h264_aac_sha256":digest,
            "original_audio_encoded_mastering":master,
            "real_pcm_measured_seconds":58.0 if slot!="long" else 240.0,
            "caption_peak_physical_chars_per_second":29.0 if slot=="long" else 19.0,
            "caption_reading_speed_needs_human_review":slot=="long",
            "original_voiceover_text":"NEVER REPRODUCE SAMPLE SPEECH",
            "unverified_news_url":"https://example.invalid/NEVER-RETAIN",
        })
    return {
        "status":FULL_STATUS,
        "full_daily_nonfactual_rehearsal_videos_encoded":3,
        "actually_voiced_complete_original_scene_count":17,
        "all_three_real_h264_aac_ffmpeg_full_decodes_passed":True,
        "all_three_final_encoded_aac_masters_in_conservative_range":True,
        "actual_final_three_video_integrated_lufs_spread":0.6,
        "all_caption_reading_rates_approved":False,
        "real_news_facts_approved":0,"rights_approvals":0,
        "human_full_watches":0,"youtube_uploads":0,
        "release_authorized":False,"episodes":rows,
    }


class PhysicalFinalAacEvidenceTests(unittest.TestCase):
    def test_three_sha_bound_undiscarded_audio_checks_become_only_numbers(self):
        raw=fixture()
        summary=summarize_measured_ephemeral_masters(raw)
        self.assertEqual(summary["status"],STATUS)
        self.assertEqual(summary["actual_original_scenes_in_full_decoded_videos"],17)
        self.assertEqual(summary["physical_original_videos_with_SHA_bound_final_AAC_measurements"],3)
        self.assertEqual(summary["final_encoded_aac_r128_loudness_spread_lu"],.6)
        self.assertEqual([r["slot"] for r in summary["episodes"]],
                         ["short_am","long","short_pm"])
        self.assertEqual([r["fast_caption_pacing_needs_human_review"]
                          for r in summary["episodes"]],[False,True,False])
        self.assertFalse(summary["human_full_watch_or_audio_listening_verified"])
        self.assertFalse(summary["news_claim_and_media_rights_approved"])
        self.assertEqual(summary["youtube_uploads_and_release_authority"],0)
        self.assertTrue(summary["no_rehearsal_video_retained_by_this_step"])
        output=json.dumps(summary)
        for sensitive in ("original_voiceover_text","NEVER REPRODUCE",
                          "unverified_news_url","https://",
                          raw["episodes"][0]["encoded_h264_aac_sha256"]):
            self.assertNotIn(sensitive,output)

    def test_wrong_encoder_identity_release_inventions_and_mastering_refused(self):
        mutations=(
            lambda d:d.update(release_authorized=True),
            lambda d:d.update(youtube_uploads=1),
            lambda d:d.update(human_full_watches=1),
            lambda d:d.update(rights_approvals=1),
            lambda d:d.update(all_three_final_encoded_aac_masters_in_conservative_range=False),
            lambda d:d.update(actual_final_three_video_integrated_lufs_spread=1.4),
            lambda d:d["episodes"][0].update(slot="long"),
            lambda d:d["episodes"][0].update(encoded_h264_aac_sha256="a"*64),
            lambda d:d["episodes"][1].update(encoded_h264_aac_sha256=
                d["episodes"][0]["encoded_h264_aac_sha256"]),
            lambda d:d["episodes"][0].update(
                human_full_audio_visual_watch_completed=True),
            lambda d:d["episodes"][0].update(caption_reading_speed_needs_human_review=True),
            lambda d:d["episodes"][0]["original_audio_encoded_mastering"].update(
                human_listening_and_mobile_playback_verified=True),
            lambda d:d["episodes"][0]["original_audio_encoded_mastering"].update(
                youtube_upload_or_release_authorized=True),
            lambda d:d["episodes"][0]["original_audio_encoded_mastering"].update(
                measured_final_encoded_integrated_lufs=-27.0),
            lambda d:d["episodes"][0]["original_audio_encoded_mastering"].update(
                measured_final_encoded_oversampled_true_peak_dbtp=0.5),
            lambda d:d["episodes"][0]["original_audio_encoded_mastering"].update(
                measured_final_encoded_loudness_range_lu=float("nan")),
            lambda d:d["episodes"][0].update(actual_full_ffmpeg_decode_passed=False),
        )
        for tamper in mutations:
            with self.subTest(tamper=str(tamper)):
                raw=fixture()
                tamper(raw)
                with self.assertRaises(MasterEvidenceRefused):
                    summarize_measured_ephemeral_masters(raw)

    def test_invalid_day_or_manual_public_review_location_never_accepted_by_cli(self):
        with TemporaryDirectory() as temp:
            fake=Path(temp)/"report.json"
            fake.write_text(json.dumps(fixture()),encoding="utf8")
            with patch("sys.argv",["aac-review","--report",str(fake)]):
                with self.assertRaises(MasterEvidenceRefused):
                    main()
        self.assertEqual(REPORT_PATH.name,
                         "EPHEMERAL_FULL_VOICE_REHEARSAL_QA.json")

    def test_no_network_tts_or_second_ffmpeg_executed_for_numeric_readback(self):
        from unittest.mock import patch as mock
        with mock("subprocess.run",side_effect=AssertionError(
                "Post-encode summary must reuse B4g5 evidence, not re-encode")):
            result=summarize_measured_ephemeral_masters(fixture())
        self.assertTrue(result["extra_ffmpeg_or_paid_model_run_performed"] is False)


if __name__=="__main__":
    unittest.main()
