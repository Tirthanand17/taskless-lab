"""B1v10 v0.6.0: preserve the accepted narration, add original sound design."""
from __future__ import annotations
import argparse, hashlib, json, math, re, subprocess, sys
from pathlib import Path
import numpy as np
from narration_review import pcm, wav, energy, SR, SPF, normalized

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]))
from autopilot.polished_sound_design_v2 import _sfx

def need(ok, msg):
    if not ok: raise ValueError(msg)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def db(x): return 20*math.log10(max(float(x),1e-12))
def rms(x): return np.sqrt(np.mean(np.asarray(x,dtype=np.float64)**2))
def plan(report,cues):
    need(report["voice"]=="af_heart" and report["release_authorized"] is False,"unexpected narration identity")
    need(report["samples"]==report["frames_at_30fps"]*SPF,"invalid source clock")
    words=[w for c in cues for w in c["words"]]
    result=[]
    for scene,token,effect in [("proof","a","soft_tick"),("proof","b","soft_ping"),("explain","fingerprints","reveal_pulse"),("payoff","trusted","soft_sweep")]:
        s=next(x for x in report["scene_timeline"] if x["id"]==scene)
        matches=[w for w in words if s["start_frame"]/30-1e-6<=w["start"]<s["end_frame"]/30 and normalized(w["word"])==[token]]
        # A appears in the proof only as the explicitly spoken letter.
        if token=="a": matches=[w for w in matches if w["word"]=="A."]
        need(len(matches)==1,"ambiguous audio anchor: "+token)
        frame=round(matches[0]["start"]*30)
        need(s["start_frame"]<=frame<s["end_frame"],"event outside scene")
        result.append({"scene":scene,"anchor":token,"effect":effect,"frame":frame,"sample":frame*SPF})
    need(all(b["sample"]-a["sample"]>=SR*.3 for a,b in zip(result,result[1:])),"events too dense")
    return result
def duck_gain(voice):
    # 20-ms RMS envelope, linearly interpolated and smoothed to avoid pumping.
    block=960
    centers=np.arange(0,len(voice),block)
    levels=np.array([rms(voice[i:i+block]) for i in centers])
    target=1-.72*np.clip((levels-.008)/.052,0,1)
    smooth=np.empty_like(target); smooth[0]=target[0]
    for i in range(1,len(target)):
        alpha=.65 if target[i]<smooth[i-1] else .12
        smooth[i]=smooth[i-1]+alpha*(target[i]-smooth[i-1])
    return np.interp(np.arange(len(voice)),centers,smooth)
def mix(voice,events):
    need(voice.ndim==1 and len(voice)>SR and np.isfinite(voice).all(),"invalid voice")
    need(.01<rms(voice) and np.max(np.abs(voice))<.94,"silent or hot source")
    t=np.arange(len(voice))/SR
    fade=np.clip(np.minimum(t/.6,(len(voice)/SR-t)/.7),0,1)
    bed=(.008*np.sin(2*np.pi*110*t)+.004*np.sin(2*np.pi*164.81*t)+.002*np.sin(2*np.pi*220*t))*fade*duck_gain(voice)
    effects=np.zeros_like(voice,dtype=np.float64)
    for i,e in enumerate(events):
        start=e["sample"]; sound=_sfx(e["effect"],SR,7123+i).astype(np.float64)*.85
        # Taper final samples so even short decays end without a hard discontinuity.
        sound[-240:]*=np.linspace(1,0,240)
        need(type(start) is int and start>=0 and start+len(sound)<=len(voice),"effect outside source")
        effects[start:start+len(sound)]+=sound
    background=bed+effects
    y=voice+background
    need(np.max(np.abs(y))<.89,"mix peak too high")
    need(db(rms(voice)/max(rms(background),1e-12))>=22,"insufficient voice margin")
    return y,bed,effects
def write(path,x): wav(path,np.round(np.clip(x,-1,32767/32768)*32768).astype(np.int16))
def ff(ffmpeg,args):
    return subprocess.run([ffmpeg,"-nostdin",*args],capture_output=True,text=True,check=True).stderr
def measure(ffmpeg,path):
    s=ff(ffmpeg,["-hide_banner","-i",str(path),"-af","loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json","-f","null","-"])
    m=re.findall(r'\{[^{}]*"input_i"[^{}]*\}',s,re.S)
    need(bool(m),"no loudness measurement")
    r=json.loads(m[-1])
    return {k:float(r[k]) for k in ("input_i","input_tp","input_lra")}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--narration",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--ffmpeg",required=True)
    a=p.parse_args()
    report=json.loads((ROOT/"NARRATION_REVIEW_QA.json").read_text(encoding="utf-8"))
    correction=json.loads((ROOT/"CAPTION_CORRECTION_QA.json").read_text(encoding="utf-8"))
    cp=ROOT/"word_captions_review.json"
    need(sha(a.narration)==report["narration_sha256"],"accepted narration hash mismatch")
    need(sha(cp)==correction["corrected_word_captions_sha256"],"caption hash mismatch")
    v=pcm(a.narration).astype(np.float64)/32768
    need(len(v)==report["samples"],"sample count mismatch")
    events=plan(report,json.loads(cp.read_text(encoding="utf-8")))
    y,b,e=mix(v,events)
    a.output.mkdir(parents=True,exist_ok=False)
    for name,x in [("mix.wav",y),("ambient.wav",b),("effects.wav",e)]: write(a.output/name,x)
    mixpath=a.output/"mix.wav";encoded=a.output/"mix.m4a";decoded=a.output/"decoded.wav"
    ff(a.ffmpeg,["-v","error","-i",str(mixpath),"-c:a","aac","-b:a","192k","-movflags","+faststart",str(encoded)])
    ff(a.ffmpeg,["-v","error","-xerror","-i",str(encoded),"-ar","48000","-ac","1","-c:a","pcm_s16le",str(decoded)])
    d=pcm(decoded);delta=len(d)-len(v)
    need(0<=delta<=1024,"unexpected AAC padding")
    loud=measure(a.ffmpeg,encoded)
    need(-20<=loud["input_i"]<=-13 and loud["input_tp"]<=-1,"encoded loudness/peak review hold")
    need(energy(d)["clipped_samples"]==0,"encoded clipping")
    r={"version":"0.6.0","narration_sha256":sha(a.narration),"narration_unchanged":True,
       "source_samples":len(v),"mix_samples":len(pcm(mixpath)),"decoded_aac_samples":len(d),"aac_padding_samples":delta,
       "duration_seconds":len(v)/SR,"sample_rate":SR,"events":events,
       "voice_over_background_db":round(db(rms(v)/rms(b+e)),2),
       "ambient_gain_during_active_speech_floor":.28,"ambient_gain_min":round(float(duck_gain(v).min()),4),
       "voice_over_bed_db":round(db(rms(v)/rms(b)),2),"mix_pcm_energy":energy(pcm(mixpath)),
       "decoded_aac_energy":energy(d),"encoded_loudness":loud,
       "artifacts_sha256":{n:sha(a.output/n) for n in ("mix.wav","ambient.wav","effects.wav","mix.m4a","decoded.wav")},
       "source_sha256":{n:sha(ROOT/n) for n in ("sound_mix.py","NARRATION_REVIEW_QA.json","CAPTION_CORRECTION_QA.json","word_captions_review.json")},
       "effects_source":"existing original oscillator/noise recipes; no external audio",
       "third_party_audio_samples":0,"planned_visual_events_not_rendered":True,
       "human_mix_listening_approved":False,"release_authorized":False}
    (a.output/"SOUND_MIX_QA.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2))
if __name__=="__main__":main()
