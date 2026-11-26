"""B1v10 local readiness audit. Never creates a publisher approval or calls YouTube."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

D=Path(__file__).resolve().parent
ROOT=D.parents[1]
sys.path.insert(0,str(ROOT))
from scripts.publish_youtube import approval_allows_exact_video
from scripts.test_validate_publish_dispatch_b4f0 import GOOD
from scripts.validate_publish_dispatch_b4f0 import validate_downloaded_media, DispatchInputRejected
from narration_review import normalized

BASE="7f4ef63"
HISTORICAL=("scripts.test_publish_youtube_preflight","scripts.test_validate_publish_dispatch_b4f0",
"scripts.test_branch1_real_python_long_publisher_preflight","autopilot.test_branch1_recovery",
"autopilot.test_branch1_nine_cause_diagnosis","autopilot.test_branch1_age_matched_learning",
"autopilot.test_branch1_growth_action_engine","autopilot.test_branch1_pilot_release_manifest",
"autopilot.test_branch1_long_pilot_release_manifest")
SYMLINK_TEST="scripts.test_validate_publish_dispatch_b4f0.DispatchTests.test_media_check_rejects_symlink"
def read(name):return json.loads((D/name).read_text(encoding="utf-8-sig"))
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def require(ok,msg):
    if not ok:raise ValueError(msg)
def protected_changes():
    names=subprocess.check_output(["git","diff","--name-only",BASE,"--"],cwd=ROOT,text=True).splitlines()
    return [x for x in names if x!="docs/B1V10_HD_PRODUCTION_UPGRADE.md" and not x.startswith("motion-v2/b1v10/")]
def verify_pilot(path,report,kind):
    require(path.is_file() and not path.is_symlink(),"missing or linked pilot")
    require(sha(path)==report["mp4_sha256"],"pilot hash mismatch")
    require(report["release_authorized"] is False,"unexpected authority")
    require(report["resolution"]==([1080,1920] if kind=="short" else [1920,1080]),"wrong dimensions")
    frames=report["decoded_frames"] if kind=="short" else report["frames"]
    require(report["fps"]==30 and abs(frames/30-report["duration_seconds"])<1e-6,"video clock mismatch")
    require(report["audio_samples"]==frames*1600,"audio clock mismatch")
    require(report["audio_energy"]["clipped_samples"]==0,"clipped audio")
    require(report["full_av_decode_pass" if kind=="short" else "full_decode_pass"] is True,"missing decode evidence")
    require(not approval_allows_exact_video({"approved_video_sha256":report["mp4_sha256"]},report["mp4_sha256"]),"publisher unexpectedly accepted unsigned media")
    return {"kind":kind,"sha256":report["mp4_sha256"],"frames":frames,"duration_seconds":report["duration_seconds"],"file_identity_verified":True,"historical_decode_evidence_verified":True,"publisher_unsigned_media_rejected":True}
def review_plan():
    return {"windows_hours":[24,72,168],"short_metrics":["shown_in_feed","stayed_to_watch_pct","engaged_views","average_view_duration_seconds","retention_3s_pct","subscribers_gained"],
            "long_metrics":["impressions","impressions_ctr_pct","average_view_duration_seconds","retention_30s_pct","subscribers_gained"],
            "method":"existing autopilot.branch1_recovery and branch1_age_matched_learning; compare format and age matched cohorts at 60-84 hours; minimum 5 videos per cohort and existing exposure thresholds",
            "missing_data":"blank, never zero-filled","baseline":"historical repo observation only: 21.2% stayed to watch, 58s long AVD, 4.8% long CTR",
            "live_metrics_collected":False,"no_virality_guarantee":True}
def flatten(suite):
    for x in suite:
        if isinstance(x,unittest.TestSuite):yield from flatten(x)
        else:yield x
def regression():
    suite=unittest.defaultTestLoader.loadTestsFromNames(HISTORICAL)
    # Do not change workstation privileges. Probe capability first.
    real_symlink=True
    with TemporaryDirectory() as tmp:
        t=Path(tmp);(t/"source").write_text("test")
        try:(t/"link").symlink_to(t/"source")
        except OSError:real_symlink=False
    tests=list(flatten(suite))
    selected=[x for x in tests if real_symlink or x.id()!=SYMLINK_TEST]
    result=unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(selected))
    require(result.wasSuccessful() and not result.skipped,"historical regression failed")
    simulated=False
    if not real_symlink:
        with TemporaryDirectory() as tmp:
            root=Path(tmp);env={**GOOD,"FM_PUBLISH_AT_UTC":"2099-11-08T05:30:00Z"}
            for k in ("FM_VIDEO_FILE","FM_CAPTIONS_FILE","FM_THUMBNAIL_FILE"):(root/env[k]).write_bytes(b"A"*300)
            require(not validate_downloaded_media(root,env)["youtube_insert_authorized"],"unsigned acceptance")
            original=Path.is_symlink
            def fake(p):return p==root/env["FM_VIDEO_FILE"] or original(p)
            with patch.object(Path,"is_symlink",fake):
                try:validate_downloaded_media(root,env)
                except DispatchInputRejected:simulated=True
            require(simulated,"mock linked-media rejection failed")
    b1=unittest.defaultTestLoader.discover(str(D),pattern="test_*.py",top_level_dir=str(D))
    r=unittest.TextTestRunner(verbosity=1).run(b1)
    require(r.wasSuccessful() and not r.skipped,"B1v10 regression failed")
    return {"historical_total":len(tests),"historical_native_passed":result.testsRun,"real_symlink_test_executed":real_symlink,
            "mock_symlink_rejection_passed":simulated,"b1v10_passed":r.testsRun,"historical_code_unchanged":True}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--short",type=Path,required=True);p.add_argument("--long",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    require(not protected_changes(),"existing production code changed")
    s,l=read("SHORT_PILOT_QA.json"),read("LONG_PILOT_QA.json")
    pilots=[verify_pilot(a.short,s,"short"),verify_pilot(a.long,l,"long")]
    n=read("LONG_NARRATION_QA.json"); c=read("LONG_CAPTION_REVIEW.json")
    expected=normalized(" ".join(x["expected"] for x in n["scene_timeline"]))
    observed=normalized(" ".join(w["word"] for x in c["cues"] for w in x["words"]))
    blockers=["Owner full playback of exact Short and long MP4, mobile visual review and final mix listening",
              "Long hook raw ASR failed; corrected captions are not pronunciation evidence",
              "Independent factual and rights clearance for exact finished files",
              "Existing proof-first policy requires recorded real software action; current pilots are explanatory illustrations of executed results",
              "Second Short and fresh daily research/inventory check are missing",
              "No live Studio cohort or measured retention improvement; no production integration/approval manifest"]
    r={"version":"1.0.0-rc1","status":"REVIEW_ONLY_HOLD","pilots":pilots,"long_corrected_tokens_match_script":expected==observed,
       "long_raw_asr_screen_pass":n["asr_screen_pass"],"regression":regression(),"blockers":blockers,
       "performance_review":review_plan(),"daily_target":{"shorts":2,"longs":1},"rendered_pilot_count":{"shorts":1,"longs":1},
       "production_integration_ready":False,"release_authorized":False,"youtube_mutations":0}
    with a.output.open("x",encoding="utf-8") as f:json.dump(r,f,indent=2);f.write("\n")
    print(json.dumps(r,indent=2))
if __name__=="__main__":main()
