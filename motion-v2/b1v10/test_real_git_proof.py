"""RC3 real-Git capture and integration evidence regression."""
import json,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
def read(n):return json.loads((D/n).read_text(encoding="utf-8"))
class RealGitProofTests(unittest.TestCase):
    def test_exact_git_history(self):
        old=read("GIT_BISECT_DEMO.json");new=read("GIT_CAPTURE_QA.json")
        result=new["actual_git_result"]
        self.assertEqual(result["commits"],old["commits"])
        self.assertEqual(result["first_bad_commit"],old["first_bad_commit"])
        self.assertEqual(result["first_bad"],11)
        self.assertTrue(result["reset_completed"])
        self.assertEqual([s["revision"] for s in result["steps"]],[7,11,9,10])
        self.assertEqual([s["classification"] for s in result["steps"]],["good","bad","good","good"])
        self.assertEqual(new["decoded_frames"],192)
        self.assertEqual(len(new["pages"]),8)
    def test_integrated_media(self):
        r=read("REAL_PROOF_LONG_QA.json");c=read("GIT_CAPTURE_QA.json");old=read("LONG_PILOT_QA.json")
        self.assertEqual(r["capture_sha256"],c["capture_sha256"])
        self.assertEqual(r["prior_mp4_sha256"],old["mp4_sha256"])
        self.assertEqual(r["frames"],3360)
        self.assertEqual(r["audio_samples"],r["frames"]*1600)
        self.assertTrue(r["pcm_identical_to_prior_pilot"])
        self.assertTrue(r["full_decode_pass"])
        self.assertEqual(len(r["observed_overlay_matches"]),8)
        self.assertTrue(all(x["mean_gray_error"]<8 and x["mean_gray_error"]<x["next_best_error"] for x in r["observed_overlay_matches"]))
        self.assertTrue(all(a<=b for a,b in zip(r["embedded_dimensions"],c["dimensions"])))
    def test_no_release_authority(self):
        r=read("REAL_PROOF_LONG_QA.json")
        for name in ("legacy_capture_validator_pass","creative_policy_full_pass","human_playback_approved","release_authorized"):
            self.assertIs(r[name],False)
if __name__=="__main__":unittest.main()
