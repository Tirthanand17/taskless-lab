"""FlowMinute educational 3D story contract, staging only.

Structural checks do not prove factual accuracy, rights ownership, human-sounding
narration, rendered geometry, or YouTube publishing. Zero network calls.
"""
from __future__ import annotations
from urllib.parse import urlsplit

STORY_BEATS = ("problem", "analogy", "demonstration", "verification", "takeaway")
MODES = {"true_3d", "real_screen_capture", "illustrative_ui", "motion_2d"}
CAMERAS = {"wide", "medium", "closeup", "over_shoulder", "orbit", "dolly"}
ROLES = {"explainer", "learner", "expert", "demonstrator"}
GATES = ("fact_review", "source_rights", "character_asset_review",
         "voice_license", "pronunciation_review", "subtitle_alignment",
         "render_decode", "scene_motion_review", "release_receipt")


class Story3DError(ValueError):
    pass


def _require(condition, reason):
    if not condition:
        raise Story3DError(reason)


def _bounded(text, minimum=4, maximum=800):
    return isinstance(text, str) and minimum <= len(text.strip()) <= maximum


def _source_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        parts = urlsplit(value)
        return (parts.scheme == "https" and parts.hostname is not None
                and "." in parts.hostname and parts.username is None
                and parts.password is None and parts.port in (None, 443)
                and parts.hostname not in ("localhost", "127.0.0.1"))
    except ValueError:
        return False


