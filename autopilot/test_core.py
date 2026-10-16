import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from autopilot.core import (
    CHANNEL_ID, GateError, MediaQA, Provider, ProviderRouter, ReleaseLedger,
    Stage, Topic, require_future, slot_utc
)

FUTURE = datetime(2026,10,14,tzinfo=timezone.utc)
HASH = "a"*64
def good_qa():
    return MediaQA(HASH,43.0,41.0,1080,1920,-2,True,True,True,True,True)

def receipt(time="2026-10-16T05:30:00+00:00",vid="abc123"):
    return {"source":"authenticated_youtube_api","channel":CHANNEL_ID,
            "youtube_id":vid,"publish_at_utc":time}

class TestFlowMinute(unittest.TestCase):
    def test_slots_correct_utc(self):
        self.assertEqual(slot_utc("2026-10-16","short_am"),"2026-10-16T05:30:00+00:00")
        self.assertEqual(slot_utc("2026-10-16","long"),"2026-10-16T10:30:00+00:00")
        self.assertEqual(slot_utc("2026-10-16","short_pm"),"2026-10-16T15:00:00+00:00")

    def test_no_past_release(self):
        with self.assertRaises(GateError):require_future("2026-10-13T10:30:00+00:00",now=FUTURE)

    def test_media_requires_rights_and_captions(self):
        good_qa().validate("short_am")
        d=good_qa().__dict__.copy()
        d["captions_verified"]=False
        with self.assertRaises(GateError):MediaQA(**d).validate("short_am")
        d["captions_verified"]=True
        d["voice_duration_s"]=48.0
        with self.assertRaises(GateError):MediaQA(**d).validate("short_am")

    def test_candidate_enforces_novelty(self):
        topic=Topic("Claude helps troubleshoot spreadsheets",
            "Viewers learn how to confirm broken lookup formulas step by step",
            "Show an invented lookup dataset and a corrected example with verified values",
            ("https://support.google.com/docs/answer/1","https://support.claude.com/en/articles/1"),.9)
        topic.validate()
        with self.assertRaises(GateError):topic.validate((topic.title,))

    def test_provider_fallback_and_budget(self):
        now=FUTURE
        a=Provider("online","voice",True,100)
        b=Provider("offline","voice",True,100)
        router=ProviderRouter([a,b])
        self.assertEqual(router.choose("voice",now=now).name,"offline")
        router.record_failure(b,403,now=now)
        self.assertEqual(router.choose("voice",now=now).name,"online")
        router.record_failure(a,429,now=now)
        with self.assertRaises(GateError):router.choose("voice",now=now)
        self.assertEqual(router.choose("voice",now=now+timedelta(minutes=46)).name,"online")

    def test_paid_provider_budget_respected(self):
        router=ProviderRouter([Provider("expensive","render",True,10,2.0)])
        with self.assertRaises(GateError):router.choose("render",remaining_budget=0)
        self.assertEqual(router.choose("render",remaining_budget=3).name,"expensive")

    def test_idempotent_reservation_and_wrong_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            led=ReleaseLedger(Path(tmp)/"state.db")
            self.assertTrue(led.reserve("short_123","short_am","2026-10-16",HASH,now=FUTURE))
            self.assertFalse(led.reserve("short_123","short_am","2026-10-16",HASH,now=FUTURE))
            with self.assertRaises(GateError):
                led.reserve("short_123","short_am","2026-10-16","b"*64,now=FUTURE)
            with self.assertRaises(GateError):
                led.reserve("short_124","short_am","2026-10-16","b"*64,now=FUTURE)
            with self.assertRaises(GateError):
                led.reserve("other","long","2026-10-16","b"*64,channel="wrong",now=FUTURE)

    def test_transition_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            led=ReleaseLedger(Path(tmp)/"q.db")
            led.reserve("short_123","short_am","2026-10-16",HASH,now=FUTURE)
            with self.assertRaises(GateError):led.advance("short_123",Stage.SCHEDULED_VERIFIED,receipt())
            self.assertTrue(led.advance("short_123",Stage.FACTS_VERIFIED))
            led.advance("short_123",Stage.QA_PASSED)
            led.advance("short_123",Stage.UPLOAD_UNRESOLVED)
            with self.assertRaises(GateError):led.advance("short_123",Stage.PRIVATE_UPLOADED,{"youtube_id":"abc123"})
            led.advance("short_123",Stage.PRIVATE_UPLOADED,receipt())
            led.advance("short_123",Stage.PROCESSING_SUCCEEDED,receipt())
            led.advance("short_123",Stage.SCHEDULE_UNRESOLVED)
            with self.assertRaises(GateError):
                led.advance("short_123",Stage.SCHEDULED_VERIFIED,receipt(vid="DIFFERENT",time="2026-10-16T05:31:00+00:00"))
            self.assertTrue(led.advance("short_123",Stage.SCHEDULED_VERIFIED,receipt()))
            self.assertFalse(led.advance("short_123",Stage.SCHEDULED_VERIFIED,receipt()))
            self.assertEqual(led.get("short_123")["youtube_id"],"abc123")
            with self.assertRaises(GateError):
                led.advance("short_123",Stage.PUBLIC_VERIFIED,receipt(vid="new"))
            self.assertTrue(led.advance("short_123",Stage.PUBLIC_VERIFIED,receipt()))

if __name__=="__main__":
    unittest.main()
