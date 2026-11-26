"""RC2 capture evidence tests. Existing Linux capture validator remains unchanged."""
import hashlib,json,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
def read(name):return json.loads((D/name).read_text(encoding="utf-8"))
class RealProofTests(unittest.TestCase):
    def test_actual_results(self):
        r=read("REAL_CAPTURE_QA.json")
        self.assertEqual(r["actual_result"]["sha256_a"],hashlib.sha256(b"A").hexdigest())
        self.assertEqual(r["actual_result"]["sha256_b"],hashlib.sha256(b"B").hexdigest())
        self.assertTrue(r["actual_result"]["expected_a_match"])
        self.assertFalse(r["actual_result"]["expected_b_match"])
        self.assertEqual(r["decoded_frames"],120)
        self.assertEqual(r["observed_state_changes"],3)
    def test_integration_clock_and_capture(self):
        r=read("REAL_PROOF_SHORT_QA.json")
        c=read("REAL_CAPTURE_QA.json")
        self.assertEqual(r["capture_sha256"],c["capture_sha256"])
        self.assertEqual(r["previous_pilot_sha256"],read("SHORT_PILOT_QA.json")["mp4_sha256"])
        self.assertEqual(r["audio_samples"],1600*r["frames"])
        self.assertTrue(r["pcm_identical_to_prior_pilot"])
        self.assertTrue(all(a<=b for a,b in zip(r["embedded_dimensions"],c["dimensions"])))
        self.assertEqual(len(r["source_state_change_frames"]),3)
        self.assertEqual(r["target_scene_boundaries"],[0,71,232,383,581])
    def test_no_legacy_approval(self):
        r=read("REAL_PROOF_SHORT_QA.json")
        for field in ("legacy_capture_validator_pass","creative_policy_full_pass","owner_full_playback_approved","release_authorized"):
            self.assertIs(r[field],False)
        self.assertIs(read("REAL_CAPTURE_QA.json")["legacy_xvfb_receipt_compatible"],False)
if __name__=="__main__":unittest.main()
