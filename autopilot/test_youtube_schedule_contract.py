"""Offline regression tests: never call Google/YouTube."""
from __future__ import annotations
import datetime as dt
import importlib.util
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("flowminute_youtube_uploader", HERE/"scripts"/"publish_youtube.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
NOW = dt.datetime(2026,10,23,14,0,tzinfo=dt.timezone.utc)
CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"

def test_valid_schedule_round_trip():
    assert MODULE.parse_scheduled_utc("2026-10-24T05:30:00Z",now=NOW) == "2026-10-24T05:30:00Z"

@pytest.mark.parametrize("bad",[
 "2026-10-24T05:30:00+05:30",
 "2026-10-24T05:30Z",
 "tomorrow 11am",
 "2026-10-24",
 "2026-13-24T05:30:00Z",
 "2026-10-23T14:14:59Z",
 "2026-10-23T13:59:59Z",
 ])
def test_schedule_refuses_ambiguity_and_past(bad):
    with pytest.raises(ValueError):
        MODULE.parse_scheduled_utc(bad,now=NOW)

def good_resource():
    return {
       "id":"vabcdEFGH12",
       "status":{"privacyStatus":"private","publishAt":"2026-10-24T05:30:00Z",
                 "uploadStatus":"uploaded"},
       "snippet":{"channelId":CHANNEL}
    }

def test_readback_confirms_correct_video_channel_and_time():
    assert MODULE.verify_youtube_schedule(good_resource(),"2026-10-24T05:30:00Z",CHANNEL)

@pytest.mark.parametrize("change",[
 ("publishAt","2026-10-24T06:30:00Z"),("privacyStatus","public"),("uploadStatus","rejected")
 ])
def test_readback_fails_on_wrong_schedule_or_privacy(change):
    x=good_resource();x["status"][change[0]]=change[1]
    assert not MODULE.verify_youtube_schedule(x,"2026-10-24T05:30:00Z",CHANNEL)

def test_readback_fails_on_wrong_channel():
    x=good_resource();x["snippet"]["channelId"]="UC"+"0"*22
    assert not MODULE.verify_youtube_schedule(x,"2026-10-24T05:30:00Z",CHANNEL)

def test_readback_requires_real_status_and_snippet():
    for payload in [{},None,{"status":{"privacyStatus":"private"}},{"snippet":{"channelId":CHANNEL}}]:
        assert not MODULE.verify_youtube_schedule(payload,"2026-10-24T05:30:00Z",CHANNEL)
