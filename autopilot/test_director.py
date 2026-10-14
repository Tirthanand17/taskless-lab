import unittest
from datetime import datetime,timezone
from autopilot.core import GateError
from autopilot.director import draft

class TestDirector(unittest.TestCase):
    def test_draft_does_not_publish(self):
        def example(n):
            return {
                "title":f"Useful explanation about practical automation number {n}",
                "viewer_benefit":"Help viewers understand the problem with concrete steps and clear results",
                "original_example":f"Separate demonstration {n} with actual sample values and a check",
                "source_urls":["https://support.google.com/docs/answer/1","https://learn.microsoft.com/en-us/office/1"],
                "editorial_score":.85
            }
        pack={"episodes":{k:example(i) for i,k in enumerate(("short_am","long","short_pm"))}}
        plan=draft("2026-10-17",pack,now=datetime(2026,10,14,tzinfo=timezone.utc))
        self.assertEqual(plan["state"],"NO_RENDER_NO_UPLOAD_NO_SCHEDULE")
        self.assertEqual(len(plan["episodes"]),3)
        self.assertFalse(any(p["publish_allowed"] for p in plan["episodes"]))
        pack["episodes"]["short_pm"]["original_example"]=pack["episodes"]["long"]["original_example"]
        with self.assertRaises(GateError):
            draft("2026-10-17",pack,now=datetime(2026,10,14,tzinfo=timezone.utc))

    def test_draft_rejects_missing_one(self):
        with self.assertRaises(GateError):
            draft("2026-10-17",{"episodes":{}},now=datetime(2026,10,14,tzinfo=timezone.utc))
