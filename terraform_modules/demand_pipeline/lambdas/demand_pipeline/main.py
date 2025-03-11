# Standard library imports
import os
import time

# Local imports
from builders.case_builder import build_cases_table_data
from builders.metadata_builder import build_metadata_table_data
from builders.templates_builder import build_templates_table_data
from builders.audit_builder import build_audit_table_data
from utils import get_dynamo_table, scan_dynamo_table, parallel_scan_dynamo_table, insert_data_into_table, get_db_connection

import boto3
from boto3.dynamodb.conditions import Attr

# Load the environment variables from .env
from dotenv import load_dotenv
if os.path.exists('.env'):
    load_dotenv()

def main():
    """
    Main entry point for processing DynamoDB tables.
    """
    # Record overall start time
    overall_start_time = time.perf_counter()

    # Retrieve the environment variable
    SOURCE_ENV = os.getenv("SOURCE_ENV", "beta")  # Default to "sandbox" if ENV is not set
    SOURCE_ACCOUNT = os.getenv("SOURCE_ACCOUNT")
    print(f"SOURCE_ACCOUNT = {SOURCE_ACCOUNT}")

    # Initialize tables
    documents_table = get_dynamo_table(f'exchange-{SOURCE_ENV}-documents', SOURCE_ACCOUNT)
    metadata_table = get_dynamo_table(f'exchange-{SOURCE_ENV}-documents-metadata', SOURCE_ACCOUNT)
    templates_table = get_dynamo_table(f'exchange-{SOURCE_ENV}-templates', SOURCE_ACCOUNT)
    audit_table = get_dynamo_table(f'exchange-{SOURCE_ENV}-documents-audit', SOURCE_ACCOUNT)

    # -------------------- Scanning Documents Table --------------------
    sts = boto3.client("sts")
    print("Caller identity:", sts.get_caller_identity())

    print("Scanning Documents Table...")
    t0 = time.perf_counter()
    document_items = parallel_scan_dynamo_table(documents_table) #, global_max_rows=500)
    t1 = time.perf_counter()
    print(f"Documents Table scan completed in {t1 - t0:.2f} seconds.")

    print("Building case data...")
    build_start = time.perf_counter()
    cases = build_cases_table_data(document_items)
    build_end = time.perf_counter()
    print(f"Case data built in {build_end - build_start:.2f} seconds.")
    case_headers = [
        'documentId', 'customerId', 'version', 'matterTechId', 'matterName', 'claimCoverage',
        'claimNumber', 'lossState', 'sendingFirm', 'recipientCarrier', 'assignedAttorney',
        'assignedCaseCollaborator', 'assignedCaseManager','clientId', 'clientName', 'matterId',
        'relatedInsuranceId'
    ]

    # -------------------- Scanning Metadata Table --------------------
    print("Scanning Metadata Table...")
    t0 = time.perf_counter()
    metadata_items = scan_dynamo_table(metadata_table)
    t1 = time.perf_counter()
    print(f"Metadata Table scan completed in {t1 - t0:.2f} seconds.")

    print("Building metadata data...")
    build_start = time.perf_counter()
    metadata = build_metadata_table_data(metadata_items)
    build_end = time.perf_counter()
    print(f"Metadata data built in {build_end - build_start:.2f} seconds.")
    metadata_headers = [
        'documentType', 'documentId', 'receiptAckTimeStamp', 'demandIsDeliverable',
        'demandTemplateId', 'demandTemplatePinnedVersion', 'demandUploadedTimeStamp',
        'demandArchivedTimeStamp'
    ]

    # -------------------- Scanning Templates Table --------------------
    print("Scanning Templates Table...")
    t0 = time.perf_counter()
    templates_items = scan_dynamo_table(templates_table)
    t1 = time.perf_counter()
    print(f"Templates Table scan completed in {t1 - t0:.2f} seconds.")

    print("Building templates data...")
    build_start = time.perf_counter()
    templates = build_templates_table_data(templates_items)
    build_end = time.perf_counter()
    print(f"Templates data built in {build_end - build_start:.2f} seconds.")
    templates_headers = [
        'templateId', 'templateName', 'version', 'defaultDemandConfig'
    ]

    # -------------------- Scanning Audits Table --------------------
    print("Scanning Audits Table...")
    t0 = time.perf_counter()
    audit_items = parallel_scan_dynamo_table(
        audit_table,
        filter_expression=Attr('actionType').eq('DemandArchived'),
        projection_expression='auditRecordId, createdTs, documentId, actionType, lastArchiveReason, lastArchiveComment',
        # global_max_rows=500
    )
    t1 = time.perf_counter()
    print(f"Audits Table scan completed in {t1 - t0:.2f} seconds.")

    print("Building audit data...")
    build_start = time.perf_counter()
    audit = build_audit_table_data(audit_items)
    build_end = time.perf_counter()
    print(f"Audit data built in {build_end - build_start:.2f} seconds.")
    audit_headers = [
        'auditRecordId', 'createdTs', 'documentId', 'actionType', 'lastArchiveReason', 'lastArchiveComment'
    ]

    # -------------------- Database Insertion --------------------
    print("Connecting to the Postgres database...")
    conn = get_db_connection()

    try:
        print("Inserting cases data...")
        insert_data_start = time.perf_counter()
        insert_data_into_table(conn, "cases", case_headers, cases)
        insert_data_end = time.perf_counter()
        print(f"Cases data inserted in {insert_data_end - insert_data_start:.2f} seconds.")

        print("Inserting metadata data...")
        insert_data_start = time.perf_counter()
        insert_data_into_table(conn, "metadata", metadata_headers, metadata)
        insert_data_end = time.perf_counter()
        print(f"Metadata data inserted in {insert_data_end - insert_data_start:.2f} seconds.")

        print("Inserting templates data...")
        insert_data_start = time.perf_counter()
        insert_data_into_table(conn, "templates", templates_headers, templates)
        insert_data_end = time.perf_counter()
        print(f"Templates data inserted in {insert_data_end - insert_data_start:.2f} seconds.")

        print("Inserting audit data...")
        insert_data_start = time.perf_counter()
        insert_data_into_table(conn, "audit", audit_headers, audit)
        insert_data_end = time.perf_counter()
        print(f"Audit data inserted in {insert_data_end - insert_data_start:.2f} seconds.")

    finally:
        conn.close()
        print("Database connection closed.")

    overall_end_time = time.perf_counter()
    print(f"Total execution time: {overall_end_time - overall_start_time:.2f} seconds.")


def handler(event, context):
    """
    AWS Lambda entry point. This calls the main function.
    """
    main()


# Entry point for local execution
if __name__ == '__main__':
    main()