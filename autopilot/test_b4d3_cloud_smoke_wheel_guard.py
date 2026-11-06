"""B4d3 enforce no apt mirror waits, retain actual FFmpeg media decoding smoke."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/flowminute-cloud-render-smoke.yml"


class MediaSmokeDependenciesAreBounded(unittest.TestCase):
    def setUp(self):
        self.workflow=WORKFLOW.read_text(encoding="utf8")

    def test_pinned_public_ffmpeg_wheel_not_unbounded_ubuntu_apt(self):
        self.assertIn("'imageio-ffmpeg==0.6.0'",self.workflow)
        self.assertIn("--only-binary=:all:",self.workflow)
        self.assertIn("imageio_ffmpeg.get_ffmpeg_exe()",self.workflow)
        self.assertNotIn("sudo apt-get",self.workflow)
        self.assertNotIn("apt-get update",self.workflow)
        self.assertNotIn("ffprobe -v",self.workflow)

    def test_real_media_is_still_physically_decoded_and_codec_tested(self):
        self.assertIn('ffmpeg -hide_banner -loglevel error -xerror -i "$f" -f null -',
                      self.workflow)
        self.assertIn('"Video: h264"',self.workflow)
        self.assertIn('"Audio: aac"',self.workflow)
        self.assertIn("1080x1920",self.workflow)
        self.assertIn('python - "$f" <<\\'PY\\'',self.workflow)
        self.assertIn("sha256sum",self.workflow)

    def test_no_upload_or_private_secret_in_cloud_smoke(self):
        self.assertIn("permissions:\n  contents: read",self.workflow)
        self.assertIn("persist-credentials: false",self.workflow)
        self.assertIn('FLOWMINUTE_ENABLE_PUBLISH: "0"',self.workflow)
        self.assertIn('FLOWMINUTE_ALLOW_LAPTOP: "0"',self.workflow)
        self.assertNotIn("id-token: write",self.workflow)
        self.assertNotIn("secrets.",self.workflow)
        self.assertNotIn("videos.insert",self.workflow)
        self.assertNotIn("actions/upload-artifact",self.workflow)


if __name__=="__main__":
    unittest.main()
