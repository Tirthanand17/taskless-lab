"""Branch 3 prelaunch static QA. Only standard library, never YouTube API."""
from __future__ import annotations
import json
from pathlib import Path
import re
import struct
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
    viral=json.loads((B3/"viral-content-strategy.json").read_text("utf8"))
    expected=["gaming","livestream","comedy","entertainment","podcast_interview"]
    live=json.loads((B3/"channel_state.json").read_text("utf8"))
    CHANNEL="UCfPEvy0SefE_5nNlYlY_CyQ"
    assert live["channel_name"]=="Clivox" and live["handle"]=="@ClivoxPulse"
    assert live["channel_id"]==CHANNEL and live["channel_created"] is True
    assert live["channel_id"]!=YOUTUBE_OLD
    assert live["channel_settings"]["upload_default_visibility"]=="private"
    assert live["channel_settings"]["intermediate_features"]=="enabled"
    assert live["channel_settings"]["advanced_features"]=="eligible_not_yet_enabled"
    assert live["channel_settings"]["phone_verification_status"]=="confirmed_by_youtube_studio_intermediate_enabled"
    assert live["channel_settings"]["automatic_publishing_enabled"] is False
    assert live["release_gates"]["verified_creator_permissions_count"]==0
    assert live["release_gates"]["publishing_channel_oauth_connected"] is False
    assert live["release_gates"]["github_release_automation_enabled"] is False
    assert live["release_gates"]["videos_uploaded_by_this_setup"]==0
    assert all(live["production_branding"][key] is True for key in
               ("avatar_uploaded_and_visible","banner_uploaded_and_publicly_visible","about_published_and_visible"))
    assert viral["channel"]=="Clivox" and viral["channel_created"] is True
    assert viral["channel_id"]==CHANNEL and viral["handle"]=="@ClivoxPulse"
    assert viral["experiment_priority_order"]==expected
    assert [pillar["id"] for pillar in viral["content_pillars"]]==expected
    assert viral["release_and_rights"]["publishing_enabled"] is False
    assert viral["release_and_rights"]["permission_required_before_download"] is True
    assert viral["release_and_rights"]["no_leaked_game_footage"] is True
    assert viral["no_candidates_approved"] is True
    assert "GTA VI" in viral["content_pillars"][0]["title"]
    assert "support.rockstargames.com" in str(viral["official_refs"])
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
    # Verify archived production PNG dimensions and bytes, not only SVG studies.
    for key,expected_dimensions,limit in (
        ("avatar_png",(1254,1254),4_000_000),
        ("banner_png",(2560,1440),6_000_000),
    ):
        relative=live["production_branding"][key]
        assert relative.startswith("branch3/branding/") and relative.endswith(".png")
        png=ROOT/relative
        assert png.is_file() and not png.is_symlink()
        assert 100_000 < png.stat().st_size <= limit
        with png.open("rb") as stream:
            header=stream.read(24)
        assert header[:8]==bytes.fromhex("89504e470d0a1a0a")
        assert header[12:16]==b"IHDR"
        assert struct.unpack(">II",header[16:24])==expected_dimensions
    banner=(B3/"branding/clivox-banner.svg").read_text("utf8")
    assert "Clips worth watching. Context worth knowing." in banner
    assert "Clivox" in banner
    profile=(B3/"channel-profile.md").read_text("utf8")
    research=(B3/"research.md").read_text("utf8")
    rights=(B3/"rights-and-release.md").read_text("utf8")
    assert "@ClivoxPulse" in profile
    assert CHANNEL in profile and "LIVE BANNER" in profile
    for url in (
        "https://support.google.com/youtube/answer/1311392",
        "https://support.google.com/youtube/answer/2797466",
        "https://support.google.com/youtube/answer/1646861"
    ):
        assert url in research
    assert "written" in rights.lower() and "DENY ALL" in rights
    assert "creator-permission-only" in rights.lower()
    assert "No new uploads" in rights
    print("BRANCH3_LIVE_CHANNEL_ASSETS_VERIFIED_NO_UPLOAD_AUTOMATION_ZERO_CREATOR_RIGHTS")

if __name__=="__main__":
    validate()
