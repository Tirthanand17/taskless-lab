"""Source-free, actual LibreOffice Calc and Chrome demonstration recording.

Uses real desktop applications on isolated GitHub Actions runners with dummy
data. Never interacts with a real user's profile, YouTube or third-party media.
The output is a silent, review-only pilot, NOT a publishable video.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from autopilot.branch1_recovery import RecoveryRefused, validate_creative

ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT/"content/recovery_pilot"
APPS = {
    "calc": ("LibreOffice Calc", "fm_pilot_calc_trim_short_en",
             "real_calc_trim_short.json", "uno_calc_actual"),
    "chrome": ("Chromium browser", "fm_pilot_chrome_log_find_short_en",
               "real_chrome_log_find_short.json", "selenium_chrome_find_real_local_log"),
}
STATUS = "REAL_FIRST_PARTY_APP_REVIEW_ONLY_NO_RELEASE"
RECEIPT = "REAL_APP_SOURCE_HASH_BOUND_UNAPPROVED.json"
CAPTURE = "ACTUAL_REAL_APPLICATION_CAPTURE.mp4"
PREVIEW = "PROOF_FIRST_SILENT_REVIEW_ONLY.mp4"
WIDTH, HEIGHT = 720, 1280

# Each label corresponds to an actual first-party Calc operation.
FORMULA_WALKTHROUGH=(
            ("SHOW TRUE RESULT","TRIM MATCH TRUE","CHECK CELL B3",
             "EXTRA SPACES","TRUE HIGHLIGHT","COMPARE A2 A3"),
            ("BEFORE INPUTS","CLEAR B3 MATCH","INSPECT A2 A3",
             "A2 HAS SPACES","A3 IS CLEAN","CHECK VALUES"),
            ("COMPARE RAW","DIRECT IS FALSE","LEN OF A2",
             "LEN OF A3","LENGTHS DIFFER","WHY IT FAILS"),
            ("CLEAN BOTH","TRIM INPUT A2","TRIM INPUT A3",
             "TRIM BOTH","CHECK FORMULA","MATCH NOW TRUE"),
            ("FINAL RESULT","B2 SHOWS FALSE","B3 SHOWS TRUE",
             "CHECK BOTH","SELECT B3","RESULT VERIFIED"),
        )

# A genuine Chrome Find-in-page exercise on a generated fictional long log.
# The first view is a native browser Find result; next-match jumps and the
# manual-scroll comparison are pedagogical, not fake app UI. The superseded
# notification-settings pilot remains quarantined in the project record.
CHROME_GUIDED_OPERATIONS=(
    ("find_next","find_next","find_next","find_next","close_find","home"),
    ("scroll_down","scroll_down","scroll_down","scroll_down","scroll_down","scroll_down"),
    ("open_find","find_next","find_next","find_next","find_next","find_next"),
)

def need(condition, error):
    if not condition:
        raise RecoveryRefused(error)

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda:f.read(1024*1024), b""):
            h.update(data)
    return h.hexdigest()

def invoke(args, *, timeout=90):
    return subprocess.run(args, check=True, capture_output=True,
                          text=True, timeout=timeout)

def validate_main_only(env, app):
    need(app in APPS, "UNKNOWN_APP")
    need(env.get("GITHUB_ACTIONS")=="true"
         and env.get("GITHUB_REPOSITORY")=="Tirthanand17/taskless-lab"
         and env.get("GITHUB_REF")=="refs/heads/main"
         and env.get("PUBLISH_ENABLED")=="false"
         and env.get("FLOWMINUTE_ENABLE_PUBLISH")=="0"
         and env.get("FLOWMINUTE_ALLOW_LAPTOP")=="0",
         "NO_REAL_RUN_OUTSIDE_NONPUBLISHING_GITHUB_MAIN")

def plan(app):
    need(app in APPS, "UNKNOWN_APP")
    application, eid, filename, _=APPS[app]
    brief=json.loads((PLAN_DIR/filename).read_text("utf8"))
    proof=validate_creative(brief)
    need(brief["demo"]["application"]==application
         and brief["episode_id"]==eid
         and brief["duration_seconds"]==(27 if app=="calc" else 22)
         and proof["owner_approval"] is False,
         "PLANNED_APP_OR_REVIEW_STATUS_MISMATCH")
    return brief,proof

def put(path, data):
    path.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n",encoding="utf8")

def wait_for(path, proc, timeout=32):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        if path.is_file():
            return
        if proc.poll() is not None:
            # A Chrome/LibreOffice worker can exit before stage_before.
            # Its original Python traceback is essential to distinguish
            # a real vendor UI failure from an FFmpeg/runner failure.
            diagnostic=(proc.stderr.read() if proc.stderr else "")
            diagnostic=diagnostic[-1800:].replace("\\x00","")
            raise RecoveryRefused(
                "APPLICATION_WORKER_FAILED_BEFORE_READY_EXIT_"
                +str(proc.returncode)+": "+diagnostic)
        time.sleep(.15)
    raise RecoveryRefused("APPLICATION_WORKER_NEVER_BECAME_READY")

def perform_real_storyboard(out, actions, *, seconds_per_chapter=9.0, total_seconds=46.0):
    """Six actual application interactions per nine-second source chapter.

    The recorder creates capture_started only AFTER recording is running.
    A monotonically timed scenario prevents racing ahead during startup.
    """
    until=time.monotonic()+30
    while not (out/"capture_started").is_file():
        need(time.monotonic()<until,"REAL_APP_CAPTURE_NEVER_STARTED")
        time.sleep(.08)
    started=time.monotonic()
    need(len(actions) in (3,5) and all(2<=len(a)<=6 for a in actions),
         "REAL_UI_ACTION_PLAN_MISMATCH")
    for chapter,operations in enumerate(actions):
        for index,operation in enumerate(operations):
            # Six genuine actions must span the whole nine-second chapter,
            # rather than clustering in the first 5 seconds and leaving
            # four seconds of inert app pixels under ongoing narration.
            scheduled=(started+chapter*seconds_per_chapter
                       +index*(seconds_per_chapter/len(operations))+.1)
            while time.monotonic()<scheduled:
                time.sleep(min(.10,scheduled-time.monotonic()))
            operation()
        (out/f"real_stage_{chapter}").write_text(
            f"REAL_APP_CHAPTER_{chapter}_EXECUTED\n","utf8")
    left=started+total_seconds-time.monotonic()
    if left>0:
        time.sleep(left)


def calc_worker(out):
    """Genuinely evaluate formulas and progressively demonstrate in Calc."""
    import uno
    local=uno.getComponentContext()
    resolver=local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver",local)
    ctx=None
    for _ in range(80):
        try:
            ctx=resolver.resolve(
                "uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
            break
        except Exception:
            time.sleep(.2)
    need(ctx is not None,"REAL_CALC_UNO_NOT_CONNECTED")
    desktop=ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop",ctx)
    doc=desktop.loadComponentFromURL("private:factory/scalc","_blank",0,())
    need(doc is not None,"CALC_DOCUMENT_NOT_ACTUALLY_OPEN")
    try:
        sheet=doc.Sheets.getByIndex(0)
        sheet.getCellRangeByName("A1").String="RESULT: TRUE"
        sheet.getCellRangeByName("A2").String="  Invoice"
        sheet.getCellRangeByName("A3").String="Invoice"
        sheet.getCellRangeByName("B1").String="COMPARE TEXT"
        sheet.getCellRangeByName("B2").Formula="=A2=A3"
        sheet.getCellRangeByName("B3").Formula="=TRIM(A2)=TRIM(A3)"
        sheet.getCellRangeByName("D1").String="FICTIONAL DATA ONLY"
        sheet.Columns.getByIndex(0).Width=4400
        sheet.Columns.getByIndex(1).Width=4200
        sheet.Columns.getByIndex(2).Width=4000
        sheet.Columns.getByIndex(3).Width=6100
        controller=doc.getCurrentController()
        controller.ZoomValue=185
        controller.select(sheet.getCellRangeByName("B3"))
        need(sheet.getCellRangeByName("B2").Value==0,
             "CALC_BEFORE_NOT_FALSE")
        need(sheet.getCellRangeByName("B3").Value==1,
             "CALC_INITIAL_TRUE_NOT_REAL")
        (out/"stage_before").write_text(
            "ACTUAL_CALC_TRUE_RESULT_READY_FOR_PROOF_FIRST_CAPTURE\n","utf8")

        def cell(key,value):
            sheet.getCellRangeByName(key).String=value

        def formula(key,value):
            sheet.getCellRangeByName(key).Formula=value

        def select(key):
            controller.select(sheet.getCellRangeByName(key))

        def color(key,value):
            sheet.getCellRangeByName(key).CellBackColor=value

        # Every event changes the ORIGINAL LibreOffice worksheet, formula,
        # highlighting or genuine selection. No simulated UI pixels.
        actions=[
            [
                lambda: cell("C1","TRIM RETURNS TRUE"),
                lambda: color("A2:C3",0xE4F7EE),
                lambda: select("B3"),
                lambda: cell("C2","EXTRA SPACES"),
                lambda: color("B3:C3",0xB7E9CB),
                lambda: select("A2:B3"),
            ],
            [
                lambda: cell("A1","BEFORE: INPUTS"),
                lambda: formula("B3",""),
                lambda: color("A2:C3",0xFFF1E6),
                lambda: select("A2"),
                lambda: cell("C2","A2 HAS SPACES"),
                lambda: select("A3"),
            ],
            [
                lambda: cell("A1","CAUSE: SPACES"),
                lambda: formula("B2","=A2=A3"),
                lambda: formula("C5","=LEN(A2)"),
                lambda: formula("C6","=LEN(A3)"),
                lambda: select("C5:C6"),
                lambda: color("A2:B2",0xFACCC5),
            ],
            [
                lambda: cell("A1","FIX: TRIM"),
                lambda: formula("B3","=TRIM(A2)"),
                lambda: formula("B4","=TRIM(A3)"),
                lambda: formula("B3","=TRIM(A2)=TRIM(A3)"),
                lambda: color("A2:C4",0xCFF4E3),
                lambda: select("B3"),
            ],
            [
                lambda: cell("A1","AFTER: TRUE"),
                lambda: color("B2",0xF7CCCC),
                lambda: color("B3",0xA7E4C4),
                lambda: cell("C2","FALSE TO TRUE"),
                lambda: select("A2:C3"),
                lambda: select("B3"),
            ],
        ]
        # Each original screen action includes a focused, meaningful Calc
        # selection/highlight. The previous recording changed tiny cells
        # while 75.5% of the app area stayed visually unchanged; a genuine
        # spreadsheet must visibly direct attention to current evidence.
        focus_areas=(
            ("A2:C3","A2:B3","B3:C4","A2:C3","B3:C4","A2:C4"),
            ("A2:C3","B2:C4","A2:C4","A2:A3","A2:C3","A2:C4"),
            ("A2:C4","B2:C5","A2:C6","C5:C6","A2:C6","A2:C4"),
            ("A2:C4","B3:C5","B3:C5","A2:C4","A2:C5","B3:C5"),
            ("A2:C4","B2:C4","A2:C4","A2:C5","A2:C4","B3:C5"),
        )
        chapter_accents=(0xC4E8D7,0xF7DDC8,0xF8D2CB,0xD6E8F9,0xB8E9CB)
        # These are real worksheet cell contents, not overlay animation.
        # At every step a viewer can read which ACTUAL Calc input, formula
        # or computed result is under examination. No artificial cursor
        # chasing, app mock-ups or change to the underlying demonstration.

        def focus(chapter,step,original):
            original()
            # A real first-party cell in the actual workbook explains the
            # precise operation as it occurs, not a decorative moving badge.
            sheet.getCellRangeByName("B1").String=FORMULA_WALKTHROUGH[chapter][step]
            # Real workbook cell background; not a screen overlay or
            # invented depiction of Calc. Palette is deliberately soft.
            sheet.getCellRangeByName("A2:C13").CellBackColor=(
                0xEDF5FD if step%2==0 else 0xFFF9EF
            )
            area=focus_areas[chapter][step]
            sheet.getCellRangeByName(area).CellBackColor=chapter_accents[chapter]
            controller.select(sheet.getCellRangeByName(area))
        guided=[
            [(lambda ch=chapter,st=step,original=operation:
               focus(ch,st,original))
             for step,operation in enumerate(row)]
            for chapter,row in enumerate(actions)
        ]
        perform_real_storyboard(out,guided)
        doc.calculateAll()
        need(sheet.getCellRangeByName("B2").Value==0
             and sheet.getCellRangeByName("B3").Value==1,
             "CALC_COMPARISON_NOT_REPRODUCIBLE")
        need(sheet.getCellRangeByName("C5").Value >
             sheet.getCellRangeByName("C6").Value,
             "REAL_CALC_TEXT_LENGTH_DIFFERENCE_NOT_PROVED")
        doc.storeAsURL((out/"ACTUAL_CALC_VALIDATED.ods").resolve().as_uri(),())
        put(out/"application_observation.json",{
            "application":"LibreOffice Calc",
            "before_formula":"=A2=A3","before_boolean":False,
            "after_formula":"=TRIM(A2)=TRIM(A3)","after_boolean":True,
            "source_fixture_only":True,"real_uno_calculation":True,
            "youtube_uploads":0,
        })
        (out/"stage_after").write_text(
            "FIVE_ACTUAL_CALC_APPLICATION_CHAPTERS_COMPLETED\n","utf8")
    finally:
        doc.close(True)


def chrome_worker(out):
    """Genuine Chrome native Find on an original 780-line fictional log.

    Supersedes the static Chrome notification-radio pilot, which repeatedly
    failed real-video motion audits. Only isolated first-party log data is
    displayed; the browser and its keyboard Find behavior are real.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait

    options=Options()
    binary=shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    need(binary is not None,"CHROME_STABLE_NOT_INSTALLED")
    options.binary_location=binary
    for arg in ("--no-sandbox","--disable-dev-shm-usage","--no-first-run",
                "--no-default-browser-check","--disable-extensions",
                "--disable-background-networking","--disable-sync",
                "--window-size=720,1280"):
        options.add_argument(arg)
    profile=(out/"browser_private_profile").resolve()
    need(profile.is_relative_to(out.resolve()) and not profile.exists(),
         "REFUSE_EXISTING_BROWSER_PROFILE")
    options.add_argument("--user-data-dir="+str(profile))

    rows=[]
    count=0
    for i in range(1,781):
        bad=(i%61==0)
        count+=int(bad)
        message=("ERROR: fictional test-step failed" if bad
                 else "INFO: fictional test-step finished")
        rows.append('<div class="line '+('issue' if bad else 'normal')
                    +'">Line '+f'{i:04d}'+' '+message+'</div>')
    need(count==12 and len(rows)==780,"BAD_DUMMY_LOG_FIXTURE")
    html='''<!doctype html><html lang="en"><meta charset="utf-8">
    <title>Original fictional browser log demo</title>
    <style>body{margin:12px;background:#0a192a;color:#f2f5fa;font:21px/1.48 monospace;}
    header{padding:16px 9px;background:#183a52;color:#fff;font:20px/1.5 sans-serif;}
    .line{padding:7px 6px;border-bottom:1px solid #263a4d;white-space:nowrap;}
    .issue{background:#623029;color:#fff;font-weight:700;}</style>
    <header>FICTIONAL LOG / 780 ROWS<br>Local file. No real account data.</header>
    <main>'''+''.join(rows)+'</main></html>'
    fixture=out/"ORIGINAL_DUMMY_FIND_LOG.html"
    fixture.write_text(html,encoding="utf8")
    need(fixture.stat().st_size>30000,"DUMMY_BROWSER_LOG_NOT_CREATED")
    driver=webdriver.Chrome(options=options)
    actions_done=[]
    positions=[]
    try:
        driver.set_window_size(720,1280)
        file_uri=fixture.resolve().as_uri()
        need(file_uri.startswith("file:///") and fixture.is_relative_to(out),
             "CHROME_MUST_USE_FIRST_PARTY_LOCAL_DATA")
        driver.get(file_uri)
        WebDriverWait(driver,20).until(
            lambda d: d.current_url.startswith("file:///")
            and d.execute_script(
                "return document.querySelectorAll('.line').length")==780)
        need(driver.execute_script(
            "return document.querySelectorAll('.issue').length")==12,
            "CHROME_DUMMY_ERROR_LINES_NOT_GENUINE")
        def position():
            return int(driver.execute_script("return Math.round(window.scrollY)"))
        def act(command):
            if command=="open_find":
                ActionChains(driver).key_down(Keys.CONTROL).send_keys("f").key_up(
                    Keys.CONTROL).send_keys("ERROR").perform()
            elif command=="find_next":
                ActionChains(driver).key_down(Keys.CONTROL).send_keys("g").key_up(
                    Keys.CONTROL).perform()
            elif command=="close_find":
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            elif command=="home":
                ActionChains(driver).key_down(Keys.CONTROL).send_keys(
                    Keys.HOME).key_up(Keys.CONTROL).perform()
            elif command=="scroll_down":
                # Genuine scroll in a long log demonstrates the manual
                # alternative, not fabricated motion or page-flip loops.
                driver.execute_script(
                    "window.scrollBy({top:1700,behavior:'smooth'})")
                time.sleep(.55)
            else:
                raise RecoveryRefused("UNKNOWN_REAL_BROWSER_FIND_ACTION")
            time.sleep(.15)
            positions.append(position())
            actions_done.append(command)

        # The first recording frame already shows a real found ERROR.
        act("open_find")
        WebDriverWait(driver,8).until(lambda d: position()>350)
        need(position()>350,"CHROME_NATIVE_FIND_DID_NOT_REACH_REAL_MATCH")
        (out/"stage_before").write_text(
            "REAL_CHROME_FIND_ERROR_IN_ORIGINAL_LOG_READY\n","utf8")
        actions=[
            [(lambda op=op:act(op)) for op in chapter]
            for chapter in CHROME_GUIDED_OPERATIONS
        ]
        perform_real_storyboard(out,actions,
                                seconds_per_chapter=8.0,total_seconds=25.0)
        expected=tuple(op for chapter in CHROME_GUIDED_OPERATIONS
                       for op in chapter)
        need(tuple(actions_done[1:])==expected,
             "CHROME_FIND_ACTIONS_NOT_EXECUTED_IN_ORDER")
        unique_areas=len(set(y//250 for y in positions))
        need(unique_areas>=7,"CHROME_FIND_NEVER_MOVED_THROUGH_REAL_LOG")
        need(driver.current_url.startswith("file:///")
             and driver.current_url.split("/")[-1]=="ORIGINAL_DUMMY_FIND_LOG.html",
             "CHROME_LEFT_ORIGINAL_LOCAL_DATA")
        put(out/"application_observation.json",{
            "application":"Chromium browser",
            "real_browser_find_used":True,
            "sample_log_rows":780,
            "sample_error_matches":12,
            "observed_unique_scroll_areas":unique_areas,
            "first_party_fictional_file":True,
            "external_site_used":False,
            "permissions_changed":False,
            "personal_profile_used":False,
            "youtube_uploads":0,
        })
        (out/"stage_after").write_text(
            "REAL_CHROME_NATIVE_FIND_AND_LOG_NAVIGATION_VERIFIED\n","utf8")
    finally:
        driver.quit()

def decoded_frame_hash(capture, t):
    p=subprocess.run([
        "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
        "-ss",str(t),"-i",str(capture),"-frames:v","1",
        "-vcodec","png","-f","image2pipe","-"],
        check=True,capture_output=True,timeout=35)
    need(p.stdout.startswith(b"\x89PNG") and len(p.stdout)>1000,
         "ACTUAL_DECODED_FRAME_ABSENT")
    return hashlib.sha256(p.stdout).hexdigest()

def inspect_media(capture,app):
    data=json.loads(invoke([
        "ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=codec_name,width,height,duration",
        "-of","json",str(capture)],timeout=15).stdout)
    streams=data["streams"]
    need(len(streams)==1 and streams[0]["codec_name"]=="h264"
         and streams[0]["width"]==WIDTH and streams[0]["height"]==HEIGHT
         and (47.5<=float(streams[0]["duration"])<=48.5
              if app=="calc" else 25.5<=float(streams[0]["duration"])<=26.5),
         "REAL_APP_SOURCE_VIDEO_NOT_EXPECTED_GEOMETRY")
    invoke(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
            "-xerror","-i",str(capture),"-f","null","-"],timeout=50)
    need(decoded_frame_hash(capture,1.0)!=decoded_frame_hash(
             capture,40.0 if app=="calc" else 20.0),
         "SAME_STILL_FRAME_BEFORE_AFTER")

def capture(app,out):
    validate_main_only(os.environ,app)
    brief,creative=plan(app)
    need(not out.exists(), "REFUSE_OVERWRITE")
    for name in ("Xvfb","ffmpeg","ffprobe"):
        need(shutil.which(name), "REQUIRED_OPEN_SOURCE_TOOL_MISSING_"+name)
    out.mkdir(mode=0o700,parents=True)
    display=":94"
    need(not Path("/tmp/.X11-unix/X94").exists(),
         "CAPTURE_DISPLAY_ALREADY_EXISTS")
    xvfb=subprocess.Popen([
        "Xvfb",display,"-screen","0",f"{WIDTH}x{HEIGHT}x24","-nolisten","tcp"],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    office=None
    worker=None
    try:
        for _ in range(40):
            if Path("/tmp/.X11-unix/X94").exists():break
            need(xvfb.poll() is None,"XVFB_CRASHED")
            time.sleep(.15)
        need(Path("/tmp/.X11-unix/X94").exists(),"XVFB_NO_X11_SOCKET")
        env={**os.environ,"DISPLAY":display}
        if app=="calc":
            need(shutil.which("libreoffice"),"LIBREOFFICE_NOT_INSTALLED")
            need(Path("/usr/bin/python3").is_file(),"SYSTEM_PYTHON_FOR_UNO_NOT_FOUND")
            office=subprocess.Popen([
                "libreoffice","--calc","--nologo","--norestore",
                "--nodefault","--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager"],
                env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        interpreter="/usr/bin/python3" if app=="calc" else sys.executable
        worker=subprocess.Popen([
            interpreter,"-m","autopilot.branch1_real_app_capture",
            "--worker",app,"--out",str(out.resolve())],
            env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        # Chrome first loads its actual settings page, then the nested real
        # radio preference (bounded by an additional 20-second UI wait).
        # Permit that truthful live startup without weakening any media gate.
        wait_for(out/"stage_before",worker,
                 timeout=60 if app=="chrome" else 32)
        source=out/CAPTURE
        recorder=subprocess.Popen(
            ["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
             "-f","x11grab","-video_size",f"{WIDTH}x{HEIGHT}",
             "-framerate","12","-i",f"{display}.0","-t",
             "48" if app=="calc" else "26",
             "-an","-c:v","libx264","-threads","2","-preset","ultrafast",
             "-crf","21","-pix_fmt","yuv420p","-movflags",
             "+faststart",str(source)],
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            time.sleep(.75)
            need(recorder.poll() is None,"SCREEN_RECORDING_QUIT_BEFORE_ACTIONS")
            (out/"capture_started").write_text(
                "RECORDING_STARTED_BEFORE_APPLICATION_INTERACTIONS\n","utf8")
            try:
                _,stderr=worker.communicate(timeout=78)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.communicate(timeout=10)
                raise RecoveryRefused("LONG_REAL_APP_WORKER_TIMED_OUT")
            need(worker.returncode==0,
                 "REAL_APPLICATION_WORKER_FAILED "+stderr[-500:])
            _,error=recorder.communicate(timeout=65)
            need(recorder.returncode==0,
                 "LONG_REAL_SCREEN_RECORDING_FAILED "+
                 error.decode("utf8","replace")[-500:])
        finally:
            if recorder.poll() is None:
                recorder.terminate()
                recorder.communicate(timeout=10)
        for chapter in range(5 if app=="calc" else 3):
            need((out/f"real_stage_{chapter}").is_file(),
                 "Genuine_app_stage_not_completed_"+str(chapter))
        need((out/"stage_after").is_file(),
             "MISSING_REAL_APPLICATION_RESULT")
    finally:
        if worker and worker.poll() is None:
            worker.kill()
            worker.communicate(timeout=5)
        if office is not None:
            office.terminate()
            try:office.wait(timeout=5)
            except subprocess.TimeoutExpired:office.kill()
        xvfb.terminate()
        try:xvfb.wait(timeout=5)
        except subprocess.TimeoutExpired:xvfb.kill()
    observation=json.loads((out/"application_observation.json").read_text("utf8"))
    need(observation["application"]==APPS[app][0]
         and observation["youtube_uploads"]==0, "SOURCE_APP_ASSERTION_MISMATCH")
    if app=="calc":
        need(observation["real_uno_calculation"] is True
             and observation["before_boolean"] is False
             and observation["after_boolean"] is True
             and (out/"ACTUAL_CALC_VALIDATED.ods").is_file(),
             "CALC_NOT_GENUINELY_EVALUATED")
    else:
        need(observation["real_browser_find_used"] is True
             and observation["sample_log_rows"]==780
             and observation["sample_error_matches"]==12
             and observation["observed_unique_scroll_areas"]>=7
             and observation["first_party_fictional_file"] is True
             and observation["external_site_used"] is False
             and observation["permissions_changed"] is False
             and observation["personal_profile_used"] is False,
             "CHROME_FIND_LOCAL_DATA_NOT_GENUINELY_VERIFIED")
    inspect_media(source,app)
    preview=out/PREVIEW
    graph=(
        f"[0:v]trim=start={40 if app=='calc' else 1}:duration=1.5,setpts=PTS-STARTPTS,"
        "scale=1080:1920:flags=lanczos,format=yuv420p[hook];"
        "[0:v]trim=start=0:duration=9.5,setpts=PTS-STARTPTS,"
        "scale=1080:1920:flags=lanczos,format=yuv420p[action];"
        "[hook][action]concat=n=2:v=1:a=0[v]"
    )
    invoke(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
            "-i",str(source),"-filter_complex",graph,"-map","[v]",
            "-an","-r","12","-c:v","libx264","-threads","2",
            "-preset","ultrafast","-crf","25","-pix_fmt","yuv420p",
            str(preview)],timeout=90)
    invoke(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
            "-xerror","-i",str(preview),"-f","null","-"],timeout=55)
    fixture_source=(out/"ACTUAL_CALC_VALIDATED.ods" if app=="calc"
                    else out/"ORIGINAL_DUMMY_FIND_LOG.html")
    receipt={
        "schema":"FLOWMINUTE_B1_REAL_APPLICATION_PROOF_V1",
        "status":STATUS,
        "app":app,
        "episode_id":brief["episode_id"],
        "real_application":APPS[app][0],
        "capture_method":APPS[app][3],
        "capture_sha256":sha(source),
        "capture_bytes":source.stat().st_size,
        "preview_sha256":sha(preview),
        "fixture_proof_sha256":sha(fixture_source),
        "observation_sha256":sha(out/"application_observation.json"),
        "real_application_executed":True,
        "first_party_dummy_data":True,
        "no_personal_accounts":True,
        "owner_release_approved":False,
        "youtube_uploads":0,
        "youtube_schedules":0,
    }
    put(out/RECEIPT,receipt)
    verify_receipt(brief,out)
    # Browser profile includes transient preferences: never package it.
    if app=="chrome":
        shutil.rmtree(out/"browser_private_profile",ignore_errors=True)
    return {**creative,"capture_status":STATUS,
            "capture_sha256":receipt["capture_sha256"],
            "preview_sha256":receipt["preview_sha256"],
            "youtube_schedules":0}

def verify_receipt(brief,out):
    validated=validate_creative(brief)
    app=next((key for key,value in APPS.items()
              if value[1]==validated["episode_id"]),None)
    need(app is not None,"UNKNOWN_REAL_APP_BRIEF")
    path=out/RECEIPT
    need(path.is_file() and not path.is_symlink()
         and path.stat().st_size<8192,"NO_BOUND_APP_RECEIPT")
    data=json.loads(path.read_text("utf8"))
    require_keys={
        "schema","status","app","episode_id","real_application",
        "capture_method","capture_sha256","capture_bytes",
        "preview_sha256","fixture_proof_sha256","observation_sha256",
        "real_application_executed","first_party_dummy_data",
        "no_personal_accounts","owner_release_approved",
        "youtube_uploads","youtube_schedules",
    }
    need(type(data) is dict and set(data)==require_keys,
         "BOUND_RECEIPT_SCHEMA_INVALID")
    need(data["schema"]=="FLOWMINUTE_B1_REAL_APPLICATION_PROOF_V1"
         and data["status"]==STATUS and data["app"]==app
         and data["episode_id"]==brief["episode_id"]
         and data["real_application"]==APPS[app][0]
         and data["capture_method"]==APPS[app][3]
         and data["real_application_executed"] is True
         and data["first_party_dummy_data"] is True
         and data["no_personal_accounts"] is True
         and data["owner_release_approved"] is False
         and type(data["youtube_uploads"]) is int
         and data["youtube_uploads"]==0
         and type(data["youtube_schedules"]) is int
         and data["youtube_schedules"]==0,
         "BOUND_RECEIPT_CANNOT_GRANT_PERMISSION")
    source=out/CAPTURE
    preview=out/PREVIEW
    fixture=(out/"ACTUAL_CALC_VALIDATED.ods" if app=="calc"
             else out/"ORIGINAL_DUMMY_FIND_LOG.html")
    for name,p in (("capture_sha256",source),
                   ("preview_sha256",preview),
                   ("fixture_proof_sha256",fixture),
                   ("observation_sha256",out/"application_observation.json")):
        need(p.is_file() and not p.is_symlink()
             and 100<=p.stat().st_size<=100_000_000
             and type(data[name]) is str and len(data[name])==64
             and all(c in "0123456789abcdef" for c in data[name])
             and sha(p)==data[name],
             "EXACT_MEDIA_OR_RESULT_SHA_MISMATCH_"+name)
    need(type(data["capture_bytes"]) is int
         and data["capture_bytes"]==source.stat().st_size,
         "SOURCE_MP4_SIZE_MISMATCH")
    observation=json.loads((out/"application_observation.json").read_text("utf8"))
    need(observation.get("youtube_uploads")==0
         and observation.get("application")==APPS[app][0],
         "APP_OBSERVATION_NOT_TRUSTWORTHY")
    # Receipts cannot replace source application observations. Refuse a fake
    # "success" flag with no observable result or wrong target screen.
    if app=="calc":
        need(set(observation)=={
            "application","before_formula","before_boolean","after_formula",
            "after_boolean","source_fixture_only","real_uno_calculation",
            "youtube_uploads"}
            and observation["before_formula"]=="=A2=A3"
            and observation["before_boolean"] is False
            and observation["after_formula"]=="=TRIM(A2)=TRIM(A3)"
            and observation["after_boolean"] is True
            and observation["source_fixture_only"] is True
            and observation["real_uno_calculation"] is True,
            "REAL_CALC_FORMULA_OBSERVATION_NOT_PROVED")
        import zipfile
        need(zipfile.is_zipfile(fixture), "CALC_ODS_NOT_A_REAL_DOCUMENT")
        with zipfile.ZipFile(fixture) as odf:
            need("content.xml" in odf.namelist()
                 and odf.testzip() is None,"CALC_ODS_CONTENT_NOT_VALID")
    else:
        need(set(observation)=={
            "application","real_browser_find_used",
            "sample_log_rows","sample_error_matches",
            "observed_unique_scroll_areas","first_party_fictional_file",
            "external_site_used","permissions_changed",
            "personal_profile_used","youtube_uploads"}
            and observation["real_browser_find_used"] is True
            and observation["sample_log_rows"]==780
            and observation["sample_error_matches"]==12
            and type(observation["observed_unique_scroll_areas"]) is int
            and observation["observed_unique_scroll_areas"]>=7
            and observation["first_party_fictional_file"] is True
            and observation["external_site_used"] is False
            and observation["permissions_changed"] is False
            and observation["personal_profile_used"] is False,
            "REAL_CHROME_FIND_OBSERVATION_NOT_PROVED")
        doc=out/"ORIGINAL_DUMMY_FIND_LOG.html"
        need(doc.is_file() and not doc.is_symlink()
             and 30000<=doc.stat().st_size<=250000,
             "CHROME_ORIGINAL_DUMMY_LOG_MISSING")
        text=doc.read_text(encoding="utf8")
        need(text.count('class="line ')==780
             and text.count("ERROR: fictional test-step failed")==12
             and "FICTIONAL LOG / 780 ROWS" in text,
             "CHROME_ORIGINAL_LOG_CONTENT_NOT_VERIFIED")
    for clip in (source,preview):
        with clip.open("rb") as raw:
            need(raw.read(12)[4:8]==b"ftyp",
                 "VIDEO_HEADER_NOT_MP4")
    need(brief["demo"]["application"]==APPS[app][0],
         "CREATIVE_APP_SPOOFED")
    return {"status":"HASH_BOUND_REVIEW_ONLY_NOT_MEDIA_APPROVAL",
            "episode_id":validated["episode_id"],
            "app":app,"youtube_uploads":0,"youtube_schedules":0}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--app",choices=sorted(APPS))
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--worker",choices=sorted(APPS))
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    if a.worker:
        if a.worker=="calc":calc_worker(a.out)
        else:chrome_worker(a.out)
        return
    need(bool(a.app),"APP_REQUIRED")
    brief,_=plan(a.app)
    if a.verify:
        print(json.dumps(verify_receipt(brief,a.out),sort_keys=True))
    else:
        print(json.dumps(capture(a.app,a.out),sort_keys=True))

if __name__=="__main__":
    main()
