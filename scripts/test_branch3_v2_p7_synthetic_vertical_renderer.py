"""P7 adversarial source-free MP4 render commands and independent QC tests."""
from __future__ import annotations

from array import array
import copy
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts.branch3_v2_p5_synthetic_moment_proposals import P5Denied
from scripts.branch3_v2_p6_synthetic_storyboard import draft_synthetic_storyboard
from scripts.test_branch3_v2_p5_synthetic_editorial_evaluation import detector_packet
from scripts.branch3_v2_p7_synthetic_vertical_renderer import (
    WIDTH, HEIGHT, FPS, OUTPUT_NAME, P7Denied, _audio_rms,
    _filters, _frame_patch, check_original_signal_and_captions,
    read_synthetic_edl, render_command, render_synthetic_video,
    verify_output_probe,
)


def edl():
    return draft_synthetic_storyboard(detector_packet())


def probe():
    return {
        "streams": [
            {
                "codec_type": "video", "codec_name": "h264",
                "pix_fmt": "yuv420p", "width": WIDTH, "height": HEIGHT,
                "avg_frame_rate": f"{FPS}/1", "nb_frames": str(FPS * 6),
                "start_time": "0.000", "duration": "6.000",
            },
            {
                "codec_type": "audio", "codec_name": "aac",
                "sample_rate": "48000", "channels": 1,
                "start_time": "0.000", "duration": "6.016",
            },
        ],
        "format": {
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "duration": "6.016", "size": "44000",
        },
    }


def aac_pcm(value):
    pcm = array("h", [value] * 2000)
    import sys
    if sys.byteorder != "little":
        pcm.byteswap()
    return pcm.tobytes()


def mocked_frame_audio(cmd, **kwargs):
    assert cmd[0] == "ffmpeg"
    t = float(cmd[cmd.index("-ss") + 1])
    if "rawvideo" in cmd:
        overlay = "crop=200:44:35:315,format=gray" in cmd
        if overlay:
            result = bytes([16] * 4000 + [240] * 4800)
        else:
            result = bytes([235 if t == 2.5 else 16] * 64)
    elif "s16le" in cmd:
        result = aac_pcm(700 if t == 2.5 else 0)
    else:
        raise AssertionError("Unexpected tool operation")
    return SimpleNamespace(returncode=0, stdout=result, stderr=b"")


