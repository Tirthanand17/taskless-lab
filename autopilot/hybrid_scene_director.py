"""FlowMinute mixed 3D + digital-illustration scene director, no cube-only loop.

Actual original procedural visuals for script BEATS, not scraped Instagram
assets. Uses already installed Pillow and reusable source-controlled true 3D
mesh projection. A source-bound seven-beat plan changes visual subject, camera,
composition, color, motion style and 3D/digital family between each beat.

The plan is DRAFT creative evidence only: no real people/shops, paid assets,
image/video models, external demos, voice/audio, login, rights or publishing.
"""
from __future__ import annotations

from dataclasses import dataclass,asdict
from hashlib import sha256
from math import pi,sin,cos
from typing import Sequence

from PIL import Image,ImageDraw

from .agent_org import WorkflowError
from .oct20_mesh_cinematic_proof import (
    WIDTH,HEIGHT,FPS,BLUE,TEAL,WHITE,_camera,mesh_cube,project_vertex,
)

@dataclass(frozen=True)
class ShotRecipe:
    beat:int
    visual_family:str
    composition:str
    lens:str
    graphic_subject:str
    teaching_purpose:str
    motion:str
    original_assets_only:bool=True
    actual_real_app_screenshot:bool=False

RECIPES=(
 ShotRecipe(0,"digital_illustration","radial_network","macro_push",
            "neon_agent_network","hook: what can act?","pulsing_neural_path"),
 ShotRecipe(1,"stylized_3d","product_table","wide_orbit",
            "grocery_bag_and_food","show fictional grocery example","object_parallax"),
 ShotRecipe(2,"stylized_3d","device_cutaway","over_shoulder",
            "shopping_draft_phone","draft cart, not purchase","scroll_card"),
 ShotRecipe(3,"digital_illustration","branch_diagram","top_down",
            "decision_flow_arrows","compare before payment","routing_pulse"),
 ShotRecipe(4,"hybrid_3d_illustration","security_closeup","low_angle",
            "large_checkout_padlock","do not buy without approval","lock_glow"),
 ShotRecipe(5,"digital_illustration","access_matrix","orthographic",
            "feature_plan_region_grid","feature availability is conditional","status_reveal"),
 ShotRecipe(6,"hybrid_3d_illustration","human_decision","eye_level",
            "human_review_phone","viewer retains final control","approval_hold"),
)
FAMILIES=frozenset(("digital_illustration","stylized_3d",
                    "hybrid_3d_illustration"))


def _hold():
    raise WorkflowError("FlowMinute hybrid visual scene policy HOLD")


def scene_recipe_plan(episode_id:str,scene_count:int=7)->dict:
    if (type(episode_id) is not str or not episode_id.startswith("fm_")
            or not 5<len(episode_id)<81
            or type(scene_count) is not int or scene_count!=7):
        _hold()
    if tuple(r.beat for r in RECIPES)!=tuple(range(7)):
        _hold()
    if (len({x.graphic_subject for x in RECIPES})!=7
            or len({x.composition for x in RECIPES})!=7
            or len({x.lens for x in RECIPES})<5
            or {x.visual_family for x in RECIPES}!=FAMILIES
            or any(not r.original_assets_only or r.actual_real_app_screenshot
                   for r in RECIPES)):
        _hold()
    # Independent episodes get different bounded composition emphasis/seed,
    # while the seven pedagogical beats remain coherent and reproducible.
    seed=int.from_bytes(sha256(episode_id.encode()).digest()[:2],"big")
    shots=[{**asdict(recipe),
            "bounded_visual_variant":(seed+7*recipe.beat)%5,
            "copyright_verified":False,
            "real_demo_verified":False,
            "release_approved":False} for recipe in RECIPES]
    return {
        "status":"SEVEN_HYBRID_ORIGINAL_CONCEPT_SHOTS_EDITORIAL_ONLY",
        "episode_id":episode_id,
        "scene_count":7,
        "shot_recipes":shots,
        "unique_subjects":7,
        "unique_compositions":7,
        "different_camera_lenses":len({r.lens for r in RECIPES}),
        "digital_scenes":sum(r.visual_family=="digital_illustration"
                             for r in RECIPES),
        "mesh_or_hybrid_scenes":sum(r.visual_family!="digital_illustration"
                                   for r in RECIPES),
        "repeat_one_subject_all_scenes":False,
        "genuine_cinematic_photorealism_verified":False,
        "voice_or_subtitle_sync_verified":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "external_network_calls":0,
        "monthly_recurring_infrastructure_inr":0,
    }


