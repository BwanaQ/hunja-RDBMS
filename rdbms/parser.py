def parse(sql):
    sql = sql.strip().rstrip(";")
    tokens = sql.split()
    command = tokens[0].upper()

    if command == "CREATE":
        return {"action": "create_table", "raw": sql}
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