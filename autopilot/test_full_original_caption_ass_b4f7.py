"""B4f7: actual hosted FFmpeg native subtitle pixel-location safety tests.

The November 7 owner MP4 review showed huge captions clipped at the top
despite old static 4/2 line-count tests. This suite samples libass output
at real 1080x1920 and 1920x1080 canvas sizes against exact permitted panel
coordinates. It tests actual decoded pixel positions, not just ASS strings.
"""
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from autopilot.full_original_caption_ass_b4f7 import (
    NativeCaptionRefused, STATUS, STYLE, native_caption_layout,
    compose_rehearsal_native_ass, write_rehearsal_native_ass,
)


class NativeCanvasCaptionTests(unittest.TestCase):
    def test_pixel_playres_and_caption_safe_rect_for_both_formats(self):
        cue=[{"start":0.0,"end":3.0,
              "text":"Check this original sample before claiming anything."}]
        for kind in ("short","long"):
            with self.subTest(kind=kind):
                ass,proof=compose_rehearsal_native_ass(cue,kind)
                cfg=STYLE[kind]
                self.assertIn(f"PlayResX: {cfg['w']}",ass)
                self.assertIn(f"PlayResY: {cfg['h']}",ass)
                self.assertIn(f"DejaVu Sans,{cfg['font']}",ass)
                self.assertIn(fr"\pos({cfg['x']},{cfg['y']})",ass)
                self.assertEqual(proof["max_subtitle_lines"],2)
                self.assertTrue(proof["source_spoken_words_preserved"])
                self.assertFalse(proof["youtube_release_authorized"])
                self.assertTrue(cfg["text_top"]<cfg["y"]<cfg["text_bottom"])
                self.assertLess(cfg["text_bottom"],cfg["panel_bottom"])

    def test_original_pcm_long_phrase_keeps_all_words_across_microcards(self):
        phrase=(
            "One convincing illustration is not experimental evidence "
            "and both examples require their own original sources.")
        cues=[{"start":0.0,"end":6.0,"text":phrase},
              {"start":6.1,"end":11.9,
               "text":"Compare the starting conditions and describe the limits."}]
        for kind in ("short","long"):
            ass,proof=compose_rehearsal_native_ass(cues,kind)
            self.assertGreaterEqual(proof["two_line_voice_timed_microcard_count"],2)
            self.assertEqual(proof["original_pcm_phrase_count"],2)
            self.assertEqual(ass.count("Dialogue:"),proof["two_line_voice_timed_microcard_count"])
            for line in ass.splitlines():
                if line.startswith("Dialogue:"):
                    self.assertLessEqual(line.count(r"\N"),1)
            self.assertNotIn("force_style",ass)
            self.assertNotIn("FontSize=27",ass)

    def test_srt_synthetic_font_expansion_cannot_return(self):
        src=(Path(__file__).resolve().parent/
             "full_original_rehearsal_media_b4e1.py").read_text()
        self.assertIn("write_rehearsal_native_ass(",src)
        self.assertIn("ass={native_path.as_posix()}",src)
        self.assertNotIn("force_style=",src)
        self.assertNotIn("subtitles={srt.as_posix()}",src)
        self.assertIn("cues=cues",src)
        self.assertIn("caption_top=h-(390 if portrait else 320)",src)

    def test_missing_unsafe_oversized_and_out_of_order_cues_rejected(self):
        cases=(
            [],
            [{"start":0.0,"end":3.0,"text":"bad "+r"{\pos(0,0)}"}],
            [{"start":0.0,"end":3.0,"text":"bad "+r"\Nbreak"}],
            [{"start":0.0,"end":0.01,"text":"Too fast to read!"}],
            [{"start":3.0,"end":6.0,"text":"First."},
             {"start":2.0,"end":7.0,"text":"Bad overlapping cue."}],
        )
        for kind in ("short","long"):
            for case in cases:
                with self.subTest(kind=kind,case=case),self.assertRaises(NativeCaptionRefused):
                    compose_rehearsal_native_ass(case,kind)
        with self.assertRaises(NativeCaptionRefused):
            native_caption_layout("vertical-unknown")

    def test_only_new_ephemeral_ass_written_once(self):
        with TemporaryDirectory() as root:
            folder=Path(root)
            cue=[{"start":0.0,"end":3.0,"text":"Original controlled rehearsal caption."}]
            ass=write_rehearsal_native_ass(folder,cue,"short")
            self.assertEqual(ass.suffix,".ass")
            self.assertIn("PlayResX: 1080",ass.read_text())
            with self.assertRaises(NativeCaptionRefused):
                write_rehearsal_native_ass(folder,cue,"short")

    @unittest.skipUnless(shutil.which("ffmpeg"),"real ffmpeg required")
    def test_physically_decoded_libass_letters_stay_inside_reserved_panels(self):
        # This exactly catches what the prior static line-count tests missed:
        # libass default-SRT synthetic PlayRes could draw subtitle text from
        # 0px TOP down to scene illustrations, rather than near footer.
        with TemporaryDirectory() as root:
            folder=Path(root)
            for kind in ("short","long"):
                with self.subTest(kind=kind):
                    cue=[{"start":0.0,"end":2.0,
                          "text":"This is an original caption pixel safety test."}]
                    script,proof=compose_rehearsal_native_ass(cue,kind)
                    cfg=STYLE[kind]
                    target=folder/(kind+".ass")
                    target.write_text(script,encoding="utf8")
                    w,h=cfg["w"],cfg["h"]
                    run=subprocess.run([
                        "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
                        "-f","lavfi","-i",f"color=c=black:s={w}x{h}:r=4:d=1",
                        "-vf",f"ass={target.as_posix()}",
                        "-frames:v","3","-pix_fmt","rgb24",
                        "-f","rawvideo","-",
                    ],capture_output=True,timeout=50,check=True)
                    self.assertEqual(len(run.stdout),w*h*3*3)
                    # Last of 3 frames is at PTS=0.5s: 60ms fade
                    # finished. Frame zero at 0s correctly has no glyphs.
                    pixels=run.stdout[-w*h*3:]
                    stride=w*3
                    rows=[y for y in range(h)
                          if any(channel>45 for channel in pixels[
                              y*stride:(y+1)*stride])]
                    self.assertGreater(len(rows),8)
                    self.assertGreaterEqual(min(rows),cfg["text_top"],
                        "ACTUAL subtitle pixels leaked above reserved panel")
                    self.assertLessEqual(max(rows),cfg["text_bottom"],
                        "ACTUAL subtitle pixels leaked into footer or frame")


if __name__=="__main__":
    unittest.main()
