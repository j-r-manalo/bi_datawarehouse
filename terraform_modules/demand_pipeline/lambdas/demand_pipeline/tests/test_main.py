import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# You may need the following depending on your local path structure
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the function under test
from main import main as main_function


@pytest.fixture
def mock_db_connection():
    """Fixture providing a mock database connection."""
    return MagicMock()


@pytest.fixture
def mock_scan_data():
    """
    Fixture returning sample data from DynamoDB scans.
    Adjust these dictionaries as needed to match the
    schema of your actual data.
    """
    documents_items = [
        {"documentId": "doc1", "someField": "value1"},
        {"documentId": "doc2", "someField": "value2"},
    ]
    metadata_items = [
        {"documentId": "doc1", "documentType": "TYPE_A"},
        {"documentId": "doc2", "documentType": "TYPE_B"},
    ]
    templates_items = [
        {"templateId": "tmpl1", "templateName": "Template 1"},
        {"templateId": "tmpl2", "templateName": "Template 2"},
    ]
    audit_items = [
        {
            "auditRecordId": "aud1",
            "documentId": "doc1",
            "actionType": "DemandArchived",
            "lastArchiveReason": "Reason1",
            "lastArchiveComment": "Comment1",
        },
        {
            "auditRecordId": "aud2",
            "documentId": "doc2",
            "actionType": "DemandArchived",
            "lastArchiveReason": "Reason2",
            "lastArchiveComment": "Comment2",
        },
    ]

    return {
        "documents_items": documents_items,
        "metadata_items": metadata_items,
        "templates_items": templates_items,
        "audit_items": audit_items,
    }


@pytest.fixture
def mock_built_data():
    """
    Fixture returning sample built data from your builder functions.
    """
    cases_data = [
        {"documentId": "doc1", "customerId": "cust1"},
        {"documentId": "doc2", "customerId": "cust2"},
    ]
    metadata_data = [
        {"documentType": "TYPE_A", "documentId": "doc1"},
        {"documentType": "TYPE_B", "documentId": "doc2"},
    ]
    templates_data = [
        {"templateId": "tmpl1", "templateName": "Template 1"},
        {"templateId": "tmpl2", "templateName": "Template 2"},
    ]
    audit_data = [
        {"auditRecordId": "aud1", "documentId": "doc1", "actionType": "DemandArchived"},
        {"auditRecordId": "aud2", "documentId": "doc2", "actionType": "DemandArchived"},
    ]
    return {
        "cases": cases_data,
        "metadata": metadata_data,
        "templates": templates_data,
        "audit": audit_data
    }


@patch("main.get_db_connection")
@patch("main.insert_data_and_validate")
@patch("main.build_audit_table_data")
@patch("main.build_templates_table_data")
@patch("main.build_metadata_table_data")
@patch("main.build_cases_table_data")
@patch("main.scan_dynamo_table")
@patch("main.parallel_scan_dynamo_table")
@patch("boto3.client")
@patch("main.get_dynamo_table")
def test_main_function_successfully_processes_data(
    mock_get_dynamo_table,
    mock_boto_client,
    mock_parallel_scan_dynamo_table,
    mock_scan_dynamo_table,
    mock_build_cases_table_data,
    mock_build_metadata_table_data,
    mock_build_templates_table_data,
    mock_build_audit_table_data,
    mock_insert_data_and_validate,
    mock_get_db_connection,
    mock_db_connection,
    mock_scan_data,
    mock_built_data,
):
    """
    Test that main_function successfully scans DynamoDB tables,
    builds data, and inserts into the database.
    """

    # -------------------- Setup Mocks --------------------
    mock_sts_instance = MagicMock()
    mock_sts_instance.get_caller_identity.return_value = {"Account": "123456789012"}
    mock_boto_client.return_value = mock_sts_instance

    # Mock get_dynamo_table
    mock_documents_table = MagicMock()
    mock_metadata_table = MagicMock()
    mock_templates_table = MagicMock()
    mock_audit_table = MagicMock()
    mock_get_dynamo_table.side_effect = [
        mock_documents_table,   # documents
        mock_metadata_table,    # metadata
        mock_templates_table,   # templates
        mock_audit_table        # audit
    ]

    # Mock parallel_scan_dynamo_table for documents and audit
    mock_parallel_scan_dynamo_table.side_effect = [
        mock_scan_data["documents_items"],
        mock_scan_data["audit_items"],
    ]

    # Mock scan_dynamo_table for metadata and templates
    mock_scan_dynamo_table.side_effect = [
        mock_scan_data["metadata_items"],
        mock_scan_data["templates_items"],
    ]

    # Mock builder functions
    mock_build_cases_table_data.return_value = mock_built_data["cases"]
    mock_build_metadata_table_data.return_value = mock_built_data["metadata"]
    mock_build_templates_table_data.return_value = mock_built_data["templates"]
    mock_build_audit_table_data.return_value = mock_built_data["audit"]

    # Mock DB connection
    mock_get_db_connection.return_value = mock_db_connection

    # Mock insert_data_into_table
    mock_insert_data_and_validate.side_effect = lambda *args, **kwargs: None

    # -------------------- Execute --------------------
    main_function()

    # -------------------- Verify --------------------
    assert mock_get_dynamo_table.call_count == 4
    assert mock_parallel_scan_dynamo_table.call_count == 2
    assert mock_scan_dynamo_table.call_count == 2

    mock_build_cases_table_data.assert_called_once_with(mock_scan_data["documents_items"])
    mock_build_metadata_table_data.assert_called_once_with(mock_scan_data["metadata_items"])
    mock_build_templates_table_data.assert_called_once_with(mock_scan_data["templates_items"])
    mock_build_audit_table_data.assert_called_once_with(mock_scan_data["audit_items"])

    mock_get_db_connection.assert_called_once()

    # The function insert_data_and_validate calls insert_data_into_table 4 times
    # (cases, metadata, templates, audit), so we expect 4 calls
    assert mock_insert_data_and_validate.call_count == 4

    # Each call: (conn, table_name, headers, data)
    insert_calls = mock_insert_data_and_validate.call_args_list
    expected_tables = ["cases", "metadata", "templates", "audit"]
    expected_data = [
        mock_built_data["cases"],
        mock_built_data["metadata"],
        mock_built_data["templates"],
        mock_built_data["audit"],
    ]

    for i, call in enumerate(insert_calls):
        positional_args = call[0]
        conn_arg = positional_args[0]
        table_arg = positional_args[1]
        headers_arg = positional_args[2]
        data_arg = positional_args[3]

        assert conn_arg == mock_db_connection
        assert table_arg == expected_tables[i]
        assert data_arg == expected_data[i]

    # Verify DB connection closed
    mock_db_connection.close.assert_called_once()


