# Standard library imports
import os
import time

# Local imports
from builders.case_builder import build_cases_table_data
from builders.metadata_builder import build_metadata_table_data
from builders.templates_builder import build_templates_table_data
from builders.audit_builder import build_audit_table_data
from utils import get_dynamo_table, scan_dynamo_table, parallel_scan_dynamo_table, insert_data_and_validate, get_db_connection

import boto3
from boto3.dynamodb.conditions import Attr

# Shared Logger
from itc_common_utilities.logger.logger_setup import setup_logger

# Initialize the logger
logger = setup_logger(__name__)

# Load the environment variables from .env
# from dotenv import load_dotenv
# if os.path.exists('.env'):
#     load_dotenv()

def main():
    """
    Main entry point for processing DynamoDB tables.
    """
    # Record overall start time
    overall_start_time = time.perf_counter()

    # Retrieve the environment variable
    SOURCE_ENV = os.getenv("SOURCE_ENV", "beta")  # Default to "beta" if ENV is not set
    SOURCE_ACCOUNT = os.getenv("SOURCE_ACCOUNT")
    logger.info(f"Running in SOURCE_ENV: {SOURCE_ENV}, SOURCE_ACCOUNT: {SOURCE_ACCOUNT}")

    # Initialize tables
    logger.info("Initializing DynamoDB table resources...")
    documents_table = get_dynamo_table(f'exchange-{SOURCE_ENV}-documents', SOURCE_ACCOUNT)
    metadata_table = get_dynamo_table(f'exchange-{SOURCE_ENV}-documents-metadata', SOURCE_ACCOUNT)
    templates_table = get_dynamo_table(f'exchange-{SOURCE_ENV}-templates', SOURCE_ACCOUNT)
    audit_table = get_dynamo_table(f'exchange-{SOURCE_ENV}-documents-audit', SOURCE_ACCOUNT)

    # -------------------- Scanning Documents Table --------------------
    sts = boto3.client("sts")
    logger.debug("Caller identity: %s", sts.get_caller_identity())

    logger.info("Scanning Documents Table...")
    t0 = time.perf_counter()
    document_items = parallel_scan_dynamo_table(documents_table) #, global_max_rows=500)
    t1 = time.perf_counter()
    logger.info(f"Documents Table scan completed in {t1 - t0:.2f} seconds. Retrieved {len(document_items)} items.")

    logger.info("Building case data...")
    build_start = time.perf_counter()
    cases = build_cases_table_data(document_items)
    build_end = time.perf_counter()
    logger.info(f"Case data built in {build_end - build_start:.2f} seconds. Generated {len(cases)} case records.")
    case_headers = [
        'documentId', 'customerId', 'version', 'matterTechId', 'matterName', 'claimCoverage',
        'claimNumber', 'lossState', 'sendingFirm', 'recipientCarrier', 'assignedAttorney',
        'assignedCaseCollaborator', 'assignedCaseManager','clientId', 'clientName', 'matterId',
        'relatedInsuranceId'
    ]

    # -------------------- Scanning Metadata Table --------------------
    logger.info("Scanning Metadata Table...")
    t0 = time.perf_counter()
    metadata_items = scan_dynamo_table(metadata_table)
    t1 = time.perf_counter()
    logger.info(f"Metadata Table scan completed in {t1 - t0:.2f} seconds. Retrieved {len(metadata_items)} items.")

    logger.info("Building metadata data...")
    build_start = time.perf_counter()
    metadata = build_metadata_table_data(metadata_items)
    build_end = time.perf_counter()
    logger.info(f"Metadata data built in {build_end - build_start:.2f} seconds. Generated {len(metadata)} metadata records.")
    metadata_headers = [
        'documentType', 'documentId', 'receiptAckTimeStamp', 'demandIsDeliverable',
        'demandTemplateId', 'demandTemplatePinnedVersion', 'demandUploadedTimeStamp',
        'demandArchivedTimeStamp'
    ]

    # -------------------- Scanning Templates Table --------------------
    logger.info("Scanning Templates Table...")
    t0 = time.perf_counter()
    templates_items = scan_dynamo_table(templates_table)
    t1 = time.perf_counter()
    logger.info(f"Templates Table scan completed in {t1 - t0:.2f} seconds. Retrieved {len(templates_items)} items.")

    logger.info("Building templates data...")
    build_start = time.perf_counter()
    templates = build_templates_table_data(templates_items)
    build_end = time.perf_counter()
    logger.info(f"Templates data built in {build_end - build_start:.2f} seconds. Generated {len(templates)} template records.")
    templates_headers = [
        'templateId', 'templateName', 'version', 'defaultDemandConfig'
    ]

    # -------------------- Scanning Audits Table --------------------
    logger.info("Scanning Audits Table with filter for 'DemandArchived' actions...")
    t0 = time.perf_counter()
    audit_items = parallel_scan_dynamo_table(
        audit_table,
        filter_expression=Attr('actionType').eq('DemandArchived'),
        projection_expression='auditRecordId, createdTs, documentId, actionType, lastArchiveReason, lastArchiveComment',
        # global_max_rows=500
    )
    t1 = time.perf_counter()
    logger.info(f"Audits Table scan completed in {t1 - t0:.2f} seconds. Retrieved {len(audit_items)} items.")

    logger.info("Building audit data...")
    build_start = time.perf_counter()
    audit = build_audit_table_data(audit_items)
    build_end = time.perf_counter()
    logger.info(f"Audit data built in {build_end - build_start:.2f} seconds. Generated {len(audit)} audit records.")
    audit_headers = [
        'auditRecordId', 'createdTs', 'documentId', 'actionType', 'lastArchiveReason', 'lastArchiveComment'
    ]

    # -------------------- Database Insertion --------------------
    logger.info("Connecting to the PostgreSQL database...")
    conn = get_db_connection()

    try:
        logger.info("Starting database transaction for cases data insertion...")
        insert_data_start = time.perf_counter()
        insert_data_and_validate(conn, "cases", case_headers, cases)
        insert_data_end = time.perf_counter()
        logger.info(f"Cases data insert transaction completed in {insert_data_end - insert_data_start:.2f} seconds.")

        logger.info("Starting database transaction for metadata insertion...")
        insert_data_start = time.perf_counter()
        insert_data_and_validate(conn, "metadata", metadata_headers, metadata)
        insert_data_end = time.perf_counter()
        logger.info(f"Metadata data insert transaction completed in {insert_data_end - insert_data_start:.2f} seconds.")

        logger.info("Starting database transaction for templates insertion...")
        insert_data_start = time.perf_counter()
        insert_data_and_validate(conn, "templates", templates_headers, templates)
        insert_data_end = time.perf_counter()
        logger.info(f"Templates data insert transaction completed in {insert_data_end - insert_data_start:.2f} seconds.")

        logger.info("Starting database transaction for audit insertion...")
        insert_data_start = time.perf_counter()
        insert_data_and_validate(conn, "audit", audit_headers, audit)
        insert_data_end = time.perf_counter()
        logger.info(f"Audit data insert transaction completed in {insert_data_end - insert_data_start:.2f} seconds.")

        # If all insertions matched their row counts, commit once at the end
        conn.commit()
        logger.info("All table insertions validated. Transaction committed successfully.")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error encountered. Transaction rolled back. Reason: {e}")
        raise e

    finally:
        conn.close()
        logger.info("Database connection closed.")

    overall_end_time = time.perf_counter()
    logger.info(f"Total execution time: {overall_end_time - overall_start_time:.2f} seconds.")


def handler(event, context):
    """
    AWS Lambda entry point. This calls the main function.
    """
    logger.info("Lambda handler invoked")
    main()
    logger.info("Lambda execution completed")


# Entry point for local execution
if __name__ == '__main__':
    logger.info("Starting script execution")
    main()
    logger.info("Script execution completed")