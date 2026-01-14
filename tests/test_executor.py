import pytest
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rdbms.parser import parse
from rdbms.executor import Executor

# --- Helpers ---
def setup_users_table(ex):
    ast = parse("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT UNIQUE, email TEXT);")
    res = ex.execute(ast)
    assert res["ok"]

# --- Tests ---
def test_insert_and_select_roundtrip():
    ex = Executor()
    setup_users_table(ex)

    # Insert
    res = ex.execute(parse("INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"))
    assert res["ok"]
    assert res["result"]["row"]["name"] == "Alice"

    # Select
    res = ex.execute(parse("SELECT * FROM users WHERE id=1;"))
    assert res["ok"]
    rows = res["result"]
    assert len(rows) == 1
    assert rows[0]["email"] == "alice@example.com"

def test_unique_constraint_violation():
    ex = Executor()
    setup_users_table(ex)

    ex.execute(parse("INSERT INTO users (id, name, email) VALUES (1, 'Bob', 'bob@example.com');"))
    res = ex.execute(parse("INSERT INTO users (id, name, email) VALUES (2, 'Bob', 'bob2@example.com');"))
    assert not res["ok"]
    assert "unique" in res["error"].lower()

def test_primary_key_violation():
    ex = Executor()
    setup_users_table(ex)

    ex.execute(parse("INSERT INTO users (id, name, email) VALUES (1, 'Carol', 'c@example.com');"))
    res = ex.execute(parse("INSERT INTO users (id, name, email) VALUES (1, 'Dave', 'd@example.com');"))
    assert not res["ok"]
    assert "primary key" in res["error"].lower()

def test_update_changes_value_and_indexes():
    ex = Executor()
    setup_users_table(ex)
    ex.execute(parse("INSERT INTO users (id, name, email) VALUES (1, 'Eve', 'e@example.com');"))

    res = ex.execute(parse("UPDATE users SET email='eve@new.com' WHERE id=1;"))
    assert res["ok"]
    assert res["result"]["updated"]

    res = ex.execute(parse("SELECT * FROM users WHERE id=1;"))
    assert res["ok"]
    rows = res["result"]
    assert rows[0]["email"] == "eve@new.com"

def test_delete_removes_row_and_indexes():
    ex = Executor()
    setup_users_table(ex)
    ex.execute(parse("INSERT INTO users (id, name, email) VALUES (1, 'Frank', 'f@example.com');"))

    res = ex.execute(parse("DELETE FROM users WHERE id=1;"))
    assert res["ok"]
    assert res["result"]["deleted"] == 1

    res = ex.execute(parse("SELECT * FROM users;"))
    assert res["ok"]
    assert res["result"] == []

def test_drop_table_removes_schema_and_storage():
    ex = Executor()
    setup_users_table(ex)

    res = ex.execute(parse("DROP TABLE users;"))
    assert res["ok"]
    assert res["result"]["dropped"] == "users"

    # Selecting should now fail
    res = ex.execute(parse("SELECT * FROM users;"))
    assert not res["ok"]
    assert "does not exist" in res["error"].lower()

def test_drop_all_tables_helper():
    ex = Executor()
    ex.execute(parse("CREATE TABLE t1 (id INTEGER PRIMARY KEY);"))
    ex.execute(parse("CREATE TABLE t2 (id INTEGER PRIMARY KEY);"))

    res = ex.drop_all_tables()
    assert res["dropped_all"]

    # Both tables should be gone
    assert not ex.catalog.get_schema("t1")
    assert not ex.catalog.get_schema("t2")