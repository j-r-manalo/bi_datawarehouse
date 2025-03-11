-- Content from 01_create_schemas.sql
-- Create the "raw" schema
CREATE SCHEMA IF NOT EXISTS raw AUTHORIZATION postgres;

-- Create the "curated" schema
CREATE SCHEMA IF NOT EXISTS curated AUTHORIZATION postgres;

-- Create the "analytics" schema
CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION postgres;

-- Content from 02_create_verifyplus_table.sql
-- Create the verifyplus table if it doesn't exist
CREATE TABLE raw.verifyplus (
    "requestCreatedDatetime" TIMESTAMP,
    "biPerPersonLimit" FLOAT,
    "accidentState" TEXT,
    "biPerOccurrenceLimit" FLOAT,
    "pdLimit" FLOAT,
    "propertyAdjusterName" TEXT,
    "numberOfClaimants" FLOAT,
    "requestType" TEXT,
    "claimSetUpStatus" TEXT,
    "claimSetUpAssignee" JSONB,
    "liabilityStatus" TEXT,
    "verifyAdjusterName" TEXT,
    "verifyRequestStatus" TEXT,
    "firmName" TEXT,
    "verifyStartDatetime" TIMESTAMP,
    "claimSetUpStartDate" DATE,
    "umPerPersonLimits" FLOAT,
    "claimSetUpCloseDate" DATE,
    "reportingCarrier" TEXT,
    "reportingPolicyNumber" TEXT,
    "reportingInsured" TEXT,
    "reportingClaimNumber" TEXT,
    "requestStatus" TEXT,
    "umStacking" TEXT,
    "customerCloseDatetime" TIMESTAMP,
    "dateOfLoss" DATE,
    "excludeFromReporting" BOOLEAN,
    "duplicateexclusionComments" TEXT,
    "duplicateRequest" BOOLEAN,
    "verifyCloseDatetimeOveride" TIMESTAMP,
    "requestId" INT PRIMARY KEY,
    "firmContactName" TEXT,
    "createdPreviousBusinessDay" BOOLEAN,
    "claimDaysToClose" FLOAT,
    "injuryAdjusterName" TEXT,
    "verifyCloseDatetime" TIMESTAMP,
    "verifyTimeOpen" FLOAT,
    "verifyAssignee" TEXT,
    "documentationStatus" TEXT,
    "numberOfAttempts" FLOAT,
    "numberOfAttemptedCalls" FLOAT,
    "numberOfAttemptedEmails" FLOAT,
    "coverageStatus" TEXT,
    "clientNames" TEXT,
    "umPerOccurrenceLimit" FLOAT,
    "coverage" TEXT
);


-- Content from 03_create_raw_cases_table.sql
-- Create the cases table if it doesn't exist
CREATE TABLE IF NOT EXISTS raw.cases (
    "documentId" text,
    "customerId" text,
    "version" integer,
    "matterTechId" text,
    "matterName" text,
    "claimCoverage" text,
    "claimNumber" text,
    "lossState" text,
    "sendingFirm" text,
    "recipientCarrier" text,
    "assignedAttorney" text,
    "assignedCaseCollaborator" text[],
    "assignedCaseManager" text,
    "clientId" text,
    "clientName" text,
    "matterId" text,
    "relatedInsuranceId" text
);


-- Content from 04_create_raw_metadata_table.sql
CREATE TABLE raw.metadata (
    "documentType" TEXT NOT NULL,
    "documentId" TEXT NOT NULL,
    "receiptAckTimeStamp" BIGINT, -- UNIX timestamp
    "demandIsDeliverable" BOOLEAN,
    "demandTemplateId" TEXT,
    "demandTemplatePinnedVersion" TEXT,
    "demandUploadedTimeStamp" BIGINT, -- UNIX timestamp
    "demandArchivedTimeStamp" BIGINT -- UNIX timestamp
);


-- Content from 05_create_raw_templates_table.sql
CREATE TABLE raw.templates (
    "templateId" TEXT NOT NULL,
    "templateName" TEXT NOT NULL,
    "version" INT NOT NULL,
    "defaultDemandConfig" JSONB
);

-- Content from 06_create_raw_audits_table.sql
CREATE TABLE raw.audit (
    "auditRecordId" TEXT NOT NULL,
    "documentId" TEXT NOT NULL,
    "createdTs" BIGINT, -- UNIX timestamp
    "actionType" TEXT,
    "lastArchiveReason" TEXT,
    "lastArchiveComment" TEXT
);


-- Content from 07_create_demands_archived_view.sql
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

-- Content from 08_create_demands_uploaded_view.sql
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

-- Content from 09_create_verifyplus_view.sql
CREATE MATERIALIZED VIEW IF NOT EXISTS curated.verifyplus AS
SELECT
    *
FROM
    raw.verifyplus ;

-- Content from 10_create_demands_summary_view.sql
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


-- Content from 11_create_roles.sql
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

-- Content from 13_grant_usage.sql
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