def validate_3d_lesson(doc: dict) -> dict:
    """Validate teaching and 3D-animation intent; return honest stage status.

    This validates a *proposed* scene graph, not animated video files.
    """
    _require(isinstance(doc, dict) and doc.get("schema_version") == 1,
             "Unknown lesson schema")
    _require(doc.get("format") in ("short", "long"), "Invalid format")
    _require(doc.get("language") in ("en", "hi"), "Invalid language")
    _require(doc.get("lesson_type") in ("concept", "practical_tutorial"),
             "Unknown lesson type")
    _require(_bounded(doc.get("episode_id"), 8, 100), "Missing episode ID")
    _require(_bounded(doc.get("title"), 10, 120), "Missing lesson title")
    _require(_bounded(doc.get("viewer_question"), 15, 250),
             "Explain the problem the viewer has")
    _require(_bounded(doc.get("learning_outcome"), 20, 280),
             "Give a concrete learning outcome")
    _require(_bounded(doc.get("repeatable_takeaway"), 20, 320),
             "Viewer needs a repeatable takeaway")
    links = doc.get("source_urls")
    _require(isinstance(links, list) and 1 <= len(links) <= 12
             and all(_source_url(x) for x in links), "Source URLs required")

    cast = doc.get("characters")
    _require(isinstance(cast, list) and 2 <= len(cast) <= 6,
             "Multiple original/cleared 3D characters required")
    ids = set()
    roles = set()
    for actor in cast:
        _require(isinstance(actor, dict), "Bad character")
        name = actor.get("id")
        _require(_bounded(name, 2, 40) and name not in ids, "Duplicate/invalid character")
        ids.add(name)
        _require(actor.get("role") in ROLES, "Unknown teaching role")
        roles.add(actor["role"])
        _require(_bounded(actor.get("visual_identity"), 12, 200),
                 "Character identity/continuity required")
        _require(actor.get("rights_state") in ("original_planned", "cleared"),
                 "Character usage rights undefined")
        _require(_bounded(actor.get("voice_style"), 8, 160), "Voice direction missing")
    _require("explainer" in roles and "learner" in roles,
             "Explain concepts through instructor and learner interaction")

    shots = doc.get("shots")
    _require(isinstance(shots, list) and 5 <= len(shots) <= 45, "Invalid shot count")
    previous_idx = -1
    total = 0
    true3d = 0
    screen = 0
    with_dialogue = set()
    shared_3d_shot = False
    object_interactions = 0
    for number, shot in enumerate(shots, start=1):
        _require(isinstance(shot, dict), "Invalid shot")
        _require(shot.get("number") == number, "Shot numbers must be sequential")
        beat = shot.get("beat")
        _require(beat in STORY_BEATS, "Unknown teaching beat")
        idx = STORY_BEATS.index(beat)
        _require(idx >= previous_idx, "Teaching beats must appear in order")
        previous_idx = idx
        duration = shot.get("duration_seconds")
        _require(type(duration) in (int, float) and 2 <= duration <= 65,
                 "Invalid shot duration")
        total += duration
        mode = shot.get("mode")
        _require(mode in MODES, "Unknown scene mode")
        _require(shot.get("camera") in CAMERAS, "Use a defined camera composition")
        _require(_bounded(shot.get("location"), 12, 180), "Physical scene location missing")
        _require(_bounded(shot.get("visual_explanation"), 25, 500),
                 "Show how visual elements teach the concept")
        _require(_bounded(shot.get("learner_payoff"), 12, 280),
                 "Every shot needs one clear viewer-facing point")
        present = shot.get("present")
        _require(isinstance(present, list) and len(present) > 0
                 and len(present) == len(set(present))
                 and set(present) <= ids, "Unknown character in scene")
        dialogue = shot.get("dialogue")
        _require(isinstance(dialogue, list) and dialogue, "Narration/dialogue missing")
        for line in dialogue:
            _require(isinstance(line, dict) and line.get("speaker") in present
                     and _bounded(line.get("text"), 7, 450), "Dialogue speaker/text invalid")
            with_dialogue.add(line["speaker"])
        if mode == "true_3d":
            true3d += 1
            _require(shot.get("camera_motion") in ("orbit", "dolly", "pan", "tracking"),
                     "Real 3D shot needs animatable camera movement")
            actions = shot.get("object_interactions")
            _require(isinstance(actions, list) and actions, "3D scene needs object interaction")
            for action in actions:
                _require(isinstance(action, dict)
                         and action.get("actor") in present
                         and _bounded(action.get("object"), 3, 80)
                         and _bounded(action.get("action"), 10, 170),
                         "3D action must bind a character to a real scene object")
                object_interactions += 1
            if len(present) >= 2:
                shared_3d_shot = True
        if mode == "real_screen_capture":
            screen += 1
            _require(_bounded(shot.get("capture_evidence"), 16, 250),
                     "Real UI requires a verifiable capture reference")
        if mode == "illustrative_ui":
            _require(shot.get("simulation_label_visible") is True,
                     "Simulated UI must be explicitly labeled")
    _require(set(STORY_BEATS) <= {s["beat"] for s in shots},
             "Use all five teaching beats: problem, analogy, demo, verify, takeaway")
    _require(2 <= true3d and true3d / len(shots) >= 0.4,
             "This multi-character episode needs substantial real 3D scenes")
    _require(shared_3d_shot and len(with_dialogue) >= 2 and object_interactions >= 2,
             "A slideshow or solo static presenter is not a multi-character 3D story")
    _require(doc["lesson_type"] != "practical_tutorial" or screen >= 1,
             "Practical tutorials require genuine software demonstration")
    _require((20 <= total <= 180) if doc["format"] == "short"
             else (180 <= total <= 3600), "Duration outside planned format")

    gates = doc.get("qa_gates")
    _require(isinstance(gates, dict) and set(gates) == set(GATES)
             and all(type(v) is bool for v in gates.values()),
             "All nine review gates must be explicit booleans")
    # A completed release receipt is not inferred from this structural validator.
    _require(gates["release_receipt"] is False,
             "Release receipt cannot be attested by storyboard input")
    return {
        "episode_id": doc["episode_id"],
        "stage": "STORYBOARD_ONLY_NOT_RENDERED",
        "duration_seconds": total,
        "shot_count": len(shots),
        "animated_3d_shots": true3d,
        "three_d_ratio": round(true3d / len(shots), 2),
        "real_software_captures": screen,
        "characters": len(cast),
        "character_object_interactions": object_interactions,
        "required_qa_pending": [name for name, passed in gates.items() if not passed],
        "upload_authorized_by_validator": False,
        "publish_ready": False,
    }
