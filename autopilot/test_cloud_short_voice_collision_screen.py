"""Synthetic duplicate short soundtrack detection, never speaker recognition."""
from array import array
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.test_cloud_transcript_alignment_intake import packet
from autopilot.cloud_transcript_alignment_intake import _draft_cues
from autopilot.cloud_signed_transcript_reviews import transcript_digest
from autopilot.cloud_cue_audio_activity import CueAcousticCoverage,RATE
from autopilot.cloud_short_voice_collision_screen import (
    _sign_bits,ShortAudioFingerprint,compare_short_audio_fingerprints,
    inspect_short_audio_fingerprint,
)


def fake_pcm(*,seed=7,amplitude=4000,seconds=42):
    """Pseudo-random synthetic PCM: deliberately NOT voice-like evidence."""
    a=array("h")
    for i in range(seconds*RATE):
        seed=(1103515245*seed+12345)&0x7fffffff
        a.append(amplitude if seed&0x400 else -amplitude)
    if sys.byteorder!="little":
        a.byteswap()
    return a.tobytes()


def scale_pcm(raw,number):
    samples=array("h")
    samples.frombytes(raw)
    if sys.byteorder!="little":
        samples.byteswap()
    scaled=array("h",(int(value*number) for value in samples))
    if sys.byteorder!="little":
        scaled.byteswap()
    return scaled.tobytes()


