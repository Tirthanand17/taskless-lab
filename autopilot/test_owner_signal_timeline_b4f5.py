"""B4f5 adversarial SHA-bound final-MP4 warning timeline and offline playback."""
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import autopilot.manual_rehearsal_review_export_b4e3 as export
from autopilot.test_manual_rehearsal_review_export_b4e3 import qa_and_three_original_mp4s
from autopilot.test_rehearsal_encoded_signal_review_b4f4 import LOG
from autopilot.rehearsal_encoded_signal_review_b4f4 import (
    inspect_review_directory, REPORT_NAME,
)
from autopilot.owner_signal_timeline_b4f5 import (
    TimelineRefused, STATUS, validate_signal_timeline,
    annotate_existing_owner_player,
)
from autopilot.offline_review_portal_b4e7 import PORTAL_FILE,build_portal


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.root=Path(self.temp.name)/"source-three-mp4"
        self.folder=Path(self.temp.name)/"owner-review-three-original"
        self.root.mkdir()
        qa=qa_and_three_original_mp4s(self.root)
        self.scope=patch.multiple(export,ROOT=self.root,TARGET=self.folder)
        self.scope.start()
        self.manifest=export.prepare_review_export(self.root,self.folder,qa)
        self.worksheet=json.loads(
            (self.folder/"HUMAN_REVIEW_WORKSHEET_UNFILLED.json").read_text())
        def fake_runner(argv,**kwargs):
            return type("Result", (), {"returncode":0,"stderr":LOG})()
        self.diag=inspect_review_directory(
            self.folder,ffmpeg="/mock-binary-ffmpeg",runner=fake_runner)
        (self.folder/REPORT_NAME).write_text(json.dumps(self.diag,indent=2)+"\n")

    def tearDown(self):
        self.scope.stop()
        self.temp.cleanup()

    def test_canonical_three_video_diagnostics_bind_to_original_hashes(self):
        timeline=validate_signal_timeline(self.manifest,self.worksheet,self.diag)
        self.assertEqual(timeline["status"],STATUS)
        self.assertEqual([r["slot"] for r in timeline["videos"]],
                         ["short_am","long","short_pm"])
        self.assertEqual([len(x["seek_hints"]) for x in timeline["videos"]],
                         [3,3,3])
        self.assertTrue(all(x["sha256"]==y["sha256"]
                            for x,y in zip(timeline["videos"],
                                           self.manifest["videos"])))
        self.assertTrue(timeline["no_warning_is_not_human_approval"])
        self.assertTrue(timeline["technical_signal_not_semantic_spinner_detector"])
        self.assertFalse(timeline["youtube_release_authorized"])
        self.assertEqual(timeline["human_full_watches"],0)

    def test_tampered_source_sha_channel_and_scene_order_are_refused(self):
        for key,value in (
            ("source_mp4_sha256","f"*64),
            ("slot","short_pm"),
            ("original_voiced_scene_count",99),
            ("measured_pcm_seconds",20),
        ):
            wrong=deepcopy(self.diag)
            wrong["videos"][0][key]=value
            with self.subTest(key=key),self.assertRaises(TimelineRefused):
                validate_signal_timeline(self.manifest,self.worksheet,wrong)

    def test_release_forgery_and_missing_signed_review_flag_fail_closed(self):
        for key,value in (
            ("status","PUBLISH_READY"),
            ("human_full_video_reviews",3),
            ("factual_and_rights_approvals",1),
            ("youtube_uploads_or_release_authority",1),
            ("warnings_require_real_owner_playback",False),
        ):
            wrong=deepcopy(self.diag)
            wrong[key]=value
            with self.subTest(key=key),self.assertRaises(TimelineRefused):
                validate_signal_timeline(self.manifest,self.worksheet,wrong)
        wrong=deepcopy(self.diag)
        wrong["videos"][0]["human_full_audio_visual_watch_completed"]=True
        with self.assertRaises(TimelineRefused):
            validate_signal_timeline(self.manifest,self.worksheet,wrong)

    def test_forbidden_interval_range_sort_and_warning_code_escalation(self):
        alterations=(
            lambda v:v["black_intervals"][0].update(start_seconds=-1),
            lambda v:v["black_intervals"][0].update(end_seconds=9999),
            lambda v:v["freeze_intervals"][0].update(duration_seconds=80),
            lambda v:v["audio_silence_intervals"][0].update(
                start_seconds=float("nan")),
            lambda v:v["black_intervals"].append(
                {"start_seconds":0,"end_seconds":0.8,"duration_seconds":0.8}),
            lambda v:v.update(warning_codes=["PUBLISH_ALLOWED"]),
            lambda v:v.update(warning_codes=[]),
            lambda v:v.update(sample_peak_dbfs_not_true_peak=float("inf")),
        )
        for edit in alterations:
            wrong=deepcopy(self.diag)
            edit(wrong["videos"][0])
            with self.subTest(edit=repr(edit)),self.assertRaises(TimelineRefused):
                validate_signal_timeline(self.manifest,self.worksheet,wrong)

    def test_report_with_no_warning_still_not_approval(self):
        clean=deepcopy(self.diag)
        for row in clean["videos"]:
            for field in ("black_intervals","freeze_intervals",
                          "audio_silence_intervals"):
                row[field]=[]
            row["warning_codes"]=[]
        t=validate_signal_timeline(self.manifest,self.worksheet,clean)
        self.assertTrue(all(not row["seek_hints"] for row in t["videos"]))
        self.assertEqual(t["human_full_watches"],0)
        self.assertFalse(t["youtube_release_authorized"])

    def test_atomic_annotation_contains_seek_buttons_and_no_autoplay(self):
        result=annotate_existing_owner_player(self.folder)
        self.assertEqual(result["seekable_warning_count"],9)
        self.assertFalse(result["owner_review_completed"])
        html=(self.folder/PORTAL_FILE).read_text()
        self.assertIn('id="signal-data"',html)
        self.assertEqual(html.count("</script>"),3)
        self.assertEqual(html.count("<video controls"),3)
        self.assertIn('addSignalReview(section,player,i);',html)
        self.assertIn('button.textContent="Seek "',html)
        self.assertIn('player.currentTime=',html)
        self.assertIn('player.pause();player.focus();',html)
        self.assertNotIn('player.play(',html)
        self.assertNotIn("fetch(",html)
        self.assertIn("connect-src 'none'",html)
        self.assertIn("NOT FOR PUBLISHING",html)
        self.assertIn("0 / 47 assessments",html)
        self.assertIn('data.youtube_publish_authorized=false',html)
        for row in self.manifest["videos"]:
            self.assertIn(row["sha256"],html)
        for extra in ("READ_ME_FIRST.txt","REVIEW_ONLY_NO_PUBLISH.json",
                      "HUMAN_REVIEW_WORKSHEET_UNFILLED.json"):
            self.assertTrue((self.folder/extra).is_file())
        self.assertFalse((self.folder/(PORTAL_FILE+".tmp")).exists())

    def test_second_annotation_and_edited_dashboard_rejected(self):
        annotate_existing_owner_player(self.folder)
        with self.assertRaises(TimelineRefused):
            annotate_existing_owner_player(self.folder)
        # Must not silently overwrite a customized/tampered review HTML.
        (self.folder/PORTAL_FILE).write_text("replaced HTML page")
        with self.assertRaises(TimelineRefused):
            annotate_existing_owner_player(self.folder)

    def test_modified_final_mp4_sha_fails_before_html_write(self):
        original=(self.folder/PORTAL_FILE).read_text()
        target=self.folder/export.SLOT_NAMES[2][1]
        target.write_bytes(b"x"*target.stat().st_size)
        with self.assertRaises(TimelineRefused):
            annotate_existing_owner_player(self.folder)
        self.assertEqual((self.folder/PORTAL_FILE).read_text(),original)

    def test_extra_js_payload_rejected_in_warning_codes(self):
        evil=deepcopy(self.diag)
        evil["videos"][1]["warning_codes"].append(
            "</script><script>evil()</script>")
        with self.assertRaises(TimelineRefused):
            validate_signal_timeline(self.manifest,self.worksheet,evil)

    def test_genuine_blank_dossier_portal_still_works_before_annotation(self):
        original=build_portal(self.manifest,self.worksheet)
        self.assertNotIn('id="signal-data"',original)
        self.assertIn("Technical warnings not yet attached",original)
        self.assertEqual(original.count("</script>"),2)
        self.assertIn('data.human_review_completed=false',original)

    @unittest.skipUnless(shutil.which("node"), "Node JS not installed")
    def test_offline_review_script_javascript_parses_on_real_node(self):
        annotate_existing_owner_player(self.folder)
        html=(self.folder/PORTAL_FILE).read_text()
        scripts=re.findall(r"<script(?:\s[^>]*)?>([\s\S]*?)</script>",html)
        self.assertEqual(len(scripts),3)
        # First two are JSON data, third is the real browser program.
        script=self.folder/"offline-review-code-only.js"
        script.write_text(scripts[-1],encoding="utf8")
        try:
            check=subprocess.run(
                ["node","--check",str(script)],capture_output=True,text=True,timeout=10)
            self.assertEqual(check.returncode,0,check.stderr[:1000])
        finally:
            script.unlink()


if __name__=="__main__":
    unittest.main()
