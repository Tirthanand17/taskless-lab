"""B3d4c2c3a: three original, primary-source-grounded educational *drafts*.

Pure stdlib, no model API, cloud credentials, YouTube upload, paid provider,
external media/image download, source-body copying or laptop storage.
Research references are official NASA/NIST/USGS public pages reviewed
2026-11-04. CI validates deterministic calculations, source citation
coverage, narration bounds and original SVG scene syntax but DOES NOT fetch
sources live or replace independent factual/rights/human review.

The three distinct topics are not historical earthquake observations,
communications measurements, actual file-download measurements or current
astronomical ephemerides. They are explanatory calculations with caveats.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, localcontext
from hashlib import sha256
from html import escape
import json
import re
from typing import Mapping
from xml.etree import ElementTree as ET

PRIMARY_REFERENCES = {
    "nasa_moon": {
        "url": "https://science.nasa.gov/moon/facts/",
        "publisher": "NASA",
        "role": "Mean Earth-Moon separation is about 384,400 kilometres",
        "reviewed": "2026-11-04",
    },
    "nist_light": {
        "url": "https://physics.nist.gov/cuu/Constants/Value/c.html",
        "publisher": "NIST",
        "role": "Speed of light in vacuum is exactly 299,792,458 metres per second",
        "reviewed": "2026-11-04",
    },
    "usgs_magnitude": {
        "url": "https://www.usgs.gov/programs/earthquake-hazards/earthquake-magnitude-energy-release-and-shaking-intensity",
        "publisher": "USGS",
        "role": "One magnitude step is ten times measured amplitude but about 32 times energy",
        "reviewed": "2026-11-04",
    },
    "usgs_energy": {
        "url": "https://earthquake.usgs.gov/education/how_much_bigger.php",
        "publisher": "USGS",
        "role": "Relative seismic energy uses 10 raised to 1.5 times magnitude difference",
        "reviewed": "2026-11-04",
    },
    "nist_binary": {
        "url": "https://physics.nist.gov/cuu/Units/binary.html",
        "publisher": "NIST",
        "role": "Eight bits per byte; decimal MB and binary MiB are different amounts",
        "reviewed": "2026-11-04",
    },
    "nist_si": {
        "url": "https://www.nist.gov/pml/owm/metric-si-prefixes",
        "publisher": "NIST",
        "role": "Mega is the decimal multiplier one million",
        "reviewed": "2026-11-04",
    },
}

SLOTS = {
    "short_am": {"time_ist": "11:00", "kind": "short", "theme": "lunar_signal"},
    "long": {"time_ist": "16:00", "kind": "long", "theme": "file_transfer"},
    "short_pm": {"time_ist": "20:30", "kind": "short", "theme": "quake_energy"},
}
SLOT_REFERENCE_IDS = {
    "short_am": ("nasa_moon", "nist_light"),
    "long": ("nist_binary", "nist_si"),
    "short_pm": ("usgs_magnitude", "usgs_energy"),
}
DISALLOWED_CLAIMS = (
    "real_human_fact_approval", "real_source_live_recheck",
    "real_video_produced", "real_rights_and_license_approval",
    "real_human_final_watch", "creator_owner_publish_consent",
    "real_provider_generated_script", "youtube_upload_enabled",
    "release_authorized",
)
STATUS = "PRIMARY_SOURCE_LINKED_EXECUTED_EDUCATION_DRAFT_NOT_FACT_OR_RIGHTS_CLEARED"


class StoryboardError(ValueError):
    """No authority to treat educational explanation as approved publication."""


@dataclass(frozen=True)
class Scene:
    scene_id: str
    narration: str
    display_title: str
    display_value: str
    visual_action: str
    claim_ids: tuple[str, ...]
    estimated_seconds: int


def canonical(value: object) -> bytes:
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise StoryboardError("Unserializable content draft") from exc
    if len(raw) > 300_000:
        raise StoryboardError("Unbounded content draft")
    return raw


def research_facts() -> dict:
    """Compute from official-source inputs, not from a model's assertion."""
    with localcontext() as ctx:
        ctx.prec = 32
        moon_km = Decimal("384400")
        c_m_s = Decimal("299792458")
        one_way = moon_km * Decimal(1000) / c_m_s
        two_way = one_way * 2
        one_step = Decimal(1000).sqrt()  # = 10^(1.5)
        two_step = Decimal(1000)
        mb_decimal_bytes = Decimal(100_000_000)
        mib_bytes = Decimal(100 * 2**20)
        twenty_mbit_s = Decimal(20_000_000)
        decimal_seconds = mb_decimal_bytes * 8 / twenty_mbit_s
        binary_seconds = mib_bytes * 8 / twenty_mbit_s
    return {
        "moon_average_km": 384400,
        "vacuum_light_m_s": 299792458,
        "moon_one_way_seconds_rounded": str(one_way.quantize(Decimal("0.01"))),
        "moon_round_trip_seconds_rounded": str(two_way.quantize(Decimal("0.01"))),
        "quake_one_magnitude_energy_multiplier_rounded": str(one_step.quantize(Decimal("0.1"))),
        "quake_two_magnitudes_energy_multiplier": int(two_step),
        "quake_one_magnitude_amplitude_multiplier": 10,
        "byte_in_bits": 8,
        "decimal_mb_bytes": 1000000,
        "binary_mib_bytes": 1048576,
        "illustrative_file_size_mb": 100,
        "illustrative_link_megabits_per_second": 20,
        "theoretical_100_mb_transfer_seconds": str(decimal_seconds.quantize(Decimal("0.01"))),
        "theoretical_100_mib_transfer_seconds": str(binary_seconds.quantize(Decimal("0.01"))),
    }


