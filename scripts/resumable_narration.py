"""Generate segmented natural-style speech with bounded retry and resumable cache.

All generated assets remain inside the existing youtube con production directory.
Synthetic speech. Human listening is required before publication.
"""
from __future__ import annotations
import argparse,asyncio,hashlib,json,sys,wave
from pathlib import Path
from shutil import copyfile
repo=Path(__file__).resolve().parents[1]
ws=repo.parent
sys.path.insert(0,str(ws/"flowminute-natural-voice-worktree"/"motion-v2"))
import natural_narration as n
import edge_tts

async def run_segment(segment, voice, pitch, mp3, ffmpeg):
    errors=[]
    for attempt in range(5):
        try:
            candidate=mp3.with_suffix(".partial.mp3")
            candidate.unlink(missing_ok=True)
            service=edge_tts.Communicate(text=segment["text"],voice=voice,rate=f'{segment["rate_percent"]:+d}%',pitch=pitch,volume="+0%")
            await service.save(str(candidate))
            if candidate.stat().st_size<100:raise RuntimeError("empty response")
            candidate.replace(mp3)
            return
        except Exception as exc:
            errors.append(f"{type(exc).__name__}:{str(exc)[:90]}")
            await asyncio.sleep([1,3,6,10,16][attempt])
    raise RuntimeError("Retry budget exhausted: "+";".join(errors))

async def generate(args):
    script=Path(args.script).resolve()
    output=Path(args.output).resolve()
    text=script.read_text(encoding="utf-8").strip()
    segs=n.plan_segments(text,args.preset)
    options=n.VOICE_PRESETS[args.preset]
    voice=args.voice or options["voice"]
    pitch=options["pitch"]
    cache=output.parent/"resumable_segments"/output.stem
    cache.mkdir(parents=True,exist_ok=True)
    ffmpeg=n.find_ffmpeg()
    wavs=[]
    cursor=0.0
    for i,s in enumerate(segs):
        key=hashlib.sha256(f"{voice}|{pitch}|{s['text']}|{s['rate_percent']}".encode()).hexdigest()[:16]
        mp3=cache/f"{i:03d}-{key}.mp3"
        wav=cache/f"{i:03d}-{key}.wav"
        if not wav.is_file() or wav.stat().st_size<1000:
            if not mp3.is_file() or mp3.stat().st_size<100:
                print(f"CHUNK {i+1}/{len(segs)} synth",flush=True)
                await run_segment(s,voice,pitch,mp3,ffmpeg)
            n.run_ffmpeg(ffmpeg,["-i",str(mp3),"-ar","48000","-ac","1","-c:a","pcm_s16le",str(wav)])
        with wave.open(str(wav),"rb") as reader:
            frames=reader.getnframes()
            duration=frames/reader.getframerate()
        s["start_seconds"]=round(cursor,3)
        s["speech_duration_seconds"]=round(duration,3)
        cursor+=duration
        s["end_seconds"]=round(cursor,3)
        cursor+=s["pause_ms"]/1000
        wavs.append(wav)
        print(f"CHUNK {i+1}/{len(segs)} ready {duration:.2f}s",flush=True)
    combined=cache/"all.wav"
    duration=n.join_pcm_wavs(wavs,segs,combined)
    if args.max_duration and duration>args.max_duration:
        raise RuntimeError(f"Audio {duration:.2f}s above maximum {args.max_duration:.2f}s")
    encoded=cache/"full.mp3"
    n.run_ffmpeg(ffmpeg,["-i",str(combined),"-af","loudnorm=I=-16:TP=-1.5:LRA=11","-c:a","libmp3lame","-b:a","192k","-ar","48000",str(encoded)])
    output.parent.mkdir(parents=True,exist_ok=True)
    copyfile(encoded,output)
    report=n.report_for(script,output,args.preset,voice,segs,duration=duration,dry_run=False)
    report["resumable_cache"]=str(cache)
    report["segment_start_end_are_exact_pcm_boundaries"]=True
    report["word_timing_is_not_forced_alignment"]=True
    Path(args.report).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("FINISHED",json.dumps({"output":str(output),"duration":duration,"words":report["words"],"segments":len(segs)}),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--script",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--report",required=True)
    parser.add_argument("--preset",default="warm-explainer",choices=list(n.VOICE_PRESETS))
    parser.add_argument("--voice")
    parser.add_argument("--max-duration",type=float,default=285.0)
    args=parser.parse_args()
    asyncio.run(generate(args))
