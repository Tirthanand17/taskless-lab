-- B3d4c2b3a: CI-ONLY least-privilege Postgres ledger and role boundary.
-- NEVER run against a production database. The CI-only role credentials are
-- set separately by disposable hosted workflow setup. NO real provider calls.
-- Requires isolated flowminute_fence_ci PostgreSQL DB and bootstrap superuser.
BEGIN;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;

CREATE ROLE fm_ci_owner NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
CREATE ROLE fm_ci_gateway LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
CREATE ROLE fm_ci_worker LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
CREATE ROLE fm_ci_auditor LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;

CREATE SCHEMA fm_private_ci AUTHORIZATION fm_ci_owner;
REVOKE ALL ON SCHEMA fm_private_ci FROM PUBLIC;
GRANT USAGE ON SCHEMA fm_private_ci TO fm_ci_gateway, fm_ci_worker, fm_ci_auditor;

SET ROLE fm_ci_owner;
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

CREATE TABLE fm_private_ci.day_ledger (
    day_key TEXT PRIMARY KEY CHECK (day_key ~ '^[0-9]{8}$'),
    owner_id TEXT NOT NULL,
    project_sha256 TEXT NOT NULL CHECK (project_sha256 ~ '^[0-9a-f]{64}$'),
    provider_id TEXT NOT NULL,
    burns INTEGER NOT NULL DEFAULT 0 CHECK (burns BETWEEN 0 AND 3)
);

CREATE TABLE fm_private_ci.burns (
    lease_id TEXT PRIMARY KEY,
    episode_id TEXT NOT NULL UNIQUE,
    day_key TEXT NOT NULL REFERENCES fm_private_ci.day_ledger(day_key),
    owner_id TEXT NOT NULL,
    project_sha256 TEXT NOT NULL CHECK (project_sha256 ~ '^[0-9a-f]{64}$'),
    model_id TEXT NOT NULL,
    context_sha256 TEXT NOT NULL CHECK (context_sha256 ~ '^[0-9a-f]{64}$'),
    external_anchor_sha256 TEXT NOT NULL CHECK (external_anchor_sha256 ~ '^[0-9a-f]{64}$'),
    token_sha256 TEXT NOT NULL CHECK (token_sha256 ~ '^[0-9a-f]{64}$'),
    status TEXT NOT NULL CHECK (status IN (
        'BURNED_UNCERTAIN_NO_RETRY',
        'MOCK_DRAFT_VALIDATED_NO_RELEASE',
        'MOCK_DRAFT_REJECTED_NO_RETRY'
    )),
    burned_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ,
    mock_output_sha256 TEXT,
    CONSTRAINT mock_terminal_fields CHECK (
        (status='BURNED_UNCERTAIN_NO_RETRY'
          AND closed_at IS NULL AND mock_output_sha256 IS NULL)
        OR
        (status<>'BURNED_UNCERTAIN_NO_RETRY'
          AND closed_at IS NOT NULL
          AND mock_output_sha256 ~ '^[0-9a-f]{64}$')
    )
);

CREATE TABLE fm_private_ci.audit_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lease_id TEXT NOT NULL REFERENCES fm_private_ci.burns(lease_id),
    event_action TEXT NOT NULL CHECK (event_action IN ('BURN', 'MOCK_CLOSE')),
    event_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX fm_audit_lease_idx ON fm_private_ci.audit_events(lease_id);

CREATE FUNCTION fm_private_ci.burn_mock_once(
    p_lease_id TEXT, p_episode_id TEXT, p_owner_id TEXT,
    p_project_sha256 TEXT, p_provider_id TEXT, p_model_id TEXT,
    p_context_sha256 TEXT, p_external_anchor_sha256 TEXT,
    p_token_sha256 TEXT, p_at TIMESTAMPTZ
) RETURNS TEXT LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, fm_private_ci, pg_temp
AS $body$
DECLARE
    v_day TEXT;
    v_owner TEXT;
    v_project TEXT;
    v_provider TEXT;
    v_count INTEGER;
BEGIN
    IF session_user <> 'fm_ci_gateway' THEN
        RAISE EXCEPTION 'CI mock gateway only' USING ERRCODE = '42501';
    END IF;
    IF p_episode_id IS NULL OR
       p_episode_id !~ '^fm_[0-9]{8}_(short_am|long|short_pm)$'
       OR p_lease_id IS NULL OR
       p_lease_id !~ '^[a-z][a-z0-9_]{2,63}$'
       OR p_owner_id IS NULL OR
       p_owner_id !~ '^[a-z][a-z0-9_]{2,63}$'
       OR p_provider_id IS DISTINCT FROM 'google_gemini_developer_api'
       OR p_model_id IS NULL OR p_model_id NOT IN ('gemini-3.8-flash','gemini-2.5-flash')
       OR p_project_sha256 IS NULL OR p_project_sha256 !~ '^[0-9a-f]{64}$'
       OR p_context_sha256 IS NULL OR p_context_sha256 !~ '^[0-9a-f]{64}$'
       OR p_external_anchor_sha256 IS NULL OR p_external_anchor_sha256 !~ '^[0-9a-f]{64}$'
       OR p_token_sha256 IS NULL OR p_token_sha256 !~ '^[0-9a-f]{64}$'
       OR p_at IS NULL THEN
        RAISE EXCEPTION 'Invalid fixture-only scope' USING ERRCODE = '22023';
    END IF;
    v_day := substring(p_episode_id from 4 for 8);
    INSERT INTO fm_private_ci.day_ledger(
        day_key,owner_id,project_sha256,provider_id,burns
    ) VALUES (v_day,p_owner_id,p_project_sha256,p_provider_id,0)
    ON CONFLICT (day_key) DO NOTHING;
    SELECT d.owner_id,d.project_sha256,d.provider_id,d.burns
      INTO v_owner,v_project,v_provider,v_count
      FROM fm_private_ci.day_ledger AS d
     WHERE d.day_key=v_day FOR UPDATE;
    IF NOT FOUND OR v_owner IS DISTINCT FROM p_owner_id
       OR v_project IS DISTINCT FROM p_project_sha256
       OR v_provider IS DISTINCT FROM p_provider_id
       OR v_count >= 3 THEN
        RAISE EXCEPTION 'Different owner/project or day cap burned'
          USING ERRCODE = '42501';
    END IF;
    INSERT INTO fm_private_ci.burns(
        lease_id,episode_id,day_key,owner_id,project_sha256,model_id,
        context_sha256,external_anchor_sha256,token_sha256,status,burned_at
    ) VALUES (
        p_lease_id,p_episode_id,v_day,p_owner_id,p_project_sha256,p_model_id,
        p_context_sha256,p_external_anchor_sha256,p_token_sha256,
        'BURNED_UNCERTAIN_NO_RETRY',p_at
    );
    UPDATE fm_private_ci.day_ledger SET burns=burns+1 WHERE day_key=v_day;
    INSERT INTO fm_private_ci.audit_events(lease_id,event_action,event_at)
    VALUES(p_lease_id,'BURN',p_at);
    RETURN 'BURNED_UNCERTAIN_NO_RETRY';
