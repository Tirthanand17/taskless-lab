"""FlowMinute Oct14 local MP4 technical QA. Read-only source videos; contact images/reports inside youtube con.
Automated decode and audio validation cannot replace full human review.
"""
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1].parent
B=ROOT/"oct15-production"
FF=next((ROOT/"flowminute-publisher-worktree"/".venv"/"Lib"/"site-packages"/"imageio_ffmpeg"/"binaries").glob("*.exe"))

def run(args):
 return subprocess.run([str(FF),"-hide_banner","-nostdin",*args],capture_output=True,text=True,timeout=240)

def duration(s):
 m=re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)",s)
 if not m:raise RuntimeError("No container duration")
 return 3600*int(m.group(1))+60*int(m.group(2))+float(m.group(3))

reports=[]
for ep,width,height in (("pilot_021",1080,1920),("long_010",1920,1080),("pilot_022",1080,1920)):
 video=B/(ep+".mp4")
 if not video.is_file():raise RuntimeError(f"{ep}: Video absent; render still running")
 if video.stat().st_size<300_000:raise RuntimeError(f"{ep}: Video too small")
 voice=json.loads((B/"audio"/(ep+"_natural_qa.json")).read_text(encoding="utf-8"))
 audio_seconds=voice["audio_duration_seconds"]
 test=run(["-v","info","-i",str(video),"-f","null","NUL"])
 if test.returncode:raise RuntimeError(f"{ep}: decode failed: {test.stderr[-400:]}")
 secs=duration(test.stderr)
 if not (audio_seconds <=secs<=audio_seconds+3):raise RuntimeError(f"{ep}: video {secs:.2f}s audio {audio_seconds:.2f}s mismatch")
 if not re.search(r"Video: h264.*?"+str(width)+"x"+str(height),test.stderr,re.S):raise RuntimeError(f"{ep}: wrong codec or resolution")
 if "Audio: aac" not in test.stderr:raise RuntimeError(f"{ep}: no AAC audio")
 test_audio=run(["-v","info","-i",str(video),"-vn","-af","volumedetect","-f","null","NUL"])
 peak=re.search(r"max_volume:\s*(-?\d+\.\d+) dB",test_audio.stderr)
 if test_audio.returncode or peak is None:raise RuntimeError(f"{ep}: audio peaks unavailable")
 if float(peak.group(1))>=-.5:raise RuntimeError(f"{ep}: may clip at {peak.group(1)} dB")
 contact=B/(ep+"_contact_FINAL.jpg")
 step=8 if ep.startswith("pilot_") else 42
 filt=f"fps=1/{step},scale={300 if ep.startswith('pilot_') else 390}:-1,tile={'5x1' if ep.startswith('pilot_') else '6x1'}"
 result=run(["-v","error","-i",str(video),"-vf",filt,"-frames:v","1","-y",str(contact)])
 if result.returncode:raise RuntimeError(f"{ep}: contact sheet failure {result.stderr[-280:]}")
 data={"id":ep,"technical_pass":True,"duration_seconds":secs,"narration_duration_seconds":audio_seconds,
       "dimensions":f"{width}x{height}","bytes":video.stat().st_size,
       "video_sha256":hashlib.sha256(video.read_bytes()).hexdigest(),
       "audio_peak_db":float(peak.group(1)),"contact_path":str(contact),
       "human_listening_review":"PENDING","full_editorial_watchthrough":"PENDING",
       "accurate_caption_timing":"PENDING"}
 reports.append(data)
 print(ep,"MP4_TECH_QA_PASS",secs,"seconds; max audio peak",peak.group(1),"dB")
destination=B/"oct15_technical_qa.json"
destination.write_text(json.dumps({"status":"technical_pass_only_not_human_approved","videos":reports},indent=2)+"\n",encoding="utf-8")
print("REPORT",destination)
