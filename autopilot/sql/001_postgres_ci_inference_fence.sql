-- B3d4c2b2: TEST-ONLY PostgreSQL schema.
-- Apply only to the isolated GitHub Actions CI DB "flowminute_fence_ci".
-- Not a deployment migration. Do not store API keys, prompts or private data.
-- Database owner can still change/delete rows: NOT an immutable production ledger.

CREATE TABLE IF NOT EXISTS fm_owner_inference_days (
    day_ist TEXT PRIMARY KEY CHECK (day_ist ~ '^[0-9]{8}$'),
    owner_id TEXT NOT NULL,
    project_sha256 CHAR(64) NOT NULL,
    provider_id TEXT NOT NULL,
    burned_count INTEGER NOT NULL DEFAULT 0 CHECK (
        burned_count BETWEEN 0 AND 3
    )
);

CREATE TABLE IF NOT EXISTS fm_owner_inference_burns (
    lease_id TEXT PRIMARY KEY,
    episode_id TEXT NOT NULL UNIQUE,
    day_ist TEXT NOT NULL REFERENCES fm_owner_inference_days(day_ist),
    owner_id TEXT NOT NULL,
    project_sha256 CHAR(64) NOT NULL,
    model_id TEXT NOT NULL,
    context_sha256 CHAR(64) NOT NULL,
    anchor_sha256 CHAR(64) NOT NULL,
    token_sha256 CHAR(64) NOT NULL,
    state TEXT NOT NULL CHECK (
        state IN (
            'BURNED_UNCERTAIN_NO_RETRY',
            'MOCK_DRAFT_VALIDATED_NO_RELEASE',
            'MOCK_DRAFT_REJECTED_NO_RETRY'
        )
    ),
    burned_at_utc TIMESTAMPTZ NOT NULL,
    closed_at_utc TIMESTAMPTZ NULL,
    mock_response_sha256 CHAR(64) NULL,
    CONSTRAINT one_mock_closed_state CHECK (
        (state = 'BURNED_UNCERTAIN_NO_RETRY'
            AND closed_at_utc IS NULL
            AND mock_response_sha256 IS NULL)
        OR
        (state != 'BURNED_UNCERTAIN_NO_RETRY'
            AND closed_at_utc IS NOT NULL
            AND mock_response_sha256 IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS fm_mock_burns_day_idx
    ON fm_owner_inference_burns(day_ist);
