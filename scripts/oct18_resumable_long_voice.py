"""Resumable Kokoro narration with per-sentence disk checkpoints.

No network; all model, scripts, caches, audio inside youtube con.
Synthetic voice, not a human recording. Never reuses a different script or voice.
"""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf
from imageio_ffmpeg import get_ffmpeg_exe
from kokoro_onnx import Kokoro

def sentences(text):
    out=[]
    for p in re.split(r'(?<=[.!?])\s+',text.strip()):
        p=p.strip()
        while len(p)>270:
            cuts=[p.rfind(x,60,220) for x in ('; ', ', ', ' - ', ': ')]
            at=max(cuts)
            if at<80:at=p.rfind(' ',0,195)
            if at<50:at=min(len(p),190)
            out.append(p[:at].strip());p=p[at:].strip()
        if p:out.append(p)
    return out

def run():
    ap=argparse.ArgumentParser()
    for x in ('script','output','report','model','voices','voice','cache'):
        ap.add_argument('--'+x,required=True)
    ap.add_argument('--speed',type=float,default=1.09)
    ap.add_argument('--max-duration',type=float,default=370)
    a=ap.parse_args()
    script=Path(a.script)
    content=script.read_text(encoding='utf-8-sig').strip()
    chunks=sentences(content)
    if len(chunks)<5:raise RuntimeError('Too few narration segments')
    cache=Path(a.cache);cache.mkdir(parents=True,exist_ok=True)
    signature=hashlib.sha256((content+'\nVOICE='+a.voice+'\nSPEED='+str(a.speed)).encode()).hexdigest()
    conf=cache/'config.json'
    if conf.exists():
        prior=json.loads(conf.read_text(encoding='utf-8'))
        if prior.get('signature')!=signature or prior.get('segments')!=len(chunks):
            raise RuntimeError('Existing cached voice segments have a different script/voice/speed; stop safely')
    else:conf.write_text(json.dumps({'signature':signature,'voice':a.voice,'speed':a.speed,'segments':len(chunks)},indent=2)+'\n',encoding='utf8')
    # Instantiate the speech model only if one or more segments remain.
    missing=[i for i in range(len(chunks)) if not (cache/f'{i:03d}.wav').exists()]
    kokoro=None
    if missing:
        print('INITIALIZE_KOKORO',a.voice,len(missing),'remaining',flush=True)
        kokoro=Kokoro(a.model,a.voices)
        if a.voice not in kokoro.get_voices():raise RuntimeError('Voice missing in model')
    durations=[]
    pieces=[]
    for i,chunk in enumerate(chunks):
        path=cache/f'{i:03d}.wav'
        if path.exists():
            info=sf.info(path)
            if info.samplerate!=24000 or info.channels!=1 or info.frames<1000:
                raise RuntimeError(f'Bad checkpoint segment {i}')
            print('REUSE_SEGMENT',i+1,'/',len(chunks),flush=True)
        else:
            print('GENERATE_SEGMENT',i+1,'/',len(chunks),'chars',len(chunk),flush=True)
            wav,sr=kokoro.create(chunk,voice=a.voice,speed=a.speed,lang='en-us')
            if int(sr)!=24000:raise RuntimeError('Bad sample rate')
            wave=np.asarray(wav,dtype=np.float32).reshape(-1)
            if len(wave)<1000 or not np.isfinite(wave).all():raise RuntimeError('Invalid sound chunk')
            tmp=cache/f'{i:03d}.partial.wav'
            sf.write(tmp,wave,24000,subtype='PCM_16')
            tmp.replace(path)
        wave,rate=sf.read(path,dtype='float32')
        if int(rate)!=24000 or len(wave)<1000:raise RuntimeError('Broken segment')
        pieces.append(wave)
        durations.append(round(len(wave)/24000,3))
        if i<len(chunks)-1:
            pause=0.25 if chunk.endswith('.') else 0.17
            pieces.append(np.zeros(round(24000*pause),dtype=np.float32))
    del kokoro
    audio=np.concatenate(pieces)
    duration=len(audio)/24000
    if duration>a.max_duration:raise RuntimeError(f'Long voice {duration:.1f}s > {a.max_duration}s')
    dest=Path(a.output); dest.parent.mkdir(parents=True,exist_ok=True)
    raw=dest.with_suffix('.offline.wav')
    sf.write(raw,audio,24000,subtype='PCM_16')
    ff=get_ffmpeg_exe()
    partial=dest.with_suffix('.encoding.mp3')
    proc=subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-i',str(raw),
              '-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar','48000','-ac','1',
              '-c:a','libmp3lame','-b:a','192k',str(partial)],capture_output=True,text=True,timeout=180)
    if proc.returncode or not partial.is_file() or partial.stat().st_size<8000:
        raise RuntimeError('Audio mp3 encoding failed: '+proc.stderr[-450:])
    partial.replace(dest)
    raw.unlink(missing_ok=True)
    report={'audio_duration_seconds':round(duration,3),'words':len(content.split()),
            'engine':'kokoro-onnx-resumable','model':'Kokoro v1.0 int8 (Apache-2.0)',
            'voice':a.voice,'sample_rate':48000,'synthetic':True,'source_script':str(script),
            'output':str(dest),'human_listening_review':'not performed',
            'segments':[{'text':s,'duration_seconds':d} for s,d in zip(chunks,durations)]}
    rp=Path(a.report)
    tmp=rp.with_suffix('.partial.json')
    tmp.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    tmp.replace(rp)
    print('OFFLINE_NARRATION_RESUMABLE_OK',round(duration,3),'chunks',len(chunks),'bytes',dest.stat().st_size,flush=True)

if __name__=='__main__':run()
