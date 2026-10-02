from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    print(" ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--episode",default="content/episodes/pilot_001.json")
    ap.add_argument("--audio",default="assets/pilot_001/voice.mp3")
    args=ap.parse_args()

    episode_path=ROOT/args.episode
    audio=ROOT/args.audio
    data=json.loads(episode_path.read_text(encoding="utf-8"))
    asset_dir=ROOT/"assets"/data["id"]
    work=asset_dir/"_render"
    work.mkdir(parents=True,exist_ok=True)

    # Generate SRT from the same manifest used by the video.
    srt=asset_dir/"captions.srt"
    run(["python",str(ROOT/"scripts"/"generate_srt.py"),str(episode_path),str(srt)])

    scene_files=[]
    fps=30
    for i,duration in enumerate(data["scene_durations"],1):
        src=asset_dir/f"scene_{i:02}.png"
        dst=work/f"scene_{i:02}.mp4"
        frames=max(1,int(duration*fps))
        zoom="min(zoom+0.00045,1.035)"
        vf=(
          f"scale=1120:1990,"
          f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"d={frames}:s=1080x1920:fps={fps},"
          "format=yuv420p"
        )
        run([
          "ffmpeg","-y","-loglevel","error","-loop","1","-i",str(src),
          "-vf",vf,"-t",str(duration),"-r",str(fps),
          "-c:v","libx264","-preset","veryfast","-crf","20","-an",str(dst)
        ])
        scene_files.append(dst)

    concat=work/"scenes.txt"
    concat.write_text("\n".join([f"file '{p.as_posix()}'" for p in scene_files]),encoding="utf-8")
    silent=work/"silent.mp4"
    run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)])

    out=asset_dir/"pilot_001_final.mp4"
    subtitle_filter=(
      f"subtitles='{srt.as_posix()}':force_style="
      "'FontName=DejaVu Sans,FontSize=16,PrimaryColour=&H00FFFFFF,"
      "OutlineColour=&H00101010,BackColour=&H90000000,BorderStyle=3,"
      "Outline=2,Shadow=0,Alignment=2,MarginV=150'"
    )
    run([
      "ffmpeg","-y","-loglevel","error","-i",str(silent),"-i",str(audio),
      "-vf",subtitle_filter,"-map","0:v:0","-map","1:a:0",
      "-c:v","libx264","-preset","veryfast","-crf","19",
      "-c:a","aac","-b:a","160k","-shortest",str(out)
    ])

    print(out)

if __name__=="__main__":
    main()
