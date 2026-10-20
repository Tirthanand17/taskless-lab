"""Synthetic full AAC PCM fixtures; acoustic energy is NOT recognized speech."""
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
from autopilot.cloud_cue_audio_activity import (
    RATE,WINDOW_MS,WINDOW_SAMPLES,_active_flags,inspect_cue_audio_activity,
    summarize_cue_activity,
)


def make_pcm(seconds,*,silence_between=None):
    """Exact synthetic alternating 4k amplitude (never genuine narration)."""
    waveform=array("h",[4000 if i%2 else -4000 for i in range(WINDOW_SAMPLES)])
    if sys.byteorder!="little":
        waveform.byteswap()
    frame=waveform.tobytes()
    empty=b"\x00"*len(frame)
    chunks=[]
    for i in range(seconds*1000//WINDOW_MS):
        middle=i*WINDOW_MS+WINDOW_MS//2
        chunks.append(
            empty if silence_between and silence_between[0]<=middle<silence_between[1]
            else frame
        )
    return b"".join(chunks)


class WholeCueAudioActivityTests(unittest.TestCase):
    def setUp(self):
        temporary=TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder=Path(temporary.name)
        self.file=self.folder/"fake-full-video.mp4"
        self.file.write_bytes(b"synthetic not playable video"*410)
        self.candidate,self.media,self.screen=packet("short_en")
        digest=sha256(self.file.read_bytes()).hexdigest()
        self.candidate=replace(self.candidate,media_sha256=digest)
        self.media=replace(self.media,video_sha256=digest,video_bytes=self.file.stat().st_size)
        self.screen=replace(self.screen,video_sha256=digest)

    def check(self,pcm,*,file=None,obs=None,candidate=None,audio=None):
        def fake_ffmpeg(args,**kwargs):
            self.assertEqual(args[0],"ffmpeg")
            self.assertIn("-map",args)
            self.assertEqual(args[-1],"pipe:1")
            self.assertNotIn("shell",kwargs)
            return CompletedProcess(args,0,pcm,b"")
        with patch("autopilot.cloud_cue_audio_activity.subprocess.run",
                   side_effect=fake_ffmpeg):
            return inspect_cue_audio_activity(
                self.file if file is None else file,
                self.candidate if candidate is None else candidate,
                self.media if obs is None else obs,
                self.screen if audio is None else audio,
            )

    def test_full_duration_synthetic_energy_is_technical_not_speech(self):
        before=self.file.read_bytes()
        result=self.check(make_pcm(42))
        self.assertEqual(result.activity_windows_scanned,42*1000//WINDOW_MS)
        self.assertGreater(result.cue_count,3)
        self.assertEqual(result.acoustically_sparse_cues,0)
        self.assertTrue(result.technical_cue_activity_pass)
        self.assertFalse(result.real_spoken_words_verified)
        self.assertFalse(result.language_verified)
        self.assertFalse(result.actual_subtitle_alignment_verified)
        self.assertFalse(result.commercial_rights_verified)
        self.assertFalse(result.publishing_authorized)
        self.assertEqual(before,self.file.read_bytes())

    def test_isolated_silent_cue_fails_even_when_five_global_windows_loud(self):
        cues=_draft_cues(self.candidate.episode_id)
        start,end,_=cues[len(cues)//2]
        output=self.check(make_pcm(42,silence_between=(start,end)))
        self.assertGreaterEqual(output.acoustically_sparse_cues,1)
        self.assertFalse(output.technical_cue_activity_pass)
        self.assertIn("SILENT_OR_NEAR_SILENT_SUBTITLE_CUES",output.blockers)
        self.assertFalse(output.actual_subtitle_alignment_verified)
        self.assertTrue(self.screen.technical_signal_pass)

    def test_whole_audio_silence_never_counts_as_narration(self):
        output=self.check(bytes(RATE*2*42))
        self.assertEqual(output.cue_count_with_acoustic_activity,0)
        self.assertEqual(output.acoustically_sparse_cues,output.cue_count)
        self.assertFalse(output.technical_cue_activity_pass)

    def test_short_decode_wrong_format_or_failure_refused(self):
        good=make_pcm(42)
        bad=[good[:-RATE*2],good+b"\x00"*(RATE*2),good[:-1],b""]
        for raw in bad:
            with self.subTest(size=len(raw)),self.assertRaises(WorkflowError):
                self.check(raw)
        with patch("autopilot.cloud_cue_audio_activity.subprocess.run",
                   return_value=CompletedProcess([],1,good,b"decode fail")
        ),self.assertRaises(WorkflowError):
            inspect_cue_audio_activity(
                self.file,self.candidate,self.media,self.screen
            )

    def test_unknown_sha_or_symlink_or_unsupported_approval_denied(self):
        alias=self.folder/"alias.mp4"
        alias.symlink_to(self.file)
        for file,media,candidate,screen in (
            (alias,self.media,self.candidate,self.screen),
            (Path("relative.mp4"),self.media,self.candidate,self.screen),
            (self.file,replace(self.media,video_sha256="1"*64),
             self.candidate,self.screen),
            (self.file,self.media,self.candidate,
             replace(self.screen,publishing_authorized=True)),
            (self.file,self.media,replace(self.candidate,media_sha256="2"*64),
             self.screen),
        ):
            with self.subTest(path=str(file)),self.assertRaises(WorkflowError):
                self.check(make_pcm(42),file=file,obs=media,
                           candidate=candidate,audio=screen)

    def test_file_mutation_while_audio_decodes_refused(self):
        current=self.file.read_bytes()
        def overwrite(args,**kwargs):
            self.file.write_bytes(b"X"*len(current))
            return CompletedProcess(args,0,make_pcm(42),b"")
        with patch("autopilot.cloud_cue_audio_activity.subprocess.run",
                   side_effect=overwrite),self.assertRaises(WorkflowError):
            inspect_cue_audio_activity(
                self.file,self.candidate,self.media,self.screen
            )

    def test_all_language_lanes_keep_release_gates_blocked(self):
        reports=[]
        for lane in ("short_en","short_hi","long_hi"):
            candidate,media,audio=packet(lane)
            spec=42 if lane.startswith("short_") else 432
            source=self.folder/(lane+".mp4")
            source.write_bytes((lane.encode()+b"_not_a_real_video")*450)
            digest=sha256(source.read_bytes()).hexdigest()
            candidate=replace(candidate,media_sha256=digest)
            media=replace(media,video_sha256=digest,video_bytes=source.stat().st_size)
            audio=replace(audio,video_sha256=digest)
            with patch("autopilot.cloud_cue_audio_activity.subprocess.run",
                       return_value=CompletedProcess([],0,make_pcm(spec),b"")):
                record=inspect_cue_audio_activity(source,candidate,media,audio)
            reports.append(record)
        result=summarize_cue_activity(tuple(reports))
        self.assertEqual(len(result["audited_lanes"]),3)
        self.assertFalse(result["actual_spoken_words_verified"])
        self.assertFalse(result["publishing_authorized"])
        with self.assertRaises(WorkflowError):
            summarize_cue_activity((reports[0],reports[0]))
        with self.assertRaises(WorkflowError):
            summarize_cue_activity((replace(reports[0],publishing_authorized=True),))

    def test_pcm_invalid_type_and_lengths_refused(self):
        for raw in (b"",b"\x00",bytearray(make_pcm(42)),b"\x00"*20):
            with self.assertRaises(WorkflowError):
                _active_flags(raw)


if __name__=="__main__":
    unittest.main()
