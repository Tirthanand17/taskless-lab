import tempfile
import sqlite3
import unittest
from dataclasses import replace
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
from autopilot.calendar import PublishingCalendar
from autopilot.calendar_ledger import AuthorizedSnapshot,PreparedEpisode,commit_calendar_drafts
from autopilot.core import CHANNEL_ID,GateError,MediaQA,ReleaseLedger,Stage,Topic

DAY=date(2026,10,18)
NOW=datetime(2026,10,17,6,tzinfo=timezone.utc)
SRC=('https://docs.python.org/3/library/','https://realpython.com/python-basics/')
WORDS=('saffron','tulip','mountain','orbit','matrix','parrot','cosmos','helmet','glacier',
       'spiral','socket','marble','planet','cabinet','bridge','bamboo','violet','pocket')
def snapshot(**kw):
    base=AuthorizedSnapshot(CHANNEL_ID,NOW.isoformat(),(),'authenticated_youtube_api')
    return replace(base,**kw)
def prepared(calendar,day=DAY):
    ans={}
    for i,slot in enumerate(calendar.plan(day)):
        sha=format(i+1,'064x')
        topic=Topic(
          f'Use {WORDS[i]} {WORDS[i+9]} techniques in practical workflows',
          f'The viewer learns to complete an original guided step by step lesson number {i} with useful results',
          f'Build an original working dummy dataset and compare accurate outputs for lesson {i}',
          SRC,.95)
        qa=MediaQA(sha,43 if slot.kind=='short' else 300,
                   41 if slot.kind=='short' else 299,
                   1080 if slot.kind=='short' else 1920,
                   1920 if slot.kind=='short' else 1080,
                   -3,True,True,True,True,True)
        ans[(slot.kind,slot.ordinal)]=PreparedEpisode(f'episode_{i}',sha,topic,qa)
    return ans

