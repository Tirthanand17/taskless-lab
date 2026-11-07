"""B4e8: YouTube November 2026 private-default/regression and mock resume tests."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from zoneinfo import ZoneInfo
import unittest

from autopilot.youtube_private_first_contract import prepare_unapproved_intent
from autopilot.youtube_private_resumable_contract_b4e8 import (
    OfflineUploadRefused, CHUNK_BYTES, PART_BYTES,
    prepare_offline_private_resumable_spec, probe_same_session_headers,
    resume_chunk_spec, interpret_injected_session_response,
    simulate_next_seven_days,
)

NOW=datetime(2026,11,7,2,0,tzinfo=timezone.utc)
IST=ZoneInfo("Asia/Kolkata")
CHANNEL="UC"+"x"*22
TIMES={"short_am":(11,0),"long":(16,0),"short_pm":(20,30)}
ID="abCDEF123_-"


def digest(label):
    return sha256(label.encode()).hexdigest()


def mock_intent(day,slot,*,index=0):
    hour,minute=TIMES[slot]
    publish_at=datetime(day.year,day.month,day.day,hour,minute,tzinfo=IST)
    date_z=publish_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return prepare_unapproved_intent(
        episode_id=f"episode_{day.strftime('%Y%m%d')}_{slot}_{index}",
        slot=slot,channel_id=CHANNEL,
        final_mp4_sha256=digest(f"mp4:{day}:{slot}:{index}"),
        captions_srt_sha256=digest(f"srt:{day}:{slot}:{index}"),
        thumbnail_sha256=digest(f"png:{day}:{slot}:{index}"),
        source_review_context_sha256=digest(f"source:{day}:{slot}:{index}"),
        title=f"Unique original demo {slot} on {day} {index}",
        description=f"Original fictional source-independent educational example {index}",
        language="en",
        synthetic_media_disclosure=True,
        made_for_kids=False,
        publish_at_utc=date_z,
        now=NOW,
    )


def sample(slot="short_am"):
    return mock_intent((NOW.astimezone(IST).date()+timedelta(days=1)),slot)


def week():
    items=[]
    start=NOW.astimezone(IST).date()+timedelta(days=1)
    for d in range(7):
        day=start+timedelta(days=d)
        for slot in TIMES:
            items.append((mock_intent(day,slot,index=d),3_000_000+d))
    return items


class PrivateFirstRequestTests(unittest.TestCase):
    def test_insert_spec_explicitly_private_even_after_november_2026_change(self):
        spec=prepare_offline_private_resumable_spec(sample(),5_000_000,now=NOW)
        self.assertEqual(spec["operation"],"videos.insert")
        self.assertEqual(spec["upload_protocol"],"resumable")
        self.assertEqual(spec["parts"],"snippet,status")
        status=spec["metadata"]["status"]
        self.assertEqual(status["privacyStatus"],"private")
        self.assertEqual(status["publishAt"],"2026-11-08T05:30:00Z")
        self.assertIs(status["containsSyntheticMedia"],True)
        self.assertIs(status["selfDeclaredMadeForKids"],False)
        self.assertEqual(spec["actual_http_requests"],0)
        self.assertFalse(spec["owner_authenticated"])
        self.assertFalse(spec["release_authorized"])
        self.assertNotIn("Authorization",spec["headers_without_authorization"])
        self.assertNotIn("token",str(spec).lower())

    def test_all_three_ist_slots_have_explicit_private_status(self):
        for slot in TIMES:
            with self.subTest(slot=slot):
                intent=sample(slot)
                spec=prepare_offline_private_resumable_spec(intent,3_000_000,now=NOW)
                self.assertEqual(spec["metadata"]["status"]["publishAt"],intent.publish_at_utc)
                self.assertEqual(spec["metadata"]["status"]["privacyStatus"],"private")

    def test_forged_approval_or_context_or_time_or_media_refused(self):
        original=sample()
        for tamper in (
            replace(original,release_authorized=True),
            replace(original,real_owner_approval=True),
            replace(original,real_youtube_oauth=True),
            replace(original,simulation_only=False),
            replace(original,context_sha256="a"*64),
            replace(original,title="Changed title"),
        ):
            with self.subTest(tamper=tamper),self.assertRaises(OfflineUploadRefused):
                prepare_offline_private_resumable_spec(tamper,5_000_000,now=NOW)
        with self.assertRaises(OfflineUploadRefused):
            prepare_offline_private_resumable_spec(original,5_000_000,
                now=datetime(2026,11,8,5,25,tzinfo=timezone.utc))
        for media_size in (None,False,-1,299999,1_000_000_001):
            with self.subTest(media=media_size),self.assertRaises(OfflineUploadRefused):
                prepare_offline_private_resumable_spec(original,media_size,now=NOW)


class ExistingSessionOnlyTests(unittest.TestCase):
    def test_resume_308_range_and_no_range(self):
        self.assertEqual(
            interpret_injected_session_response(308,{"Range":"bytes=0-524287"},
                1_000_000)["next_byte"],524288)
        self.assertEqual(
            interpret_injected_session_response(308,{},1_000_000)["next_byte"],0)
        self.assertFalse(interpret_injected_session_response(
            308,{"Range":"bytes=0-524287"},1_000_000)["new_insert_allowed"])

    def test_resume_invalid_server_claims_fail_closed(self):
        for raw in ("bytes=1-55","bytes=0-1000000","bytes=0-999999",
                    "bytes=0-x","bytes=0--1","bytes=0-0,5-6"):
            with self.subTest(raw=raw),self.assertRaises(OfflineUploadRefused):
                interpret_injected_session_response(308,{"Range":raw},999999)
        with self.assertRaises(OfflineUploadRefused):
            interpret_injected_session_response(308,{},1_000_000,video_id=ID)

    def test_transient_failures_query_existing_session_never_reinsert(self):
        for status in (500,502,503,504):
            with self.subTest(status=status):
                result=interpret_injected_session_response(status,{},1_000_000)
                self.assertTrue(result["probe_same_session_first"])
                self.assertEqual(result["actual_http_requests"],0)
                self.assertFalse(result["new_insert_allowed"])
        self.assertEqual(probe_same_session_headers(9),
                         {"Content-Length":"0","Content-Range":"bytes */9"})

    def test_ambiguous_and_permanent_errors_require_manual_reconciliation(self):
        for code in (400,401,403,404,408,409,429,202):
            with self.subTest(code=code):
                result=interpret_injected_session_response(code,{},1_000_000)
                self.assertTrue(result["manual_reconciliation_required"])
                self.assertFalse(result["new_insert_allowed"])

    def test_completed_response_without_video_id_is_never_retried(self):
        for code in (200,201):
            with self.assertRaises(OfflineUploadRefused):
                interpret_injected_session_response(code,{},3_000_000)
            result=interpret_injected_session_response(code,{},3_000_000,video_id=ID)
            self.assertEqual(result["unverified_video_id"],ID)
            self.assertFalse(result["authenticated_remote_upload_proven"])
            self.assertFalse(result["release_authorized"])

    def test_chunk_ranges_use_actual_server_byte_offset(self):
        result=resume_chunk_spec(20_000_000,524288)
        self.assertEqual(result["start_byte"],524288)
        self.assertEqual(result["end_byte"],524288+CHUNK_BYTES-1)
        self.assertEqual(result["headers_without_auth"]["Content-Range"],
                         f"bytes 524288-{524288+CHUNK_BYTES-1}/20000000")
        final=resume_chunk_spec(3_000_000,2_900_000)
        self.assertEqual(final["end_byte"],2_999_999)
        self.assertEqual(final["chunk_byte_count"],100_000)
        self.assertFalse(final["new_insert_allowed"])

    def test_invalid_chunk_sizes_or_offsets_fail_closed(self):
        for size,offset,chunk in (
            (0,0,CHUNK_BYTES),(1000,1000,CHUNK_BYTES), (1000,-1,CHUNK_BYTES),
            (1000,0,PART_BYTES-1),(1000,0,PART_BYTES+1),
        ):
            with self.subTest(case=(size,offset,chunk)),self.assertRaises(OfflineUploadRefused):
                resume_chunk_spec(size,offset,chunk_bytes=chunk)


class SevenDaySimulationTests(unittest.TestCase):
    def test_exact_7_day_21_private_first_mock_contracts_only(self):
        receipt=simulate_next_seven_days(week(),now=NOW)
        self.assertEqual(receipt["simulated_days"],7)
        self.assertEqual(receipt["simulated_slots"],21)
        self.assertEqual(receipt["private_first_specs_created"],21)
        self.assertEqual(receipt["real_youtube_uploads"],0)
        self.assertEqual(receipt["real_youtube_scheduled_or_published"],0)
        self.assertEqual(receipt["video_upload_quota_consumed"],0)
        self.assertFalse(receipt["release_authorized"])
        self.assertEqual(receipt["slots"][0]["publish_at_utc"],"2026-11-08T05:30:00Z")
        self.assertEqual(receipt["slots"][-1]["slot"],"short_pm")
        self.assertNotIn("Unique original demo",str(receipt))

    def test_duplicates_and_reordered_slots_and_missing_days_blocked(self):
        cases=[]
        base=week()
        cases.append(base[:-1])
        x=week();x[1]=x[0];cases.append(x)
        x=week();x[0],x[1]=x[1],x[0];cases.append(x)
        x=week();x[3]=(replace(x[3][0],final_mp4_sha256=x[0][0].final_mp4_sha256),
                       x[3][1]);cases.append(x)
        x=week();x[6]=(replace(x[6][0],channel_id="UC"+"y"*22),x[6][1]);cases.append(x)
        for i,entry in enumerate(cases):
            with self.subTest(case=i),self.assertRaises(OfflineUploadRefused):
                simulate_next_seven_days(entry,now=NOW)

    def test_seven_day_receipt_cannot_claim_21_real_uploads(self):
        receipt=simulate_next_seven_days(week(),now=NOW)
        self.assertFalse(receipt["owner_authenticated"])
        self.assertFalse(receipt["durable_production_fence_deployed"])
        self.assertEqual(receipt["rights_and_factual_approvals"],0)
        self.assertTrue(all(not x["real_video_uploaded"] and
                            not x["real_video_scheduled"] for x in receipt["slots"]))


if __name__=="__main__":
    unittest.main()
