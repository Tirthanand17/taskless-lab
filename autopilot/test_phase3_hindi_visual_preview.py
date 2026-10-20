"""Genuine Hindi glyph-render and landscape-vs-portrait MP4 regression tests.

All outputs are intentionally silent and editorially unapproved. These tests
use installed OFL/OS font packages only, never a network TTS provider.
"""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase3_hindi_visual_preview import (
    _authored_profile, _shown_cue, _font,
    render_hindi_frame, render_hindi_visual_preview,
)

class HindiRealVisualTests(unittest.TestCase):
    def test_exact_two_authored_episode_profiles(self):
        h=_authored_profile("csv_tutorial_short_hi")
        l=_authored_profile("csv_tutorial_long_hi")
        self.assertEqual((h[0],h[1],len(h[2])),("short",42,4))
        self.assertEqual((l[0],l[1],len(l[2])),("long",432,24))
        self.assertEqual(h[3][0][0],0)
        self.assertEqual(l[3][-1][1],432000)

    def test_short_and_long_use_actual_hindi_cues(self):
        for episode in ("csv_tutorial_short_hi","csv_tutorial_long_hi"):
            with self.subTest(episode=episode):
                profile=_authored_profile(episode)
                cue=_shown_cue(profile,800)
                self.assertTrue(any("\u0900"<=x<="\u097f" for x in cue))
                self.assertNotIn("<",cue)

    def test_portrait_and_landscape_are_correct_aspect_ratios(self):
        s=render_hindi_frame("csv_tutorial_short_hi",1,width=360)
        l=render_hindi_frame("csv_tutorial_long_hi",1,width=640)
        self.assertEqual(s.size,(360,640))
        self.assertEqual(l.size,(640,360))
        self.assertEqual(s.mode,"RGB")

    def test_real_full_hd_frames_use_correct_portrait_and_landscape(self):
        portrait=render_hindi_frame("csv_tutorial_short_hi",1,width=1080)
        landscape=render_hindi_frame("csv_tutorial_long_hi",1,width=1920)
        self.assertEqual(portrait.size,(1080,1920))
        self.assertEqual(landscape.size,(1920,1080))
        self.assertNotEqual(portrait.getpixel((10,10)),portrait.getpixel((10,1000)))
        self.assertNotEqual(landscape.getpixel((10,10)),landscape.getpixel((10,1000)))

    def test_full_hd_preview_is_hard_capped_to_36_frames(self):
        with tempfile.TemporaryDirectory() as root:
            for episode,width in (
                ("csv_tutorial_short_hi",1080),
                ("csv_tutorial_long_hi",1920),
            ):
                with self.subTest(episode=episode),self.assertRaises(WorkflowError):
                    render_hindi_visual_preview(
                        episode,Path(root)/(episode+".mp4"),
                        width=width,fps=24,duration_s=2)
                self.assertFalse((Path(root)/(episode+".mp4")).exists())

    def test_animated_pixels_change_in_same_scene(self):
        x=render_hindi_frame("csv_tutorial_short_hi",1,width=360)
        y=render_hindi_frame("csv_tutorial_short_hi",1.25,width=360)
        self.assertNotEqual(x.tobytes(),y.tobytes())

    def test_24_long_scenes_use_accurate_source_specific_storyboard(self):
        from autopilot.phase3_hindi_visual_preview import (
            LONG_SCENE_STORYBOARD, LONG_CODE_SNIPPETS, LONG_ROW_CALLOUTS,
        )
        self.assertEqual(len(LONG_SCENE_STORYBOARD),24)
        self.assertEqual(len({label for _,label in LONG_SCENE_STORYBOARD}),24)
        self.assertEqual(set(mode for mode,_ in LONG_SCENE_STORYBOARD),
                         {0,1,2,3,4,5,6})
        # No generic position%4 cycling: actual narrative flow is
        # intro -> privacy -> CSV concepts -> writer/reader -> math ->
        # CSV edge cases -> privacy -> recap.
        for index,mode in {
            0:0,1:4,2:0,5:2,6:2,7:2,8:2,9:2,10:5,
            11:1,12:1,13:1,14:3,16:2,17:2,18:4,19:5,
            20:5,21:2,22:5,23:6,
        }.items():
            with self.subTest(scene=index):
                self.assertEqual(LONG_SCENE_STORYBOARD[index][0],mode)
        self.assertEqual(
            set(LONG_CODE_SNIPPETS),
            {i for i,(mode,_) in enumerate(LONG_SCENE_STORYBOARD)
             if mode==2},
        )
        self.assertEqual(set(LONG_ROW_CALLOUTS),{11,12,13})
        self.assertIn("50",LONG_ROW_CALLOUTS[12])
        self.assertIn("58",LONG_ROW_CALLOUTS[13])

    def test_landscape_code_overlay_stays_inside_card_and_above_footer(self):
        from PIL import Image, ImageDraw
        from autopilot.phase3_hindi_visual_preview import (
            LONG_CODE_SNIPPETS,
        )
        from autopilot.phase3_hindi_visual_preview import _font as font
        draw=ImageDraw.Draw(Image.new("RGB",(960,540)))
        code_font=font(22)
        left,right=44,960-44
        code_left=left+43
        code_right=right-20
        footer_top=(425-184)-26
        for index,lines in LONG_CODE_SNIPPETS.items():
            with self.subTest(scene=index):
                self.assertEqual(len(lines),4)
                for line in lines:
                    self.assertLess(draw.textlength(line,font=code_font),
                                    code_right-code_left)
                last_line_bottom=63+3*36+max(
                    code_font.getbbox(line)[3] for line in lines)
                self.assertLess(last_line_bottom,footer_top-5)

    def test_all_long_workflows_show_lesson_specific_checks(self):
        from autopilot.phase3_hindi_visual_preview import (
            LONG_WORKFLOW_STEPS, LONG_WORKFLOW_FOOTERS,
            LONG_SCENE_STORYBOARD,
        )
        self.assertEqual(set(LONG_WORKFLOW_STEPS),{10,15,19,20,22})
        self.assertEqual(set(LONG_WORKFLOW_FOOTERS),set(LONG_WORKFLOW_STEPS))
        for index,labels in LONG_WORKFLOW_STEPS.items():
            with self.subTest(index=index):
                self.assertEqual(LONG_SCENE_STORYBOARD[index][0],5)
                self.assertEqual(len(labels),4)
                self.assertTrue(all(len(x)<=12 for x in labels))
        self.assertIn("INVALID",LONG_WORKFLOW_FOOTERS[10])
        self.assertIn("int()",LONG_WORKFLOW_FOOTERS[15])
        self.assertIn("RIGHTS",LONG_WORKFLOW_STEPS[20])
        self.assertIn("QUESTION",LONG_WORKFLOW_STEPS[22])

    def test_visual_totals_are_derived_from_executed_csv_lesson(self):
        from autopilot.examples.flowminute_csv_demo import (
            COLUMNS as DEMO_HEADERS, ROWS as DEMO_ROWS, demonstrate_csv_total,
        )
        from autopilot.phase3_hindi_visual_preview import (
            COLUMNS, LONG_ROW_CALLOUTS, _SAMPLE_LINE_TOTALS, _SAMPLE_TOTAL,
        )
        proof=demonstrate_csv_total()
        self.assertEqual(tuple(DEMO_HEADERS),COLUMNS[0])
        self.assertEqual(tuple(tuple(row[k] for k in DEMO_HEADERS)
                               for row in DEMO_ROWS),COLUMNS[1:])
        self.assertEqual(tuple(line["line_total"] for line in proof["rows"]),
                         _SAMPLE_LINE_TOTALS)
        self.assertEqual(proof["total"],_SAMPLE_TOTAL)
        self.assertEqual(_SAMPLE_LINE_TOTALS,(20,30,8))
        self.assertIn("20",LONG_ROW_CALLOUTS[11])
        self.assertIn("50",LONG_ROW_CALLOUTS[12])
        self.assertIn("58",LONG_ROW_CALLOUTS[13])
        self.assertFalse(proof["publishing_authorized"])

    def test_code_overlays_are_consistent_with_real_in_memory_demo(self):
        from autopilot.phase3_hindi_visual_preview import LONG_CODE_SNIPPETS
        combined="\\n".join(" ".join(x) for x in LONG_CODE_SNIPPETS.values())
        self.assertIn("w.writerows(ROWS)",combined)
        self.assertIn("w.writeheader()",combined)
        self.assertIn("DictReader(source)",combined)
        self.assertIn("StringIO(newline=",combined)
        self.assertIn('int(row["units"])',combined)
        self.assertIn("58",combined)
        self.assertNotIn('open("demo.csv"',combined)
        self.assertNotIn("writer = csv.DictWriter(stream,",combined)

    def test_final_long_recap_uses_three_stages_not_only_a_number(self):
        from autopilot.phase3_hindi_visual_preview import LONG_SCENE_STORYBOARD
        self.assertEqual(LONG_SCENE_STORYBOARD[23][0],6)
        ending=render_hindi_frame("csv_tutorial_long_hi",423,width=640)
        result=render_hindi_frame("csv_tutorial_long_hi",261,width=640)
        self.assertNotEqual(ending.tobytes(),result.tobytes())
        self.assertFalse(ending.getbbox() is None)

    def test_privacy_math_and_workflow_long_frames_render_distinctly(self):
        # The same long video now has multiple source-specific visual modes
        # whose actual pixels render; no external graphic/voice is fetched.
        slots=[1,5,11,14,19,22,23]
        images=[render_hindi_frame("csv_tutorial_long_hi",
                    i*18+9,width=640) for i in slots]
        self.assertTrue(all(img.size==(640,360) for img in images))
        self.assertEqual(len({img.tobytes() for img in images}),len(images))
        self.assertNotEqual(images[0].getpixel((320,190)),
                            images[2].getpixel((320,190)))

    def test_cue_changes_during_first_video_scene(self):
        short=_authored_profile("csv_tutorial_short_hi")
        self.assertNotEqual(_shown_cue(short,500),_shown_cue(short,8500))

    def test_frames_are_deterministic(self):
        a=render_hindi_frame("csv_tutorial_long_hi",3,width=640)
        b=render_hindi_frame("csv_tutorial_long_hi",3,width=640)
        self.assertEqual(a.tobytes(),b.tobytes())

    def test_every_authored_long_scene_renders_with_real_devanagari(self):
        profile=_authored_profile("csv_tutorial_long_hi")
        for index,(start,end,*_) in enumerate(profile[2]):
            # Real scene midpoint, not just the beginning of an unfinished plan.
            with self.subTest(scene=index+1):
                mid=(start+end)/2000
                img=render_hindi_frame("csv_tutorial_long_hi",mid,width=640)
                self.assertEqual(img.size,(640,360))
                self.assertTrue(_shown_cue(profile,int(mid*1000)))

    def test_hindi_short_stages_match_executable_fictional_source(self):
        from autopilot.examples.flowminute_csv_demo import (
            ROWS, demonstrate_csv_total,
        )
        from autopilot.phase3_hindi_visual_preview import (
            SHORT_SCENE_STORYBOARD, SHORT_ITEM_NAMES, SHORT_CODE_SNIPPETS,
            COLUMNS, _SAMPLE_LINE_TOTALS,
        )
        self.assertEqual(len(SHORT_SCENE_STORYBOARD),4)
        self.assertEqual(tuple(mode for mode,_ in SHORT_SCENE_STORYBOARD),
                         (0,1,2,3))
        self.assertTrue(all(any("\u0900"<=letter<="\u097f" for letter in label)
                            for _,label in SHORT_SCENE_STORYBOARD))
        self.assertEqual(tuple(SHORT_ITEM_NAMES),tuple(row["product"] for row in ROWS))
        self.assertEqual(tuple(tuple(row[k] for k in COLUMNS[0])
                               for row in ROWS),COLUMNS[1:])
        self.assertEqual(
            tuple(x["line_total"] for x in demonstrate_csv_total()["rows"]),
            _SAMPLE_LINE_TOTALS,
        )
        self.assertEqual(tuple(_SAMPLE_LINE_TOTALS),(20,30,8))
        self.assertEqual(len(SHORT_CODE_SNIPPETS),4)
        code=" ".join(SHORT_CODE_SNIPPETS)
        self.assertIn("output.getvalue()",code)
        self.assertIn("StringIO(csv_text)",code)
        self.assertIn("csv.DictReader(source)",code)
        self.assertNotIn("csv.DictReader(rows)",code)
        self.assertFalse(demonstrate_csv_total()["publishing_authorized"])

    def test_hindi_short_portrait_text_fits_source_visual_card(self):
        from PIL import Image, ImageDraw
        from autopilot.phase3_hindi_visual_preview import (
            SHORT_ITEM_NAMES, SHORT_CODE_SNIPPETS, _font,
        )
        d=ImageDraw.Draw(Image.new("RGB",(540,960)))
        # Short card extends from x=34 to x=506. New code starts x=77.
        code_font=_font(20)
        for line in SHORT_CODE_SNIPPETS:
            with self.subTest(line=line):
                self.assertLess(d.textlength(line,font=code_font),506-77-15)
        labels=_font(24,devanagari=True)
        for word in SHORT_ITEM_NAMES.values():
            with self.subTest(item=word):
                self.assertLess(d.textlength(word,font=labels),380)
        # 3 item cards: top=235; first start 333, last ends 620,
        # proof footer above bottom=704. No voice or user data loaded.
        self.assertLess(235+98+2*102+83,704-39)

    def test_four_hindi_short_scenes_draw_distinct_topic_graphics(self):
        frames=[render_hindi_frame("csv_tutorial_short_hi",moment,width=360)
                for moment in (5,15,25,36)]
        self.assertTrue(all(frame.size==(360,640) for frame in frames))
        self.assertEqual(len(set(frame.tobytes() for frame in frames)),4)

    def test_every_hindi_short_scene_renders_and_last_frame(self):
        profile=_authored_profile("csv_tutorial_short_hi")
        for index,(start,end,*_) in enumerate(profile[2]):
            with self.subTest(scene=index+1):
                img=render_hindi_frame("csv_tutorial_short_hi",
                                      (start+end)/2000,width=360)
                self.assertEqual(img.size,(360,640))
        final=render_hindi_frame("csv_tutorial_short_hi",41.875,width=360)
        self.assertEqual(final.size,(360,640))

    def test_bounds_fail_closed(self):
        with self.assertRaises(WorkflowError):
            render_hindi_frame("not_a_video",1,width=360)
        for width in (0,600,1000):
            with self.subTest(width=width),self.assertRaises(WorkflowError):
                render_hindi_frame("csv_tutorial_short_hi",1,width=width)
        with self.assertRaises(WorkflowError):
            render_hindi_frame("csv_tutorial_long_hi",432,width=640)

    def test_no_automatic_overwriting_or_media_storage_directory_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"output.mp4"
            p.write_bytes(b"exists")
            with self.assertRaises(WorkflowError):
                render_hindi_visual_preview("csv_tutorial_short_hi",p)
            p.unlink()
            with self.assertRaises(WorkflowError):
                render_hindi_visual_preview("csv_tutorial_short_hi",
                                            Path(tmp)/"not_created"/"output.mp4")
            
    def test_invalid_requested_full_long_media_render_exceeds_proof_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"clip.mp4"
            with self.assertRaises(WorkflowError):
                render_hindi_visual_preview("csv_tutorial_long_hi",p,
                                            duration_s=432,fps=24)
            self.assertFalse(p.exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Preinstalled FFmpeg required")
    def test_actual_two_video_outputs_decode_and_remain_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            for episode,width,dimensions in (
                ("csv_tutorial_short_hi",360,(360,640)),
                ("csv_tutorial_long_hi",640,(640,360)),
            ):
                with self.subTest(episode=episode):
                    path=Path(tmp)/(episode+".mp4")
                    result=render_hindi_visual_preview(
                        episode,path,duration_s=0.5,fps=8,width=width)
                    self.assertTrue(result["actual_video_pixels_encoded"])
                    self.assertFalse(result["audio_track_present"])
                    self.assertFalse(result["publishing_authorized"])
                    self.assertEqual((result["width"],result["height"]),dimensions)
                    meta=subprocess.run([
                        "ffprobe","-v","error","-show_entries",
                        "stream=codec_type,codec_name,width,height:format=duration",
                        "-of","json",str(path)],capture_output=True,text=True,
                        check=True,timeout=20)
                    record=json.loads(meta.stdout)
                    self.assertEqual(len(record["streams"]),1)
                    self.assertEqual(record["streams"][0]["codec_type"],"video")
                    self.assertEqual(record["streams"][0]["codec_name"],"h264")
                    self.assertEqual(
                        (record["streams"][0]["width"],record["streams"][0]["height"]),
                        dimensions)
                    subprocess.run([
                        "ffmpeg","-v","error","-xerror","-i",str(path),
                        "-f","null","-"],check=True,timeout=30)

if __name__=="__main__":
    unittest.main()
