import os, sys
import json
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rdbms.storage import Storage, DATA_DIR

@pytest.fixture
def storage():
    return Storage()

@pytest.fixture(autouse=True)
def cleanup():
    # Clean up any leftover files before and after each test
    yield
    for f in os.listdir(DATA_DIR):
        if f.endswith(".db"):
            os.remove(os.path.join(DATA_DIR, f))

def test_insert_and_read_all(storage):
    table = "test_users"
    row1 = {"id": 1, "name": "Alice"}
    row2 = {"id": 2, "name": "Bob"}

    storage.insert(table, row1)
    storage.insert(table, row2)

    rows = storage.read_all(table)
    assert rows == [row1, row2]

def test_read_all_empty_table(storage):
    table = "nonexistent"
    rows = storage.read_all(table)
    assert rows == []

def test_drop_table_removes_file(storage):
    table = "temp"
    row = {"id": 1, "name": "Temp"}
    storage.insert(table, row)

    file_path = storage._table_file(table)
    assert os.path.exists(file_path)

    storage.drop_table(table)
    assert not os.path.exists(file_path)

def test_insert_appends_rows(storage):
    table = "append_test"
    row1 = {"id": 1, "val": "first"}
    row2 = {"id": 2, "val": "second"}

    storage.insert(table, row1)
    storage.insert(table, row2)

    # Verify file contents are two JSON lines
    file_path = storage._table_file(table)
    with open(file_path, "r") as f:
        lines = f.readlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == row1
    assert json.loads(lines[1]) == row2