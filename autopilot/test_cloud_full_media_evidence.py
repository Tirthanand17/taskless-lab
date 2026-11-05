"""Local technical media intake; no new full-HD workload or publishing."""
from dataclasses import replace
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import shutil
import subprocess
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_capacity_admission import LANES,FPS
from autopilot.cloud_full_media_evidence import (
    TechnicalFullHDObservation,inspect_full_length_media,
    evaluate_observed_media_capacity,
)

NOW=datetime(2026,10,19,8,tzinfo=timezone.utc)


def probe(lane):
    spec=next(x for x in LANES if x.lane==lane)
    return {
        "streams":[
            {"codec_type":"video","codec_name":"h264","width":spec.width,
             "height":spec.height,"nb_read_frames":str(spec.duration_s*FPS),
             "avg_frame_rate":"24/1","r_frame_rate":"24/1"},
            {"codec_type":"audio","codec_name":"aac"},
        ],
        "format":{"duration":str(float(spec.duration_s))},
    }


def mocked_media_path():
    temporary=TemporaryDirectory()
    path=Path(temporary.name)/"fixture.mp4"
    path.write_bytes(b"synthetic bytes: NOT real MP4 media"*150)
    return temporary,path


def valid_observation(lane):
    spec=next(x for x in LANES if x.lane==lane)
    return TechnicalFullHDObservation(
        lane=lane,video_sha256=sha256(lane.encode()).hexdigest(),
        video_bytes=20000,frames_decoded_or_counted=spec.duration_s*FPS,
        width=spec.width,height=spec.height,container_duration_s=float(spec.duration_s),
        video_codec="h264",audio_codec="aac",
        whole_media_ffmpeg_decode_passed=True,
        render_wall_seconds_claimed=100,
        peak_memory_mib_claimed=1024,
        observed_at=NOW,original_file_unchanged_after_inspection=True,
    )


