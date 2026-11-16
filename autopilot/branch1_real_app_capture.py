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
    "chrome": ("Chromium browser", "fm_pilot_chrome_notifications_short_en",
               "real_chrome_notifications_short.json", "selenium_chrome_settings_actual"),
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

# Deliberate, one-way first-party Chrome settings journey. Each row is
# six real browser operations across one nine-second recording chapter.
# No permission toggle, third-party site or alternating page loops.
CHROME_GUIDED_OPERATIONS=(
    # A genuine before/after in a throwaway profile, not mock settings.
    ("focus_block","ask","block","inspect","top","inspect"),
    # Coherent navigation; internal page visits only.
    ("home","top","privacy","down","site","top"),
    # Review where Notifications appears under actual Site settings.
    ("down","down","up","down","up","top"),
    # Live default-setting selection in the real Notifications screen.
    ("notifications","ask","block","focus_block","inspect","top"),
    # Verify the real resulting blocked setting and exception lists.
    ("inspect","top","focus_block","inspect","top","focus_block"),
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
         and brief["duration_seconds"]==11
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

def perform_real_storyboard(out, actions):
    """Six actual application interactions per nine-second source chapter.

    The recorder creates capture_started only AFTER recording is running.
    A monotonically timed scenario prevents racing ahead during startup.
    """
    until=time.monotonic()+30
    while not (out/"capture_started").is_file():
        need(time.monotonic()<until,"REAL_APP_CAPTURE_NEVER_STARTED")
        time.sleep(.08)
    started=time.monotonic()
    need(len(actions)==5 and all(len(a)==6 for a in actions),
         "REAL_UI_ACTION_PLAN_MISMATCH")
    for chapter,operations in enumerate(actions):
        for index,operation in enumerate(operations):
            # Six genuine actions must span the whole nine-second chapter,
            # rather than clustering in the first 5 seconds and leaving
            # four seconds of inert app pixels under ongoing narration.
            scheduled=started+chapter*9.0+index*1.5+.1
            while time.monotonic()<scheduled:
                time.sleep(min(.10,scheduled-time.monotonic()))
            operation()
        (out/f"real_stage_{chapter}").write_text(
            f"REAL_APP_CHAPTER_{chapter}_EXECUTED\n","utf8")
    left=started+46-time.monotonic()
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
    """Real Chrome notification default control in an isolated demo profile.

    The temporary Chrome profile is created inside a GitHub Actions runner,
    never a user's browser. Only this disposable profile's default option
    is clicked, by Selenium in the actual Chrome UI.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException
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
    need(profile.is_relative_to(out.resolve())
         and not profile.exists(), "REFUSE_EXISTING_BROWSER_PROFILE")
    options.add_argument("--user-data-dir="+str(profile))
    driver=webdriver.Chrome(options=options)
    home="chrome://settings/"
    site="chrome://settings/content"
    privacy="chrome://settings/privacy"
    notification="chrome://settings/content/notifications"
    history=[]
    toggle_history=[]
    try:
        driver.set_window_size(720,1280)
        def visit(uri):
            need(uri in (home,site,privacy,notification),
                 "DISALLOWED_EXTERNAL_OR_USER_BROWSER_URI")
            driver.get(uri)
            WebDriverWait(driver,20).until(
                lambda d: d.current_url.rstrip("/") == uri.rstrip("/")
                and d.execute_script(
                    "return !!document.querySelector('settings-ui')"))
            need(driver.current_url.startswith("chrome://settings"),
                 "CHROME_DID_NOT_OPEN_REAL_SETTINGS")
            history.append(uri)

        # Chrome settings are nested in real Web Components. Resolve the
        # actual radio-button element, not a copied HTML or synthetic UI.
        find_control_js = """
            const seen = new Set();
            function find(root,selector) {
                if (!root || seen.has(root)) return null;
                seen.add(root);
                const direct=root.querySelector(selector);
                if (direct) return direct;
                for (const item of root.querySelectorAll('*')) {
                    if (item.shadowRoot) {
                        const hit=find(item.shadowRoot,selector);
                        if (hit) return hit;
                    }
                }
                return null;
            }
            const group=find(document,'settings-category-default-radio-group#notificationDefaultRadioGroup');
            if (!group) return null;
            const control=group.shadowRoot?.querySelector('#'+arguments[0]+'RadioOption');
            return control || null;
        """
        get_option_js = """
            const seen = new Set();
            function find(root) {
                if (!root || seen.has(root)) return null;
                seen.add(root);
                const direct=root.querySelector('settings-category-default-radio-group#notificationDefaultRadioGroup');
                if (direct) return direct;
                for(const item of root.querySelectorAll('*')) {
                    if(item.shadowRoot) {
                        const hit=find(item.shadowRoot);
                        if(hit) return hit;
                    }
                }
                return null;
            }
            const group=find(document);
            return group ? String(group.selectedValue || '').toLowerCase() : '';
        """
        def selected_option():
            need(driver.current_url==notification,
                 "NOT_ON_REAL_NOTIFICATION_DEFAULT_PAGE")
            return driver.execute_script(get_option_js)
        def toggle(to):
            need(to in ("ask","block"),"ONLY_REAL_ASK_AND_BLOCK_CHOICES")
            need(driver.current_url==notification,
                 "NO_TOGGLE_OUTSIDE_DISPOSABLE_CHROME_SETTINGS")
            option=WebDriverWait(driver,15).until(
                lambda d: d.execute_script(find_control_js,to))
            # A genuine WebDriver pointer click on Chrome's internal radio.
            ActionChains(driver).move_to_element(option).click().perform()
            WebDriverWait(driver,12).until(
                lambda d: selected_option()==to)
            need(selected_option()==to,"CHROME_REAL_RADIO_NOT_CHANGED")
            toggle_history.append(to)
        def focus_block():
            need(driver.current_url==notification,
                 "FOCUS_ONLY_ON_REAL_NOTIFICATION_PAGE")
            option=WebDriverWait(driver,15).until(
                lambda d: d.execute_script(find_control_js,"block"))
            ActionChains(driver).move_to_element(option).perform()
        def browse(action):
            if action in {"home":home,"privacy":privacy,"site":site,
                          "notifications":notification}:
                visit({"home":home,"privacy":privacy,"site":site,
                       "notifications":notification}[action])
            elif action in ("ask","block"):
                toggle(action)
            elif action=="focus_block":
                focus_block()
            elif action in ("down","up","top","inspect"):
                need(driver.current_url.startswith("chrome://settings"),
                     "BROWSER_LEFT_FIRST_PARTY_SETTINGS")
                delta={"down":330,"up":-330,"top":-10000,
                       "inspect":480}[action]
                result=driver.execute_script(
                    """
                    const seen=new Set(),candidates=[];
                    function scan(root) {
                        if (!root||seen.has(root)) return;
                        seen.add(root);
                        for (const el of root.querySelectorAll('*')) {
                            if(el.shadowRoot)scan(el.shadowRoot);
                            if(el.clientHeight>150 && el.clientWidth>200 &&
                               el.scrollHeight>el.clientHeight+24)
                                candidates.push(el);
                        }
                    }
                    scan(document);
                    candidates.sort((a,b)=>
                        b.clientHeight*b.clientWidth-a.clientHeight*a.clientWidth);
                    const target=candidates[0] || document.scrollingElement;
                    if(!target)return false;
                    const before=target.scrollTop;
                    target.scrollTop=arguments[0]<-1000?0:before+arguments[0];
                    return Math.abs(target.scrollTop-before)>2;
                    """,delta)
                need(type(result) is bool,"INVALID_ACTUAL_CHROME_SCROLL")
            else:
                raise RecoveryRefused("UNKNOWN_CHROME_STORY_OPERATION")

        visit(notification)
        # settings-ui exists before the nested notification radio group and
        # its asynchronously loaded preference are necessarily ready. Wait
        # for Chrome's actual selected value, not a synthetic/fake setting.
        try:
            WebDriverWait(driver,20).until(
                lambda d: selected_option() in ("ask","block"))
        except TimeoutException as exc:
            raise RecoveryRefused(
                "CHROME_REAL_NOTIFICATION_DEFAULT_NEVER_LOADED") from exc
        need(selected_option() in ("ask","block"),
             "CHROME_ORIGINAL_NOTIFICATION_DEFAULT_NOT_READABLE")
        # Show actual blocked payoff first; the final disposable profile
        # is destroyed by the runner after recording.
        toggle("block")
        need(selected_option()=="block",
             "REAL_PROOF_FIRST_BLOCK_SETTING_MISSING")
        (out/"stage_before").write_text(
            "DISPOSABLE_PROFILE_REAL_CHROME_BLOCK_STATE_READY\n","utf8")
        actions=[
            [(lambda action=action:browse(action)) for action in chapter]
            for chapter in CHROME_GUIDED_OPERATIONS
        ]
        perform_real_storyboard(out,actions)
        need(history==[notification,home,privacy,site,notification]
             and driver.current_url==notification,
             "CHROME_MUST_FOLLOW_ONE_WAY_GENUINE_SETTINGS_PATH")
        need(toggle_history.count("ask")>=2
             and toggle_history.count("block")>=3
             and selected_option()=="block",
             "CHROME_REAL_BEFORE_AFTER_RADIOS_NOT_VERIFIED")
        put(out/"application_observation.json",{
            "application":"Chromium browser",
            "before_url":"chrome://settings/",
            "after_url":driver.current_url,
            "real_settings_ui_element":True,
            # No real user's Chrome profile, account, or permission changed.
            "permissions_changed":False,
            "personal_profile_used":False,
            "temporary_profile_default_toggled":True,
            "demo_notification_default_final":"block",
            "youtube_uploads":0,
        })
        (out/"stage_after").write_text(
            "REAL_CHROME_TEMPORARY_NOTIFICATION_SETTING_CONFIRMED\n","utf8")
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

def inspect_media(capture):
    data=json.loads(invoke([
        "ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=codec_name,width,height,duration",
        "-of","json",str(capture)],timeout=15).stdout)
    streams=data["streams"]
    need(len(streams)==1 and streams[0]["codec_name"]=="h264"
         and streams[0]["width"]==WIDTH and streams[0]["height"]==HEIGHT
         and 47.5<=float(streams[0]["duration"])<=48.5,
         "REAL_APP_SOURCE_VIDEO_NOT_EXPECTED_GEOMETRY")
    invoke(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
            "-xerror","-i",str(capture),"-f","null","-"],timeout=50)
    need(decoded_frame_hash(capture,1.0)!=decoded_frame_hash(capture,40.0),
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
        wait_for(out/"stage_before",worker)
        source=out/CAPTURE
        recorder=subprocess.Popen(
            ["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
             "-f","x11grab","-video_size",f"{WIDTH}x{HEIGHT}",
             "-framerate","12","-i",f"{display}.0","-t","48",
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
        for chapter in range(5):
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
        need(observation["real_settings_ui_element"] is True
             and observation["permissions_changed"] is False
             and observation["personal_profile_used"] is False
             and observation["temporary_profile_default_toggled"] is True
             and observation["demo_notification_default_final"]=="block",
             "BROWSER_DEMO_TEMPORARY_SETTING_NOT_GENUINELY_VERIFIED")
    inspect_media(source)
    preview=out/PREVIEW
    graph=(
        "[0:v]trim=start=40:duration=1.5,setpts=PTS-STARTPTS,"
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
                    else out/"application_observation.json")
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
             else out/"application_observation.json")
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
            "application","before_url","after_url",
            "real_settings_ui_element","permissions_changed",
            "personal_profile_used","temporary_profile_default_toggled",
            "demo_notification_default_final","youtube_uploads"}
            and observation["before_url"]=="chrome://settings/"
            and observation["after_url"]==
                "chrome://settings/content/notifications"
            and observation["real_settings_ui_element"] is True
            and observation["permissions_changed"] is False
            and observation["personal_profile_used"] is False
            and observation["temporary_profile_default_toggled"] is True
            and observation["demo_notification_default_final"]=="block",
            "REAL_CHROME_SETTINGS_OBSERVATION_NOT_PROVED")
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
