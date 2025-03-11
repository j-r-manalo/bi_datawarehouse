CREATE TABLE raw.audit (
    "auditRecordId" TEXT NOT NULL,
    "documentId" TEXT NOT NULL,
    "createdTs" BIGINT, -- UNIX timestamp
    "actionType" TEXT,
    "lastArchiveReason" TEXT,
    "lastArchiveComment" TEXT
);