def _scene(n: str, title: str, value: str, action: str,
           claims: tuple[str, ...], seconds: int) -> Scene:
    if not 8 <= len(n.split()) <= 83:
        raise StoryboardError("Scene cannot be empty or overly dense")
    if not 6 <= seconds <= 30 or not 1 <= len(claims) <= 3:
        raise StoryboardError("Insufficient scene duration or claim coverage")
    return Scene("", n, title, value, action, claims, seconds)


def _moon(f: dict) -> list[Scene]:
    return [
        _scene(
            "Imagine speaking to someone on the Moon. Before they can answer, your voice becomes an electronic signal racing across space. Even a perfect signal cannot arrive instantly.",
            "The Moon call", "Not instant", "earth_moon_signal", ("moon_delay",), 12,
        ),
        _scene(
            "NASA gives the Moon's average separation from Earth as about 384,400 kilometres. The actual distance changes as the Moon travels around Earth, so today's delay will vary.",
            "Average separation", "384,400 km", "orbit_ruler", ("moon_distance",), 11,
        ),
        _scene(
            "NIST specifies the speed of light in vacuum as exactly 299,792,458 metres per second. Radio signals in empty space travel at essentially this speed.",
            "The speed limit", "299,792,458 m/s", "signal_sweep", ("light_speed",), 12,
        ),
        _scene(
            f"Convert kilometres into metres, then divide distance by speed. The ideal one-way travel time works out to roughly {f['moon_one_way_seconds_rounded']} seconds using the average distance.",
            "Distance ÷ speed", f"{f['moon_one_way_seconds_rounded']} s one way", "one_way_clock",
            ("moon_delay", "moon_distance"), 12,
        ),
        _scene(
            f"A reply must cross the same distance again. That makes the ideal round-trip signal travel time around {f['moon_round_trip_seconds_rounded']} seconds, even before equipment processing or human reaction.",
            "A reply travels back", f"{f['moon_round_trip_seconds_rounded']} s round trip", "return_wave",
            ("moon_delay",), 12,
        ),
        _scene(
            "So a pause in a Moon conversation is not poor internet by itself; physics adds a delay first. The numbers are averages, not a live mission measurement.",
            "Physics, then networks", "Average only", "takeaway_moon",
            ("moon_delay",), 10,
        ),
    ]