def _points(d,coords,fill,width=3):
    d.line(coords,fill=fill,width=width,joint="curve")


def _mesh(d,center,size,spin,color,camera):
    faces=mesh_cube(center,size,spin,color,camera)
    for _,poly,shade,_ in sorted(faces,key=lambda x:-x[0]):
        d.polygon(poly,fill=(*shade,255))
        d.line([*poly,poly[0]],fill=(122,228,240,180),width=2)


def _card(d,bounds,color=(11,39,60,246),outline=(42,173,201,220),r=22):
    d.rounded_rectangle(bounds,radius=r,fill=color,outline=outline,width=2)


def _original_neon(d,t,variant):
    # Neural graph is a real moving digital illustration, not flat cubes.
    core=(270+18*sin(t*.5),505+16*cos(t*.4))
    for ring in range(4):
        radius=68+ring*62+5*sin(t*1.2+ring)
        d.ellipse((core[0]-radius,core[1]-radius,
                   core[0]+radius,core[1]+radius),
                  outline=(29,78+ring*19,146+ring*16,108),width=2)
    nodes=[]
    for j in range(21):
        a=j*2*pi/21+(variant*.13)
        r=115+72*(j%4)/3+7*sin(t*.8+j)
        x=core[0]+cos(a)*r
        y=core[1]+sin(a)*r
        nodes.append((x,y))
        d.ellipse((x-6,y-6,x+6,y+6),
                  fill=(17+4*(j%5),169+7*(j%7),217,230))
    for j in range(21):
        a=nodes[j]
        b=nodes[(j*7+3)%21]
        _points(d,[a,b],(12,108,154,120),2)
    for j in range(4):
        x,y=nodes[(int(t*4)+j*5)%21]
        d.ellipse((x-10,y-10,x+10,y+10),fill=(65,230,213,245))
    d.ellipse((core[0]-47,core[1]-47,core[0]+47,core[1]+47),
              fill=(7,67,104,255),outline=(70,235,221,255),width=5)
    d.arc((core[0]-20,core[1]-14,core[0]+20,core[1]+19),
          start=25,end=330,fill=(*WHITE,255),width=4)


def _grocery_world(d,t,variant):
    # 3D rotated grocery package meshes and hand-drawn original produce/bag.
    camera=_camera(int(24*t)+variant*6)
    for i,(xyz,color) in enumerate((
        ((-2.0,-.38,0),(35,176,208)),
        ((-.8,-.23,.3),(220,158,77)),
        ((1.3,-.28,-.2),(26,176,108)),
    )):
        _mesh(d,(xyz[0],xyz[1]+.12*sin(t+i),xyz[2]),
              1.15 if i!=1 else 1.55,.2+i*.37+t*.21,color,camera)
    # Representative illustrated groceries; no seller/brand/real prices.
    _card(d,(95,603,446,730),(25,45,52,241),(92,173,150,255),15)
    d.polygon([(147,645),(175,572),(246,572),(268,645)],
              fill=(183,143,89,255),outline=(236,199,146,255))
    d.arc((174,540,247,612),40,180,fill=(225,185,128,255),width=6)
    d.ellipse((298,590,375,666),fill=(224,71,68,255),
              outline=(252,150,100,255),width=3)
    d.ellipse((323,577,348,603),fill=(33,174,100,255))
    d.polygon([(386,672),(411,604),(434,667)],
              fill=(39,188,116,255))


def _phone_world(d,t,variant):
    # Isometric phone + distinct original check-list overlays, no fake UI.
    lean=12*sin(t*.6+variant)
    quad=[(144+lean,330),(364+lean,351),(344+lean,727),(121+lean,707)]
    d.polygon([(x+13,y+16) for x,y in quad],fill=(4,12,33,255))
    d.polygon(quad,fill=(22,40,72,255),outline=(78,218,242,255),width=5)
    d.rounded_rectangle((170+lean,377,333+lean,412),radius=12,
                        fill=(31,93,123,255))
    for i,color in enumerate(((14,186,139),(44,176,212),(188,127,72))):
        y=459+i*78+(4*sin(t+i))
        d.rounded_rectangle((170+lean,y,312+lean,y+52),radius=10,
                            fill=(15,62,78,255),
                            outline=(*color,255),width=3)
        d.ellipse((183+lean,y+14,204+lean,y+35),fill=(*color,255))
        d.line((217+lean,y+24,287+lean,y+24),
               fill=(167,211,220,255),width=4)
    d.rounded_rectangle((156+lean,684,309+lean,710),radius=10,
                        fill=(86,100,112,150),outline=(90,200,211,255))
    _points(d,[(366,562),(438,572),(452,614)],
            (27,210,164,255),5)
    d.ellipse((433,610,464,641),outline=(27,210,164,255),width=4)


