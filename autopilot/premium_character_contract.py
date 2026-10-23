"""Stage-only quality contract for expressive, premium-looking human 3D characters.

These specs are requirements, NOT evidence that rigs, voices or rights exist.
"""
from __future__ import annotations

JOINTS={"hips","spine","neck","head","shoulder_left","shoulder_right",
        "elbow_left","elbow_right","wrist_left","wrist_right",
        "knee_left","knee_right","ankle_left","ankle_right"}
FACE={"blink_left","blink_right","jaw_open","brow_raise",
      "smile_left","smile_right","viseme_A","viseme_O","viseme_MBP"}
ACTIONS={"gaze","gesture","expression","prop_contact","speech"}

class PremiumRigError(ValueError):
    pass

def require(value, msg):
    if not value:
        raise PremiumRigError(msg)

def validate_performance(spec:dict, storyboard:dict)->dict:
    require(isinstance(spec,dict) and spec.get("schema_version")==1,"Unknown spec version")
    require(spec.get("episode_id")==storyboard.get("episode_id"),"Episode mismatch")
    scenes=storyboard.get("shots",[])
    number=spec.get("scene_number")
    require(type(number) is int and 1<=number<=len(scenes),"Unknown scene")
    scene=scenes[number-1]
    require(scene["mode"]=="true_3d","Scene must be genuine 3D geometry")
    cast=spec.get("characters")
    require(isinstance(cast,list) and len(cast)>=2,"Multi-character acting required")
    ids={x.get("id") for x in cast}
    require(ids==set(scene["present"]),"Character list mismatches storyboard")
    for person in cast:
        require(set(person.get("required_joints",[]))>=JOINTS,"Missing armature joints")
        require(set(person.get("required_face_shapes",[]))>=FACE,"Missing facial/viseme controls")
        require(person.get("asset_status") in ("requested","in_progress","rights_cleared"),
                "Unverified asset state")
        require(person.get("performance_audio_status") in ("not_generated","unverified"),
                "Stage must not claim audio approval")
        require(isinstance(person.get("wardrobe_identity"),str)
                and len(person["wardrobe_identity"])>=15,"Distinct wardrobe identity required")
    timeline=spec.get("performance_timeline")
    require(isinstance(timeline,list) and len(timeline)>=5,"Acting timeline too sparse")
    duration=scene.get("duration_seconds") or (scene["end_ms"]-scene["start_ms"])/1000
    kinds={name:set() for name in ids}
    for action in timeline:
        require(isinstance(action,dict) and action.get("actor") in ids
                and action.get("type") in ACTIONS,"Unknown role or action")
        start,end=action.get("start_second"),action.get("end_second")
        require(type(start) in (int,float) and type(end) in (int,float)
                and 0<=start<end<=duration,"Action outside scene timeline")
        require(isinstance(action.get("directing_note"),str)
                and len(action["directing_note"])>=15,"Missing acting direction")
        if action["type"]=="prop_contact":
            require(isinstance(action.get("prop_id"),str)
                    and len(action["prop_id"])>=4
                    and action.get("contact_target") in ("left_hand","right_hand"),
                    "Object contact needs a real prop ID and hand")
        kinds[action["actor"]].add(action["type"])
    require(any("prop_contact" in x for x in kinds.values()),"Physical object interaction missing")
    require(all("gaze" in x or "expression" in x for x in kinds.values()),
            "Every character needs intentional acting")
    camera=spec.get("camera")
    require(isinstance(camera,dict) and camera.get("move") in ("dolly","arc","orbit","tracking")
            and isinstance(camera.get("visual_focus"),str) and len(camera["visual_focus"])>=15,
            "Camera must clearly teach an object")
    require(spec.get("rig_asset_qc") is False and spec.get("lip_sync_qc") is False
            and spec.get("artistic_review") is False,"This stage cannot approve itself")
    return {"status":"PERFORMANCE_SPEC_ONLY_NOT_RENDERED","characters":len(ids),
            "actions":len(timeline),"rig_controls_specified":True,
            "release_ready":False,"lip_sync_audio_present":False,"rigged_asset_verified":False}
