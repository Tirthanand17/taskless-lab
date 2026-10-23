"""Rebuild an honest 32-second cinematic Short from exactly four REAL 3D MP4s.

0–8s: Approved, re-exported HeyGen Asha/Jay opener.
8–32s: Three distinct premium 3D clips. Mix ONE continuous narration stem.

No MP4 footage generation, placeholder pictures, YouTube connection, billing,
license clearance or automatic release-approval occurs here.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from autopilot.flow_episode_compositor import assemble, validate_manifest, AssemblyError

ACCEPTED_VO_SHA256="f81dba668732b01b4fc4bbad0e54414f01765e13ec47879dbdb789a334e7d203"


def demand(condition, reason):
    if not condition:
        raise AssemblyError(reason)


def command(args, *, timeout=180):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if p.returncode:
        raise AssemblyError("FFmpeg failed: "+(p.stderr or p.stdout)[-700:])
    return p.stdout


def ffprobe_seconds(path):
    return float(command(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)]).strip())


def render_v2(manifest:dict, narration:Path, output:Path, *,
              expected_voice_sha:str=ACCEPTED_VO_SHA256) -> dict:
    # Composition is always creative review stage, NEVER a release authorization.
    demand(manifest.get("creative_revision")=="cinematic_v2_32s",
           "Only cinematic v2 may use this 32-second audio assembly")
    review=validate_manifest(manifest,test_mode=False)
    demand(review["planned_ms"]==32000 and review["full_duration"],
           "No missing or padded 3D scenes allowed")
    demand(narration.is_file() and not narration.is_symlink()
           and narration.suffix.lower()==".wav", "Verified WAV narration missing")
    demand(len(expected_voice_sha)==64
           and sha256(narration.read_bytes()).hexdigest()==expected_voice_sha,
           "Continuous 24-second voice checksum changed")
    demand(abs(ffprobe_seconds(narration)-24.0)<.03,
           "Continuous voice does not fit 8–32 seconds")

    # Silence detection runs on pure VO, not soundtrack music.
    from scripts.creative_pacing_gate import audit_file
    pacing=audit_file(narration,narration_start=0.,max_gap=1.2)
    demand(pacing["pass"],"Narration still contains unacceptable silent gaps")

    demand(output.suffix==".mp4" and output.parent.is_dir()
           and not output.parent.is_symlink() and not output.exists(),
           "Refuse to overwrite or write unsafe final review output")

    with TemporaryDirectory(prefix="flowminute-cinematic-32-",dir=output.parent) as work:
        root=Path(work)
        source=root/"staged_real_four_shots.mp4"
        assembly=assemble(manifest,source,test_mode=False)
        demand(assembly["segments"]==4 and assembly["missing_seconds"]==0,
               "3D scene assembly incomplete")
        mixed=root/"staged_32s_audio.mp4"
        # Keep existing two-character speaking in 0–8s.
        # For new 8–32s scenes, keep original ambient sound at 10% and
        # overlay the independently verified continuous human-like VO at 100%.
        filt=(
          "[0:a]asplit=2[all][original];"
          "[all]atrim=start=0:end=8,asetpts=PTS-STARTPTS,"
          "aresample=48000,apad,atrim=0:8[intro];"
          "[original]atrim=start=8:end=32,asetpts=PTS-STARTPTS,"
          "aresample=48000,volume=0.10[ambience];"
          "[1:a]aresample=48000,atrim=start=0:end=24,"
          "asetpts=PTS-STARTPTS,volume=1.0[voice];"
          "[ambience][voice]amix=inputs=2:duration=first:"
          "dropout_transition=0[body];"
          "[intro][body]concat=n=2:v=0:a=1,"
          "atrim=0:32,asetpts=N/SR/TB[outa]"
        )
        command(["ffmpeg","-hide_banner","-nostdin","-loglevel","error",
            "-y","-i",str(source),"-i",str(narration),
            "-filter_complex",filt,"-map","0:v:0","-map","[outa]",
            "-c:v","copy","-c:a","aac","-ar","48000","-b:a","160k",
            "-t","32","-movflags","+faststart",str(mixed)])
        command(["ffmpeg","-hide_banner","-nostdin","-loglevel","error",
            "-xerror","-i",str(mixed),"-f","null","-"])
        secs=ffprobe_seconds(mixed)
        demand(abs(secs-32)<.3,"32-second cinematic output timing drift")
        mixed.replace(output)

    report={
      "episode_id":"fm_20261024_short_en",
      "creative_revision":"cinematic_v2_32s",
      "state":"REAL_32S_FOUR_CLIP_DRAFT_AWAITING_VISUAL_AND_HUMAN_REVIEW",
      "duration_seconds":round(secs,3),
      "output_mp4":output.name,
      "output_sha256":sha256(output.read_bytes()).hexdigest(),
      "actual_source_3d_clips":4,
      "narration_stem_sha256":expected_voice_sha,
      "voice_only_gap_audit":pacing,
      "no_vector_substitution":True,
      "video_technically_verified":True,
      "voice_human_approved":False,
      "character_consistency_human_approved":False,
      "rights_human_approved":False,
      "captions_aligned_and_verified":False,
      "creative_owner_approved":False,
      "youtube_uploaded":False,
      "youtube_scheduled":False
    }
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--voice",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--report",type=Path,default=None)
    args=p.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    result=render_v2(manifest,args.voice,args.output)
    if args.report:
        demand(not args.report.exists(),"Refuse to overwrite previous QA")
        args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
