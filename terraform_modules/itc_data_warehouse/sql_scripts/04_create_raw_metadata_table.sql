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
