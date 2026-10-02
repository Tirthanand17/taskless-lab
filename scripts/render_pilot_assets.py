from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "pilot_001"
OUT.mkdir(parents=True, exist_ok=True)
CONTENT = ROOT / "content" / "episodes"
CONTENT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
BG="#09111f"; CARD="#121e32"; CARD2="#172943"; TEXT="#f7f9fc"
MUTED="#a9bbcf"; CYAN="#5ee7ff"; GREEN="#71efa8"; RED="#ff8181"; YELLOW="#ffd966"

FONT_B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def F(size,bold=False): return ImageFont.truetype(FONT_B if bold else FONT_R,size)

def wrap(d,text,font,width):
    out=[]; line=""
    for word in text.split():
        test=(line+" "+word).strip()
        if d.textbbox((0,0),test,font=font)[2] <= width: line=test
        else:
            if line: out.append(line)
            line=word
    if line: out.append(line)
    return out

def pill(d,xy,label,fill,fg=TEXT):
    x1,y1,x2,y2=xy
    d.rounded_rectangle(xy,radius=24,fill=fill)
    d.text(((x1+x2)//2,(y1+y2)//2),label,anchor="mm",font=F(32,True),fill=fg)

def base(kicker,title):
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    pill(d,(60,60,420,132),kicker.upper(),CARD2,CYAN)
    y=185
    for ln in wrap(d,title,F(78,True),W-120):
        d.text((60,y),ln,font=F(78,True),fill=TEXT); y+=92
    return im,d,y

def footer(d):
    d.line((60,H-105,W-60,H-105),fill="#29425f",width=3)
    d.text((60,H-78),"TASKLESS LAB  •  AI + AUTOMATION",font=F(25,True),fill=MUTED)

def table(d,x,y,headers,rows,widths):
    h=78; xx=x
    for i,val in enumerate(headers):
        d.rounded_rectangle((xx,y,xx+widths[i]-8,y+h),radius=16,fill="#1c3656")
        d.text((xx+18,y+22),val,font=F(30,True),fill=TEXT); xx+=widths[i]
    yy=y+h+12
    for row in rows:
        xx=x
        for i,val in enumerate(row):
            d.rounded_rectangle((xx,yy,xx+widths[i]-8,yy+h),radius=16,fill=CARD)
            d.text((xx+18,yy+22),str(val),font=F(27),fill=TEXT); xx+=widths[i]
        yy+=h+12
    return yy

def save_scene(idx,kicker,title,drawer):
    im,d,y=base(kicker,title); drawer(d,y+30); footer(d)
    p=OUT/f"scene_{idx:02}.png"; im.save(p); return p

def s1(d,y):
    d.rounded_rectangle((65,y,1015,y+540),radius=34,fill=CARD)
    d.text((105,y+45),"MESSY CSV",font=F(45,True),fill=RED)
    table(d,105,y+120,["name","email"],[
      (" Alice ","ALICE@EXAMPLE.COM "),("Alice","alice@example.com"),("Bob","  bob@example.com")
    ],[280,550])
    d.text((540,y+505),"↓",anchor="mm",font=F(70,True),fill=CYAN)
    d.rounded_rectangle((65,y+590,1015,y+900),radius=34,fill="#103126")
    d.text((105,y+635),"CLEAN + VALIDATED",font=F(44,True),fill=GREEN)
    for i,t in enumerate(["Standardized fields","Duplicates flagged","Change summary created"]):
        d.text((105,y+720+i*60),t,font=F(34,True),fill=TEXT)

def s2(d,y):
    d.text((70,y),"The problem is often invisible.",font=F(39,True),fill=YELLOW)
    table(d,70,y+90,["Field","Messy value"],[
      ("Email","ALICE@EXAMPLE.COM "),("Header"," Customer ID "),("Missing","N/A / - / blank"),("Duplicate","same row twice")
    ],[250,650])

def s3(d,y):
    d.rounded_rectangle((70,y,1010,y+760),radius=34,fill=CARD)
    pill(d,(110,y+55,380,y+120),"AI PROMPT","#153b4a",CYAN)
    lines=["Normalize column headers","Trim leading/trailing spaces","Standardize email casing","Flag duplicate rows","Do NOT delete anything yet"]
    yy=y+175
    for i,line in enumerate(lines,1):
        d.ellipse((112,yy+8,150,yy+46),fill=CYAN if i<5 else YELLOW)
        d.text((172,yy),line,font=F(35,i==5),fill=TEXT); yy+=100
    d.text((110,y+690),"Specific instructions beat vague “clean this file.”",font=F(30,True),fill=MUTED)

def s4(d,y):
    d.text((70,y),"Ask for a validation summary.",font=F(42,True),fill=YELLOW)
    cards=[("1,248","Rows in",CYAN),("37","Duplicates flagged",RED),("14","Missing emails",YELLOW),("4","Columns changed",GREEN)]
    yy=y+110
    for val,label,color in cards:
        d.rounded_rectangle((90,yy,990,yy+170),radius=28,fill=CARD)
        d.text((150,yy+48),val,font=F(58,True),fill=color)
        d.text((390,yy+62),label,font=F(36,True),fill=TEXT); yy+=195

def s5(d,y):
    d.text((70,y),"Review before export.",font=F(42,True),fill=YELLOW)
    d.rounded_rectangle((70,y+100,1010,y+840),radius=34,fill=CARD)
    d.text((115,y+145),"BEFORE",font=F(38,True),fill=RED); d.text((590,y+145),"AFTER",font=F(38,True),fill=GREEN)
    pairs=[(" Customer ID ","customer_id"),("ALICE@EXAMPLE.COM ","alice@example.com"),("N/A","missing"),("duplicate row","flagged")]
    yy=y+235
    for before,after in pairs:
        d.rounded_rectangle((110,yy,475,yy+105),radius=18,fill="#281d29")
        d.rounded_rectangle((575,yy,940,yy+105),radius=18,fill="#173127")
        d.text((135,yy+34),before,font=F(28,True),fill=TEXT)
        d.text((600,yy+34),after,font=F(28,True),fill=TEXT)
        d.text((525,yy+52),"→",anchor="mm",font=F(36,True),fill=CYAN); yy+=135

def s6(d,y):
    d.rounded_rectangle((75,y+40,1005,y+650),radius=38,fill=CARD)
    d.text((540,y+155),"AUTOMATE THE BORING PART.",anchor="mm",font=F(52,True),fill=CYAN)
    d.text((540,y+270),"VERIFY THE RESULT.",anchor="mm",font=F(60,True),fill=GREEN)
    d.text((540,y+405),"Good automation explains what changed.",anchor="mm",font=F(32,True),fill=TEXT)
    d.text((540,y+475),"Save this workflow for the next messy CSV.",anchor="mm",font=F(29),fill=MUTED)
    pill(d,(280,y+555,800,y+625),"TASKLESS LAB","#173b49",CYAN)

for args in [(1,"HOOK","Stop cleaning CSVs cell by cell.",s1),(2,"PROBLEM","A CSV can look fine and still be messy.",s2),(3,"WORKFLOW","Give AI precise cleanup rules.",s3),(4,"VERIFY","Make the cleanup measurable.",s4),(5,"REVIEW","Never trust silent changes.",s5),(6,"PAYOFF","Faster cleanup. Safer output.",s6)]:
    save_scene(*args)

def thumb(path,headline,accent,badge):
    im=Image.new("RGB",(1280,720),BG); d=ImageDraw.Draw(im)
    pill(d,(60,48,350,108),"TASKLESS LAB",CARD2,CYAN)
    y=155
    for ln in wrap(d,headline,F(72,True),700):
        d.text((60,y),ln,font=F(72,True),fill=TEXT); y+=82
    d.rounded_rectangle((790,120,1215,575),radius=34,fill=CARD)
    d.text((1002,195),"CSV",anchor="mm",font=F(92,True),fill=accent)
    d.text((1002,305),"MESSY",anchor="mm",font=F(46,True),fill=RED)
    d.text((1002,375),"↓",anchor="mm",font=F(52,True),fill=CYAN)
    d.text((1002,455),"CLEAN",anchor="mm",font=F(50,True),fill=GREEN)
    pill(d,(850,600,1155,660),badge,"#173b49",CYAN)
    im.save(OUT/path)

thumb("thumb_a.png","STOP CLEANING CSVs MANUALLY",CYAN,"AI WORKFLOW")
thumb("thumb_b.png","MESSY CSV → CLEAN DATA",GREEN,"BEFORE / AFTER")
thumb("thumb_c.png","AI CSV CLEANUP THAT YOU CAN VERIFY",YELLOW,"SAFER METHOD")

captions=[
 {"start":0.0,"end":3.3,"text":"Stop cleaning messy CSV files cell by cell."},
 {"start":3.3,"end":6.1,"text":"Here’s a safer AI workflow."},
 {"start":6.1,"end":12.0,"text":"Upload a non-sensitive CSV and give precise cleanup rules."},
 {"start":12.0,"end":18.1,"text":"Normalize headers, trim spaces, standardize email casing."},
 {"start":18.1,"end":21.8,"text":"Flag duplicates — don’t delete them yet."},
 {"start":21.8,"end":27.4,"text":"Then ask for a validation summary."},
 {"start":27.4,"end":33.2,"text":"Rows in. Duplicates flagged. Missing values. Columns changed."},
 {"start":33.2,"end":37.1,"text":"Good automation should explain what changed."},
 {"start":37.1,"end":40.8,"text":"Review a few rows, then export."},
 {"start":40.8,"end":44.12,"text":"Faster than manual cleanup — and easier to repeat."}
]
episode={
 "id":"pilot_001",
 "title":"The wrong way to clean your CSV files #productivity #excel #tips",
 "title_variants":[
   {"title":"The wrong way to clean your CSV files #productivity #excel #tips","vidiq_score":94},
   {"title":"Save hours on CSV cleanup #automation #chatgpt #data","vidiq_score":92},
   {"title":"The fastest way to fix messy CSV files #automation #chatgpt #excel","vidiq_score":90}
 ],
 "description":"A safer AI workflow for CSV cleanup: normalize headers, trim whitespace, standardize known fields, flag duplicates, and produce a validation summary before export. Use non-sensitive data and verify important changes before importing into another system. #automation #excel #csv #chatgpt",
 "duration_seconds":44.12,
 "scene_durations":[3.8,8.0,8.5,8.0,8.5,7.32],
 "voice":"Liam - Energetic, Social Media Creator",
 "captions":captions,
 "privacy":"brand-only; no personal data"
}
(CONTENT/"pilot_001.json").write_text(json.dumps(episode,indent=2),encoding="utf-8")
print("pilot assets generated")
