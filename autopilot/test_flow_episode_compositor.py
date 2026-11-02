"""FFmpeg-backed tests for FlowMinute's real-media draft compositor.

Generated color/sine clips test assembly mechanics only; no public video or AI
clip is misrepresented as produced. All files remain in temp test directories.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from autopilot.flow_episode_compositor import AssemblyError, assemble, validate_manifest


class FlowEpisodeCompositorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise unittest.SkipTest("FFmpeg required")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)

        def make(name: str, dimensions: str, color: str):
            target = cls.root / name
            args = [
                "ffmpeg","-hide_banner","-nostdin","-loglevel","error",
                "-f","lavfi","-i",f"color=c={color}:s={dimensions}:r=24",
                "-f","lavfi","-i","sine=frequency=420:sample_rate=32000",
                "-t","2.2","-c:v","libx264","-preset","ultrafast",
                "-threads","1","-pix_fmt","yuv420p","-c:a","aac",
                "-shortest","-y",str(target)
            ]
            result = subprocess.run(args,capture_output=True,text=True,timeout=50)
            if result.returncode:
                raise RuntimeError(result.stderr[-1000:])
            return target
        cls.first = make("scene_one.mp4","360x640","blue")
        cls.second = make("scene_two.mp4","360x640","green")
        cls.landscape = make("landscape.mp4","640x360","yellow")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "tmp"):
            cls.tmp.cleanup()

    def setup_manifest(self):
        return {
            "schema_version":1,
            "episode_id":"fm_20261024_short_en",
            "segments":[
                {"id":"first_scene","path":str(self.first),
                 "sha256":sha256(self.first.read_bytes()).hexdigest(),
                 "source_start_ms":0,"duration_ms":1500},
                {"id":"second_scene","path":str(self.second),
                 "sha256":sha256(self.second.read_bytes()).hexdigest(),
                 "source_start_ms":0,"duration_ms":1500},
            ]
        }

    def test_partial_preview_requires_explicit_test_mode(self):
        with self.assertRaisesRegex(AssemblyError,"Incomplete timeline"):
            validate_manifest(self.setup_manifest())

    def test_partial_draft_plan_tells_how_much_is_missing(self):
        check=validate_manifest(self.setup_manifest(),test_mode=True)
        self.assertEqual(check["assembled_ms"],3000)
        self.assertEqual(check["missing_ms"],45000)
        self.assertFalse(check["release_authorized"])

    def test_physical_mp4_joins_and_decodes(self):
        output=self.root/"review_draft.mp4"
        info=assemble(self.setup_manifest(),output,test_mode=True)
        self.assertTrue(output.is_file())
        self.assertEqual(info["status"],"PARTIAL_TEST_DRAFT_ONLY")
        self.assertEqual(info["dimensions"],[720,1280])
        self.assertEqual(info["segments"],2)
        self.assertLess(abs(info["verified_duration_seconds"]-3),.35)
        self.assertFalse(info["publishing_authorized"])
        self.assertFalse(info["natural_voice_verified"])
        self.assertEqual(info["output_sha256"],sha256(output.read_bytes()).hexdigest())

    def test_no_overwrite_on_repeat(self):
        file=self.root/"repeat_protection.mp4"
        file.write_bytes(b"original")
        with self.assertRaisesRegex(AssemblyError,"Output must"):
            assemble(self.setup_manifest(),file,test_mode=True)
        self.assertEqual(file.read_bytes(),b"original")

    def test_wrong_checksum_rejected(self):
        plan=self.setup_manifest()
        plan["segments"][0]["sha256"]="0"*64
        with self.assertRaisesRegex(AssemblyError,"checksum changed"):
            validate_manifest(plan,test_mode=True)

    def test_landscape_clip_rejected(self):
        plan=self.setup_manifest()
        plan["segments"][0]["path"]=str(self.landscape)
        plan["segments"][0]["sha256"]=sha256(self.landscape.read_bytes()).hexdigest()
        with self.assertRaisesRegex(AssemblyError,"aspect ratio"):
            validate_manifest(plan,test_mode=True)

    def test_duplicate_segment_name_rejected(self):
        plan=self.setup_manifest()
        plan["segments"][1]["id"]="first_scene"
        with self.assertRaisesRegex(AssemblyError,"duplicated"):
            validate_manifest(plan,test_mode=True)

    def test_overshoot_rejected_without_false_trimming(self):
        plan=self.setup_manifest()
        plan["segments"][1]["source_start_ms"]=2000
        with self.assertRaisesRegex(AssemblyError,"exceeds actual"):
            validate_manifest(plan,test_mode=True)

    def test_missing_scene_file_rejected(self):
        plan=self.setup_manifest()
        plan["segments"][0]["path"]=str(self.root/"no_such_clip.mp4")
        with self.assertRaisesRegex(AssemblyError,"Missing, symlinked"):
            validate_manifest(plan,test_mode=True)

    def test_wrong_episode_id_rejected(self):
        plan=self.setup_manifest()
        plan["episode_id"]="other_video"
        with self.assertRaisesRegex(AssemblyError,"Unsupported episode"):
            validate_manifest(plan,test_mode=True)

    def test_false_approval_field_does_not_grant_permission(self):
        plan=self.setup_manifest()
        plan["release_authorized"]=True
        result=validate_manifest(plan,test_mode=True)
        self.assertFalse(result["release_authorized"])

    def test_reject_symlink_source(self):
        link=self.root/"symlink_scene.mp4"
        try:
            link.symlink_to(self.first)
        except OSError:
            self.skipTest("Symlinks unavailable")
        plan=self.setup_manifest()
        plan["segments"][0]["path"]=str(link)
        with self.assertRaisesRegex(AssemblyError,"symlinked"):
            validate_manifest(plan,test_mode=True)


if __name__=="__main__":
    unittest.main()
