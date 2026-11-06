"""B4e0b CI guard: no apt stall allowed on Kokoro source-locked voice runner.

Trusted first main B4e0 job #42242580566 exited 124 during apt install
despite the Python espeakng-loader 0.2.4 bundled wheel being installed.
"""
from __future__ import annotations

from pathlib import Path
import unittest

WORKFLOW=Path(__file__).resolve().parent.parent/(
    ".github/workflows/flowminute-daily-cloud-foundation.yml"
)


class FreeWheelOnlyKokoroBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=WORKFLOW.read_text(encoding="utf8")
        cls.voice_setup=cls.text.split(
            "      - name: Install verified public CPU voice and FFmpeg dependencies"
        )[1].split(
            "      - name: Download only pinned SHA256 public Kokoro speech weights"
        )[0]

    def test_no_system_apt_install_or_apt_update_in_live_media_stage(self):
        self.assertNotIn("sudo ",self.voice_setup)
        self.assertNotIn("apt-get install",self.voice_setup)
        self.assertNotIn("apt-get update",self.voice_setup)
        self.assertNotIn("timeout 110",self.voice_setup)

    def test_pinned_wheel_has_embedded_phonemizer_library_and_dictionary(self):
        self.assertIn("espeakng-loader==0.2.4",self.voice_setup)
        self.assertIn("kokoro-onnx==0.6.1",self.voice_setup)
        self.assertIn("--only-binary=:all:",self.voice_setup)
        self.assertIn("espeakng_loader.get_library_path()",self.voice_setup)
        self.assertIn("espeakng_loader.get_data_path()",self.voice_setup)
        self.assertIn("ctypes.CDLL(str(lib))",self.voice_setup)
        self.assertIn("lib.is_file() and data.is_dir()",self.voice_setup)

    def test_cannot_convert_no_publishing_run_into_upload_authority(self):
        self.assertIn('FLOWMINUTE_ENABLE_PUBLISH: "0"',self.text)
        self.assertIn('FLOWMINUTE_DAILY_SPEND_CAP_USD: "0"',self.text)
        self.assertIn("contents: read",self.text)
        self.assertIn("actions: read",self.text)
        self.assertNotIn("contents: write",self.text)
        self.assertNotIn("actions: write",self.text)

    def test_all_media_and_weights_destroyed_even_on_apt_replacement_failure(self):
        self.assertIn(
            "rm -rf /tmp/flowminute-b4e0-rendered-previews /tmp/flowminute-b4e0-pinned-model",
            self.text,
        )
        self.assertIn("if: always()",self.text)
        self.assertIn("B4E0_PUBLIC_KOKORO_MODEL_AND_VOICE_HASHES_MATCH",self.text)
        self.assertIn("full_h264_aac_decode_passed_all_three",self.text)


if __name__=="__main__":
    unittest.main()
