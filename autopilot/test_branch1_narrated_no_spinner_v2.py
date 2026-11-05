"""B1q2 tangible full video bridge tests, exactly sourced past Shorts only."""
from __future__ import annotations
from dataclasses import replace
from hashlib import sha256
import importlib.util
import inspect
import json
from pathlib import Path
import tempfile
import unittest

from autopilot.branch1_no_spinner_storyboard import (
    draw_source_keyframe,storyboard_cues,NoSpinnerVisualRejected,
)
from autopilot.branch1_three_narrated_no_spinner_v2 import (
    SOURCES,FPS,STATUS,RealShortRejected,_load_source,_fit_original_ass_text,
    _render_caption_files,_verified_srt_source,_time_srt,_time_ass,
    original_pcm_and_measured_cues,original_animated_keyframe_timeline,
    _esc_ass,
)

ROOT=Path(__file__).resolve().parents[1]


class SourceBoundNoSpinnerFullVideoCodeTests(unittest.TestCase):
    def test_only_three_actual_recorded_original_short_episodes_are_eligible(self):
        self.assertEqual(len(SOURCES),3)
        self.assertEqual({v for _,v in SOURCES},{"af_heart","bf_emma","am_michael"})
        self.assertEqual(FPS,24)
        for eid,_ in SOURCES:
            with self.subTest(episode=eid):
                obj=_load_source(ROOT,eid)
                self.assertEqual(obj["id"],eid)
                self.assertGreater(len(storyboard_cues(obj)),5)
        with self.assertRaises(RealShortRejected):
            _load_source(ROOT,"fm_20261111_fake_short")

    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Native glyph/1080p safe zone tested by dedicated B1q2 Pillow CI")
    def test_all_3_source_caption_overlays_are_original_and_native_fit(self):
        for eid,_ in SOURCES:
            source=_load_source(ROOT,eid)
            for c in source["captions"]:
                with self.subTest(eid=eid,text=c["text"][:30]):
                    lines,size=_fit_original_ass_text(c["text"])
                    self.assertGreaterEqual(size,26)
                    self.assertLessEqual(len(lines),4)
                    self.assertEqual(" ".join(lines),c["text"])

    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Native glyph/1080p safe zone tested by dedicated B1q2 Pillow CI")
    def test_exact_source_illustrations_reserve_clean_timed_ass_band(self):
        from PIL import ImageChops
        for eid,_ in SOURCES:
            src=_load_source(ROOT,eid)
            with self.subTest(eid=eid):
                a,receipt=draw_source_keyframe(src,0,.71)
                b,altered=draw_source_keyframe(
                    src,0,.71,caption_layer="timed_ass_overlay")
                self.assertEqual(a.size,(1080,1920))
                self.assertTrue(altered["timed_ass_caption_overlay_required"])
                self.assertFalse(receipt["timed_ass_caption_overlay_required"])
                self.assertIsNone(ImageChops.difference(
                    a.crop((0,0,1080,300)),b.crop((0,0,1080,300))).getbbox(),
                    "Native intro and theme labels must remain identical")
                self.assertIsNotNone(ImageChops.difference(
                    a.crop((0,301,1080,495)),b.crop((0,301,1080,495))).getbbox(),
                    "Native video must replace giant duplicated original sentence with short theme headline")
                self.assertIsNone(ImageChops.difference(
                    a.crop((0,495,1080,1410)),b.crop((0,495,1080,1410))).getbbox(),
                    "Original source artwork above the ASS subtitle band must remain unchanged")
                self.assertFalse(altered["hero_headline_repeats_full_spoken_sentence"])
                self.assertIsNotNone(ImageChops.difference(
                    a.crop((80,1410,999,1650)),b.crop((80,1410,999,1650))).getbbox(),
                    "Timed overlay must remove static captions to prevent doubled words")
                self.assertIsNone(ImageChops.difference(
                    a.crop((0,1650,1080,1920)),b.crop((0,1650,1080,1920))).getbbox())
        src=_load_source(ROOT,SOURCES[0][0])
        with self.assertRaises(NoSpinnerVisualRejected):
            draw_source_keyframe(src,0,.4,caption_layer="duplicated_unsafe_static")

    def test_script_escape_rejects_injection_not_claiming_fake_caption(self):
        self.assertEqual(_esc_ass("my {source} \\ text"),"my (source) ＼ text")
        for bad in ("x\nInjected", "x\rno", "x\0bad"):
            with self.assertRaises(RealShortRejected):
                _esc_ass(bad)

    def test_bad_receipt_id_and_injected_video_id_cannot_bind_source(self):
        with tempfile.TemporaryDirectory() as root:
            d=Path(root)/"content"/"episodes";d.mkdir(parents=True)
            r=Path(root)/"state"/"scheduled";r.mkdir(parents=True)
            id=SOURCES[0][0]
            s=_load_source(ROOT,id)
            rec=json.loads((ROOT/"state"/"scheduled"/f"{id}.json").read_text())
            rec["youtube_video_id"]="an invalid id"
            (d/f"{id}.json").write_text(json.dumps(s))
            (r/f"{id}.json").write_text(json.dumps(rec))
            with self.assertRaises(RealShortRejected):
                _load_source(Path(root),id)

    def test_loop_or_provider_insertion_is_not_a_secret_automatic_publisher(self):
        from autopilot import branch1_three_narrated_no_spinner_v2 as mod
        src=inspect.getsource(mod)
        for banned in ("videos().insert(", "youtube.upload(", "youtube.videos().update(",
                       "while True:", "d.arc(", "d.ellipse(",
                       "requests.get(", "GenUI.issueNewTurn("):
            self.assertNotIn(banned,src)
        self.assertIn('original_file_spinners_replaced_on_youtube":0',src)
        self.assertIn('new_original_private_uploads":0',src)