class ShortAudioCollisionTests(unittest.TestCase):
    def setUp(self):
        td=TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root=Path(td.name)
        self.inputs={}
        for lane in ("short_en","short_hi"):
            file=root/(lane+".mp4")
            file.write_bytes((lane.encode()+b"__fake_mp4__")*600)
            digest=sha256(file.read_bytes()).hexdigest()
            candidate,media,screen=packet(lane)
            candidate=replace(candidate,media_sha256=digest)
            media=replace(media,video_sha256=digest,video_bytes=file.stat().st_size)
            screen=replace(screen,video_sha256=digest)
            cue=CueAcousticCoverage(
                lane=lane,media_sha256=digest,
                candidate_transcript_sha256=transcript_digest(candidate),
                authored_srt_sha256=candidate.authored_draft_srt_sha256,
                cue_count=len(_draft_cues(candidate.episode_id)),
                activity_windows_scanned=210,
                cue_count_with_acoustic_activity=len(_draft_cues(candidate.episode_id)),
                acoustically_sparse_cues=0,lowest_cue_active_percent=100,
                entire_audio_decoded=True,technical_cue_activity_pass=True,
                blockers=(),
            )
            self.inputs[lane]=(file,candidate,media,screen,cue)

    def inspect(self,lane,pcm,*,video=None,candidate=None,media=None,
                screen=None,cue=None):
        file,default_candidate,default_media,default_screen,default_cue=self.inputs[lane]
        def decode(command,**kwargs):
            self.assertEqual(command[0],"ffmpeg")
            self.assertEqual(command[-1],"pipe:1")
            self.assertNotIn("shell",kwargs)
            return CompletedProcess(command,0,pcm,b"")
        with patch("autopilot.cloud_short_voice_collision_screen.subprocess.run",
                   side_effect=decode):
            return inspect_short_audio_fingerprint(
                file if video is None else video,
                default_candidate if candidate is None else candidate,
                default_media if media is None else media,
                default_screen if screen is None else screen,
                default_cue if cue is None else cue,
            )

    def test_different_synthetic_pcm_not_marked_duplicate_or_narrator_proven(self):
        en=self.inspect("short_en",fake_pcm(seed=17))
        hi=self.inspect("short_hi",fake_pcm(seed=21))
        report=compare_short_audio_fingerprints((hi,en))
        self.assertTrue(report["technical_collision_not_detected"])
        self.assertTrue(report["declared_narrator_plans_differ"])
        self.assertFalse(report["two_audibly_distinct_natural_speakers_verified"])
        self.assertFalse(report["correct_spoken_languages_verified"])
        self.assertFalse(report["commercial_rights_independently_verified"])
        self.assertFalse(report["upload_authorized"])
        self.assertNotIn("media_sha256",report)
        self.assertNotIn("pcm_sha256",report)

    def test_exact_same_audio_different_container_mp4_is_detected(self):
        pcm=fake_pcm(seed=99)
        en=self.inspect("short_en",pcm)
        hi=self.inspect("short_hi",pcm)
        result=compare_short_audio_fingerprints((en,hi))
        self.assertIn("IDENTICAL_FINAL_SHORT_AUDIO_TRACK",
                      result["audio_collision_blockers"])
        self.assertFalse(result["technical_collision_not_detected"])

    def test_gain_change_and_polarity_flip_cannot_fake_distinct_short_sound(self):
        pcm=fake_pcm(seed=89)
        en=self.inspect("short_en",pcm)
        for gain in (0.4,-0.5):
            with self.subTest(gain=gain):
                hi=self.inspect("short_hi",scale_pcm(pcm,gain))
                result=compare_short_audio_fingerprints((en,hi))
                self.assertIn("NEAR_IDENTICAL_SHORT_PCM_SIGN_PATTERN",
                              result["audio_collision_blockers"])
                self.assertFalse(result["two_audibly_distinct_natural_speakers_verified"])

    def test_forged_claims_wrong_lane_duplicate_or_missing_record_denied(self):
        en=self.inspect("short_en",fake_pcm(seed=12))
        hi=self.inspect("short_hi",fake_pcm(seed=13))
        for records in (
            (en,),(en,en),(hi,hi),
            (en,replace(hi,publishing_authorized=True)),
            (replace(en,distinct_narrator_identity_verified=True),hi),
            (replace(en,narrator_plan_id="narrator_forged"),hi),
            (replace(en,pcm_sha256="z"*64),hi),
            (replace(en,_signs=b"bad"),hi),
        ):
            with self.subTest(count=len(records)),self.assertRaises(WorkflowError):
                compare_short_audio_fingerprints(records)

    def test_invalid_or_falsely_cleared_cue_report_blocks_pcm(self):
        file,candidate,media,screen,cue=self.inputs["short_en"]
        for bad in (
            replace(cue,technical_cue_activity_pass=False),
            replace(cue,media_sha256="0"*64),
            replace(cue,actual_subtitle_alignment_verified=True),
            replace(cue,cue_count=cue.cue_count+1),
            replace(cue,acoustically_sparse_cues=1,blockers=("MISSING_CUE",)),
        ):
            with self.subTest(candidate=bad.blockers),self.assertRaises(WorkflowError):
                self.inspect("short_en",fake_pcm(),cue=bad)

    def test_bad_source_symlink_wrong_video_hash_and_mutated_file_denied(self):
        file,candidate,media,screen,cue=self.inputs["short_hi"]
        link=file.parent/"link.mp4"
        link.symlink_to(file)
        for p,record in ((link,media),(Path("relative.mp4"),media),
                         (file,replace(media,video_sha256="9"*64))):
            with self.subTest(path=str(p)),self.assertRaises(WorkflowError):
                self.inspect("short_hi",fake_pcm(),video=p,media=record)
        original=file.read_bytes()
        def overwrite(command,**kwargs):
            file.write_bytes(b"X"*len(original))
            return CompletedProcess(command,0,fake_pcm(),b"")
        with patch("autopilot.cloud_short_voice_collision_screen.subprocess.run",
                   side_effect=overwrite),self.assertRaises(WorkflowError):
            inspect_short_audio_fingerprint(
                file,candidate,media,screen,cue
            )

    def test_truncated_oversized_or_corrupt_pcm_denied(self):
        full=fake_pcm(seed=47)
        for pcm in (full[:-30000],full+b"\x00"*30000,full[:-1],b""):
            with self.subTest(byte_count=len(pcm)),self.assertRaises(WorkflowError):
                self.inspect("short_en",pcm)
        with patch("autopilot.cloud_short_voice_collision_screen.subprocess.run",
                   return_value=CompletedProcess([],1,full,b"failure")
        ),self.assertRaises(WorkflowError):
            f,c,m,s,r=self.inputs["short_en"]
            inspect_short_audio_fingerprint(f,c,m,s,r)

    def test_fingerprints_are_private_in_process_and_not_media_permission(self):
        en=self.inspect("short_en",fake_pcm(seed=42))
        self.assertNotIn("_signs",repr(en))
        self.assertFalse(en.distinct_narrator_identity_verified)
        self.assertFalse(en.real_speech_verified)
        self.assertFalse(en.publishing_authorized)
        self.assertFalse(en.upload_authorized)
        self.assertIsInstance(en._signs,bytes)
        self.assertGreater(len(en._signs),1000)
        for x in (b"",b"\x00",bytearray(fake_pcm()),b"\x00"*400):
            with self.assertRaises(WorkflowError):
                _sign_bits(x)


if __name__=="__main__":
    unittest.main()
