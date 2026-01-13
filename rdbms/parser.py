import re

def parse(sql):
    sql = sql.strip().rstrip(";")
    tokens = sql.split()
    command = tokens[0].upper()

    if command == "CREATE":
        return _parse_create(sql)
    elif command == "INSERT":
        return _parse_insert(sql)
    elif command == "SELECT":
        return _parse_select(sql)
    elif command == "UPDATE":
        return _parse_update(sql)
    elif command == "DELETE":
        return _parse_delete(sql)
    else:
        return {"action": "unknown", "raw": sql}

def _parse_create(sql):
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

def _parse_insert(sql):
    match = re.match(r"INSERT INTO (\w+)\s*\((.+)\)\s*VALUES\s*\((.+)\)", sql, re.IGNORECASE)
    if not match:
        raise ValueError("Invalid INSERT syntax")

    table_name = match.group(1)
    cols = [c.strip() for c in match.group(2).split(",")]
    vals_raw = match.group(3)

    # Split values by commas, respecting quotes
    vals = []
    current = ""
    in_quotes = False
    for ch in vals_raw:
        if ch == "'" and not in_quotes:
            in_quotes = True
        elif ch == "'" and in_quotes:
            in_quotes = False
            vals.append(current.strip())   # store cleaned value
            current = ""
        elif ch == "," and not in_quotes:
            if current.strip():
                vals.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        vals.append(current.strip())

    row = dict(zip(cols, vals))
    return {"action": "insert", "table": table_name, "row": row}

def _parse_select(sql):
    # Supports: SELECT * FROM table [WHERE col=value]
    match = re.match(r"SELECT\s+\*\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?", sql, re.IGNORECASE)
    if not match:
        raise ValueError("Invalid SELECT syntax")

    table_name = match.group(1)
    where_clause = match.group(2)

    condition = None
    if where_clause:
        cond_match = re.match(r"(\w+)\s*=\s*'?(.*?)'?$", where_clause.strip())
        if not cond_match:
            raise ValueError("Only simple WHERE col=value supported")
        condition = {"column": cond_match.group(1), "value": cond_match.group(2)}

    return {
        "action": "select",
        "table": table_name,
        "condition": condition
    }
def _parse_update(sql):
    # Example: UPDATE events SET name='Updated Meetup' WHERE id=1;
    match = re.match(r"UPDATE\s+(\w+)\s+SET\s+(\w+)\s*=\s*'?(.*?)'?\s+WHERE\s+(\w+)\s*=\s*'?(.*?)'?$", sql, re.IGNORECASE)
    if not match:
        raise ValueError("Invalid UPDATE syntax")

    table_name = match.group(1)
    set_col = match.group(2)
    set_val = match.group(3)
    where_col = match.group(4)
    where_val = match.group(5)

    return {
        "action": "update",
        "table": table_name,
        "set": {set_col: set_val},
        "condition": {"column": where_col, "value": where_val}
    }

def _parse_delete(sql):
    # Example: DELETE FROM events WHERE id=1;
    match = re.match(r"DELETE\s+FROM\s+(\w+)\s+WHERE\s+(\w+)\s*=\s*'?(.*?)'?$", sql, re.IGNORECASE)
    if not match:
        raise ValueError("Invalid DELETE syntax")

    table_name = match.group(1)
    where_col = match.group(2)
    where_val = match.group(3)

    return {
        "action": "delete",
        "table": table_name,
        "condition": {"column": where_col, "value": where_val}
    }
