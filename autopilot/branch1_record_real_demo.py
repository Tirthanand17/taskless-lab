"""Free genuine-software capture pilot: execute Python CSV cleanup in XTerm.

Runs on an isolated GitHub runner with FFmpeg/Xvfb/XTerm, on synthetic
fixtures only. Records the REAL terminal application performing REAL code.
No simulated UI screenshots, Gmail login, YouTube calls, private data or upload.
The proof-first preview has NO narration and is NOT publication-ready.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time

from autopilot.branch1_recovery import RecoveryRefused, verify_capture

EPISODE_ID = "fm_pilot_csv_cleanup_short_en"
WIDTH, HEIGHT = 1280, 720

def insist(ok, reason):
    if not ok:
        raise RecoveryRefused(reason)

def sh(command, *, cwd=None, env=None, timeout=60):
    return subprocess.run(command, cwd=cwd, env=env, check=True,
                          capture_output=True, text=True, timeout=timeout)

def sha_file(path):
    hasher = hashlib.sha256()
    with path.open("rb") as reader:
        for chunk in iter(lambda: reader.read(1024*1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def fixture(out):
    """A tiny first-party fabricated CSV, not an actual customer spreadsheet."""
    source = out/"source.csv"
    with source.open("w", newline="", encoding="utf8") as f:
        writer = csv.writer(f)
        writer.writerows([
            ["invoice", "amount", "status"],
            ["INV-101", "120", "paid"],
            ["INV-102", "85", "open"],
            ["INV-101", "120", "paid"],
            ["INV-103", "55", "paid"],
        ])
    code = out/"clean_csv.py"
    code.write_text(
        "import csv\n"
        "from pathlib import Path\n"
        "base = Path(__file__).resolve().parent\n"
        "with (base/'source.csv').open(newline='') as f:\n"
        "    rows = list(csv.DictReader(f))\n"
        "seen = set()\n"
        "clean = []\n"
        "for row in rows:\n"
        "    if row['invoice'] not in seen:\n"
        "        seen.add(row['invoice'])\n"
        "        clean.append(row)\n"
        "with (base/'clean.csv').open('w', newline='') as f:\n"
        "    writer = csv.DictWriter(f, fieldnames=['invoice','amount','status'])\n"
        "    writer.writeheader()\n"
        "    writer.writerows(clean)\n"
        "print('REAL EXECUTION: 4 input rows -> 3 unique invoices')\n",
        encoding="utf8")
    # Protect against accidental rendering of personal data.
    insist(b"@" not in source.read_bytes() and b"@" not in code.read_bytes(),
           "NO_EMAILS_IN_DEMONSTRATION")
    return source, code

def run(out: Path, brief_path: Path) -> dict:
    brief = json.loads(brief_path.read_text("utf8"))
    insist(brief["episode_id"] == EPISODE_ID
           and brief["demo"]["application"] == "Python terminal",
           "DEMO_EPISODE_MISMATCH")
    insist(not out.exists(), "REFUSE_OVERWRITE_OR_REUSE_OF_MEDIA")
    for tool in ("ffmpeg", "ffprobe", "Xvfb", "xterm"):
        insist(shutil.which(tool) is not None, "MISSING_FREE_SYSTEM_TOOL_"+tool)
    out.mkdir(mode=0o700, parents=True)
    original, cleaner = fixture(out)
    show = out/"real_demo.sh"
    show.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "cd "+shlex.quote(str(out.resolve()))+"\n"
        "printf '\\033[2J\\033[H'\n"
        "printf 'FLOWMINUTE / REAL PYTHON CSV DEMONSTRATION\\n'\n"
        "printf 'FIRST PARTY TEST DATA - NO PRIVATE RECORDS\\n\\n'\n"
        "printf 'BEFORE: duplicate invoice in real file\\n'\n"
        "cat source.csv\n"
        "sleep 3\n"
        "printf '\\nACTUAL ACTION: python3 clean_csv.py\\n'\n"
        "python3 clean_csv.py\n"
        "sleep 1\n"
        "printf '\\nAFTER: actual clean.csv output\\n'\n"
        "cat clean.csv\n"
        "sleep 7\n",
        encoding="utf8")
    show.chmod(0o700)
    import tempfile
    with tempfile.TemporaryDirectory(prefix="fm-b1-x11-") as xdir:
        display = ":92"
        insist(not Path("/tmp/.X11-unix/X92").exists(),
               "FIXED_DISPLAY_IN_USE")
        xvfb = subprocess.Popen(["Xvfb", display, "-screen", "0",
                                 f"{WIDTH}x{HEIGHT}x24", "-nolisten", "tcp"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        terminal = None
        try:
            for _ in range(40):
                if Path("/tmp/.X11-unix/X92").exists():
                    break
                insist(xvfb.poll() is None, "XVFB_QUIT_EARLY")
                time.sleep(.1)
            insist(Path("/tmp/.X11-unix/X92").exists(), "XVFB_NOT_READY")
            env = {**os.environ, "DISPLAY": display, "HOME": xdir}
            terminal = subprocess.Popen([
                "xterm", "-fa", "DejaVu Sans Mono", "-fs", "14",
                "-geometry", "105x26+75+30", "-bg", "#101b2b",
                "-fg", "#e5eef7", "-e", "/bin/bash", str(show),
            ], env=env, cwd=out, stdout=subprocess.DEVNULL,
               stderr=subprocess.DEVNULL)
            time.sleep(1.0)
            insist(terminal.poll() is None, "REAL_TERMINAL_NOT_RUNNING")
            capture = out/"ACTUAL_PYTHON_TERMINAL_CAPTURE.mp4"
            sh(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                "-f", "x11grab", "-video_size", f"{WIDTH}x{HEIGHT}",
                "-framerate", "12", "-i", f"{display}.0", "-t", "10",
                "-an", "-c:v", "libx264", "-preset", "ultrafast",
                "-crf", "22", "-pix_fmt", "yuv420p", "-movflags",
                "+faststart", str(capture)], timeout=65)
        finally:
            if terminal is not None:
                terminal.terminate()
                try:
                    terminal.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    terminal.kill()
                    terminal.wait(timeout=3)
            xvfb.terminate()
            try:
                xvfb.wait(timeout=4)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                xvfb.wait(timeout=3)
    with (out/"clean.csv").open(newline="", encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    insist(len(rows) == 3 and [r["invoice"] for r in rows]
           == ["INV-101", "INV-102", "INV-103"],
           "REAL_CSV_EXECUTION_NOT_VERIFIED")
    capture = out/"ACTUAL_PYTHON_TERMINAL_CAPTURE.mp4"
    inspected = json.loads(sh([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,duration",
        "-of", "json", str(capture)], timeout=15).stdout)
    streams = inspected["streams"]
    insist(len(streams) == 1 and streams[0]["codec_name"] == "h264"
           and streams[0]["width"] == WIDTH
           and streams[0]["height"] == HEIGHT
           and 9.5 <= float(streams[0]["duration"]) <= 10.5,
           "RECORDED_SOFTWARE_VIDEO_INVALID")
    sh(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-xerror", "-i", str(capture), "-f", "null", "-"], timeout=40)
    # A perfectly encoded static/black frame would not be authentic proof.
    # Sample actual decoded RGB PNG frames at the before and after stages.
    def actual_frame_hash(second: float) -> str:
        output = subprocess.run([
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-ss", str(second), "-i", str(capture), "-frames:v", "1",
            "-vcodec", "png", "-f", "image2pipe", "-"],
            check=True, capture_output=True, timeout=30).stdout
        insist(len(output) > 1000 and output.startswith(b"\x89PNG"),
               "NO_ACTUAL_FRAME_AT_STAGE")
        return hashlib.sha256(output).hexdigest()

    before_frame = actual_frame_hash(1.0)
    after_frame = actual_frame_hash(7.0)
    insist(before_frame != after_frame,
           "STATIC_OR_UNCHANGED_DEMONSTRATION_REFUSED")
    # Review-only proof-first edit: show the real AFTER result immediately,
    # then the REAL recorded before/action/result sequence. It deliberately
    # has no voice or music; never package this as an approved YouTube Short.
    preview = out/"PROOF_FIRST_NO_NARRATION_REVIEW_ONLY.mp4"
    style = (
        "scale=1080:608:flags=lanczos,"
        "pad=1080:1920:0:656:color=0x081422,"
        "format=yuv420p"
    )
    graph = (
        f"[0:v]trim=start=5.0:duration=1.6,setpts=PTS-STARTPTS,{style}[hook];"
        f"[0:v]trim=start=0:duration=9.4,setpts=PTS-STARTPTS,{style}[walk];"
        "[hook][walk]concat=n=2:v=1:a=0[v]"
    )
    sh(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(capture), "-filter_complex", graph, "-map", "[v]",
        "-an", "-r", "12", "-c:v", "libx264", "-preset", "ultrafast",
        "-crf", "25", "-pix_fmt", "yuv420p", str(preview)], timeout=90)
    sh(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-xerror", "-i", str(preview), "-f", "null", "-"], timeout=45)
    fixture_bytes = original.read_bytes()+cleaner.read_bytes()
    receipt = {
        "schema": "FLOWMINUTE_B1_REAL_CAPTURE_V1",
        "status": "ACTUAL_FIRST_PARTY_TERMINAL_CAPTURE_REVIEW_ONLY",
        "episode_id": EPISODE_ID,
        "capture_sha256": sha_file(capture),
        "capture_bytes": capture.stat().st_size,
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "capture_method": "xvfb_xterm_ffmpeg_live",
        "private_data": False,
        "youtube_uploads": 0,
        "release_approved": False,
    }
    receipt_path = out/"EXACT_REAL_CAPTURE_UNAPPROVED.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n",
                            encoding="utf8")
    proof = verify_capture(brief, capture, receipt_path)
    proof["proof_first_silent_review_sha256"] = sha_file(preview)
    proof["actual_csv_input_rows"] = 4
    proof["actual_csv_output_rows"] = 3
    (out/"REVIEW_ONLY_NO_UPLOAD.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True)+"\n",
        encoding="utf8")
    return proof

def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--brief", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    print(json.dumps(run(args.out, args.brief), sort_keys=True))

if __name__ == "__main__":
    main()
