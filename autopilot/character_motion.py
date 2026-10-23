"""Pure-Python 3D character motion and exact prop contact; draft only.

This describes 8 seconds of physical clue handoff. It does not create or license
a character model, generate speech, certify cinematic quality, or publish videos.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import pi, sin, sqrt


@dataclass(frozen=True)
class V3:
    x: float
    y: float
    z: float
    def __add__(self, q: V3) -> V3: return V3(self.x+q.x,self.y+q.y,self.z+q.z)
    def __sub__(self, q: V3) -> V3: return V3(self.x-q.x,self.y-q.y,self.z-q.z)
    def __mul__(self, n: float) -> V3: return V3(self.x*n,self.y*n,self.z*n)
    def __truediv__(self, n: float) -> V3: return self*(1/n)
    def dot(self, q: V3) -> float: return self.x*q.x+self.y*q.y+self.z*q.z
    def norm(self) -> float: return sqrt(self.dot(self))
    def normalized(self) -> V3:
        n=self.norm()
        if n<1e-9: raise ValueError("Degenerate vector")
        return self/n


def clamp(n: float) -> float: return max(0., min(1., n))
def smoothstep(n: float) -> float:
    t=clamp(n)
    return t*t*(3-2*t)
def lerp(a: V3,b: V3,u: float) -> V3: return a+(b-a)*u
def route(t: float, keys: tuple[tuple[float,V3], ...]) -> V3:
    if t<=keys[0][0]: return keys[0][1]
    for (t0,a),(t1,b) in zip(keys,keys[1:]):
        if t<=t1: return lerp(a,b,smoothstep((t-t0)/(t1-t0)))
    return keys[-1][1]


ASHA=V3(-1.75,0.,.18)
KABIR=V3(0.,0.,.18)
UPPER=.53
FOREARM=.48
CUBE_RADIUS=.12


def shoulder(root: V3, side: str) -> V3:
    if side not in ("left","right"): raise ValueError("Unknown hand")
    return root+V3(-.36 if side=="left" else .36,1.97,0.)


def inverse_elbow(upper: V3, wrist: V3, *, side: str) -> V3:
    d=wrist-upper
    length=d.norm()
    if not abs(UPPER-FOREARM)+1e-5<length<UPPER+FOREARM-1e-5:
        raise ValueError("Wrist target outside anatomical reach")
    normal=d.normalized()
    projection=(UPPER*UPPER-FOREARM*FOREARM+length*length)/(2*length)
    radius=sqrt(max(0.,UPPER*UPPER-projection*projection))
    direction=V3(-1. if side=="left" else 1.,-.2,-.25)
    direction=(direction-normal*direction.dot(normal)).normalized()
    result=upper+normal*projection+direction*radius
    if abs((result-upper).norm()-UPPER)>1e-6 or abs((wrist-result).norm()-FOREARM)>1e-6:
        raise AssertionError("Inverse kinematics inaccurate")
    return result


KEYS=(
    (0.,V3(-1.32,1.17,-.43)),(1.45,V3(-1.32,1.17,-.43)),
    (1.95,V3(-1.31,1.42,-.43)),(2.65,V3(-.96,1.50,-.42)),
    (3.15,V3(-.88,1.50,-.42)),(3.50,V3(-.88,1.50,-.42)),
    (4.70,V3(-.40,1.28,-.47)),(8.,V3(-.40,1.28,-.47)),
)
IDLE_ASHA=ASHA+V3(.54,1.42,-.23)
IDLE_KABIR=KABIR+V3(-.49,1.49,-.21)


@dataclass(frozen=True)
class Pose:
    t:float
    cube:V3
    asha_wrist:V3
    kabir_wrist:V3
    asha_elbow:V3
    kabir_elbow:V3
    asha_gripping:bool
    kabir_gripping:bool
    asha_blink:float
    kabir_blink:float
    learner_nod:float
    result_visible:bool


def blink(t:float,centers:tuple[float,...])->float:
    return max((max(0.,1-abs(t-c)/.095) for c in centers),default=0.)


def sample(t:float)->Pose:
    if not 0<=t<=8: raise ValueError("Invalid timeline timestamp")
    cube=route(t,KEYS)
    holdingA=1.48<=t<=3.2
    holdingK=3.2<t<=4.72
    pointA=cube+V3(-CUBE_RADIUS-.045,.005,.015)
    pointK=cube+V3(CUBE_RADIUS+.045,.005,.015)
    inA=smoothstep((t-.78)/.7)
    outA=1-smoothstep((t-3.2)/.70)
    inK=smoothstep((t-2.40)/.80)
    outK=1-smoothstep((t-4.72)/.78)
    wristA=lerp(IDLE_ASHA,pointA,min(inA,outA))
    wristK=lerp(IDLE_KABIR,pointK,min(inK,outK))
    return Pose(t,cube,wristA,wristK,
                inverse_elbow(shoulder(ASHA,"right"),wristA,side="right"),
                inverse_elbow(shoulder(KABIR,"left"),wristK,side="left"),
                holdingA,holdingK,blink(t,(.72,3.9,6.4)),
                blink(t,(1.38,5.8)),
                .085*smoothstep((t-5.25)/1.1)*sin(pi*clamp((t-5.25)/1.8)),
                t>=4.85)


def proof(fps:int=12)->dict:
    if not 8<=fps<=60: raise ValueError("Bad frame rate")
    poses=[sample(i/fps) for i in range(8*fps+1)]
    distances=[]
    for pose in poses:
        if pose.asha_gripping:
            distances.append((pose.asha_wrist-(pose.cube+V3(-CUBE_RADIUS-.045,.005,.015))).norm())
        if pose.kabir_gripping:
            distances.append((pose.kabir_wrist-(pose.cube+V3(CUBE_RADIUS+.045,.005,.015))).norm())
    if not distances: raise AssertionError("Missing prop contact")
    return {
        "frames_evaluated":len(poses),"duration_seconds":8.,
        "maximum_grasp_error_m":max(distances),
        "characters_with_object_contact":2,
        "explicit_blinks":True,"jaw_audio_synced":False,
        "verified_voice_performance":False,"renders_created":0,
        "youtube_uploads":0,"publish_ready":False
    }
