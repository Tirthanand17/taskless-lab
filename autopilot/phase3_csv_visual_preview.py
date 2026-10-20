"""Phase 3: original CSV Short VISUAL-ONLY MP4 renderer (no voice or publication).

Uses Pillow + FFmpeg installed on a disposable Linux runner. Authored English
text is loaded from the fixed script file and drawn as a visual subtitle
mockup; there is NO audio/speech synchronization, rights attestation,
customer data, cloud provider access, YouTube upload or scheduling.

This intentionally refuses to call itself a release-ready video.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont
from .phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv
from .examples.flowminute_csv_demo import (
    COLUMNS as DEMO_COLUMNS, ROWS as DEMO_ROWS, demonstrate_csv_total,
)

SCRIPT = (Path(__file__).parent / "research_briefs" /
          "2026-10-17_csv_bilingual_one_day_scripts_DRAFT.md")
SCENES = (
    (0, 10, "CSV: FROM ROWS TO MEANING", "PRODUCT  |  UNITS  |  PRICE"),
    (10, 20, "FICTIONAL SAMPLE DATA", "THREE PRODUCTS, EXAMPLE PRICES"),
    (20, 30, "PYTHON DICTREADER", "READ COLUMNS BY NAME"),
    (30, 42, "EXAMPLE TOTAL", "20 + 30 + 8"),
)


def _illustrative_csv_data() -> tuple[tuple[str, str, str, int], ...]:
    """Return verified example products and their real executable row totals.

    Never read personal data; fail closed if the displayed example could
    misrepresent the original spoken fictitious 58-unit lesson.
    """
    computed = demonstrate_csv_total()
    if (tuple(DEMO_COLUMNS) != ("product", "units", "price")
            or computed.get("dataset_is_fictional") is not True
            or computed.get("purchased_anything") is not False
            or computed.get("youtube_uploaded") is not False
            or computed.get("publishing_authorized") is not False
            or computed.get("total") != 58
            or len(DEMO_ROWS) != 3
            or len(computed["rows"]) != len(DEMO_ROWS)):
        raise ValueError("English visual example no longer matches fictional CSV lesson")
    result = []
    for row, assessed in zip(DEMO_ROWS, computed["rows"]):
        if (set(row) != set(DEMO_COLUMNS)
                or assessed["product"] != row["product"]
                or row["product"] not in ("Pen", "Notebook", "Eraser")
                or assessed["line_total"] != int(row["units"]) * int(row["price"])):
            raise ValueError("English CSV graphic products or totals are inconsistent")
        result.append((
            row["product"], row["units"], row["price"], assessed["line_total"]
        ))
    if tuple(x[3] for x in result) != (20, 30, 8):
        raise ValueError("English Short must match original arithmetic demonstration")
    return tuple(result)

FONTS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
)
BOLD = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/lato/Lato-Heavy.ttf",
)


def _font(size: int, *, bold: bool = False):
    for path in (BOLD if bold else FONTS):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    raise RuntimeError("Required system-installed font not found; no download permitted")


def english_script_rows() -> tuple[str, ...]:
    if not SCRIPT.is_file() or SCRIPT.stat().st_size > 75_000:
        raise ValueError("Bounded authored CSV script required")
    source = SCRIPT.read_text(encoding="utf-8")
    a, b = source.index("## SHORT 2"), source.index("## LONG VIDEO")
    rows = re.findall(
        r"^\| \d\d:\d\d–\d\d:\d\d \| (.+?) \| (.+?) \|$",
        source[a:b], flags=re.MULTILINE,
    )
    if len(rows) != 4:
        raise ValueError("Authored English Short must have four timed rows")
    return tuple(text.strip() for text, _ in rows)


@lru_cache(maxsize=1)
def _english_srt_timing() -> tuple[tuple[int,int,str], ...]:
    """Actual authored English SRT; estimated scene timing, never speech ASR."""
    srt=build_subtitles_from_authored_csv()["csv_tutorial_short_en"]["srt"]
    blocks=srt.strip().split("\n\n")
    records=[]
    for block in blocks:
        lines=block.splitlines()
        if len(lines)!=3 or not lines[0].isdigit() or " --> " not in lines[1]:
            raise ValueError("Malformed internally generated SRT")
        start,end=lines[1].split(" --> ")
        def stamp(value: str) -> int:
            hours,minute,second=value.split(":")
            sec,milli=second.split(",")
            return ((int(hours)*3600+int(minute)*60+int(sec))*1000+int(milli))
        records.append((stamp(start),stamp(end),lines[2]))
    if not records or records[0][0]!=0 or records[-1][1]!=42000:
        raise ValueError("Incorrect authored English Short SRT duration")
    return tuple(records)


def _estimated_caption_at(time_s: float) -> str:
    """Return one readable estimated caption, not an audio-aligned word cue."""
    millis=round(time_s*1000)
    for start,end,spoken in _english_srt_timing():
        if start <= millis < end:
            return spoken
    raise ValueError("No authored SRT cue covers requested video time")


def _wrap(text: str, *, font, draw, max_width: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        next_line = (current + " " + word).strip()
        if draw.textlength(next_line, font=font) <= max_width:
            current = next_line
        else:
            if not current:
                raise ValueError("Single word exceeds caption area")
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > 5:
        raise ValueError("Authored caption too long for portrait safe area")
    return lines


def visual_frame(time_s: float, *, width: int,
                 spoken: tuple[str, ...] | None = None) -> Image.Image:
    """Draw one original motion-infographic frame, without external images."""
    if width not in (360, 540, 720, 1080) or not 0 <= time_s < 42:
        raise ValueError("Invalid bounded visual preview geometry/time")
    text = english_script_rows() if spoken is None else spoken
    if len(text) != 4 or any(not isinstance(item, str) for item in text):
        raise ValueError("Four authored English captions required")
    items = _illustrative_csv_data()
    height = width * 16 // 9
    factor = width / 540
    s = lambda n: round(n * factor)
    xy = lambda seq: tuple(s(n) for n in seq)

    # Original dark-navy gradient, parallax grid and pseudo-3D glass card.
    image = Image.new("RGB", (width, height))
    pixels = ImageDraw.Draw(image)
    for y in range(height):
        p = y / height
        pixels.line((0, y, width, y), fill=(6, int(17+9*p), int(33+20*p)))
    draw = ImageDraw.Draw(image, "RGBA")
    for i in range(11):
        yy = s(120 + 78*i + (time_s*5)%78)
        draw.line((0, yy, width, yy), fill=(34, 135, 170, 34))
    for i in range(14):
        x = s(30 + (i*53)%480 + 13*math.sin(time_s+i))
        y = s(95 + (i*61)%740 + 10*math.cos(time_s/2+i))
        draw.ellipse((x-2, y-2, x+2, y+2), fill=(78, 220, 218, 110))

    draw.rounded_rectangle(xy((24, 86, 516, 154)), radius=s(17),
                           fill=(8, 35, 60, 230), outline=(42, 210, 219, 190),
                           width=max(1, s(2)))
    draw.text(xy((50, 109)), "FM / FLOWMINUTE LAB",
              font=_font(s(24), bold=True), fill=(222, 252, 254))
    draw.text(xy((38, 180)), "ORIGINAL VISUAL STUDY  /  NO AUDIO",
              font=_font(s(15)), fill=(110, 220, 228))

    scene_idx = next((i for i, (a, b, _, __) in enumerate(SCENES)
                      if a <= time_s < b), 3)
    title, detail = SCENES[scene_idx][2:]
    top = 246 + 7 * math.sin(time_s*1.1)
    draw.rounded_rectangle(xy((34, top+22, 504, top+464)), radius=s(27),
                           fill=(7, 120, 152, 90))
    draw.rounded_rectangle(xy((44, top+8, 494, top+440)), radius=s(25),
                           fill=(6, 37, 62, 238), outline=(44, 209, 227, 200),
                           width=max(1, s(3)))
    ft = _font(s(24 if len(title)>20 else 27), bold=True)
    draw.text((width//2-draw.textlength(title, font=ft)/2,s(top+45)), title,
              font=ft, fill=(239, 249, 251))
    draw.text(xy((87, top+107)), detail, font=_font(s(16), bold=True),
              fill=(88, 236, 227))

    if scene_idx == 0:
        # An actual table with three named headers, not three unrelated
        # cards that confuse columns with product/amount rows.
        headers = tuple(DEMO_COLUMNS)
        positions = (93, 238, 378)
        for i,heading in enumerate(headers):
            draw.text(xy((positions[i], top+159)), heading.upper(),
                      font=_font(s(15), bold=True), fill=(114,243,225))
        for row_index,(product,units,price,_total) in enumerate(items):
            y=top+204+row_index*58
            draw.rounded_rectangle(xy((71,y,467,y+47)),radius=s(11),
                                   fill=(18,88,120,215),
                                   outline=(55,183,207,168))
            for pos,word in zip(positions,(product,units,price)):
                draw.text(xy((pos,y+13)),word,
                          font=_font(s(17),bold=True),fill=(236,250,253))
        draw.text(xy((89,top+403)),"FICTIONAL CSV TABLE",
                  font=_font(s(14),bold=True),fill=(90,236,217))
    elif scene_idx == 1:
        # The narrated 3 fictional items now clearly show units, example
        # price and total without confusing a unit with a product label.
        for row_index,(product,units,price,total) in enumerate(items):
            y=top+157+row_index*78
            draw.rounded_rectangle(xy((73,y,468,y+65)),radius=s(13),
                                   fill=(16,90,119,214),
                                   outline=(54,201,222,162))
            draw.text(xy((91,y+12)),product,
                      font=_font(s(18),bold=True),fill=(236,250,252))
            draw.text(xy((91,y+38)),f"{units} x {price} = {total}",
                      font=_font(s(17)),fill=(245,220,160))
        draw.text(xy((90,top+405)),"FICTIONAL UNITS  /  NO PURCHASE",
                  font=_font(s(13),bold=True),fill=(90,236,217))
    elif scene_idx == 2:
        # A four-line illustration of the *real in-memory demo pattern*:
        # read the text from a written buffer before building DictReader.
        code = (
            "csv_text = output.getvalue()",
            "source = StringIO(csv_text)",
            "reader = csv.DictReader(source)",
            "row['product']  ->  'Pen'",
        )
        for i, line in enumerate(code):
            draw.text(xy((61, top+159+i*52)),line,
                      font=_font(s(16)),
                      fill=(87,239,222) if i==2 else (238,247,248))
        draw.text(xy((86, top+401)),"ILLUSTRATIVE / NOT EXECUTED UI",
                  font=_font(s(13),bold=True),fill=(249,198,118))
    else:
        totals=tuple(row[3] for row in items)
        total=sum(totals)
        formula=" + ".join(str(n) for n in totals)
        draw.text(xy((105,top+165)),formula,
                  font=_font(s(29),bold=True),fill=(244,252,254))
        center=(s(269),s(top+305))
        radius=s(76+4*math.sin(time_s*2))
        draw.ellipse((center[0]-radius,center[1]-radius,
                      center[0]+radius,center[1]+radius),
                     fill=(8,146,174,194),outline=(110,246,217,230),
                     width=max(1,s(4)))
        number=str(total)
        ft=_font(s(66),bold=True)
        draw.text((center[0]-draw.textlength(number,font=ft)/2,
                   center[1]-s(51)),number,font=ft,fill=(251,244,210))
        draw.text(xy((88,top+408)),"EXAMPLE UNITS — NO PURCHASE",
                  font=_font(s(14)),fill=(148,239,236))

    # One original visual caption sample. Not actual speech synchronization.
    draw.rounded_rectangle(xy((28, 748, 512, 895)), radius=s(17),
                           fill=(3, 17, 32, 245), outline=(47, 189, 210, 185),
                           width=max(1, s(2)))
    font = _font(s(17), bold=True)
    cue = _estimated_caption_at(time_s) if spoken is None else text[scene_idx]
    lines = _wrap(cue,font=font,draw=draw,max_width=s(433))
    for i, line in enumerate(lines):
        draw.text((width//2-draw.textlength(line,font=font)/2,s(766+24*i)),
                  line,font=font,fill=(246,248,253))
    draw.text(xy((43, 923)), "NO RECORDED VOICE  /  NOT FOR PUBLICATION",
              font=_font(s(12)),fill=(155,197,211))
    return image


def render_visual_preview(output: Path, *, duration_s: float = 3,
                          fps: int = 12, width: int = 360,
                          start_s: float = 0) -> dict:
    """Render a safe original visual-only MP4 using FFmpeg and no network."""
    if (not isinstance(start_s,(int,float)) or isinstance(start_s,bool)
            or not math.isfinite(start_s)
            or not 0 <= start_s < 42 or start_s + duration_s > 42
            or not 0.5 <= duration_s <= 42
            or fps not in (8,12,15,24)
            or width not in (360,540,720,1080)
            or (width == 1080 and round(duration_s*fps) > 36)):
        raise ValueError("Unsafe render preview size, rate, offset or duration")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg must already be installed")
    captions = english_script_rows()
    output = Path(output)
    if output.suffix != ".mp4":
        raise ValueError("MP4 visual-only output required")
    if output.is_symlink() or output.exists() or not output.parent.is_dir():
        raise ValueError("Fresh MP4 in an existing ordinary output folder required")
    command = ["ffmpeg", "-nostdin", "-v", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "rgb24",
               "-video_size", f"{width}x{width*16//9}", "-framerate", str(fps),
               "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "veryfast",
               "-pix_fmt", "yuv420p", "-crf", "27", "-movflags", "+faststart", str(output)]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    try:
        for i in range(round(duration_s*fps)):
            frame = visual_frame(start_s+i/fps, width=width)
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        error = proc.stderr.read()
        proc.wait(timeout=120)
        if proc.returncode != 0:
            raise RuntimeError("Visual encoder failed: "+error.decode("utf-8","replace")[-300:])
    except Exception:
        proc.kill()
        proc.wait()
        output.unlink(missing_ok=True)
        raise
    if not output.is_file() or output.stat().st_size < 2048:
        raise RuntimeError("No usable visual MP4 produced")
    return {
        "status": "REAL_MP4_VISUALS_ONLY_NOT_PUBLISHABLE",
        "duration_s": duration_s, "width": width, "height": width*16//9,
        "frame_rate": fps, "size_bytes": output.stat().st_size,
        "preview_offset_seconds": start_s,
        "media_audio_present": False, "narration_recorded": False,
        "audio_rights_verified": False, "source_fact_review_authenticated": False,
        "youtube_upload_authorized": False, "publishing_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--duration", type=float, default=3)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--width", type=int, default=360)
    parser.add_argument("--start", type=float, default=0)
    options=parser.parse_args(argv)
    print(json.dumps(render_visual_preview(options.output,
        duration_s=options.duration,fps=options.fps,width=options.width,
        start_s=options.start),
        sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
