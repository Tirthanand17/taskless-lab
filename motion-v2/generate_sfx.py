from pathlib import Path
import math, wave, struct

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"public"
OUT.mkdir(parents=True,exist_ok=True)
SR=44100

def write(name, samples):
    mx=max(1e-9,max(abs(x) for x in samples))
    scale=min(1.0,0.82/mx)
    with wave.open(str(OUT/name),"w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for x in samples:
            v=int(max(-1,min(1,x*scale))*32767)
            w.writeframes(struct.pack("<h",v))

def click():
    n=int(SR*.09)
    s=[]
    for i in range(n):
        t=i/SR
        env=math.exp(-42*t)
        s.append(env*(0.8*math.sin(2*math.pi*900*t)+0.25*math.sin(2*math.pi*1800*t)))
    return s

def warning():
    n=int(SR*.28)
    s=[]
    for i in range(n):
        t=i/SR
        env=min(1,t/.025)*math.exp(-5.5*t)
        freq=430 if t<.14 else 350
        s.append(env*.6*math.sin(2*math.pi*freq*t))
    return s

def confirm():
    n=int(SR*.30)
    s=[]
    for i in range(n):
        t=i/SR
        env=min(1,t/.02)*math.exp(-5*t)
        freq=620 if t<.13 else 820
        s.append(env*.45*math.sin(2*math.pi*freq*t))
    return s

write("ui-click.wav",click())
write("warning.wav",warning())
write("confirm.wav",confirm())
print("generated",OUT)
