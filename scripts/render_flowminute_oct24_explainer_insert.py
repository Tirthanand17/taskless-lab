"""Original visual-only animated explanation insert, NOT a release-ready YouTube video.

Companion to a separate 8-second completed HeyGen pilot. Zero calls to external
services, subscriptions or cloud APIs. Educational diagrams are conceptual,
never a depiction of a real product UI. Free of personal information.
"""
from __future__ import annotations
import argparse
import math
import subprocess
import wave
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W,H,FPS = 540,960,20
SECS=40
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font_bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if not Path(font_path).is_file(): raise FileNotFoundError('Free system font missing')
font_cache={}
def f(sz,bold=False):
    k=(sz,bold)
    if k not in font_cache: font_cache[k]=ImageFont.truetype(font_bold if bold else font_path,sz)
    return font_cache[k]

navy=(11,19,34)
cyan=(29,233,228)
blue=(100,132,245)
amber=(251,196,96)
white=(244,248,253)
muted=(171,191,213)

# Per-frame base precomputed; radial lighting and small illuminated workshop pixels.
y,x=np.mgrid[0:H,0:W].astype(np.float32)
grad=(np.maximum(0, 1 - ((x-260)**2/(520**2) + (y-420)**2/(640**2))))
base=np.zeros((H,W,3),dtype=np.uint8)
base[...,0]=(12+20*grad).astype('uint8')
base[...,1]=(19+19*grad).astype('uint8')
base[...,2]=(31+26*grad).astype('uint8')
cv2.rectangle(base,(26,172),(514,772),(52,65,79),2,cv2.LINE_AA)
for i in range(14):
    u=30+i*36
    cv2.line(base,(u,171),(u,772),(24,35,50),1,cv2.LINE_AA)
for j in range(18):
    v=180+j*34
    cv2.line(base,(26,v),(514,v),(24,35,50),1,cv2.LINE_AA)
# Background workshop lights
for c in [(54,189),(486,221),(74,691),(450,708),(180,150),(362,148)]:
    cv2.circle(base,c,2,(93,120,133),-1,cv2.LINE_AA)


def rect_alpha(img, x0,y0,x1,y1,color,alpha=.76):
    roi=img[max(0,y0):min(H,y1),max(0,x0):min(W,x1)]
    if not roi.size:return
    roi[:]=(roi.astype(np.float32)*(1-alpha)+np.array(color,dtype=np.float32)*alpha).astype(np.uint8)

def round_box(img,xy,col,thick=1,r=12):
    x0,y0,x1,y1=map(int,xy); cv2.rectangle(img,(x0+r,y0),(x1-r,y1),col,thick,cv2.LINE_AA)
    cv2.rectangle(img,(x0,y0+r),(x1,y1-r),col,thick,cv2.LINE_AA)
    for c,start in [((x0+r,y0+r),180),((x1-r,y0+r),270),((x1-r,y1-r),0),((x0+r,y1-r),90)]:cv2.ellipse(img,c,(r,r),0,start,start+90,col,thick,cv2.LINE_AA)

def iso_block(img,cx,cy,sz,color,phase=0,kind='model'):
    bob=int(math.sin(phase*2.8)*5);cy+=bob
    front=np.array([[cx-sz,cy],[cx,cy+int(sz*.35)],[cx+sz,cy],[cx,cy-int(sz*.35)]],np.int32)
    top=np.array([[cx-sz,cy],[cx-int(sz*.72),cy-int(sz*.7)],[cx+int(sz*.28),cy-int(sz*.98)],[cx,cy-int(sz*.35)]],np.int32)
    right=np.array([[cx,cy-int(sz*.35)],[cx+int(sz*.28),cy-int(sz*.98)],[cx+int(sz*1.28),cy-int(sz*.64)],[cx+sz,cy]],np.int32)
    c=np.array(color,dtype=np.int32)
    def calc(mult):return tuple(int(min(255,v*mult)) for v in c)
    cv2.fillConvexPoly(img,front,calc(.72),cv2.LINE_AA)
    cv2.fillConvexPoly(img,top,calc(1.02),cv2.LINE_AA)
    cv2.fillConvexPoly(img,right,calc(.45),cv2.LINE_AA)
    for poly in [front,top,right]:cv2.polylines(img,[poly],True,calc(1.25),2,cv2.LINE_AA)
    if kind=='model':
        cv2.circle(img,(cx,cy-int(sz*.58)),max(6,sz//7),(245,249,252),2,cv2.LINE_AA)
    return (cx,cy)

def draw_text(img, txt, at, size, color=white,bold=False):
    im=Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))
    d=ImageDraw.Draw(im)
    d.text(at,txt,font=f(size,bold),fill=color,stroke_width=0)
    return cv2.cvtColor(np.array(im),cv2.COLOR_RGB2BGR)

