from rdbms.catalog import Catalog
from rdbms.storage import Storage

class Executor:
    def __init__(self):
        self.catalog = Catalog()
        self.storage = Storage()

    def execute(self, ast):
        action = ast["action"]

        if action == "create_table":
            print("CREATE TABLE executed (stub).")
        elif action == "insert":
            print("INSERT executed (stub).")
        elif action == "select":
            print("SELECT executed (stub).")
        elif action == "update":
            print("UPDATE executed (stub).")
        elif action == "delete":
            print("DELETE executed (stub).")
        else:
            print("Unknown command.")