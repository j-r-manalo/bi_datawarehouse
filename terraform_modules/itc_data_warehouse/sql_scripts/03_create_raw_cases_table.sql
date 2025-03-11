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
