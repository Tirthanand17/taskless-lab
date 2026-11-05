"""B1q8 synthetic offline proof for exact arc source rewrite and SHA gates.

No video owners, OAuth, media files, YouTube IDs or unreleased scripts are
fetched in this public CI. Native media review is a separate, gated stage.
"""
from __future__ import annotations

from hashlib import sha256
import unittest

from autopilot.branch1_legacy_arc_remediation_v7 import (
    remove_verified_central_arc, verify_original_master_against_receipt,
    safe_slot_counts, SourceRepairRejected,
    SCHEDULED_ARC_SLOTS_IST, OTHER_RENDERER_SLOTS_IST, STATUS, EXPECTED_CHANNEL,
)

OLD_SOURCE=(
    "def render_scene(i,p,t):\n"
    "    im=IMAGES[i].copy()\n"
    "    d=ImageDraw.Draw(im)\n"
    "    c=m.accent_colors[SCENES[i]['accent']]\n"
    "    phase=.5+.5*math.sin(t*7)\n"
    "    d.arc((242,573,480,801),int(15+130*phase),int(155+130*phase),fill=c,width=5)\n"
    "    d.line((53,1216,53+int(614*min(1,t/TOTAL)),1216),fill=c,width=8)\n"
    "    return im\n"
    "def main():\n"
    "    original_sound();write_captions();m.draw_core=render_scene\n"
    "    motion=m.render_video()\n"
    "    # Media and schedule mutation are outside this pure function.\n"
)


class ExactOriginalMasterGuard(unittest.TestCase):
    def test_exact_rolling_arc_removed_without_any_other_edit(self):
        corrected, receipt=remove_verified_central_arc(OLD_SOURCE)
        self.assertEqual(receipt["status"],STATUS)
        self.assertNotIn("d.arc(",corrected)
        self.assertNotIn("math.sin(t*7)",corrected)
        self.assertIn("one-shot camera",corrected)
        self.assertIn("d.line((53,1216,53+int(614*min(1,t/TOTAL)),1216)",corrected)
        self.assertIn("m.draw_core=render_scene",corrected)
        self.assertIn("original_sound();write_captions();",corrected)
        self.assertNotEqual(corrected,OLD_SOURCE)
        self.assertEqual(receipt["source_sha256_before"],
                         sha256(OLD_SOURCE.encode()).hexdigest())
        self.assertEqual(receipt["patched_source_sha256"],
                         sha256(corrected.encode()).hexdigest())
        for key in (
            "original_youtube_upload_modified",
            "youtube_video_edited_or_rescheduled",
            "new_video_uploaded",
            "new_video_owner_approved",
            "exact_narration_or_captions_modified",
        ):
            self.assertFalse(receipt[key])

    def test_CRLF_original_source_remains_CRLF(self):
        source=OLD_SOURCE.replace("\n","\r\n")
        edited,_=remove_verified_central_arc(source)
        self.assertNotIn("\n",edited.replace("\r\n",""))
        self.assertNotIn("d.arc(",edited)
        self.assertIn("\r\n",edited)

    def test_idempotent_double_patch_never_mutates_twice(self):
        edited,_=remove_verified_central_arc(OLD_SOURCE)
        with self.assertRaises(SourceRepairRejected):
            remove_verified_central_arc(edited)

    def test_reject_changed_arc_coords_missing_motion_or_multiple_rings(self):
        variants=(
            OLD_SOURCE.replace("242,573,480,801","241,573,480,801"),
            OLD_SOURCE.replace("int(15+130*phase)","int(30+130*phase)"),
            OLD_SOURCE.replace("m.draw_core=render_scene","m.draw_core=other"),
            OLD_SOURCE.replace("def render_scene(i,p,t):","def render_images(i,p,t):"),
            OLD_SOURCE.replace("d.arc((242,573,480,801),","d.arc((242,574,480,801),"),
            OLD_SOURCE.replace("    return im","    d.arc((0,0,50,50),5,130,fill=c)\n    return im"),
            OLD_SOURCE.replace("d.line((53,1216,53+int(614*min(1,t/TOTAL)),1216)",
                               "d.line((53,1216,53+int(900*min(1,t/TOTAL)),1216)"),
            OLD_SOURCE+OLD_SOURCE,
        )
        for case in variants:
            with self.subTest(case=case[:35]),self.assertRaises(SourceRepairRejected):
                remove_verified_central_arc(case)

    def test_full_original_media_sha_matches_both_qa_and_youtube_receipt(self):
        blob=b"SYNTHETIC-MASTER-NOT-PRODUCTION-OR-PUBLISHED"
        digest=sha256(blob).hexdigest()
        qa={"sha256":digest,"full_media_decode_passed":True}
        receipt={"video_sha256":digest,"channel_id":EXPECTED_CHANNEL,
                 "human_full_watch_attested":False}
        outcome=verify_original_master_against_receipt(blob,qa,receipt)
        self.assertEqual(outcome["original_mp4_sha256"],digest)
        self.assertTrue(outcome["local_original_master_matches_recorded_youtube_receipt"])
        self.assertFalse(outcome["original_youtube_video_changed"])
        self.assertFalse(outcome["new_replacement_media_prepared"])
        for bad_qa,bad_rc in (
            ({"sha256":"0"*64,"full_media_decode_passed":True},receipt),
            (qa,dict(receipt,video_sha256="f"*64)),
            (qa,dict(receipt,channel_id="UC_WRONG")),
            (dict(qa,full_media_decode_passed=False),receipt),
        ):
            with self.assertRaises(SourceRepairRejected):
                verify_original_master_against_receipt(blob,bad_qa,bad_rc)

    def test_11_arc_sources_2_different_13_future_shorts_21_schedule(self):
        observed=safe_slot_counts()
        self.assertEqual(observed["owner_uploads_scanned_at_observation"],89)
        self.assertEqual(observed["remaining_private_scheduled_at_observation"],19)
        self.assertEqual(observed["already_published_nov05_at_observation"],2)
        self.assertEqual(observed["remaining_private_shorts_at_observation"],13)
        self.assertEqual(observed["exact_source_arc_and_master_receipt_matched"],11)
        self.assertEqual(len(SCHEDULED_ARC_SLOTS_IST),11)
        self.assertEqual(len(OTHER_RENDERER_SLOTS_IST),2)
        self.assertTrue(set(SCHEDULED_ARC_SLOTS_IST).isdisjoint(OTHER_RENDERER_SLOTS_IST))
        self.assertFalse(observed["automatic_new_upload_or_old_scheduled_delete"])
        self.assertFalse(observed["live_automatic_authorized_youtube_write"])
        self.assertNotIn(EXPECTED_CHANNEL,str(observed))


if __name__=="__main__":
    unittest.main()
