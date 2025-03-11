CREATE MATERIALIZED VIEW IF NOT EXISTS curated.demands_uploaded AS
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
        c."clientId" AS "matterClientId",
        c."assignedAttorney",
        c."assignedCaseCollaborator",
        m."demandUploadedTimeStamp",
        m."demandArchivedTimeStamp",
        m."demandTemplateId",
        ROW_NUMBER() OVER (PARTITION BY c."documentId" ORDER BY c."version" DESC) AS rn
    FROM
        raw."cases" c
    LEFT JOIN
        raw."metadata" m ON c."documentId" = m."documentId"
    WHERE
        m."demandUploadedTimeStamp" IS NOT NULL
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
    "sendingFirm",
    "precedentDocumentId",
    to_timestamp("demandUploadedTimeStamp") AS "demandUploadedDate",
    to_timestamp("demandArchivedTimeStamp") AS "demandArchivedDate",
    "matterName",
    "clientName",
    "recipientCarrier",
    "claimNumber",
    "claimCoverage",
    "lossState",
    "assignedCaseManager",
    "matterClientId",
    "assignedAttorney",
    "assignedCaseCollaborator"
FROM
    latest_cases lc
LEFT JOIN
    latest_templates t ON lc."demandTemplateId" = t."templateId" AND t.rn = 1
WHERE
    lc.rn = 1
    AND (
        lc."demandTemplateId" IS NULL
        OR lc."demandTemplateId" = ''
        OR (t."client_level_flag" != 'YES' AND t."templateId" IS NOT NULL AND t."templateId" != '')
    );

CREATE UNIQUE INDEX CONCURRENTLY demands_uploaded_idx
ON curated.demands_uploaded ("precedentDocumentId", "demandUploadedDate");