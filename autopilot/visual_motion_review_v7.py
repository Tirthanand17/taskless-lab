"""B4e5 source-locked all-32-scene VISUAL MOTION review pack.

Makes three true 2-D visual contact sheets (6/20/6 source scenes) and derives
pixel-motion evidence from ticks 0, 60, 120 for every scene. No model, audio
claim, live topic, app service, Google OAuth or YouTube publishing is used.

This is not a psychological attention test or automatic ring/spinner detector:
a human must still watch all final videos and reject distracting patterns.
The dated NASA/NIST/USGS educational drafts are demos, NOT fresh daily content.
"""
from __future__ import annotations

from hashlib import sha256
import io
import json
from pathlib import Path
import textwrap
from typing import Mapping

from autopilot.primary_sourced_storyboards import (
    build_story, render_original_svg, require_exact_draft,
)
from autopilot.cinematic_scene_v3 import SCENE_PANEL
from autopilot.floating_cinematic_v6 import paint_floating_original_beat
from autopilot.cinematic_editorial_grid_v5 import apply_source_cinematic_editorial_grid

STATUS = "B4E5_32_PHYSICAL_SCENE_MOTION_CONTACT_SHEETS_UNAPPROVED"
SLOTS = ("short_am", "long", "short_pm")
COUNTS = {"short_am": 6, "long": 20, "short_pm": 6}
SCENE_DAY = "2026-11-12"
TICKS = (0, 60, 120)
REVIEW_QUESTIONS = (
    "Are the first two seconds visually legible and specific to this topic?",
    "Are any generic moving circles, rings, arcs or spinners distracting?",
    "Are graphics, narration and captions synchronized without collisions?",
    "Are scientific examples/source claims accurate and rights cleared?",
    "Did a human watch and listen to all final media before approval?",
)


class MotionReviewRefused(ValueError):
    """A broken physical media frame or forged review receipt cannot pass."""


def _checked_story(slot: str) -> dict:
    if slot not in COUNTS:
        raise MotionReviewRefused("Unknown editorial release slot")
    story = build_story(slot, SCENE_DAY)
    require_exact_draft(story)
    if story["scene_count"] != COUNTS[slot] or story["release_authorized"] is not False:
        raise MotionReviewRefused("Invalid original source story/review boundary")
    return story


def _frame(story: Mapping, scene_index: int, tick: int):
    """Actually draw the original native SVG + PIL overlay, not mock pixels."""
    from PIL import Image
    import cairosvg
    try:
        original = render_original_svg(story, scene_index, tick)
        raw = cairosvg.svg2png(bytestring=original.encode("utf-8"))
        with Image.open(io.BytesIO(raw)) as src:
            picture = src.convert("RGB")
        hero = paint_floating_original_beat(
            picture, story=story, scene_index=scene_index, tick=tick,
        )
        grid = apply_source_cinematic_editorial_grid(
            picture, story=story, scene_index=scene_index,
        )
    except Exception:
        raise MotionReviewRefused("Source-locked physical art frame failed") from None
    if (hero.get("release_authorized") is not False
        or grid.get("release_authorized") is not False
        or hero.get("old_bordered_presentation_panel_removed") is not True
        or hero.get("reference_clip_media_reused") is not False
        or hero.get("source_story_draft_sha256") != story["draft_sha256"]):
        raise MotionReviewRefused("Source art / approval boundary forged")
    return picture, hero


def _hero_sha(picture, rect: tuple[int, int, int, int]) -> str:
    return sha256(picture.crop(rect).tobytes()).hexdigest()


