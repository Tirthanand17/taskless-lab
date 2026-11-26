"""RC4 long-format evidence and review fences."""
import json,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
def read(n):return json.loads((D/n).read_text(encoding="utf-8"))
class FocusLongTests(unittest.TestCase):
    def test_sources_and_clock(self):
        r=read("FOCUS_LONG_QA.json")
        self.assertEqual(r["capture_sha256"],read("GIT_CAPTURE_QA.json")["capture_sha256"])
        self.assertEqual(r["prior_pilot_sha256"],read("LONG_PILOT_QA.json")["mp4_sha256"])
        self.assertEqual(r["resolution"],[1920,1080])
        self.assertEqual(r["fps"],30)
        self.assertEqual(r["frames"],3360)
        self.assertEqual(r["audio_samples"],1600*r["frames"])
        self.assertTrue(r["pcm_identical"] and r["full_decode_pass"])
        self.assertEqual(r["audio_energy"]["clipped_samples"],0)
    def test_panels(self):
        r=read("FOCUS_LONG_QA.json");p=r["panels"]
        self.assertEqual([x["page"] for x in p],list(range(8)))
        self.assertGreaterEqual(p[0]["start_frame"],335)
        self.assertEqual(p[0]["crop"],[0,196,470,38])
        self.assertEqual(p[6]["start_frame"],2155)
        self.assertTrue(all(a["end_frame"]<=b["start_frame"] for a,b in zip(p,p[1:])))
        self.assertTrue(all(1<=x["magnification"]<=2 for x in p))
        self.assertEqual(len(r["observed_crops"]),8)
        self.assertTrue(all(x["mean_gray_error"]<3 for x in r["observed_crops"]))
    def test_review_only(self):
        r=read("FOCUS_LONG_QA.json")
        self.assertFalse(r["human_mobile_approved"])
        self.assertFalse(r["release_authorized"])
if __name__=="__main__":unittest.main()
