"""B1q6: fake-only read-only YouTube schedule reconciliation tests.

Passing these tests is NOT an authenticated YouTube observation and does
not authorize an insert/update/delete. All fake private media IDs are kept
out of the report.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from autopilot.branch1_nov_repair_inventory import (
    CHANNEL, build_nov_repair_inventory,
)
from autopilot.branch1_owner_schedule_readonly_v6 import (
    read_owner_nov_schedule, ReadonlyScheduleRejected, RELEASE_STATUS,
)

ROOT=Path(__file__).resolve().parents[1]
OBSERVED=datetime(2026,11,5,12,30,tzinfo=timezone.utc)


class _Call:
    def __init__(self, function): self.function=function
    def execute(self): return self.function()


class _Api:
    def __init__(self, owner, kind):
        self.owner,self.kind=owner,kind

    def list(self, **kwargs):
        self.owner.called.append(self.kind+".list")
        if self.kind=="channels":
            assert kwargs == {"part":"id,contentDetails","mine":True,"maxResults":50}
        elif self.kind=="playlistItems":
            assert kwargs["part"]=="contentDetails" and kwargs["maxResults"]==50
        elif self.kind=="videos":
            assert kwargs["part"]=="id,snippet,status" and kwargs["maxResults"]==50
        return _Call(lambda:self.owner.response(self.kind,kwargs))


class FakeOwnerYoutube:
    def __init__(self):
        self.called=[]
        self.channel=CHANNEL
        self.inventory=build_nov_repair_inventory(ROOT)
        self.uploads_id="UU"+"E"*22
        self.records={}
        for slot in self.inventory["slots"]:
            if slot["historical"]:
                video_id=slot["historical"]["original_youtube_video_id"]
                self.records[video_id]={
                    "id":video_id,
                    "snippet":{"channelId":CHANNEL,
                               "title":"SECRET UNRELEASED TEST TITLE"},
                    "status":{"privacyStatus":"private",
                              "publishAt":slot["utc_publish_at"]},
                }
        self.omit_video=None
        self.repeat_token=False

    def channels(self): return _Api(self,"channels")
    def playlistItems(self): return _Api(self,"playlistItems")
    def videos(self): return _Api(self,"videos")

    def response(self,kind,kwargs):
        if kind=="channels":
            return {"items":[{
                "id":self.channel,
                "contentDetails":{"relatedPlaylists":{"uploads":self.uploads_id}},
            }]}
        if kind=="playlistItems":
            if self.repeat_token:
                return {"items":[],"nextPageToken":"SAME"}
            assert kwargs["playlistId"]==self.uploads_id
            return {"items":[{"contentDetails":{"videoId":i}}
                             for i in sorted(self.records)]}
        ids=kwargs["id"].split(",")
        return {"items":[v for i in ids
                         if i!=self.omit_video
                         if (v:=self.records.get(i)) is not None]}


class OwnerOnlyReadonlyReconciliation(unittest.TestCase):
    def test_all_21_slots_plus_four_confirmed_known_private_receipts(self):
        yt=FakeOwnerYoutube()
        outcome=read_owner_nov_schedule(yt,root=ROOT,checked_at_utc=OBSERVED)
        self.assertEqual(outcome["status"],RELEASE_STATUS)
        self.assertEqual(outcome["slots_checked"],21)
        self.assertEqual(outcome["original_git_receipts_count"],4)
        self.assertEqual(outcome["private_scheduled_slots_found"],4)
        self.assertEqual(outcome["historical_ids_same_private_schedule_count"],4)
        self.assertEqual(outcome["slot_conflicts"],0)
        self.assertEqual(sum(r["owner_private_scheduled_count"] for r in outcome["slots"]),4)
        self.assertTrue(outcome["owner_uploads_pagination_exhausted"])
        self.assertTrue(outcome["channel_owned_by_authenticated_oauth"])
        self.assertFalse(outcome["video_uploaded_or_edited_or_deleted"])
        self.assertFalse(outcome["safe_to_change_any_scheduled_video"])
        self.assertEqual(sorted(set(yt.called)),
            ["channels.list","playlistItems.list","videos.list"])
        serialized=json.dumps(outcome)
        self.assertNotIn("SECRET UNRELEASED TEST TITLE",serialized)
        self.assertNotIn(CHANNEL,serialized)
        for original in yt.records:
            self.assertNotIn(original,serialized)
        self.assertEqual(len(outcome["slots"]),21)

    def test_same_slot_two_privates_is_conflict_not_automatic_replacement(self):
        yt=FakeOwnerYoutube()
        yt.records["Z"*11]={
            "id":"Z"*11,
            "snippet":{"channelId":CHANNEL,"title":"Secret second future Short"},
            "status":{"privacyStatus":"private","publishAt":"2026-11-06T05:30:00Z"},
        }
        outcome=read_owner_nov_schedule(yt,root=ROOT,checked_at_utc=OBSERVED)
        self.assertEqual(outcome["slot_conflicts"],1)
        conflict=[x for x in outcome["slots"] if x["date_ist"]=="2026-11-06"
                  and x["time_ist"]=="11:00"][0]
        self.assertEqual(conflict["owner_private_scheduled_count"],2)
        self.assertEqual(conflict["slot_status"],
                         "MULTIPLE_PRIVATE_VIDEOS_AT_ONE_SLOT_STOP")
        self.assertFalse(conflict["replacement_eligible_without_human_release_approval"])

    def test_published_original_is_not_misreported_as_pending_schedule(self):
        yt=FakeOwnerYoutube()
        old=next(k for k,v in yt.records.items()
                 if v["status"]["publishAt"]=="2026-11-05T15:00:00Z")
        yt.records[old]["status"]={"privacyStatus":"public"}
        result=read_owner_nov_schedule(yt,root=ROOT,
                                       checked_at_utc=datetime(2026,11,6,12,
                                                               tzinfo=timezone.utc))
        first=next(r for r in result["slots"] if r["date_ist"]=="2026-11-05"
                   and r["time_ist"]=="20:30")
        self.assertEqual(first["historical_status"],"HISTORICAL_ID_NOW_PUBLIC")
        self.assertTrue(first["slot_time_already_passed"])
        self.assertEqual(first["owner_private_scheduled_count"],0)
        self.assertFalse(result["safe_to_change_any_scheduled_video"])

    def test_wrong_authenticated_channel_fails_closed(self):
        yt=FakeOwnerYoutube();yt.channel="UC"+"X"*22
        with self.assertRaises(ReadonlyScheduleRejected):
            read_owner_nov_schedule(yt,root=ROOT,checked_at_utc=OBSERVED)

    def test_remote_owner_mismatch_in_video_fails_closed(self):
        yt=FakeOwnerYoutube()
        first=next(iter(yt.records.values()))
        first["snippet"]["channelId"]="UC"+"X"*22
        with self.assertRaises(ReadonlyScheduleRejected):
            read_owner_nov_schedule(yt,root=ROOT,checked_at_utc=OBSERVED)

    def test_missing_video_in_complete_upload_scan_is_indeterminate(self):
        yt=FakeOwnerYoutube()
        yt.omit_video=next(iter(yt.records))
        with self.assertRaises(ReadonlyScheduleRejected):
            read_owner_nov_schedule(yt,root=ROOT,checked_at_utc=OBSERVED)

    def test_repeated_page_token_is_not_complete_channel_inventory(self):
        yt=FakeOwnerYoutube();yt.repeat_token=True
        with self.assertRaises(ReadonlyScheduleRejected):
            read_owner_nov_schedule(yt,root=ROOT,checked_at_utc=OBSERVED)

    def test_private_publish_at_must_be_timezone_aware(self):
        yt=FakeOwnerYoutube()
        next(iter(yt.records.values()))["status"]["publishAt"]="2026-11-05T15:00:00"
        with self.assertRaises(ReadonlyScheduleRejected):
            read_owner_nov_schedule(yt,root=ROOT,checked_at_utc=OBSERVED)

    def test_no_naive_readback_time(self):
        with self.assertRaises(ReadonlyScheduleRejected):
            read_owner_nov_schedule(FakeOwnerYoutube(),root=ROOT,
                                    checked_at_utc=datetime(2026,11,5,12,30))


if __name__=="__main__":
    unittest.main()
