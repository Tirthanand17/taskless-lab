"""Canonical D1 read-only query compatibility, simulated SQLite only."""
from pathlib import Path
import re
import sqlite3
import unittest

SOURCE=Path(__file__).with_name('canonical_d1_readback_candidate.mjs')


def query(field):
    text=SOURCE.read_text(encoding='utf8')
    found=re.search(rf"\b{field}: '([^']+)'", text)
    if not found: raise AssertionError('query not present')
    sql=found.group(1)
    assert sql.startswith('SELECT ')
    assert sql.count('?')==1
    assert not re.search(r'\b(?:INSERT|DELETE|UPDATE|DROP|ALTER|ATTACH|CREATE)\b',sql,re.I)
    return sql

class CanonicalSqlCompatibility(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.execute('CREATE TABLE releases (release_date TEXT,episode_id TEXT,channel_id TEXT,slot_ist TEXT,publish_at_utc TEXT,state TEXT,media_sha256 TEXT,youtube_id TEXT UNIQUE, PRIMARY KEY(release_date,episode_id))')
        self.db.execute('CREATE TABLE release_events (id INTEGER PRIMARY KEY,release_date TEXT,episode_id TEXT,event_kind TEXT,detail_json TEXT,at_utc TEXT)')
        for day,slot,name in [('2026-10-20','short_morning','a'),('2026-10-20','long','b'),('2026-10-20','short_evening','c'),('2026-10-21','long','d')]:
            self.db.execute('INSERT INTO releases VALUES (?,?,?,?,?,?,?,?)',(day,name,'channel',slot,'time','PLANNED','a'*64,None))
            self.db.execute('INSERT INTO release_events(release_date,episode_id,event_kind,detail_json,at_utc) VALUES (?,?,?,?,?)',(day,name,'PLANNED','{}','2026-10-20T00:00:00Z'))

    def test_sql_matches_real_canonical_names_and_parameter_binding(self):
        for name in ('releases','events'):
            sql=query(name)
            self.db.execute('EXPLAIN '+sql,('2026-10-20',)).fetchall()
            rows=self.db.execute(sql,('2026-10-20',)).fetchall()
            self.assertEqual(len(rows),3)
            self.assertNotIn('fm_release_writer_lease',sql)
            self.assertNotIn('fm_writer_release_shadow',sql)

    def test_sql_is_date_scoped_and_cannot_mutate(self):
        for name in ('releases','events'):
            sql=query(name)
            self.assertEqual(len(self.db.execute(sql,('2026-10-21',)).fetchall()),1)
            self.assertEqual(len(self.db.execute(sql,('2026-10-22',)).fetchall()),0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM releases').fetchone()[0],4)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM release_events').fetchone()[0],4)

    def test_queries_bounded_even_if_database_contains_many_rows(self):
        for i in range(145):
            self.db.execute('INSERT INTO release_events(release_date,episode_id,event_kind,detail_json,at_utc) VALUES (?,?,?,?,?)',('2026-10-20','x','PLANNED','{}','2026-10-20T00:00:00Z'))
        self.assertEqual(len(self.db.execute(query('events'),('2026-10-20',)).fetchall()),100)

if __name__=='__main__': unittest.main()
