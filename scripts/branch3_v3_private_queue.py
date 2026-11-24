"""Durable compute-job journal for CLIVOX V3.

Only repeatable private computation. No credentials, media paths, remote upload,
rights or release authority. Caller owns storage and dispatch authorization.
"""
from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager

STAGES = frozenset(("inspect", "transcribe", "propose", "render", "verify"))
HEX = re.compile(r"[0-9a-f]{64}\Z")
MAX_ATTEMPTS = 3


def digest(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise ValueError("invalid digest")
    return value


def timestamp(value):
    if type(value) is not int or not 0 <= value < 2**62:
        raise ValueError("invalid time")
    return value


class ComputeQueue:
    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("""CREATE TABLE IF NOT EXISTS v3_compute_jobs (
            id INTEGER PRIMARY KEY, stage TEXT NOT NULL, input_digest TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('ready','running','done','held')),
            available INTEGER NOT NULL, generation INTEGER NOT NULL DEFAULT 0,
            attempts INTEGER NOT NULL DEFAULT 0, lease_until INTEGER,
            output_digest TEXT,
            CHECK ((state='running') = (lease_until IS NOT NULL)),
            CHECK ((state='done') = (output_digest IS NOT NULL)),
            UNIQUE(stage,input_digest))""")
        self.db.commit()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    def enqueue(self, stage, input_digest, now):
        if type(stage) is not str or stage not in STAGES:
            raise ValueError("unknown compute stage")
        digest(input_digest)
        timestamp(now)
        with self.transaction():
            self.db.execute("""INSERT OR IGNORE INTO v3_compute_jobs
                (stage,input_digest,state,available) VALUES(?,?,'ready',?)""",
                (stage, input_digest, now))
            return self.db.execute("SELECT id FROM v3_compute_jobs WHERE stage=? AND input_digest=?",
                                   (stage, input_digest)).fetchone()[0]

    def claim(self, now, lease_seconds=300):
        timestamp(now)
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 3600:
            raise ValueError("invalid lease")
        with self.transaction():
            self.db.execute("""UPDATE v3_compute_jobs SET state=CASE WHEN attempts>=?
                THEN 'held' ELSE 'ready' END, lease_until=NULL, available=?
                WHERE state='running' AND lease_until<=?""", (MAX_ATTEMPTS, now, now))
            row = self.db.execute("""SELECT id,stage,input_digest,generation FROM v3_compute_jobs
                WHERE state='ready' AND available<=? ORDER BY available,id LIMIT 1""",
                (now,)).fetchone()
            if row is None:
                return None
            job, stage, source, generation = row
            self.db.execute("""UPDATE v3_compute_jobs SET state='running',
                generation=generation+1, attempts=attempts+1, lease_until=? WHERE id=?""",
                (now + lease_seconds, job))
            return {"id": job, "stage": stage, "input_digest": source,
                    "generation": generation+1}

    def finish(self, job, generation, now, output_digest):
        timestamp(now)
        digest(output_digest)
        if type(job) is not int or type(generation) is not int:
            raise ValueError("invalid lease identity")
        with self.transaction():
            n = self.db.execute("""UPDATE v3_compute_jobs SET state='done',
                output_digest=?, lease_until=NULL WHERE id=? AND generation=?
                AND state='running' AND lease_until>?""",
                (output_digest, job, generation, now)).rowcount
            return n == 1

    def fail(self, job, generation, now):
        timestamp(now)
        if type(job) is not int or type(generation) is not int:
            raise ValueError("invalid lease identity")
        with self.transaction():
            n = self.db.execute("""UPDATE v3_compute_jobs SET state=CASE WHEN attempts>=?
                THEN 'held' ELSE 'ready' END, available=? + attempts*30, lease_until=NULL
                WHERE id=? AND generation=? AND state='running' AND lease_until>?""",
                (MAX_ATTEMPTS, now, job, generation, now)).rowcount
            return n == 1

    def counts(self):
        result = dict.fromkeys(("ready", "running", "done", "held"), 0)
        result.update(self.db.execute("SELECT state,count(*) FROM v3_compute_jobs GROUP BY state"))
        return result
