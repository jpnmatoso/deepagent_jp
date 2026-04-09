-- Grant ownership of threads table to agent_user
-- Run this script as postgres or sagitarioa user

-- Option 1: Grant ownership of just the threads table
ALTER TABLE threads OWNER TO agent_user;

-- Option 2 (recommended): Grant ownership of all sagitarioa tables to agent_user
DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tableowner != 'agent_user'
    LOOP
        EXECUTE 'ALTER TABLE ' || tbl || ' OWNER TO agent_user';
    END LOOP;
END $$;

-- Also grant ownership of sequences (if any)
DO $$
DECLARE
    seq text;
BEGIN
    FOR seq IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public' AND sequence_owner != 'agent_user'
    LOOP
        EXECUTE 'ALTER SEQUENCE ' || seq || ' OWNER TO agent_user';
    END LOOP;
END $$;