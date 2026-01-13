import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

class Storage:
    def __init__(self):
        pass

    def _table_file(self, table):
        return os.path.join(DATA_DIR, f"{table}.db")

    def insert(self, table, row):
        file = self._table_file(table)
        with open(file, "a") as f:
            f.write(json.dumps(row) + "\n")

    def read_all(self, table):
        file = self._table_file(table)
        if not os.path.exists(file):
            return []
        with open(file, "r") as f:
            return [json.loads(line) for line in f]