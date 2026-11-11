"""B1r3: distinctive original case evidence on FIRST FRAME of real videos.

Pillow renders bounded deterministic full-resolution artwork; no third-party
images or real user interfaces. Case media is original, visually labeled
'FICTIONAL', and no looping spinner is drawn. The surrounding native ASS
caption area is owned by the previously tested original renderer.
"""
from __future__ import annotations

from PIL import ImageDraw

IDS = {
    "nov12_short_a_excel_16digits",
    "nov12_short_b_ai_fake_citations",
    "nov12_long_excel_silent_errors",
    "nov12_short_c_drive_link",
}
BG = (13, 29, 45)
WHITE = (249, 252, 254)
MUTED = (155, 190, 213)
WARNING = (255, 131, 113)
OK = (115, 229, 194)
INK = (19, 56, 77)
SHEET = (234, 244, 249)
UI_DARK = (20, 47, 66)


class OriginalHeroRefused(ValueError):
    """Bad source story, scene, color or outside-art instruction."""


def _required(condition, reason):
    if not condition:
        raise OriginalHeroRefused(reason)


def _pr(draw, box, fill, stroke, radius=22, width=3):
    draw.rounded_rectangle(box, radius=radius, fill=fill,
                           outline=stroke, width=width)


def _t(draw, value, x, y, width, size, color=WHITE, strong=True):
    # Reuse the native renderer's bounded font and glyph refusal.
    from autopilot.branch1_nov12_four_review_videos import draw_text
    _required(type(value) is str and "\n" not in value and len(value)<94,
              "Unsafe or unreadable storyboard literal")
    draw_text(draw, value, x, y, width, size, color, strong)


def _start_card(draw, r, label, value, accent, active, shade=WHITE):
    x0, y0, x1, y1 = r
    _pr(draw, r, (35, 66, 83) if active else (24, 47, 66),
        accent if active else (77, 109, 127), 20, 4 if active else 2)
    _t(draw, label, x0+24, y0+20, x1-x0-48, 29,
       accent if active else MUTED)
    _t(draw, value, x0+24, y0+79, x1-x0-48, 66,
       shade if active else (200, 216, 229))


def _short_first_frame(draw, ep, index, phase, accent, box):
    """Issue visible from t=0; phase changes focus, not hidden payoff."""
    x0,y0,x1,y1=box
    kind=ep["id"]
    _pr(draw,box,BG,(76,116,134),30)
    _t(draw,"EXAMPLE  /  ORIGINAL ILLUSTRATION",
       x0+38,y0+28,x1-x0-76,30,accent)
    if kind=="nov12_short_a_excel_16digits":
        _t(draw,"SAME CODE. DIFFERENT LAST DIGIT.",
           x0+38,y0+100,x1-x0-76,36,WHITE)
        raw="1234567890123456"
        wrong="1234567890123450"
        _start_card(draw,(x0+37,y0+199,x1-37,y0+405),
                    "SOURCE: TEXT",raw,OK,phase==1)
        _t(draw,"LAST DIGIT  6  →  0",
           x0+70,y0+455,x1-x0-140,65,WARNING)
        _start_card(draw,(x0+37,y0+594,x1-37,y0+800),
                    "IMPORTED AS NUMBER",wrong,WARNING,phase==2)
        _t(draw,"DON'T PASTE IDS AS NUMBERS",
           x0+48,y1-93,x1-x0-96,33,accent)
    elif kind=="nov12_short_b_ai_fake_citations":
        _t(draw,"THIS PAPER TITLE IS INVENTED.",
           x0+38,y0+101,x1-x0-76,42,WHITE)
        _pr(draw,(x0+37,y0+201,x1-37,y0+677),
            SHEET,accent if phase>=1 else (101,155,166),22,
            5 if phase>=1 else 3)
        _pr(draw,(x0+64,y0+234,x1-64,y0+315),
            (43,84,103),(43,84,103),12)
        _t(draw,"AI-GENERATED REFERENCE",
           x0+87,y0+252,x1-x0-174,32,WHITE)
        _t(draw,"THE INVISIBLE",x0+72,y0+358,
           x1-x0-144,57,INK)
        _t(draw,"SPREADSHEET STUDY",x0+72,y0+437,
           x1-x0-144,55,INK)
        _t(draw,"FICTIONAL TITLE — NOT A REAL PAPER",
           x0+72,y0+537,x1-x0-144,27,(77,106,121))
        _pr(draw,(x0+63,y0+713,x1-63,y0+828),
            (91,43,51) if phase==2 else (52,54,68),
            WARNING if phase==2 else (115,100,111),14)
        _t(draw,"NO SOURCE VERIFIED",
           x0+95,y0+739,x1-x0-190,54,
           WARNING if phase==2 else WHITE)
    elif kind=="nov12_short_c_drive_link":
        _t(draw,"A PRIVATE FILE. A PUBLIC LINK?",
           x0+36,y0+98,x1-x0-72,41,WHITE)
        _pr(draw,(x0+37,y0+204,x1-37,y0+746),
            SHEET,accent if phase>=1 else (92,164,179),21,
            5 if phase>=1 else 3)
        _pr(draw,(x0+60,y0+236,x1-60,y0+313),
            (47,88,105),(47,88,105),12)
        _t(draw,"FICTIONAL FILE SHARING",x0+85,y0+255,
           x1-x0-170,31,WHITE)
        _t(draw,"GENERAL ACCESS",x0+75,y0+360,
           x1-x0-150,34,INK)
        _pr(draw,(x0+73,y0+430,x1-73,y0+597),
            (250,220,197) if phase==2 else (218,233,237),
            WARNING if phase==2 else (119,163,173),14)
        _t(draw,"ANYONE WITH THE LINK",x0+98,y0+475,
           x1-x0-196,48,(119,50,34) if phase==2 else INK)
        _t(draw,"CAN VIEW IF THEY RECEIVE IT",x0+77,y0+650,
           x1-x0-154,29,(63,100,112))
        _t(draw,"CHECK GENERAL ACCESS",
           x0+55,y0+799,x1-x0-110,41,accent)
    else:
        raise OriginalHeroRefused("Missing opening original topic hero")
    # Phase0 contains the full problem+consequence: no 2s blank reveal.


