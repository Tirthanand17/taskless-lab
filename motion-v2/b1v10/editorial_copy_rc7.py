"""Correct RC7 Short opening copy without disturbing the captured proof or soundtrack."""
import argparse,json,subprocess,tempfile
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from production_review_rc6 import read,sha,exact,need,inspect_video,inspect_audio
from narration_review import pcm
D=Path(__file__).resolve().parent
COPY={
 "sha256":(71,"One byte changes.","Why a different hash?","THE QUESTION","Same hash algorithm","Different input, different fingerprint."),
 "float":(102,"Simple math.","Unexpected answer.","THE SURPRISE","Look at the extra digits.","Why does Python print this?")
}
def plate(size,title,lines):
 im=Image.new("RGB",size,"#132536");d=ImageDraw.Draw(im)
 d.rounded_rectangle((1,1,size[0]-2,size[1]-2),22,outline="#45627A",width=2)
 for (text,y,n,color) in lines:
  f=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",n)
  need(d.textlength(text,font=f)<size[0]-56,"copy overflow")
  d.text((28,y),text,font=f,fill=color)
 return im
def run(k,video,out,ffmpeg):
 old=next(x for x in read("RC7_OPENING_QA.json")["pilots"] if x["pilot"]==k)
 exact(video,old["mp4_sha256"]);out.mkdir(parents=True,exist_ok=False);out=out.absolute()
 end,h1,h2,kicker,t1,t2=COPY[k]
 header=plate((824,226),"header",[("FLOWMINUTE / "+("FILE INTEGRITY" if k=="sha256" else "PYTHON LAB"),14,28,"#72E3ED"),(h1,62,60,"#F3F7FC"),(h2,140,50,"#D1FA83")])
 proof=plate((824,300),"proof",[(kicker,30,30,"#72E3ED"),(t1,99,44,"#F3F7FC"),(t2,196,32,"#B7CBDD")])
 header.save(out/"header.png");proof.save(out/"proof.png")
 def ff(args):subprocess.run([ffmpeg,"-nostdin","-v","error",*map(str,args)],check=True)
 final=out/"EDITORIAL_REVIEW.mp4";silent=out/"silent.mp4"
 filter=f"[0:v][1:v]overlay=72:190:enable='lt(n,{end})'[h];[h][2:v]overlay=72:1070:enable='lt(n,{end})'[out]"
 ff(["-i",video,"-i",out/"header.png","-i",out/"proof.png","-filter_complex_threads","1","-filter_complex",filter,"-map","[out]","-an","-frames:v",old["frames"],"-c:v","libx264","-preset","fast","-crf","18","-threads","2","-pix_fmt","yuv420p",silent])
 ff(["-i",silent,"-i",video,"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",final])
 inspect_video(final,old["resolution"],30,old["frames"],ffmpeg,True)
 audio=inspect_audio(final,ffmpeg,old["audio"]["decoded_samples"])
 with tempfile.TemporaryDirectory() as t:
  wavs=[Path(t)/f"{i}.wav" for i in range(2)]
  for p,v in zip(wavs,(video,final)):ff(["-i",v,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",p])
  need(np.array_equal(pcm(wavs[0]),pcm(wavs[1])),"audio changed")
 prior=cv2.VideoCapture(str(video));new=cv2.VideoCapture(str(final));obs=[]
 try:
  for r in old["opening_panels"]:
   x,y,w,h=r["roi"]
   for frame in (r["start_frame"],(r["start_frame"]+r["end_frame"])//2,r["end_frame"]-1):
    prior.set(cv2.CAP_PROP_POS_FRAMES,frame);new.set(cv2.CAP_PROP_POS_FRAMES,frame)
    a,f=prior.read();b,g=new.read();need(a and b,"decode")
    err=float(np.mean(cv2.absdiff(f[y:y+h,x:x+w],g[y:y+h,x:x+w])))
    need(err<5,"original captured evidence changed")
    obs.append({"frame":frame,"mean_pixel_error":round(err,4)})
    if frame==0:Image.fromarray(cv2.cvtColor(g,cv2.COLOR_BGR2RGB)).resize((360,640),Image.Resampling.LANCZOS).save(out/"opening.jpg",quality=95)
 finally:prior.release();new.release()
 report={"version":"1.0.0-rc7-phase2","pilot":k,"prior_sha256":old["mp4_sha256"],"mp4_sha256":sha(final),"frames":old["frames"],"resolution":old["resolution"],"audio":audio,"pcm_identical":True,"observed_evidence":obs,"opening_proof_frame":0,"copy":list(COPY[k]),"full_decode_pass":True,"release_authorized":False,"legacy_creative_pass":False}
 (out/"EDITORIAL_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,indent=2))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--pilot",choices=COPY,required=True);p.add_argument("--video",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args();run(a.pilot,a.video.absolute(),a.out,a.ffmpeg)
if __name__=="__main__":main()
