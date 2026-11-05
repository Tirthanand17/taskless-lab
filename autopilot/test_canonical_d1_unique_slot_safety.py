"""Major Phase 4: isolated canonical D1 table/slot race and rollback rehearsal.

No live D1, Google API, network, token or production credential access.
Uses fresh disposable SQLite for every test. It does NOT establish Cloudflare
D1 transaction/fencing semantics, owner video identity, or migration authority.
"""
import sqlite3
import unittest

CANONICAL = """CREATE TABLE releases (
    release_date TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    slot_ist TEXT NOT NULL,
    publish_at_utc TEXT,
    state TEXT NOT NULL,
    media_sha256 TEXT,
    youtube_id TEXT UNIQUE,
    updated_at_utc TEXT,
    PRIMARY KEY(release_date,episode_id)
)"""
EVENTS = """CREATE TABLE release_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_date TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    event_kind TEXT NOT NULL,
    detail_json TEXT,
    at_utc TEXT NOT NULL
)"""
DAY = '2026-10-20'
CH = 'UCCcL9Q_jqVq6LJmnYUSAFZA'
SLOTS = (
    ('short_morning', 'fm_20261020_short_en', '2026-10-20T05:30:00Z', 'AbCdEfGhIj0'),
    ('long', 'fm_20261020_long_hi', '2026-10-20T10:30:00Z', 'KlMnOpQrSt1'),
    ('short_evening', 'fm_20261020_short_hi', '2026-10-20T15:00:00Z', 'MnOpQrStUv2'),
)


def release(slot, episode, when, video, *, state='SCHEDULED_VERIFIED'):
    return (DAY, episode, CH, slot, when, state, 'a'*64, video, '2026-10-19T00:00:00Z')


class CanonicalSlotSafety(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.addCleanup(self.db.close)
        self.db.execute(CANONICAL)
        self.db.execute(EVENTS)
        self.db.execute('CREATE INDEX idx_release_date_slot ON releases(release_date,slot_ist)')

    def insert(self, lane):
        self.db.execute('INSERT INTO releases VALUES (?,?,?,?,?,?,?,?,?)', release(*lane))

    def assertEmpty(self):
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM releases').fetchone()[0], 0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM release_events').fetchone()[0], 0)

    def test_original_nonunique_index_allows_second_episode_same_slot(self):
        first = SLOTS[0]
        self.insert(first)
        self.insert(('short_morning','fm_20261020_short_hi',first[2],'0123456789A'))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM releases').fetchone()[0],2)
        # This is the actual production flaw to address before enabling writes.

    def test_proposed_index_blocks_second_distinct_episode_on_same_slot(self):
        self.db.execute('CREATE UNIQUE INDEX ux_release_date_slot ON releases(release_date,slot_ist)')
        self.insert(SLOTS[0])
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert(('short_morning','fm_20261020_short_hi',SLOTS[0][2],'0123456789A'))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM releases').fetchone()[0], 1)

    def test_unique_video_id_independently_blocks_reused_remote_receipt(self):
        self.db.execute('CREATE UNIQUE INDEX ux_release_date_slot ON releases(release_date,slot_ist)')
        self.insert(SLOTS[0])
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert(('long','fm_20261020_long_hi',SLOTS[1][2],SLOTS[0][3]))

    def test_composite_episode_key_is_distinct_from_slot_constraint(self):
        self.insert(SLOTS[0])
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert(SLOTS[0])
        # Existing episode uniqueness does not protect a distinct episode.
        self.insert(('short_morning','fm_20261020_short_hi',SLOTS[0][2],'0123456789A'))

    def test_index_migration_rejects_existing_conflicting_rows(self):
        self.insert(SLOTS[0])
        self.insert(('short_morning','fm_20261020_short_hi',SLOTS[0][2],'0123456789A'))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('CREATE UNIQUE INDEX ux_release_date_slot ON releases(release_date,slot_ist)')
        self.assertIsNone(self.db.execute("SELECT name FROM sqlite_master WHERE name='ux_release_date_slot'").fetchone())

    def test_transaction_failure_rolls_back_index_releases_and_events(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            self.db.execute('CREATE UNIQUE INDEX ux_release_date_slot ON releases(release_date,slot_ist)')
            self.insert(SLOTS[0])
            self.db.execute("INSERT INTO release_events(release_date,episode_id,event_kind,detail_json,at_utc) VALUES(?,?,?,?,?)",
                            (DAY,SLOTS[0][1],'SIMULATED_IMPORT','{}','2026-10-19T00:00:00Z'))
            self.insert(('short_morning','fm_20261020_short_hi',SLOTS[0][2],'0123456789A'))
        except sqlite3.IntegrityError:
            self.db.execute('ROLLBACK')
        else:
            self.db.execute('COMMIT')
            self.fail('Expected a rollback-triggering unique-slot collision')
        self.assertEmpty()
        self.assertIsNone(self.db.execute("SELECT name FROM sqlite_master WHERE name='ux_release_date_slot'").fetchone())

    def test_mid_transaction_unknown_event_failure_keeps_zero_rows(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            self.insert(SLOTS[0])
            self.db.execute('INSERT INTO release_events(nonexistent_column) VALUES (?)',('no',))
        except sqlite3.OperationalError:
            self.db.execute('ROLLBACK')
        self.assertEmpty()

    def test_three_unique_slots_with_events_can_commit_atomically_in_sqlite(self):
        self.db.execute('BEGIN IMMEDIATE')
        self.db.execute('CREATE UNIQUE INDEX ux_release_date_slot ON releases(release_date,slot_ist)')
        for lane in SLOTS:
            self.insert(lane)
            self.db.execute('INSERT INTO release_events(release_date,episode_id,event_kind,detail_json,at_utc) VALUES (?,?,?,?,?)',
                            (DAY,lane[1],'SIMULATED_IMPORT','{}','2026-10-19T00:00:00Z'))
        self.db.execute('COMMIT')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM releases').fetchone()[0],3)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM release_events').fetchone()[0],3)
        self.assertEqual(self.db.execute('SELECT COUNT(DISTINCT slot_ist) FROM releases').fetchone()[0],3)


if __name__=='__main__':
    unittest.main()
