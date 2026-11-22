-- Reference schema for repeatable media computation on a single private worker host.
-- Application opens the database on local encrypted storage and enables foreign keys per connection.
PRAGMA foreign_keys = ON;

CREATE TABLE compute_job (
    id INTEGER PRIMARY KEY,
    stage TEXT NOT NULL CHECK (stage IN ('inspect', 'transcribe', 'propose', 'render', 'verify')),
    input_digest TEXT NOT NULL CHECK (length(input_digest) = 64 AND input_digest NOT GLOB '*[^0-9a-f]*'),
    state TEXT NOT NULL DEFAULT 'ready' CHECK (state IN ('ready', 'running', 'done', 'held')),
    available_at INTEGER NOT NULL DEFAULT 0,
    lease_generation INTEGER NOT NULL DEFAULT 0 CHECK (lease_generation >= 0),
    lease_until INTEGER,
    result_digest TEXT CHECK (result_digest IS NULL OR
        (length(result_digest) = 64 AND result_digest NOT GLOB '*[^0-9a-f]*')),
    CHECK ((state = 'running') = (lease_until IS NOT NULL)),
    CHECK ((state = 'done') = (result_digest IS NOT NULL)),
    UNIQUE (stage, input_digest)
);

CREATE INDEX compute_job_ready ON compute_job (state, available_at, id);

-- The private dispatcher consumes one completion per job. A repeated delivery may occur
-- between enqueue and acknowledgement. The next compute job has its own stable unique key.
CREATE TABLE compute_completion (
    job_id INTEGER PRIMARY KEY REFERENCES compute_job (id),
    delivered_at INTEGER
);
