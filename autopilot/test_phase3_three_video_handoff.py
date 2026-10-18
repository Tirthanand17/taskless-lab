"""Full-episode three-video handoff regressions (FAKE BYTES; NOT genuine media).

The orchestration tests intentionally substitute mock WAV/media/SRT inspectors.
They verify rejection boundaries, not voice, captions, rights or real HD mux.
Existing dedicated tests separately exercise actual ffprobe and WAV parsing.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase3_complete_narration_intake import CompleteNarrationTake
from autopilot.phase3_caption_candidate_intake import CandidateCaption
from autopilot.phase3_three_video_handoff import (
    TechnicalHandoffInput,prepare_three_video_technical_handoff,
)
from autopilot.phase3_visual_signal_audit import EPISODES


PROFILES={
    "csv_tutorial_short_en":("en","narrator_english_b"),
    "csv_tutorial_short_hi":("hi","narrator_hindi_a"),
    "csv_tutorial_long_hi":("hi","narrator_hindi_long_c"),
}
def hash_bytes(raw:bytes)->str:
    return sha256(raw).hexdigest()

class ThreeOriginalVideoHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.items=[]
        self.audio_receipts=[]
        for ep in sorted(EPISODES):
            lang,narrator=PROFILES[ep]
            duration,w,h,fps,frames=EPISODES[ep]
            mp4=self.root/(ep+".mp4")
            wav=self.root/(ep+".wav")
            srt=self.root/(ep+".srt")
            license_file=self.root/(ep+".license.txt")
            for path,content in (
                (mp4,("UNREAL_MP4_"+ep).encode()*20),
                (wav,("UNREAL_WAV_"+ep).encode()*20),
                (srt,("UNREAL_SRT_"+ep).encode()*20),
                (license_file,b"UNVERIFIED SIMULATED RIGHTS BYTES"),
            ):
                path.write_bytes(content)
            take=CompleteNarrationTake(
                episode_id=ep,wav_path=wav,wav_sha256=hash_bytes(wav.read_bytes()),
                declared_language=lang,declared_narrator_id=narrator,
                source_kind="owned_recording",claimed_license_spdx="owned-recording-contract",
                rights_document_path=license_file,
                rights_document_sha256=hash_bytes(license_file.read_bytes()),
                commercial_use_claimed=True, adaptation_allowed_claimed=True,
                attribution_prepared=True,speaker_consent_claimed=True,
            )
            caption=CandidateCaption(
                episode_id=ep,srt_path=srt,srt_sha256=hash_bytes(srt.read_bytes()),
                wav_sha256=take.wav_sha256,declared_language=lang,
                declared_narrator_id=narrator,
                origin_claim="manually_timecoded_unverified",
            )
            video_receipt={
                "video_sha256":hash_bytes(mp4.read_bytes()),
                "video_duration_seconds":duration,
                "video_width":w,"video_height":h,
                "video_frame_rate":fps,"video_frame_count":frames,
                "original_language_intended":lang,
                "narrator_plan_id":narrator,
                "media_has_narration":False,
                "receipt_issuer_authenticated":False,
                "publishing_authorized":False,
            }
            self.audio_receipts.append({
                "episode_id":ep,
                "clip_sha256":take.wav_sha256,
                "original_language_declared":lang,
                "intended_narrator_id":narrator,
                "technical_wav_screen_passed":True,
                "draft_srt_sha256":"e"*64,
                "duration_seconds":duration,
                "audio_content_recognized_as_speech":False,
                "spoken_subtitles_word_aligned":False,
                "approved_for_audio_mux":False,
                "publishing_authorized":False,
            })
            self.items.append(TechnicalHandoffInput(
                ep,mp4,video_receipt,take,caption,
                self.root/(ep+".future-mux.mp4"),
            ))

    def mocked_audio(self, takes):
        return {
            "publishing_authorized":False,
            "three_licensed_human_sounding_voices_verified":False,
            "human_language_or_legal_review_verified":False,
            "complete_takes_received":3,
            "episodes":self.audio_receipts,
        }

    def mocked_video(self,*,receipt,episode_id,mp4):
        return {
            "publishing_authorized":False,
            "video_sha256":hash_bytes(mp4.read_bytes()),
        }

    def mocked_caption(self,candidate,audio_receipt):
        return {
            "publishing_authorized":False,
            "true_speech_to_caption_alignment_verified":False,
            "ready_for_mux":False,
            "srt_sha256":candidate.srt_sha256,
            "wav_sha256":candidate.wav_sha256,
            "language_declared":candidate.declared_language,
            "narrator_plan_id":candidate.declared_narrator_id,
            "source_script_sha256":"c"*64,
        }

    def check(self, items=None, *, audio=None,video=None,caption=None,signal=None,pacing=None):
        with (patch("autopilot.phase3_three_video_handoff.review_complete_narration_takes",
                    side_effect=audio or self.mocked_audio),
              patch("autopilot.phase3_three_video_handoff.verify_quarantined_receipt",
                    side_effect=video or self.mocked_video),
              patch("autopilot.phase3_three_video_handoff.review_candidate_caption",
                    side_effect=caption or self.mocked_caption),
              patch("autopilot.phase3_three_video_handoff.inspect_nonplaceholder_audio_candidate",
                    side_effect=signal or (lambda *,wav_path,episode_id,expected_sha256: {
                        "status":"OBVIOUS_AUDIO_PLACEHOLDER_NOT_DETECTED_UNVERIFIED",
                        "episode_id":episode_id,"wav_sha256":expected_sha256,
                        "publishing_authorized":False,
                        "intelligible_speech_recognized":False,
                        "ready_for_mux_or_upload":False,
                    })),
              patch("autopilot.phase3_three_video_handoff.inspect_voice_pacing_candidate",
                    side_effect=pacing or (lambda *,wav_path,episode_id,expected_sha256: {
                        "status":"PACING_AND_WAVEFORM_TECHNICAL_SCREEN_ONLY_UNVERIFIED",
                        "episode_id":episode_id,"wav_sha256":expected_sha256,
                        "natural_human_speech_verified":False,
                        "ready_for_mux_or_upload":False,
                        "publishing_authorized":False,
                    }))):
            return prepare_three_video_technical_handoff(self.items if items is None else items)

    def modified(self, index, **changes):
        result=list(self.items)
        result[index]=replace(result[index],**changes)
        return result

    def test_all_three_originals_bind_to_language_appropriate_inputs_without_writes(self):
        before={x.name:x.read_bytes() for x in self.root.iterdir()}
        result=self.check()
        self.assertEqual(result["status"],
                         "THREE_VIDEO_TECHNICAL_HANDOFF_ONLY_RELEASE_BLOCKED")
        self.assertEqual(len(result["episodes"]),3)
        self.assertEqual(len(result["source_bundle_sha256"]),64)
        self.assertEqual({r["intended_language"] for r in result["episodes"]
                          if "short" in r["episode_id"]},{"en","hi"})
        for key in ("actual_voice_speech_language_verified",
                    "actual_word_audio_alignment_verified",
                    "professional_visual_or_factual_quality_verified",
                    "legal_rights_authenticated","final_mux_generated",
                    "any_durable_cloud_media_stored",
                    "youtube_upload_or_publishing_authorized"):
            with self.subTest(key=key):
                self.assertFalse(result[key])
        self.assertEqual(result["network_calls"],0)
        self.assertEqual(result["files_written"],0)
        self.assertEqual(before,{x.name:x.read_bytes() for x in self.root.iterdir()})
        for item in self.items:
            self.assertFalse(item.future_mux_path.exists())

    def test_missing_duplicate_and_unknown_episode_rejected(self):
        for entries in (
            self.items[:2],
            [self.items[0],self.items[0],self.items[2]],
            self.modified(0,episode_id="unknown"),
        ):
            with self.subTest(episodes=[x.episode_id for x in entries]):
                with self.assertRaises(WorkflowError):
                    self.check(entries)

    def test_cross_episode_voice_caption_and_video_swap_rejected(self):
        a,b=self.items[:2]
        for altered in (
            self.modified(0,narration_take=b.narration_take),
            self.modified(0,caption_candidate=b.caption_candidate),
            self.modified(0,video_receipt=b.video_receipt),
        ):
            with self.assertRaises(WorkflowError):
                self.check(altered)

    def test_byte_tamper_after_receipt_is_rejected_even_with_fake_verifier(self):
        self.items[0].silent_video_path.write_bytes(b"tampered simulated movie")
        with self.assertRaisesRegex(WorkflowError,"silent-video"):
            self.check()

    def test_tampered_voice_or_srt_receipt_cannot_be_misbound(self):
        item=self.items[0]
        wrong_cap=replace(item.caption_candidate,wav_sha256="a"*64)
        def hard_caption(candidate,voice):
            return dict(self.mocked_caption(candidate,voice),wav_sha256="b"*64)
        with self.assertRaises(WorkflowError):
            self.check(self.modified(0,caption_candidate=wrong_cap),
                       caption=hard_caption)
        def too_powerful(candidate,voice):
            return dict(self.mocked_caption(candidate,voice),ready_for_mux=True)
        with self.assertRaises(WorkflowError):
            self.check(caption=too_powerful)

    def test_false_video_and_wav_approval_claims_rejected(self):
        def bad_video(*,receipt,episode_id,mp4):
            return dict(self.mocked_video(receipt=receipt,episode_id=episode_id,
                                          mp4=mp4),publishing_authorized=True)
        with self.assertRaises(WorkflowError):
            self.check(video=bad_video)
        def bad_audio(takes):
            return dict(self.mocked_audio(takes),publishing_authorized=True)
        with self.assertRaises(WorkflowError):
            self.check(audio=bad_audio)

    def test_bad_full_frame_count_or_geometry_rejected(self):
        for key,val in (("video_frame_count",3),("video_width",640),
                        ("video_duration_seconds",8)):
            r=dict(self.items[0].video_receipt,**{key:val})
            with self.subTest(key=key),self.assertRaises(WorkflowError):
                self.check(self.modified(0,video_receipt=r))

    def test_symlinks_output_overwrite_and_missing_parents_rejected(self):
        item=self.items[0]
        link=self.root/"some-link.mp4"
        link.symlink_to(item.silent_video_path)
        with self.assertRaises(WorkflowError):
            self.check(self.modified(0,silent_video_path=link))
        item.future_mux_path.write_bytes(b"existing")
        with self.assertRaises(WorkflowError):
            self.check()
        self.assertEqual(item.future_mux_path.read_bytes(),b"existing")
        item.future_mux_path.unlink()
        with self.assertRaises(WorkflowError):
            self.check(self.modified(0,future_mux_path=self.root/"missing"/"new.mp4"))

    def test_same_input_and_output_path_reused_across_episodes_rejected(self):
        # Both originals are allowed only distinct output targets.
        with self.assertRaises(WorkflowError):
            self.check(self.modified(0,future_mux_path=self.items[1].future_mux_path))
        # Rights document symlink is rejected by the path gate.
        link=self.root/"rights_link.txt"
        link.symlink_to(self.items[0].narration_take.rights_document_path)
        newtake=replace(self.items[0].narration_take,rights_document_path=link)
        with self.assertRaises(WorkflowError):
            self.check(self.modified(0,narration_take=newtake))

    def test_wrong_lane_wav_receipt_or_missing_audio_episode_rejected(self):
        old=self.audio_receipts
        try:
            self.audio_receipts=old[:2]
            with self.assertRaises(WorkflowError):
                self.check()
        finally:
            self.audio_receipts=old
        altered=list(old)
        altered[0]=dict(old[0],clip_sha256="0"*64)
        self.audio_receipts=altered
        try:
            def stricter(candidate,voice):
                if voice.get("clip_sha256")!=candidate.wav_sha256:
                    raise WorkflowError("WAV digest mismatch")
                return self.mocked_caption(candidate,voice)
            with self.assertRaises(WorkflowError):
                self.check(caption=stricter)
        finally:
            self.audio_receipts=old

    def test_voice_signal_rejects_forged_speech_clearance(self):
        def forged(*,wav_path,episode_id,expected_sha256):
            return {
                "status":"OBVIOUS_AUDIO_PLACEHOLDER_NOT_DETECTED_UNVERIFIED",
                "episode_id":episode_id,
                "wav_sha256":expected_sha256,
                "intelligible_speech_recognized":True,
                "ready_for_mux_or_upload":True,
                "publishing_authorized":False,
            }
        with self.assertRaisesRegex(WorkflowError,"signal screen"):
            self.check(signal=forged)

    def test_voice_signal_true_placeholder_failure_blocks_handoff(self):
        def blocked(*,wav_path,episode_id,expected_sha256):
            raise WorkflowError("Sustained synthetic-like pure tone")
        with self.assertRaisesRegex(WorkflowError,"pure tone"):
            self.check(signal=blocked)

    def test_pacing_receipt_cannot_claim_natural_human_voice(self):
        def forged(*,wav_path,episode_id,expected_sha256):
            return {
                "status":"PACING_AND_WAVEFORM_TECHNICAL_SCREEN_ONLY_UNVERIFIED",
                "episode_id":episode_id,"wav_sha256":expected_sha256,
                "natural_human_speech_verified":True,
                "ready_for_mux_or_upload":False,
                "publishing_authorized":False,
            }
        with self.assertRaisesRegex(WorkflowError,"falsely claimed"):
            self.check(pacing=forged)

    def test_actual_waveform_failure_blocks_video_handoff(self):
        def damaged(*,wav_path,episode_id,expected_sha256):
            raise WorkflowError("Severe saturated/clipped original narrator PCM")
        with self.assertRaisesRegex(WorkflowError,"clipped"):
            self.check(pacing=damaged)

    def test_invalid_user_provided_receipt_type_or_bulk_claim_rejected(self):
        with self.assertRaises(WorkflowError):
            self.check(self.modified(0,video_receipt="invalid"))
        # Non-boolean false must not silently satisfy the trust boundary.
        fake=dict(self.items[0].video_receipt,media_has_narration=0)
        with self.assertRaises(WorkflowError):
            self.check(self.modified(0,video_receipt=fake))

if __name__=="__main__":
    unittest.main()
