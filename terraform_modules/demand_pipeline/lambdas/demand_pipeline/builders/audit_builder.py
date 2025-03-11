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
    # Process each item to extract the additional fields from the payload.
    for item in results:
        payload = item.get('payload')
        if payload and isinstance(payload, dict):
            # Extract archiveReason.
            archive_reason = payload.get('archiveReason')
            if isinstance(archive_reason, dict) and 'S' in archive_reason:
                archive_reason_value = archive_reason['S']
            else:
                archive_reason_value = archive_reason
            item['lastArchiveReason'] = archive_reason_value

            # Extract archiveComments.
            archive_comments = payload.get('archiveComments')
            if isinstance(archive_comments, dict) and 'S' in archive_comments:
                archive_comments_value = archive_comments['S']
            else:
                archive_comments_value = archive_comments
            item['lastArchiveComment'] = archive_comments_value
        else:
            # Set to None if no valid payload is present.
            item['lastArchiveReason'] = None
            item['lastArchiveComment'] = None

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

    print("Final dataset prepared with", len(final_dataset), "records.")
    return final_dataset