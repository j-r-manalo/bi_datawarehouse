-- =============================================
-- Create read-only roles for Raw, Curated, and Analytics layers
-- =============================================
DO $$
BEGIN
    -- Create the raw_read_only role for the bronze (raw) layer
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'raw_read_only'
    ) THEN
        CREATE ROLE raw_read_only NOLOGIN;
    END IF;

    -- Create the curated_read_only role for the silver (curated) layer
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'curated_read_only'
    ) THEN
        CREATE ROLE curated_read_only NOLOGIN;
    END IF;

    -- Create the analytics_read_only role for the gold (analytics) layer
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'analytics_read_only'
    ) THEN
        CREATE ROLE analytics_read_only NOLOGIN;
    END IF;

    -- Create a composite role for both curated and analytics read-only access
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'curated_and_analytics_read_only'
    ) THEN
        CREATE ROLE curated_and_analytics_read_only NOLOGIN;
    END IF;

    -- Create a composite role for raw, curated and analytics read-only access
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'raw_curated_analytics_read_only'
    ) THEN
        CREATE ROLE raw_curated_analytics_read_only NOLOGIN;
    END IF;
END $$;