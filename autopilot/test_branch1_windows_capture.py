"""Windows receipt tests through the same entry point as existing Linux validation."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from autopilot.branch1_recovery import verify_capture,RecoveryRefused
from autopilot.branch1_windows_capture import SCHEMA,METHOD,brief_digest,digest
ROOT=Path(__file__).resolve().parents[1]
class WindowsCaptureTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.d=Path(self.t.name);self.media=self.d/"capture.mp4";self.media.write_bytes(b"identity-only test"*2500)
        self.brief=json.loads((ROOT/"content/recovery_pilot/real_csv_proof_first_short.json").read_text())
        n=round(self.brief["duration_seconds"]*10)
        self.e=self.d/"evidence.json";self.r=self.d/"receipt.json"
        for name in ("demo.py","capture.py"):(self.d/name).write_text("# test fixture only")
        self.log={"method":METHOD,"continuous":True,"scripted_demo":True,"release_authorized":False,"capture_sha256":digest(self.media),"fps":10,"frames":n,"dimensions":[870,494],"capture_times_seconds":[i/10 for i in range(n)],"max_sample_lag_seconds":0,
                  "changes":[{"frame":i,"seconds":i/10,"delta":2.0} for i in (6,19,31,42,55,66)],"source_sha256":{x:digest(self.d/x) for x in ("demo.py","capture.py")}}
        self.receipt={"schema":SCHEMA,"episode_id":self.brief["episode_id"],"capture_method":METHOD,"capture_sha256":digest(self.media),"capture_bytes":self.media.stat().st_size,"brief_sha256":brief_digest(self.brief),"evidence_sha256":"","private_data":False,"release_approved":False,"youtube_uploads":0}
        self.write()
    def write(self):
        self.e.write_text(json.dumps(self.log));self.receipt["evidence_sha256"]=digest(self.e);self.r.write_text(json.dumps(self.receipt))
    def check(self):
        return verify_capture(self.brief,self.media,self.r,windows_evidence=self.e)
    def test_windows_identity_is_not_approval(self):
        result=self.check()
        self.assertEqual(result["capture_status"],"WINDOWS_EXACT_HASH_VERIFIED_REVIEW_ONLY")
        self.assertFalse(result["owner_approval"]);self.assertFalse(result["provenance_authenticated"])
        with self.assertRaises(RecoveryRefused):verify_capture(self.brief,self.media,self.r)
    def test_mismatches(self):
        self.media.write_bytes(self.media.read_bytes()+b"x")
        with self.assertRaises(RecoveryRefused):self.check()
    def test_brief_binding(self):
        self.brief["title"]="Another valid title"
        with self.assertRaises(RecoveryRefused):self.check()
    def test_scope_spoof(self):
        for k,v in [("release_approved",True),("private_data",True),("youtube_uploads",False),("capture_method","xvfb_xterm_ffmpeg_live")]:
            with self.subTest(k=k):
                old=self.receipt[k];self.receipt[k]=v;self.write()
                with self.assertRaises(RecoveryRefused):self.check()
                self.receipt[k]=old
    def test_log_tampering(self):
        self.e.write_text("{}")
        with self.assertRaises(RecoveryRefused):self.check()
    def test_even_rehashed_bad_evidence_rejected(self):
        for k,v in [("continuous",False),("frames",1),("fps",True),("changes",[]),("max_sample_lag_seconds",.2),("source_sha256",{"../demo.py":"a"*64,"capture.py":"b"*64})]:
            with self.subTest(k=k):
                old=self.log[k];self.log[k]=v;self.write()
                with self.assertRaises(RecoveryRefused):self.check()
                self.log[k]=old
    def test_source_tampering(self):
        (self.d/"demo.py").write_text("# modified")
        with self.assertRaises(RecoveryRefused):self.check()
if __name__=="__main__":unittest.main()