def overlay(img, txt, y, size, color=white, bold=False):
    timg=np.zeros((94,W,4),dtype=np.uint8)
    im=Image.fromarray(timg,'RGBA')
    d=ImageDraw.Draw(im)
    bb=d.textbbox((0,0),txt,font=f(size,bold));tw=bb[2]-bb[0]
    d.text(((W-tw)//2,20),txt,font=f(size,bold),fill=(*color,255))
    layer=np.asarray(im).copy()
    h=min(94,H-y);a=layer[:h,:,3:]/255
    img[y:y+h]=(img[y:y+h].astype(float)*(1-a)+layer[:h,:,:3].astype(float)*a).astype(np.uint8)

def line_animation(img,a,b,phase,col=cyan):
    cv2.line(img,a,b,(60,75,84),5,cv2.LINE_AA)
    cv2.line(img,a,b,tuple(int(v*.84) for v in col),2,cv2.LINE_AA)
    u=(phase*.32)%1
    p=(int(a[0]*(1-u)+b[0]*u),int(a[1]*(1-u)+b[1]*u))
    cv2.circle(img,p,9,(247,255,250),-1,cv2.LINE_AA)
    cv2.circle(img,p,17,col,2,cv2.LINE_AA)

def draw_scene(frame,k,t):
    pulse=(math.sin(2*math.pi*t/3)+1)/2
    # outline progressing with each scene: line timekeeper along top
    cv2.line(frame,(27,128),(513,128),(45,55,71),4,cv2.LINE_AA)
    cv2.line(frame,(27,128),(27+int((k+t/8)/5*486),128),(79,219,232),4,cv2.LINE_AA)
    # atmospheric wide glass table / horizon, constant all scenes
    poly=np.array([[51,677],[486,677],[516,746],[21,746]],np.int32)
    cv2.fillConvexPoly(frame,poly,(26,35,49),cv2.LINE_AA)
    cv2.polylines(frame,[poly],True,(83,111,133),2,cv2.LINE_AA)
    for i in range(2):
        v=int(t*27+i*243)%500
        cv2.line(frame,(30+v,715),(90+v,715),(59,132,150),1,cv2.LINE_AA)
    if k==0:
        cx,cy=270,440
        iso_block(frame,175,443,69,cyan,t,'model')
        iso_block(frame,351,443,69,amber,t+0.7,'model')
        line_animation(frame,(244,485),(282,485),t,cyan)
        overlay(frame,'TWO CHOICES',229,28,bold=True)
        overlay(frame,'not a replacement',527,23,color=muted)
    elif k==1:
        # transparent Model Garden shelves across a room
        overlay(frame,'MODEL GARDEN',221,27,bold=True)
        for i,c in enumerate([cyan,blue,amber]):
            cx=117+153*i
            iso_block(frame,cx,420+int(math.sin(t+i)*9),43,c,t+i)
            cv2.line(frame,(cx-62,501),(cx+65,501),(92,143,171),3,cv2.LINE_AA)
            cv2.line(frame,(cx-62,512),(cx+65,512),(43,58,71),1,cv2.LINE_AA)
        overlay(frame,'a shelf of model options',545,20,color=muted)
    elif k==2:
        overlay(frame,'PICK FOR THE TASK',216,26,bold=True)
        source=(148,438);target=(393,438)
        line_animation(frame,source,target,t,cyan)
        iso_block(frame,*source,50,cyan,t)
        cv2.rectangle(frame,(342,387),(450,486),(32,48,67),-1,cv2.LINE_AA)
        round_box(frame,(342,387,450,486),(91,172,201),2)
        for j in range(4):cv2.line(frame,(362,403+j*19),(430-j*8,403+j*19),(60,189,201),2,cv2.LINE_AA)
        overlay(frame,'Model  >  workflow',528,20,color=muted)
    elif k==3:
        overlay(frame,'ENTERPRISE CONTROLS',210,25,bold=True)
        # physical shield motif to convey governance, not actual security certification
        shield=np.array([[270,324],[363,356],[351,471],[270,540],[189,471],[177,356]],np.int32)
        cv2.fillConvexPoly(frame,shield,(30,65,84),cv2.LINE_AA)
        cv2.polylines(frame,[shield],True,(96,227,226),4,cv2.LINE_AA)
        cv2.line(frame,(223,422),(257,450),(199,250,248),7,cv2.LINE_AA)
        cv2.line(frame,(257,450),(321,391),(199,250,248),7,cv2.LINE_AA)
        overlay(frame,'Data governance matters',545,20,color=muted)
    elif k==4:
        overlay(frame,'CHECK BEFORE USING',215,25,bold=True)
        options=['ACCESS', 'PRICE', 'USE CASE']
        for i,s in enumerate(options):
            yy=341+i*104
            col=[cyan,blue,amber][i]
            rect_alpha(frame,94,yy,455,yy+76,(27,44,59),.82)
            round_box(frame,(94,yy,455,yy+76),col,2,13)
            cv2.circle(frame,(129,yy+38),12,col,-1,cv2.LINE_AA)
            overlay(frame,s,yy+1,24,color=white,bold=True)
        overlay(frame,'Rollout announced Oct 21',690,17,color=muted)

# overlays are computed once; on every frame only dynamic graphics are rendered.
CAPTIONS=[
 ('OPENAI + GOOGLE CLOUD','New model choice for enterprises'),
 ('MODEL GARDEN','Different AI models on one platform'),
 ('CODEX + WORKFLOWS','Choose the tool for the job'),
 ('GOVERNED ACCESS','Controls and policies still apply'),
 ('GENERAL ACCESS COMING','Check availability and price')]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--fps',type=int,default=FPS)
    args=p.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    raw=args.output.with_suffix('.visual_raw.mp4')
    wr=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*'mp4v'),args.fps,(W,H))
    if not wr.isOpened():raise RuntimeError('Failed to initialize video writer')
    try:
        for j in range(int(SECS*args.fps)):
            sec=j/args.fps
            k=min(4,int(sec//8)); t=sec%8
            frame=base.copy()
            # Left-to-right environmental light sweep
            x0=int((sec*37)%(W+280))-140
            cv2.line(frame,(x0,182),(x0+230,745),(31,63,72),1,cv2.LINE_AA)
            draw_scene(frame,k,t)
            # neutral safe header and episode ident
            overlay(frame,'FLOWMINUTE  LAB',25,20,color=(137,245,246),bold=True)
            # upper label and on-frame narration cue (not timed subtitles)
            overlay(frame,CAPTIONS[k][0],81,17,color=white,bold=True)
            overlay(frame,CAPTIONS[k][1],789,19,color=white,bold=True)
            overlay(frame,'CONCEPT VISUAL  |  NOT REAL SOFTWARE UI',851,12,color=muted)
            wr.write(cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
    finally:
        wr.release()
    # Soft original non-musical technical ambience, low level. Not a substitute for VO.
    sr=32000;n=SECS*sr
    idx=np.arange(n,dtype=np.float64)
    signal=np.zeros(n,dtype=np.float64)
    for at in [0,8,16,24,32]:
        s=int((at+.13)*sr);r=min(sr//2,n-s)
        if r<=0:continue
        tt=np.arange(r)/sr
        sweep=np.sin(2*np.pi*(270*tt+650*tt*tt))*np.exp(-8*tt)
        signal[s:s+r]+=.12*sweep
    # Ambient low stereo texture avoids dead silence; no human voice is asserted.
    signal += .005*np.sin(2*np.pi*48*idx/sr)
    wav=args.output.with_suffix('.audio_temp.wav')
    with wave.open(str(wav),'wb') as h:
        h.setnchannels(1);h.setsampwidth(2);h.setframerate(sr)
        h.writeframes((np.clip(signal,-1,1)*32767).astype('<i2').tobytes())
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(raw),'-i',str(wav),'-vf','scale=720:1280:flags=lanczos,format=yuv420p','-r',str(args.fps),'-c:v','libx264','-preset','veryfast','-crf','20','-c:a','aac','-b:a','96k','-shortest','-movflags','+faststart',str(args.output)]
    try:subprocess.run(cmd,check=True)
    finally:raw.unlink(missing_ok=True);wav.unlink(missing_ok=True)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-xerror','-i',str(args.output),'-f','null','-'],check=True)
    print('WROTE',args.output,args.output.stat().st_size)

if __name__=='__main__':main()
