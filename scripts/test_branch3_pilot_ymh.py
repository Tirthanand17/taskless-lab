"""YMH Ep. 347 pilot must stay a non-publishing research treatment."""
from __future__ import annotations
import copy
import json
import unittest

from scripts.branch3_validate_pilot_ymh import (PILOT,STATE,PERMISSIONS,
    PilotNotReady,verify_source_free_pilot)

class TestYmhPilotSafety(unittest.TestCase):
    def setUp(self):
        self.p=json.loads(PILOT.read_text("utf8"))
        self.s=json.loads(STATE.read_text("utf8"))
        self.perms=json.loads(PERMISSIONS.read_text("utf8"))

    def test_valid_source_free_treatment(self):
        verify_source_free_pilot(self.p,self.s,self.perms)

    def test_missing_or_fabricated_approval_flags_rejected(self):
        for field in ("full_ymh_campaign_rules_reviewed",
            "participant_eligibility_verified",
            "content_rewards_17_6_assignment_acknowledged","commercial_scope_verified",
            "source_episode_watched_in_context","final_render_approved"):
            p=copy.deepcopy(self.p)
            p["required_gates"][field]=True
            with self.subTest(field=field),self.assertRaises(PilotNotReady):
                verify_source_free_pilot(p,self.s,self.perms)

    def test_media_and_upload_fail_closed(self):
        for field in ("file_generation_allowed","third_party_media_download_allowed",
                      "ready_to_upload","ready_to_publish"):
            p=copy.deepcopy(self.p)
            p[field]=True
            with self.subTest(field=field),self.assertRaises(PilotNotReady):
                verify_source_free_pilot(p,self.s,self.perms)

    def test_wrong_channel_or_unverified_phone_rejected(self):
        s=copy.deepcopy(self.s)
        s["channel_id"]="UCCcL9Q_jqVq6LJmnYUSAFZA"
        with self.assertRaises(PilotNotReady):
            verify_source_free_pilot(self.p,s,self.perms)
        s=copy.deepcopy(self.s)
        s["channel_settings"]["intermediate_features"]="eligible_not_yet_enabled"
        with self.assertRaises(PilotNotReady):
            verify_source_free_pilot(self.p,s,self.perms)

    def test_no_invented_source_or_transcript(self):
        for key,val in (("original_video_id","invalid12345"),
                        ("original_video_url","https://youtu.be/notthis"),
                        ("episode_number",345)):
            p=copy.deepcopy(self.p)
            p["candidate_source"][key]=val
            with self.assertRaises(PilotNotReady):
                verify_source_free_pilot(p,self.s,self.perms)
        p=copy.deepcopy(self.p)
        p["research_window"]["transcript_verified"]=True
        with self.assertRaises(PilotNotReady):
            verify_source_free_pilot(p,self.s,self.perms)

if __name__=="__main__":
    unittest.main()
