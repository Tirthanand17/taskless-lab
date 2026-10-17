"""Offline-only regression fixtures; no Cloudflare or YouTube activity."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from autopilot.core import CHANNEL_ID
from autopilot.phase4b_readonly_audit import (
    AuditBlocked, inspect_local_schema_only, known_ledger_compatibility,
    reconcile_claimed_releases,
)

TIME="2026-10-20T05:30:00+00:00"
SHA="a"*64
VID="abc123def45"

def claim(**kw):
    item=dict(source="private_sqlite_claim",channel_id=CHANNEL_ID,
              episode_id="ep_01",stage="planned",media_sha256=SHA,
              youtube_id=VID,planned_utc=TIME)
    item.update(kw)
    return item

class Phase4BReadOnlyAuditTests(unittest.TestCase):
    def make_db(self, ddl, values=None):
        folder=tempfile.TemporaryDirectory()
        p=Path(folder.name)/"fixture.sqlite"
        db=sqlite3.connect(p)
        db.executescript(ddl)
        if values:
            for sql, args in values:
                db.execute(sql,args)
        db.commit();db.close()
        self.addCleanup(folder.cleanup)
        return p

    def test_inspector_only_reports_schema_never_ciphertext(self):
        secret="ENCRYPTED_GRANT_BYTES_MUST_NEVER_LEAK_123"
        p=self.make_db("""CREATE TABLE releases (release_date TEXT, episode_id TEXT,
                            stage TEXT, youtube_id TEXT, UNIQUE(youtube_id));
                          CREATE TABLE oauth_grant (encrypted_access_token TEXT);""",
                       [("INSERT INTO oauth_grant VALUES (?)",(secret,))])
        before=p.read_bytes()
        result=inspect_local_schema_only(p)
        self.assertNotIn(secret,str(result))
        self.assertNotIn("oauth_grant",str(result))
        self.assertEqual(result["protected_object_count"],1)
        self.assertIn("private_sqlite_v1",known_ledger_compatibility(result)["recognized_local_shapes"])
        self.assertEqual(p.read_bytes(),before)
        self.assertFalse(result["verified_production_d1"])
        self.assertFalse(result["migration_authorized"])

    def test_missing_path_never_creates_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"missing.sqlite"
            with self.assertRaises(FileNotFoundError):
                inspect_local_schema_only(path)
            self.assertFalse(path.exists())

    def test_schema_names_with_quotes_are_escaped(self):
        p=self.make_db('CREATE TABLE "look""up" ("name" TEXT);')
        result=inspect_local_schema_only(p)
        self.assertEqual(result["objects"][0]["columns"],["name"])

    def test_no_sqlite_dml_allowed_on_own_connection(self):
        p=self.make_db("CREATE TABLE releases (episode TEXT)")
        schema=inspect_local_schema_only(p)
        self.assertFalse(schema["contains_data_rows"])
        db=sqlite3.connect(p.as_uri()+"?mode=ro",uri=True)
        with self.assertRaises(sqlite3.OperationalError):
            db.execute("INSERT INTO releases VALUES('bad')")
        db.close()

    def test_bounded_object_inventory(self):
        p=self.make_db("CREATE TABLE a (x INT); CREATE TABLE b (x INT);")
        with self.assertRaises(AuditBlocked):
            inspect_local_schema_only(p,max_objects=1)

    def test_unknown_ledger_layout_blocks(self):
        p=self.make_db("CREATE TABLE other (id INTEGER)")
        r=known_ledger_compatibility(inspect_local_schema_only(p))
        self.assertIn("UNKNOWN_OR_AMBIGUOUS_LOCAL_LEDGER_LAYOUT",r["blockers"])
        self.assertFalse(r["production_migration_ready"])

    def test_public_draft_ledger_metadata_recognized(self):
        p=self.make_db("CREATE TABLE releases (episode TEXT,kind TEXT,planned_utc TEXT,stage TEXT,channel TEXT)")
        r=known_ledger_compatibility(inspect_local_schema_only(p))
        self.assertEqual(r["recognized_local_shapes"],["public_draft_v1"])

    def test_malicious_claimed_remote_is_never_authoritative(self):
        report=reconcile_claimed_releases([claim(source="youtube_claim",stage="public_verified")])
        self.assertFalse(report["safe_to_migrate"])
        self.assertFalse(report["safe_to_publish"])
        self.assertIn("UNTRUSTED_CALLER_SUPPLIED_OBSERVATIONS_NOT_PRODUCTION_EVIDENCE",report["blockers"])

    def test_consistent_two_records_report_no_conflict(self):
        r=reconcile_claimed_releases([claim(),claim(source="public_draft_claim")])
        self.assertEqual(r["conflicts"],[])
        self.assertEqual(r["release_count"],1)
        self.assertFalse(r["safe_to_migrate"])

    def test_same_episode_conflicting_id_is_blocked(self):
        r=reconcile_claimed_releases([claim(),claim(source="d1_claim",youtube_id="ZZZ123abc45")])
        self.assertIn("REMOTE_VIDEO_ID_MISMATCH",[x["problem"] for x in r["conflicts"]])

    def test_same_episode_conflicting_hash_blocked(self):
        r=reconcile_claimed_releases([claim(),claim(source="d1_claim",media_sha256="b"*64)])
        self.assertIn("MEDIA_HASH_MISMATCH",[x["problem"] for x in r["conflicts"]])

    def test_same_episode_conflicting_schedule_blocked(self):
        r=reconcile_claimed_releases([claim(),claim(source="d1_claim",planned_utc="2026-10-20T05:31:00+00:00")])
        self.assertIn("SCHEDULE_SLOT_MISMATCH",[x["problem"] for x in r["conflicts"]])

    def test_cross_episode_duplicate_video_id_blocked(self):
        r=reconcile_claimed_releases([claim(),claim(episode_id="ep_02",planned_utc="2026-10-21T05:30:00+00:00")])
        self.assertIn("REMOTE_ID_SHARED_BY_DIFFERENT_EPISODES",[x["problem"] for x in r["conflicts"]])

    def test_cross_episode_duplicate_slot_blocked(self):
        r=reconcile_claimed_releases([claim(),claim(episode_id="ep_02",youtube_id="abc123def46")])
        self.assertIn("SLOT_SHARED_BY_DIFFERENT_EPISODES",[x["problem"] for x in r["conflicts"]])

    def test_published_without_video_id_blocked(self):
        r=reconcile_claimed_releases([claim(stage="public_verified",youtube_id=None)])
        self.assertIn("REMOTE_STATE_WITHOUT_VIDEO_ID",[x["problem"] for x in r["conflicts"]])

    def test_invalid_timestamp_or_wrong_channel_rejected(self):
        for row in (claim(planned_utc="2026-10-20T11:00:00+05:30"),claim(channel_id="WRONG"),claim(media_sha256="no")):
            with self.assertRaises(AuditBlocked):
                reconcile_claimed_releases([row])

    def test_empty_claims_blocked(self):
        r=reconcile_claimed_releases([])
        self.assertIn("NO_RELEASE_OBSERVATIONS",r["blockers"])

    def test_protected_column_name_is_redacted(self):
        p=self.make_db("CREATE TABLE releases (episode TEXT, access_token TEXT, stage TEXT)")
        r=inspect_local_schema_only(p)
        self.assertNotIn("access_token",str(r))
        self.assertIn("protected_column",str(r))

if __name__ == '__main__':
    unittest.main()
