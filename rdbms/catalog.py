import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

CATALOG_FILE = os.path.join(DATA_DIR, "catalog.json")

class Catalog:
    def __init__(self):
        if not os.path.exists(CATALOG_FILE):
            with open(CATALOG_FILE, "w") as f:
                json.dump({}, f)
        self._load()

    def _load(self):
        with open(CATALOG_FILE, "r") as f:
            self.tables = json.load(f)

    def _save(self):
        with open(CATALOG_FILE, "w") as f:
            json.dump(self.tables, f, indent=2)

    def create_table(self, name, schema):
        if name in self.tables:
            raise ValueError(f"Table {name} already exists")
        self.tables[name] = schema
        self._save()

    def drop_table(self, name):
        if name not in self.tables:
            raise ValueError(f"Table {name} does not exist")
        del self.tables[name]
        self._save()

    def list_tables(self):
        return list(self.tables.keys())

    def get_schema(self, name):
        return self.tables.get(name)