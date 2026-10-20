"""Oct 20 narrator packets and THREE real disposable PCM WAVs.

The waveform fixtures are SYNTHETIC TONES, deliberately not human voices.
Tests make no speech, identity, rights, ASR or upload approval claims. This
exercises actual reuse of the existing WAV inspector for 42/44/480 seconds.
"""
from array import array
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys
import wave
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.oct20_owned_voice_handoff import (
    TARGETS,Oct20OwnedVoiceTake,create_oct20_voice_session_packet,
    export_oct20_narrator_notes,screen_oct20_owned_voice_takes,
)


def sha(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def synthetic_tone_pcm(path:Path,seconds:int)->None:
    # Intentionally changing loudness of a mechanical square wave every
    # 250ms. It is STILL NOT A HUMAN VOICE, but is not the exact repeated
    # fixture now quarantined by the new signal-shape screen.
    with wave.open(str(path),"wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        for block_number in range(seconds*4):
            amplitude=5200+(block_number*31)%2900
            samples=array("h",(amplitude if (i//80)%2 else -amplitude
                               for i in range(4000)))
            if sys.byteorder!="little":
                samples.byteswap()
            writer.writeframesraw(samples.tobytes())


class Oct20OwnedVoiceHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir=TemporaryDirectory(prefix="flowminute-synthetic-voice-tests-")
        cls.root=Path(cls.dir.name)
        cls.packet=create_oct20_voice_session_packet()
        cls.cues={r["episode_id"]:r for r in cls.packet["lanes"]}
        cls.takes=[]
        for ep,(lang,kind,seconds,role) in TARGETS.items():
            wav=cls.root/(ep+".wav")
            synthetic_tone_pcm(wav,seconds)
            consent=cls.root/(ep+".rights-private.txt")
            consent.write_text(
                "SYNTHETIC FIXTURE ONLY. NO REAL PERSON. NO ACTUAL CONSENT.\n",
                encoding="utf-8",
            )
            cls.takes.append(Oct20OwnedVoiceTake(
                episode_id=ep,source_wav=wav,
                declared_wav_sha256=sha(wav),
                script_sha256=cls.cues[ep]["script_sha256"],
                narrator_role=role,
                rights_file=consent,
                declared_rights_sha256=sha(consent),
                source_kind="owned_recording",
                commercial_use_declared=True,
                speaker_consent_declared=True,
            ))
        cls.takes=tuple(cls.takes)

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def test_real_source_packet_contains_original_25_narration_cues(self):
        report=self.packet
        self.assertEqual(report["status"],
                         "ORIGINAL_THREE_VIDEO_NARRATOR_RECORDING_SCRIPT_ONLY")
        self.assertEqual(report["total_recording_cues"],25)
        self.assertEqual(report["recording_take_count_required"],3)
        self.assertEqual({x["episode_id"] for x in report["lanes"]},set(TARGETS))
        self.assertEqual([x["target_seconds"] for x in report["lanes"]],
                         [42,44,480])
        self.assertEqual([x["cue_count"] for x in report["lanes"]],[7,7,11])
        self.assertEqual(
            [x["language"] for x in report["lanes"]],["en","hi","hi"])
        for lane in report["lanes"]:
            self.assertFalse(lane["narrator_person_identified_or_licensed"])
            self.assertEqual(
                lane["cues"][0]["editorial_start_second"],0)
            self.assertEqual(
                lane["cues"][-1]["editorial_end_second"],lane["target_seconds"])
            self.assertTrue(all(x["cue_is_estimated_not_asr_aligned"]
                                for x in lane["cues"]))
            self.assertTrue(all(len(x["recording_text_sha256"])==64
                                for x in lane["cues"]))
        for denied in ("independent_human_voice_confirmed",
                       "rights_legally_authenticated",
                       "word_level_audio_alignment_verified",
                       "youtube_upload_authorized",
                       "youtube_publish_authorized"):
            self.assertFalse(report[denied])
        self.assertEqual(report["actual_wav_takes_received"],0)
        self.assertEqual(report["external_network_requests"],0)
        self.assertEqual(report["monthly_recurring_infrastructure_inr"],0)

    def test_actual_three_complete_synthetic_tone_wavs_are_not_human_voices(self):
        # Three REAL 42/44/480-sec PCM WAVs, not a mocked audio inspector.
        result=screen_oct20_owned_voice_takes(self.takes)
        self.assertEqual(result["expected_episode_count"],3)
        self.assertEqual(result["wav_digest_checks_passed"],3)
        self.assertEqual(result["distinct_wav_file_bytes"],3)
        self.assertTrue(result["recording_lengths_matched_targets"])
        self.assertTrue(result["local_rights_document_hashes_matched"])
        self.assertTrue(result["actual_pcm_signal_anomaly_screen_passed"])
        self.assertFalse(result["obvious_repeated_test_tones_or_clipping_hold"])
        self.assertFalse(result["acoustic_voice_naturalness_or_identity_determined"])
        for denied in (
            "independent_human_voice_confirmed",
            "real_speech_language_verified",
            "two_distinct_short_speakers_audibly_verified",
            "commercial_voice_rights_legally_authenticated",
            "human_consent_independently_authenticated",
            "word_level_asr_transcription_verified","srt_sync_verified",
            "ready_for_media_mux","youtube_upload_authorized",
            "youtube_publish_authorized",
        ):
            self.assertFalse(result[denied])
        for fake_secret in ("rights-private.txt","narrator_",".wav"):
            self.assertNotIn(fake_secret,str(result))

    def test_missing_reordered_or_duplicate_episode_is_denied(self):
        with self.assertRaises(WorkflowError):
            screen_oct20_owned_voice_takes(self.takes[:2])
        with self.assertRaises(WorkflowError):
            screen_oct20_owned_voice_takes((self.takes[0],)*3)
        # Correctly reordered independent inputs remain valid.
        report=screen_oct20_owned_voice_takes(tuple(reversed(self.takes)))
        self.assertEqual(report["wav_digest_checks_passed"],3)

    def test_repeated_42_second_square_wave_newly_refused_by_three_take_intake(self):
        # This exact 250ms repeated waveform previously passed duration/RMS
        # and SHA checks even if a caller claimed its consent/rights. The
        # new actual-PCM triage must quarantine it before editor handoff.
        repeated=self.root/"repeated_42_second_square_hold.wav"
        samples=array("h",(6400 if (i//80)%2 else -6400
                           for i in range(4000)))
        if sys.byteorder!="little":
            samples.byteswap()
        raw=samples.tobytes()
        try:
            with wave.open(str(repeated),"wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                for _ in range(42*4):
                    wav.writeframesraw(raw)
            bad=replace(self.takes[0],source_wav=repeated,
                        declared_wav_sha256=sha(repeated))
            with self.assertRaises(WorkflowError):
                screen_oct20_owned_voice_takes((bad,*self.takes[1:]))
        finally:
            repeated.unlink(missing_ok=True)

    def test_older_csv_episode_and_wrong_new_script_are_denied(self):
        bad=replace(self.takes[0],episode_id="csv_tutorial_short_en")
        with self.assertRaises(WorkflowError):
            screen_oct20_owned_voice_takes((bad,*self.takes[1:]))
        bad=replace(self.takes[0],script_sha256="a"*64)
        with self.assertRaises(WorkflowError):
            screen_oct20_owned_voice_takes((bad,*self.takes[1:]))

    def test_wrong_language_role_and_voice_source_never_admitted(self):
        for kwargs in (
            {"narrator_role":"narrator_english_old"},
            {"source_kind":"unapproved_paid_voice_api"},
            {"source_kind":"offline_tts"},
        ):
            with self.subTest(kwargs=kwargs),self.assertRaises(WorkflowError):
                screen_oct20_owned_voice_takes((
                    replace(self.takes[0],**kwargs),*self.takes[1:],
                ))

    def test_claimed_commercial_rights_and_consent_required_but_not_proof(self):
        for field in ("commercial_use_declared","speaker_consent_declared"):
            with self.subTest(field=field),self.assertRaises(WorkflowError):
                screen_oct20_owned_voice_takes((
                    replace(self.takes[0],**{field:False}),
                    *self.takes[1:],
                ))

    def test_rights_document_changed_or_symlink_is_rejected(self):
        rights=self.takes[0].rights_file
        alias=self.root/"dangerous-symlink.txt"
        try:
            alias.symlink_to(rights)
            with self.assertRaises(WorkflowError):
                screen_oct20_owned_voice_takes((
                    replace(self.takes[0],rights_file=alias),
                    *self.takes[1:],
                ))
        finally:
            alias.unlink(missing_ok=True)
        rights.write_text("MUTATED SYNTHETIC RIGHTS\n",encoding="utf-8")
        try:
            with self.assertRaises(WorkflowError):
                screen_oct20_owned_voice_takes(self.takes)
        finally:
            rights.write_text(
                "SYNTHETIC FIXTURE ONLY. NO REAL PERSON. NO ACTUAL CONSENT.\n",
                encoding="utf-8",
            )

    def test_changed_wav_file_digest_is_denied_without_echo(self):
        wrong=replace(self.takes[0],declared_wav_sha256="f"*64)
        with self.assertRaises(WorkflowError) as context:
            screen_oct20_owned_voice_takes((wrong,*self.takes[1:]))
        self.assertNotIn(self.root.name,str(context.exception))

    def test_mismatched_actual_42_vs_44_seconds_wav_denied(self):
        # Put a real EN 42-second WAV in HI 44-second slot.
        wrong=replace(self.takes[1],source_wav=self.takes[0].source_wav,
                      declared_wav_sha256=self.takes[0].declared_wav_sha256)
        with self.assertRaises(WorkflowError):
            screen_oct20_owned_voice_takes(
                (self.takes[0],wrong,self.takes[2]))

    def test_provisional_inspector_claiming_voice_rights_is_denied(self):
        good={
            "sha256":self.takes[0].declared_wav_sha256,
            "status":"WAV_TECHNICAL_EVIDENCE_NOT_SPEECH_APPROVAL",
            "declared_language":"en",
            "declared_narrator_id":"narrator_en_short_oct20",
            "real_speech_verified":True,
            "human_naturalness_verified":False,
            "license_rights_verified":True,
            "audio_caption_alignment_verified":False,
            "duration_seconds":42,
        }
        with patch(
            "autopilot.oct20_owned_voice_handoff.inspect_external_voice_wav",
            return_value=good,
        ):
            with self.assertRaises(WorkflowError):
                screen_oct20_owned_voice_takes(self.takes)

    def test_recording_note_export_exact_three_and_no_overwrite(self):
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)
            receipt=export_oct20_narrator_notes(folder)
            self.assertEqual(receipt["files_written"],3)
            self.assertEqual(receipt["voice_assets_created"],0)
            self.assertFalse(receipt["actual_speech_recorded"])
            self.assertFalse(receipt["youtube_publish_authorized"])
            paths=sorted(folder.glob("*.recording_notes.md"))
            self.assertEqual(len(paths),3)
            for file in paths:
                s=file.read_text(encoding="utf-8")
                self.assertIn("UNLICENSED",s)
                self.assertIn("Scene 1",s)
                self.assertIn("Independent consent",s)
            old=paths[0].read_bytes()
            with self.assertRaises(WorkflowError):
                export_oct20_narrator_notes(folder)
            self.assertEqual(paths[0].read_bytes(),old)

    def test_invalid_export_destination_refused_without_creating_folder(self):
        with TemporaryDirectory() as tmp:
            missing=Path(tmp)/"outside"
            with self.assertRaises(WorkflowError):
                export_oct20_narrator_notes(missing)
            self.assertFalse(missing.exists())


if __name__=="__main__":
    unittest.main()
