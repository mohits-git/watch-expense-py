import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_ddb_table():
    table = MagicMock()
    table.meta.client = MagicMock()
    return table


@pytest.fixture
def table_name():
    return "test-watch-expense-table"
