import copy,json,unittest,tempfile,hashlib
from pathlib import Path
from final_readiness import verify_pilot,review_plan
class ReadinessTests(unittest.TestCase):
    def fixture(self,p):
        p.write_bytes(b"fixture, not real media")
        return {"mp4_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"release_authorized":False,"resolution":[1080,1920],"decoded_frames":30,"fps":30,"duration_seconds":1,"audio_samples":48000,"audio_energy":{"clipped_samples":0},"full_av_decode_pass":True}
    def test_unsigned(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"test.mp4";r=self.fixture(p)
            self.assertTrue(verify_pilot(p,r,"short")["publisher_unsigned_media_rejected"])
    def test_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"test.mp4";r=self.fixture(p);p.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError,"hash"):verify_pilot(p,r,"short")
    def test_bad_clock_and_authority(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"test.mp4";r=self.fixture(p)
            for field,value in [("audio_samples",1),("release_authorized",True),("full_av_decode_pass",False)]:
                with self.assertRaises(ValueError):verify_pilot(p,{**r,field:value},"short")
    def test_no_fake_metrics(self):
        self.assertFalse(review_plan()["live_metrics_collected"])
        self.assertEqual(review_plan()["windows_hours"],[24,72,168])
if __name__=="__main__":unittest.main()
