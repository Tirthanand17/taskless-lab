"""B1v10 smoke verification; no release authorization."""
from pathlib import Path
import sys, json, subprocess, hashlib, time
import cv2,numpy as np
from PIL import Image
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'nov22-branch1-recovery'/'ffmpeg_vendor'))
import imageio_ffmpeg
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'vertical-smoke.mp4';c=cv2.VideoCapture(str(p))
w,h=int(c.get(cv2.CAP_PROP_FRAME_WIDTH)),int(c.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps=c.get(cv2.CAP_PROP_FPS);n=int(c.get(cv2.CAP_PROP_FRAME_COUNT))
assert (w,h,n)==(1080,1920,90) and abs(fps-30)<.01
frames=[];tiles=[]
for i in range(n):
 ok,f=c.read();assert ok,i
 if i in (0,30,60,89):
  tiles.append(Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((270,480),Image.Resampling.LANCZOS))
 if i%8==0:frames.append(cv2.resize(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY),(227,402)))
c.release()
sheet=Image.new('RGB',(1080,480))
for i,t in enumerate(tiles):sheet.paste(t,(270*i,0))
sheet.save(R/'smoke-contact.jpg',quality=94)
deltas=[float(np.mean(cv2.absdiff(a,b))) for a,b in zip(frames,frames[1:])]
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(p),'-map','0:v:0','-f','null','NUL'],check=True)
still=R/'landscape-smoke.png'
with Image.open(still) as im:assert im.size==(1920,1080);im.verify()
report={'version':'0.1.0','source_sha256':sha(R/'smoke.tsx'),'vertical_sha256':sha(p),'landscape_sha256':sha(still),'resolution':[w,h],'fps':fps,'frames':n,'duration_seconds':n/fps,'decode_pass':True,'landscape_still_pass':True,'motion_sample_interval_frames':8,'motion_change_fraction_gt_0_5':sum(x>.5 for x in deltas)/len(deltas),'sampled_frames':4,'review_only':True,'audio_present':False,'release_authorized':False}
(R/'SMOKE_QA.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
