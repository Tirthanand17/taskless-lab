"""True-3D procedural preview for FlowMinute educational storyboards.

RUN ONLY in an authorized Blender install:
  blender -b --python scripts/blender_story3d_preview.py -- \
    --episode fm_20261024_short_en --shot 3 --output preview.mp4

No external assets, network, desktop path, YouTube action or paid services.
Stylized primitive avatars are placeholders for fully rigged licensed characters.
The result is a geometry-animated SCENE PREVIEW without lip sync, voice or QA.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys

try:
    import bpy
    from mathutils import Vector
except ImportError as exc:
    raise SystemExit("Requires Blender Python (bpy); this is not a 2.5D replacement") from exc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
STORIES = ROOT / "content" / "storyboards" / "oct24_multicharacter_3d_plans.json"


def rgba(hexcode):
    h = hexcode.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1,)


def material(name, color, metallic=0, roughness=0.48, glow=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba(color)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba(color)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if glow:
        bsdf.inputs["Emission Color"].default_value = rgba(color)
        bsdf.inputs["Emission Strength"].default_value = glow
    return mat


def cube(name, location, scale, mat, bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Rounded corners", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def ball(name, location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    ob.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return ob


def point(obj, frame, location=None, rotation=None):
    if location is not None:
        obj.location = location
        obj.keyframe_insert(data_path="location", frame=frame)
    if rotation is not None:
        obj.rotation_euler = rotation
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def make_actor(identity, x, y, seq, palette):
    skin, shirt, hair, accent, white = palette
    root = bpy.data.objects.new("Rig_" + identity, None)
    bpy.context.collection.objects.link(root)
    root.location = (x, y, 0)
    torso = cube(identity + "_torso", (x, y, 1.27), (.74, .40, 1.05), shirt, 0.18)
    head = ball(identity + "_face", (x, y - .06, 2.05), (.32, .29, .38), skin)
    hair_cap = ball(identity + "_hair", (x, y + .025, 2.31), (.32, .28, .19), hair)
    left = ball(identity + "_left_hand", (x - .52, y - .04, 1.41), (.14, .14, .14), skin)
    right = ball(identity + "_right_hand", (x + .52, y - .04, 1.42), (.14, .14, .14), skin)
    # Real geometry is spatially animated, not a parallax movement of a flat image.
    for obj in (torso, head, hair_cap, left, right):
        obj.parent = root
        obj.location = obj.location - Vector((x, y, 0))
    ball(identity + "_left_eye", (x - .11, y - .325, 2.08), (.032,.02,.044), hair)
    ball(identity + "_right_eye", (x + .11, y - .325, 2.08), (.032,.02,.044), hair)
    cube(identity + "_chest_accent", (x, y - .21, 1.40), (.39, .018, .04), accent, 0.01)
    for frame, wave in ((1,0), (seq//2,.12), (seq,-.03)):
        point(root,frame,rotation=(0,0,wave))
        point(right,frame,location=(.52, -.04-.11*math.sin(frame/seq*math.pi),1.40+.18*math.sin(frame/seq*math.pi)))
        point(left,frame,location=(-.52, -.05, 1.36+.09*math.sin(frame/seq*math.pi)))
    return root


def camera_and_light(frames, width, height):
    bpy.ops.object.camera_add(location=(0, -10.7, 4.6))
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    direction = Vector((0, 0.1, 1.35)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z","Y").to_euler()
    cam.data.type = "PERSP"
    cam.data.lens = 38 if width > height else 44
    point(cam,1,location=(-.65,-10.3,4.4))
    point(cam,frames,location=(.55,-9.1,4.0))
    def light(name, xyz, power, hue):
        bpy.ops.object.light_add(type="AREA", location=xyz)
        item=bpy.context.object
        item.name=name
        item.data.energy=power
        item.data.color=hue
        item.data.shape="DISK"
        item.data.size=6
        return item
    light("Cyan key",(-4,-4,6),900,(.42,.94,1))
    light("Warm fill",(5,-2,5),650,(1,.78,.58))
    light("Blue rim",(2,4,5),1100,(.3,.65,1))


def build(episode, shot, output, frames):
    from autopilot.story3d import validate_3d_lesson
    pack = json.loads(STORIES.read_text(encoding="utf-8"))
    doc = next((ep for ep in pack["episodes"] if ep["episode_id"]==episode), None)
    if not doc:
        raise SystemExit("Unknown episode; use an ID from the reviewed episode pack")
    validate_3d_lesson(doc)
    if shot < 1 or shot > len(doc["shots"]):
        raise SystemExit("Shot number out of range")
    scene_info = doc["shots"][shot-1]
    if scene_info["mode"] != "true_3d":
        raise SystemExit("Select a shot planned for true 3D geometry; UI captures cannot be faked")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for item in bpy.data.materials:
        bpy.data.materials.remove(item)
    navy=material("midnight navy","#091c34")
    panels=material("studio wall panels","#142a42",.38)
    floor=material("studio floor","#152f45",.22)
    cyan=material("cyan emission","#16d8ed",.25,.3,2.0)
    gold=material("warm accents","#ffbf7b",.45)
    skin=material("skin","#d9a57b",.05)
    shirts=material("character clothing","#173957",.12)
    hair=material("dark hair","#181b31",.10)
    white=material("soft ivory","#eff9ff")
    cube("true 3D room floor",(0,0,-.09),(12,9,.18),floor)
    cube("rear wall",(0,3.8,3),(12,.3,6),navy)
    for i in range(6):
        cube("wall light panel "+str(i),(-5+i*2,3.59,3.1),(1.55,.12,3.9),panels)
    cube("front holographic desk",(0, -.55,.72),(5.7,1.85,.13),panels)
    for i in range(5):
        cube("desk data stripe "+str(i),(-1.9+i*.95,-1.48,.82),(.7,.015,.04),cyan,.02)
    cube("3D lab monitor",(0,3.25,3.2),(5.0,.18,2.3),panels)
    cube("monitor inner glow",(0,3.12,3.25),(4.45,.09,1.9),cyan)
    for i in range(4):
        cube("hologram bar "+str(i),(-1.5+i,.2,2.4),(.27,.28,.4+i*.25),cyan)
    who={c["id"]:c for c in doc["characters"]}
    present=scene_info["present"]
    spacing=2.5
    for i,name in enumerate(present):
        x=(i-(len(present)-1)/2)*spacing
        make_actor(name,x,-.05,frames,(skin,shirts,hair,cyan,white))
    for n,interaction in enumerate(scene_info["object_interactions"]):
        name=interaction["object"]
        x=-1.8+n*.9
        ob=ball("interacted_3D_object_"+name,(x,-1.3,1.0),(.22,.22,.22),gold)
        point(ob,1,location=(x,-1.3,1.0))
        point(ob,frames//2,location=(x+.25,-1.35,1.62))
        point(ob,frames,location=(x+.5,-1.30,1.06))
    camera_and_light(frames,960,540)
    scene=bpy.context.scene
    scene.render.resolution_x=960
    scene.render.resolution_y=540
    scene.render.resolution_percentage=100
    scene.render.fps=24
    scene.frame_start=1
    scene.frame_end=frames
    scene.render.image_settings.color_mode="RGB"
    if hasattr(scene,"render"):
        try: scene.render.engine="BLENDER_EEVEE_NEXT"
        except Exception: scene.render.engine="BLENDER_EEVEE"
    scene.world.color=(.018,.027,.052)
    scene.view_settings.view_transform="Standard"
    scene.render.image_settings.file_format="FFMPEG"
    scene.render.ffmpeg.format="MPEG4"
    scene.render.ffmpeg.codec="H264"
    scene.render.filepath=str(output)
    # Deliberately no call to bpy.ops.render.render() on import or validation.
    bpy.ops.render.render(animation=True)
    print("TRUE_3D_PREVIEW_RENDERED",episode,"shot",shot,str(output))


def main():
    cli = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument("--episode",required=True)
    parser.add_argument("--shot",type=int,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--frames",type=int,default=96)
    arg=parser.parse_args(cli)
    if not 24<=arg.frames<=240:parser.error("Preview only: 24 to 240 frames")
    if not arg.output.parent.is_dir():parser.error("Output parent must exist")
    if arg.output.suffix.lower() != ".mp4":parser.error("Output must be an MP4 path")
    build(arg.episode,arg.shot,arg.output,arg.frames)


if __name__=="__main__":
    main()
