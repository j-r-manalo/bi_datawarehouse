from itc_common_utilities.logger.logger_setup import setup_logger

# Initialize the logger
logger = setup_logger(__name__)


def build_audit_table_data(results):
    """
    Processes scanned DynamoDB results by extracting 'archiveReason' and 'archiveComments'
    from the payload and building the final dataset for insertion.

    For each item in results:
      - Extracts the 'archiveReason' from the payload (if available) and adds it as 'lastArchiveReason'.
      - Extracts the 'archiveComments' from the payload (if available) and adds it as 'lastArchiveComment'.
      - If the payload is missing or not a dict, both new fields are set to None.

    Finally, builds a final dataset containing only:
        auditRecordId, createdTs, documentId, actionType, lastArchiveReason, and lastArchiveComment.

    :param results: List of dictionaries from the DynamoDB scan.
    :return: List of processed dictionaries.
    """
    logger.info(f"Processing {len(results)} audit records...")

    # Track counts for logging
    missing_payload_count = 0
    processed_count = 0

    # Process each item to extract the additional fields from the payload.
    for item in results:
        payload = item.get('payload')
        if payload and isinstance(payload, dict):
            processed_count += 1

            # Extract archiveReason.
            archive_reason = payload.get('archiveReason')
            if isinstance(archive_reason, dict) and 'S' in archive_reason:
                archive_reason_value = archive_reason['S']
                logger.debug(f"Extracted archive reason in DynamoDB format for record {item.get('auditRecordId')}")
            else:
                archive_reason_value = archive_reason
            item['lastArchiveReason'] = archive_reason_value

            # Extract archiveComments.
            archive_comments = payload.get('archiveComments')
            if isinstance(archive_comments, dict) and 'S' in archive_comments:
                archive_comments_value = archive_comments['S']
                logger.debug(f"Extracted archive comments in DynamoDB format for record {item.get('auditRecordId')}")
            else:
                archive_comments_value = archive_comments
            item['lastArchiveComment'] = archive_comments_value
        else:
            # Set to None if no valid payload is present.
            missing_payload_count += 1
            item['lastArchiveReason'] = None
            item['lastArchiveComment'] = None
            logger.debug(f"Missing or invalid payload for record {item.get('auditRecordId')}")

    logger.info(
        f"Processed {processed_count} records with valid payloads. Found {missing_payload_count} records with missing/invalid payloads.")

    # Build the final dataset.
    final_dataset = []
    for item in results:
        final_record = {
            'auditRecordId': item.get('auditRecordId'),
            'createdTs': item.get('createdTs'),
            'documentId': item.get('documentId'),
            'actionType': item.get('actionType'),
            'lastArchiveReason': item.get('lastArchiveReason'),
            'lastArchiveComment': item.get('lastArchiveComment')
        }
        final_dataset.append(final_record)

    logger.info(f"Final audit dataset prepared with {len(final_dataset)} records.")
    return final_dataset