def changed_motion_fraction(a, b, rect) -> float:
    """Measured hero pixel change, not a judgment about viewer engagement."""
    from PIL import ImageChops, Image
    if a.mode != "RGB" or b.mode != "RGB" or a.size != b.size:
        raise MotionReviewRefused("Unmatched source frame geometry")
    x0, y0, x1, y1 = rect
    if not (0 <= x0 < x1 <= a.width and 0 <= y0 < y1 <= a.height):
        raise MotionReviewRefused("Invalid source hero rectangle")
    native_a = a.crop(rect).resize((160, 112), Image.Resampling.BILINEAR)
    native_b = b.crop(rect).resize((160, 112), Image.Resampling.BILINEAR)
    changed = ImageChops.difference(native_a, native_b).convert("L")
    n = sum(pixel >= 3 for pixel in changed.getdata())
    return round(n / (160 * 112), 5)


def _font(size: int):
    from PIL import ImageFont
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _contact_sheet(story: dict, samples: list, destination: Path) -> dict:
    """Dense, readable visual inventory with all source-locked scene labels."""
    from PIL import Image, ImageDraw
    is_short = story["format"] == "short"
    target = (276, 490) if is_short else (452, 254)
    columns = 3 if is_short else 4
    rows = (len(samples) + columns - 1) // columns
    pad, label_h, top_h = 18, 92, 86
    W = pad + columns * (target[0] + pad)
    H = top_h + rows * (target[1] + label_h + pad) + pad
    if W * H > 12_000_000:
        raise MotionReviewRefused("Unbounded editorial contact-sheet size")
    sheet = Image.new("RGB", (W, H), (8, 18, 32))
    draw = ImageDraw.Draw(sheet)
    accent = (104, 224, 194)
    title = f"FLOWMINUTE  /  {story['slot'].replace('_', ' ').upper()}  /  SOURCE REVIEW"
    draw.text((pad, 16), title, font=_font(19), fill=(240, 247, 251))
    draw.text((pad, 48), "32-SCENE DEMO  |  UNAPPROVED / NOT DAILY FRESH / NO UPLOAD",
              font=_font(11), fill=accent)
    for idx, (scene, picture) in enumerate(zip(story["scenes"], samples, strict=True)):
        col, row = idx % columns, idx // columns
        x = pad + col * (target[0] + pad)
        y = top_h + row * (target[1] + label_h + pad)
        preview = picture.resize(target, Image.Resampling.LANCZOS)
        sheet.paste(preview, (x, y))
        draw.rectangle((x, y + target[1], x + target[0], y + target[1] + label_h),
                       fill=(16, 35, 55))
        label = f"{idx+1:02d}  {scene['display_title']}"
        for n, line in enumerate(textwrap.wrap(label, width=32)[:2]):
            draw.text((x + 7, y + target[1] + 5 + 19*n),
                      line, font=_font(12), fill=(233, 239, 244))
        metric = textwrap.shorten(str(scene["display_value"]), width=34, placeholder="...")
        draw.text((x + 7, y + target[1] + 56), metric,
                  font=_font(11), fill=accent)
    sheet.save(destination, format="PNG", optimize=True)
    total = destination.stat().st_size
    if not 20_000 < total < 18_000_000:
        raise MotionReviewRefused("Review contact-sheet image missing/invalid size")
    return {
        "filename": destination.name,
        "sha256": sha256(destination.read_bytes()).hexdigest(),
        "bytes": total,
        "scene_count": len(samples),
        "all_scene_tiles_are_physically_rendered": True,
        "human_visual_approval": False,
    }


