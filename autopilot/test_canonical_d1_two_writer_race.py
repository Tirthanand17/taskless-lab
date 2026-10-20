"""Two independent simulated writers competing for one release slot.

This tests a local SQLite design property, not D1 distributed fencing.
No network, Cloudflare, OAuth, YouTube, external services or production writes.
"""
import os
import sqlite3
import tempfile
import unittest

SCHEMA = """CREATE TABLE releases (
 release_date TEXT NOT NULL, episode_id TEXT NOT NULL,
 channel_id TEXT NOT NULL, slot_ist TEXT NOT NULL,
 publish_at_utc TEXT, state TEXT NOT NULL, media_sha256 TEXT,
 youtube_id TEXT UNIQUE, updated_at_utc TEXT,
 PRIMARY KEY(release_date,episode_id))"""
DAY = '2026-10-20'
CHANNEL = 'UCCcL9Q_jqVq6LJmnYUSAFZA'
SLOT = 'short_morning'
TIME = '2026-10-20T05:30:00Z'

class TwoWriterReservationTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.TemporaryDirectory(prefix='flowminute-d1-race-')
        self.addCleanup(handle.cleanup)
        path = os.path.join(handle.name, 'isolated_simulation.sqlite')
        self.writer_a = sqlite3.connect(path, timeout=0.1, isolation_level=None)
        self.addCleanup(self.writer_a.close)
        self.writer_b = sqlite3.connect(path, timeout=0.1, isolation_level=None)
        self.addCleanup(self.writer_b.close)
        self.writer_a.execute('PRAGMA journal_mode=WAL')
        self.writer_a.execute(SCHEMA)
        self.writer_a.execute('CREATE INDEX idx_release_date_slot ON releases(release_date,slot_ist)')

    @staticmethod
    def claim(db, episode, video=None):
        db.execute("INSERT INTO releases VALUES (?,?,?,?,?,?,?,?,?)",
          (DAY,episode,CHANNEL,SLOT,TIME,'UPLOAD_STARTED','a'*64,video,'2026-10-19T00:00:00Z'))

    def test_nonunique_production_like_index_allows_split_brain_claims(self):
        self.claim(self.writer_a, 'fm_20261020_short_en')
        self.claim(self.writer_b, 'fm_20261020_short_hi')
        self.assertEqual(self.writer_a.execute('SELECT COUNT(*) FROM releases').fetchone()[0],2)

    def test_unique_date_slot_rejects_competing_writer_and_retains_first_id(self):
        self.writer_a.execute('CREATE UNIQUE INDEX ux_release_date_slot ON releases(release_date,slot_ist)')
        self.claim(self.writer_a,'fm_20261020_short_en')
        with self.assertRaises(sqlite3.IntegrityError):
            self.claim(self.writer_b,'fm_20261020_short_hi')
        only=self.writer_a.execute('SELECT episode_id,state FROM releases').fetchall()
        self.assertEqual(only,[('fm_20261020_short_en','UPLOAD_STARTED')])

    def test_locked_first_writer_denies_second_writer_before_lease_release(self):
        self.writer_a.execute('BEGIN IMMEDIATE')
        self.claim(self.writer_a, 'fm_20261020_short_en')
        with self.assertRaises(sqlite3.OperationalError):
            self.writer_b.execute('BEGIN IMMEDIATE')
        self.writer_a.execute('ROLLBACK')
        self.assertEqual(self.writer_b.execute('SELECT COUNT(*) FROM releases').fetchone()[0],0)

    def test_uncertain_upload_state_is_not_automatically_freed(self):
        self.writer_a.execute('CREATE UNIQUE INDEX ux_release_date_slot ON releases(release_date,slot_ist)')
        self.claim(self.writer_a, 'fm_20261020_short_en')
        # A crash with no video ID must preserve the reserved date/slot.
        self.assertEqual(self.writer_a.execute('SELECT youtube_id FROM releases').fetchone(),(None,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.claim(self.writer_b,'fm_20261020_short_hi')
        self.assertEqual(self.writer_a.execute('SELECT state FROM releases').fetchone(),('UPLOAD_STARTED',))

    def test_commit_then_replay_same_episode_does_not_trigger_new_upload(self):
        self.writer_a.execute('CREATE UNIQUE INDEX ux_release_date_slot ON releases(release_date,slot_ist)')
        self.claim(self.writer_a, 'fm_20261020_short_en')
        with self.assertRaises(sqlite3.IntegrityError):
            self.claim(self.writer_b,'fm_20261020_short_en')
        self.assertEqual(self.writer_a.execute('SELECT COUNT(*) FROM releases').fetchone()[0],1)

if __name__ == '__main__':
    unittest.main()
