from decimal import Decimal

import json

def extract_names_from_case_managers(item, field_name, list_key="caseManagers", first_name_key="firstName",
                                     last_name_key="lastName"):
    """
    Extract a list of full names from a nested list field in the DynamoDB item.

    :param item: The DynamoDB item (dict).
    :param field_name: The name of the parent field (e.g., 'sendingFirm').
    :param list_key: The key within the parent field that holds the list (e.g., 'caseManagers').
    :param first_name_key: The key for the first name in each item.
    :param last_name_key: The key for the last name in each item.
    :return: A list of joined names (first and last) from the list.
    """
    names = []

    # Get the parent field from the item.
    parent_field = item.get(field_name)
    if not parent_field:
        return names

    # If parent_field is a string, try parsing it as JSON.
    if isinstance(parent_field, str):
        try:
            parent_field = json.loads(parent_field)
        except json.JSONDecodeError:
            print(f"Could not parse {field_name} as JSON.")
            return names

    # If the parent_field is wrapped in a DynamoDB "M", unwrap it.
    if isinstance(parent_field, dict) and "M" in parent_field:
        parent_field = parent_field["M"]

    # Now get the list from the parent field using the specified list_key.
    list_data = parent_field.get(list_key)
    if not list_data:
        return names

    # If list_data is a string, try parsing it as JSON.
    if isinstance(list_data, str):
        try:
            list_data = json.loads(list_data)
        except json.JSONDecodeError:
            print(f"Could not parse {list_key} data as JSON.")
            return names

    # Unwrap the list if it is in DynamoDB "L" format.
    if isinstance(list_data, dict) and "L" in list_data:
        items_list = list_data["L"]
    else:
        items_list = list_data

    # Make sure items_list is a list.
    if not isinstance(items_list, list):
        return names

    # Iterate over each entry in the list.
    for entry in items_list:
        # Ensure each entry is a dict.
        if not isinstance(entry, dict):
            continue

        # Unwrap the entry if it's in DynamoDB "M" format.
        details = entry.get("M", entry)
        if not isinstance(details, dict):
            continue

        # Extract first and last names; check if they are dicts with an "S" key.
        first_name_val = details.get(first_name_key)
        last_name_val = details.get(last_name_key)
        first_name = ""
        last_name = ""

        if isinstance(first_name_val, dict):
            first_name = first_name_val.get("S", "")
        elif isinstance(first_name_val, str):
            first_name = first_name_val

        if isinstance(last_name_val, dict):
            last_name = last_name_val.get("S", "")
        elif isinstance(last_name_val, str):
            last_name = last_name_val

        full_name = f"{first_name} {last_name}".strip() or first_name
        names.append(full_name)

    # Dedupe the list while preserving order.
    names = list(dict.fromkeys(names))
    return names