def _flow_world(d,t,variant):
    stages=[(103,422),(264,335),(422,422),(264,600)]
    for i in range(4):
        a=stages[i];b=stages[(i+1)%4]
        d.line((a[0],a[1],b[0],b[1]),fill=(43,158,196,255),width=5)
        f=(t*.45+i*.25)%1
        x=a[0]+(b[0]-a[0])*f
        y=a[1]+(b[1]-a[1])*f
        d.ellipse((x-7,y-7,x+7,y+7),fill=(91,241,218,255))
    for i,(x,y) in enumerate(stages):
        col=((30,136,194),(23,193,141),(227,147,65),(178,83,133))[i]
        d.rounded_rectangle((x-53,y-47,x+53,y+47),
                            radius=24,fill=(*col,255),
                            outline=(170,230,233,255),width=3)
        for j in range(3):
            d.line((x-28,y-22+j*19,x+27,y-22+j*19),
                   fill=(227,247,255,255),width=4)


def _lock_world(d,t,variant):
    camera=_camera(14+int(t*24))
    _mesh(d,(0,0,0),2.8,.12+sin(t*.2)*.08,(19,150,185),camera)
    pulse=6*sin(t*1.5)
    d.arc((167,342-pulse,377,574-pulse),180,359,
          fill=(72,226,228,255),width=17)
    d.rounded_rectangle((149,475,389,693),radius=26,
                        fill=(13,60,77,251),
                        outline=(75,235,195,255),width=7)
    d.ellipse((246,545,292,591),fill=(174,247,244,255))
    d.polygon([(265,571),(280,630),(251,630)],
              fill=(174,247,244,255))
    d.line((165,692,373,480),fill=(244,91,102,190),width=6)


def _availability_world(d,t,variant):
    for i in range(3):
        top=360+i*120
        _card(d,(55,top,484,top+92),(15,48,75,245),
              (49,147+20*i,187,255),17)
        d.ellipse((82,top+20,135,top+73),
                  fill=(24,106+35*i,148,255),
                  outline=(95,220,238,255),width=3)
        for j in range(2):
            y=top+30+j*26
            d.line((159,y,345-(j*40),y),
                   fill=(125,195,209,255),width=5)
        d.rounded_rectangle((367,top+25,455,top+63),radius=13,
                            outline=(230,182,105,255),width=3,
                            fill=(89,69,55,255))
    d.arc((200,302,341,382),150,330,fill=(67,226,210,255),width=5)


def _human_control_world(d,t,variant):
    # Schematic original generic human, not a real/personality likeness.
    camera=_camera(12+int(t*13))
    _mesh(d,(1.8,-.3,-.8),1.6,.35+t*.13,(21,162,184),camera)
    d.ellipse((88,315,227,453),fill=(207,161,124,255),
              outline=(249,205,172,255),width=4)
    d.polygon([(101,453),(217,453),(257,692),(49,692)],
              fill=(22,126,157,255),outline=(71,201,220,255))
    _card(d,(285,432,470,695),(15,59,86,248),
          (49,213,181,255),21)
    d.line((309,491,372,547,449,463),fill=(113,244,187,255),width=11)
    d.ellipse((335,624,412,676),outline=(66,236,208,255),width=5)
    d.line((230,532,295,576),fill=(205,164,125,255),width=24)


_DRAW=(
    _original_neon,
    _grocery_world,
    _phone_world,
    _flow_world,
    _lock_world,
    _availability_world,
    _human_control_world,
)


def render_scene_world(image:Image.Image,episode_id:str,
                       scene_index:int,frame_number:int)->None:
    """Paint distinct 3D/illustrative story props INSIDE existing frame."""
    if (type(image) is not Image.Image or image.size!=(WIDTH,HEIGHT)
            or image.mode!="RGBA" or type(scene_index) is not int
            or not 0<=scene_index<7
            or type(frame_number) is not int or frame_number<0
            or type(episode_id) is not str):
        _hold()
    info=scene_recipe_plan(episode_id)
    variant=info["shot_recipes"][scene_index]["bounded_visual_variant"]
    d=ImageDraw.Draw(image,"RGBA")
    _DRAW[scene_index](d,frame_number/FPS,variant)
