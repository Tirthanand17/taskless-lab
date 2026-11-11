"""B1v4: native context-rich fictional product walkthrough instead of 15 reused slides.

All UI is drawn in original Pillow vector artwork from authenticated source
scripts, not screenshots from an actual Excel/Chrome/ChatGPT/Sheets account.
Source and consequence visible from frame zero; no looping shapes or stock.
This module ONLY owns the content-area pixels; captions/audio stay untouched.
"""
from __future__ import annotations

from PIL import ImageDraw

from autopilot.branch1_nov12_four_review_videos import draw_text

BG=(12,29,44)
FRAME=(63,115,138)
INK=(22,55,75)
WHITE=(248,252,255)
MUTED=(117,150,170)
PAPER=(236,247,251)
LILAC=(228,220,250)
GREEN=(202,246,226)
ORANGE=(255,227,210)
GREEN_DARK=(18,113,81)
ORANGE_DARK=(135,61,43)
GOOGLE_BLUE=(66,131,203)

class FictionalUIRefused(ValueError):
    """No off-topic, out-of-frame, untrusted case can replace original media."""


def ok(test,reason):
    if not test:
        raise FictionalUIRefused(reason)


def rounded(d,r,fill,stroke=None,rad=16,width=2):
    d.rounded_rectangle(tuple(map(int,r)),radius=rad,fill=fill,
                        outline=stroke if stroke is not None else fill,width=width)


def text(d,t,x,y,w,sz=35,color=INK,bold=True):
    ok(type(t) is str and "\n" not in t and 1<=len(t)<=98
       and w>24 and x>=0 and y>=0,"Unsafe bounded case caption or mock UI")
    draw_text(d,t,int(x),int(y),int(w),int(sz),color,bold)


def heading(d,r,title,app,accent):
    x0,y0,x1,y1=r
    rounded(d,r,PAPER,FRAME,24)
    rounded(d,(x0+12,y0+12,x1-12,y0+99),BG,BG,13)
    text(d,app,x0+35,y0+28,x1-x0-70,29,accent)
    text(d,"FICTIONAL DATA  /  EDUCATIONAL MOCKUP",x0+35,y0+62,
         x1-x0-70,21,(196,217,229),False)


def chip(d,r,value,active,accent,dark=INK):
    x0,y0,x1,y1=r
    rounded(d,r,GREEN if active else WHITE,accent if active else (156,184,198),14,3)
    text(d,value,x0+22,y0+15,x1-x0-44,46,dark)


def excel_short(d,r,a,b,index,phase,accent):
    x0,y0,x1,y1=r
    heading(d,r,"","SYNTHETIC WORKBOOK  /  CHECK THE INPUT",accent)
    inner=(x0+30,y0+140,x1-30,y1-105)
    u0,v0,u1,v1=inner
    rounded(d,inner,WHITE,(151,184,198),17)
    # A genuine workbook grammar, not floating two-card infographic.
    rounded(d,(u0+14,v0+15,u1-14,v0+92),(225,236,242),None,9)
    text(d,"A",u0+51,v0+36,90,34,INK)
    text(d,"B",u0+343,v0+36,90,34,INK)
    text(d,"C",u0+626,v0+36,90,34,INK)
    for row in range(4):
        y=v0+110+row*132
        d.rectangle((u0+19,y,u1-19,y+122),
                    fill=(246,250,252) if row%2==0 else (230,241,247))
        text(d,str(row+2),u0+35,y+42,45,32,MUTED,False)
        d.line((u0+269,y,u0+269,y+122),fill=(171,198,213),width=2)
        d.line((u0+540,y,u0+540,y+122),fill=(171,198,213),width=2)
        if row==1:
            rounded(d,(u0+85,y+13,u0+518,y+112),
                    GREEN if phase==1 else (223,238,241),
                    accent if phase==1 else (138,188,196),13,4)
            text(d,a,u0+105,y+37,375,55,INK)
        if row==2:
            rounded(d,(u0+85,y+13,u0+518,y+112),
                    ORANGE if phase==2 else (242,234,222),
                    (241,111,79) if phase==2 else (180,154,139),13,4)
            text(d,b,u0+105,y+36,375,55,ORANGE_DARK)
        if row==0:
            text(d,"SOURCE",u0+103,y+40,440,35,INK)
        if row==3:
            text(d,"VERIFY THE REAL VALUE",u0+102,y+42,600,29,INK)
    rounded(d,(u0+17,v1-109,u1-17,v1-18),(29,72,92),None,12)
    text(d,"fx    "+("SOURCE   →   CHECK" if index%2 else "DATA TYPE   →   RESULT"),
         u0+50,v1-85,u1-u0-100,29,WHITE)
    text(d,"MATCH THE SOURCE BEFORE CHANGING A CELL",x0+33,y1-76,
         x1-x0-66,25,INK)


