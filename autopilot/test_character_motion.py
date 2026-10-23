"""Motion tests; passing these does not certify video visuals or lip sync."""
import unittest
from autopilot.character_motion import V3, ASHA, KABIR, sample, shoulder, inverse_elbow, proof, UPPER, FOREARM


class CharacterMotionTests(unittest.TestCase):
    def test_both_arms_have_exact_bone_lengths(self):
        for i in range(97):
            frame=sample(i/12)
            for root,side,elbow,wrist in (
                (ASHA,"right",frame.asha_elbow,frame.asha_wrist),
                (KABIR,"left",frame.kabir_elbow,frame.kabir_wrist)
            ):
                self.assertAlmostEqual((elbow-shoulder(root,side)).norm(),UPPER,places=5)
                self.assertAlmostEqual((wrist-elbow).norm(),FOREARM,places=5)

    def test_hand_has_physically_locked_contact(self):
        self.assertLess(proof(12)["maximum_grasp_error_m"],1e-7)

    def test_no_two_hands_claim_custody_simultaneously(self):
        for i in range(97):
            frame=sample(i/12)
            self.assertFalse(frame.asha_gripping and frame.kabir_gripping)

    def test_draft_proof_cannot_publish(self):
        state=proof()
        self.assertFalse(state["publish_ready"])
        self.assertFalse(state["jaw_audio_synced"])
        self.assertEqual(state["youtube_uploads"],0)

    def test_out_of_reach_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"outside anatomical reach"):
            inverse_elbow(V3(0,0,0),V3(4,0,0),side="right")

    def test_actual_object_movement(self):
        self.assertLess(sample(0).cube.x,sample(5).cube.x)
        self.assertTrue(sample(6).result_visible)

    def test_expressive_eye_blink_events(self):
        self.assertEqual(sample(.72).asha_blink,1.)
        self.assertEqual(sample(1.38).kabir_blink,1.)

    def test_time_boundaries(self):
        for t in (-.1,8.1):
            with self.assertRaises(ValueError):
                sample(t)


if __name__ == "__main__":
    unittest.main()
