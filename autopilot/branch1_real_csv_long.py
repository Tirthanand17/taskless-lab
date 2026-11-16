"""Original three-bug CSV long-form lesson, real executable Python on XTerm.

Review-only, first-party fictional data on a disposable GitHub runner.
No simulated vendor interface, third-party footage, OAuth, publish, or uploads.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

EPISODE="fm_real_python_csv_three_bugs_long_en"
STATUS="LONG_REAL_PYTHON_EXECUTED_SOURCE_OWNER_REVIEW_ONLY"
WIDTH,HEIGHT=1600,900
SOURCE="REAL_PYTHON_LONG_SCREEN.mp4"
FINAL="REAL_PYTHON_LONG_NARRATED_REVIEW_ONLY.mp4"
SRT="ORIGINAL_SOURCE_TIMED_CAPTIONS.srt"
RECEIPT="ORIGINAL_LONG_MEDIA_RECEIPT_NO_RELEASE.json"
# A single continuous problem to solve; no repeated generic productivity slides.
STORY=(
 ("PROOF FIRST / WRONG TOTAL",
  "This original CSV says eight rows add up to two thousand six hundred fifty six dollars and twenty five cents. But the genuinely cleaned file has six invoices worth one thousand four hundred thirty dollars and seventy five cents. Let us find each mistake using real Python."),
 ("SEE THE ORIGINAL DATA",
  "Here is the actual fictional source CSV, not a mock spreadsheet. Two invoice identifiers contain repeated records, one identifier begins with spaces, and amounts use commas. Notice how a human can overlook the differences even when the file looks ordinary."),
 ("BUG ONE / HIDDEN SPACES",
  "A leading space changes a string. The text for invoice one hundred one is not the same raw identifier as invoice one hundred one without spaces. Before comparing identifiers we should normalize the input. Python strip removes surrounding whitespace from each key."),
 ("BUG TWO / DUPLICATE KEYS",
  "A simple row count is not a count of unique invoices. Some entries repeat after whitespace is removed. We will use a set of normalized invoice keys to find repeated records instead of deleting arbitrary rows or pretending every repeated value is safe to discard."),
 ("BUG THREE / AMOUNT STRINGS",
  "A currency amount containing a comma is text until it is parsed. Calling float on the original comma-formatted string is not a reliable money-cleaning strategy. For this small example, remove the thousands separator and use Python Decimal for exact cent arithmetic."),
 ("CHECK THE ORIGINAL TOTAL",
  "Now run a real naive total that counts every row, including duplicates. The result is two thousand six hundred fifty six dollars and twenty five cents. That is the total you would report if you cleaned numeric formatting but forgot the duplicate invoice problem."),
 ("NORMALIZE INVOICE IDS",
  "Run the normalization step on the actual source records. It removes surrounding spaces and compares normalized invoice identifiers. Now two duplicate invoice keys become visible. We keep the first matching record for this demonstration and record every discarded duplicate."),
 ("PARSE THE MONEY VALUES",
  "Next, convert each amount with Decimal instead of binary floating-point arithmetic. The values are still original fictional invoice amounts. This stage verifies every parsed amount and refuses a malformed value rather than silently inventing a zero or dropping an error."),
 ("REMOVE VERIFIED DUPLICATES",
  "The corrected output contains exactly six unique invoice keys. Verify that each remaining invoice has one record and that two repeated entries were actually removed. Real data pipelines should investigate conflicting duplicate amounts instead of blindly choosing which value wins."),
 ("CALCULATE THE FIXED TOTAL",
  "Add the six normalized Decimal amounts from the deduplicated records. The real result is one thousand four hundred thirty dollars and seventy five cents. Compare it against the incorrect total to see how much money was counted twice. This is the measurable payoff."),
 ("SAVE AND RELOAD THE FILE",
  "Write the output to a new CSV file, leaving the original untouched. Then reopen the saved data with Python, verify six invoices remain and independently recompute the expected total. A saved file is more useful evidence than a success message printed without checking anything."),
 ("TAKEAWAY / TEST THE ASSUMPTIONS",
  "Remember the three checks: normalize identifiers, inspect duplicates, and parse currency as Decimal. Real customer records may have legitimate repeated invoice keys, corrections, or multiple lines per invoice, so verify the business rules before deduplicating. This tutorial used entirely fictional data.")
)
RAW_ROWS=(
 ("  INV-101","1,200.50","paid"),
 ("INV-101","1,200.50","paid"),
 ("INV-102","80.00","open"),
 ("INV-103","20.25","paid"),
 ("INV-104","25.00","paid"),
 ("INV-104","25.00","paid"),
 ("INV-105","15.00","paid"),
 ("INV-106","90.00","open"),
)
RAW_TOTAL=Decimal("2656.25")
CLEAN_TOTAL=Decimal("1430.75")
EXPECTED_IDS=("INV-101","INV-102","INV-103","INV-104","INV-105","INV-106")

class LongPilotRefused(ValueError):
    pass

def need(ok,reason):
    if not ok:
        raise LongPilotRefused(reason)

def sha(path):
    h=sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def make_fixture(folder):
    file=folder/"source_fictional.csv"
    need(not file.exists(),"REFUSE_REPLACING_SOURCE")
    with file.open("w",newline="",encoding="utf8") as f:
        w=csv.writer(f)
        w.writerow(("invoice","amount","status"))
        w.writerows(RAW_ROWS)
    return file

def read_and_clean(source):
    need(source.is_file() and not source.is_symlink()
         and 100<=source.stat().st_size<5000,
         "WRONG_OR_PRIVATE_SOURCE")
    with source.open("r",encoding="utf8",newline="") as f:
        reader=csv.DictReader(f)
        need(reader.fieldnames==["invoice","amount","status"],
             "UNEXPECTED_CSV_COLUMNS")
        original=list(reader)
    need(len(original)==8,"UNEXPECTED_SOURCE_ROWS")
    output=[]
    duplicates=[]
    seen=set()
    raw_total=Decimal(0)
    for row in original:
        need(set(row)=={"invoice","amount","status"}
             and row["status"] in ("paid","open"),
             "UNEXPECTED_FIXTURE_VALUES")
        raw_id=row["invoice"]
        canonical=raw_id.strip()
        need(re.fullmatch(r"INV-[0-9]{3}",canonical) is not None,
             "UNSAFE_OR_NONFICTIONAL_INVOICE_ID")
        try:
            amount=Decimal(row["amount"].replace(",",""))
        except InvalidOperation:
            raise LongPilotRefused("MALFORMED_MONEY") from None
        need(amount.is_finite() and amount>0 and amount.as_tuple().exponent>=-2,
             "UNSAFE_CURRENCY_AMOUNTS")
        raw_total+=amount
        if canonical in seen:
            duplicates.append(canonical)
            matched=next(r for r in output if r["invoice"]==canonical)
            need(matched["amount"]==str(amount)
                 and matched["status"]==row["status"],
                 "CONFLICTING_DUPLICATE_REQUIRES_HUMAN_RESOLUTION")
            continue
        seen.add(canonical)
        output.append({"invoice":canonical,"amount":str(amount),
                       "status":row["status"]})
    total=sum((Decimal(r["amount"]) for r in output),Decimal("0"))
    need(raw_total==RAW_TOTAL and total==CLEAN_TOTAL
         and tuple(x["invoice"] for x in output)==EXPECTED_IDS
         and len(duplicates)==2,
         "ACTUAL_PYTHON_CALCULATION_NOT_EXPECTED")
    return {"original":original,"clean":output,"duplicates":duplicates,
            "raw_total":str(raw_total),"clean_total":str(total),
            "difference":str(raw_total-total)}

def save_clean_and_recheck(folder,data):
    target=folder/"clean_fictional.csv"
    need(not target.exists(),"REFUSE_OVERWRITING_CLEAN_OUTPUT")
    source=folder/"source_fictional.csv"
    before=sha(source)
    with target.open("w",newline="",encoding="utf8") as f:
        writer=csv.DictWriter(f,fieldnames=["invoice","amount","status"])
        writer.writeheader()
        writer.writerows(data["clean"])
    with target.open("r",newline="",encoding="utf8") as f:
        reader=csv.DictReader(f)
        saved=list(reader)
    amount=sum((Decimal(x["amount"]) for x in saved),Decimal(0))
    need(saved==data["clean"] and len(saved)==6 and amount==CLEAN_TOTAL
         and sha(source)==before,"REAL_CLEAN_CSV_RELOAD_FAILED")
    return target

def verify_story():
    need(len(STORY)==12 and len(RAW_ROWS)==8,"LONG_STORY_INCOMPLETE")
    words=sum(len(spoken.split()) for _,spoken in STORY)
    need(360<=words<=640,"REAL_LONG_TUTORIAL_NOT_SUBSTANTIVE")
    for title,spoken in STORY:
        need(type(title) is str and re.fullmatch("[A-Z0-9 /]+",title)
             and 14<=len(title)<=50
             and type(spoken) is str and 140<=len(spoken)<=520
             and not any(x in spoken for x in ("{","}","<",">","@")),
             "UNSAFE_STORY_AND_VOICE")
    return {"scenes":12,"words":words,"real_python_required":True,
            "youtube_release_approved":False}

def stage_content(idx,part,data):
    need(0<=idx<12 and part in range(4),"INVALID_EXECUTION_STAGE")
    rows=data["original"]
    clean=data["clean"]
    title=STORY[idx][0]
    # Every value on screen is computed from the actual fictional CSV.
    chunks=(
        ("ACTUAL WRONG TOTAL: $"+data["raw_total"],
         "ACTUAL CLEAN TOTAL: $"+data["clean_total"],
         "DOUBLE COUNTED: $"+data["difference"],
         "NEXT: PROVE THE THREE SOURCES OF ERROR"),
        ("READ CSV WITH PYTHON csv.DictReader",
         "ACTUAL RAW ROWS: "+str(len(rows)),
         "FIRST RAW ID: "+repr(rows[0]["invoice"]),
         "SAMPLE ROWS: "+str([(r["invoice"],r["amount"]) for r in rows[:3]])),
        ("RAW FIRST ID: "+repr(rows[0]["invoice"]),
         "TRIMMED FIRST ID: "+repr(rows[0]["invoice"].strip()),
         "STRIP REMOVES LEADING BLANKS: "+str(len(rows[0]["invoice"])-len(rows[0]["invoice"].strip())),
         "NORMALIZED FIRST ID: "+clean[0]["invoice"]),
        ("SOURCE ROW COUNT: "+str(len(rows)),
         "UNIQUE CLEAN IDS: "+str(len(clean)),
         "DUPLICATE NORMALIZED IDS: "+str(data["duplicates"]),
         "DO NOT DELETE CONFLICTING DUPLICATES SILENTLY"),
        ("FIRST RAW AMOUNT: "+repr(rows[0]["amount"]),
         "DECIMAL AFTER COMMA REMOVAL: "+str(Decimal(rows[0]["amount"].replace(",",""))),
         "PARSER: decimal.Decimal",
         "CENTS STAY EXACT WITHOUT FLOAT CONVERSION"),
        ("COUNTING ALL "+str(len(rows))+" ROWS",
         "SOURCE TOTAL: $"+data["raw_total"],
         "TRUE UNIQUE-KEY TOTAL: $"+data["clean_total"],
         "OVERCOUNT: $"+data["difference"]),
        ("normalize = invoice.strip()",
         "FIRST ID BEFORE: "+repr(rows[0]["invoice"]),
         "FIRST ID AFTER: "+clean[0]["invoice"],
         "DUPLICATES: "+",".join(data["duplicates"])),
        ("Decimal(text.replace(',', ''))",
         "PARSED AMOUNT: "+clean[0]["amount"],
         "PAID EXAMPLE: "+clean[2]["amount"],
         "MALFORMED INPUT WOULD BE REJECTED"),
        ("DEDUPE BY NORMALIZED INVOICE KEY",
         "CLEAN IDS: "+str([r["invoice"] for r in clean]),
         "ROWS REMOVED: "+str(len(rows)-len(clean)),
         "EACH DUPLICATE MATCHES AMOUNT AND STATUS"),
        ("sum(Decimal(row['amount']) for row in clean)",
         "FIXED TOTAL: $"+data["clean_total"],
         "UNFIXED TOTAL: $"+data["raw_total"],
         "MONEY OVERCOUNTED: $"+data["difference"]),
        ("CLEAN OUTPUT = clean_fictional.csv",
         "SAVED ROW COUNT: "+str(len(clean)),
         "SOURCE RETAINED: source_fictional.csv",
         "VERIFIED TOTAL AGAIN: $"+data["clean_total"]),
        ("1. STRIP NORMALIZED INVOICE IDS",
         "2. INVESTIGATE CONFLICTING DUPLICATES",
         "3. PARSE MONEY USING DECIMAL",
         "ACTUAL RESULT: SIX RECORDS, $"+data["clean_total"]),
    )
    return title,chunks[idx][part]

def render_stage_runner(folder,clock):
    need(os.environ.get("DISPLAY")==":93" and os.environ.get("GITHUB_ACTIONS")=="true",
         "XTERM_NOT_EPHEMERAL_GITHUB_XVFB")
    data=read_and_clean(folder/"source_fictional.csv")
    durations=json.loads(clock.read_text("utf8"))
    need(type(durations) is list and len(durations)==len(STORY)
         and all(type(v) in (int,float) and math.isfinite(v)
                 and 5<v<30 for v in durations),
         "SOURCE_AND_SPEECH_CLOCK_NOT_ALIGNED")
    for i,seconds in enumerate(durations):
        title=STORY[i][0]
        started=time.monotonic()
        # In the opening, show proof and a second genuine calculation
        # within three seconds; no inert logo or synthetic result overlay.
        offsets=((0.,1.1,2.3,max(3.5,seconds*.57)) if i==0 else
                 (0.,seconds*.24,seconds*.48,seconds*.72))
        for part in range(4):
            intended=started+offsets[part]
            while time.monotonic()<intended:
                time.sleep(min(.08,intended-time.monotonic()))
            if i==10 and part==0:
                save_clean_and_recheck(folder,data)
            if part==0:
                print("\033[2J\033[H",end="",flush=True)
                print("FLOWMINUTE LAB  /  ORIGINAL LIVE PYTHON",flush=True)
                print("FICTIONAL CSV - NO CUSTOMER ACCOUNTS",flush=True)
                print("-"*73,flush=True)
                print(title,flush=True)
                print("-"*73,flush=True)
            title,line=stage_content(i,part,data)
            print("  > real Python stage_content(",i,",",part,")",flush=True)
            print("  ",line,"\n",flush=True)
        until=started+seconds
        while time.monotonic()<until:
            time.sleep(min(.08,until-time.monotonic()))
        (folder/f"STAGE_{i:02}.proof").write_text(
            f"ACTUAL_PYTHON_STAGE_{i}_COMPLETE\n","utf8")
    print("\nREAL_PYTHON_EXECUTION_FINISHED",flush=True)
    return {"completed_stages":12}

def real_app_screen(folder,seconds):
    for tool in ("Xvfb","xterm","ffmpeg","ffprobe"):
        need(shutil.which(tool) is not None,"REAL_RUNNER_TOOL_MISSING_"+tool)
    need(os.environ.get("GITHUB_ACTIONS")=="true"
         and os.environ.get("GITHUB_REPOSITORY")=="Tirthanand17/taskless-lab"
         and os.environ.get("GITHUB_REF")=="refs/heads/main"
         and os.environ.get("PUBLISH_ENABLED")=="false"
         and os.environ.get("FLOWMINUTE_ENABLE_PUBLISH")=="0"
         and os.environ.get("FLOWMINUTE_ALLOW_LAPTOP")=="0",
         "REAL_LONG_CAPTURE_GITHUB_ONLY_NO_PUBLISH")
    import tempfile
    display=":93"
    need(not Path("/tmp/.X11-unix/X93").exists(),"X11_DISPLAY_IN_USE")
    xvfb=subprocess.Popen(["Xvfb",display,"-screen","0",
                           f"{WIDTH}x{HEIGHT}x24","-nolisten","tcp"],
                          stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    term=None
    record=None
    try:
        for _ in range(50):
            if Path("/tmp/.X11-unix/X93").exists():break
            need(xvfb.poll() is None,"XVFB_EXITED")
            time.sleep(.1)
        need(Path("/tmp/.X11-unix/X93").exists(),"XVFB_NOT_READY")
        # Child's only visual elements are the real xterm app and actual
        # stdout from Python's reading and computation of the CSV fixture.
        env={**os.environ,"DISPLAY":display,"HOME":str(folder)}
        term=subprocess.Popen(
            ["xterm","-fa","DejaVu Sans Mono","-fs","19",
             "-geometry","94x27+42+30","-bg","#0c1d2a","-fg","#f2f7ff",
             "-e",sys.executable,"-m","autopilot.branch1_real_csv_long",
             "--stage-runner","--out",str(folder)],
            env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(.8)
        need(term.poll() is None,"REAL_PYTHON_XTERM_QUIT")
        source=folder/SOURCE
        record=subprocess.Popen(
            ["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
             "-f","x11grab","-video_size",f"{WIDTH}x{HEIGHT}",
             "-framerate","8","-i",display+".0",
             "-t",f"{seconds:.3f}","-an","-c:v","libx264","-threads","2",
             "-preset","ultrafast","-crf","24","-pix_fmt","yuv420p",
             "-movflags","+faststart",str(source)],
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        record.communicate(timeout=480)
        need(record.returncode==0,"GENUINE_X11_SOURCE_CAPTURE_FAILED")
        try:term.wait(timeout=10)
        except subprocess.TimeoutExpired:term.terminate()
        need(all((folder/f"STAGE_{i:02}.proof").is_file()
                 for i in range(12)),
             "SOME_REAL_PYTHON_STAGES_MISSING")
        return source
    finally:
        if record and record.poll() is None:
            record.kill();record.communicate(timeout=5)
        if term and term.poll() is None:
            term.kill();term.communicate(timeout=5)
        xvfb.terminate()
        try:xvfb.wait(timeout=5)
        except subprocess.TimeoutExpired:xvfb.kill()

def cmd(args,timeout=700):
    try:p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired):
        raise LongPilotRefused("PHYSICAL_MEDIA_COMMAND_UNAVAILABLE") from None
    need(p.returncode==0,"PHYSICAL_MEDIA_COMMAND_FAILED")
    return p.stdout

def render(out,model,voices):
    need(not out.exists() and out.parent==Path("/tmp"),
         "NO_OVERWRITE_OR_PERSONAL_MEDIA")
    verify_story()
    from autopilot.cloud_av_probe import verify_pinned_assets
    verify_pinned_assets(model,voices)
    from autopilot.branch1_nov12_four_review_videos import (
        synthesize,cues_to_files,
    )
    from autopilot.verified_aac_mastering_b4g5 import (
        AUDIO_MASTERING_FILTER,AUDIO_REMASTER_FILTER,
        EncodedMasteringRefused,verify_exact_encoded_master,
    )
    from kokoro_onnx import Kokoro
    out.mkdir(parents=True,mode=0o700)
    fixture=make_fixture(out)
    data=read_and_clean(fixture)
    voice=Kokoro(str(model),str(voices))
    ep={"type":"long","voice":"af_heart","id":EPISODE,
        "scenes":[[title,"BEFORE","ACTUAL RESULT",spoken]
                  for title,spoken in STORY]}
    wav,scene_seconds,cues,total=synthesize(voice,ep,out)
    need(110<=total<=300 and len(scene_seconds)==12,
         "LONG_NARRATION_NOT_SUBSTANTIVE")
    (out/"source_clock.json").write_text(json.dumps(scene_seconds),"utf8")
    ass,srt=cues_to_files(cues,"long",out)
    raw=real_app_screen(out,total)
    cmd(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
         "-xerror","-i",str(raw),"-f","null","-"],timeout=240)
    # Retain the honest real terminal. The source is landscape 16:9.
    final=out/FINAL
    filtergraph=(
        f"[0:v]scale=1920:1080:flags=lanczos,"
        f"drawbox=x=0:y=780:w=iw:h=300:color=0x081827@0.94:t=fill,"
        f"ass={ass.as_posix()},format=yuv420p[v]"
    )
    cmd(["ffmpeg","-nostdin","-hide_banner","-y","-loglevel","error",
         "-i",str(raw),"-i",str(wav),
         "-filter_complex",filtergraph,"-map","[v]","-map","1:a:0",
         "-t",f"{total:.3f}","-r","24",
         "-c:v","libx264","-threads","2","-preset","veryfast","-crf","25",
         "-pix_fmt","yuv420p",
         "-af",AUDIO_MASTERING_FILTER,
         "-ar","48000","-c:a","aac","-b:a","128k",
         "-movflags","+faststart",str(final)],timeout=700)
    try:
        mastering=verify_exact_encoded_master("ffmpeg",final,sha(final),total)
    except EncodedMasteringRefused as e:
        need(str(e)=="Final encoded audio falls outside conservative owner-review mastering band",
             "UNRECOVERABLE_AUDIO_MASTER_FAILURE")
        temp=out/"REMASTER_ONCE.mp4"
        cmd(["ffmpeg","-nostdin","-hide_banner","-y","-loglevel","error",
             "-i",str(final),"-map","0:v:0","-map","0:a:0",
             "-c:v","copy","-af",AUDIO_REMASTER_FILTER,
             "-ar","48000","-c:a","aac","-b:a","128k",
             "-movflags","+faststart",str(temp)],timeout=240)
        mastering=verify_exact_encoded_master("ffmpeg",temp,sha(temp),total)
        temp.replace(final)
    cmd(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
         "-xerror","-i",str(final),"-f","null","-"],timeout=250)
    streams=json.loads(cmd(["ffprobe","-v","error","-show_entries",
        "stream=codec_type,codec_name,width,height:format=duration",
        "-of","json",str(final)],timeout=30))
    video=[x for x in streams["streams"] if x["codec_type"]=="video"]
    audio=[x for x in streams["streams"] if x["codec_type"]=="audio"]
    seconds=float(streams["format"]["duration"])
    need(len(video)==len(audio)==1
         and video[0]["codec_name"]=="h264"
         and audio[0]["codec_name"]=="aac"
         and video[0]["width"]==1920 and video[0]["height"]==1080
         and abs(seconds-total)<.7,"LONG_FINAL_CODEC_OR_CLOCK_BAD")
    receipt={
        "schema":"FLOWMINUTE_B1_EXECUTED_PYTHON_LONG_V1",
        "status":STATUS,"episode_id":EPISODE,
        "source_sha256":sha(raw),"final_sha256":sha(final),
        "fixture_sha256":sha(fixture),"caption_sha256":sha(srt),
        "duration_seconds":round(seconds,3),
        "raw_csv_rows":len(data["original"]),
        "clean_csv_rows":len(data["clean"]),
        "raw_total":data["raw_total"],"clean_total":data["clean_total"],
        "independent_encoded_aac_mastering":mastering,
        "true_software_execution":True,
        "fictional_data_only":True,
        "owner_watched":False,"rights_signed":False,
        "youtube_uploads":0,"youtube_schedules":0,
        "publishing_authorized":False,
    }
    (out/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n","utf8")
    return {"duration":round(seconds,3),"sha256":sha(final),
            "status":STATUS,"owner_review":False,
            "youtube_uploads":0,"youtube_schedules":0}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--stage-runner",action="store_true")
    p.add_argument("--model",type=Path)
    p.add_argument("--voices",type=Path)
    p.add_argument("--offline-test",action="store_true")
    args=p.parse_args()
    if args.stage_runner:
        print(render_stage_runner(args.out,args.out/"source_clock.json"))
    elif args.offline_test:
        need(not args.out.exists(),"OFFLINE_FIXTURE_MUST_BE_NEW")
        args.out.mkdir(parents=True)
        source=make_fixture(args.out)
        print(json.dumps(read_and_clean(source),sort_keys=True))
    else:
        need(args.model is not None and args.voices is not None,
             "ORIGINAL_PINNED_VOICE_MISSING")
        print(json.dumps(render(args.out,args.model,args.voices),sort_keys=True))

if __name__=="__main__":
    main()
