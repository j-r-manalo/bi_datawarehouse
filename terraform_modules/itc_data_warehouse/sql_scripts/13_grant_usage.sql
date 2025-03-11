-- =============================================
-- Grant privileges for the "raw" schema (bronze layer)
-- =============================================
GRANT USAGE ON SCHEMA raw TO raw_read_only;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO raw_read_only;
-- Ensure future tables in the "raw" schema are automatically granted SELECT privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA raw
    GRANT SELECT ON TABLES TO raw_read_only;

-- =============================================
-- Grant privileges for the "curated" schema (silver layer)
-- =============================================
GRANT USAGE ON SCHEMA curated TO curated_read_only;
GRANT SELECT ON ALL TABLES IN SCHEMA curated TO curated_read_only;
ALTER DEFAULT PRIVILEGES IN SCHEMA curated
    GRANT SELECT ON TABLES TO curated_read_only;

-- =============================================
-- Grant privileges for the "analytics" schema (gold layer)
-- =============================================
GRANT USAGE ON SCHEMA analytics TO analytics_read_only;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO analytics_read_only;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics
    GRANT SELECT ON TABLES TO analytics_read_only;

-- =============================================
-- Grant membership in composite role (curated and analytics)
-- =============================================
GRANT curated_read_only TO curated_and_analytics_read_only;
GRANT analytics_read_only TO curated_and_analytics_read_only;

-- =============================================
-- Grant membership in all 3 schemas composite role (raw, curated, and analytics)
-- =============================================
GRANT raw_read_only TO raw_curated_analytics_read_only;
GRANT curated_read_only TO raw_curated_analytics_read_only;
GRANT analytics_read_only TO raw_curated_analytics_read_only;