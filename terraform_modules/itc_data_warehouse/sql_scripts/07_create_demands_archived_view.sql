CREATE MATERIALIZED VIEW IF NOT EXISTS curated.demands_archived AS
WITH latest_cases AS (
    SELECT
        c."sendingFirm",
        c."documentId" AS "precedentDocumentId",
        c."matterName",
        c."clientName",
        c."recipientCarrier",
        c."claimNumber",
        c."claimCoverage",
        c."lossState",
        c."assignedCaseManager",
        c."assignedAttorney",
        m."demandUploadedTimeStamp",
        m."demandArchivedTimeStamp",
        m."demandIsDeliverable",
        m."demandTemplateId",
        ROW_NUMBER() OVER (PARTITION BY c."documentId" ORDER BY c."version" DESC) AS rn
    FROM
        raw."cases" c
    JOIN
        raw."metadata" m ON c."documentId" = m."documentId"
    WHERE
        m."demandArchivedTimeStamp" IS NOT NULL
),
latest_audit AS (
    SELECT
        a."documentId",
        a."lastArchiveReason",
        a."lastArchiveComment"
    FROM
        raw."audit" a
    WHERE
        a."createdTs" = (
            SELECT MAX(a2."createdTs")
            FROM raw."audit" a2
            WHERE a2."documentId" = a."documentId"
        )
),
latest_templates AS (
    SELECT
        t."templateId",
        t."templateName",
        CASE
            WHEN LOWER(t."templateName") LIKE '%client%' THEN 'YES'
            ELSE 'NO'
        END AS "client_level_flag",
        ROW_NUMBER() OVER (PARTITION BY t."templateId" ORDER BY t."version" DESC) AS rn
    FROM
        raw."templates" t
    WHERE
        t."templateId" IS NOT NULL
        AND t."templateId" != ''
)
SELECT
    to_timestamp(lc."demandArchivedTimeStamp") AS "demandArchivedDate",
    lc."precedentDocumentId",
    lc."sendingFirm",
    lc."matterName",
    lc."clientName",
    lc."recipientCarrier",
    lc."claimNumber",
    lc."claimCoverage",
    lc."lossState",
    lc."assignedAttorney",
    lc."assignedCaseManager",
    COALESCE(la."lastArchiveReason", '') AS "lastArchiveReason",
    COALESCE(la."lastArchiveComment", '') AS "lastArchiveComment"
FROM
    latest_cases lc
LEFT JOIN
    latest_audit la ON lc."precedentDocumentId" = la."documentId"
LEFT JOIN
    latest_templates t ON lc."demandTemplateId" = t."templateId" AND t.rn = 1
WHERE
    lc.rn = 1
    AND (
        lc."demandTemplateId" IS NULL
        OR lc."demandTemplateId" = ''
        OR (t."client_level_flag" != 'YES' AND t."templateId" IS NOT NULL AND t."templateId" != '')
    );

CREATE UNIQUE INDEX CONCURRENTLY demands_archived_idx
ON curated.demands_archived ("precedentDocumentId", "demandArchivedDate");