def _quake(f: dict) -> list[Scene]:
    return [
        _scene(
            "A magnitude seven earthquake is not just a little larger than magnitude six. Magnitude is a logarithmic scale, so small-looking numerical steps can mean enormous changes in released energy.",
            "The surprising scale", "+1 is not +1%", "magnitude_steps", ("quake_energy",), 12,
        ),
        _scene(
            "The United States Geological Survey explains that one whole magnitude step corresponds to roughly ten times the measured seismic-wave amplitude. That is the wave measurement, not the energy ratio.",
            "Wave amplitude", "10× per step", "amplitude_ladder", ("quake_amplitude",), 12,
        ),
        _scene(
            f"For energy, the multiplier is ten raised to one point five: approximately {f['quake_one_magnitude_energy_multiplier_rounded']} times for a single magnitude step. That is why seven versus six is a far bigger difference than one percent.",
            "Energy grows faster", f"{f['quake_one_magnitude_energy_multiplier_rounded']}×", "energy_columns", ("quake_energy",), 13,
        ),
        _scene(
            f"Go up two steps, from magnitude five to seven, and the idealized relative energy becomes {f['quake_two_magnitudes_energy_multiplier']:,} times. The model compares magnitudes, not observed losses from two specific earthquakes.",
            "Two steps", f"{f['quake_two_magnitudes_energy_multiplier']:,}× energy", "energy_two_steps", ("quake_energy",), 12,
        ),
        _scene(
            "Important distinction: more radiated energy does not automatically mean a thousand times more damage. Distance, depth, local ground and building design all change the shaking people experience.",
            "Energy ≠ damage", "Local conditions matter", "damage_caveat", ("quake_damage_caveat",), 12,
        ),
        _scene(
            "When a headline gives an earthquake magnitude, read it as a logarithmic measure of event size. Do not treat the scale like ordinary marks on a ruler.",
            "Read the scale right", "Logarithmic", "takeaway_quake", ("quake_amplitude", "quake_energy"), 9,
        ),
    ]


