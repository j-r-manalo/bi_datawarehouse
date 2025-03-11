CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.demands_summary AS
WITH
-- Extract monthly upload counts
uploaded_monthly AS (
    SELECT
        to_char("demandUploadedDate", 'YYYY-MM') AS "month",
        "sendingFirm",
        COUNT(*) AS "uploaded_count"
    FROM
        curated.demands_uploaded
    GROUP BY
        to_char("demandUploadedDate", 'YYYY-MM'),
        "sendingFirm"
),
-- Extract monthly archived counts
archived_monthly AS (
    SELECT
        to_char("demandArchivedDate", 'YYYY-MM') AS "month",
        "sendingFirm",
        COUNT(*) AS "archived_count"
    FROM
        curated.demands_archived
    GROUP BY
        to_char("demandArchivedDate", 'YYYY-MM'),
        "sendingFirm"
)
-- Combine uploaded and archived counts by month and firm
SELECT
    COALESCE(u."month", a."month") AS "month",
    COALESCE(u."sendingFirm", a."sendingFirm") AS "sendingFirm",
    COALESCE(u."uploaded_count", 0) AS "uploaded",
    COALESCE(a."archived_count", 0) AS "archived"
FROM
    uploaded_monthly u
FULL OUTER JOIN
    archived_monthly a
ON
    u."month" = a."month" AND u."sendingFirm" = a."sendingFirm";


CREATE UNIQUE INDEX CONCURRENTLY demands_summary_idx
ON analytics.demands_summary ("month","sendingFirm");