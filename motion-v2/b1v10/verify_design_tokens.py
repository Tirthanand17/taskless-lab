"""Validate design tokens: exact native canvas, safe region geometry, readable contrast."""
import json
from pathlib import Path
from itertools import combinations

root = Path(__file__).resolve().parent
d = json.loads((root / "design.json").read_text(encoding="utf-8"))

def inside(a, b):
    return a["x"] >= b["x"] and a["y"] >= b["y"] and a["x"] + a["w"] <= b["x"] + b["w"] and a["y"] + a["h"] <= b["y"] + b["h"]

def overlaps(a, b):
    return max(a["x"], b["x"]) < min(a["x"]+a["w"], b["x"]+b["w"]) and max(a["y"], b["y"]) < min(a["y"]+a["h"], b["y"]+b["h"])

def luminance(h):
    v = [int(h[i:i+2],16)/255 for i in (1,3,5)]
    a = [x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in v]
    return sum(x*y for x,y in zip(a,(.2126,.7152,.0722)))

def contrast(a,b):
    x,y = sorted((luminance(a),luminance(b)))
    return (y+.05)/(x+.05)

for name, shape in (("vertical",(1080,1920)),("landscape",(1920,1080))):
    f = d["formats"][name]
    assert (f["width"],f["height"]) == shape
    assert inside(f["safe"],dict(x=0,y=0,w=shape[0],h=shape[1]))
    for a in f["regions"].values():
        assert a["w"] > 0 and a["h"] > 0 and inside(a,f["safe"])
    assert not any(overlaps(a,b) for a,b in combinations(f["regions"].values(),2))
    assert f["type"]["caption"] >= 36 and f["type"]["small"] >= 24
    print(name, "geometry PASS")
for foreground in ("ink","muted","cyan","lime"):
    for background in ("background","panel","panelLight"):
        c = contrast(d["colors"][foreground],d["colors"][background])
        assert c >= 4.5, (foreground,background,c)
print("12 text contrast pairs PASS; geometry and contrast are not rendered text or human visual QA")
