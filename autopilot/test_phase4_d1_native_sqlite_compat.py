"""Execute exact exported D1-shaped JavaScript SQL in disposable SQLite only."""
from pathlib import Path
import json
import shutil
import sqlite3
import subprocess
import unittest
HERE=Path(__file__).parent
DAY="2026-10-20"
EP="fm_20261020_long_hi"
CH="UCCcL9Q_jqVq6LJmnYUSAFZA"
STAMP="2026-10-20T06:00:00Z"
SHA="a"*64
class D1NativeSqliteTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  node=shutil.which("node")
  if not node:raise unittest.SkipTest("Node missing; cannot attest SQL")
  cmd=[node,"--input-type=module","-e","import {D1_RESERVATION_SQL as q} from './autopilot/phase4_d1_native_reservation_candidate.mjs';console.log(JSON.stringify(q))"]
  r=subprocess.run(cmd,cwd=HERE.parent,capture_output=True,text=True,timeout=25)
  if r.returncode:raise RuntimeError("Could not read source SQL")
  cls.sql=json.loads(r.stdout)
 def setUp(self):
  self.db=sqlite3.connect(":memory:",isolation_level=None)
  self.addCleanup(self.db.close)
  self.db.execute("CREATE TABLE releases (release_date TEXT NOT NULL,episode_id TEXT NOT NULL,channel_id TEXT,slot_ist TEXT,publish_at_utc TEXT,state TEXT,media_sha256 TEXT,youtube_id TEXT UNIQUE,updated_at_utc TEXT,PRIMARY KEY(release_date,episode_id))")
  self.db.execute("CREATE INDEX idx_release_date_slot ON releases(release_date,slot_ist)")
  self.db.execute("CREATE TABLE release_events (id INTEGER PRIMARY KEY AUTOINCREMENT,release_date TEXT,episode_id TEXT,event_kind TEXT,detail_json TEXT,at_utc TEXT)")
  self.db.execute("INSERT INTO releases VALUES(?,?,?,?,?,?,?,?,?)",(DAY,EP,CH,"long","2026-10-20T10:30:00Z","MEDIA_QA_PASSED",SHA,None,"2026-10-19T00:00:00Z"))
 def unique(self):self.db.execute("CREATE UNIQUE INDEX ux_release_date_slot ON releases(release_date,slot_ist)")
 def updateargs(self):return (STAMP,DAY,EP,CH,"long","2026-10-20T10:30:00Z",SHA)
 def eventargs(self):return (STAMP,DAY,EP,CH,"long","2026-10-20T10:30:00Z",SHA,STAMP,DAY,EP)
 def test_existing_nonunique_slot_index_is_not_production_lock(self):
  r=self.db.execute(self.sql["indexes"]).fetchall()
  self.assertFalse(any(x[1]=="ux_release_date_slot" and x[2]==1 for x in r))
 def test_required_unique_index_is_exact_two_columns(self):
  self.unique();r=self.db.execute(self.sql["columns"]).fetchall()
  self.assertEqual([x[2] for x in r],["release_date","slot_ist"])
 def test_sql_is_preparable_using_real_canonical_columns(self):
  self.unique()
  self.db.execute("EXPLAIN "+self.sql["reserve"],self.updateargs())
  self.db.execute("EXPLAIN "+self.sql["event"],self.eventargs())
 def test_cas_event_once_and_no_replay(self):
  self.unique()
  self.assertEqual(self.db.execute(self.sql["reserve"],self.updateargs()).rowcount,1)
  self.assertEqual(self.db.execute(self.sql["event"],self.eventargs()).rowcount,1)
  self.assertEqual(self.db.execute(self.sql["reserve"],self.updateargs()).rowcount,0)
  self.assertEqual(self.db.execute(self.sql["event"],self.eventargs()).rowcount,0)
  self.assertEqual(self.db.execute("SELECT COUNT(*) FROM release_events").fetchone()[0],1)
 def test_event_before_reservation_cannot_append(self):
  self.unique()
  self.assertEqual(self.db.execute(self.sql["event"],self.eventargs()).rowcount,0)
 def test_existing_video_id_refuses_new_upload_attempt(self):
  self.unique();self.db.execute("UPDATE releases SET youtube_id='AbCdEfGhIj0'")
  self.assertEqual(self.db.execute(self.sql["reserve"],self.updateargs()).rowcount,0)
 def test_wrong_media_sha_refuses_cas(self):
  self.unique();args=list(self.updateargs());args[-1]="0"*64
  self.assertEqual(self.db.execute(self.sql["reserve"],args).rowcount,0)
 def test_gap_after_cas_and_before_event_stays_held(self):
  self.unique();self.db.execute(self.sql["reserve"],self.updateargs())
  self.assertEqual(self.db.execute("SELECT state FROM releases").fetchone()[0],"UPLOAD_STARTED")
  self.assertEqual(self.db.execute("SELECT COUNT(*) FROM release_events").fetchone()[0],0)
  self.assertEqual(self.db.execute(self.sql["reserve"],self.updateargs()).rowcount,0)
 def test_unique_index_blocks_another_episode_same_slot(self):
  self.unique()
  with self.assertRaises(sqlite3.IntegrityError):
   self.db.execute("INSERT INTO releases VALUES(?,?,?,?,?,?,?,?,?)",(DAY,"fm_20261020_short_hi",CH,"long","2026-10-20T10:30:00Z","MEDIA_QA_PASSED",SHA,None,STAMP))
 def test_local_transaction_rollback_does_not_prove_d1_batch(self):
  self.unique();self.db.execute("BEGIN IMMEDIATE")
  self.db.execute(self.sql["reserve"],self.updateargs())
  self.db.execute(self.sql["event"],self.eventargs())
  self.db.execute("ROLLBACK")
  self.assertEqual(self.db.execute("SELECT state FROM releases").fetchone()[0],"MEDIA_QA_PASSED")
  self.assertEqual(self.db.execute("SELECT COUNT(*) FROM release_events").fetchone()[0],0)