def review_all_32_original_scenes(destination: Path) -> dict:
    """Generate review data only, leaving dated original scripts unchanged."""
    destination = Path(destination)
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():
        raise MotionReviewRefused("A new absolute unapproved review directory is required")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(mode=0o700)
    manifests = []
    scene_total = 0
    try:
        for slot in SLOTS:
            story = _checked_story(slot)
            area = SCENE_PANEL[story["format"]]
            thumbnails = []
            scene_records = []
            for idx, scene in enumerate(story["scenes"]):
                images = []
                for tick in TICKS:
                    picture, evidence = _frame(story, idx, tick)
                    if evidence["scene_id"] != scene["scene_id"]:
                        raise MotionReviewRefused("Source scene id changed")
                    images.append(picture)
                hashes = [_hero_sha(image, area) for image in images]
                if len(set(hashes)) != 3:
                    raise MotionReviewRefused("Source scene frozen across 3 sample ticks")
                change_before = changed_motion_fraction(images[0], images[1], area)
                change_after = changed_motion_fraction(images[1], images[2], area)
                if change_before <= 0 or change_after <= 0:
                    raise MotionReviewRefused("No measured source scene motion")
                scene_records.append({
                    "scene_id": scene["scene_id"],
                    "source_metric_sha256": sha256(
                        scene["display_value"].encode("utf-8")).hexdigest(),
                    "3_samples": list(TICKS),
                    "distinct_full_native_hero_frames": 3,
                    "changed_hero_pixel_fraction_first_half": change_before,
                    "changed_hero_pixel_fraction_second_half": change_after,
                    "rendered_scene_source_sha256": story["draft_sha256"],
                    "visual_spinner_absence_human_confirmed": False,
                    "factual_claims_human_verified": False,
                    "release_authorized": False,
                })
                thumbnails.append(images[1])
            if len({s["scene_id"] for s in scene_records}) != COUNTS[slot]:
                raise MotionReviewRefused("Repeated scene identity in review pack")
            if len({
                _hero_sha(pic, area) for pic in thumbnails
            }) != COUNTS[slot]:
                raise MotionReviewRefused("Repeated visually identical center-tick hero scene")
            art = _contact_sheet(story, thumbnails,
                                 destination/f"{slot.upper()}_ALL_BEATS_UNAPPROVED.png")
            manifests.append({
                "slot": slot,
                "episode_id": story["episode_id"],
                "theme": story["theme"],
                "format": story["format"],
                "source_day_ist": SCENE_DAY,
                "source_draft_sha256": story["draft_sha256"],
                "scenes": scene_records,
                "contact_sheet": art,
                "actual_all_source_scene_ticks_rendered": True,
                "actual_encoded_mp4_playback_reviewed": False,
                "fresh_daily_research": False,
                "human_final_review_complete": False,
                "release_authorized": False,
            })
            scene_total += len(scene_records)
        if scene_total != 32 or [x["slot"] for x in manifests] != list(SLOTS):
            raise MotionReviewRefused("Incomplete 2 Shorts + 1 long visual review")
        report = {
            "status": STATUS,
            "schema_version": 1,
            "review_scope": "EXISTING_NASA_NIST_USGS_DEMO_SCENES_ONLY",
            "source_day_ist": SCENE_DAY,
            "shots_checked": scene_total,
            "source_motion_frames_physically_rendered": 3*scene_total,
            "episode_order": list(SLOTS),
            "episodes": manifests,
            "human_review_questions": list(REVIEW_QUESTIONS),
            "automated_spinner_free_certification": False,
            "human_creative_approval": False,
            "human_claim_rights_and_listen_review": False,
            "video_encoded_in_this_workflow": False,
            "daily_fresh_content_produced": False,
            "real_youtube_uploads": 0,
            "release_authorized": False,
        }
        (destination/"UNAPPROVED_32_SCENE_MOTION_REPORT.json").write_text(
            json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8",
        )
        return report
    except Exception:
        # A partial review folder is not fit for retention/promotion.
        import shutil
        shutil.rmtree(destination, ignore_errors=True)
        raise


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Original 32-scene visual QA; NO PUBLISH")
    p.add_argument("--out", type=Path, required=True)
    x = p.parse_args()
    report = review_all_32_original_scenes(x.out)
    print(json.dumps({
        "status": report["status"],
        "shots_checked": report["shots_checked"],
        "rendered_frames": report["source_motion_frames_physically_rendered"],
        "contact_sheets": len(report["episodes"]),
        "daily_fresh": False,
        "youtube_uploads": 0,
        "release_authorized": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
