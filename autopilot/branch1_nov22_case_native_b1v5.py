"""FlowMinute 2026-11-22 Branch1 demonstration renderer (no upload and no OAuth).
Original, verifiable case-native visuals from generated CSV and reproducible pandas examples.
Usage: python branch1_case_native.py --root <working folder> --episode short1|short2|long
Runs with Pillow, cv2, numpy, imageio_ffmpeg; full SRT/voice assets must already exist.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, re, subprocess, sys
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

INK=(10,17,31); SURFACE=(20,34,54); WHITE=(245,249,255)
MUTED=(153,174,201); CYAN=(46,226,185); AMBER=(255,189,90)
ROSE=(255,104,130); PURPLE=(183,158,255); BORDER=(53,75,105)
FONT_DIRS=[Path('C:/Windows/Fonts'),Path('/usr/share/fonts/truetype/dejavu')]
FONT_CACHE={}
def font(size,bold=False,mono=False):
    key=(size,bold,mono)
    if key not in FONT_CACHE:
        names=['consola.ttf','DejaVuSansMono.ttf'] if mono else (['segoeuib.ttf','DejaVuSans-Bold.ttf'] if bold else ['segoeui.ttf','DejaVuSans.ttf'])
        found=None
        for directory in FONT_DIRS:
            for name in names:
                p=directory/name
                if p.exists():found=p;break
            if found:break
        FONT_CACHE[key]=ImageFont.truetype(str(found),size) if found else ImageFont.load_default()
    return FONT_CACHE[key]
def text(d,x,y,s,size=36,color=WHITE,bold=False,mono=False):
    d.text((int(x),int(y)),str(s),font=font(size,bold,mono),fill=color,stroke_width=0)
def wrap(d,x,y,s,width,size,color=WHITE,bold=False,mono=False,spacing=1.28,limit=10):
    words=str(s).split(); line='';rows=[]
    for word in words:
        test=(line+' '+word).strip()
        if line and d.textbbox((0,0),test,font=font(size,bold,mono))[2]>width:
            rows.append(line);line=word
        else:line=test
    if line:rows.append(line)
    for i,row in enumerate(rows[:limit]):text(d,x,y+i*int(size*spacing),row,size,color,bold,mono)
    return len(rows[:limit])*size*spacing
def rect(d,box,fill,r=22,outline=None,width=2):
    d.rounded_rectangle([int(n) for n in box],radius=int(r),fill=fill,outline=outline,width=width)
def rule(d,x,y,w,c=CYAN,h=6):d.rectangle((int(x),int(y),int(x+w),int(y+h)),fill=c)
def backdrop(w,h,key):
    # static gradient bands, not a spinner or artificial loop
    im=Image.new('RGB',(w,h),INK);d=ImageDraw.Draw(im)
    for j in range(0,h,34):
        frac=j/h
        d.rectangle((0,j,w,min(h,j+34)),fill=(int(8+frac*6),int(17+frac*11),int(31+frac*13)))
    d.polygon([(w,0),(w,round(h*.41)),(round(w*.51),0)],fill=(16,30,49))
    d.polygon([(0,h),(0,round(h*.75)),(round(w*.28),h)],fill=(13,32,45))
    return im
def base(kind,number,total,kicker,title,detail,accent):
    short=kind!='long';w,h=(1080,1920) if short else (1920,1080)
    im=backdrop(w,h,kind);d=ImageDraw.Draw(im)
    left=62 if short else 90
    rule(d,left,62,27,accent,14)
    text(d,left+47,55,'FLOWMINUTE  /  REAL DATA FIX',26 if short else 29,WHITE,True)
    text(d,w-left-120,58,f'{number:02d}/{total:02d}',24 if short else 27,MUTED,True)
    text(d,left,137,kicker.upper(),27 if short else 28,accent,True)
    wrap(d,left,205,title,w-2*left,64 if short else 73,WHITE,True,spacing=1.14,limit=2)
    detail_y=365 if short else 325
    wrap(d,left,detail_y,detail,w-left*2,28 if short else 28,MUTED,False,limit=2)
    if short:
        text(d,left,1775,'ORIGINAL EDUCATIONAL RECONSTRUCTION  •  NOT LIVE APP FOOTAGE',17,MUTED,True)
    else:
        text(d,left,1013,'GENERATED SAMPLE DATA  /  VERIFIED EXECUTED OUTPUT  /  NO CUSTOMER RECORDS',21,MUTED,True)
    return im,d,(w,h,left)
def chip(d,x,y,t,c=CYAN,fs=26):
    w=int(d.textbbox((0,0),t,font=font(fs,True))[2])+36
    rect(d,(x,y,x+w,y+fs+33),(26,51,66),14,outline=c)
    text(d,x+18,y+15,t,fs,c,True)
    return w

def panel(d,r,label=None,stroke=BORDER):
    rect(d,r,SURFACE,24,stroke,3)
    if label:
        x,y,x2,y2=r
        text(d,x+24,y+24,label,23,MUTED,True)
def datatable(d,x,y,w,headers,rows,col_fracs=None,highlight=None,negative=None,row_h=88,header_h=74,fs=32):
    n=len(headers);col_fracs=col_fracs or [1/n]*n
    rect(d,(x,y,x+w,y+header_h+len(rows)*row_h+12),(19,41,61),20,BORDER)
    d.rounded_rectangle((x+5,y+5,x+w-5,y+header_h),radius=16,fill=(37,62,82))
    cursor=x+22
    xspots=[]
    for frac,head in zip(col_fracs,headers):
        xspots.append(cursor)
        text(d,cursor,y+25,head,26,MUTED,True)
        cursor+=int(w*frac)
    for i,row in enumerate(rows):
        yy=y+header_h+i*row_h
        ishi=(highlight==i);isbad=(negative==i)
        fill=(27,76,73) if ishi else ((79,44,60) if isbad else ((25,43,62) if i%2==0 else (29,48,67)))
        d.rectangle((x+6,yy,x+w-6,yy+row_h-3),fill=fill)
        for j,v in enumerate(row):
            text(d,xspots[j],yy+20,str(v),fs,CYAN if ishi else (ROSE if isbad else WHITE),True if ishi else False,mono=j==0)
    return y+header_h+len(rows)*row_h+12
def codebox(d,x,y,w,lines,label='PYTHON  /  VERIFIED EXAMPLE',font_size=35,emphasis=None):
    height=106+len(lines)*int(font_size*1.63)
    panel(d,(x,y,x+w,y+height),label)
    for i,line in enumerate(lines):
        c=CYAN if emphasis==i else (AMBER if ('#' in line or 'ERROR' in line) else WHITE)
        text(d,x+30,y+84+i*int(font_size*1.63),line,font_size,c,False,True)
    return y+height
def metric(d,x,y,w,label,value,accent=CYAN,large=False):
    h=175 if large else 138
    panel(d,(x,y,x+w,y+h),None,stroke=accent)
    text(d,x+27,y+20,label,27,MUTED,True)
    text(d,x+27,y+(62 if large else 56),str(value),78 if large else 62,accent,True)
    return h

def scene_short1(idx,phase=0):
    accent=CYAN
    headlines=[('BEFORE / AFTER','ONE CSV ID. TWO VALUES.','Your order match can silently fail.'),
    ('THE SOURCE FILE','THE ZEROS ARE REALLY THERE','Generated orders.csv. Original identifier must survive.'),
    ('THE FIX','TELL PANDAS IT IS TEXT','Use the exact column name and string type.'),
    ('EXECUTED RESULT','00123 IS STILL 00123','The Python output is reproduced from the supplied CSV.'),
    ('THE RULE','AN ID IS NOT A NUMBER','Save this before your next CSV import.')]
    im,d,(w,h,L)=base('short1',idx+1,5,*headlines[idx],accent)
    if idx==0:
        panel(d,(L,480,w-L,1290),'ONE IDENTIFIER — TWO DIFFERENT VALUES')
        rect(d,(L+45,610,w-L-45,855),(19,74,69),26,CYAN,5)
        text(d,L+85,640,'CSV VALUE',31,MUTED,True)
        text(d,L+100,715,'00123',115,CYAN,True,True)
        rect(d,(L+45,920,w-L-45,1162),(77,39,58),26,ROSE,5)
        text(d,L+85,948,'NUMERIC IMPORT',31,MUTED,True)
        text(d,L+100,1023,'123',110,ROSE,True,True)
        chip(d,L+25,1355,'MISMATCH — NOT EQUAL',ROSE,29)
    elif idx==1:
        datatable(d,L,497,w-2*L,['order_id','customer','amount'],[['00123','Maya','499'],['00124','Ravi','299'],['00125','Nina','300']],col_fracs=[.39,.37,.24],highlight=0,fs=35,row_h=126,header_h=98)
        chip(d,L,1125,'GENERATED INPUT — NOT REAL SALES',CYAN)
    elif idx==2:
        codebox(d,L,510,w-2*L,['pd.read_csv(',"  'orders_sample.csv',",'  dtype={',"    'order_id': 'string'",'  }',')'],font_size=39,emphasis=3)
        chip(d,L,1260,'KEY IDEA: IDENTIFIER = STRING',CYAN,26)
    elif idx==3:
        codebox(d,L,530,w-2*L,['$ python verified_demo.py',"First preserved ID: '00123'", "First cleaned customer: 'Maya'"],font_size=31,emphasis=1)
        metric(d,L,1010,w-2*L,'LEADING ZERO PRESERVED','00123',CYAN,True)
        chip(d,L,1290,'REAL EXECUTED PYTHON OUTPUT',CYAN)
    else:
        metric(d,L,530,w-2*L,'IDENTIFIER','00123',CYAN,True)
        metric(d,L,745,w-2*L,'NUMERIC QUANTITY','123',ROSE,True)
        panel(d,(L,1000,w-L,1290))
        wrap(d,L+35,1050,'READ ID COLUMNS AS TEXT BEFORE ANY CALCULATION.',w-2*L-70,49,WHITE,True,limit=3)
    return im

def scene_short2(idx,phase=0):
    accent=AMBER
    heads=[('MERGE WARNING','3 ORDERS BECAME 4 ROWS!','One repeated customer key changes the final total.'),
           ('THE INPUT','WATCH CUSTOMER ID A02','A02 appears twice in the customer table.'),
           ('THE BAD RESULT','THE JOIN REPEATS A SALE','The default merge does not require unique keys.'),
           ('ONE-LINE GUARDRAIL','MAKE YOUR JOIN CHECK ITSELF','validate="one_to_one" refuses duplicate join keys.'),
           ('ACTUAL ERROR','STOP BEFORE REPORTING TOTALS','It warns you; it does not choose which record to delete.')]
    im,d,(w,h,L)=base('short2',idx+1,5,*heads[idx],accent)
    if idx==0:
        metric(d,L,502,(w-2*L-24)//2,'BEFORE MERGE','3',CYAN,True)
        metric(d,L+(w-2*L-24)//2+24,502,(w-2*L-24)//2,'AFTER MERGE','4',ROSE,True)
        panel(d,(L,780,w-L,1280),'FALSE REVENUE IN THIS GENERATED EXAMPLE')
        text(d,L+36,877,'$90  -->  $120',78,ROSE,True,True)
        chip(d,L+40,1105,'DUPLICATED ROW = DUPLICATED $30',ROSE)
    elif idx==1:
        datatable(d,L,500,w-2*L,['cust_id','orders'],[['A01','20'],['A02','30'],['A03','40']],col_fracs=[.57,.43],highlight=1,row_h=93,fs=38)
        datatable(d,L,1055,w-2*L,['cust_id','tier'],[['A01','Basic'],['A02','Gold'],['A02','Trial'],['A03','Basic']],col_fracs=[.57,.43],highlight=2,row_h=73,fs=35)
    elif idx==2:
        datatable(d,L,520,w-2*L,['cust_id','amount','tier'],[['A01','20','Basic'],['A02','30','Gold'],['A02','30','Trial'],['A03','40','Basic']],col_fracs=[.36,.34,.30],negative=2,row_h=109,fs=34)
        chip(d,L,1240,'BAD TOTAL: 20 + 30 + 30 + 40 = 120',ROSE,25)
    elif idx==3:
        codebox(d,L,530,w-2*L,['orders.merge(', '    customers,','    on="cust_id",', '    validate="one_to_one"',')'],font_size=36,emphasis=3)
        chip(d,L,1200,'THE CODE CHECKS THE JOIN TYPE',CYAN,25)
    else:
        codebox(d,L,533,w-2*L,['MergeError:', 'Merge keys are not unique', 'in right dataset;', 'not a one-to-one merge'],font_size=33,emphasis=0)
        panel(d,(L,1160,w-L,1440))
        wrap(d,L+33,1205,'INSPECT DUPLICATE KEYS. DO NOT DELETE BLINDLY.',w-2*L-66,41,WHITE,True,limit=3)
    return im

def scene_long(idx,phase=0):
    A=PURPLE; L=95;W=1920
    heads=[('REAL DATA PROBLEM','ONE ID. TWO AMOUNTS.','Would you trust an automatic duplicate remover?'),
    ('GENERATED DATA','OUR 9-ROW CSV','A deliberately messy test dataset — no real customers.'),
    ('STEP 1 / TYPES','PRESERVE ORDER IDs','00123 and 123 are not interchangeable IDs.'),
    ('STEP 2 / TEXT','REMOVE HIDDEN SPACES','Normalize names without changing original records.'),
    ('STEP 3 / DUPES','DELETE ONLY EXACT MATCHES','One identical duplicate can be identified safely.'),
    ('STEP 4 / CONFLICTS','SAME ID ≠ SAME RECORD','Two different amounts require a human decision.'),
    ('STEP 5 / MISSING','EMPTY IS NOT ZERO','Do not silently invent missing transaction values.'),
    ('CHECKPOINT','TRACK EVERY EXCEPTION','Nine rows become one duplicate, two conflicts, one blank and five ready.'),
    ('VERIFIED RESULT','FIVE CLEAN ORDERS: ₹1,218','The result is computed from unambiguous sample records.'),
    ('TAKEAWAY','CLEAN WITHOUT DATA LOSS','Make exceptions visible instead of hiding them.')]
    im,d,(w,h,L)=base('long',idx+1,10,*heads[idx],A)
    Y=443
    if idx==0:
        datatable(d,L,Y,860,['order_id','amount'],[['00125','300'],['00125','350']],col_fracs=[.55,.45],negative=1,row_h=133,header_h=78,fs=63)
        metric(d,1050,502,750,'UNRESOLVED CONFLICT','₹50',ROSE,True)
        text(d,1050,749,'Do not guess which amount is correct.',29,MUTED)
    elif idx==1:
        datatable(d,L,Y,1260,['ID','customer','amount'],[['00123','Maya','499'],['00124','Ravi','299'],['00123','Maya','499'],['00125','Nina','300'],['00125','Nina','350'],['00126','Arun','—'],['00127','Sara','120'],['00128','Meera','210'],['00129','Salma','90']],col_fracs=[.34,.34,.32],highlight=2,row_h=52,header_h=64,fs=27)
        metric(d,1413,488,400,'INPUT ROWS','9',A,True)
        text(d,1419,745,'Repeated IDs, hidden spaces,',26,MUTED)
        text(d,1419,785,'and a missing amount.',26,MUTED)
    elif idx==2:
        codebox(d,L,Y,1030,['df = pd.read_csv(',"  'orders_sample.csv',",'  dtype={"order_id":"string"}',')'],font_size=39,emphasis=2)
        metric(d,1180,520,620,'FIRST RESULT',"'00123'",CYAN,True)
    elif idx==3:
        codebox(d,L,Y,980,['df["customer"] = (', '  df["customer"]', '   .str.replace("\\u00a0", " ")','   .str.strip()',')'],font_size=37,emphasis=2)
        metric(d,1110,514,690,'AFTER CLEANING',"'Maya'",CYAN,True)
    elif idx==4:
        datatable(d,L,Y,880,['ID','customer','amount'],[['00123','Maya','499'],['00123','Maya','499']],col_fracs=[.4,.34,.26],negative=1,row_h=124,fs=44)
        codebox(d,1060,483,750,['df.drop_duplicates()'],font_size=34,emphasis=0)
        metric(d,1060,685,750,'REMOVED','1 exact duplicate',CYAN,False)
    elif idx==5:
        datatable(d,L,Y,860,['ID','customer','amount'],[['00125','Nina','300'],['00125','Nina','350']],col_fracs=[.35,.34,.31],negative=1,row_h=127,fs=45)
        codebox(d,1030,493,780,['duplicate ID 00125', 'amount differs: 300 / 350', 'ACTION: REVIEW BOTH'],font_size=31,emphasis=2)
    elif idx==6:
        datatable(d,L,Y,930,['order_id','customer','amount'],[['00126','Arun','BLANK']],col_fracs=[.33,.34,.33],negative=0,row_h=144,fs=48)
        codebox(d,1110,490,685,['pd.to_numeric(', '  df["amount"],', '  errors="coerce")'],font_size=31,emphasis=2)
    elif idx==7:
        for n,(a,b,c) in enumerate([('INPUT','9',CYAN),('EXACT DUP','1',AMBER),('CONFLICT','2',ROSE),('MISSING','1',PURPLE)]):
            x=L+n*441
            metric(d,x,498,410,a,b,c,True)
        metric(d,L,749,1728,'READY UNAMBIGUOUS RECORDS','5',CYAN,False)
    elif idx==8:
        metric(d,L,Y,800,'READY RECORDS','5',CYAN,True)
        metric(d,990,Y,830,'TOTAL FROM THESE 5','₹1,218',CYAN,True)
        codebox(d,L,677,1728,['499 + 299 + 120 + 210 + 90 = 1218'],font_size=44,emphasis=0)
    else:
        cards=[('1', 'PRESERVE IDs',CYAN),('2','NORMALIZE TEXT',PURPLE),('3','REMOVE EXACT DUPES',AMBER),('4','FLAG CONFLICTS',ROSE),('5','REVIEW MISSING',CYAN)]
        for i,(n,label,c) in enumerate(cards):
            y=440+i*97
            rect(d,(L,y,1818,y+80),(23,43,62),16,c,2)
            text(d,L+29,y+15,n,35,c,True)
            text(d,L+110,y+18,label,34,WHITE,True)
    return im

SCENES={'short1':5,'short2':5,'long':10}
# Boundaries sourced from word-timed exact narration; SRT checked before render.
# No guessed dynamic synchronization after speech ends.
SEGMENT_START={'short1':[0,6.0,11.0,16.4,22.0],
               'short2':[0,5.8,11.7,17.8,23.2],
               'long':[0,8.4,14.0,31.0,45.4,57.0,66.0,75.0,86.0,99.8]}

def verify_srt(path,video_duration):
    txt=path.read_text(encoding='utf8').strip()
    spans=[]
    for b in re.split(r'\n\s*\n',txt):
        z=b.splitlines()
        if len(z)<3 or '-->' not in z[1]:raise ValueError('invalid SRT cue')
        t=z[1].split('-->')
        def s(time):
            h,m,sec,ms=map(int,time.strip().replace(', ',':').replace(',',':').split(':'))
            return h*3600+m*60+sec+ms/1000
        spans.append((s(t[0]),s(t[1])))
    if not spans or spans[-1][1]>video_duration+.08: raise ValueError('SRT exceeds video end')
    return len(spans),spans[-1][1]

def ffprobe_duration(ffmpeg,path):
    p=subprocess.run([ffmpeg,'-hide_banner','-i',str(path)],capture_output=True,text=True)
    m=re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)',p.stderr)
    if not m:raise RuntimeError('No readable duration for '+str(path))
    return int(m[1])*3600+int(m[2])*60+float(m[3])
def asset_prep(root,ep,only_preview=False):
    stage_count=SCENES[ep]; render=scene_long if ep=='long' else (scene_short1 if ep=='short1' else scene_short2)
    stage_dir=root/(ep+'_native_scenes');stage_dir.mkdir(parents=True,exist_ok=True)
    # Every shot has a different meaningful information organization or error-state outcome.
    imgs=[]
    for i in range(stage_count):
        image=render(i)
        path=stage_dir/f'scene_{i:02}.png';image.save(path,optimize=True)
        imgs.append(path)
    # Contact sheet for real visual inspection before any media publishing.
    cols=2 if ep!='long' else 3
    thumbs=[]
    for p in imgs:
        with Image.open(p) as im:
            snap=im.copy(); snap.thumbnail((480,680) if ep!='long' else (580,325))
            thumbs.append(snap)
    cw=max(im.width for im in thumbs);ch=max(im.height for im in thumbs);rows=math.ceil(len(thumbs)/cols)
    board=Image.new('RGB',(cols*(cw+24)+24,rows*(ch+70)+24),(20,31,49));d=ImageDraw.Draw(board)
    for i,im in enumerate(thumbs):
        x=24+(i%cols)*(cw+24);y=24+(i//cols)*(ch+70)
        board.paste(im,(x,y));text(d,x,y+ch+17,f'SHOT {i+1:02} / {stage_count:02}',24,WHITE,True)
    board_path=root/f'{ep}_native_contact_sheet.jpg';board.save(board_path,quality=90)
    # Thumbnail is separately composed for 16:9 long and vertical Shorts. This does not
    # mean the YouTube Studio thumbnail was uploaded or accepted.
    first=render(0)
    with first:
        th=first.copy()
        if ep=='long':th=th.resize((1280,720),Image.Resampling.LANCZOS)
        d=ImageDraw.Draw(th);w,h=th.size
        if ep!='long':
            rect(d,(65,500,w-65,940),(9,23,40),32,CYAN if ep=='short1' else AMBER,8)
            title1='00123 ≠ 123' if ep=='short1' else '3 ROWS → 4?!'
            tag='DON\'T LOSE IDs' if ep=='short1' else 'MERGE WARNING'
            text(d,95,595,title1,93,WHITE,True)
            text(d,95,770,tag,52,CYAN if ep=='short1' else AMBER,True)
        else:
            rect(d,(75,230,w-75,500),(9,23,40),32,PURPLE,7)
            text(d,112,263,'DON\'T DELETE',80,WHITE,True)
            text(d,112,370,'GOOD ORDERS',74,PURPLE,True)
        thumb=root/f'{ep}_NATIVE_thumbnail.png';th.save(thumb,optimize=True)
    return imgs,board_path,thumb

def render_one(root,episode):
    import imageio_ffmpeg
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    voice=root/f'{episode}_final_voice.mp3';srt=root/f'{episode}.srt'
    if not voice.is_file() or voice.stat().st_size<10000:raise RuntimeError('Missing valid narration '+str(voice))
    if not srt.is_file():raise RuntimeError('Missing SRT '+str(srt))
    voice_secs=ffprobe_duration(ffmpeg,voice);total=voice_secs+0.8
    cues,lastcue=verify_srt(srt,total)
    imgs,board,thumbnail=asset_prep(root,episode)
    starts=SEGMENT_START[episode]
    if starts[-1]>=total-1 or len(starts)!=len(imgs):raise ValueError('Invalid editorial timeline')
    ends=starts[1:]+[total]
    fc=root/f'{episode}_native_frames.ffconcat'
    lines=['ffconcat version 1.0']
    for start,end,img in zip(starts,ends,imgs):
        dur=end-start
        if dur<1.1:raise ValueError('Unreadable scene')
        # full shot then highlighted result state via controlled cut, no looping animation
        lines.append("file '"+img.as_posix()+"'");lines.append('duration '+f'{dur:.3f}')
    lines.append("file '"+imgs[-1].as_posix()+"'")
    fc.write_text('\n'.join(lines)+'\n',encoding='utf8')
    out=root/f'{episode}_B1V5_NATIVE_REVIEW_ONLY.mp4'
    cmd=[ffmpeg,'-nostdin','-hide_banner','-loglevel','warning','-y',
         '-f','concat','-safe','0','-i',str(fc),'-i',str(voice),
         '-vf','fps=24,format=yuv420p','-t',f'{total:.3f}',
         '-map','0:v:0','-map','1:a:0','-c:v','libx264','-threads','3',
         '-preset','faster','-crf','20','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','160k','-ar','48000','-movflags','+faststart',str(out)]
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode:raise RuntimeError('FFmpeg failed '+p.stderr[-1200:])
    p=subprocess.run([ffmpeg,'-v','error','-xerror','-i',str(out),'-f','null','-'],capture_output=True,text=True)
    if p.returncode:raise RuntimeError('Full decode failed '+p.stderr[-800:])
    cap=cv2.VideoCapture(str(out));w=int(cap.get(3));h=int(cap.get(4));fps=cap.get(5);frames=cap.get(7);cap.release()
    expect=(1920,1080) if episode=='long' else (1080,1920)
    if (w,h)!=expect or abs(fps-24)>.1:raise RuntimeError('Wrong output dimensions/fps')
    sha=hashlib.sha256(out.read_bytes()).hexdigest()
    report={'episode':episode,'video':str(out),'sha256':sha,'width':w,'height':h,'fps':fps,'duration_seconds':round(frames/fps,3),'caption_cues':cues,'last_caption_end':lastcue,
            'technical_decoding':'PASS','thumbnail':str(thumbnail),'contact_sheet':str(board),
            'narration_full_listening':'PENDING','editorial_creative_approval':'PENDING',
            'youtube_upload':False,'youtube_schedule':False,'studio_verification':False}
    (root/f'{episode}_b1v5_technical_qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print('B1V5_RENDER_AND_DECODE_PASS',episode,json.dumps({k:report[k] for k in ('sha256','duration_seconds','width','height','caption_cues')},ensure_ascii=False),flush=True)
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--episode',choices=['short1','short2','long'],required=True);ap.add_argument('--preview-only',action='store_true');a=ap.parse_args()
    if a.preview_only:
        paths=asset_prep(a.root,a.episode)
        print('PREVIEW_READY',a.episode,paths[1],paths[2])
    else:render_one(a.root,a.episode)