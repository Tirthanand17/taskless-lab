"""Full-length owned/declared offline voice intake tests. NO genuine voices.

Mocked wave receipts and dummy local evidence bytes test orchestration only;
the actual WAV energy/sample check is separately tested in voice handoff.
Neither a tone nor a forged rights document is licensed narration.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import math
import struct
import unittest
import wave

from autopilot.agent_org import WorkflowError
from autopilot.phase3_complete_narration_intake import (
    CompleteNarrationTake,review_complete_narration_takes,
)
from autopilot.phase3_voice_subtitle_handoff import inspect_external_voice_wav

PROFILES=(
    ("csv_tutorial_short_hi","hi","narrator_hindi_a",42),
    ("csv_tutorial_short_en","en","narrator_english_b",42),
    ("csv_tutorial_long_hi","hi","narrator_hindi_long_c",432),
)


def sha(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


class CompleteThreeNarrationGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.audio_seconds={}
        self.items=[]
        for i,(episode,lang,narrator,duration) in enumerate(PROFILES):
            audio=self.root/f"audio_{i}.wav"
            audio.write_bytes((f"SIMULATED BYTES-{i}-".encode("ascii"))*20)
            rights=self.root/f"claims_{i}.txt"
            rights.write_text("UNVERIFIED CLAIMED RIGHTS DOCUMENT - synthetic example only",encoding="utf-8")
            self.audio_seconds[episode]=duration
            self.items.append(CompleteNarrationTake(
                episode_id=episode,wav_path=audio,wav_sha256=sha(audio),
                declared_language=lang,declared_narrator_id=narrator,
                source_kind="owned_recording",
                claimed_license_spdx="owned-recording-contract",
                rights_document_path=rights,rights_document_sha256=sha(rights),
                commercial_use_claimed=True,adaptation_allowed_claimed=True,
                attribution_prepared=True,speaker_consent_claimed=True,
            ))

    def mock_technical(self,path,*,episode_id,expected_seconds,
                       declared_narrator_id,declared_language):
        return {
            "sha256":sha(path),
            "duration_seconds":expected_seconds,
            "real_speech_verified":False,
            "license_rights_verified":False,
        }

    def check(self,takes=None):
        with patch(
            "autopilot.phase3_complete_narration_intake.inspect_external_voice_wav",
            side_effect=self.mock_technical
        ):
            return review_complete_narration_takes(
                self.items if takes is None else takes)

    def variant(self,index,**updates):
        items=list(self.items)
        items[index]=replace(items[index],**updates)
        return items

    def test_three_full_take_metadata_link_to_original_language_and_voice(self):
        report=self.check()
        self.assertEqual(report["complete_takes_received"],3)
        self.assertEqual(report["distinct_audio_byte_hashes"],3)
        self.assertEqual(set(x["episode_id"] for x in report["episodes"]),
                         set(x[0] for x in PROFILES))
        byep={x["episode_id"]:x for x in report["episodes"]}
        for episode,lang,narrator,duration in PROFILES:
            r=byep[episode]
            self.assertEqual(r["original_language_declared"],lang)
            self.assertEqual(r["intended_narrator_id"],narrator)
            self.assertEqual(r["duration_seconds"],duration)
            self.assertEqual(len(r["draft_srt_sha256"]),64)
            self.assertFalse(r["spoken_subtitles_word_aligned"])
            self.assertFalse(r["approved_for_audio_mux"])
            self.assertFalse(r["publishing_authorized"])

    def test_no_human_approval_claim_even_when_fake_wav_inspection_succeeds(self):
        x=self.check()
        for name in (
            "three_licensed_human_sounding_voices_verified",
            "two_distinct_short_narrators_audibly_verified",
            "human_language_or_legal_review_verified",
            "real_audio_caption_alignment_verified",
            "external_provenance_authenticated",
            "public_or_private_upload_authorized",
            "any_video_ready_for_publication","publishing_authorized",
            "provider_or_model_download_performed","cloud_media_artifacts_stored",
        ):
            with self.subTest(name=name):
                self.assertIs(x[name],False)
        self.assertEqual(x["network_calls"],0)

    def test_cross_language_or_swapped_speaker_fail_closed(self):
        for field,value in (
            ("declared_language","en"),
            ("declared_narrator_id","narrator_english_b"),
        ):
            with self.subTest(field=field),self.assertRaises(WorkflowError):
                self.check(self.variant(0,**{field:value}))

    def test_duplicate_episode_or_missing_take_rejected(self):
        with self.assertRaises(WorkflowError):
            self.check(self.items[:2])
        with self.assertRaises(WorkflowError):
            self.check((self.items[0],self.items[0],self.items[2]))
        with self.assertRaises(WorkflowError):
            self.check(self.variant(1,episode_id="unknown_clip"))

    def test_identical_audio_bytes_not_counted_as_distinct_voices(self):
        self.items[1].wav_path.write_bytes(self.items[0].wav_path.read_bytes())
        takes=self.variant(1,wav_sha256=sha(self.items[1].wav_path))
        with self.assertRaisesRegex(WorkflowError,"Identical WAV bytes"):
            self.check(takes)

    def test_audio_sha_change_detected(self):
        self.items[0].wav_path.write_bytes(b"changed-audio-bytes")
        with self.assertRaises(WorkflowError):
            self.check()

    def test_rights_document_mutation_or_symlink_rejected(self):
        self.items[0].rights_document_path.write_text("CHANGED RIGHTS CLAIM",encoding="utf-8")
        with self.assertRaises(WorkflowError):
            self.check()
        self.items[0].rights_document_path.write_text(
            "UNVERIFIED CLAIMED RIGHTS DOCUMENT - synthetic example only",encoding="utf-8")
        alias=self.root/"rights_link.txt"
        alias.symlink_to(self.items[0].rights_document_path)
        with self.assertRaises(WorkflowError):
            self.check(self.variant(0,rights_document_path=alias))

    def test_license_or_commercial_claim_not_present_rejected(self):
        for field,value in (
            ("claimed_license_spdx","CC-BY-NC-4.0"),
            ("commercial_use_claimed",False),
            ("adaptation_allowed_claimed",False),
            ("attribution_prepared",False),
            ("speaker_consent_claimed",False),
            ("offline_model_sha256","0"*64),
        ):
            with self.subTest(field=field),self.assertRaises(WorkflowError):
                self.check(self.variant(0,**{field:value}))

    def test_offline_tts_requires_declared_pinned_model_hash(self):
        take=self.variant(0,source_kind="offline_tts",
                          claimed_license_spdx="Apache-2.0",
                          speaker_consent_claimed=False)
        with self.assertRaises(WorkflowError):
            self.check(take)
        take=self.variant(0,source_kind="offline_tts",
                          claimed_license_spdx="Apache-2.0",
                          speaker_consent_claimed=False,
                          offline_model_sha256="a"*64)
        self.assertFalse(self.check(take)["publishing_authorized"])

    def test_bogus_declared_source_or_unpinned_clip_rejected(self):
        for kwargs in (
            {"source_kind":"paid_voice_provider"},
            {"wav_sha256":"INVALID"},
            {"claimed_license_spdx":"Apache-2.0"},
        ):
            with self.subTest(kwargs=kwargs),self.assertRaises(WorkflowError):
                self.check(self.variant(1,**kwargs))

    def test_audio_duration_must_match_video_not_just_nonzero(self):
        def short_audio(path,*,episode_id,expected_seconds,
                        declared_narrator_id,declared_language):
            return {
                "sha256":sha(path),
                "duration_seconds":expected_seconds-20,
                "real_speech_verified":False,
                "license_rights_verified":False,
            }
        with patch("autopilot.phase3_complete_narration_intake.inspect_external_voice_wav",
                   side_effect=short_audio):
            with self.assertRaisesRegex(WorkflowError,"duration/digest"):
                review_complete_narration_takes(self.items)

    def test_claimed_speech_from_raw_audio_inspector_is_rejected(self):
        def untrusted_voice(path,*,episode_id,expected_seconds,
                           declared_narrator_id,declared_language):
            return {
                "sha256":sha(path),"duration_seconds":expected_seconds,
                "real_speech_verified":True,"license_rights_verified":True,
            }
        with patch("autopilot.phase3_complete_narration_intake.inspect_external_voice_wav",
                   side_effect=untrusted_voice):
            with self.assertRaises(WorkflowError):
                review_complete_narration_takes(self.items)

    def test_real_wav_tone_is_not_complete_42_second_narration(self):
        # Real wave bytes, not a mocked inspector; deliberately ONE SECOND
        # of 220Hz synthetic tone. This can have high WAV energy, but it
        # must not be a completed original 42s voice asset.
        track=self.root/"one_second_tone.wav"
        with wave.open(str(track),"wb") as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
            data=b"".join(struct.pack("<h",int(6000*math.sin(
                2*math.pi*220*i/16000))) for i in range(16000))
            w.writeframes(data)
        with self.assertRaises(WorkflowError):
            inspect_external_voice_wav(
                track,episode_id="csv_tutorial_short_en",
                expected_seconds=42,
                declared_narrator_id="narrator_english_b",declared_language="en",
            )


if __name__=="__main__":
    unittest.main()
