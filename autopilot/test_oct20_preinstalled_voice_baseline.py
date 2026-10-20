"""Actual optional locally installed eSpeak voice pacing experiment.

Mechanical EN/HI generated sounds are never human voice/rights approval.
CI skips real audio when eSpeak is absent; static source/read-only checks run.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import shutil
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.oct20_preinstalled_voice_baseline import (
    SPEAKERS,original_first_scene,make_existing_espeak_comparison,
)


class Oct20ExistingMechanicalBaselineTests(unittest.TestCase):
    def test_frozen_actual_english_hindi_original_scene_hooks(self):
        self.assertEqual(set(SPEAKERS),{
            "fm_20261020_short_en","fm_20261020_short_hi",
        })
        en=original_first_scene("fm_20261020_short_en")
        hi=original_first_scene("fm_20261020_short_hi")
        self.assertEqual(en["first_scene_duration_seconds"],4)
        self.assertEqual(hi["first_scene_duration_seconds"],5)
        self.assertTrue(en["source_first_scene_text"].startswith("Chatbots"))
        self.assertTrue(hi["source_first_scene_text"].startswith("AI से"))
        self.assertEqual(en["voice_language"],"en")
        self.assertEqual(hi["voice_language"],"hi")
        self.assertEqual(len(en["source_first_scene_sha256"]),64)
        self.assertEqual(len(hi["source_first_scene_sha256"]),64)

    def test_refuse_legacy_csv_or_long_episode_as_short_speech_demo(self):
        for episode in (
            "csv_tutorial_short_en","fm_20261020_long_hi",
            "unknown","",None,False,
        ):
            with self.subTest(episode=str(episode)),self.assertRaises(WorkflowError):
                original_first_scene(episode)

    def test_never_overwrite_existing_audio_file(self):
        with TemporaryDirectory() as tmp:
            existing=Path(tmp)/"keep.wav"
            existing.write_bytes(b"ORIGINAL-OWNER-AUDIO")
            with self.assertRaises(WorkflowError):
                make_existing_espeak_comparison(
                    episode_id="fm_20261020_short_en",
                    output_path=existing,
                )
            self.assertEqual(existing.read_bytes(),b"ORIGINAL-OWNER-AUDIO")

    def test_refuse_wrong_extension_or_nonexistent_parent(self):
        with TemporaryDirectory() as tmp:
            for name in ("wrong.mp3","wrong.aac","wrong.txt"):
                with self.subTest(name=name),self.assertRaises(WorkflowError):
                    make_existing_espeak_comparison(
                        episode_id="fm_20261020_short_en",
                        output_path=Path(tmp)/name,
                    )
            target=Path(tmp)/"no_parent"/"clip.wav"
            with self.assertRaises(WorkflowError):
                make_existing_espeak_comparison(
                    episode_id="fm_20261020_short_en",output_path=target)
            self.assertFalse(target.parent.exists())

    def test_missing_engine_blocks_without_model_download(self):
        with TemporaryDirectory() as tmp:
            with patch(
                "autopilot.oct20_preinstalled_voice_baseline.shutil.which",
                return_value=None,
            ):
                with self.assertRaises(WorkflowError):
                    make_existing_espeak_comparison(
                        episode_id="fm_20261020_short_hi",
                        output_path=Path(tmp)/"not_generated.wav",
                    )
            self.assertFalse((Path(tmp)/"not_generated.wav").exists())

    @unittest.skipUnless(shutil.which("espeak"),
                         "Low-fidelity eSpeak CLI already installed required")
    def test_real_mechanical_english_hindi_pcm_but_voice_rejected(self):
        with TemporaryDirectory() as tmp:
            receipts=[]
            for episode in SPEAKERS:
                name=Path(tmp)/(episode+".wav")
                result=make_existing_espeak_comparison(
                    episode_id=episode,output_path=name)
                receipts.append(result)
                with self.subTest(episode=episode):
                    self.assertGreater(name.stat().st_size,1000)
                    self.assertEqual(
                        result["status"],
                        "ACTUAL_ESPEAK_MECHANICAL_BASELINE_REJECTED_FOR_NARRATION",
                    )
                    self.assertTrue(result["technical_pcm_screen_passed"])
                    self.assertTrue(result["not_a_production_voice"])
                    for key in (
                        "spoken_word_timing_verified",
                        "actual_human_speech_verified",
                        "natural_voice_quality_verified",
                        "native_hindi_pronunciation_verified",
                        "distinct_short_speakers_verified",
                        "commercial_voice_rights_reviewed",
                        "eligible_for_mux",
                        "youtube_upload_authorized",
                        "youtube_publish_authorized",
                    ):
                        self.assertIs(result[key],False)
                    self.assertEqual(result["new_models_downloaded"],0)
                    self.assertEqual(result["external_network_requests"],0)
                    self.assertEqual(result["monthly_recurring_infrastructure_inr"],0)
            self.assertNotEqual(receipts[0]["wav_sha256"],
                                receipts[1]["wav_sha256"])


if __name__=="__main__":
    unittest.main()
