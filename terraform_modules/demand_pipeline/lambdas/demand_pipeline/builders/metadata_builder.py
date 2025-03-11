def build_metadata_table_data(items):
    """
    Transforms a list of document items into metadata table data.

    :param items: List of document items from DynamoDB.
    :return: List of metadata table data.
    """
    metadata_table_dict = []

    for item in items:
        try:
            metadata_data = {
                'documentType': item.get('documentType'),
                'documentId': item.get('documentId'),
                'demandIsDeliverable': item.get('demandIsDeliverable'),
                'demandTemplateId': item.get('demandTemplateId'),
                'receiptAckTimeStamp': None,
                'demandUploadedTimeStamp': item.get('createdTs'),
                'demandArchivedTimeStamp': None,
            }

            # Extract document status history
            if isinstance(item.get('documentStatusHistory'), list):
                for status in item['documentStatusHistory']:
                    if status.get('documentStatus') == 'DocumentReceived':
                        ts = status.get('timestamp')
                        if ts is not None:
                            # Convert timestamp to int before assignment
                            metadata_data['receiptAckTimeStamp'] = int(float(ts))
                    if status.get('documentStatus') == 'DocumentArchived':
                        ts = status.get('timestamp')
                        if ts is not None:
                            # Convert timestamp to int before assignment
                            metadata_data['demandArchivedTimeStamp'] = int(float(ts))

            metadata_table_dict.append(metadata_data)

        except KeyError as e:
            print(f"Missing key {e} in item: {item}")
        except Exception as e:
            print(f"Error processing item: {e}")

    return metadata_table_dict