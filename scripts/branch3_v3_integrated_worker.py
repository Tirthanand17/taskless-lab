"""Integrated, restart-checked CLIVOX V3 staging worker.

The ONLY input is self-generated media. No production source interface,
external downloads, private account access, or publish actions. Outputs
are verified and removed with the temporary workspace.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import tempfile
import time
from pathlib import Path

from scripts.branch3_v3_private_queue import ComputeQueue
from scripts.branch3_v3_generated_media_smoke import fixture
from scripts.branch3_v3_local_proxy import measure_local_proxy
from scripts.branch3_v3_transcript_context import (
    fixture_rows, synthesize_generated, transcribe_generated, combine_observations,
)
from scripts.branch3_v3_editorial_draft import draft
from scripts.branch3_v3_vertical_render_smoke import run, caption_ass, need
from scripts.branch3_v2_p5_longform_local_signal_planner import canonical
from scripts.branch3_v2_p5_synthetic_moment_proposals import _probe_closed

VERSION = "v3-generated-worker-1"


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()


def connect(path):
    db=sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.execute("""CREATE TABLE IF NOT EXISTS receipts
                  (digest TEXT PRIMARY KEY, payload BLOB NOT NULL)""")
    db.commit()
    return db


def stage(folder, name, inputs, compute):
    """One bounded compute step, immutable hash-checked receipt, fresh connection."""
    _probe_closed()
    key=digest({"version":VERSION,"stage":name,"inputs":inputs})
    db=connect(folder/"jobs.sqlite")
    try:
        q=ComputeQueue(db)
        now=int(time.time())
        job=q.enqueue(name,key,now)
        row=db.execute("SELECT state,output_digest FROM v3_compute_jobs WHERE id=?",(job,)).fetchone()
        if row[0]=="done":
            receipt=db.execute("SELECT payload FROM receipts WHERE digest=?",(row[1],)).fetchone()
            need(receipt is not None and hashlib.sha256(receipt[0]).hexdigest()==row[1],"RECEIPT_INTEGRITY")
            return json.loads(receipt[0])
        lease=q.claim(now,3600)
        need(lease is not None and lease["id"]==job,"LEASE")
        try:
            result=compute()
            payload=canonical(result)
            need(len(payload)<=2_000_000,"RECEIPT_LIMIT")
            sha=hashlib.sha256(payload).hexdigest()
            # Immutable receipt is committed first; the fenced queue pointer is
            # the sole authority. A stale/orphan receipt cannot complete a job.
            db.execute("INSERT OR IGNORE INTO receipts VALUES(?,?)",(sha,payload))
            db.commit()
            need(q.finish(job,lease["generation"],int(time.time()),sha),"STALE_LEASE")
            return result
        except BaseException:
            q.fail(job,lease["generation"],int(time.time()))
            raise
    finally:
        db.close()


def packaging(plan, source_sha, preview_sha, cover_sha):
    """Evidence-bound draft. No invented creator identity, title, or approval."""
    title=plan["observed_opening_title_draft"]
    need(title is not None,"TITLE_REVIEW_REQUIRED")
    return {"stage":"UNAPPROVED_PACKAGING", "title":title,
            "description":"Original generated CLIVOX staging demonstration; not for publication.",
            "hashtags":[], "hook_alternatives":[title],
            "commentary_origin":"generated fixture only", "source_sha256":source_sha,
            "preview_sha256":preview_sha,"cover_sha256":cover_sha,
            "caption_sha256":hashlib.sha256(plan["caption_srt"].encode()).hexdigest(),
            "original_commentary_reviewed":False,"title_truth_reviewed":False,
            "ready_to_publish":False,"youtube_upload_authorized":False}


def render(folder, source, plan, actual_speech):
    c=plan["candidate"]
    start,end=c["start_ms"],c["end_ms"]
    duration=(end-start)/1000
    need(15<=duration<=55 and plan["layout"]["mode"]=="fit" and plan["caption_cues"],"DRAFT")
    (folder/"captions.ass").write_text(caption_ass(plan["caption_cues"],end-start),encoding="utf-8")
    (folder/"captions.srt").write_text(plan["caption_srt"],encoding="utf-8")
    vf=("fps=24,scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x111820,setsar=1,"
        "tpad=stop_mode=clone:stop_duration=1,ass=captions.ass")
    run(["ffmpeg","-v","error","-nostdin","-protocol_whitelist","file",
         "-ss",str(start/1000),"-i",source.name,"-t",str(duration),
         "-map","0:v:0","-map","0:a:0","-vf",vf,"-af","aresample=48000,volume=0.60,alimiter=limit=0.65:level=false:latency=1",
         "-c:v","libx264","-threads:v","2","-preset","ultrafast","-crf","23",
         "-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-ac","1",
         "-movflags","+faststart","preview.mp4"],folder)
    # Cover extracted from the exact output, not a hallucinated scene.
    cue=plan["caption_cues"][0]
    frame_time=(cue["start_ms"]+cue["end_ms"])/2000
    run(["ffmpeg","-v","error","-nostdin","-ss",str(frame_time),"-i","preview.mp4",
         "-frames:v","1","-vf","scale=540:960","cover.png"],folder)
    return {"preview_sha256":file_digest(folder/"preview.mp4"),
            "cover_sha256":file_digest(folder/"cover.png"),"duration_seconds":duration,
            "caption_frame_seconds":frame_time,"actual_generated_speech":actual_speech}


def verify(folder, rendered):
    path=folder/"preview.mp4"
    need(file_digest(path)==rendered["preview_sha256"] and
         file_digest(folder/"cover.png")==rendered["cover_sha256"],"OUTPUT_INTEGRITY")
    data=json.loads(run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",
                         "preview.mp4"],folder,64000))
    need(len(data["streams"])==2,"STREAMS")
    v=next(s for s in data["streams"] if s["codec_type"]=="video")
    a=next(s for s in data["streams"] if s["codec_type"]=="audio")
    need((v["width"],v["height"],v["codec_name"],v["pix_fmt"],v["avg_frame_rate"])
         ==(1080,1920,"h264","yuv420p","24/1"),"VIDEO")
    need((a["codec_name"],a["sample_rate"],a["channels"])==("aac","48000",1),"AUDIO")
    need(abs(float(data["format"]["duration"])-rendered["duration_seconds"])<.2
         and abs(float(v["duration"])-float(a["duration"]))<.2,"DURATION")
    run(["ffmpeg","-v","error","-xerror","-nostdin","-i","preview.mp4",
         "-map","0:v","-map","0:a","-f","null","-"],folder)
    pixels=run(["ffmpeg","-v","error","-ss",str(rendered["caption_frame_seconds"]),
                "-i","preview.mp4","-vf","crop=820:180:100:1450,format=gray",
                "-frames:v","1","-f","rawvideo","pipe:1"],folder,820*180)
    need(len(pixels)==820*180 and sum(p>210 for p in pixels)>100,"VISIBLE_CAPTION")
    import array,sys
    raw=run(["ffmpeg","-v","error","-i","preview.mp4","-vn","-ac","1","-ar","8000",
             "-f","s16le","pipe:1"],folder,900000)
    pcm=array.array("h");pcm.frombytes(raw)
    if sys.byteorder!="little":pcm.byteswap()
    peak=max((abs(x) for x in pcm),default=0)
    need(len(pcm)>8000 and 200<peak<32000,f"AUDIO_LEVEL_samples_{len(pcm)}_peak_{peak}")
    return {"decoded":True,"caption_pixels_verified":True,"audio_peak_pcm16":max(abs(x) for x in pcm),
            "preview_sha256":rendered["preview_sha256"],"human_review_required":True}


def restore_check(folder):
    db=connect(folder/"jobs.sqlite")
    backup=sqlite3.connect(folder/"restore.sqlite")
    try:
        db.backup(backup)
        need(backup.execute("PRAGMA integrity_check").fetchone()==("ok",),"BACKUP")
        q=ComputeQueue(backup)
        need(q.counts()=={"ready":0,"running":0,"done":5,"held":0},"RESTORE_JOBS")
        for sha,payload in backup.execute("SELECT digest,payload FROM receipts"):
            need(hashlib.sha256(payload).hexdigest()==sha,"RESTORE_RECEIPT")
        need(backup.execute("""SELECT count(*) FROM v3_compute_jobs j LEFT JOIN receipts r
              ON j.output_digest=r.digest WHERE j.state='done' AND r.digest IS NULL""").fetchone()==(0,),
             "RESTORE_POINTER")
        return q.counts()
    finally:
        backup.close();db.close()


def pipeline(actual_speech=False):
    _probe_closed()
    with tempfile.TemporaryDirectory(prefix="clivox-v3-integrated-") as root:
        folder=Path(root)
        source=fixture(folder)
        if actual_speech:
            synthesize_generated(folder/"speech.wav")
            run(["ffmpeg","-v","error","-nostdin","-i",source.name,"-i","speech.wav",
                 "-map","0:v:0","-map","1:a:0","-c:v","copy","-af","apad","-ar","8000",
                 "-c:a","aac","-t","80","speech-source.mp4"],folder)
            source=folder/"speech-source.mp4"
        sha=file_digest(source)
        def inspect():
            return measure_local_proxy(source.resolve(),"dialogue")
        measurements=stage(folder,"inspect",sha,inspect)
        rows=stage(folder,"transcribe",[sha,actual_speech],
                   lambda:transcribe_generated(source,80000) if actual_speech else fixture_rows())
        def select():
            report=combine_observations(measurements,rows)
            need(bool(report["candidates"]),"NO_CANDIDATE")
            return draft(measurements,rows,report["candidates"][0]["candidate_id"],160,90)
        plan=stage(folder,"propose",[digest(measurements),digest(rows)],select)
        rendered=stage(folder,"render",[sha,digest(plan)],lambda:render(folder,source,plan,actual_speech))
        verified=stage(folder,"verify",digest(rendered),lambda:verify(folder,rendered))
        replay=stage(folder,"verify",digest(rendered),lambda: (_ for _ in ()).throw(ValueError("duplicate")))
        need(replay==verified,"REPLAY")
        pack=packaging(plan,sha,rendered["preview_sha256"],rendered["cover_sha256"])
        counts=restore_check(folder)
        _probe_closed()
        return {"generated_only":True,"actual_offline_asr":actual_speech,
                "word_count":sum(len(r["words"]) for r in rows),
                "render":rendered,"qa":verified,"packaging":pack,"restored_jobs":counts,
                "duplicate_compute_prevented":True,"production_ready":False,
                "youtube_upload_authorized":False}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline-asr",action="store_true")
    args=parser.parse_args()
    print(json.dumps(pipeline(args.offline_asr),sort_keys=True))
