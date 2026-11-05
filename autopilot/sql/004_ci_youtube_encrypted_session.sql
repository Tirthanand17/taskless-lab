-- B4b3 CI-only encrypted upload-session checkpoint, for disposable postgres:16.
-- Relies on 002 CI private roles and 003 single-attempt fence; NEVER production.
-- Bytes are supplied already AES-GCM encrypted by the mock gateway. No URI,
-- decryption key, OAuth credentials, or real YouTube calls may enter this DB.
BEGIN;
SET ROLE fm_ci_owner;

CREATE TABLE fm_private_ci.youtube_mock_session_envelopes (
    channel_id TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    intent_context_sha256 TEXT NOT NULL CHECK (intent_context_sha256 ~ '^[0-9a-f]{64}$'),
    mp4_sha256 TEXT NOT NULL CHECK (mp4_sha256 ~ '^[0-9a-f]{64}$'),
    total_bytes BIGINT NOT NULL CHECK (total_bytes > 0 AND total_bytes <= 256000000000),
    encryption_version SMALLINT NOT NULL CHECK (encryption_version = 1),
    key_version TEXT NOT NULL CHECK (key_version ~ '^ci_v[0-9]{1,2}$'),
    nonce BYTEA NOT NULL CHECK (octet_length(nonce) = 12),
    ciphertext BYTEA NOT NULL CHECK (
        octet_length(ciphertext) >= 32 AND octet_length(ciphertext) <= 4096),
    aad_sha256 TEXT NOT NULL CHECK (aad_sha256 ~ '^[0-9a-f]{64}$'),
    mock_handle_sha256 TEXT NOT NULL CHECK (mock_handle_sha256 ~ '^[0-9a-f]{64}$'),
    sealed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (channel_id, episode_id),
    CONSTRAINT b4b3_attempt FOREIGN KEY (channel_id, episode_id)
       REFERENCES fm_private_ci.youtube_mock_attempts(channel_id, episode_id),
    CONSTRAINT b4b3_unique_key_nonce UNIQUE (key_version, nonce)
);
CREATE TABLE fm_private_ci.youtube_mock_session_audit (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_id TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('SEALED_BEFORE_ANY_TRANSFER', 'MOCK_GATEWAY_RETRIEVAL')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT b4b3_session_audit_fk FOREIGN KEY (channel_id, episode_id)
       REFERENCES fm_private_ci.youtube_mock_session_envelopes(channel_id, episode_id)
);

CREATE FUNCTION fm_private_ci.seal_youtube_mock_session_once(
    p_channel TEXT, p_episode TEXT, p_token_hash TEXT,
    p_context_hash TEXT, p_mp4_hash TEXT, p_total_bytes BIGINT,
    p_key_version TEXT, p_nonce BYTEA, p_ciphertext BYTEA,
    p_aad_hash TEXT, p_mock_handle_hash TEXT
) RETURNS TEXT LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, fm_private_ci, pg_temp
AS $body$
DECLARE
    v_matched INTEGER;
BEGIN
    IF session_user <> 'fm_ci_gateway' THEN
        RAISE EXCEPTION 'Only isolated mock gateway can seal' USING ERRCODE='42501';
    END IF;
    IF p_channel IS NULL OR p_channel !~ '^UC[A-Za-z0-9_-]{22}$'
       OR p_episode IS NULL OR p_episode !~ '^[A-Za-z0-9_-]{8,100}$'
       OR p_token_hash IS NULL OR p_token_hash !~ '^[0-9a-f]{64}$'
       OR p_context_hash IS NULL OR p_context_hash !~ '^[0-9a-f]{64}$'
       OR p_mp4_hash IS NULL OR p_mp4_hash !~ '^[0-9a-f]{64}$'
       OR p_total_bytes IS NULL OR p_total_bytes <= 0 OR p_total_bytes > 256000000000
       OR p_key_version IS NULL OR p_key_version !~ '^ci_v[0-9]{1,2}$'
       OR p_nonce IS NULL OR octet_length(p_nonce) <> 12
       OR p_ciphertext IS NULL OR octet_length(p_ciphertext) NOT BETWEEN 32 AND 4096
       OR p_aad_hash IS NULL OR p_aad_hash !~ '^[0-9a-f]{64}$'
       OR p_mock_handle_hash IS NULL OR p_mock_handle_hash !~ '^[0-9a-f]{64}$'
    THEN
        RAISE EXCEPTION 'Malformed or unapproved synthetic envelope' USING ERRCODE='22023';
    END IF;
    -- Lock existing one-shot B4b1 attempt, never create/release another one.
    SELECT 1 INTO v_matched
      FROM fm_private_ci.youtube_mock_attempts a
     WHERE a.channel_id=p_channel
       AND a.episode_id=p_episode
       AND a.ephemeral_token_sha256=p_token_hash
       AND a.intent_context_sha256=p_context_hash
       AND a.mp4_sha256=p_mp4_hash
       AND a.state='POSSIBLY_SENT_NO_RETRY'
       AND a.remote_video_id IS NULL
     FOR UPDATE;
    IF v_matched IS DISTINCT FROM 1 THEN
       RAISE EXCEPTION 'No exact existing unreported fenced attempt'
         USING ERRCODE='42501';
    END IF;
    INSERT INTO fm_private_ci.youtube_mock_session_envelopes (
        channel_id,episode_id,intent_context_sha256,mp4_sha256,
        total_bytes,encryption_version,key_version,nonce,ciphertext,
        aad_sha256,mock_handle_sha256
    ) VALUES (
        p_channel,p_episode,p_context_hash,p_mp4_hash,
        p_total_bytes,1,p_key_version,p_nonce,p_ciphertext,
        p_aad_hash,p_mock_handle_hash
    );
    INSERT INTO fm_private_ci.youtube_mock_session_audit(channel_id,episode_id,action)
    VALUES(p_channel,p_episode,'SEALED_BEFORE_ANY_TRANSFER');
    RETURN 'CI_MOCK_ENCRYPTED_SESSION_SEALED_NO_RELEASE';
