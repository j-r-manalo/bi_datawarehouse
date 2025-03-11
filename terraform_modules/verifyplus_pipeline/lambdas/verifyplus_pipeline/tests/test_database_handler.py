import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


# Import your database handler module
# from database_handler import insert_data_into_table, get_db_connection

# This is the improved function we want to test
def insert_data_into_table_with_validation(conn, table_name, headers, data, source_count=None):
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

    # In a real implementation, you would call the original function:
    # insert_data_into_table(conn, table_name, headers, data)

    # And then verify the actual count:
    # cursor = conn.cursor()
    # cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    # inserted_count = cursor.fetchone()[0]
    # if source_count is not None and inserted_count != source_count:
    #     conn.rollback()
    #     raise ValueError(f"Row count mismatch after insertion: {source_count} rows in source, but {inserted_count} rows inserted")
    # conn.commit()

    # For testing, we'll simulate this behavior
    return len(data)  # Return the count for testing


# Fixtures for database testing
@pytest.fixture
def mock_database():
    """Fixture to set up a mock database environment"""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    # Configure the cursor's fetchone to return a count
    cursor.fetchone.return_value = [5]  # Simulating 5 rows inserted

    return {
        'connection': conn,
        'cursor': cursor
    }


@pytest.fixture
def sample_data():
    """Fixture providing sample data for testing"""
    return {
        'headers': ['id', 'name', 'value'],
        'data': [
            {'id': 1, 'name': 'item1', 'value': 100},
            {'id': 2, 'name': 'item2', 'value': 200},
            {'id': 3, 'name': 'item3', 'value': 300},
            {'id': 4, 'name': 'item4', 'value': 400},
            {'id': 5, 'name': 'item5', 'value': 500},
        ]
    }


# Testing the row count validation logic
def test_validation_with_matching_counts(sample_data):
    """Test that validation passes when source and data counts match"""
    # Setup
    headers = sample_data['headers']
    data = sample_data['data']
    source_count = len(data)

    # Execute
    result = insert_data_into_table_with_validation(
        conn=MagicMock(),
        table_name="test_table",
        headers=headers,
        data=data,
        source_count=source_count
    )

    # Verify
    assert result == source_count


def test_validation_with_mismatched_counts(sample_data):
    """Test that validation fails when source and data counts don't match"""
    # Setup
    headers = sample_data['headers']
    data = sample_data['data']
    incorrect_source_count = len(data) + 1  # One more than actual

    # Execute and verify exception
    with pytest.raises(ValueError, match="Row count mismatch"):
        insert_data_into_table_with_validation(
            conn=MagicMock(),
            table_name="test_table",
            headers=headers,
            data=data,
            source_count=incorrect_source_count
        )


def test_validation_without_source_count(sample_data):
    """Test that validation is skipped when no source_count is provided"""
    # Setup
    headers = sample_data['headers']
    data = sample_data['data']

    # Execute
    result = insert_data_into_table_with_validation(
        conn=MagicMock(),
        table_name="test_table",
        headers=headers,
        data=data,
        source_count=None  # No source count provided
    )

    # Verify function executes without error
    assert result == len(data)


# Integration test with database mock
def test_database_integration(mock_database, sample_data):
    """
    Test a more complete simulation of the database integration.
    This is a more advanced test showing how pytest can handle complex scenarios.
    """

    # This would be the actual implementation in your code
    def full_implementation(conn, table_name, headers, data, source_count=None):
        if source_count is not None and len(data) != source_count:
            raise ValueError(f"Row count mismatch before insertion")

        # Simulate insertion by calling cursor.execute() multiple times
        cursor = conn.cursor()
        for row in data:
            cursor.execute(f"INSERT INTO {table_name} ...")

        # Verify inserted count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        inserted_count = cursor.fetchone()[0]

        if source_count is not None and inserted_count != source_count:
            conn.rollback()
            raise ValueError(f"Row count mismatch after insertion")

        conn.commit()
        return inserted_count

    # Setup test data
    conn = mock_database['connection']
    headers = sample_data['headers']
    data = sample_data['data']
    source_count = len(data)

    # Test the happy path
    result = full_implementation(conn, "test_table", headers, data, source_count)
    assert result == 5
    conn.commit.assert_called_once()

    # Test mismatch scenario (we need to reset our mock)
    conn.reset_mock()
    # Make the database return a different count than expected
    mock_database['cursor'].fetchone.return_value = [4]  # Only 4 rows inserted

    with pytest.raises(ValueError, match="Row count mismatch after insertion"):
        full_implementation(conn, "test_table", headers, data, source_count)

    # Verify transaction was rolled back
    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()