class ReadOnlyHDIntakeTests(unittest.TestCase):
    def test_synthetic_stub_probe_and_decode_enforce_metadata_not_authorship(self):
        tmp,path=mocked_media_path()
        self.addCleanup(tmp.cleanup)
        original=path.read_bytes()
        def mocked_run(args,**_):
            if args[0]=="ffprobe":
                return CompletedProcess(args,0,json.dumps(probe("short_en")),"")
            if args[0]=="ffmpeg":
                return CompletedProcess(args,0,"","")
            raise AssertionError("Unexpected command")
        with patch("autopilot.cloud_full_media_evidence.subprocess.run",
                   side_effect=mocked_run) as call:
            evidence=inspect_full_length_media(
                "short_en",path,claimed_render_seconds=5,
                claimed_peak_ram_mib=1024,measured_at=NOW
            )
        self.assertEqual(call.call_count,2)
        self.assertEqual(evidence.video_sha256,sha256(original).hexdigest())
        self.assertEqual(evidence.frames_decoded_or_counted,1008)
        self.assertFalse(evidence.third_party_license_authenticated)
        self.assertFalse(evidence.natural_narration_verified)
        self.assertFalse(evidence.publishing_authorized)
        self.assertEqual(path.read_bytes(),original)
        self.assertEqual(evidence.video_bytes,len(original))

    def test_mocked_video_altered_in_between_ffprobe_and_decode_rejected(self):
        tmp,path=mocked_media_path()
        self.addCleanup(tmp.cleanup)
        def changing(args,**_):
            if args[0]=="ffprobe":
                return CompletedProcess(args,0,json.dumps(probe("short_en")),"")
            path.write_bytes(b"changed synthetic file"*200)
            return CompletedProcess(args,0,"","")
        with patch("autopilot.cloud_full_media_evidence.subprocess.run",
                   side_effect=changing),self.assertRaises(WorkflowError):
            inspect_full_length_media(
                "short_en",path,claimed_render_seconds=5,
                claimed_peak_ram_mib=100,measured_at=NOW,
            )

    def test_short_wrong_size_frames_codecs_audio_duration_and_fps_rejected(self):
        tmp,path=mocked_media_path()
        self.addCleanup(tmp.cleanup)
        variations=[
            lambda d: d["streams"][0].update(width=160),
            lambda d: d["streams"][0].update(nb_read_frames="24"),
            lambda d: d["streams"][0].update(codec_name="mpeg4"),
            lambda d: d["streams"][0].update(avg_frame_rate="23/1"),
            lambda d: d["streams"][0].update(r_frame_rate="24000/1001"),
            lambda d: d["streams"][1].update(codec_name="mp3"),
            lambda d: d["format"].update(duration="1"),
            lambda d: d["streams"].append(dict(d["streams"][1])),
        ]
        for i,change in enumerate(variations):
            with self.subTest(case=i):
                meta=probe("short_en")
                change(meta)
                with patch("autopilot.cloud_full_media_evidence.subprocess.run",
                    return_value=CompletedProcess([] ,0,json.dumps(meta),"")
                ),self.assertRaises(WorkflowError):
                    inspect_full_length_media(
                        "short_en",path,claimed_render_seconds=5,
                        claimed_peak_ram_mib=100,measured_at=NOW,
                    )

    def test_decode_nonzero_or_error_text_refused(self):
        tmp,path=mocked_media_path()
        self.addCleanup(tmp.cleanup)
        for code,stderr in ((1,"decode failed"),(0,"corrupt audio frame")):
            def run(args,**_):
                if args[0]=="ffprobe":
                    return CompletedProcess(args,0,json.dumps(probe("short_en")),"")
                return CompletedProcess(args,code,"",stderr)
            with self.subTest(code=code,stderr=stderr),patch(
                "autopilot.cloud_full_media_evidence.subprocess.run",
                side_effect=run,
            ),self.assertRaises(WorkflowError):
                inspect_full_length_media(
                    "short_en",path,claimed_render_seconds=5,
                    claimed_peak_ram_mib=100,measured_at=NOW,
                )

    def test_no_symlink_missing_relative_paths_or_resource_input_laundering(self):
        tmp,path=mocked_media_path()
        self.addCleanup(tmp.cleanup)
        link=path.parent/"alias.mp4"
        link.symlink_to(path)
        for candidate in (link,path.parent/"absent.mp4",Path("relative.mp4")):
            with self.subTest(file=str(candidate)),self.assertRaises(WorkflowError):
                inspect_full_length_media(
                    "short_en",candidate,claimed_render_seconds=5,
                    claimed_peak_ram_mib=100,measured_at=NOW,
                )
        for wall,memory in ((0,100),(float("inf"),100),(2,True),
                            (10,-3),(True,100)):
            with self.subTest(wall=wall,memory=memory),self.assertRaises(WorkflowError):
                inspect_full_length_media(
                    "short_en",path,claimed_render_seconds=wall,
                    claimed_peak_ram_mib=memory,measured_at=NOW,
                )

    def test_real_one_second_low_resolution_ffmpeg_clip_cannot_qualify(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("No FFmpeg binaries installed in local CI")
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"one-second-AV.mkv"
            result=subprocess.run([
                "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
                "-f","lavfi","-i","color=c=black:s=160x90:r=24",
                "-f","lavfi","-i","anullsrc=r=48000:cl=mono",
                "-t","1","-c:v","mpeg4","-q:v","5",
                "-c:a","aac",str(path),
            ],capture_output=True,timeout=25)
            self.assertEqual(result.returncode,0,result.stderr[:500])
            self.assertGreater(path.stat().st_size,2048)
            with self.assertRaises(WorkflowError):
                inspect_full_length_media(
                    "short_en",path,claimed_render_seconds=1,
                    claimed_peak_ram_mib=100,measured_at=NOW,
                )

    def test_mocked_complete_artifacts_never_remove_rights_veto(self):
        obs=tuple(valid_observation(x.lane) for x in LANES)
        outcome=evaluate_observed_media_capacity(obs,None,now=NOW)
        self.assertEqual(len(outcome["technical_video_sha256_by_lane"]),3)
        self.assertIn("PROVIDER_ZERO_OVERAGE_CONTRACT_MISSING",
                      outcome["blocking_reasons"])
        for lane in LANES:
            self.assertIn(
                lane.lane+":NARRATION_CAPTION_RIGHTS_NOT_VERIFIED",
                outcome["blocking_reasons"]
            )
        self.assertFalse(outcome["publishing_authorized"])
        self.assertFalse(outcome["signed_media_editorial_reviews_present"])
        self.assertTrue(outcome[
            "operator_render_time_and_ram_not_independently_attested"
        ])

    def test_falsely_approved_observation_or_checksum_or_mismatched_lane_rejected(self):
        original=valid_observation("short_en")
        for altered in (
            replace(original,publishing_authorized=True),
            replace(original,third_party_license_authenticated=True),
            replace(original,signed_by_independent_reviewer=True),
            replace(original,video_sha256="bad"),
            replace(original,frames_decoded_or_counted=24),
            replace(original,lane="long_hi"),
            replace(original,whole_media_ffmpeg_decode_passed=False),
        ):
            with self.subTest(altered=altered),self.assertRaises(WorkflowError):
                evaluate_observed_media_capacity((altered,),None,now=NOW)
        with self.assertRaises(WorkflowError):
            evaluate_observed_media_capacity((original,original),None,now=NOW)


if __name__=="__main__":
    unittest.main()