def extract_metadata_fields(item, field_name, keys_to_extract):
    """
    Extract specified fields from a metadata field in the DynamoDB item,
    including handling nested structures like claimant names.

    :param item: The DynamoDB item (dict).
    :param field_name: The name of the field to extract from the item (e.g., 'caseManagementMetadata').
    :param keys_to_extract: List of keys to extract from the metadata.
    :return: A dictionary with extracted fields.
    """
    # Initialize an empty dictionary to store extracted values
    extracted_data = {}

    # Get the specified field from the item
    metadata = item.get(field_name)

    # If the metadata is a string, try parsing it as JSON
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            print(f"Could not parse {field_name} as JSON.")
            metadata = {}

    # If the metadata is a dictionary, extract the specified keys
    if isinstance(metadata, dict):
        for key in keys_to_extract:
            value = metadata.get(key)
            # If the value is a dictionary (as in DynamoDB format), get the 'S' key
            if isinstance(value, dict):
                extracted_data[key] = value.get('S')
            else:
                # Otherwise, just assign the value directly
                extracted_data[key] = value

        # Handle the claimant field for firstName and lastName
        claimant = metadata.get('claimant')
        if claimant:
            first_name = claimant.get('firstName', '')
            last_name = claimant.get('lastName', '')
            # Join first and last names, checking if lastName is present
            extracted_data['clientName'] = f"{first_name} {last_name}".strip() or first_name

        # Handle the primary contact field for firstName and lastName
        primaryContact = metadata.get('primaryContact')
        if primaryContact:
            first_name = primaryContact.get('firstName', '')
            last_name = primaryContact.get('lastName', '')
            # Join first and last names, checking if lastName is present
            extracted_data['assignedCaseManager'] = f"{first_name} {last_name}".strip() or first_name

        # Handle the attorney field for firstName and lastName
        attorney = metadata.get('attorney')
        if attorney:
            first_name = attorney.get('firstName', '')
            last_name = attorney.get('lastName', '')
            # Join first and last names, checking if lastName is present
            extracted_data['assignedAttorney'] = f"{first_name} {last_name}".strip() or first_name

        # Handle the caseManagers field
        manager_names = extract_names_from_case_managers(item, field_name="sendingFirm", list_key="caseManagers")
        extracted_data['assignedCaseCollaborator'] = manager_names

    else:
        # If metadata is not a dictionary, default to None for all keys
        for key in keys_to_extract:
            extracted_data[key] = None

    return extracted_data

def build_cases_table_data(items):
    """
    Transforms a list of document items into case data for storage.

    :param items: List of document items from DynamoDB.
    :return: List of transformed case data.
    """
    cases_data_dict = []

    for item in items:
        try:
            # Transform item fields
            item['demandDetails']['demandResponseRelativeDueDate'] = (
                float(item['demandDetails']['demandResponseRelativeDueDate'])
                if item['demandDetails']['demandResponseRelativeDueDate']
                else None
            )
            item['createdTs'] = float(item['createdTs'])
            item['version'] = float(item['version'])

            # Process nested structures
            for attachment in item['attachments']:
                attachment['sourceFileSize'] = float(attachment['sourceFileSize']) if isinstance(attachment['sourceFileSize'], Decimal) else attachment['sourceFileSize']
                attachment['createdTs'] = float(attachment['createdTs'])

            # Extract sending firm name and remove trailing whitespace
            sending_firm_name = item['sendingFirm']['firmName']
            if isinstance(sending_firm_name, str):
                sending_firm_name = sending_firm_name.rstrip()

            # Build case data
            case_data = {
                'documentId': item['documentId'],
                'customerId': item['customerId'],
                'version': item['version'],
                'claimCoverage': item['claimInfo']['claimCoverage'],
                'claimNumber': item['claimInfo']['claimNumber'],
                'sendingFirm': sending_firm_name,
                'recipientCarrier': item['recipientCarrier']['carrierCommonName']
            }

            # Add easy case data
            cases_data_dict.append(case_data)

            # Get the data from caseManagementMetadata field
            keys_to_extract = ['relatedInsuranceId', 'clientId', 'matterId', 'matterTechId', 'matterName']
            extracted_metadata = extract_metadata_fields(item, 'caseManagementMetadata', keys_to_extract)
            case_data.update(extracted_metadata)

            # Get the data from claimInfo field
            keys_to_extract = ['lossState', 'claimNumber', 'claimCoverage', 'claimant']
            extracted_metadata = extract_metadata_fields(item, 'claimInfo', keys_to_extract)
            case_data.update(extracted_metadata)

            # Get the data from sendingFirm field
            keys_to_extract = ['primaryContact','attorney']
            extracted_metadata = extract_metadata_fields(item, 'sendingFirm', keys_to_extract)
            case_data.update(extracted_metadata)




        except KeyError as e:
            print(f"Missing key {e} in item: {item}")
        except Exception as e:
            print(f"Error processing item: {e}")

    return cases_data_dict