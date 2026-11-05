"""No-network tests: dummy MP4 bytes + mocked PCM DO NOT prove real speech."""
from array import array
from dataclasses import replace
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from unittest.mock import patch
import math
import sys
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_capacity_admission import FPS,LANES
from autopilot.cloud_full_media_evidence import TechnicalFullHDObservation
from autopilot.cloud_muxed_audio_screen import (
    N,POSITIONS,MuxedAudioScreen,_signal,inspect_muxed_audio,summarize_muxed_audio,
)

NOW=datetime(2026,10,19,9,tzinfo=timezone.utc)


def raw(kind):
    if kind=="noise":
        seed=1
        a=[]
        for _ in range(N):
            seed=(1103515245*seed+12345)&0x7fffffff
            a.append((seed%14000)-7000)
    elif kind=="tone":
        a=[int(9000*math.sin(2*math.pi*440*i/16000)) for i in range(N)]
    elif kind=="silence":
        a=[0]*N
    elif kind=="clip":
        a=[32767 if i%2 else -32768 for i in range(N)]
    elif kind=="dc":
        a=[11000]*N
    else:
        raise ValueError(kind)
    pcm=array("h",a)
    if sys.byteorder!="little":
        pcm.byteswap()
    return pcm.tobytes()


def fixture():
    temp=TemporaryDirectory()
    file=Path(temp.name)/"mock-media.mp4"
    file.write_bytes(b"not actual audio or video"*350)
    return temp,file


def video(lane="short_en",digest="a"*64,n=7500):
    spec=next(x for x in LANES if x.lane==lane)
    return TechnicalFullHDObservation(
        lane,digest,n,spec.duration_s*FPS,spec.width,spec.height,
        float(spec.duration_s),"h264","aac",True,15.0,900,NOW,True,
    )


def decodes(kind):
    def run(cmd,**_):
        if cmd[0]!="ffmpeg" or cmd[-1]!="pipe:1":
            raise AssertionError("Unrecognized decoder")
        return CompletedProcess(cmd,0,raw(kind),b"")
    return run


def good_screen(lane="short_en"):
    return MuxedAudioScreen(
        lane,"a"*64,5,5,0,0,0,True,(),
    )


