"""Branch 3 prelaunch static QA. Only standard library, never YouTube API."""
from __future__ import annotations
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
B3=ROOT/"branch3"
YOUTUBE_OLD="UCCcL9Q_jqVq6LJmnYUSAFZA"

def validate() -> None:
    registry=json.loads((B3/"source_registry.template.json").read_text("utf8"))
    assert registry["channel_created"] is False
    assert registry["channel_id"] is None
    assert registry["global_upload_enabled"] is False
    assert registry["creator_permissions"]==[]
    assert registry["candidates"]==[]
    assert YOUTUBE_OLD not in json.dumps(registry)
    permissions=json.loads((B3/"creator_permissions.json").read_text("utf8"))
    assert permissions["policy"]=="EXPLICIT_CREATOR_GRANT_ONLY"
    assert permissions["creators"]==[], "Never auto-approve a real creator in public prelaunch CI"
    assert permissions["schema_version"]==1
    files={
        "clivox-avatar.svg":(800,800),
        "clivox-banner.svg":(2560,1440),
    }
    for name,(w,h) in files.items():
        p=B3/"branding"/name
        assert p.is_file() and p.stat().st_size < 40_000
        body=p.read_text("utf8")
        assert "<script" not in body.lower()
        # SVG's required xmlns HTTP URL is a namespace identifier, not a
        # fetched external asset. Reject actual remote image/link references.
        stripped=body.replace('xmlns="http://www.w3.org/2000/svg"','')
        assert not re.search(r"(?:https?://|data:|javascript:|<image\\b|(?:href|xlink:href)\\s*=)",stripped,re.I)
        svg=ET.fromstring(body)
        assert svg.tag=="{http://www.w3.org/2000/svg}svg"
        assert int(svg.attrib["width"])==w and int(svg.attrib["height"])==h
        assert svg.attrib["viewBox"]==f"0 0 {w} {h}"
    banner=(B3/"branding/clivox-banner.svg").read_text("utf8")
    assert "Clips worth watching. Context worth knowing." in banner
    assert "Clivox" in banner
    profile=(B3/"channel-profile.md").read_text("utf8")
    research=(B3/"research.md").read_text("utf8")
    rights=(B3/"rights-and-release.md").read_text("utf8")
    assert "@Clivox" in profile
    assert "unverified" in profile.lower()
    for url in (
        "https://support.google.com/youtube/answer/1311392",
        "https://support.google.com/youtube/answer/2797466",
        "https://support.google.com/youtube/answer/1646861"
    ):
        assert url in research
    assert "written" in rights.lower() and "DENY ALL" in rights
    assert "creator-permission-only" in rights.lower()
    assert "No new uploads" in rights
    print("BRANCH3_STATIC_CHANNEL_READY_ONLY_ZERO_UPLOADS_ZERO_RIGHTS")

if __name__=="__main__":
    validate()
