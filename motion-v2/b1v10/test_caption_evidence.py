import copy,json,unittest
from pathlib import Path
from correct_caption_homophone import correct
from narration_review import normalized,validate_words
D=Path(__file__).resolve().parent
class CaptionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.r=json.loads((D/"NARRATION_REVIEW_QA.json").read_text(encoding="utf-8"))
        self.raw=json.loads((D/"word_captions.json").read_text(encoding="utf-8"))
    def test_exact_correction(self):
        revised,entry=correct(self.raw,self.r)
        self.assertEqual(entry["asr_token"],"bite?")
        self.assertEqual(entry["caption_token"],"byte?")
        raw=[w for c in self.raw for w in c["words"]]
        final=[w for c in revised for w in c["words"]]
        self.assertEqual([(w["start"],w["end"]) for w in raw],[(w["start"],w["end"]) for w in final])
        self.assertEqual(normalized(" ".join(w["word"] for w in final)),normalized(" ".join(s["expected"] for s in self.r["scene_timeline"])))
        self.assertEqual(sum(a["word"]!=b["word"] for a,b in zip(raw,final)),1)
    def test_unknown_mismatch(self):
        r=copy.deepcopy(self.r);r["scene_timeline"][0]["recognized"]="A different sentence"
        with self.assertRaises(ValueError):correct(self.raw,r)
    def test_other_scene_error(self):
        r=copy.deepcopy(self.r);r["scene_timeline"][1]["exact_token_match"]=False
        with self.assertRaises(ValueError):correct(self.raw,r)
    def test_frame_clock(self):
        last=0
        for s in self.r["scene_timeline"]:
            self.assertEqual(s["start_frame"],last)
            self.assertGreater(s["end_frame"],last)
            last=s["end_frame"]
        self.assertEqual(last,self.r["frames_at_30fps"])
        self.assertEqual(last*1600,self.r["samples"])
        validate_words([w for c in self.raw for w in c["words"]],self.r["duration_seconds"])
if __name__=="__main__":unittest.main()