def _data_long(f: dict) -> list[Scene]:
    # The long episode has its own 20-scene visual grammar and technical
    # explanation, independent of the space and earthquake shorts.
    return [
        _scene("A download estimate can be wrong before you even press start. The culprit is often a single capital letter: lowercase b versus uppercase B. They do not mean the same quantity.", "One letter, eightfold effect", "b ≠ B", "bit_tiles", ("bit_byte",), 15),
        _scene("We'll calculate a file transfer from first principles. No live speed test, no branded provider, and no mysterious app benchmark: just clearly stated assumptions and units you can check.", "A transparent model", "Numbers, not a speed test", "transfer_assumptions", ("ideal_model",), 15),
        _scene("NIST describes one byte as eight bits. A bit can represent a binary zero or one, while eight bits together form the byte used in our file-size example.", "Build one byte", "8 bits = 1 byte", "eight_bit_grid", ("bit_byte",), 17),
        _scene("When a network connection advertises twenty megabits per second, that is twenty million bits each second in decimal notation. It is not automatically twenty megabytes per second.", "Read the label", "20 Mb/s", "speedometer_bits", ("megabit_definition",), 17),
        _scene("NIST documents that the prefix mega is one million. This matters because decimal units are not the same as the binary prefixes used by some software storage displays.", "The SI prefix mega", "1,000,000", "decimal_blocks", ("mega_decimal",), 17),
        _scene("Let's choose a deliberately round decimal file size: one hundred megabytes. Since each megabyte is a million bytes, the example contains one hundred million bytes.", "A sample file", "100 MB", "file_decimal", ("file_sample", "mega_decimal"), 16),
        _scene("Now multiply bytes by eight bits per byte. Our one hundred million bytes become eight hundred million bits. Keeping the unit labels next to the numbers prevents a common mistake.", "Bytes become bits", "800,000,000 bits", "byte_to_bit_pipeline", ("file_sample", "bit_byte"), 18),
        _scene("Divide eight hundred million bits by the ideal twenty million bits per second. The result is forty seconds, assuming that every advertised bit of the connection carries your file.", "The simple division", f"{f['theoretical_100_mb_transfer_seconds']} seconds", "transfer_timer", ("ideal_transfer",), 18),
        _scene("That forty-second result is a theoretical floor for this simplified example, not a promise. Protocol headers, congestion, connection overhead and server limits can make actual transfers slower.", "An ideal floor", "Real transfer can take longer", "network_overhead", ("ideal_model",), 19),
        _scene("Here is the next trap. Some file displays use binary units and others use decimal ones. The letter i in MiB is not decoration: it specifies a power-of-two multiple.", "Decimal versus binary", "MB ≠ MiB", "unit_split", ("binary_prefix",), 16),
        _scene("NIST lists one mebibyte, written MiB, as two to the twentieth bytes. That equals exactly one million forty-eight thousand five hundred seventy-six bytes.", "One MiB", "1,048,576 bytes", "binary_blocks", ("binary_prefix",), 18),
        _scene("One decimal MB, by contrast, is exactly one million bytes. For one unit the difference looks modest, but comparing many units makes the rounding gap visible.", "One MB", "1,000,000 bytes", "decimal_binary_compare", ("mega_decimal", "binary_prefix"), 19),
        _scene("Now change only the file-size unit in our thought experiment. One hundred MiB is one hundred times one million forty-eight thousand five hundred seventy-six bytes.", "A binary-sized file", "100 MiB", "file_binary", ("binary_prefix",), 16),
        _scene("Multiply that binary-sized file by eight bits per byte, as before. We now have eight hundred thirty-eight million eight hundred sixty thousand eight hundred bits to send.", "Bits still matter", "838,860,800 bits", "binary_bits", ("bit_byte", "binary_prefix"), 18),
        _scene(f"At twenty megabits per second, the binary-sized example takes about {f['theoretical_100_mib_transfer_seconds']} seconds ideally. That is longer than the decimal one hundred MB example, even though both begin with the number one hundred.", "The new time", f"{f['theoretical_100_mib_transfer_seconds']} seconds", "two_timers", ("binary_transfer",), 20),
        _scene("Neither result tells you whether a home router or remote server is performing well. They only isolate the effect of units while holding the assumed network speed constant.", "What it proves", "Units, not a diagnosis", "model_boundary", ("ideal_model",), 20),
        _scene("Notice how careful units make the steps auditable. Start with a file size. Convert to bytes if necessary, then bits, and finally divide by bits per second.", "The repeatable method", "file → bits → seconds", "formula_pipeline", ("bit_byte", "ideal_transfer"), 20),
        _scene("If a speed label uses megabits per second, write Mb with a lowercase b. If the file size uses megabytes, write MB with a capital B. Match the units before you calculate.", "Two symbols", "Mb/s versus MB", "capitalization_pair", ("bit_byte", "mega_decimal"), 18),
        _scene("If a storage display says MiB, do not quietly treat it as MB. The binary mebi prefix means two to the twentieth, while decimal mega means ten to the sixth.", "Two multipliers", "2²⁰ versus 10⁶", "binary_decimal_scales", ("binary_prefix", "mega_decimal"), 20),
        _scene("A small notation mistake can shift a download estimate. A reliable explanation shows the formula, the assumptions and the units, then checks the real transfer separately when measurements are available.", "Keep the units visible", "Calculate, then measure", "conclusion_transfer", ("ideal_model", "ideal_transfer"), 20),
    ]


