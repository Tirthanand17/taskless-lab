"""RC4 review-only evidence checks."""
import hashlib,json,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
def read(n):return json.loads((D/n).read_text(encoding="utf-8"))
class FocusShortTests(unittest.TestCase):
    def test_capture_and_audio(self):
        r=read("FOCUS_SHORT_QA.json")
        self.assertEqual(r["capture_sha256"],read("REAL_CAPTURE_QA.json")["capture_sha256"])
        self.assertEqual(r["prior_pilot_sha256"],read("SHORT_PILOT_QA.json")["mp4_sha256"])
        self.assertEqual(r["resolution"],[1080,1920])
        self.assertEqual(r["frames"],581)
        self.assertEqual(r["audio_samples"],r["frames"]*1600)
        self.assertTrue(r["pcm_identical"] and r["full_decode_pass"])
        self.assertEqual(r["audio_energy"]["clipped_samples"],0)
    def test_timed_panels(self):
        r=read("FOCUS_SHORT_QA.json")
        p=r["panels"]
        e={x["anchor"]:x["frame"] for x in read("SOUND_MIX_QA.json")["events"]}
        self.assertEqual(len(p),5)
        self.assertEqual([p[i]["start"] for i in (0,1,3,4)],[e[k] for k in ("a","b","fingerprints","trusted")])
        self.assertTrue(all(a["end"]<=b["start"] for a,b in zip(p,p[1:])))
        for x in p:
            a,b,w,h=x["crop"];dw,dh=x["display"]
            self.assertTrue(0<=a and 0<=b and a+w<=870 and b+h<=692)
            self.assertTrue(dw<=770 and dh<=190)
            self.assertTrue(1<=x["scale"]<=2)
        self.assertEqual(len(r["observed_crops"]),5)
        self.assertTrue(all(x["mean_gray_error"]<10 for x in r["observed_crops"]))
    def test_review_only(self):
        r=read("FOCUS_SHORT_QA.json")
        self.assertFalse(r["human_mobile_approved"])
        self.assertFalse(r["release_authorized"])
if __name__=="__main__":unittest.main()
