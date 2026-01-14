import re

def parse(sql):
    sql = sql.strip().rstrip(";")
    tokens = sql.split()
    if not tokens:
        return {"action": "unknown", "raw": sql}
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
    elif command == "DROP":
        return _parse_drop(sql)
    else:
        return {"action": "unknown", "raw": sql}

def _split_top_level(defs: str):
    """Split by commas that are not inside parentheses."""
    parts, buf, depth = [], "", 0
    for ch in defs:
        if ch == "(":
            depth += 1
            buf += ch
        elif ch == ")":
            depth = max(0, depth - 1)
            buf += ch
        elif ch == "," and depth == 0:
            parts.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf.strip())
    return parts

def _parse_create(sql):
    match = re.match(r"CREATE TABLE (\w+)\s*\((.+)\)$", sql.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("Invalid CREATE TABLE syntax")

    table_name = match.group(1)
    cols_def = match.group(2)

    columns = {}
    table_constraints = []

    for col_def in _split_top_level(cols_def):
        col_def = col_def.strip()

        uniq_match = re.match(r"^UNIQUE\s*\((.+)\)$", col_def, re.IGNORECASE)
        if uniq_match:
            cols = [c.strip() for c in uniq_match.group(1).split(",")]
            if not cols or any(not c for c in cols):
                raise ValueError(f"Invalid UNIQUE constraint: {col_def}")
            table_constraints.append({"type": "unique", "columns": cols})
            continue

        parts = col_def.split()
        if len(parts) < 2:
            raise ValueError(f"Invalid column definition: {col_def}")

        col_name = parts[0]
        col_type = parts[1].upper()
        constraints = {"primary_key": False, "unique": False}

        upper_parts = [p.upper() for p in parts[2:]]
        if "PRIMARY" in upper_parts and "KEY" in upper_parts:
            constraints["primary_key"] = True
        if "UNIQUE" in upper_parts:
            constraints["unique"] = True

        columns[col_name] = {"type": col_type, **constraints}

    return {
        "action": "create_table",
        "table": table_name,
        "columns": columns,
        "table_constraints": table_constraints
    }

def _parse_insert(sql):
    match = re.match(r"INSERT INTO (\w+)\s*\((.+)\)\s*VALUES\s*\((.+)\)$", sql.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("Invalid INSERT syntax")

    table_name = match.group(1)
    cols = [c.strip() for c in match.group(2).split(",")]
    vals_raw = match.group(3)

    vals = _tokenize_top_level(vals_raw, sep=",")
    vals = [_strip_quotes(v) for v in vals]

    row = dict(zip(cols, vals))
    return {"action": "insert", "table": table_name, "row": row}

def _parse_select(sql):
    sql = re.sub(r"\s+", " ", sql.strip())

    join_match = re.match(
        r"SELECT\s+(.+)\s+FROM\s+(\w+)\s+INNER\s+JOIN\s+(\w+)\s+ON\s+(\w+\.\w+)\s*=\s*(\w+\.\w+)(?:\s+WHERE\s+(.+))?$",
        sql, re.IGNORECASE
    )
    if join_match:
        cols_raw = join_match.group(1)
        left_table = join_match.group(2)
        right_table = join_match.group(3)
        left_on = join_match.group(4)
        right_on = join_match.group(5)
        where_clause = join_match.group(6)

        columns = [c.strip() for c in cols_raw.split(",")]

        condition = None
        if where_clause:
            cond_match = re.match(r"(\w+(?:\.\w+)?)\s*=\s*'?(.*?)'?$", where_clause.strip())
            if not cond_match:
                raise ValueError("Only simple WHERE col=value supported")
            condition = {"column": cond_match.group(1), "value": cond_match.group(2)}

        return {
            "action": "select_join",
            "columns": columns,
            "left_table": left_table,
            "right_table": right_table,
            "on": {"left": left_on, "right": right_on},
            "condition": condition
        }

    match = re.match(r"SELECT\s+\*\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?$", sql, re.IGNORECASE)
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

    return {"action": "select", "table": table_name, "condition": condition}

def _parse_update(sql):
    m = re.match(r"UPDATE\s+(\w+)\s+SET\s+(.+?)\s+WHERE\s+(.+)$", sql.strip(), re.IGNORECASE)
    if not m:
        raise ValueError("Invalid UPDATE syntax")

    table_name = m.group(1)
    set_clause = m.group(2).strip()
    where_clause = m.group(3).strip()

    assignments = _tokenize_top_level(set_clause, sep=",")
    set_map = {}
    for a in assignments:
        if "=" not in a:
            raise ValueError(f"Invalid assignment in SET: {a}")
        col, val = a.split("=", 1)
        set_map[col.strip()] = _strip_quotes(val.strip())

    where_match = re.match(r"(\w+)\s*=\s*(.+)$", where_clause)
    if not where_match:
        raise ValueError("Only simple WHERE col=value supported")
    where_col = where_match.group(1)
    where_val = _strip_quotes(where_match.group(2).strip())

    return {"action": "update", "table": table_name, "set": set_map,
            "condition": {"column": where_col, "value": where_val}}

def _parse_delete(sql):
    match = re.match(r"DELETE\s+FROM\s+(\w+)\s+WHERE\s+(\w+)\s*=\s*'?(.*?)'?$", sql.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("Invalid DELETE syntax")

    table_name = match.group(1)
    where_col = match.group(2)
    where_val = match.group(3)

    return {"action": "delete", "table": table_name,
            "condition": {"column": where_col, "value": where_val}}

def _parse_drop(sql):
    match = re.match(r"DROP TABLE (\w+)$", sql.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("Invalid DROP TABLE syntax")
    table_name = match.group(1)
    return {"action": "drop_table", "table": table_name}

# Helpers
def _tokenize_top_level(s: str, sep=","):
    parts, buf, depth, in_quotes = [], [], 0, False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "'" and not in_quotes:
            in_quotes = True
            buf.append(ch)
            i += 1
            while i < len(s):
                buf.append(s[i])
                if s[i] == "'" and i + 1 < len(s) and s[i+1] == "'":
                    buf.append(s[i+1])
                    i += 2
                    continue
                if s[i] == "'":
                    i += 1
                    break
                i += 1
            in_quotes = False
            continue
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == sep and depth == 0 and not in_quotes:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        i += 1
    if buf:
        parts.append("".join(buf).strip())
    return parts

def _strip_quotes(val: str):
    val = val.strip()
    if len(val) >= 2 and val[0] == "'" and val[-1] == "'":
        inner = val[1:-1]
        return inner.replace("''", "'")
    return val