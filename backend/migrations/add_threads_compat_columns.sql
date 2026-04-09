-- Add compatibility columns to threads table in sagitarioa
-- Run this script against sagitarioa database

-- Add updated_at column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'threads' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE threads ADD COLUMN updated_at timestamp with time zone;
    END IF;
END $$;

-- Add metadata column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'threads' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE threads ADD COLUMN metadata jsonb DEFAULT '{}'::jsonb;
    END IF;
END $$;