"""B1v10 v0.1.1: review-only native-HD motion proof, not release approval."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def verify_video(path: Path, size: tuple[int, int], ffmpeg: str) -> dict:
    require(path.is_file(), f"Missing {path.name}")
    cap = cv2.VideoCapture(str(path))
    try:
        require(cap.isOpened(), f"Cannot open {path.name}")
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        require((w, h) == size, f"Wrong resolution: {(w, h)}")
        require(abs(fps - 30) < .01, f"Wrong FPS: {fps}")
        n = 0
        sampled = []
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            require(frame.shape[:2] == (h, w), "Inconsistent decoded dimensions")
            if n % 8 == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                sampled.append(cv2.resize(gray, (240, 240), interpolation=cv2.INTER_AREA))
            n += 1
        require(n == 90, f"Wrong decoded frame count: {n}")
    finally:
        cap.release()
    deltas = [float(np.mean(cv2.absdiff(a, b))) for a, b in zip(sampled, sampled[1:])]
    fraction = sum(d > .5 for d in deltas) / len(deltas)
    require(fraction >= .75, f"Insufficient sampled motion: {fraction:.3f}")
    subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-xerror", "-i", str(path),
                    "-map", "0:v:0", "-f", "null", "-"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return {"filename": path.name, "sha256": digest(path), "resolution": [w, h],
            "fps": fps, "decoded_frames": n, "duration_seconds": n / fps,
            "decode_pass": True, "motion_sample_interval_frames": 8,
            "motion_samples": len(sampled), "motion_change_fraction_gt_0_5": fraction,
            "mean_sample_deltas": [round(d, 3) for d in deltas]}

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    args = p.parse_args()
    ffmpeg = args.ffmpeg
    if not ffmpeg:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg = get_ffmpeg_exe()
    root = args.directory.resolve()
    prior = json.loads((root / "SMOKE_QA.json").read_text(encoding="utf-8-sig"))
    source = digest(root / "smoke.tsx")
    require(source == prior["source_sha256"], "Source changed since v0.1.0")
    vertical = verify_video(root / "vertical-smoke.mp4", (1080, 1920), ffmpeg)
    require(vertical["sha256"] == prior["vertical_sha256"], "Prior vertical artifact changed")
    landscape = verify_video(root / "landscape-motion-v010.mp4", (1920, 1080), ffmpeg)
    report = {"version": "0.1.1", "source_sha256": source,
              "vertical": vertical, "landscape": landscape,
              "review_only": True, "narration_verified": False,
              "visual_review_pass": False, "release_authorized": False,
              "limitations": ["Three-second benchmark only", "Motion threshold is not a creative quality score",
                              "No narration or music verification", "No owner approval or publication"]}
    result = root / "DUAL_MOTION_QA.json"
    result.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