def browser_short(d,r,a,b,index,phase,accent):
    x0,y0,x1,y1=r
    heading(d,r,"","BROWSER SETTINGS  /  FAKE EXAMPLE",accent)
    inner=(x0+30,y0+140,x1-30,y1-104)
    u0,v0,u1,v1=inner
    rounded(d,inner,WHITE,(159,181,201),15)
    rounded(d,(u0+15,v0+17,u1-15,v0+96),(230,239,243),None,11)
    text(d,"example.test  /  settings / permissions",u0+36,v0+42,
         u1-u0-72,29,INK,False)
    text(d,"SITE ACCESS",u0+29,v0+139,u1-u0-58,41,INK)
    rows=[("NOTIFICATIONS","Allowed" if index%2==0 else "Ask"),
          ("LOCATION","Ask first"),("CAMERA","Blocked")]
    for j,(label,state) in enumerate(rows):
        y=v0+212+j*102
        rounded(d,(u0+23,y,u1-23,y+90),
                (238,246,248) if j%2 else (226,237,242),None,10)
        text(d,label,u0+44,y+25,470,30,INK)
        rounded(d,(u1-234,y+14,u1-44,y+77),
                GREEN if phase==1 and j==0 else (208,223,234),None,25)
        text(d,state.upper(),u1-215,y+29,160,26,INK)
    rounded(d,(u0+21,v1-225,u1-21,v1-129),
            GREEN if phase==1 else (235,242,247),
            accent if phase==1 else FRAME,14)
    text(d,a,u0+57,v1-196,u1-u0-110,48,INK)
    rounded(d,(u0+21,v1-109,u1-21,v1-12),
            ORANGE if phase==2 else (238,235,231),
            (241,111,79) if phase==2 else (184,164,155),14)
    text(d,b,u0+57,v1-80,u1-u0-110,48,ORANGE_DARK)
    text(d,"NOT REAL ACCOUNT SETTINGS",x0+38,y1-76,x1-x0-76,26,INK)


def ai_short(d,r,a,b,index,phase,accent):
    x0,y0,x1,y1=r
    heading(d,r,"","CHAT ASSISTANT  /  FICTIONAL CONVERSATION",accent)
    inner=(x0+30,y0+140,x1-30,y1-101)
    u0,v0,u1,v1=inner
    rounded(d,inner,(242,248,253),(151,176,201),18)
    rounded(d,(u0+22,v0+31,u1-210,v0+128),
            (222,230,245),None,20)
    text(d,"MY QUESTION ABOUT PRIVACY",u0+45,v0+64,u1-u0-295,34,INK)
    rounded(d,(u0+101,v0+183,u1-26,v0+430),
            GREEN if phase==1 else (229,241,244),
            accent if phase==1 else (154,185,204),20)
    text(d,"CURRENT CHAT MODE",u0+137,v0+214,u1-u0-195,29,MUTED)
    text(d,a,u0+137,v0+303,u1-u0-190,61,INK)
    rounded(d,(u0+22,v0+493,u1-108,v0+734),
            ORANGE if phase==2 else (236,235,240),
            (243,130,109) if phase==2 else (176,171,188),20)
    text(d,"CHECK THE EFFECT",u0+58,v0+518,u1-u0-170,29,MUTED)
    text(d,b,u0+58,v0+609,u1-u0-170,60,ORANGE_DARK)
    text(d,"TEMPORARY ≠ ZERO RETENTION",x0+35,y1-74,
         x1-x0-70,27,INK)


def sheets_short(d,r,a,b,index,phase,accent):
    x0,y0,x1,y1=r
    heading(d,r,"","SHARED SPREADSHEET  /  FICTIONAL TEAM",accent)
    inner=(x0+28,y0+140,x1-28,y1-100)
    u0,v0,u1,v1=inner
    rounded(d,inner,WHITE,(126,174,187),16)
    rounded(d,(u0+14,v0+15,u1-14,v0+82),
            (31,103,72),None,12)
    text(d,"TEAM SHEET  /  DATA     FILTER VIEW",u0+35,v0+34,
         u1-u0-70,31,WHITE)
    labels=("NAME","ROLE","STATUS")
    for j,label in enumerate(labels):
        text(d,label,u0+44+j*250,v0+124,230,30,INK)
    rows=[("Alex","Editor","Active"),("Blair","Viewer","Active"),
          ("Casey","Editor","Filtered")]
    for j,row in enumerate(rows):
        y=v0+178+j*116
        rounded(d,(u0+26,y,u1-26,y+109),
                (230,245,239) if j==1 and phase==1 else
                (236,245,250) if j%2 else (247,251,253),None,10)
        for k,v in enumerate(row):
            text(d,v,u0+43+k*250,y+39,235,30,INK)
    rounded(d,(u0+26,v1-246,u1-26,v1-134),
            GREEN if phase==1 else (231,242,246),
            accent if phase==1 else (117,161,177),13)
    text(d,a,u0+54,v1-208,u1-u0-108,55,INK)
    rounded(d,(u0+26,v1-121,u1-26,v1-13),
            ORANGE if phase==2 else (241,231,229),
            (239,115,94) if phase==2 else (177,145,144),13)
    text(d,b,u0+54,v1-89,u1-u0-108,54,ORANGE_DARK)
    text(d,"EDIT ACCESS AND FILTER VIEWS DIFFER",x0+33,y1-75,
         x1-x0-66,26,INK)


