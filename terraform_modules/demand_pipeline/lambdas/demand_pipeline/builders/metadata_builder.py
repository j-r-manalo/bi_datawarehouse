from itc_common_utilities.logger.logger_setup import setup_logger

# Initialize the logger
logger = setup_logger(__name__)


def build_metadata_table_data(items):
    """
    Transforms a list of document items into metadata table data.

    :param items: List of document items from DynamoDB.
    :return: List of metadata table data.
    """
    logger.info(f"Building metadata table data from {len(items)} items")
    metadata_table_dict = []
    success_count = 0
    error_count = 0
    receipt_ack_count = 0
    archived_count = 0

    for item in items:
        try:
            document_id = item.get('documentId', 'unknown')
            logger.debug(f"Processing metadata for document {document_id}")

            metadata_data = {
                'documentType': item.get('documentType'),
                'documentId': document_id,
                'demandIsDeliverable': item.get('demandIsDeliverable'),
                'demandTemplateId': item.get('demandTemplateId'),
                'receiptAckTimeStamp': None,
                'demandUploadedTimeStamp': item.get('createdTs'),
                'demandArchivedTimeStamp': None,
            }

            # Extract document status history
            if isinstance(item.get('documentStatusHistory'), list):
                logger.debug(
                    f"Processing status history with {len(item['documentStatusHistory'])} entries for document {document_id}")

                for status in item['documentStatusHistory']:
                    if status.get('documentStatus') == 'DocumentReceived':
                        ts = status.get('timestamp')
                        if ts is not None:
                            # Convert timestamp to int before assignment
                            metadata_data['receiptAckTimeStamp'] = int(float(ts))
                            receipt_ack_count += 1
                            logger.debug(f"Found DocumentReceived status for document {document_id} at timestamp {ts}")

                    if status.get('documentStatus') == 'DocumentArchived':
                        ts = status.get('timestamp')
                        if ts is not None:
                            # Convert timestamp to int before assignment
                            metadata_data['demandArchivedTimeStamp'] = int(float(ts))
                            archived_count += 1
                            logger.debug(f"Found DocumentArchived status for document {document_id} at timestamp {ts}")
            else:
                logger.debug(f"No status history found for document {document_id}")

            metadata_table_dict.append(metadata_data)
            success_count += 1
            logger.debug(f"Successfully processed metadata for document {document_id}")

        except KeyError as e:
            error_count += 1
            logger.error(f"Missing key {e} in item: {item.get('documentId', 'unknown')}")
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing metadata for document {item.get('documentId', 'unknown')}: {e}")

    logger.info(f"Successfully processed {success_count} metadata records, encountered {error_count} errors")
    logger.info(
        f"Found {receipt_ack_count} documents with receipt acknowledgment and {archived_count} archived documents")
    logger.info(f"Final metadata dataset contains {len(metadata_table_dict)} records")

    return metadata_table_dict