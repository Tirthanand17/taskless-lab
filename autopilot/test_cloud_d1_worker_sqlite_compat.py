"""Cross-language SQL smoke: run actual Worker candidate SQL in SQLite RAM.

The Worker .mjs interface itself is exercised by Node's built-in test runner.
This test independently parses its constant SQL arrays and executes the
exact statement bytes on a fresh disposable SQLite ':memory:' database.
Cloudflare D1 may behave differently; this is NOT a live provider proof.
"""
from pathlib import Path
import ast
import re
import sqlite3
import unittest

SOURCE = Path(__file__).with_name("cloud_d1_worker_candidate.mjs")
LEASE_DDL = """CREATE TABLE fm_release_writer_lease(
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    owner_nonce TEXT NOT NULL DEFAULT '',
    fence_epoch INTEGER NOT NULL DEFAULT 0,
    expires_at_unix INTEGER NOT NULL DEFAULT 0,
    last_checked_unix INTEGER NOT NULL DEFAULT 0
)"""
RELEASE_DDL = """CREATE TABLE fm_writer_release_shadow(
    release_date TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    media_sha256 TEXT NOT NULL,
    stage TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    PRIMARY KEY(release_date,episode_id)
)"""


def candidate_sql(name:str)->str:
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(
        rf"\b{name}:\s*\[(.*?)\]\.join\(\" \"\)",
        source, flags=re.DOTALL,
    )
    if not match:
        raise AssertionError("D1 Worker candidate SQL constant unavailable")
    fragments = re.findall(r'"[^"\n]*"', match.group(1))
    if not 3 <= len(fragments) <= 20:
        raise AssertionError("D1 SQL fragment count changed")
    values = [ast.literal_eval(text) for text in fragments]
    if any(not isinstance(x, str) for x in values):
        raise AssertionError("D1 SQL fragment is not a string")
    return " ".join(values)


class CrossLanguageWorkerCASModelTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:",isolation_level=None)
        self.addCleanup(self.db.close)
        self.db.execute(LEASE_DDL)
        self.db.execute(RELEASE_DDL)
        self.db.execute(
            "INSERT INTO fm_release_writer_lease VALUES(1,'',0,0,0)"
        )
        self.db.execute(
            "INSERT INTO fm_writer_release_shadow VALUES(?,?,?,?,?)",
            ("2026-10-20","tutorial_short_en","a"*64,"media_qa_passed",""),
        )

    def test_all_three_worker_sql_constants_parse_and_use_server_time(self):
        for operation in ("claim","renew","reserve"):
            statement=candidate_sql(operation)
            with self.subTest(operation=operation):
                self.assertTrue(statement.startswith("UPDATE "))
                self.assertIn("unixepoch('now')",statement)
                self.assertNotIn("INSERT INTO",statement)
                self.assertNotIn("DROP TABLE",statement)
                self.assertLess(len(statement),1500)
                # SQLite EXPLAIN prepares real byte-identical statements.
                params={"claim":("A"*32,60,0),
                        "renew":(60,"A"*32,1),
                        "reserve":("2026-10-20","tutorial_short_en",
                                   "a"*64,"A"*32,1)}[operation]
                self.db.execute("EXPLAIN "+statement,params).fetchall()

    def test_actual_sql_fences_competitor_and_duplicate_reservation(self):
        claim=candidate_sql("claim")
        renew=candidate_sql("renew")
        reserve=candidate_sql("reserve")
        a="A"*32
        b="B"*32
        self.assertEqual(self.db.execute(claim,(a,60,0)).rowcount,1)
        self.assertEqual(self.db.execute(claim,(b,60,0)).rowcount,0)
        self.assertEqual(self.db.execute(renew,(60,b,1)).rowcount,0)
        self.assertEqual(self.db.execute(renew,(60,a,1)).rowcount,1)
        self.assertEqual(self.db.execute(reserve,(
            "2026-10-20","tutorial_short_en","a"*64,b,1,
        )).rowcount,0)
        self.assertEqual(self.db.execute(reserve,(
            "2026-10-20","tutorial_short_en","b"*64,a,1,
        )).rowcount,0)
        self.assertEqual(self.db.execute(reserve,(
            "2026-10-20","tutorial_short_en","a"*64,a,1,
        )).rowcount,1)
        self.assertEqual(self.db.execute(reserve,(
            "2026-10-20","tutorial_short_en","a"*64,a,1,
        )).rowcount,0)
        stage=self.db.execute(
            "SELECT stage FROM fm_writer_release_shadow"
        ).fetchone()
        self.assertEqual(stage,("upload_started",))

    def test_expired_epoch_denies_claim_on_stale_token_or_wrong_stage(self):
        claim=candidate_sql("claim")
        reserve=candidate_sql("reserve")
        now=self.db.execute("SELECT unixepoch('now')").fetchone()[0]
        self.db.execute(
            "UPDATE fm_release_writer_lease SET fence_epoch=4,"
            "owner_nonce=?,expires_at_unix=?,last_checked_unix=?",
            ("A"*32,now-1,now-1),
        )
        self.assertEqual(self.db.execute(claim,("B"*32,10,3)).rowcount,0)
        self.assertEqual(self.db.execute(claim,("B"*32,60,4)).rowcount,1)
        self.assertEqual(self.db.execute(reserve,(
            "2026-10-20","tutorial_short_en","a"*64,"A"*32,4
        )).rowcount,0)
        self.assertEqual(self.db.execute(reserve,(
            "2026-10-20","tutorial_short_en","a"*64,"B"*32,5
        )).rowcount,1)
        self.db.execute(
            "UPDATE fm_writer_release_shadow SET stage='upload_started'"
        )
        self.assertEqual(self.db.execute(reserve,(
            "2026-10-20","tutorial_short_en","a"*64,"B"*32,5
        )).rowcount,0)


if __name__=="__main__":
    unittest.main()
