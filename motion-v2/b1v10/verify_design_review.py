"""Create hash-bound review evidence for four native-HD stills, not publication approval."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps, ImageDraw

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("review", type=Path)
args = p.parse_args()
root = Path(__file__).resolve().parent
review = args.review.resolve()
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

files = []
sheet = Image.new("RGB", (960, 1010), "#09131f")
draw = ImageDraw.Draw(sheet)
for name, dims, target, top in (
    ("vertical", (1080,1920), (270,480), 30),
    ("landscape", (1920,1080), (450,253), 565),
):
    for i, frame in enumerate((15,75)):
        file = review / f"{name}-{frame}.png"
        with Image.open(file) as im:
            if im.size != dims or im.format != "PNG":
                raise ValueError(f"Invalid native PNG: {file}")
            im.load()
            rgb = im.convert("RGB")
            if max(lohi[1]-lohi[0] for lohi in rgb.getextrema()) < 50:
                raise ValueError(f"Unexpected blank image: {file}")
            thumbnail = ImageOps.contain(rgb,target,Image.Resampling.LANCZOS)
            x = 20 + i * 480
            sheet.paste(thumbnail, (x,top))
            draw.text((x,top-20),f"{name} / frame {frame}",fill="white")
        files.append({"file":file.name,"frame":frame,"dimensions":list(dims),"sha256":sha(file)})
    if files[-1]["sha256"] == files[-2]["sha256"]:
        raise ValueError(f"Identical start and end stills: {name}")
sheet = sheet.crop((0,0,960,840))
sheet.save(review/"contact.jpg",quality=94)
report = {"version":"0.2.0","source_sha256":{name:sha(root/name) for name in
          ("design.json","visual-system.tsx","design-demo.tsx","verify_design_tokens.py","render_design_review.cjs")},
          "stills":files,"contact_sha256":sha(review/"contact.jpg"),
          "native_png_decode_pass":True,"distinct_sampled_states":True,
          "review_only":True,"full_playback_verified":False,"narration_verified":False,
          "human_visual_approval":False,"release_authorized":False}
(review/"DESIGN_REVIEW_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
