# rdbms/index.py
import os, json

DATA_DIR = "data"

class Index:
    def __init__(self, table, column):
        self.table = table
        self.column = column
        self.file = os.path.join(DATA_DIR, f"{table}_{column}.idx")
        if not os.path.exists(self.file):
            with open(self.file, "w") as f:
                json.dump({}, f)

    def _load(self):
        with open(self.file, "r") as f:
            return json.load(f)

    def _save(self, idx):
        with open(self.file, "w") as f:
            json.dump(idx, f)

    def add(self, value, row_id):
        idx = self._load()
        idx.setdefault(str(value), []).append(row_id)
        self._save(idx)

    def remove(self, value, row_id):
        idx = self._load()
        if str(value) in idx and row_id in idx[str(value)]:
            idx[str(value)].remove(row_id)
            if not idx[str(value)]:
                del idx[str(value)]
        self._save(idx)

    def lookup(self, value):
        idx = self._load()
        return idx.get(str(value), [])