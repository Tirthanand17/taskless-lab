from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"brand"
OUT.mkdir(parents=True,exist_ok=True)

BG="#09111f"; CARD="#121e32"; TEXT="#f7f9fc"; MUTED="#a9bbcf"; CYAN="#5ee7ff"; GREEN="#71efa8"
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def F(n,b=False): return ImageFont.truetype(B if b else R,n)

# 800 x 800 profile image
im=Image.new("RGB",(800,800),BG); d=ImageDraw.Draw(im)
d.rounded_rectangle((82,82,718,718),radius=150,fill=CARD)
d.rounded_rectangle((150,160,650,650),radius=110,outline=CYAN,width=12)
d.text((400,305),"FM",anchor="mm",font=F(205,True),fill=CYAN)
d.text((400,490),"FLOWMINUTE",anchor="mm",font=F(63,True),fill=TEXT)
d.text((400,565),"LAB",anchor="mm",font=F(66,True),fill=GREEN)
im.save(OUT/"profile.png")

# YouTube banner 2560 x 1440; keep important content centered in safe region.
im=Image.new("RGB",(2560,1440),BG); d=ImageDraw.Draw(im)
for x in range(0,2560,160):
    d.line((x,0,x,1440),fill="#0d1a2a",width=1)
for y in range(0,1440,160):
    d.line((0,y,2560,y),fill="#0d1a2a",width=1)
d.rounded_rectangle((485,450,2075,990),radius=70,fill=CARD)
d.text((1280,595),"FLOWMINUTE LAB",anchor="mm",font=F(155,True),fill=CYAN)
d.text((1280,760),"LESS REPETITIVE WORK.",anchor="mm",font=F(58,True),fill=TEXT)
d.text((1280,840),"MORE USEFUL OUTPUT.",anchor="mm",font=F(58,True),fill=GREEN)
d.text((1280,930),"AI • EXCEL • PYTHON • AUTOMATION",anchor="mm",font=F(34,True),fill=MUTED)
im.save(OUT/"banner.png")

# Watermark
im=Image.new("RGBA",(150,150),(0,0,0,0)); d=ImageDraw.Draw(im)
d.rounded_rectangle((8,8,142,142),radius=32,fill=(18,30,50,230),outline=CYAN,width=4)
d.text((75,75),"FM",anchor="mm",font=F(54,True),fill=CYAN)
im.save(OUT/"watermark.png")

print("generated FlowMinute Lab profile, banner and watermark")

# workflow-trigger: brand-assets-v1