def _claims(slot: str) -> dict[str, dict]:
    if slot=="short_am":
        return {
            "moon_distance":{"summary":"Mean Earth-Moon separation approximated at 384400 km","sources":["nasa_moon"]},
            "light_speed":{"summary":"Light in vacuum is exactly 299792458 metres per second","sources":["nist_light"]},
            "moon_delay":{"summary":"Average-distance one-way and return latency follow distance divided by c; no equipment latency included","sources":["nasa_moon","nist_light"]},
        }
    if slot=="short_pm":
        return {
            "quake_amplitude":{"summary":"USGS explains factor of 10 measured amplitude per whole magnitude increase","sources":["usgs_magnitude"]},
            "quake_energy":{"summary":"USGS empirical relative energy factor is 10 raised to 1.5 times magnitude difference","sources":["usgs_energy","usgs_magnitude"]},
            "quake_damage_caveat":{"summary":"Magnitude energy alone is not an exact property-damage or shaking predictor","sources":["usgs_magnitude"]},
        }
    return {
        "bit_byte":{"summary":"NIST byte corresponds to exactly eight bits","sources":["nist_binary"]},
        "mega_decimal":{"summary":"SI mega is ten to the sixth and decimal MB is one million bytes","sources":["nist_si","nist_binary"]},
        "megabit_definition":{"summary":"Twenty Mb/s in the ideal example represents 20 million bits each second","sources":["nist_si","nist_binary"]},
        "file_sample":{"summary":"One hundred decimal MB contains 100 million bytes; example not observed transfer","sources":["nist_si","nist_binary"]},
        "ideal_transfer":{"summary":"A 100 MB file on an ideal 20 Mb/s link would take 40 seconds ignoring overhead","sources":["nist_binary","nist_si"]},
        "ideal_model":{"summary":"Transfers are idealized and omit all real network/server overhead","sources":["nist_binary","nist_si"]},
        "binary_prefix":{"summary":"One MiB is 1048576 bytes, not one decimal MB","sources":["nist_binary"]},
        "binary_transfer":{"summary":"One hundred MiB at ideal 20 Mb/s would take 41.94 seconds","sources":["nist_binary","nist_si"]},
    }