class SyntheticVerticalRenderTests(unittest.TestCase):
    def test_safe_p6_draft_inputs_are_source_free(self):
        p = edl()
        self.assertEqual(p["real_creator_source_files"], 0)
        self.assertEqual(p["creator_commercial_reuse_grants"], 0)
        self.assertEqual(p["youtube_uploads"], 0)
        self.assertFalse(p["human_editor_approved"])

    def test_render_command_no_external_inputs_fixed_original_captions(self):
        with tempfile.TemporaryDirectory() as root:
            font = Path(root) / "fontfile.ttf"
            font.write_bytes(b"synthetic-test-font-name-only")
            destination = Path(root) / OUTPUT_NAME
            with patch(
                "scripts.branch3_v2_p7_synthetic_vertical_renderer.FONT", font
            ):
                command = render_command(edl(), target=destination)
                filters = _filters(edl())
            self.assertEqual(command[0], "ffmpeg")
            self.assertEqual(command.count("-i"), 6)
            self.assertEqual(command.count("lavfi"), 6)
            self.assertIn("libx264", command)
            self.assertIn("yuv420p", command)
            self.assertIn("aac", command)
            self.assertIn("+faststart", command)
            self.assertIn("drawtext=", filters)
            self.assertEqual(filters.count("drawtext="), 3)
            self.assertIn("Watch the scene switch.", filters)
            self.assertIn("Flash and tone.", filters)
            self.assertIn("A sudden cut still needs context.", filters)
            self.assertIn("fontsize=12", filters)
            self.assertIn("fontsize=17", filters)
            for index, token in enumerate(command):
                if token == "-i":
                    self.assertEqual(command[index - 2:index], ["-f", "lavfi"])
                    self.assertTrue(
                        command[index + 1].startswith((
                            "color=", "anullsrc=", "sine=")))
            self.assertNotIn("http", " ".join(command))
            self.assertNotIn("yt-dlp", command)
            self.assertNotIn("upload", " ".join(command).lower())

    def test_forged_creator_approval_and_transcript_do_not_render(self):
        with tempfile.TemporaryDirectory() as root:
            font = Path(root) / "fontfile.ttf"
            font.write_bytes(b"fixture")
            for name, value in (
                ("human_editor_approved", True),
                ("creator_commercial_reuse_grants", 1),
                ("real_creator_source_files", 1),
                ("youtube_uploads", 1),
                ("youtube_publish_authorized", True),
            ):
                item = edl()
                item[name] = value
                with self.subTest(field=name):
                    with patch(
                        "scripts.branch3_v2_p7_synthetic_vertical_renderer.FONT", font
                    ), self.assertRaises(ValueError):
                        render_command(item, target=Path(root) / OUTPUT_NAME)

    def test_closed_upstream_rights_block_before_render(self):
        with tempfile.TemporaryDirectory() as root:
            with patch(
                "scripts.branch3_v2_p7_synthetic_vertical_renderer._probe_closed",
                side_effect=P5Denied("CLIVOX_P5_RIGHTS_DENIED"),
            ), self.assertRaises(P5Denied):
                render_command(edl(), target=Path(root) / OUTPUT_NAME)

    def test_output_probe_validates_portrait_av_streams_and_timing(self):
        verify_output_probe(probe(), actual_bytes=44000)
        cases = [
            ("video-width", lambda x: x["streams"][0].update(width=1920)),
            ("wrong-height", lambda x: x["streams"][0].update(height=1080)),
            ("codec", lambda x: x["streams"][0].update(codec_name="vp9")),
            ("fps", lambda x: x["streams"][0].update(avg_frame_rate="30/1")),
            ("frame-count", lambda x: x["streams"][0].update(nb_frames="130")),
            ("audio", lambda x: x["streams"][1].update(codec_name="mp3")),
            ("channels", lambda x: x["streams"][1].update(channels=2)),
            ("sample-rate", lambda x: x["streams"][1].update(sample_rate="44100")),
            ("audio-delay", lambda x: x["streams"][1].update(start_time="0.500")),
            ("audio-short", lambda x: x["streams"][1].update(duration="4.000")),
            ("too-long", lambda x: x["format"].update(duration="12.000")),
            ("not-mp4", lambda x: x["format"].update(format_name="matroska")),
            ("wrong-bytes", lambda x: x["format"].update(size="23000")),
            ("additional-stream", lambda x: x["streams"].append({"codec_type":"subtitle"})),
        ]
        for name, mutation in cases:
            doc = copy.deepcopy(probe())
            mutation(doc)
            with self.subTest(case=name), self.assertRaises(P7Denied):
                verify_output_probe(doc, actual_bytes=44000)
        with self.assertRaises(P7Denied):
            verify_output_probe(probe(), actual_bytes=True)

    def test_generated_scene_caption_and_tone_qa_mock(self):
        check_original_signal_and_captions(
            Path("/tmp/source-free-fixture-only.mp4"), runner=mocked_frame_audio)
        self.assertEqual(len(_frame_patch(
            Path("/tmp/source-free-fixture-only.mp4"), 1,
            runner=mocked_frame_audio, overlay=True)), 8800)
        self.assertGreater(_audio_rms(
            Path("/tmp/source-free-fixture-only.mp4"), 2.5,
            runner=mocked_frame_audio), 200)

    def test_missing_caption_wrong_scene_and_wrong_tone_fail(self):
        def missing_caption(cmd, **kwargs):
            p = mocked_frame_audio(cmd, **kwargs)
            if "rawvideo" in cmd and "crop=200:44:35:315,format=gray" in cmd:
                return SimpleNamespace(returncode=0, stdout=b"\x00" * 8800)
            return p
        with self.assertRaises(P7Denied):
            check_original_signal_and_captions(
                Path("/tmp/fixture.mp4"), runner=missing_caption)

        def scene_wrong(cmd, **kwargs):
            p = mocked_frame_audio(cmd, **kwargs)
            if "rawvideo" in cmd and "crop=8:8:0:0,format=gray" in cmd:
                return SimpleNamespace(returncode=0, stdout=b"\x10" * 64)
            return p
        with self.assertRaises(P7Denied):
            check_original_signal_and_captions(
                Path("/tmp/fixture.mp4"), runner=scene_wrong)

        def audio_wrong(cmd, **kwargs):
            p = mocked_frame_audio(cmd, **kwargs)
            if "s16le" in cmd:
                return SimpleNamespace(returncode=0, stdout=aac_pcm(0))
            return p
        with self.assertRaises(P7Denied):
            check_original_signal_and_captions(
                Path("/tmp/fixture.mp4"), runner=audio_wrong)

    def test_ephemeral_edl_file_guard_no_symlinks_or_escape(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)
            item = path / "synthetic-edl-draft-only.json"
            item.write_text(json.dumps(edl()), encoding="utf-8")
            self.assertEqual(read_synthetic_edl(path), edl())
            (path / "alias.json").symlink_to(item)
            for bad in ("alias.json", "../../source.json",
                        "/tmp/not_this_fixture.json"):
                with self.subTest(file=bad), self.assertRaises(P7Denied):
                    read_synthetic_edl(path, bad)
            broken = edl()
            broken["owner_final_media_approved"] = True
            item.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaises(P7Denied):
                read_synthetic_edl(path)
            item.write_text("Z" * 33000, encoding="utf-8")
            with self.assertRaises(P7Denied):
                read_synthetic_edl(path)

    def test_render_existing_output_is_denied_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / "synthetic-edl-draft-only.json").write_text(
                json.dumps(edl()), encoding="utf-8")
            old = folder / OUTPUT_NAME
            old.write_bytes(b"old media placeholder")
            with self.assertRaises(P7Denied):
                render_synthetic_video(scratch=folder)
            self.assertEqual(old.read_bytes(), b"old media placeholder")

    def test_runner_success_without_new_video_must_fail(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / "synthetic-edl-draft-only.json").write_text(
                json.dumps(edl()), encoding="utf-8")
            fakefont = folder / "f.ttf"
            fakefont.write_bytes(b"mockonly")
            with patch(
                "scripts.branch3_v2_p7_synthetic_vertical_renderer.FONT",
                fakefont,
            ), self.assertRaises(P7Denied):
                render_synthetic_video(
                    scratch=folder, runner=lambda *args, **kwargs:
                        SimpleNamespace(returncode=0, stdout=b"", stderr=b""))

    def test_ffmpeg_tool_failure_cannot_promote_synthetic_render(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / "synthetic-edl-draft-only.json").write_text(
                json.dumps(edl()), encoding="utf-8")
            mockfont = folder / "f.ttf"
            mockfont.write_bytes(b"mockonly")
            with patch(
                "scripts.branch3_v2_p7_synthetic_vertical_renderer.FONT",
                mockfont,
            ), self.assertRaises(P7Denied):
                render_synthetic_video(
                    scratch=folder, runner=lambda *args, **kwargs:
                        SimpleNamespace(returncode=1, stdout=b"", stderr=b""))

    def test_output_names_safe_and_no_user_selected_external_content(self):
        with tempfile.TemporaryDirectory() as root:
            font = Path(root) / "font.ttf"
            font.write_bytes(b"fixture")
            with patch(
                "scripts.branch3_v2_p7_synthetic_vertical_renderer.FONT", font
            ), self.assertRaises(P7Denied):
                render_command(edl(), target=Path(root) / "creator_video.mp4")


if __name__ == "__main__":
    unittest.main()
