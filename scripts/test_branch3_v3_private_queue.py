import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.branch3_v3_private_queue import ComputeQueue

A, B = "a"*64, "b"*64


class QueueTests(unittest.TestCase):
    def test_restart_reclaims_expired_lease_and_rejects_stale_worker(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "private.sqlite"
            db = sqlite3.connect(path)
            q = ComputeQueue(db)
            job = q.enqueue("propose", A, 1)
            self.assertEqual(q.enqueue("propose", A, 2), job)
            old = q.claim(2, 5)
            db.close()
            db = sqlite3.connect(path)
            q = ComputeQueue(db)
            new = q.claim(7, 5)
            self.assertEqual(new["id"], job)
            self.assertGreater(new["generation"], old["generation"])
            self.assertFalse(q.finish(job, old["generation"], 8, B))
            self.assertTrue(q.finish(job, new["generation"], 8, B))
            self.assertFalse(q.finish(job, new["generation"], 8, B))
            self.assertEqual(q.counts()["done"], 1)
            self.assertIsNone(q.claim(100))
            db.close()

    def test_failure_and_backoff_then_hold(self):
        with sqlite3.connect(":memory:") as db:
            q = ComputeQueue(db)
            job = q.enqueue("render", A, 0)
            for t in (0, 30, 90):
                lease = q.claim(t)
                self.assertTrue(q.fail(job, lease["generation"], t))
                self.assertIsNone(q.claim(t+1))
            self.assertEqual(q.counts()["held"], 1)
            self.assertIsNone(q.claim(10000))

    def test_disallows_upload_and_bad_values(self):
        with sqlite3.connect(":memory:") as db:
            q = ComputeQueue(db)
            for stage, digest, now in (("upload", A, 0), ("render", "not-a-hash", 0),
                                       ("render", A, True)):
                with self.assertRaises(ValueError):
                    q.enqueue(stage, digest, now)
            self.assertEqual(q.counts()["ready"], 0)

    def test_expired_completion_denied_even_before_reclaim(self):
        with sqlite3.connect(":memory:") as db:
            q = ComputeQueue(db)
            job = q.enqueue("verify", A, 0)
            lease = q.claim(0, 1)
            self.assertFalse(q.finish(job, lease["generation"], 1, B))
            self.assertFalse(q.fail(job, lease["generation"], 1))
            self.assertEqual(q.claim(1)["generation"], 2)


if __name__ == "__main__":
    unittest.main()
