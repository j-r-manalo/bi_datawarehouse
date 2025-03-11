CREATE MATERIALIZED VIEW IF NOT EXISTS curated.verifyplus AS
SELECT
    *
FROM
    raw.verifyplus ;