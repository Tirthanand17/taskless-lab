"""B3d4c1: executed, original, data-backed educational visuals (NO PUBLISH).

Three explicitly selected demo algorithms on an invented four-row CSV fixture:
1. preserving identifier text, 2. an explicit ISO date format contract,
3. flagging ambiguous duplicate identifiers without deleting records.

The narrative topic/recipe match is only a LEXICAL PROTECTION, NOT editorial
semantic verification. The original code output is a synthetic worked example,
never an actual customer dataset, verified external claim, licence or release
approval. No arbitrary model-generated Python/code, network, upload or keys.
"""
from __future__ import annotations

import csv
from datetime import date
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import re
import textwrap
from typing import Any

from autopilot.full_pack_fixture import CSV_SAMPLE, EXPECTED_COLUMNS

STATUS = "EXECUTED_SYNTHETIC_DEMO_VISUALS_UNREVIEWED_NO_PUBLISH"
RECIPES = {
    "preserve_text_identifiers": {
        "title_phrase": "identifier strings",
        "walkthrough_phrase": "five-digit member identifier",
        "narration_phrase": "identifier",
        "name": "KEEP IDENTIFIER ZEROS",
        "theme": "String identity is not numeric value",
    },
    "validate_iso_dates": {
        "title_phrase": "iso date validation",
        "walkthrough_phrase": "calendar values",
        "narration_phrase": "date",
        "name": "CHECK DATE CONTRACTS",
        "theme": "Reject ambiguity without rewriting source",
    },
    "review_duplicate_keys": {
        "title_phrase": "duplicate conflict checks",
        "walkthrough_phrase": "conflicting synthetic member records",
        "narration_phrase": "duplicate",
        "name": "REVIEW CONFLICTING KEYS",
        "theme": "Keep both records until the rule is known",
    },
}
MAX_STEPS = 5


class ExecutedDemoError(ValueError):
    """Fail closed on unexpected algorithm or a substituted visual claim."""


def canonical(obj: object) -> bytes:
    try:
        text = json.dumps(obj, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ExecutedDemoError("Invalid executed demonstration record") from exc
    if len(text) > 50_000:
        raise ExecutedDemoError("Unbounded demonstration provenance")
    return text


def _synthetic_rows() -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(CSV_SAMPLE))
    if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
        raise ExecutedDemoError("Synthetic demo schema changed")
    rows = list(reader)
    if len(rows) != 4 or any(
        set(row) != set(EXPECTED_COLUMNS)
        or any(not isinstance(v, str) or not v for v in row.values())
        for row in rows
    ):
        raise ExecutedDemoError("Synthetic record schema drift")
    return rows


def _step(label: str, before_title: str, before: str,
          after_title: str, after: str, takeaway: str) -> dict[str, str]:
    item = {
        "label": label, "before_title": before_title, "before": before,
        "after_title": after_title, "after": after, "takeaway": takeaway,
    }
    if any(not isinstance(v, str) or not 2 <= len(v) <= 150 for v in item.values()):
        raise ExecutedDemoError("An original visual step was malformed")
    return item


