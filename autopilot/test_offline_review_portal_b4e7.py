"""B4e7 all-local owner portal: strict video file list, no networks or approval."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import autopilot.manual_rehearsal_review_export_b4e3 as export
from autopilot.offline_review_portal_b4e7 import build_portal, PORTAL_FILE
from autopilot.review_worksheet_validator_b4e6 import ReviewValidationError
from autopilot.test_manual_rehearsal_review_export_b4e3 import qa_and_three_original_mp4s


class OfflinePortalTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.root=Path(self.temp.name)/"unapproved-three-original-mp4"
        self.target=Path(self.temp.name)/"review-only"
        self.root.mkdir()
        self.qa=qa_and_three_original_mp4s(self.root)
        self.scope=patch.multiple(export,ROOT=self.root,TARGET=self.target)
        self.scope.start()

    def tearDown(self):
        self.scope.stop()
        self.temp.cleanup()

    def package(self):
        manifest=export.prepare_review_export(self.root,self.target,self.qa)
        worksheet=json.loads((self.target/"HUMAN_REVIEW_WORKSHEET_UNFILLED.json").read_text())
        return manifest,worksheet

    def test_full_three_video_local_review_page_ships_with_exact_sha(self):
        manifest,worksheet=self.package()
        path=self.target/PORTAL_FILE
        self.assertEqual(PORTAL_FILE,"OPEN_LOCAL_REVIEW_DASHBOARD.html")
        self.assertTrue(path.is_file())
        html=path.read_text()
        self.assertEqual(html.count("<video controls"),3)
        for video in manifest["videos"]:
            self.assertIn('src="'+video["file"]+'"',html)
            self.assertIn(video["sha256"],html)
        self.assertIn("0 / 47 assessments",html)
        self.assertIn("NOT FOR PUBLISHING",html)
        self.assertIn("Download my local review JSON",html)
        self.assertIn("review_worksheet_validator_b4e6",html)

    def test_strict_no_remote_js_or_upload_endpoints(self):
        self.package()
        html=(self.target/PORTAL_FILE).read_text()
        for forbidden in (
            "https://","http://","fetch(","XMLHttpRequest","navigator.sendBeacon",
            "<iframe","<form","<link","<img","import(","type=\"module\"",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,html)
        self.assertIn("connect-src 'none'",html)
        self.assertIn("media-src 'self' file:",html)
        self.assertIn('data.human_review_completed=false',html)
        self.assertIn('data.youtube_publish_authorized=false',html)

    def test_all_17_scenes_and_30_checks_stay_initially_blank(self):
        manifest,worksheet=self.package()
        html=build_portal(manifest,worksheet)
        self.assertEqual([len(v["scenes"]) for v in worksheet["videos"]],[4,9,4])
        for v in worksheet["videos"]:
            self.assertEqual(len(v["checks"]),10)
            self.assertTrue(all(x=="NOT_REVIEWED" for x in v["checks"].values()))
            self.assertEqual(v["overall_human_decision"],"NOT_REVIEWED")
        self.assertIn("self-reported; not authenticated",html)
        self.assertFalse(manifest["publishing_authorized"])

    def test_manifest_tamper_or_release_flag_is_rejected(self):
        manifest,worksheet=self.package()
        altered=deepcopy(worksheet)
        altered["videos"][0]["sha256"]="a"*64
        with self.assertRaises(ReviewValidationError):build_portal(manifest,altered)
        altered=deepcopy(worksheet)
        altered["rights_approved"]=True
        with self.assertRaises(ReviewValidationError):build_portal(manifest,altered)
        altered=deepcopy(worksheet)
        altered["videos"][0]["scenes"][0].update(
            review_status="PASS",timecode_mm_ss="00:01")
        with self.assertRaises(ReviewValidationError):build_portal(manifest,altered)

    def test_script_json_escapes_injected_html_delimiter(self):
        manifest,worksheet=self.package()
        worksheet["instructions"]="</script><script>bad()</script>"
        html=build_portal(manifest,worksheet)
        self.assertNotIn("<script>bad()",html)
        self.assertIn(r"\u003c/script\u003e",html)
        self.assertEqual(html.count("</script>"),2)

    def test_packager_preserves_only_known_safe_files(self):
        self.package()
        self.assertEqual(set(x.name for x in self.target.iterdir()),{
            name for _,name,_ in export.SLOT_NAMES
        }|{"READ_ME_FIRST.txt","REVIEW_ONLY_NO_PUBLISH.json",
           "HUMAN_REVIEW_WORKSHEET_UNFILLED.json",PORTAL_FILE})


if __name__=="__main__":
    unittest.main()