class TestLedgerBridge(unittest.TestCase):
 def setUp(self):
    self.folder=tempfile.TemporaryDirectory()
    self.ledger=ReleaseLedger(Path(self.folder.name)/'real.db')
    self.calendar=PublishingCalendar()
 def tearDown(self): self.folder.cleanup()
 def commit(self,**kw):
    return commit_calendar_drafts(calendar=kw.pop('calendar',self.calendar),day=kw.pop('day',DAY),
       prepared=kw.pop('prepared',prepared(self.calendar)),snapshot=kw.pop('snapshot',snapshot()),
       ledger=self.ledger,now=kw.pop('now',NOW),**kw)
 def rows(self):
    with sqlite3.connect(self.ledger.path) as con:
       return con.execute('SELECT episode,kind,stage FROM releases ORDER BY episode').fetchall()
 def test_default_three_reserved_only_planned(self):
    r=self.commit()
    self.assertEqual(len(r),3)
    self.assertTrue(all(r.values()))
    self.assertEqual({kind for _,kind,_ in self.rows()},{'short','long'})
    self.assertTrue(all(stage=='planned' for _,_,stage in self.rows()))
 def test_idempotent_replay_only_returns_false(self):
    self.commit()
    r=self.commit()
    self.assertEqual(list(r.values()),[False,False,False])
    self.assertEqual(len(self.rows()),3)
 def test_six_shorts_three_longs_atomic(self):
    cal=PublishingCalendar()
    cal.apply('Tomorrow upload 6 Shorts and 3 long videos',today=NOW.date())
    r=commit_calendar_drafts(calendar=cal,day=DAY,prepared=prepared(cal),
       snapshot=snapshot(),ledger=self.ledger,now=NOW)
    self.assertEqual(len(r),9)
    self.assertEqual(len(self.rows()),9)
 def test_incorrect_channel_blocks_before_database(self):
    with self.assertRaises(GateError):
       self.commit(snapshot=snapshot(channel='UC-wrong'))
    self.assertEqual(self.rows(),[])
 def test_stale_snapshot_blocks(self):
    with self.assertRaises(GateError):
       self.commit(snapshot=snapshot(checked_utc=(NOW-timedelta(hours=1)).isoformat()))
    self.assertEqual(self.rows(),[])
 def test_untrusted_source_blocks(self):
    with self.assertRaises(GateError):
       self.commit(snapshot=snapshot(source='manual_ledger'))
 def test_missing_prepared_slot_blocks(self):
    data=prepared(self.calendar);data.pop(next(iter(data)))
    with self.assertRaises(GateError):self.commit(prepared=data)
    self.assertEqual(self.rows(),[])
 def test_failed_rights_check_atomic(self):
    data=prepared(self.calendar);key=('long',1)
    data[key]=replace(data[key],qa=replace(data[key].qa,rights_verified=False))
    with self.assertRaises(GateError):self.commit(prepared=data)
    self.assertEqual(self.rows(),[])
 def test_invalid_media_hash_atomic(self):
    data=prepared(self.calendar);key=('long',1)
    data[key]=replace(data[key],sha256='f'*64)
    with self.assertRaises(GateError):self.commit(prepared=data)
    self.assertEqual(self.rows(),[])
 def test_duplicate_media_hash_atomic(self):
    data=prepared(self.calendar)
    data[('short',2)]=replace(data[('short',2)],episode='episode_0',
        qa=data[('short',1)].qa,sha256=data[('short',1)].sha256)
    with self.assertRaises(GateError):self.commit(prepared=data)
    self.assertEqual(self.rows(),[])
 def test_legacy_slot_collision_blocks_without_partial_insert(self):
    self.ledger.reserve('legacy','short_am',DAY.isoformat(),'a'*64,now=NOW)
    with self.assertRaises(GateError):self.commit()
    self.assertEqual(len(self.rows()),1)
    self.assertEqual(self.rows()[0][0],'legacy')
 def test_legacy_cannot_overwrite_existing_adaptive_slot(self):
    self.commit()
    with self.assertRaises(GateError):
       self.ledger.reserve('new_legacy','short_am',DAY.isoformat(),'c'*64,now=NOW)
    self.assertEqual(len(self.rows()),3)
 def test_conflict_second_insert_rolls_back_first(self):
    slots=self.calendar.plan(DAY)
    self.ledger.reserve_prepared_batch([('reserved','long',slots[1].planned_utc,'b'*64)],now=NOW)
    with self.assertRaises(GateError):self.commit()
    self.assertEqual(len(self.rows()),1)
 def test_occupied_youtube_schedule_blocks(self):
    s=snapshot(occupied_utc=(self.calendar.plan(DAY)[1].planned_utc,))
    with self.assertRaises(Exception):self.commit(snapshot=s)
    self.assertEqual(self.rows(),[])
 def test_z_suffix_from_actual_youtube_schedule_blocks(self):
    target=self.calendar.plan(DAY)[0].planned_utc.replace('+00:00','Z')
    with self.assertRaises(Exception):
       self.commit(snapshot=snapshot(occupied_utc=(target,)))
    self.assertEqual(self.rows(),[])
 def test_paused_day_never_reserves(self):
    cal=PublishingCalendar()
    cal.apply('Pause all videos tomorrow',today=NOW.date())
    with self.assertRaises(GateError):
       commit_calendar_drafts(calendar=cal,day=DAY,prepared={},snapshot=snapshot(),ledger=self.ledger,now=NOW)
 def test_remote_receipt_still_required_for_release(self):
    self.commit()
    with self.assertRaises(GateError):
       self.ledger.advance('episode_0',Stage.SCHEDULED_VERIFIED)
 def test_non_utc_malformed_snapshot_fails(self):
    with self.assertRaises(GateError):
       self.commit(snapshot=snapshot(checked_utc='not-a-date'))
 def test_invalid_media_too_old_reservation_blocked(self):
    with self.assertRaises(GateError):
       self.commit(now=NOW+timedelta(days=2),snapshot=snapshot(checked_utc=(NOW+timedelta(days=2)).isoformat()))
if __name__=='__main__':unittest.main()