def _computed_steps(recipe: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows = _synthetic_rows()
    if recipe == "preserve_text_identifiers":
        raw = rows[0]["member_id"]
        converted = str(int(raw))
        if raw != "00127" or converted != "127":
            raise ExecutedDemoError("Unreviewed identifier output changed")
        return [
            _step("INSPECT SOURCE ROW", "CSV row 1 key", repr(raw),
                  "CSV reader type", "str", "Keep the five characters"),
            _step("MEASURE ORIGINAL", "Original key", repr(raw),
                  "Character count", str(len(raw)), "Labels are not quantities"),
            _step("EXECUTE int()", "Source key", repr(raw),
                  "Integer conversion", converted, "Leading zeros disappear"),
            _step("KEEP TEXT ID", "Original", repr(raw),
                  "Converted text", repr(converted), "Do not silently rewrite keys"),
        ], {
            "identifier_string": raw, "identifier_length": len(raw),
            "integer_conversion": int(raw), "converted_string": converted,
            "leading_zeroes_lost": len(raw) - len(converted),
            "source_rows_preserved": len(rows),
        }
    if recipe == "validate_iso_dates":
        valid, invalid = [], []
        for i, row in enumerate(rows, 1):
            raw_date = row["joined_on"]
            try:
                parsed = date.fromisoformat(raw_date)
            except ValueError:
                invalid.append({"row": i, "raw": raw_date})
            else:
                valid.append({"row": i, "canonical_date": parsed.isoformat()})
        if len(valid) != 3 or invalid != [{"row": 4, "raw": "11/04/26"}]:
            raise ExecutedDemoError("Synthetic ISO report not reproducible")
        return [
            _step("DEFINE CONTRACT", "Accepted", "YYYY-MM-DD",
                  "Input row 1", rows[0]["joined_on"], "Use an explicit date format"),
            _step("EXECUTE PARSER", "Row 2 input", rows[1]["joined_on"],
                  "date.fromisoformat", valid[1]["canonical_date"], "Validated without changes"),
            _step("REJECT NON-ISO", "Row 4 raw", invalid[0]["raw"],
                  "Parser result", "REJECT / RETAIN", "Never guess day/month order"),
            _step("REPORT EXCEPTIONS", "Valid rows", str(len(valid)),
                  "Review rows", str(len(invalid)), "Leave original dataset intact"),
        ], {
            "valid_date_rows": valid, "invalid_date_rows": invalid,
            "source_rows_preserved": len(rows),
            "ambiguous_date_automatically_fixed": False,
        }
    if recipe == "review_duplicate_keys":
        seen: dict[str, int] = {}
        conflicts = []
        for index, row in enumerate(rows, 1):
            key = row["member_id"]
            if key in seen:
                first = rows[seen[key] - 1]
                conflicts.append({
                    "member_id": key, "first_row": seen[key],
                    "repeat_row": index,
                    "joining_dates_differ": first["joined_on"] != row["joined_on"],
                    "statuses_differ": first["status"] != row["status"],
                })
            else:
                seen[key] = index
        if conflicts != [{
            "member_id": "00127", "first_row": 1, "repeat_row": 3,
            "joining_dates_differ": True, "statuses_differ": False,
        }]:
            raise ExecutedDemoError("Synthetic duplicate conflict report changed")
        return [
            _step("SCAN ALL FOUR ROWS", "Number of rows", str(len(rows)),
                  "Distinct keys", str(len(seen)), "Do not remove source records"),
            _step("DETECT REPEATED KEY", "First row", "Row 1 : '00127'",
                  "Repeated row", "Row 3 : '00127'", "Same identifier, two records"),
            _step("COMPARE DATES", "Row 1 joined", rows[0]["joined_on"],
                  "Row 3 joined", rows[2]["joined_on"], "Dates differ; needs review"),
            _step("CREATE REVIEW FLAG", "Conflicts found", str(len(conflicts)),
                  "Rows deleted", "0", "Retain both until reviewed"),
        ], {
            "duplicate_conflicts": conflicts,
            "distinct_identifier_count": len(seen),
            "source_rows_preserved": len(rows),
            "rows_deleted": 0,
        }
    raise ExecutedDemoError("Unknown computation recipe; no arbitrary code may run")


def build_executed_demo(plan: dict, proposal: dict, recipe: str) -> dict:
    """Run a known algorithm only for an exact supported signed script topic.

    Caller MUST first authenticate the independent B3d1 external script
    anchor and B3d4b full-source-bound canonical plan at the producer edge.
    """
    from autopilot.signed_narrated_cloud_pack import validate_plan
    validate_plan(plan)
    if (not isinstance(recipe, str) or recipe not in RECIPES
            or not isinstance(proposal, dict)
            or proposal.get("title") != plan.get("title_unverified")
            or not isinstance(proposal.get("example_walkthrough"), str)
            or not isinstance(proposal.get("narration"), str)):
        raise ExecutedDemoError("Unsupported explicit original teaching example")
    spec = RECIPES[recipe]
    if (spec["title_phrase"] not in proposal["title"].casefold()
            or spec["walkthrough_phrase"] not in proposal["example_walkthrough"].casefold()
            or spec["narration_phrase"] not in proposal["narration"].casefold()):
        raise ExecutedDemoError("Unsigned/improperly matched demo topic and script")
    steps, outcome = _computed_steps(recipe)
    if not 3 <= len(steps) <= MAX_STEPS:
        raise ExecutedDemoError("A recipe has no auditable original visual sequence")
    immutable = {
        "schema_version": 1,
        "status": STATUS,
        "episode_id": plan["episode_id"],
        "script_manifest_sha256": plan["script_manifest_sha256"],
        "full_spoken_narration_sha256": plan["full_spoken_narration_sha256"],
        "recipe_id": recipe,
        "topic": spec["name"],
        "viewer_benefit_draft": plan["viewer_benefit_unverified"],
        "input_is_invented": True,
        "example_csv_sha256": sha256(CSV_SAMPLE.encode("utf-8")).hexdigest(),
        "algorithm": "stdlib_python_csv_and_date_v1",
        "executed_steps": steps,
        "computed_outcome": outcome,
        "computation_reproduced_from_fixed_test_fixture": True,
        "independent_reviewer_checked_semantic_fit": False,
        "source_article_fact_checked": False,
        "rights_and_voice_license_approved": False,
        "thumbnail_editorial_review_complete": False,
        "generative_model_created_script": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
    }
    return {**immutable, "evidence_packet_sha256": sha256(canonical(immutable)).hexdigest()}


def require_exact_demo(plan: dict, proposal: dict, recipe: str, packet: dict) -> None:
    """Never accept an editable copy of the computed text as evidence."""
    verified = build_executed_demo(plan, proposal, recipe)
    if not isinstance(packet, dict) or canonical(packet) != canonical(verified):
        raise ExecutedDemoError("Executed synthetic result differs from recomputed proof")


def _draw_text_lines(draw, x: int, y: int, text: str, font, *,
                     color: tuple[int, int, int], width: int,
                     max_lines: int = 3, spacing: int = 46) -> None:
    if not isinstance(text, str) or len(text) > 450:
        raise ExecutedDemoError("Unbounded original text")
    for idx, line in enumerate(textwrap.wrap(text, width=width,
                                            break_long_words=False)[:max_lines]):
        draw.text((x, y+idx*spacing), line, font=font, fill=color)


def render_demo_frame(plan: dict, packet: dict, scene_index: int, output: Path) -> str:
    """Draw actual outcomes as ORIGINAL static storyboard with moving FFmpeg progress.

    Scene-specific steps rotate, but a human must STILL confirm they match the
    exact intended narrated claims. Does not simulate any real external UI.
    """
    from PIL import Image, ImageDraw
    from autopilot.script_to_preview_bridge import _font, _safe_text
    if (not isinstance(plan, dict) or not isinstance(packet, dict)
            or packet.get("status") != STATUS
            or packet.get("episode_id") != plan.get("episode_id")
            or packet.get("script_manifest_sha256") != plan.get("script_manifest_sha256")
            or type(scene_index) is not int
            or not 0 <= scene_index < plan.get("scene_count", -1)):
        raise ExecutedDemoError("Unknown scene or substituted demonstration evidence")
    steps = packet["executed_steps"]
    if not isinstance(steps, list) or not 3 <= len(steps) <= MAX_STEPS:
        raise ExecutedDemoError("Missing execution trace")
    current = steps[scene_index % len(steps)]
    portrait = plan["format"] == "short"
    width, height = (1080,1920) if portrait else (1920,1080)
    im = Image.new("RGB", (width,height), (12,26,43))
    draw = ImageDraw.Draw(im)
    fhead, fbody, fsmall = _font(58 if portrait else 69), _font(38), _font(26)
    colors = ((25,131,163),(143,85,167),(80,158,113),(190,128,53))
    accent = colors[scene_index % len(colors)]
    for y in range(0,height,100):
        draw.line((0,y,width,y), fill=(23,47,64), width=2)
    draw.rounded_rectangle((45,43,width-45,height-43),radius=32,
                           outline=(76,111,134),width=3)
    draw.text((73,80), "FLOWMINUTE  /  EXECUTED SYNTHETIC DEMO",
              font=fsmall,fill=(157,217,236))
    draw.text((73,134), "SCENE %02d / %02d" % (scene_index+1,plan["scene_count"]),
              font=fsmall,fill=(236,245,255))
    _draw_text_lines(draw,73,214,packet["topic"],fhead,color=(249,252,255),
                     width=24 if portrait else 40,max_lines=2,spacing=76)
    ybar = 485 if portrait else 365
    draw.rounded_rectangle((76,ybar,width-76,ybar+26),radius=12,fill=accent)
    label_y = 562 if portrait else 425
    _draw_text_lines(draw,82,label_y,current["label"],fbody,
                     color=(255,230,160),width=39,max_lines=2)
    box_a = (80,700,width-80,920) if portrait else (80,535,930,735)
    box_b = (80,970,width-80,1190) if portrait else (980,535,width-80,735)
    for rect, label, value in (
        (box_a,current["before_title"],current["before"]),
        (box_b,current["after_title"],current["after"]),
    ):
        draw.rounded_rectangle(rect,radius=21,fill=(30,58,83),
                               outline=accent,width=4)
        x1,y1,x2,y2=rect
        _draw_text_lines(draw,x1+30,y1+28,label,fsmall,color=(159,223,236),width=35)
        _draw_text_lines(draw,x1+29,y1+103,value,fbody,
                         color=(253,252,234),width=25,max_lines=2)
    summary_y = 1280 if portrait else 765
    _draw_text_lines(draw,83,summary_y,current["takeaway"],fbody,
                     color=(230,240,246),width=36 if portrait else 80,max_lines=2)
    # Subtitle safe area preserved for the existing B3b FFmpeg libass filter.
    safe_y = height-(326 if portrait else 205)
    draw.rounded_rectangle((83,safe_y,width-83,height-90),
                           radius=17,fill=(15,36,57))
    draw.text((103,safe_y+21),"REAL CODE OUTPUT  /  SYNTHETIC DATA",
              font=fsmall,fill=(164,223,247))
    draw.text((103,height-132),
              "UNREVIEWED  /  NO LICENSE OR SOURCE APPROVAL",
              font=fsmall,fill=(255,180,141))
    output=Path(output)
    if output.suffix.lower() != ".png" or output.is_symlink():
        raise ExecutedDemoError("Unexpected original-frame output path")
    im.save(output,format="PNG",optimize=True)
    if not 5000 < output.stat().st_size < 18_000_000:
        raise ExecutedDemoError("Source computation storyboard was not encoded")
    return sha256(output.read_bytes()).hexdigest()


def render_demo_thumbnail(plan: dict, packet: dict, output: Path) -> str:
    """Create an ORIGINAL, unapproved thumbnail; not a clickbait factual claim."""
    from PIL import Image, ImageDraw
    from autopilot.script_to_preview_bridge import _font
    if (packet.get("status") != STATUS
            or packet.get("script_manifest_sha256") != plan.get("script_manifest_sha256")
            or plan.get("release_authorized") is not False
            or packet.get("thumbnail_editorial_review_complete") is not False):
        raise ExecutedDemoError("Unreviewed demo thumbnail cannot assert clearance")
    image = Image.new("RGB",(1280,720),(12,28,48))
    d = ImageDraw.Draw(image)
    title, smaller = _font(72),_font(35)
    d.rounded_rectangle((38,42,1240,678),radius=42,
                        fill=(25,56,80),outline=(94,156,188),width=5)
    d.text((83,100),"FLOWMINUTE  |  EXECUTED DEMO",
           font=smaller,fill=(169,231,255))
    _draw_text_lines(d,86,228,packet["topic"],title,color=(250,253,254),
                     width=24,max_lines=2,spacing=95)
    d.rounded_rectangle((90,520,1190,608),radius=15,fill=(49,115,117))
    d.text((115,539),"INVENTED DATA  /  ORIGINAL CODE OUTPUT",
           font=smaller,fill=(251,246,219))
    d.text((87,639),"UNREVIEWED THUMBNAIL  |  NO UPLOAD",
           font=smaller,fill=(255,191,158))
    output=Path(output)
    if output.suffix.lower()!=".png" or output.is_symlink():
        raise ExecutedDemoError("Unexpected thumbnail output path")
    image.save(output,format="PNG",optimize=True)
    if not 5000 < output.stat().st_size < 18_000_000:
        raise ExecutedDemoError("Original thumbnail not encoded")
    return sha256(output.read_bytes()).hexdigest()
