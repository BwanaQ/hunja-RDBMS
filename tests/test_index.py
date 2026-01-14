import os
import json
import pytest
from rdbms.index import Index, DATA_DIR

@pytest.fixture(autouse=True)
def cleanup():
    # Clean up any leftover index files before and after each test
    yield
    for f in os.listdir(DATA_DIR):
        if f.endswith(".idx"):
            os.remove(os.path.join(DATA_DIR, f))

def test_index_file_created():
    idx = Index("users", "id")
    assert os.path.exists(idx.file)
    with open(idx.file, "r") as f:
        data = json.load(f)
    assert data == {}

def test_add_and_lookup_single_value():
    idx = Index("users", "id")
    idx.add(1, "0")
    result = idx.lookup(1)
    assert result == ["0"]

def test_add_multiple_values_and_lookup():
    idx = Index("orders", "buyer")
    idx.add("Alice", "0")
    idx.add("Alice", "1")
    idx.add("Bob", "2")

    assert set(idx.lookup("Alice")) == {"0", "1"}
    assert idx.lookup("Bob") == ["2"]
    assert idx.lookup("Charlie") == []

def test_remove_value():
    idx = Index("products", "sku")
    idx.add("ABC123", "0")
    idx.add("ABC123", "1")

    # Remove one row_id
    idx.remove("ABC123", "0")
    assert idx.lookup("ABC123") == ["1"]

    # Remove the last row_id -> key should disappear
    idx.remove("ABC123", "1")
    assert idx.lookup("ABC123") == []

def test_index_persists_between_instances():
    idx1 = Index("sessions", "token")
    idx1.add("xyz", "0")

    # Create a new Index object pointing to same file
    idx2 = Index("sessions", "token")
    assert idx2.lookup("xyz") == ["0"]