def long_ui(d,r,a,b,index,phase,accent,variant):
    x0,y0,x1,y1=r
    rounded(d,r,(226,241,249),FRAME,22)
    width=x1-x0
    left=(x0+12,y0+12,x0+int(width*.67),y1-12)
    l0,t0,l1,t1=left
    rounded(d,left,WHITE,(148,184,201),14)
    bar=(l0+11,t0+11,l1-11,t0+72)
    barcolor=(31,90,75) if variant=="sheets" else (
        (30,65,98) if variant=="ai" else (37,76,93))
    rounded(d,bar,barcolor,None,9)
    app={"excel":"FICTIONAL WORKBOOK / VALUE CHECK",
         "browser":"FICTIONAL PERMISSION SETTINGS",
         "ai":"FICTIONAL CHAT MODE COMPARISON",
         "sheets":"FICTIONAL SHARED SHEET"}[variant]
    text(d,app,l0+34,t0+27,l1-l0-68,27,WHITE)
    # App-native content: alternating row grid, error/status cells,
    # privacy mode conversation boxes or browser permission controls.
    if variant in ("excel","sheets"):
        for col,name in enumerate(("A","B","C")):
            text(d,name,l0+89+col*295,t0+90,100,24,INK)
        for j in range(2):
            y=t0+142+j*120
            rounded(d,(l0+29,y,l1-30,y+107),
                    (218,245,229) if phase==1 and j==0 else
                    (255,226,215) if phase==2 and j==1 else
                    (236,244,248),None,10)
            text(d,f"{j+2:02d}",l0+44,y+32,50,29,MUTED,False)
            text(d,a if j==0 else b,l0+109,y+25,l1-l0-145,
                 58,INK if j==0 else ORANGE_DARK)
    elif variant=="browser":
        for j in range(2):
            y=t0+123+j*144
            rounded(d,(l0+31,y,l1-32,y+130),
                    (228,244,238) if j==0 and phase==1 else
                    (255,235,219) if j==1 and phase==2 else
                    (234,244,249),None,12)
            text(d,"CURRENT" if j==0 else "REVIEW ACTION",
                 l0+49,y+17,l1-l0-98,24,MUTED)
            text(d,a if j==0 else b,l0+49,y+67,l1-l0-98,54,
                 INK if j==0 else ORANGE_DARK)
    else:
        for j in range(2):
            y=t0+123+j*144
            right_shift=75 if j==0 else 15
            rounded(d,(l0+29+right_shift,y,l1-29-(0 if j==0 else 75),y+129),
                    (222,235,247) if j==0 and phase==1 else
                    (255,226,214) if j==1 and phase==2 else
                    (235,242,247),None,22)
            text(d,"CHAT MODE" if j==0 else "WHAT CHANGES",
                 l0+58+right_shift,y+14,l1-l0-180,24,MUTED)
            text(d,a if j==0 else b,l0+58+right_shift,y+70,
                 l1-l0-190,52,INK if j==0 else ORANGE_DARK)
    # One decisive teaching card on the right; not 12 identical full slides.
    rx0=l1+10
    rounded(d,(rx0,y0+13,x1-13,y1-13),(18,43,61),(91,136,154),17)
    text(d,f"REAL CASE  {index+1:02d} / 12",rx0+28,y0+36,
         x1-rx0-56,27,accent)
    text(d,"SOURCE",rx0+28,y0+133,x1-rx0-56,24,(183,210,220))
    text(d,a,rx0+29,y0+174,x1-rx0-58,50,WHITE)
    text(d,"CHECK / RESULT",rx0+28,y0+277,x1-rx0-56,24,(183,210,220))
    text(d,b,rx0+29,y0+319,x1-rx0-58,45,
         (255,176,140) if phase==2 else WHITE)


def paint_story_ui(draw,ep,scene,index,phase,accent,area):
    """Opaque replacement of generic center cards only, no captions touched."""
    ok(type(ep) is dict and type(scene) is list and len(scene)==4
       and type(index) is int and 0<=index<len(ep["scenes"])
       and type(phase) is int and phase in (0,1,2)
       and type(accent) is tuple and len(accent)==3,
       "Unsafe or repeated source data for one-way original UI")
    date=ep.get("date_ist")
    ok(date in {f"2026-11-{n:02d}" for n in range(13,18)},
       "Unexpected target date outside owner-selected original calendar")
    variant="excel" if date in ("2026-11-13","2026-11-15") else (
        "browser" if date=="2026-11-14" else
        "ai" if date=="2026-11-16" else "sheets")
    a,b=scene[1:3]
    # Only overwrite the original approved center rectangle, leaving the
    # scene-specific question, printed source label, progress and fixed
    # physical ASS subtitle area at unchanged pixel coordinates.
    if ep["kind"]=="short":
        factory={"excel":excel_short,"browser":browser_short,
                 "ai":ai_short,"sheets":sheets_short}[variant]
        factory(draw,area,a,b,index,phase,accent)
    elif ep["kind"]=="long":
        long_ui(draw,area,a,b,index,phase,accent,variant)
    else:
        raise FictionalUIRefused("No unknown original media type")
