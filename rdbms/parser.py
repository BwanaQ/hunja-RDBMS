# rdbms/parser.py

import re

def parse(sql):
    sql = sql.strip().rstrip(";")
    tokens = sql.split()
    command = tokens[0].upper()

    if command == "CREATE":
        return _parse_create(sql)
    elif command == "INSERT":
        return {"action": "insert", "raw": sql}
    elif command == "SELECT":
        return {"action": "select", "raw": sql}
    elif command == "UPDATE":
        return {"action": "update", "raw": sql}
    elif command == "DELETE":
        return {"action": "delete", "raw": sql}
    else:
        return {"action": "unknown", "raw": sql}

def _parse_create(sql):
    # Example: CREATE TABLE events (id INTEGER PRIMARY KEY, name TEXT UNIQUE, date DATE);
    match = re.match(r"CREATE TABLE (\w+)\s*\((.+)\)", sql, re.IGNORECASE)
    if not match:
        raise ValueError("Invalid CREATE TABLE syntax")

    table_name = match.group(1)
    cols_def = match.group(2)

    columns = {}
    for col_def in cols_def.split(","):
        parts = col_def.strip().split()
        col_name = parts[0]
        col_type = parts[1].upper()
        constraints = {"primary_key": False, "unique": False}
        if "PRIMARY" in [p.upper() for p in parts]:
            constraints["primary_key"] = True
        if "UNIQUE" in [p.upper() for p in parts]:
            constraints["unique"] = True
        columns[col_name] = {"type": col_type, **constraints}

    return {
        "action": "create_table",
        "table": table_name,
        "columns": columns
    }