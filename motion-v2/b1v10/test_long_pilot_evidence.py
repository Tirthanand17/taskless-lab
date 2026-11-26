import unittest
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8-sig"))

class LongPilotEvidenceTest(unittest.TestCase):
    def test_real_git_steps(self):
        d=read("GIT_BISECT_DEMO.json")
        self.assertEqual(len(d["commits"]),16)
        self.assertEqual(d["first_bad"],11)
        self.assertEqual([s["revision"] for s in d["steps"]],[7,11,9,10])
        self.assertEqual([s["classification"] for s in d["steps"]],["good","bad","good","good"])
        self.assertTrue(d["reset_completed"])
    def test_render_clock(self):
        r=read("LONG_PILOT_QA.json")
        n=read("LONG_NARRATION_QA.json")
        self.assertEqual(r["resolution"],[1920,1080])
        self.assertEqual(r["frames"],n["frames_at_30fps"])
        self.assertEqual(r["audio_samples"],n["samples"])
        self.assertEqual(r["audio_energy"]["clipped_samples"],0)
        self.assertTrue(r["full_decode_pass"])
        self.assertFalse(r["release_authorized"])
        self.assertFalse(r["full_human_playback_approved"])
    def test_timeline(self):
        r=read("LONG_PILOT_QA.json")
        states=r["visual_states"]
        self.assertEqual(len(states),17)
        self.assertEqual(states[0]["start_frame"],0)
        self.assertEqual(states[-1]["end_frame"],r["frames"])
        self.assertTrue(all(a["end_frame"]==b["start_frame"] for a,b in zip(states,states[1:])))
        self.assertTrue(all(e["sample"]==e["frame"]*1600 for e in r["planned_sound_events"]))
    def test_correction_not_approval(self):
        r=read("LONG_PILOT_QA.json")
        self.assertFalse(r["raw_asr_screen_pass"])
        self.assertEqual(len(r["caption_corrections"]),5)
        self.assertFalse(r["release_authorized"])

if __name__=="__main__":unittest.main()