def _short_step_frame(draw, ep, scene, index, phase, accent, box):
    x0,y0,x1,y1=box
    heading,a,b,_=scene
    _pr(draw,box,BG,(69,110,129),27)
    _t(draw,"ACTIONABLE  /  ILLUSTRATIVE",
       x0+40,y0+32,x1-x0-80,32,accent)
    mode=index%4
    if mode==1:
        _t(draw,"THE RULE TO REMEMBER",x0+45,y0+140,
           x1-x0-90,47,MUTED)
        _pr(draw,(x0+44,y0+259,x1-44,y0+545),
            (34,61,82),accent if phase>=1 else (66,91,117),26)
        _t(draw,a,x0+91,y0+341,x1-x0-182,93,WHITE)
        _pr(draw,(x0+44,y0+621,x1-44,y0+820),
            (29,70,78),OK if phase==2 else (69,110,115),22)
        _t(draw,b,x0+88,y0+679,x1-x0-176,73,
           OK if phase==2 else WHITE)
    elif mode==2:
        _t(draw,"DO THIS. THEN CHECK THAT.",
           x0+42,y0+143,x1-x0-84,43,MUTED)
        for j,(text,active) in enumerate(((a,phase>=1),(b,phase==2))):
            r=(x0+42,y0+262+j*301,x1-42,y0+505+j*301)
            _pr(draw,r,(34,75,83) if active else (25,49,69),
                accent if active else (66,94,112),21)
            _t(draw,f"{j+1:02d}",r[0]+40,r[1]+69,107,75,accent)
            _t(draw,text,r[0]+160,r[1]+78,
               r[2]-r[0]-198,61,WHITE)
    elif mode==3:
        _pr(draw,(x0+43,y0+148,x1-43,y0+814),
            SHEET,(105,163,182),24)
        _pr(draw,(x0+63,y0+171,x1-63,y0+260),
            (43,83,106),(43,83,106),12)
        _t(draw,"FICTIONAL SCREEN — CHECK THE DATA",
           x0+85,y0+201,x1-x0-170,29,WHITE)
        for j,(value,active) in enumerate(((a,phase>=1),(b,phase==2))):
            r=(x0+82,y0+307+j*226,x1-82,y0+481+j*226)
            _pr(draw,r,(214,245,240) if active else (217,229,236),
                (38,156,160) if active else (132,161,176),13)
            _t(draw,value,r[0]+24,r[1]+56,r[2]-r[0]-48,60,
               (20,75,84) if active else (59,89,111))
    else:
        _t(draw,"COMPARE BEFORE YOU SHARE",
           x0+40,y0+144,x1-x0-80,44,MUTED)
        _start_card(draw,(x0+40,y0+252,x1-40,y0+504),
                    "BEFORE / SOURCE",a,OK,phase>=1)
        _start_card(draw,(x0+40,y0+573,x1-40,y0+825),
                    "CHECK / ACTION",b,accent,phase>=2)
    _t(draw,"ONE SMALL CHECK CAN PREVENT A BIG ERROR",
       x0+53,y1-78,x1-x0-106,26,MUTED)


