"""Adversarial source-only tests: no browser, personal profile or upload."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from autopilot.branch1_real_app_capture import (
    APPS, STATUS, CAPTURE, PREVIEW, RECEIPT, plan,
    validate_main_only, verify_receipt, perform_real_storyboard,
    FORMULA_WALKTHROUGH, CHROME_GUIDED_OPERATIONS,
)
from autopilot.branch1_recovery import RecoveryRefused, validate_creative

def good_env():
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": "Tirthanand17/taskless-lab",
        "GITHUB_REF": "refs/heads/main",
        "PUBLISH_ENABLED": "false",
        "FLOWMINUTE_ENABLE_PUBLISH": "0",
        "FLOWMINUTE_ALLOW_LAPTOP": "0",
    }

def demo_observation(app):
    if app=="calc":
        return {
            "application": "LibreOffice Calc",
            "before_formula": "=A2=A3",
            "before_boolean": False,
            "after_formula": "=TRIM(A2)=TRIM(A3)",
            "after_boolean": True,
            "source_fixture_only": True,
            "real_uno_calculation": True,
            "youtube_uploads": 0,
        }
    return {
        "application":"Chromium browser",
        "real_browser_find_used":True,
        "sample_log_rows":780,
        "sample_error_matches":12,
        "observed_unique_scroll_areas":8,
        "first_party_fictional_file":True,
        "external_site_used":False,
        "permissions_changed":False,
        "personal_profile_used":False,
        "youtube_uploads":0,
    }

def fake_receipt(app,out):
    # A source-free test receipt: byte identity only. It must NOT be treated
    # as proof a real vendor application was actually operated.
    observation=out/"application_observation.json"
    observation.write_text(json.dumps(demo_observation(app)),encoding="utf8")
    fixture=observation
    if app=="calc":
        fixture=out/"ACTUAL_CALC_VALIDATED.ods"
        with zipfile.ZipFile(fixture,"w") as zipped:
            zipped.writestr("content.xml", "<office:document/>")
            zipped.writestr("mimetype","application/vnd.oasis.opendocument.spreadsheet")
    else:
        fixture=out/"ORIGINAL_DUMMY_FIND_LOG.html"
        lines=[
            '<div class="line normal">Line %04d INFO: fictional test-step finished</div>' % i
            if i%61 else
            '<div class="line issue">Line %04d ERROR: fictional test-step failed</div>' % i
            for i in range(1,781)]
        fixture.write_text("FICTIONAL LOG / 780 ROWS\n"+"".join(lines),"utf8")
    for name in (CAPTURE,PREVIEW):
        (out/name).write_bytes(b"\x00\x00\x00\x18ftypisom"+b"X"*38000)
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    receipt={
        "schema":"FLOWMINUTE_B1_REAL_APPLICATION_PROOF_V1",
        "status":STATUS,
        "app":app,
        "episode_id":APPS[app][1],
        "real_application":APPS[app][0],
        "capture_method":APPS[app][3],
        "capture_sha256":digest(out/CAPTURE),
        "capture_bytes":(out/CAPTURE).stat().st_size,
        "preview_sha256":digest(out/PREVIEW),
        "fixture_proof_sha256":digest(fixture),
        "observation_sha256":digest(observation),
        "real_application_executed":True,
        "first_party_dummy_data":True,
        "no_personal_accounts":True,
        "owner_release_approved":False,
        "youtube_uploads":0,
        "youtube_schedules":0,
    }
    (out/RECEIPT).write_text(json.dumps(receipt),encoding="utf8")
    return receipt

class RealAppAdapterTests(unittest.TestCase):
    def test_creative_plan_both_fully_source_free_and_unapproved(self):
        for app in APPS:
            with self.subTest(app=app):
                b,proof=plan(app)
                self.assertEqual(b["demo"]["application"], APPS[app][0])
                self.assertLessEqual(proof["opening_proof_by_seconds"],2)
                self.assertLessEqual(proof["first_real_action_at_seconds"],3)
                self.assertFalse(proof["owner_approval"])
                self.assertEqual(proof["youtube_uploads"],0)
                self.assertEqual(len(b["beats"]),6)

    def test_real_calc_formula_steps_are_distinct_and_factually_limited(self):
        self.assertEqual(len(FORMULA_WALKTHROUGH),5)
        for chapter in FORMULA_WALKTHROUGH:
            self.assertEqual(len(chapter),6)
            self.assertEqual(len(set(chapter)),6)
            for item in chapter:
                self.assertGreaterEqual(len(item),8)
                self.assertLessEqual(len(item),18)
                self.assertNotIn("MICROSOFT EXCEL",item)
                self.assertNotIn("SUBSCRIBE",item)
        self.assertIn("B2 SHOWS FALSE",FORMULA_WALKTHROUGH[4])
        self.assertIn("B3 SHOWS TRUE",FORMULA_WALKTHROUGH[4])
        self.assertIn("LEN OF A2",FORMULA_WALKTHROUGH[2])
        self.assertIn("TRIM INPUT A3",FORMULA_WALKTHROUGH[3])

    def test_calc_actual_sheet_labels_fit_without_hiding_worksheet_evidence(self):
        # A real-source readability regression check; screenshots still
        # require an independent phone-size human/vision review.
        import re
        source=(Path(__file__).parent/"branch1_real_app_capture.py").read_text("utf8")
        labels=re.findall(r'lambda: cell\("A1","([^"]+)"\)',source)
        self.assertEqual(len(labels),4)
        self.assertTrue(all(len(label)<=18 for label in labels))
        self.assertIn('sheet.getCellRangeByName("A1").String="RESULT: TRUE"',source)
        self.assertIn('sheet.Columns.getByIndex(0).Width=4400',source)
        self.assertIn('sheet.Columns.getByIndex(1).Width=4200',source)
        for outdated in ("RESULT: TWO TEXT LABELS NOW MATCH",
                         "BEFORE: ALMOST IDENTICAL TEXT",
                         "CAUSE: EXTRA SPACES CHANGE MATCH",
                         "AFTER: REAL FORMULA RETURNS TRUE"):
            self.assertNotIn(outdated,source)

    def test_chrome_native_find_on_original_data_not_repeated_radio_setting(self):
        chapters=CHROME_GUIDED_OPERATIONS
        self.assertEqual(len(chapters),3)
        self.assertTrue(all(len(chapter)==6 for chapter in chapters))
        allowed={"find_next","close_find","home","scroll_down","open_find"}
        self.assertTrue(all(op in allowed for ch in chapters for op in ch))
        self.assertEqual(chapters[0][-2:],("close_find","home"))
        self.assertEqual(chapters[1],("scroll_down",)*6)
        self.assertEqual(chapters[2][0],"open_find")
        self.assertEqual(chapters[2][1:],("find_next",)*5)
        self.assertNotIn("notifications",str(chapters).lower())
        self.assertNotIn("https:",str(chapters).lower())
        observation=demo_observation("chrome")
        self.assertTrue(observation["real_browser_find_used"])
        self.assertEqual(observation["sample_log_rows"],780)
        self.assertEqual(observation["sample_error_matches"],12)
        self.assertTrue(observation["first_party_fictional_file"])
        self.assertFalse(observation["external_site_used"])
        self.assertFalse(observation["personal_profile_used"])

    def test_chrome_real_find_source_and_runner_only(self):
        source=(Path(__file__).parent/"branch1_real_app_capture.py").read_text("utf8")
        self.assertIn("CHROME_NATIVE_FIND_DID_NOT_REACH_REAL_MATCH",source)
        self.assertIn("CHROME_FIND_NEVER_MOVED_THROUGH_REAL_LOG",source)
        self.assertIn('file_uri.startswith("file:///")',source)
        self.assertIn("ORIGINAL_DUMMY_FIND_LOG.html",source)
        self.assertIn('seconds_per_chapter=8.0,total_seconds=25.0',source)
        self.assertIn('"48" if app=="calc" else "26"',source)
        self.assertIn('for chapter in range(5 if app=="calc" else 3)',source)
        self.assertIn("CHROME_ORIGINAL_LOG_CONTENT_NOT_VERIFIED",source)
        self.assertIn("REAL_CHROME_FIND_OBSERVATION_NOT_PROVED",source)
        self.assertNotIn("CHROME_ORIGINAL_NOTIFICATION_DEFAULT_NOT_READABLE",source)
        self.assertNotIn("selenium_chrome_settings_actual",source)

    def test_real_five_chapter_storyboard_requires_running_recorder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            clock=[0.0]
            seen=[]
            def monotonic():
                return clock[0]
            def sleep(seconds):
                clock[0]+=max(0.0,float(seconds))
            chapters=[
                [(lambda chapter=i,step=j:seen.append((chapter,step)))
                 for j in range(6)]
                for i in range(5)
            ]
            with patch("autopilot.branch1_real_app_capture.time.monotonic",monotonic):
                with patch("autopilot.branch1_real_app_capture.time.sleep",sleep):
                    with self.assertRaises(RecoveryRefused):
                        perform_real_storyboard(root,chapters)
                    self.assertEqual(seen,[])
                    (root/"capture_started").write_text("RUNNING\n","utf8")
                    perform_real_storyboard(root,chapters)
            self.assertEqual(len(seen),30)
            self.assertEqual(seen[0],(0,0))
            self.assertEqual(seen[-1],(4,5))
            self.assertGreaterEqual(clock[0],76.0)
            for n in range(5):
                self.assertTrue((root/f"real_stage_{n}").is_file())

    def test_genuine_app_steps_extend_across_entire_visible_chapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"capture_started").write_text("RECORDING_IS_RUNNING","utf8")
            clock=[0.0]
            events=[]
            def monotonic():
                return clock[0]
            def sleep(seconds):
                clock[0]+=max(0.0,float(seconds))
            chapters=[
                [(lambda chapter=ch,step=step:
                    events.append((chapter,step,clock[0])))
                 for step in range(6)]
                for ch in range(5)
            ]
            with patch("autopilot.branch1_real_app_capture.time.monotonic",monotonic):
                with patch("autopilot.branch1_real_app_capture.time.sleep",sleep):
                    perform_real_storyboard(root,chapters)
            self.assertEqual(len(events),30)
            for chapter in range(5):
                real=[event[2] for event in events if event[0]==chapter]
                self.assertGreaterEqual(real[-1]-real[0],7.4)
                self.assertLessEqual(real[-1]-real[0],7.6)
                self.assertLess(real[-1],chapter*9.0+8.5)
                for prev,nxt in zip(real,real[1:]):
                    self.assertAlmostEqual(nxt-prev,1.5,delta=.15)
            self.assertGreaterEqual(clock[0],46)

    def test_early_real_application_failure_reports_bounded_python_traceback(self):
        from autopilot.branch1_real_app_capture import wait_for
        from io import StringIO
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as d:
            proc=SimpleNamespace(
                poll=lambda: 7,
                returncode=7,
                stderr=StringIO("Traceback: REAL_CHROME_RADIO_NOT_FOUND"))
            with self.assertRaisesRegex(RecoveryRefused,
                    "REAL_CHROME_RADIO_NOT_FOUND"):
                wait_for(Path(d)/"never_created_before_capture",proc,timeout=1)

    def test_main_only_never_auto_run_with_privileged_or_laptop_context(self):
        for app in APPS:
            validate_main_only(good_env(),app)
            for key, bad in (
                ("GITHUB_ACTIONS","false"),
                ("GITHUB_REPOSITORY","other/other"),
                ("GITHUB_REF","refs/pull/123/merge"),
                ("GITHUB_REF","refs/heads/feature/unsafe"),
                ("PUBLISH_ENABLED","true"),
                ("FLOWMINUTE_ENABLE_PUBLISH","1"),
                ("FLOWMINUTE_ALLOW_LAPTOP","1"),
            ):
                with self.subTest(app=app,key=key):
                    env={**good_env(),key:bad}
                    with self.assertRaises(RecoveryRefused):
                        validate_main_only(env,app)
        with self.assertRaises(RecoveryRefused):
            validate_main_only(good_env(),"arbitrary")

    def test_receipt_rejects_changes_in_media_and_fake_permission(self):
        for app in APPS:
            with tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)
                original=fake_receipt(app,folder)
                b,_=plan(app)
                result=verify_receipt(b,folder)
                self.assertEqual(result["youtube_uploads"],0)
                self.assertEqual(result["status"],
                                 "HASH_BOUND_REVIEW_ONLY_NOT_MEDIA_APPROVAL")
                for name, bad in (
                    ("owner_release_approved",True),
                    ("youtube_schedules",1),
                    ("youtube_uploads",1),
                    ("real_application","Google Chrome" if app=="calc" else "Firefox"),
                    ("capture_method","screenshot_stub"),
                    ("no_personal_accounts",False),
                    ("first_party_dummy_data",False),
                    ("app","another_app"),
                    ("episode_id","wrong_episode"),
                    ("capture_sha256","0"*64),
                ):
                    with self.subTest(app=app,name=name):
                        data={**original,name:bad}
                        (folder/RECEIPT).write_text(json.dumps(data),"utf8")
                        with self.assertRaises(RecoveryRefused):
                            verify_receipt(b,folder)
                (folder/RECEIPT).write_text(json.dumps(original),"utf8")
                clip=folder/CAPTURE
                clip.write_bytes(clip.read_bytes()+b"changed")
                with self.assertRaises(RecoveryRefused):
                    verify_receipt(b,folder)
                clip.write_bytes(clip.read_bytes()[:-7])
                preview=folder/PREVIEW
                preview.write_bytes(preview.read_bytes()[:-1])
                with self.assertRaises(RecoveryRefused):
                    verify_receipt(b,folder)

    def test_real_ui_observation_not_simple_success_flag(self):
        for app in APPS:
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)
                original=fake_receipt(app,out)
                b,_=plan(app)
                observations = [
                    {"youtube_uploads":0,"application":APPS[app][0]},
                    {**demo_observation(app),"youtube_uploads":1},
                    {**demo_observation(app),"application":"fake simulated screenshot"},
                ]
                if app=="calc":
                    observations += [
                        {**demo_observation(app),"after_boolean":False},
                        {**demo_observation(app),"real_uno_calculation":False},
                    ]
                else:
                    observations += [
                        {**demo_observation(app),"real_browser_find_used":False},
                        {**demo_observation(app),"sample_log_rows":779},
                        {**demo_observation(app),"sample_error_matches":11},
                        {**demo_observation(app),"observed_unique_scroll_areas":2},
                        {**demo_observation(app),"first_party_fictional_file":False},
                        {**demo_observation(app),"external_site_used":True},
                        {**demo_observation(app),"permissions_changed":True},
                        {**demo_observation(app),"personal_profile_used":True},
                    ]
                for obs in observations:
                    with self.subTest(app=app,observation=obs):
                        path=out/"application_observation.json"
                        path.write_text(json.dumps(obs),"utf8")
                        new={**original,"observation_sha256":
                             hashlib.sha256(path.read_bytes()).hexdigest()}
                        (out/RECEIPT).write_text(json.dumps(new),"utf8")
                        with self.assertRaises(RecoveryRefused):
                            verify_receipt(b,out)

    def test_reject_mismatched_creative_brief_even_if_receipt_matches(self):
        for app in APPS:
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)
                fake_receipt(app,out)
                b,_=plan(app)
                forged=copy.deepcopy(b)
                forged["demo"]["application"]=(
                    "Chromium browser" if app=="calc" else "LibreOffice Calc")
                with self.assertRaises(RecoveryRefused):
                    verify_receipt(forged,out)
                forged=copy.deepcopy(b)
                forged["approval"]["release_signed"]=True
                with self.assertRaises(RecoveryRefused):
                    verify_receipt(forged,out)

if __name__=="__main__":
    unittest.main()
