# rdbms/executor.py
from rdbms.catalog import Catalog
from rdbms.storage import Storage
import os, json

class Executor:
    def __init__(self):
        self.catalog = Catalog()
        self.storage = Storage()

    def execute(self, ast):
        action = ast["action"]

        if action == "create_table":
            table = ast["table"]
            columns = ast["columns"]
            self.catalog.create_table(table, {"columns": columns})
            print(f"Table '{table}' created with columns: {list(columns.keys())}")

        elif action == "insert":
            table = ast["table"]
            row = ast["row"]
            schema = self.catalog.get_schema(table)
            if not schema:
                raise ValueError(f"Table {table} does not exist")
            # TODO: enforce constraints later
            self.storage.insert(table, row)
            print(f"Row inserted into '{table}': {row}")

        elif action == "select":
            table = ast["table"]
            condition = ast.get("condition")
            rows = self.storage.read_all(table)
            if not rows:
                print(f"No rows found in '{table}'")
                return
            for r in rows:
                if condition:
                    col, val = condition["column"], condition["value"]
                    if str(r.get(col)) == val:
                        print(r)
                else:
                    print(r)

        elif action == "update":
            table = ast["table"]
            set_clause = ast["set"]
            condition = ast["condition"]

            rows = self.storage.read_all(table)
            updated = False
            new_rows = []
            for r in rows:
                if str(r.get(condition["column"])) == condition["value"]:
                    r.update(set_clause)
                    updated = True
                new_rows.append(r)

            # Rewrite file
            file = self.storage._table_file(table)
            with open(file, "w") as f:
                for row in new_rows:
                    f.write(json.dumps(row) + "\n")

            if updated:
                print(f"Rows in '{table}' updated where {condition['column']}={condition['value']}")
            else:
                print(f"No matching rows found in '{table}'")

        elif action == "delete":
            table = ast["table"]
            condition = ast["condition"]

            rows = self.storage.read_all(table)
            new_rows = [r for r in rows if str(r.get(condition["column"])) != condition["value"]]

            file = self.storage._table_file(table)
            with open(file, "w") as f:
                for row in new_rows:
                    f.write(json.dumps(row) + "\n")

            deleted_count = len(rows) - len(new_rows)
            if deleted_count > 0:
                print(f"Deleted {deleted_count} row(s) from '{table}' where {condition['column']}={condition['value']}")
            else:
                print(f"No matching rows found in '{table}'")


        else:
            print("Unknown command.")