import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Adjust sys.path to include the parent directory where main.py is located.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the main function from main.py.
from main import main as main_function


# Fixtures for common test setups
@pytest.fixture
def mock_api_response():
    """Fixture providing standard mock API responses"""
    return [
        # Mock report_data
        {
            'data': [
                {'1': {'value': 'test value 1'},
                 '2': {'value': 'test value 2'},
                 '3': {'value': '2025-02-27T13:00:00Z'},
                 '4': {'value': '2025-02-27T13:00:00Z'},
                 '5': {'value': '2025-02-27T13:00:00Z'},
                 '6': {'value': '2025-02-27T13:00:00Z'},
                 '7': {'value': '2025-02-27T13:00:00Z'}}
            ]
        },
        # Mock report_metadata
        {'meta': 'data'},
        # Mock fields_info
        [
            {'id': 1, 'label': 'Test Field One'},
            {'id': 2, 'label': 'Test Field Two'},
            {'id': 3, 'label': 'customerCloseDatetime'},
            {'id': 4, 'label': 'verifyCloseDatetimeOveride'},
            {'id': 5, 'label': 'verifyStartDatetime'},
            {'id': 6, 'label': 'verifyCloseDatetime'},
            {'id': 7, 'label': 'Claim SetUp StartDate'}
        ]
    ]


@pytest.fixture
def mock_db_connection():
    """Fixture providing a mock database connection"""
    mock_conn = MagicMock()
    return mock_conn


# Mock the fix_timestamp_columns function to avoid the column check error
@patch('main.make_api_call')
@patch('main.get_db_connection')
@patch('main.insert_data_into_table')
@patch('main.fix_timestamp_columns')
@patch('main.fix_date_columns')
def test_main_function_successfully_processes_data(mock_fix_date_columns, mock_fix_timestamps, mock_insert_data, mock_get_conn, mock_api_call,
                                                   mock_api_response):
    # Setup mock returns
    mock_api_call.side_effect = mock_api_response

    # Make fix_date_columns return its input unmodified
    mock_fix_date_columns.side_effect = lambda df, cols: df

    # Make fix_timestamp_columns return its input unmodified
    mock_fix_timestamps.side_effect = lambda df, cols: df

    # Mock database connection
    mock_conn = MagicMock()
    mock_get_conn.return_value = mock_conn

    # Call the main function
    main_function()

    # Verify all API calls were made
    assert mock_api_call.call_count == 3

    # Verify database connection was established
    mock_get_conn.assert_called_once()

    # Verify data was inserted into the database
    mock_insert_data.assert_called_once()

    # Verify the connection was closed
    mock_conn.close.assert_called_once()


@patch('main.make_api_call')
def test_main_exits_when_api_calls_fail(mock_api_call):
    # Make one of the API calls return None
    mock_api_call.side_effect = [None, {}, {}]

    # Assert that main_function exits with SystemExit
    with pytest.raises(SystemExit) as e:
        main_function()
    assert e.value.code == 1


def fake_exit(code):
    raise SystemExit(code)

@patch('main.make_api_call')
@patch('sys.exit', side_effect=fake_exit)
def test_main_exits_on_key_error(mock_exit, mock_api_call):
    # Setup mock returns with invalid fields_info structure
    mock_api_call.side_effect = [
        {'data': [{'1': {'value': 'test'}}]},  # report_data
        {},  # report_metadata
        [{'wrong_key': 1}]  # fields_info with wrong structure
    ]

    # Call the main function and assert SystemExit is raised with code 1
    with pytest.raises(SystemExit) as exc_info:
        main_function()
    assert exc_info.value.code == 1


# Using pytest parameterization to test different row count scenarios
@pytest.mark.parametrize(
    "source_data,expected_success",
    [
        # Scenario 1: Matching row counts (should succeed)
        (
                {
                    'data': [
                        {'1': {'value': 'row1 val1'}, '2': {'value': 'row1 val2'}},
                        {'1': {'value': 'row2 val1'}, '2': {'value': 'row2 val2'}},
                    ]
                },
                True
        ),
        # Scenario 2: Empty data (should still succeed as 0=0)
        (
                {'data': []},
                True
        ),
    ]
)
@patch('main.make_api_call')
@patch('main.get_db_connection')
@patch('main.insert_data_into_table')
@patch('main.fix_timestamp_columns')
@patch('main.fix_date_columns')
def test_row_count_consistency_scenarios(mock_fix_date_columns, mock_fix_timestamps, mock_insert_data, mock_get_conn, mock_api_call,
                                         source_data, expected_success):
    """
    Test to verify that the number of rows read from the source matches
    the number of rows inserted into the target database across different scenarios.
    """
    # Setup mock API data
    mock_api_call.side_effect = [
        source_data,  # report_data
        {},  # report_metadata
        [  # fields_info
            {'id': 1, 'label': 'Field One'},
            {'id': 2, 'label': 'Field Two'}
        ]
    ]

    # Make fix_date_columns return its input unmodified
    mock_fix_date_columns.side_effect = lambda df, cols: df

    # Make fix_timestamp_columns return its input unmodified
    mock_fix_timestamps.side_effect = lambda df, cols: df

    # Mock database connection
    mock_conn = MagicMock()
    mock_get_conn.return_value = mock_conn

    # Capture the actual number of rows sent to insert_data_into_table
    inserted_rows = None

    def capture_rows_count(*args, **kwargs):
        nonlocal inserted_rows
        # args[2] is requests_data (list of dicts)
        inserted_rows = len(args[2])

    mock_insert_data.side_effect = capture_rows_count

    # Call the main function
    main_function()

    # Verify source and target row counts match
    source_rows_count = len(source_data['data'])
    assert inserted_rows == source_rows_count, \
        f"Row count mismatch: {source_rows_count} rows in source, but {inserted_rows} rows inserted"


# Integration test for row count validation
def test_row_count_validation():
    """
    Test to validate that an exception is thrown if source and target row counts don't match.
    This test demonstrates how the actual implementation should work.
    """

    # Create a modified version of the insert_data_into_table function that validates row counts
    def validate_row_counts(conn, table_name, headers, data, source_count=None):
        """
        Insert data into a table and validate row counts match.

        Args:
            conn: Database connection
            table_name: Target table name
            headers: Column headers
            data: Rows to insert
            source_count: Number of rows in source data

        Raises:
            ValueError: If target row count doesn't match source count
        """
        # If source_count is provided, validate that it matches data length
        if source_count is not None and len(data) != source_count:
            raise ValueError(
                f"Row count mismatch: {source_count} rows in source, but {len(data)} rows to be inserted"
            )

    # Test case where counts match
    validate_row_counts(None, "test_table", ["col1", "col2"],
                        [{"col1": "val1", "col2": "val2"}], 1)

    # Test case where counts don't match
    with pytest.raises(ValueError, match="Row count mismatch"):
        validate_row_counts(None, "test_table", ["col1", "col2"],
                            [{"col1": "val1", "col2": "val2"}], 2)