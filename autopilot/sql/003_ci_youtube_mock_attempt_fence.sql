-- Branch 2 B4b1: PostgreSQL 16 CI-ONLY durable, one-shot YouTube intent fence.
-- Requires the disposable roles/private schema from 002_ci_least_privilege_ledger.sql.
-- No real owner approval, OAuth, YouTube inserts, production DB or publisher.
-- This migration MUST NEVER be run on real systems. CI mock state only.
BEGIN;
SET ROLE fm_ci_owner;

CREATE TABLE fm_private_ci.youtube_mock_attempts (
    channel_id TEXT NOT NULL CHECK (channel_id ~ '^UC[A-Za-z0-9_-]{22}$'),
    episode_id TEXT NOT NULL CHECK (episode_id ~ '^[A-Za-z0-9_-]{8,100}$'),
    slot TEXT NOT NULL CHECK (slot IN ('short_am','long','short_pm')),
    publish_at TIMESTAMPTZ NOT NULL,
    intent_context_sha256 TEXT NOT NULL CHECK (intent_context_sha256 ~ '^[0-9a-f]{64}$'),
    mp4_sha256 TEXT NOT NULL CHECK (mp4_sha256 ~ '^[0-9a-f]{64}$'),
    srt_sha256 TEXT NOT NULL CHECK (srt_sha256 ~ '^[0-9a-f]{64}$'),
    thumbnail_sha256 TEXT NOT NULL CHECK (thumbnail_sha256 ~ '^[0-9a-f]{64}$'),
    reviewed_source_sha256 TEXT NOT NULL CHECK (reviewed_source_sha256 ~ '^[0-9a-f]{64}$'),
    ephemeral_token_sha256 TEXT NOT NULL CHECK (ephemeral_token_sha256 ~ '^[0-9a-f]{64}$'),
    state TEXT NOT NULL DEFAULT 'POSSIBLY_SENT_NO_RETRY'
      CHECK (state IN ('POSSIBLY_SENT_NO_RETRY','REMOTE_ID_REPORTED_UNVERIFIED')),
    remote_video_id TEXT UNIQUE CHECK (remote_video_id IS NULL OR remote_video_id ~ '^[A-Za-z0-9_-]{11}$'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    remote_id_reported_at TIMESTAMPTZ,
    PRIMARY KEY (channel_id, episode_id),
    UNIQUE (channel_id, publish_at),
    UNIQUE (channel_id, intent_context_sha256),
    UNIQUE (channel_id, mp4_sha256),
    CONSTRAINT youtube_mock_state_consistency CHECK (
       (state='POSSIBLY_SENT_NO_RETRY' AND remote_video_id IS NULL AND remote_id_reported_at IS NULL)
       OR (state='REMOTE_ID_REPORTED_UNVERIFIED'
            AND remote_video_id IS NOT NULL AND remote_id_reported_at IS NOT NULL)
    )
);

CREATE TABLE fm_private_ci.youtube_mock_audit (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_id TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    event_name TEXT NOT NULL CHECK (event_name IN ('FENCED_BEFORE_NETWORK','UNVERIFIED_REMOTE_ID')),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (channel_id, episode_id)
       REFERENCES fm_private_ci.youtube_mock_attempts(channel_id,episode_id)
);

CREATE FUNCTION fm_private_ci.reserve_youtube_mock_once(
    p_channel TEXT, p_episode TEXT, p_slot TEXT, p_publish_at TIMESTAMPTZ,
    p_context_sha TEXT, p_mp4_sha TEXT, p_srt_sha TEXT,
    p_thumbnail_sha TEXT, p_reviewed_source_sha TEXT, p_token_sha TEXT
) RETURNS TEXT LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, fm_private_ci, pg_temp
AS $function$
DECLARE
    v_ist_time TIME WITHOUT TIME ZONE;
    v_required TIME WITHOUT TIME ZONE;
BEGIN
    IF session_user <> 'fm_ci_gateway' THEN
       RAISE EXCEPTION 'CI mock gateway role required' USING ERRCODE='42501';
    END IF;
    IF p_channel IS NULL OR p_channel !~ '^UC[A-Za-z0-9_-]{22}$'
       OR p_episode IS NULL OR p_episode !~ '^[A-Za-z0-9_-]{8,100}$'
       OR p_slot IS NULL OR p_slot NOT IN ('short_am','long','short_pm')
       OR p_publish_at IS NULL
       OR p_context_sha IS NULL OR p_context_sha !~ '^[0-9a-f]{64}$'
       OR p_mp4_sha IS NULL OR p_mp4_sha !~ '^[0-9a-f]{64}$'
       OR p_srt_sha IS NULL OR p_srt_sha !~ '^[0-9a-f]{64}$'
       OR p_thumbnail_sha IS NULL OR p_thumbnail_sha !~ '^[0-9a-f]{64}$'
       OR p_reviewed_source_sha IS NULL OR p_reviewed_source_sha !~ '^[0-9a-f]{64}$'
       OR p_token_sha IS NULL OR p_token_sha !~ '^[0-9a-f]{64}$'
    THEN
       RAISE EXCEPTION 'Invalid CI-only upload intent' USING ERRCODE='22023';
    END IF;
    v_required := CASE p_slot
       WHEN 'short_am' THEN '11:00:00'::TIME
       WHEN 'long' THEN '16:00:00'::TIME
       WHEN 'short_pm' THEN '20:30:00'::TIME
       END;
    v_ist_time := (p_publish_at AT TIME ZONE 'Asia/Kolkata')::TIME;
    IF v_ist_time <> v_required OR p_publish_at <= clock_timestamp() + INTERVAL '15 minutes' THEN
       RAISE EXCEPTION 'Wrong or expired future IST slot' USING ERRCODE='22023';
    END IF;
    -- UNIQUE indexes are the cross-connection exclusive CAS boundary.
    -- Failure is *terminal*: caller cannot issue videos.insert after any error.
    INSERT INTO fm_private_ci.youtube_mock_attempts (
        channel_id,episode_id,slot,publish_at,intent_context_sha256,
        mp4_sha256,srt_sha256,thumbnail_sha256,reviewed_source_sha256,
        ephemeral_token_sha256,state
    ) VALUES (
        p_channel,p_episode,p_slot,p_publish_at,p_context_sha,
        p_mp4_sha,p_srt_sha,p_thumbnail_sha,p_reviewed_source_sha,
        p_token_sha,'POSSIBLY_SENT_NO_RETRY'
    );
    INSERT INTO fm_private_ci.youtube_mock_audit(channel_id,episode_id,event_name)
    VALUES (p_channel,p_episode,'FENCED_BEFORE_NETWORK');
    RETURN 'POSSIBLY_SENT_NO_RETRY';
END;
$function$;

CREATE FUNCTION fm_private_ci.note_youtube_mock_remote_id_once(
    p_channel TEXT, p_episode TEXT, p_token_sha TEXT, p_remote_id TEXT
) RETURNS TEXT LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, fm_private_ci, pg_temp
AS $function$
DECLARE
    v_new TEXT;
BEGIN
    IF session_user <> 'fm_ci_gateway' THEN
       RAISE EXCEPTION 'CI mock gateway role required' USING ERRCODE='42501';
    END IF;
    IF p_channel IS NULL OR p_episode IS NULL OR p_token_sha IS NULL
       OR p_token_sha !~ '^[0-9a-f]{64}$'
       OR p_remote_id IS NULL OR p_remote_id !~ '^[A-Za-z0-9_-]{11}$'
    THEN
       RAISE EXCEPTION 'Missing exact mock id/secret' USING ERRCODE='22023';
    END IF;
    UPDATE fm_private_ci.youtube_mock_attempts
       SET state='REMOTE_ID_REPORTED_UNVERIFIED',
           remote_video_id=p_remote_id,remote_id_reported_at=clock_timestamp()
     WHERE channel_id=p_channel AND episode_id=p_episode
       AND ephemeral_token_sha256=p_token_sha
       AND state='POSSIBLY_SENT_NO_RETRY'
       AND remote_video_id IS NULL
     RETURNING state INTO v_new;
    IF v_new IS NULL THEN
       RAISE EXCEPTION 'Unknown/replayed or forged mock remote-id report' USING ERRCODE='42501';
    END IF;
    INSERT INTO fm_private_ci.youtube_mock_audit(channel_id,episode_id,event_name)
    VALUES (p_channel,p_episode,'UNVERIFIED_REMOTE_ID');
    RETURN v_new;
END;
$function$;

CREATE FUNCTION fm_private_ci.inspect_youtube_mock_attempt(
    p_channel TEXT,p_episode TEXT
) RETURNS TABLE(
    channel_id TEXT,episode_id TEXT,slot TEXT,
    planned_utc TIMESTAMPTZ,state TEXT,unverified_remote_video_id TEXT,
    attempt_count INTEGER,audit_event_count BIGINT
) LANGUAGE sql SECURITY DEFINER
SET search_path = pg_catalog, fm_private_ci, pg_temp
AS $function$
    SELECT x.channel_id,x.episode_id,x.slot,x.publish_at,x.state,
           x.remote_video_id,1::INTEGER,COUNT(a.event_id)
      FROM fm_private_ci.youtube_mock_attempts x
      JOIN fm_private_ci.youtube_mock_audit a
        ON (a.channel_id=x.channel_id AND a.episode_id=x.episode_id)
     WHERE x.channel_id=p_channel AND x.episode_id=p_episode
     GROUP BY x.channel_id,x.episode_id,x.slot,x.publish_at,
              x.state,x.remote_video_id;
$function$;

-- Never grant tables, secret hash, or write access to runtime roles.
REVOKE ALL ON fm_private_ci.youtube_mock_attempts FROM PUBLIC;
REVOKE ALL ON fm_private_ci.youtube_mock_audit FROM PUBLIC;
REVOKE ALL ON SEQUENCE fm_private_ci.youtube_mock_audit_event_id_seq FROM PUBLIC;
REVOKE ALL ON FUNCTION fm_private_ci.reserve_youtube_mock_once(
    TEXT,TEXT,TEXT,TIMESTAMPTZ,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION fm_private_ci.note_youtube_mock_remote_id_once(
    TEXT,TEXT,TEXT,TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION fm_private_ci.inspect_youtube_mock_attempt(TEXT,TEXT) FROM PUBLIC;
RESET ROLE;

GRANT EXECUTE ON FUNCTION fm_private_ci.reserve_youtube_mock_once(
    TEXT,TEXT,TEXT,TIMESTAMPTZ,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT) TO fm_ci_gateway;
GRANT EXECUTE ON FUNCTION fm_private_ci.note_youtube_mock_remote_id_once(
    TEXT,TEXT,TEXT,TEXT) TO fm_ci_gateway;
GRANT EXECUTE ON FUNCTION fm_private_ci.inspect_youtube_mock_attempt(TEXT,TEXT)
    TO fm_ci_gateway,fm_ci_auditor;
COMMIT;