class MuxedAACScreenTests(unittest.TestCase):
    def test_dummy_noise_can_pass_signal_but_not_voice_rights_or_release(self):
        temp,file=fixture();self.addCleanup(temp.cleanup)
        unchanged=file.read_bytes()
        obs=video(digest=sha256(unchanged).hexdigest(),n=len(unchanged))
        with patch("autopilot.cloud_muxed_audio_screen.subprocess.run",
                   side_effect=decodes("noise")) as mock:
            report=inspect_muxed_audio(file,obs)
        self.assertEqual(mock.call_count,len(POSITIONS))
        self.assertTrue(report.technical_signal_pass)
        self.assertFalse(report.actual_speech_recognized)
        self.assertFalse(report.intended_language_verified)
        self.assertFalse(report.distinct_short_narrators_verified)
        self.assertFalse(report.publishing_authorized)
        self.assertEqual(file.read_bytes(),unchanged)

    def test_silence_tone_clipping_and_dc_are_all_rejected(self):
        temp,file=fixture();self.addCleanup(temp.cleanup)
        obs=video(digest=sha256(file.read_bytes()).hexdigest(),
                  n=file.stat().st_size)
        for kind,key in (
            ("silence","MUXED_AUDIO_MOSTLY_SILENT"),
            ("tone","MUXED_AUDIO_PURE_TONE_PLACEHOLDER"),
            ("clip","MUXED_AUDIO_CLIPPING"),
            ("dc","MUXED_AUDIO_DC_OFFSET"),
        ):
            with self.subTest(kind=kind),patch(
                "autopilot.cloud_muxed_audio_screen.subprocess.run",
                side_effect=decodes(kind)
            ):
                result=inspect_muxed_audio(file,obs)
                self.assertFalse(result.technical_signal_pass)
                self.assertIn(key,result.blockers)

    def test_short_decode_missing_audio_and_stderr_fail_closed(self):
        temp,file=fixture();self.addCleanup(temp.cleanup)
        obs=video(digest=sha256(file.read_bytes()).hexdigest(),
                  n=file.stat().st_size)
        for bad in (
            CompletedProcess([],0,b"short",b""),
            CompletedProcess([],1,raw("noise"),b""),
            CompletedProcess([],0,raw("noise"),b"decoder warning"),
        ):
            with self.subTest(code=bad.returncode),patch(
                "autopilot.cloud_muxed_audio_screen.subprocess.run",
                return_value=bad
            ),self.assertRaises(WorkflowError):
                inspect_muxed_audio(file,obs)

    def test_file_change_between_audio_samples_fails_checksum(self):
        temp,file=fixture();self.addCleanup(temp.cleanup)
        obs=video(digest=sha256(file.read_bytes()).hexdigest(),
                  n=file.stat().st_size)
        calls=[0]
        def mutator(cmd,**_):
            calls[0]+=1
            if calls[0]==3:
                file.write_bytes(b"Z"*file.stat().st_size)
            return CompletedProcess(cmd,0,raw("noise"),b"")
        with patch("autopilot.cloud_muxed_audio_screen.subprocess.run",
                   side_effect=mutator),self.assertRaises(WorkflowError):
            inspect_muxed_audio(file,obs)

    def test_bad_relative_path_symlink_sha_frames_and_false_review_denied(self):
        temp,file=fixture();self.addCleanup(temp.cleanup)
        link=file.parent/"alias.mp4";link.symlink_to(file)
        obs=video(digest=sha256(file.read_bytes()).hexdigest(),
                  n=file.stat().st_size)
        for candidate,record in (
            (link,obs),(Path("relative.mp4"),obs),
            (file,replace(obs,video_sha256="0"*64)),
            (file,replace(obs,frames_decoded_or_counted=10)),
            (file,replace(obs,publishing_authorized=True)),
        ):
            with self.subTest(candidate=str(candidate)),self.assertRaises(WorkflowError):
                inspect_muxed_audio(candidate,record)

    def test_noise_features_not_speech_and_malformed_pcm_fails(self):
        features=_signal(raw("noise"))
        self.assertGreater(features[0],.003)
        self.assertLess(features[1],.045)
        self.assertLess(features[2],.14)
        self.assertLess(features[3],.92)
        for bad in (b"",b"short",bytearray(raw("noise"))):
            with self.assertRaises(WorkflowError):
                _signal(bad)

    def test_three_lanes_signals_still_do_not_clear_language_or_rights(self):
        source=tuple(video(x.lane) for x in LANES)
        samples=tuple(good_screen(x.lane) for x in LANES)
        report=summarize_muxed_audio(source,samples)
        self.assertEqual(len(report["inspected_lanes"]),3)
        self.assertEqual(len(report["blockers"]),3)
        self.assertFalse(report["two_distinct_short_speakers_verified"])
        self.assertFalse(report["speech_aligned_subtitles_verified"])
        self.assertFalse(report["commercial_voice_and_media_rights_verified"])
        self.assertFalse(report["publishing_authorized"])

    def test_reused_mismatched_or_falsely_approved_signal_rejected(self):
        source=tuple(video(x.lane) for x in LANES)
        for bad in (
            (good_screen(),good_screen()),
            (replace(good_screen(),video_sha256="b"*64),),
            (replace(good_screen(),spoken_caption_alignment_verified=True),),
        ):
            with self.subTest(count=len(bad)),self.assertRaises(WorkflowError):
                summarize_muxed_audio(source,bad)
        partial=summarize_muxed_audio(source,(good_screen(),))
        self.assertIn("long_hi:MUXED_AAC_NOT_INSPECTED",partial["blockers"])

    def test_no_files_written(self):
        temp,file=fixture();self.addCleanup(temp.cleanup)
        obs=video(digest=sha256(file.read_bytes()).hexdigest(),n=file.stat().st_size)
        with patch("autopilot.cloud_muxed_audio_screen.subprocess.run",
                   side_effect=decodes("noise")):
            inspect_muxed_audio(file,obs)
        self.assertEqual(list(file.parent.iterdir()),[file])


if __name__=="__main__":
    unittest.main()