END;
$body$;

CREATE FUNCTION fm_private_ci.retrieve_youtube_mock_session(
    p_channel TEXT, p_episode TEXT, p_token_hash TEXT,
    p_context_hash TEXT, p_mp4_hash TEXT
) RETURNS TABLE (
    saved_context_sha256 TEXT, saved_mp4_sha256 TEXT, media_size BIGINT,
    saved_key_version TEXT, saved_nonce BYTEA, saved_ciphertext BYTEA,
    saved_aad_sha256 TEXT, saved_mock_handle_sha256 TEXT
) LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, fm_private_ci, pg_temp
AS $body$
BEGIN
    IF session_user <> 'fm_ci_gateway' THEN
       RAISE EXCEPTION 'Only isolated mock gateway can retrieve ciphertext'
         USING ERRCODE='42501';
    END IF;
    IF p_channel IS NULL OR p_episode IS NULL
       OR p_token_hash IS NULL OR p_token_hash !~ '^[0-9a-f]{64}$'
       OR p_context_hash IS NULL OR p_context_hash !~ '^[0-9a-f]{64}$'
       OR p_mp4_hash IS NULL OR p_mp4_hash !~ '^[0-9a-f]{64}$'
    THEN
       RAISE EXCEPTION 'Missing scoped synthetic ticket' USING ERRCODE='22023';
    END IF;
    -- FOR UPDATE prevents read/complete race on same existing attempt.
    PERFORM 1 FROM fm_private_ci.youtube_mock_attempts a
     WHERE a.channel_id=p_channel AND a.episode_id=p_episode
       AND a.ephemeral_token_sha256=p_token_hash
       AND a.intent_context_sha256=p_context_hash
       AND a.mp4_sha256=p_mp4_hash
       AND a.state='POSSIBLY_SENT_NO_RETRY'
     FOR UPDATE;
    IF NOT FOUND THEN
       RAISE EXCEPTION 'Unknown/modified/reported attempt' USING ERRCODE='42501';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM fm_private_ci.youtube_mock_session_envelopes s
                   WHERE s.channel_id=p_channel AND s.episode_id=p_episode
                     AND s.intent_context_sha256=p_context_hash
                     AND s.mp4_sha256=p_mp4_hash) THEN
       RAISE EXCEPTION 'No sealed checkpoint: do not start new session'
         USING ERRCODE='42501';
    END IF;
    INSERT INTO fm_private_ci.youtube_mock_session_audit(channel_id,episode_id,action)
    VALUES (p_channel,p_episode,'MOCK_GATEWAY_RETRIEVAL');

    RETURN QUERY
      SELECT s.intent_context_sha256,s.mp4_sha256,s.total_bytes,
             s.key_version,s.nonce,s.ciphertext,s.aad_sha256,s.mock_handle_sha256
        FROM fm_private_ci.youtube_mock_session_envelopes s
       WHERE s.channel_id=p_channel AND s.episode_id=p_episode;
END;
$body$;

CREATE FUNCTION fm_private_ci.inspect_youtube_mock_session(
    p_channel TEXT,p_episode TEXT
) RETURNS TABLE(sealed BOOLEAN, event_count BIGINT, encrypted_version SMALLINT)
LANGUAGE sql SECURITY DEFINER
SET search_path = pg_catalog, fm_private_ci, pg_temp
AS $body$
    SELECT TRUE, COUNT(a.event_id)::BIGINT, s.encryption_version
      FROM fm_private_ci.youtube_mock_session_envelopes s
      JOIN fm_private_ci.youtube_mock_session_audit a
       ON s.channel_id=a.channel_id AND s.episode_id=a.episode_id
     WHERE s.channel_id=p_channel AND s.episode_id=p_episode
     GROUP BY s.encryption_version;
$body$;

REVOKE ALL ON fm_private_ci.youtube_mock_session_envelopes FROM PUBLIC;
REVOKE ALL ON fm_private_ci.youtube_mock_session_audit FROM PUBLIC;
REVOKE ALL ON SEQUENCE fm_private_ci.youtube_mock_session_audit_event_id_seq FROM PUBLIC;
REVOKE ALL ON FUNCTION fm_private_ci.seal_youtube_mock_session_once(
    TEXT,TEXT,TEXT,TEXT,TEXT,BIGINT,TEXT,BYTEA,BYTEA,TEXT,TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION fm_private_ci.retrieve_youtube_mock_session(
    TEXT,TEXT,TEXT,TEXT,TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION fm_private_ci.inspect_youtube_mock_session(TEXT,TEXT) FROM PUBLIC;
RESET ROLE;

GRANT EXECUTE ON FUNCTION fm_private_ci.seal_youtube_mock_session_once(
    TEXT,TEXT,TEXT,TEXT,TEXT,BIGINT,TEXT,BYTEA,BYTEA,TEXT,TEXT) TO fm_ci_gateway;
GRANT EXECUTE ON FUNCTION fm_private_ci.retrieve_youtube_mock_session(
    TEXT,TEXT,TEXT,TEXT,TEXT) TO fm_ci_gateway;
GRANT EXECUTE ON FUNCTION fm_private_ci.inspect_youtube_mock_session(TEXT,TEXT)
    TO fm_ci_gateway,fm_ci_auditor;
COMMIT;