def build_story(slot: str, day: str="2026-11-12") -> dict:
    if slot not in SLOTS or not isinstance(day,str):
        raise StoryboardError("Only three established IST release slots allowed")
    try:
        when=date.fromisoformat(day)
    except ValueError as exc:
        raise StoryboardError("Not an ISO date") from exc
    if str(when)!=day or not date(2026,11,12)<=when<=date(2030,12,31):
        raise StoryboardError("Selected source-researched prototype date out of scope")
    fact=research_facts()
    source_ids=SLOT_REFERENCE_IDS[slot]
    script={
        "short_am": lambda:_moon(fact),
        "short_pm": lambda:_quake(fact),
        "long": lambda:_data_long(fact),
    }[slot]()
    claims=_claims(slot)
    if not script or any(not isinstance(s,Scene) for s in script):
        raise StoryboardError("Missing original scenes")
    completed=[]
    for index,entry in enumerate(script,1):
        if set(entry.claim_ids)-set(claims):
            raise StoryboardError("Uncited assertion on a scene")
        completed.append(asdict(Scene(
            scene_id=f"{slot}_beat_{index:02d}",
            narration=entry.narration,
            display_title=entry.display_title,
            display_value=entry.display_value,
            visual_action=entry.visual_action,
            claim_ids=entry.claim_ids,
            estimated_seconds=entry.estimated_seconds,
        )))
    if set(claims)!=set(k for item in completed for k in item["claim_ids"]):
        raise StoryboardError("Declared research claim omitted in story")
    if (slot=="long" and (len(completed)<20 or sum(x["estimated_seconds"] for x in completed)<310)
            or slot!="long" and (len(completed)!=6 or sum(x["estimated_seconds"] for x in completed)<55)):
        raise StoryboardError("Inadequate duration for proposed original educational story")
    ids={x for v in claims.values() for x in v["sources"]}
    if ids!=set(source_ids):
        raise StoryboardError("Cited primary references do not match signed topic sources")
    metadata={
        "schema_version":1,
        "status":STATUS,
        "episode_id":f"fm_{when:%Y%m%d}_{slot}",
        "slot":slot,
        "time_ist":SLOTS[slot]["time_ist"],
        "format":SLOTS[slot]["kind"],
        "theme":SLOTS[slot]["theme"],
        "primary_sources":{sid:PRIMARY_REFERENCES[sid] for sid in source_ids},
        "scientific_calculation_inputs_and_outputs":fact,
        "claim_index":claims,
        "scenes":completed,
        "scene_count":len(completed),
        "narration_words":sum(len(x["narration"].split()) for x in completed),
        "estimated_duration_seconds":sum(x["estimated_seconds"] for x in completed),
        "evidence_status":"public_primary_links_curated_not_refetched_in_ci",
        "real_primary_source_live_rechecked_by_runner":False,
        "independent_claim_by_claim_human_review_passed":False,
        "actual_content_originality_human_reviewed":False,
        "voice_music_image_rights_approved":False,
        "human_full_watch_listen_completed":False,
        "real_provider_generated_script":False,
        "private_media_and_editorial_receipts_deployed":False,
        "actual_video_rendered_for_this_story":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
    return {**metadata,"draft_sha256":sha256(canonical(metadata)).hexdigest()}


def require_exact_draft(story: Mapping) -> None:
    if not isinstance(story,dict):
        raise StoryboardError("Missing generated original draft")
    expected=build_story(story.get("slot"),story.get("episode_id","")[3:11][:4]+"-"+
                         story.get("episode_id","")[3:11][4:6]+"-"+
                         story.get("episode_id","")[3:11][6:])
    if canonical(story)!=canonical(expected):
        raise StoryboardError("Original calculation, citation, narration or scene modified")


def render_original_svg(story: dict, scene_index: int, tick: int=0) -> str:
    """Original vector drawing with three *distinct* topic-specific visual grammars.

    This generates independent local SVG storyboard preview bytes, not a
    licensed video/image nor a human-reviewed final frame. No HTML/script
    injection; all text escaped and source is a trusted exact storyboard.
    """
    require_exact_draft(story)
    if type(scene_index) is not int or not 0<=scene_index<story["scene_count"]:
        raise StoryboardError("Scene frame outside planned episode")
    if type(tick) is not int or not 0<=tick<=120:
        raise StoryboardError("Animated tick outside deterministic storyboard sample")
    scene=story["scenes"][scene_index]
    short=story["format"]=="short"
    w,h=(1080,1920) if short else (1920,1080)
    scale=(w/1080)
    # SVG visual frame is drawn at a standard 1080-unit width.
    W=1080; H=1920 if short else 608
    top=480 if short else 130
    theme=story["theme"]
    palette={
        "lunar_signal":("#090f25","#58c9ed","#f2e5bf"),
        "quake_energy":("#21131a","#ff9f62","#eee3d7"),
        "file_transfer":("#0a1b27","#72dfbd","#dff4ff"),
    }
    bg,accent,paper=palette[theme]
    labels=[
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="{bg}"/>',
        f'<text x="72" y="85" fill="{accent}" font-family="DejaVu Sans" font-size="27" font-weight="bold">'
        f'FLOWMINUTE · {escape(theme.replace("_"," ").upper())}</text>',
        f'<text x="72" y="{top-74}" fill="{paper}" font-family="DejaVu Sans" font-size="43" font-weight="bold">'
        f'{escape(scene["display_title"])}</text>',
        f'<text x="72" y="{top-20}" fill="{accent}" font-family="DejaVu Sans" font-size="36">'
        f'{escape(scene["display_value"])}</text>',
    ]
    if theme=="lunar_signal":
        t=(tick%120)/119
        x=260+560*t
        labels.extend([
            f'<circle cx="210" cy="{top+280}" r="140" fill="#246ea8" stroke="#78c8fe" stroke-width="10"/>',
            f'<path d="M 90 {top+290} Q 210 {top+80} 328 {top+295}" stroke="#5cdca5" stroke-width="20" fill="none" opacity=".66"/>',
            f'<circle cx="885" cy="{top+280}" r="77" fill="#bbb9bd" stroke="#f3f1ed" stroke-width="8"/>',
            f'<path d="M 330 {top+280} L 806 {top+280}" stroke="{accent}" stroke-width="9" stroke-dasharray="21 22"/>',
            f'<circle cx="{x:.1f}" cy="{top+280}" r="17" fill="#ffffff"/>',
            f'<text x="155" y="{top+475}" font-size="27" fill="{paper}">EARTH</text>',
            f'<text x="845" y="{top+475}" font-size="27" fill="{paper}">MOON</text>',
            f'<rect x="100" y="{top+525}" width="{int(870*t)}" height="12" rx="5" fill="{accent}"/>',
        ])
    elif theme=="quake_energy":
        levels=(150,350,565)
        for i,height in enumerate(levels):
            x=150+i*285
            labels.extend([
                f'<rect x="{x}" y="{top+625-height}" width="200" height="{height}" rx="12" fill="{accent}" opacity="{.44+i*.25:.2f}"/>',
                f'<text x="{x+25}" y="{top+663}" fill="{paper}" font-family="DejaVu Sans" font-size="27">M {5+i}</text>',
            ])
        labels.extend([
            f'<path d="M 80 {top+625} H 990" stroke="{paper}" stroke-width="4"/>',
            f'<text x="170" y="{top+730}" fill="{accent}" font-size="31">≈ 32× energy per step</text>',
            f'<circle cx="{160+(tick%120)*6}" cy="{top+170}" r="11" fill="#ffcba5"/>',
        ])
    else:
        for i in range(8):
            x=115+i*115
            active=(i+tick//6)%8
            labels.append(
                f'<rect x="{x}" y="{top+165}" width="75" height="82" rx="7" '
                f'fill="{accent if active<4 else "#29556d"}" stroke="#c9f9f2" stroke-width="2"/>'
            )
            labels.append(
                f'<text x="{x+25}" y="{top+219}" font-size="35" fill="{bg}">{i%2}</text>'
            )
        labels.extend([
            f'<text x="100" y="{top+330}" font-size="27" fill="{paper}">8 bits = 1 byte · decimal MB vs binary MiB</text>',
            f'<rect x="100" y="{top+400}" width="870" height="22" rx="10" fill="#1b3b4c"/>',
            f'<rect x="100" y="{top+400}" width="{int(870*tick/120)}" height="22" rx="10" fill="{accent}"/>',
            f'<text x="100" y="{top+480}" font-size="30" fill="{accent}">100 MB · ideal 20 Mb/s · 40 s</text>',
        ])
    # Deliberately original vector illustrations only; no third-party logos
    # or media copied or generated from a source page.
    labels.append(
        f'<text x="72" y="{H-75}" fill="{paper}" font-family="DejaVu Sans" font-size="24">'
        f'Scene {scene_index+1:02d}/{story["scene_count"]:02d} · DRAFT · NOT APPROVED</text>'
    )
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{w}" height="{h}">'+"".join(labels)+"</svg>"
    try:
        ET.fromstring(svg)
    except ET.ParseError as exc:
        raise StoryboardError("Malformed original vector scene") from exc
    return svg


def evaluate_three_draft_stories(day="2026-11-12") -> dict:
    stories=[build_story(slot,day) for slot in ("short_am","long","short_pm")]
    if len({s["draft_sha256"] for s in stories})!=3 or len({s["theme"] for s in stories})!=3:
        raise StoryboardError("Duplicated topic or draft")
    if [s["time_ist"] for s in stories]!=["11:00","16:00","20:30"]:
        raise StoryboardError("Daily IST timing mismatch")
    scene_hashes=[]
    for story in stories:
        require_exact_draft(story)
        scene_hashes.append(sha256(render_original_svg(story,0,50).encode()).hexdigest())
    if len(set(scene_hashes))!=3:
        raise StoryboardError("Not distinct topic-specific visual compositions")
    return {
        "status":"THREE_DISTINCT_PRIMARY_LINKED_EDUCATIONAL_DRAFTS_UNAPPROVED",
        "episode_ids":[s["episode_id"] for s in stories],
        "research_topics":[s["theme"] for s in stories],
        "draft_sha256":[s["draft_sha256"] for s in stories],
        "first_original_vector_scene_sha256":scene_hashes,
        "narration_words":[s["narration_words"] for s in stories],
        "estimated_duration_seconds":[s["estimated_duration_seconds"] for s in stories],
        "primary_reference_id_count":len({sid for s in stories for sid in s["primary_sources"]}),
        "three_different_executed_topic_calculations":True,
        "three_original_svg_visual_grammars":True,
        "primary_sources_fetched_and_human_claim_reviewed":False,
        "scripts_signed_by_real_channel_owner":False,
        "music_voice_images_rights_verified":False,
        "actual_audio_video_encoded":False,
        "actual_youtube_upload_or_schedule":False,
        "release_authorized":False,
    }
