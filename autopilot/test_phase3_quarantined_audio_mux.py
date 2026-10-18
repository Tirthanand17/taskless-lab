"""Phase 3R3 real H.264+AAC mux regression, using fake audio ONLY.

Creates tiny local clips with FFmpeg; synthetic sine wave WAV never proves speech,
rights, identity, language, pronunciation or caption synchronization.
No paid provider, uploads, persistent public artifacts or external network.
"""
from pathlib import Path
import json
import math
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave

from autopilot.agent_org import WorkflowError
from autopilot.phase3_quarantined_audio_mux import (
    mux_visual_with_external_wav,
)


def tone(path: Path, *, seconds: float=.5, amplitude:float=.09) -> None:
    rate=16000
    with wave.open(str(path),"wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        data=b"".join(
            struct.pack("<h",round(amplitude*32767*
                                 math.sin(2*math.pi*220*i/rate)))
            for i in range(round(seconds*rate))
        )
        wav.writeframes(data)


def video(path:Path, *, geometry:str="360x640",with_audio:bool=False) -> None:
    cmd=["ffmpeg","-nostdin","-v","error","-y",
         "-f","lavfi","-i",f"color=c=navy:s={geometry}:r=24:d=0.5"]
    if with_audio:
        cmd+=["-f","lavfi","-i","sine=frequency=440:sample_rate=16000:duration=0.5",
              "-map","0:v:0","-map","1:a:0","-c:a","aac"]
    cmd+=["-t","0.5","-c:v","libx264","-pix_fmt","yuv420p",str(path)]
    subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,check=True,timeout=40)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Disposable runner must have installed FFmpeg/FFprobe")
class QuarantinedMuxTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.silent=self.root/"silent.mp4"
        self.voice=self.root/"synthetic_tone.wav"
        self.output=self.root/"qa_only.mp4"
        video(self.silent)
        tone(self.voice)

    def tearDown(self):
        self.tmp.cleanup()

    def mux(self, **kwargs):
        return mux_visual_with_external_wav(
            episode_id=kwargs.get("episode_id","csv_tutorial_short_en"),
            video_path=kwargs.get("video_path",self.silent),
            wav_path=kwargs.get("wav_path",self.voice),
            output_path=kwargs.get("output_path",self.output))

    def test_real_media_streams_decode_but_cannot_publish(self):
        result=self.mux()
        self.assertTrue(self.output.is_file())
        self.assertEqual(result["status"],"REAL_AV_MUX_TECHNICAL_PASS_PUBLICATION_BLOCKED")
        self.assertEqual(result["video_codec"],"h264")
        self.assertEqual(result["audio_codec"],"aac")
        self.assertEqual(len(result["output_sha256"]),64)
        self.assertFalse(result["actual_natural_speech_verified"])
        self.assertFalse(result["voice_rights_verified"])
        self.assertFalse(result["audio_caption_alignment_verified"])
        self.assertFalse(result["youtube_upload_authorized"])
        self.assertFalse(result["publishing_authorized"])
        self.assertEqual(result["network_calls"],0)
        self.assertFalse(result["external_paid_services_used"])
        probed=subprocess.run(["ffprobe","-v","error","-show_entries",
                              "stream=codec_type,codec_name","-of","json",str(self.output)],
                             capture_output=True,text=True,check=True,timeout=20)
        streams=json.loads(probed.stdout)["streams"]
        self.assertEqual({s["codec_type"] for s in streams},{"video","audio"})

    def test_two_languages_formats_technically_mux_but_not_speaker_verified(self):
        other=self.root/"landscape.mp4"
        video(other,geometry="640x360")
        result=self.mux(episode_id="csv_tutorial_long_hi",video_path=other)
        self.assertEqual((result["video_width"],result["video_height"]),(640,360))
        self.assertFalse(result["two_distinct_narrators_verified"])
        self.assertFalse(result["production_release_authorized"])

    def test_silent_tone_refused_and_no_partial_output(self):
        tone(self.voice,amplitude=0)
        with self.assertRaises(WorkflowError):
            self.mux()
        self.assertFalse(self.output.exists())

    def test_video_with_existing_audio_rejected_without_rewriting(self):
        with_audio=self.root/"has_audio.mp4"
        video(with_audio,with_audio=True)
        with self.assertRaises(WorkflowError):
            self.mux(video_path=with_audio)
        self.assertTrue(with_audio.is_file())
        self.assertFalse(self.output.exists())

    def test_wrong_geometry_for_episode(self):
        invalid=self.root/"landscape.mp4"
        video(invalid,geometry="640x360")
        with self.assertRaises(WorkflowError):
            self.mux(video_path=invalid)
        self.assertFalse(self.output.exists())

    def test_absent_and_invalid_episode_rejected(self):
        with self.assertRaises(WorkflowError):
            self.mux(episode_id="not_authorized")
        self.assertFalse(self.output.exists())

    def test_mismatched_voice_duration_rejected(self):
        tone(self.voice,seconds=3)
        with self.assertRaises(WorkflowError):
            self.mux()
        self.assertFalse(self.output.exists())

    def test_input_symlink_rejected(self):
        other=self.root/"link.mp4"
        other.symlink_to(self.silent)
        with self.assertRaises(WorkflowError):
            self.mux(video_path=other)
        self.assertFalse(self.output.exists())

    def test_preexisting_output_refused_no_overwrite(self):
        self.output.write_bytes(b"existing")
        with self.assertRaises(WorkflowError):
            self.mux()
        self.assertEqual(self.output.read_bytes(),b"existing")

    def test_bad_output_directory_not_created(self):
        path=self.root/"missing_folder"/"qa.mp4"
        with self.assertRaises(WorkflowError):
            self.mux(output_path=path)
        self.assertFalse(path.parent.exists())

    def test_unapproved_script_subtitles_remain_estimates(self):
        r=self.mux()
        self.assertTrue(r["script_subtitle_estimated"])
        self.assertFalse(r["audio_caption_alignment_verified"])
        self.assertFalse(r["independent_factual_review_verified"])
        self.assertFalse(r["real_three_video_batch_ready"])

    def test_bad_corrupted_mp4_rejected(self):
        self.silent.write_bytes(b"This is not a video")
        with self.assertRaises(WorkflowError):
            self.mux()
        self.assertFalse(self.output.exists())

if __name__=="__main__":
    unittest.main()