@unittest.skipUnless(
    importlib.util.find_spec("PIL") is not None and
    importlib.util.find_spec("numpy") is not None and
    importlib.util.find_spec("soundfile") is not None,
    "Physical source and PCM tests run with local-only GitHub workflow deps",
)
class RealFrameAndPcmCuesWithoutThirdPartyModelTests(unittest.TestCase):
    class FakeNoCredentialVoiceEngine:
        """Only a local deterministic PCM fixture; NOT real Kokoro performance."""
        def create(self, text,*,voice,speed,lang):
            import numpy as np
            if not 5<=len(text)<=240:
                raise AssertionError("Lost original caption text")
            rate=22050
            seconds=2.75
            t=np.arange(round(rate*seconds),dtype=np.float32)/rate
            return (.048*np.sin(2*np.pi*280*t)).astype(np.float32),rate

    def test_real_pcm_sequence_exact_speech_script_and_ass_subtitles(self):
        import soundfile as sf
        for eid,voice in SOURCES:
            episode=_load_source(ROOT,eid)
            with self.subTest(eid=eid),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)
                wav,cues,total,meta=original_pcm_and_measured_cues(
                    self.FakeNoCredentialVoiceEngine(),episode,folder,voice)
                self.assertGreater(total,22)
                self.assertLess(total,100)
                self.assertEqual(len(cues),len(episode["captions"]))
                self.assertTrue(meta["exact_source_words_unchanged"])
                self.assertEqual([x["text"] for x in cues],
                                 [x["text"] for x in episode["captions"]])
                arr,rate=sf.read(wav)
                self.assertEqual(rate,22050)
                self.assertLess(abs(len(arr)/rate-total),.0002)
                srt,ass=_render_caption_files(cues,folder)
                self.assertIn("PlayResX: 1080",ass.read_text())
                self.assertIn("PlayResY: 1920",ass.read_text())
                self.assertIn(r"\an8\pos(540,1450)",ass.read_text())
                _verified_srt_source(srt,cues,total)
                with self.assertRaises(RealShortRejected):
                    _verified_srt_source(srt,cues[:-1],total)
                self.assertFalse(meta["human_voice_approval"])

    def test_actual_animated_voice_timeline_is_full_length_source_locked_and_no_static_captions(self):
        eid,voice=SOURCES[1]
        episode=_load_source(ROOT,eid)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            wav,cues,total,rec=original_pcm_and_measured_cues(
                self.FakeNoCredentialVoiceEngine(),episode,root,voice)
            cat,drawn,visual=original_animated_keyframe_timeline(
                episode,cues,root,spoken_total=total)
            self.assertGreaterEqual(drawn,len(cues)*3)
            self.assertGreater(cat.stat().st_size,250)
            self.assertTrue(visual["perpetual_spinning_ring_absent"])
            self.assertTrue(visual["true_caption_and_hero_starts_bound_to_same_pcm"])
            self.assertEqual(visual["actual_hero_pcm_max_start_drift_seconds"],0)
            self.assertAlmostEqual(
                visual["visual_ffconcat_total_with_silences_seconds"],total,places=2)
            self.assertEqual(len({x["original_visual_motion"] for x in cues}),8)
            self.assertTrue(visual["three_distinct_original_semantic_hero_subjects"])
            self.assertEqual(len(list(root.glob("motion_*.png"))),drawn)

    def test_voice_not_actual_youtube_schedule_and_not_implicitly_approved(self):
        episode=_load_source(ROOT,SOURCES[0][0])
        source=storyboard_cues(episode)
        self.assertTrue(all(x["owner_approved"] is False for x in source))
        for v in (-.1,121,float("nan")):
            with self.assertRaises(RealShortRejected):
                _time_ass(v)
        self.assertEqual(_time_srt(3.25),"00:00:03,250")
        self.assertEqual(_time_ass(3.25),"0:00:03.25")


if __name__=="__main__":
    unittest.main()
