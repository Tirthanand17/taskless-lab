"""Local Kokoro narration and measured word timings. Never grants release approval."""
from __future__ import annotations
import argparse, difflib, hashlib, json, math, re, subprocess, sys, wave
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
FPS=30
SR=48000
SPF=SR//FPS
def require(ok,message):
    if not ok: raise ValueError(message)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def normalized(text):
    return re.findall(r"[a-z0-9]+", text.casefold())
def compare(expected,recognized):
    a,b=normalized(expected),normalized(recognized)
    return difflib.SequenceMatcher(None,a,b,autojunk=False).ratio()
def frame_samples(n,pause_ms):
    return math.ceil((n+round(pause_ms*SR/1000))/SPF)*SPF
def validate_words(words,duration):
    require(words,"no observed words")
    last=0
    for w in words:
        a,b=w["start"],w["end"]
        require(math.isfinite(a) and math.isfinite(b) and 0<=a<b<=duration+1e-6,"invalid word timing")
        require(a>=last-1e-6,"overlapping words")
        require(bool(w["word"].strip()),"empty word")
        last=b
def cues(words):
    groups=[];group=[]
    for w in words:
        if group and (len(group)>=5 or len(" ".join(x["word"] for x in group+[w]))>36 or w["end"]-group[0]["start"]>3):
            groups.append(group);group=[]
        group.append(w)
    if group:groups.append(group)
    return [{"start":g[0]["start"],"end":g[-1]["end"],"text":" ".join(w["word"] for w in g),"words":g} for g in groups]
def timestamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
def wav(path,x):
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes(np.asarray(x,dtype="<i2").tobytes())
def pcm(path):
    with wave.open(str(path),"rb") as f:
        require((f.getframerate(),f.getnchannels(),f.getsampwidth())==(SR,1,2),"unexpected PCM")
        return np.frombuffer(f.readframes(f.getnframes()),dtype="<i2").copy()
def energy(x):
    y=x.astype(np.float64)/32768
    peak=float(np.max(np.abs(y)))
    rms=float(np.sqrt(np.mean(y*y)))
    return {"peak_dbfs":round(20*math.log10(max(peak,1e-9)),2),"rms_dbfs":round(20*math.log10(max(rms,1e-9)),2),
            "clipped_samples":int(np.sum(np.abs(x.astype(np.int32))>=32767))}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assets",type=Path,required=True);p.add_argument("--ffmpeg",required=True)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--spec",type=Path,required=True)
    args=p.parse_args()
    config=json.loads(args.spec.read_text(encoding="utf-8"))
    require(config["voice"]=="af_heart" and config["review_only"] is True,"voice or authority changed")
    require(not args.output.exists(),"output must be new")
    args.output.mkdir(parents=True)
    sys.path.insert(0,str(args.assets/"kokoro_vendor"))
    import soundfile as sf
    import espeakng_loader
    from phonemizer.backend.espeak.wrapper import EspeakWrapper
    EspeakWrapper.set_library(espeakng_loader.get_library_path())
    from kokoro_onnx import Kokoro
    from faster_whisper import WhisperModel
    model=args.assets/"kokoro-v1.0.int8.onnx";voices=args.assets/"voices-v1.0.bin"
    engine=Kokoro(str(model),str(voices))
    asr=WhisperModel("base",device="cpu",compute_type="int8",local_files_only=True,cpu_threads=4)
    timeline=[]; allcues=[]; tracks=[];offset=0
    for i,s in enumerate(config["scenes"]):
        raw=args.output/f"raw-{i}.wav"; ready=args.output/f"scene-{i}.wav"
        samples,sr=engine.create(s["text"],voice=config["voice"],speed=s["speed"],lang=config["language"])
        sf.write(str(raw),samples,sr,subtype="PCM_16")
        subprocess.run([args.ffmpeg,"-nostdin","-v","error","-i",str(raw),"-af","loudnorm=I=-16:TP=-2:LRA=7","-ar",str(SR),"-ac","1","-c:a","pcm_s16le",str(ready)],check=True)
        x=pcm(ready);n=frame_samples(len(x),s["pause_ms"]);x=np.pad(x,(0,n-len(x)));wav(ready,x)
        dur=n/SR
        seg,_=asr.transcribe(str(ready),language="en",word_timestamps=True,beam_size=3,condition_on_previous_text=False,vad_filter=False)
        words=[];last=0
        for z in seg:
            for w in z.words or []:
                a=max(0,last,float(w.start));b=min(dur,float(w.end))
                require(b>a,"ASR zero or reversed word")
                words.append({"word":w.word.strip(),"start":a,"end":b,"probability":float(w.probability)})
                last=b
        validate_words(words,dur)
        heard=" ".join(w["word"] for w in words)
        match=compare(s["text"],heard)
        e=energy(x);require(e["clipped_samples"]==0,"clipped PCM")
        require(e["rms_dbfs"]>-35,"quiet or silent track")
        require(words[0]["start"]<1.0 and dur-words[-1]["end"]<1.5,"excessive edge silence")
        # Record recognized words faithfully; don't invent timestamps for expected words.
        absolute=[{**w,"start":round(w["start"]+offset/SR,6),"end":round(w["end"]+offset/SR,6)} for w in words]
        allcues.extend(cues(absolute))
        timeline.append({"id":s["id"],"start_frame":offset//SPF,"end_frame":(offset+n)//SPF,
                         "expected":s["text"],"recognized":heard,"token_similarity":round(match,4),
                         "exact_token_match":normalized(s["text"])==normalized(heard),
                         "word_count":len(words),"first_word_seconds":words[0]["start"],
                         "tail_seconds":round(dur-words[-1]["end"],3),"energy":e,"wav_sha256":sha(ready)})
        offset+=n;tracks.append(x)
        print(s["id"],round(dur,2),round(match,3),heard,flush=True)
    full=args.output/"narration.wav";wav(full,np.concatenate(tracks))
    words=[w for c in allcues for w in c["words"]];validate_words(words,offset/SR)
    srt=args.output/"captions.srt"
    srt.write_text("\n\n".join(f"{i}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n{c['text']}" for i,c in enumerate(allcues,1))+"\n",encoding="utf-8")
    cap=args.output/"word_captions.json";cap.write_text(json.dumps(allcues,indent=2)+"\n",encoding="utf-8")
    report={"version":"1.0.0-rc9","voice":config["voice"],"synthetic":True,"model_sha256":sha(model),"voices_sha256":sha(voices),
            "sample_rate":SR,"samples":offset,"duration_seconds":offset/SR,"frames_at_30fps":offset//SPF,
            "narration_sha256":sha(full),"captions_sha256":sha(srt),"word_captions_sha256":sha(cap),
            "spec_sha256":sha(args.spec),"script_sha256":sha(Path(__file__)),
            "scene_timeline":timeline,"caption_cues":len(allcues),"recognized_words":len(words),
            "all_exact_token_matches":all(t["exact_token_match"] for t in timeline),
            "asr_screen_pass":all(t["token_similarity"]>=.90 for t in timeline),
            "energy":energy(pcm(full)),"human_listening_approved":False,"rights_approved":False,
            "visual_sync_reviewed":False,"release_authorized":False}
    (args.output/"NARRATION_REVIEW_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("REPORT",json.dumps(report),flush=True)
if __name__=="__main__":main()