# The long video is ONE workbook storyline, not twelve recycled slide cards.
_LONG_STORY = (
    ("1234567890123456","1234567890123450","WATCH THE LAST DIGIT","6 BECOMES 0"),
    ("00123","123","THREE COMMON TRAPS","DIGITS / ZEROS / DATES"),
    ("1234567890123456","1234567890123450","NUMERIC PRECISION","15 SIGNIFICANT DIGITS"),
    ("1234567890123456","1234567890123450","THE VALUE CHANGED","NOT ONLY DISPLAY"),
    ("00123","123","A LEADING ZERO VANISHES","ID ≠ QUANTITY"),
    ("00123","123","THIS IS A CODE","STORE IT AS TEXT"),
    ("12/2","AUTO DATE","DATE DETECTION","VERIFY THE LOCALE"),
    ("00123","123","CSV HAS NO CELL TYPES","CHECK THE IMPORT"),
    ("00123","00123","IMPORT COLUMN AS TEXT","PRESERVE THE SOURCE"),
    ("00123","00123","TEXT BEFORE PASTE","DEFINE THE TYPE FIRST"),
    ("1234567890123450","SOURCE LOST","FORMAT CANNOT RESTORE","REIMPORT ORIGINAL"),
    ("00123","00123","COMPARE SOURCE + OUTPUT","VERIFY BEFORE SHARE"),
)


def _long_workbook(draw, box, row, phase, accent):
    x0,y0,x1,y1=box
    left,right,title,payoff=row
    _pr(draw,box,SHEET,(107,156,180),23)
    _pr(draw,(x0+16,y0+16,x1-16,y0+78),
        (31,79,91),(31,79,91),12)
    _t(draw,"FICTIONAL CSV PREVIEW — NOT A LIVE EXCEL CAPTURE",
       x0+40,y0+29,x1-x0-80,28,WHITE)
    columns=((x0+36,x0+450,"A  /  RAW DATA"),
             (x0+478,x1-34,"B  /  IMPORTED"))
    for cx0,cx1,label in columns:
        _pr(draw,(cx0,y0+112,cx1,y0+181),
            (198,219,230),(161,187,203),11)
        _t(draw,label,cx0+16,y0+130,cx1-cx0-32,27,INK)
    for j,(cx0,cx1,_) in enumerate(columns):
        _pr(draw,(cx0,y0+209,cx1,y0+325),
            (225,249,241) if (phase==1 and j==0)
             else (255,229,218) if (phase==2 and j==1)
             else WHITE,
            OK if (phase==1 and j==0)
            else WARNING if (phase==2 and j==1)
            else (154,185,198),14,4)
        val=left if j==0 else right
        _t(draw,val,cx0+18,y0+245,cx1-cx0-36,53,
           (15,76,73) if j==0 else (151,65,53))
    _t(draw,"SOURCE → TYPE DETECTION → RESULT",
       x0+43,y1-69,x1-x0-86,29,INK)


def _long_editorial(draw, scene, index, phase, accent, box):
    x0,y0,x1,y1=box
    row=_LONG_STORY[index]
    # 45% wider truthful illustration, 55% substantive screen-led lesson.
    _long_workbook(draw,(x0,y0,x0+1002,y1),row,phase,accent)
    cx=x0+1025
    _pr(draw,(cx,y0,x1,y1),(21,41,58),(72,110,134),24)
    _t(draw,"WHY THIS MATTERS",cx+36,y0+33,x1-cx-72,31,accent)
    _t(draw,row[2],cx+38,y0+126,x1-cx-76,53,WHITE)
    _pr(draw,(cx+32,y0+236,x1-32,y0+348),
        (97,45,49) if phase==2 and index in (0,2,3,4,6,7,10)
        else (31,77,76) if phase==2 else (34,57,76),
        WARNING if phase==2 and index in (0,2,3,4,6,7,10)
        else OK if phase==2 else (84,110,130),15)
    _t(draw,row[3],cx+58,y0+265,x1-cx-116,39,
       WARNING if phase==2 and index in (0,2,3,4,6,7,10)
       else OK if phase==2 else WHITE)
    _t(draw,f"CASE {index+1:02d} / 12",
       cx+38,y1-62,x1-cx-76,27,MUTED)
    _required(index<len(_LONG_STORY),"Unknown original long beat")


def overlay_original_hero(image,ep,scene,index,phase,accent):
    """Apply a single visual story to existing subtitle-safe physical frame.

    The older source renderer owns caption placement. This function changes
    ONLY y405–1390 in Shorts or y352–790 in long. No TTS, API, or network.
    """
    _required(type(ep) is dict and ep.get("id") in IDS
              and type(scene) is list and len(scene)==4
              and type(index) is int and 0<=index<len(ep["scenes"])
              and type(phase) is int and phase in (0,1,2)
              and type(accent) is tuple and len(accent)==3
              and image.size==((1080,1920) if ep.get("type")=="short"
                               else (1920,1080)),
              "Untrusted hero and original episode metadata")
    draw=ImageDraw.Draw(image)
    if ep["type"]=="short":
        area=(78,405,1002,1390)
        if index==0:
            _short_first_frame(draw,ep,index,phase,accent,area)
        else:
            _short_step_frame(draw,ep,scene,index,phase,accent,area)
    elif ep["id"]=="nov12_long_excel_silent_errors":
        _long_editorial(draw,scene,index,phase,accent,
                        (108,352,1812,790))
    else:
        raise OriginalHeroRefused("Mismatch between original media and hero")
    return image
