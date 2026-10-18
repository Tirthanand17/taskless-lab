"""Phase 3R2 SRT candidate technical gates; NO real audio or true ASR.

The fixture starts from existing unverified script-estimated subtitles. Moving
a test timestamp does not make the synthetic candidate accurately aligned.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase3_caption_candidate_intake import (
    CandidateCaption, review_candidate_caption, review_three_caption_candidates,
)
from autopilot.phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv
from autopilot.phase3_complete_narration_intake import EPISODES
from autopilot.phase2r3_authored_pack_audit import SECTIONS


class CandidateCaptionIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.drafts = build_subtitles_from_authored_csv()
        self.candidates = []
        self.audio = {}
        for kind, language, episode, narrator, duration, beats in SECTIONS:
            wav_hash = sha256(("UNREAL_FAKE_WAV_" + episode).encode()).hexdigest()
            self.audio[episode] = {
                "episode_id": episode,
                "original_language_declared": language,
                "intended_narrator_id": narrator,
                "clip_sha256": wav_hash,
                "duration_seconds": duration,
                "technical_wav_screen_passed": True,
                "draft_srt_sha256": self.drafts[episode]["srt_sha256"],
                "audio_content_recognized_as_speech": False,
                "spoken_subtitles_word_aligned": False,
                "approved_for_audio_mux": False,
                "publishing_authorized": False,
            }
            original = self.drafts[episode]["srt"]
            # A time shift is NOT proof that a real speaker aligned to the text.
            simulated = original.replace("00:00:00,000 -->", "00:00:00,050 -->", 1)
            self.assertNotEqual(original, simulated)
            file = self.root / (episode + ".srt")
            file.write_bytes(simulated.encode("utf-8"))
            self.candidates.append(CandidateCaption(
                episode_id=episode, srt_path=file,
                srt_sha256=sha256(file.read_bytes()).hexdigest(),
                wav_sha256=wav_hash, declared_language=language,
                declared_narrator_id=narrator,
                origin_claim="manually_timecoded_unverified",
            ))

    def valid_one(self, index=0, candidate=None, receipt=None):
        target = self.candidates[index] if candidate is None else candidate
        return review_candidate_caption(
            target, self.audio[target.episode_id] if receipt is None else receipt)

    def change_srt(self, index, transform):
        old = self.candidates[index]
        new_data = transform(old.srt_path.read_text("utf-8"))
        old.srt_path.write_text(new_data, encoding="utf-8", newline="\n")
        return replace(old, srt_sha256=sha256(old.srt_path.read_bytes()).hexdigest())

    def test_language_specific_original_text_and_hashed_timeline_intake(self):
        for index, candidate in enumerate(self.candidates):
            r = self.valid_one(index)
            self.assertEqual(r["episode_id"], candidate.episode_id)
            self.assertEqual(r["srt_sha256"], candidate.srt_sha256)
            self.assertTrue(r["all_authored_text_preserved_exactly"])
            self.assertGreater(r["cue_count"], 4)
            for field in ("actual_spoken_words_recognized",
                          "true_speech_to_caption_alignment_verified",
                          "caption_editor_identity_verified",
                          "independent_language_listening_review_verified",
                          "licensed_voice_and_asset_rights_verified",
                          "ready_for_mux", "ready_for_upload",
                          "publishing_authorized"):
                with self.subTest(episode=candidate.episode_id, field=field):
                    self.assertFalse(r[field])
            self.assertEqual(r["network_calls"], 0)

    def test_original_estimated_captions_are_never_passed_as_corrected(self):
        c = self.candidates[0]
        c.srt_path.write_text(self.drafts[c.episode_id]["srt"],
                              encoding="utf-8", newline="\n")
        same = replace(c, srt_sha256=sha256(c.srt_path.read_bytes()).hexdigest())
        with self.assertRaisesRegex(WorkflowError, "estimated SRT"):
            self.valid_one(candidate=same)

    def test_changed_caption_bytes_or_hash_rejected(self):
        c = self.candidates[0]
        c.srt_path.write_bytes(c.srt_path.read_bytes() + b"x")
        with self.assertRaisesRegex(WorkflowError, "changed after"):
            self.valid_one()
        with self.assertRaises(WorkflowError):
            self.valid_one(candidate=replace(c,srt_sha256="xx"))

    def test_wrong_language_narrator_wav_episode_blocked(self):
        c = self.candidates[0]
        for mutation in (
            {"declared_language": "en"},
            {"declared_narrator_id": "narrator_english_b"},
            {"wav_sha256": "a"*64},
            {"episode_id": "csv_tutorial_short_en"},
            {"origin_claim": "definitely_speech_verified"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(WorkflowError):
                self.valid_one(candidate=replace(c, **mutation))

    def test_forged_wav_approval_is_rejected(self):
        c = self.candidates[0]
        for name in ("audio_content_recognized_as_speech",
                     "spoken_subtitles_word_aligned",
                     "approved_for_audio_mux", "publishing_authorized"):
            altered = dict(self.audio[c.episode_id], **{name: True})
            with self.subTest(name=name), self.assertRaises(WorkflowError):
                self.valid_one(receipt=altered)

    def test_truncated_or_reordered_text_rejected_even_with_new_sha(self):
        for index in (0, 1, 2):
            new = self.change_srt(index, lambda s: s.replace(" ", "", 1))
            with self.subTest(index=index), self.assertRaises(WorkflowError):
                self.valid_one(index,candidate=new)

    def test_broken_overlap_and_nonmonotonic_numbering_rejected(self):
        altered = self.change_srt(0, lambda s: s.replace("00:00:00,050 -->",
                                                        "00:00:00,900 -->",1))
        # It may still be valid (shorter first cue); force reverse ordering.
        changed = self.change_srt(0,lambda s:s.replace("00:00:00,900 -->",
                                                       "00:00:40,000 -->",1))
        with self.assertRaises(WorkflowError):
            self.valid_one(candidate=changed)

    def test_line_controls_bom_symlink_and_unsafe_markup_rejected(self):
        c = self.candidates[0]
        original = c.srt_path.read_bytes()
        for payload in (
            b"\xef\xbb\xbf" + original,
            original.replace(b" --> ", b" \t--> ", 1),
            original.replace(b"\n", b"\r\n", 1),
            original.replace(b"\n", b"\n<b>", 1),
            original.replace(b"\n", b"\n" + "\u202e".encode("utf-8"), 1),
        ):
            c.srt_path.write_bytes(payload)
            with self.subTest(payload=payload[:12]), self.assertRaises(WorkflowError):
                self.valid_one(candidate=replace(
                    c,srt_sha256=sha256(payload).hexdigest()))
        c.srt_path.write_bytes(original)
        link = self.root/"subtitle_alias.srt"
        link.symlink_to(c.srt_path)
        with self.assertRaises(WorkflowError):
            self.valid_one(candidate=replace(c,srt_path=link))

    def test_empty_extra_cues_and_missing_unbound_rejected(self):
        c=self.candidates[0]
        with self.assertRaises(WorkflowError):
            self.valid_one(receipt=dict(self.audio[c.episode_id],
                                        draft_srt_sha256="0"*64))
        with self.assertRaises(WorkflowError):
            review_candidate_caption(c,{})
        changed=self.change_srt(0,lambda s:s.replace("\n2\n","\n99\n",1))
        with self.assertRaises(WorkflowError):
            self.valid_one(candidate=changed)

    def test_three_episode_batch_requires_distinct_full_wav_audit(self):
        # The batch's WAV auditor is mocked; NO real WAVs were provided.
        fake = {"publishing_authorized":False,"episodes":list(self.audio.values())}
        with patch("autopilot.phase3_caption_candidate_intake.review_complete_narration_takes",
                   return_value=fake) as check:
            report = review_three_caption_candidates((), self.candidates)
            check.assert_called_once_with(())
        self.assertEqual(report["caption_files_structurally_screened"],3)
        self.assertFalse(report["genuine_speech_alignment_verified"])
        self.assertFalse(report["youtube_upload_or_publishing_authorized"])
        with patch("autopilot.phase3_caption_candidate_intake.review_complete_narration_takes",
                   return_value=fake):
            for bad in (self.candidates[:2],
                        [self.candidates[0],self.candidates[0],self.candidates[2]]):
                with self.assertRaises(WorkflowError):
                    review_three_caption_candidates((),bad)

    def test_batch_rejects_bogus_publishing_authority(self):
        with patch("autopilot.phase3_caption_candidate_intake.review_complete_narration_takes",
                   return_value={"publishing_authorized":True,"episodes":list(self.audio.values())}):
            with self.assertRaises(WorkflowError):
                review_three_caption_candidates((),self.candidates)


if __name__ == "__main__":
    unittest.main()
