import pytest
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rdbms.parser import parse

def test_create_table_basic():
    sql = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT UNIQUE);"
    ast = parse(sql)
    assert ast["action"] == "create_table"
    assert ast["table"] == "users"
    assert "id" in ast["columns"]
    assert ast["columns"]["id"]["primary_key"] is True
    assert ast["columns"]["name"]["unique"] is True
    assert ast["table_constraints"] == []

def test_create_table_with_composite_unique():
    sql = "CREATE TABLE orders (order_id INTEGER, buyer TEXT, UNIQUE(order_id, buyer));"
    ast = parse(sql)
    assert ast["action"] == "create_table"
    assert ast["table"] == "orders"
    assert any(c["type"] == "unique" and c["columns"] == ["order_id", "buyer"]
               for c in ast["table_constraints"])

def test_insert_with_quotes_and_commas():
    sql = "INSERT INTO users (id, name, email) VALUES (1, 'O''Brien', 'obrien@example.com');"
    ast = parse(sql)
    assert ast["action"] == "insert"
    assert ast["table"] == "users"
    assert ast["row"]["name"] == "O'Brien"
    assert ast["row"]["email"] == "obrien@example.com"

def test_select_simple():
    sql = "SELECT * FROM users WHERE id=1;"
    ast = parse(sql)
    assert ast["action"] == "select"
    assert ast["table"] == "users"
    assert ast["condition"]["column"] == "id"
    assert ast["condition"]["value"] == "1"

def test_select_join_with_condition():
    sql = ("SELECT users.name, events.title FROM users "
           "INNER JOIN events ON users.id = events.user_id "
           "WHERE events.title='Meetup';")
    ast = parse(sql)
    assert ast["action"] == "select_join"
    assert "users.name" in ast["columns"]
    assert ast["left_table"] == "users"
    assert ast["right_table"] == "events"
    assert ast["on"]["left"] == "users.id"
    assert ast["on"]["right"] == "events.user_id"
    assert ast["condition"]["column"] == "events.title"
    assert ast["condition"]["value"] == "Meetup"

def test_update_multiple_assignments():
    sql = "UPDATE users SET name='Alice', email='alice@example.com' WHERE id=1;"
    ast = parse(sql)
    assert ast["action"] == "update"
    assert ast["table"] == "users"
    assert ast["set"]["name"] == "Alice"
    assert ast["set"]["email"] == "alice@example.com"
    assert ast["condition"]["column"] == "id"
    assert ast["condition"]["value"] == "1"

def test_delete():
    sql = "DELETE FROM users WHERE id=1;"
    ast = parse(sql)
    assert ast["action"] == "delete"
    assert ast["table"] == "users"
    assert ast["condition"]["column"] == "id"
    assert ast["condition"]["value"] == "1"