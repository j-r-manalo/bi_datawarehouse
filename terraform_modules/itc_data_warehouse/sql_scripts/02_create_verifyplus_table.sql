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

CREATE UNIQUE INDEX CONCURRENTLY verifyplus_idx
ON curated.verifyplus ("requestId");