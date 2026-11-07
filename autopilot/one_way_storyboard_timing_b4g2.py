"""B4g2 duration-proportional one-way instructional storyboard highlights.

A scene makes 2 or 3 real instructional highlights in a FIXED direction,
never rotating back to the beginning and never replaying an animation loop.
No YouTube, user information, remote assets or publish status.
"""
from __future__ import annotations
import math


# Original 11 scene IDs and their unique educational visual grammar.
# Deliberately Pillow-independent so no-media, no-secrets CI can test the
# FFconcat timing source without installing the full renderer.
SOURCE_SCENE_GRAMMAR = {
    "HOOK_QUESTION":"compare",
    "SOURCE_SCOPE":"steps",
    "DEMONSTRATION":"matrix",
    "VERIFY_AND_LIMIT":"gate",
    "MECHANISM":"steps",
    "BASELINE":"compare",
    "EXAMPLE_1":"matrix",
    "EXAMPLE_2":"compare",
    "COUNTEREXAMPLE":"gate",
    "FACT_AND_RIGHTS_GATE":"gate",
    "NEXT_VIEWER_ACTION":"steps",
}


class OneWayStageRefused(ValueError):
    """Unverified scene duration, timeline or stage cycle."""


def stage_hold_seconds(actual_pcm_scene_seconds: float, stage_count: int,
                       reveal_seconds: float) -> tuple[float,...]:
    """Bounded FFconcat frame holds, derived from one original scene's PCM.

    Phase 0 is a brief orienting original still; later focus steps evenly
    advance across the scene. This is *not* per-word forced alignment.
    """
    if not (type(actual_pcm_scene_seconds) in (float,int)
            and math.isfinite(actual_pcm_scene_seconds)
            and 3 <= actual_pcm_scene_seconds <=55
            and type(stage_count) is int and stage_count in (3,4)
            and type(reveal_seconds) in (float,int)
            and math.isfinite(reveal_seconds)
            and .15 <= reveal_seconds <= .5):
        raise OneWayStageRefused("Invalid original video phase duration or count")
    rest=(actual_pcm_scene_seconds-reveal_seconds)/(stage_count-1)
    if rest<1.5:
        raise OneWayStageRefused("Too short for truthful one-way stage reveals")
    result=(float(reveal_seconds),)+(float(rest),)*(stage_count-2)+(
        float(actual_pcm_scene_seconds - reveal_seconds
              - rest*(stage_count-2)),)
    if (abs(sum(result)-actual_pcm_scene_seconds)>.0001
        or any(not math.isfinite(x) or x<.15 for x in result)):
        raise OneWayStageRefused("Unbounded scene stage timing")
    return result


def active_focus_sequence(visual_grammar: str) -> tuple[int|None,...]:
    """Empty initial diagram, then distinct checkpoints in visible order."""
    if visual_grammar in ("compare","gate"):
        return (None,0,1)
    if visual_grammar in ("matrix","steps"):
        return (None,0,1,2)
    raise OneWayStageRefused("No approved original diagram grammar")


def grammar_for_original_scene(scene_id: str) -> str:
    if type(scene_id) is not str or scene_id not in SOURCE_SCENE_GRAMMAR:
        raise OneWayStageRefused("Unknown original educational scene category")
    return SOURCE_SCENE_GRAMMAR[scene_id]
