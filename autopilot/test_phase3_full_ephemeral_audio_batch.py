"""FFmpeg full-episode ephemeral mux safety tests; all media/mock bytes FAKE.

Mock mux subprocesses and untrusted WAV receipts do NOT demonstrate genuine
licensed voices, full episode renders, correct captions or external approvals.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import json
import subprocess
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase3_visual_signal_audit import EPISODES
from autopilot.phase3_full_ephemeral_audio_batch import (
    _probe_exact_muxed, render_ephemeral_quarantined_audio_batch,
)

class RealMuxProbeTest(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file=Path(self.temp.name)/"fake_output.mp4"
        self.file.write_bytes(b"NOT_REAL_AV_OUTPUT"*300)

    def fake_probe(self, command, **kwargs):
        ep="csv_tutorial_short_en"
        duration,w,h,fps,frames=EPISODES[ep]
        data={
            "streams":[
                {"codec_type":"video","codec_name":"h264",
                 "width":w,"height":h,"nb_frames":str(frames),
                 "avg_frame_rate":"24/1"},
                {"codec_type":"audio","codec_name":"aac","sample_rate":"48000"},
            ],
            "format":{"duration":str(duration)},
        }
        return SimpleNamespace(stdout=json.dumps(data),returncode=0)

    def test_strict_two_codec_exact_native_hd_metadata_accepts_mock(self):
        with patch("autopilot.phase3_full_ephemeral_audio_batch.subprocess.run",
                   side_effect=self.fake_probe):
            result=_probe_exact_muxed(self.file,"csv_tutorial_short_en")
        self.assertEqual(result["video_frames"],1008)
        self.assertEqual(result["audio_codec"],"aac")

    def test_bad_video_and_bad_audio_streams_fail_closed(self):
        for field,value in (("codec_name","opus"),("sample_rate","44100")):
            def bad_probe(command,**kwargs):
                q=self.fake_probe(command,**kwargs)
                data=json.loads(q.stdout)
                if field=="codec_name":
                    data["streams"][1]["codec_name"]=value
                else:
                    data["streams"][1]["sample_rate"]=value
                return SimpleNamespace(stdout=json.dumps(data))
            with self.subTest(field=field),patch(
                "autopilot.phase3_full_ephemeral_audio_batch.subprocess.run",
                side_effect=bad_probe),self.assertRaises(WorkflowError):
                _probe_exact_muxed(self.file,"csv_tutorial_short_en")

    def test_unknown_episode_rejected(self):
        with self.assertRaises(WorkflowError):
            _probe_exact_muxed(self.file,"unknown")

    def test_symlink_and_missing_output_rejected(self):
        alias=self.file.parent/"alias.mp4"
        alias.symlink_to(self.file)
        for f in (alias,self.file.parent/"absent.mp4"):
            with self.assertRaises(WorkflowError):
                _probe_exact_muxed(f,"csv_tutorial_short_en")


class EphemeralFullBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.items=[]
        self.handoff=[]
        self.produced=[]
        self.decode_count=0
        for ep in sorted(EPISODES):
            duration=EPISODES[ep][0]
            wav_sha=sha256(("MOCK_WAV_"+ep).encode()).hexdigest()
            vid_sha=sha256(("MOCK_VIDEO_"+ep).encode()).hexdigest()
            srt_sha=sha256(("MOCK_SRT_"+ep).encode()).hexdigest()
            take=SimpleNamespace(
                wav_path=self.root/(ep+".wav"),wav_sha256=wav_sha,
                declared_narrator_id="narrator_fake",declared_language="hi")
            v={"video_sha256":vid_sha}
            self.items.append(SimpleNamespace(
                episode_id=ep,silent_video_path=self.root/(ep+".mp4"),
                narration_take=take,video_receipt=v,
                future_mux_path=self.root/(ep+".future-mux.mp4")))
            self.handoff.append({
                "episode_id":ep,"duration_seconds_expected":duration,
                "wav_sha256":wav_sha,"silent_video_sha256":vid_sha,
                "candidate_srt_sha256":srt_sha,
                "mux_permitted":False,"publishing_authorized":False,
            })

    def fake_handoff(self,entries):
        return {
            "status":"THREE_VIDEO_TECHNICAL_HANDOFF_ONLY_RELEASE_BLOCKED",
            "youtube_upload_or_publishing_authorized":False,
            "final_mux_generated":False,
            "episodes":self.handoff,
        }

    def fake_wav(self,item,duration):
        return {"duration_seconds":duration}

    def fake_probe(self,path,episode):
        duration,w,h,fps,frames=EPISODES[episode]
        return {"duration_seconds":duration,
                "video_width":w,"video_height":h,
                "video_frames":frames,"video_frame_rate":fps,
                "video_codec":"h264","audio_codec":"aac",
                "audio_sample_rate_hz":48000}

    def fake_process(self,cmd,**kwargs):
        if "ffmpeg"!=cmd[0]:
            raise AssertionError("Only already-installed local FFmpeg permitted")
        output=Path(cmd[-1])
        if output.suffix==".mp4":
            self.produced.append(output)
            output.write_bytes(b"MOCK_MP4_BODY_NOT_REAL_AV")
        else:
            self.decode_count+=1
        return SimpleNamespace(returncode=0)

    def run_batch(self, *, process=None, handoff=None,wav=None,probe=None):
        with (patch("autopilot.phase3_full_ephemeral_audio_batch.prepare_three_video_technical_handoff",
                    side_effect=handoff or self.fake_handoff),
              patch("autopilot.phase3_full_ephemeral_audio_batch._inspect_input_wav",
                    side_effect=wav or self.fake_wav),
              patch("autopilot.phase3_full_ephemeral_audio_batch._probe_exact_muxed",
                    side_effect=probe or self.fake_probe),
              patch("autopilot.phase3_full_ephemeral_audio_batch.subprocess.run",
                    side_effect=process or self.fake_process),
              patch("autopilot.phase3_full_ephemeral_audio_batch.shutil.which",
                    return_value="/usr/bin/ffmpeg"),
              patch("autopilot.phase3_full_ephemeral_audio_batch.shutil.disk_usage",
                    return_value=SimpleNamespace(free=3_000_000_000))):
            return render_ephemeral_quarantined_audio_batch(self.items,
                                                           scratch_dir=self.root)

    def test_three_quarantined_outputs_are_deletable_and_never_published(self):
        report=self.run_batch()
        self.assertEqual(len(self.produced),3)
        self.assertEqual(self.decode_count,3)
        self.assertEqual(report["number_of_ephemeral_outputs_verified"],3)
        self.assertFalse(report["temporary_video_files_retainable"])
        self.assertFalse(report["any_media_persisted_after_run"])
        self.assertFalse(report["upload_schedule_or_publishing_authorized"])
        self.assertEqual(len(report["episodes"]),3)
        for r in report["episodes"]:
            self.assertFalse(r["real_natural_narration_verified"])
            self.assertFalse(r["caption_alignment_verified"])
            self.assertFalse(r["final_caption_track_muxed"])
        self.assertFalse(any(p.exists() for p in self.produced))
        self.assertEqual(list(self.root.iterdir()),[])

    def test_interrupted_second_mux_purges_even_first_media(self):
        def failing(cmd,**kwargs):
            if len(self.produced)>=1 and str(cmd[-1]).endswith(".mp4"):
                return SimpleNamespace(returncode=1)
            return self.fake_process(cmd,**kwargs)
        with self.assertRaises(WorkflowError):
            self.run_batch(process=failing)
        self.assertFalse(any(p.exists() for p in self.produced))
        self.assertEqual(list(self.root.iterdir()),[])

    def test_incomplete_wav_audio_cannot_be_padded(self):
        def too_short(item,duration):
            return {"duration_seconds":duration-1}
        with self.assertRaisesRegex(WorkflowError,"trim or pad"):
            self.run_batch(wav=too_short)
        self.assertEqual(self.produced,[])

    def test_fake_production_authorization_fails_before_creating_any_media(self):
        def forgery(entries):
            return dict(self.fake_handoff(entries),
                        youtube_upload_or_publishing_authorized=True)
        with self.assertRaises(WorkflowError):
            self.run_batch(handoff=forgery)
        self.assertEqual(self.produced,[])

    def test_false_stage_mux_allowed_rejected(self):
        old=self.handoff
        self.handoff=[dict(x,mux_permitted=True) if i==0 else x
                      for i,x in enumerate(old)]
        try:
            with self.assertRaises(WorkflowError):
                self.run_batch()
        finally:
            self.handoff=old

    def test_source_paths_are_not_written_as_future_artifacts(self):
        result=self.run_batch()
        self.assertEqual(result["network_calls"],0)
        for item in self.items:
            self.assertFalse(item.future_mux_path.exists())

    def test_explicit_scratch_directory_must_preexist(self):
        with self.assertRaises(WorkflowError):
            render_ephemeral_quarantined_audio_batch(self.items,
                scratch_dir=self.root/"no-such-subdir")


if __name__=="__main__":
    unittest.main()
