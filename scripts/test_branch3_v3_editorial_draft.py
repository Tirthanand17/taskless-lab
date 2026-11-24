import unittest

from scripts.branch3_v3_multimodal_candidates import demo
from scripts.branch3_v3_transcript_context import fixture_rows
from scripts.branch3_v3_editorial_draft import draft, layout


class EditorialDraftTests(unittest.TestCase):
    def test_recomputed_caption_draft_and_hold(self):
        d=demo("dialogue")
        d["semantic_events_ms"]=None
        p=draft(d,fixture_rows(),"v3_01",1920,1080)
        self.assertEqual(p["layout"]["mode"],"fit")
        self.assertEqual(p["observed_opening_title_draft"],"Why does the first move matter?")
        self.assertTrue(p["caption_cues"])
        self.assertIn(" --> ",p["caption_srt"])
        self.assertTrue(all(0<=c["start_ms"]<c["end_ms"]<=24000
                            and len(c["text"])<=42 for c in p["caption_cues"]))
        self.assertFalse(p["render_authorized"])
        self.assertFalse(p["youtube_upload_authorized"])
        self.assertIsNone(p["original_commentary"])
        with self.assertRaises(ValueError):
            draft(d,fixture_rows(),"unknown",1920,1080)

    def test_safe_game_layout(self):
        p=layout("gaming",1920,1080,[0,0,320,240],[320,0,1600,1080])
        self.assertEqual(p["mode"],"game_facecam_stack")
        self.assertEqual(p["output"],[1080,1920])
        self.assertEqual(p["layers"][1]["target"],[0,600,1080,1320])
        for a,b in [([1,0,320,240],[320,0,1600,1080]),
                    ([0,0,320,240],[320,0,1920,1080]),
                    ([0,0,320,240],None)]:
            with self.assertRaises(ValueError):
                layout("gaming",1920,1080,a,b)


if __name__=="__main__":
    unittest.main()
