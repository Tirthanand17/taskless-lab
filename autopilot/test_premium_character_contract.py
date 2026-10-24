from copy import deepcopy
import unittest
from autopilot.premium_character_contract import validate_performance, PremiumRigError, JOINTS, FACE

STORY={"episode_id":"scene_demo01","shots":[{"mode":"true_3d","duration_seconds":10,"present":["asha","jay"]}]}
CHAR=lambda who: {"id":who,"required_joints":sorted(JOINTS),
    "required_face_shapes":sorted(FACE),"asset_status":"requested",
    "performance_audio_status":"not_generated",
    "wardrobe_identity":"Original blue futuristic lab workwear"}
SPEC={"schema_version":1,"episode_id":"scene_demo01","scene_number":1,
      "characters":[CHAR("asha"),CHAR("jay")],
      "performance_timeline":[
       {"actor":"asha","type":"gaze","start_second":0,"end_second":2,
        "directing_note":"Looks at the red question object"},
       {"actor":"jay","type":"expression","start_second":0,"end_second":2,
        "directing_note":"Shows genuine curiosity about the topic"},
       {"actor":"asha","type":"prop_contact","start_second":2,"end_second":5,
        "prop_id":"warning_cube","contact_target":"right_hand",
        "directing_note":"Lifts physical cube and points at it"},
       {"actor":"jay","type":"speech","start_second":3,"end_second":6,
        "directing_note":"Asks a concrete novice question"},
       {"actor":"asha","type":"gesture","start_second":5,"end_second":8,
        "directing_note":"Shows an open hand demonstration"}],
      "camera":{"move":"dolly","visual_focus":"Keep hands and demonstration cube legible"},
      "rig_asset_qc":False,"lip_sync_qc":False,"artistic_review":False}

class RigContractTests(unittest.TestCase):
    def test_not_rendered(self):
        self.assertFalse(validate_performance(SPEC,STORY)["release_ready"])
    def test_face_missing(self):
        spec=deepcopy(SPEC);spec["characters"][0]["required_face_shapes"].remove("viseme_MBP")
        with self.assertRaises(PremiumRigError):validate_performance(spec,STORY)
    def test_joint_missing(self):
        spec=deepcopy(SPEC);spec["characters"][0]["required_joints"].remove("elbow_left")
        with self.assertRaises(PremiumRigError):validate_performance(spec,STORY)
    def test_missing_contact(self):
        spec=deepcopy(SPEC);spec["performance_timeline"][2]["contact_target"]="fake"
        with self.assertRaises(PremiumRigError):validate_performance(spec,STORY)
    def test_missing_actor(self):
        spec=deepcopy(SPEC);spec["performance_timeline"][1]["actor"]="unknown"
        with self.assertRaises(PremiumRigError):validate_performance(spec,STORY)
    def test_fake_approved_audio(self):
        spec=deepcopy(SPEC);spec["characters"][0]["performance_audio_status"]="approved"
        with self.assertRaises(PremiumRigError):validate_performance(spec,STORY)
    def test_wrong_camera(self):
        spec=deepcopy(SPEC);spec["camera"]["move"]="static_slide"
        with self.assertRaises(PremiumRigError):validate_performance(spec,STORY)
    def test_no_self_art_qa(self):
        spec=deepcopy(SPEC);spec["artistic_review"]=True
        with self.assertRaises(PremiumRigError):validate_performance(spec,STORY)
    def test_real_3d_required(self):
        story=deepcopy(STORY);story["shots"][0]["mode"]="motion_2d"
        with self.assertRaises(PremiumRigError):validate_performance(SPEC,story)

if __name__=="__main__":
    unittest.main()