@patch("main.get_db_connection")
@patch("main.insert_data_and_validate")
@patch("main.build_audit_table_data")
@patch("main.build_templates_table_data")
@patch("main.build_metadata_table_data")
@patch("main.build_cases_table_data")
@patch("main.scan_dynamo_table")
@patch("main.parallel_scan_dynamo_table")
@patch("boto3.client")
@patch("main.get_dynamo_table")
def test_main_with_empty_scans(
    mock_get_dynamo_table,
    mock_boto_client,
    mock_parallel_scan_dynamo_table,
    mock_scan_dynamo_table,
    mock_build_cases_table_data,
    mock_build_metadata_table_data,
    mock_build_templates_table_data,
    mock_build_audit_table_data,
    mock_insert_data_and_validate,
    mock_get_db_connection,
    mock_db_connection
):
    """
    Test that main_function completes gracefully even if the DynamoDB scans return empty lists.
    """
    mock_sts_instance = MagicMock()
    mock_sts_instance.get_caller_identity.return_value = {"Account": "123456789012"}
    mock_boto_client.return_value = mock_sts_instance

    mock_documents_table = MagicMock()
    mock_metadata_table = MagicMock()
    mock_templates_table = MagicMock()
    mock_audit_table = MagicMock()
    mock_get_dynamo_table.side_effect = [
        mock_documents_table,
        mock_metadata_table,
        mock_templates_table,
        mock_audit_table,
    ]

    # Empty lists from the scans
    mock_parallel_scan_dynamo_table.side_effect = [
        [],  # documents
        [],  # audit
    ]
    mock_scan_dynamo_table.side_effect = [
        [],  # metadata
        [],  # templates
    ]

    # Builders return empty lists
    mock_build_cases_table_data.return_value = []
    mock_build_metadata_table_data.return_value = []
    mock_build_templates_table_data.return_value = []
    mock_build_audit_table_data.return_value = []

    mock_get_db_connection.return_value = mock_db_connection
    mock_insert_data_and_validate.side_effect = lambda *args, **kwargs: None

    # Execute
    main_function()

    # Verify builders were called
    mock_build_cases_table_data.assert_called()
    mock_build_metadata_table_data.assert_called()
    mock_build_templates_table_data.assert_called()
    mock_build_audit_table_data.assert_called()

    # Since each insert method is called, we expect 4 calls (cases, metadata, templates, audit),
    # all with empty data
    assert mock_insert_data_and_validate.call_count == 4
    for call_args in mock_insert_data_and_validate.call_args_list:
        data_arg = call_args[0][3]  # the 'data' param
        assert data_arg == []

    mock_db_connection.close.assert_called_once()