END;
$body$;

CREATE FUNCTION fm_private_ci.close_mock_once(
    p_lease_id TEXT,p_episode_id TEXT,p_token_sha256 TEXT,
    p_output_sha256 TEXT,p_valid BOOLEAN,p_at TIMESTAMPTZ
) RETURNS TEXT LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, fm_private_ci, pg_temp
AS $body$
DECLARE
    v_token TEXT;
    v_state TEXT;
    v_burned TIMESTAMPTZ;
    v_new_state TEXT;
BEGIN
    IF session_user <> 'fm_ci_gateway' THEN
        RAISE EXCEPTION 'CI mock gateway only' USING ERRCODE = '42501';
    END IF;
    IF p_lease_id IS NULL OR p_episode_id IS NULL
       OR p_token_sha256 IS NULL OR p_token_sha256 !~ '^[0-9a-f]{64}$'
       OR p_output_sha256 IS NULL OR p_output_sha256 !~ '^[0-9a-f]{64}$'
       OR p_valid IS NULL OR p_at IS NULL THEN
       RAISE EXCEPTION 'Invalid mock-only close arguments' USING ERRCODE = '22023';
    END IF;
    SELECT b.token_sha256,b.status,b.burned_at
      INTO v_token,v_state,v_burned
      FROM fm_private_ci.burns AS b
     WHERE b.lease_id=p_lease_id AND b.episode_id=p_episode_id FOR UPDATE;
    IF NOT FOUND OR v_state <> 'BURNED_UNCERTAIN_NO_RETRY'
       OR v_token IS DISTINCT FROM p_token_sha256
       OR p_at < v_burned THEN
       RAISE EXCEPTION 'Mock lease missing/forged/already closed'
         USING ERRCODE = '42501';
    END IF;
    v_new_state := CASE WHEN p_valid THEN
       'MOCK_DRAFT_VALIDATED_NO_RELEASE' ELSE 'MOCK_DRAFT_REJECTED_NO_RETRY' END;
    UPDATE fm_private_ci.burns
       SET status=v_new_state,closed_at=p_at,mock_output_sha256=p_output_sha256
     WHERE lease_id=p_lease_id AND episode_id=p_episode_id
       AND status='BURNED_UNCERTAIN_NO_RETRY';
    IF NOT FOUND THEN
       RAISE EXCEPTION 'Mock close lost race' USING ERRCODE = '42501';
    END IF;
    INSERT INTO fm_private_ci.audit_events(lease_id,event_action,event_at)
    VALUES(p_lease_id,'MOCK_CLOSE',p_at);
    RETURN v_new_state;
END;
$body$;

CREATE FUNCTION fm_private_ci.read_mock_state(p_lease_id TEXT)
RETURNS TABLE (state TEXT, audit_count BIGINT, episode_id TEXT)
LANGUAGE sql SECURITY DEFINER
SET search_path = pg_catalog, fm_private_ci, pg_temp
AS $body$
  SELECT b.status,COUNT(a.event_id)::BIGINT,b.episode_id
    FROM fm_private_ci.burns AS b
    JOIN fm_private_ci.audit_events AS a ON a.lease_id=b.lease_id
   WHERE b.lease_id=p_lease_id
   GROUP BY b.status,b.episode_id;
$body$;

REVOKE ALL ON ALL TABLES IN SCHEMA fm_private_ci FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA fm_private_ci FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA fm_private_ci FROM PUBLIC;
RESET ROLE;

GRANT EXECUTE ON FUNCTION fm_private_ci.burn_mock_once(
    TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TIMESTAMPTZ
) TO fm_ci_gateway;
GRANT EXECUTE ON FUNCTION fm_private_ci.close_mock_once(
    TEXT,TEXT,TEXT,TEXT,BOOLEAN,TIMESTAMPTZ
) TO fm_ci_gateway;
GRANT EXECUTE ON FUNCTION fm_private_ci.read_mock_state(TEXT)
  TO fm_ci_gateway,fm_ci_worker,fm_ci_auditor;

COMMIT;
