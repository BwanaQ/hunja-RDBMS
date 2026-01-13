# rdbms/executor.py
import os
import json
import re

from rdbms.catalog import Catalog
from rdbms.storage import Storage
from rdbms.index import Index  # simple hash index per column

DATA_DIR = "data"


class Executor:
    def __init__(self):
        self.catalog = Catalog()
        self.storage = Storage()

    def execute(self, ast):
        try:
            action = ast["action"]

            if action == "create_table":
                self._create_table(ast)

            elif action == "insert":
                self._insert(ast)

            elif action == "select":
                self._select(ast)

            elif action == "update":
                self._update(ast)

            elif action == "delete":
                self._delete(ast)

            else:
                print("Unknown command.")

        except ValueError as ve:
            print(f"Error: {ve}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    # -----------------------------
    # Actions
    # -----------------------------

    def _create_table(self, ast):
        table = ast["table"]
        columns = ast["columns"]
        self.catalog.create_table(table, {"columns": columns})
        print(f"Table '{table}' created with columns: {list(columns.keys())}")

    def _insert(self, ast):
        table = ast["table"]
        row = ast["row"]
        schema = self.catalog.get_schema(table)
        if not schema:
            raise ValueError(f"Table '{table}' does not exist")

        rows = self.storage.read_all(table)

        # Constraints
        self._enforce_primary_key(schema, rows, row, table)
        self._enforce_unique(schema, rows, row, table)
        self._enforce_types(schema, row)

        # Persist
        self.storage.insert(table, row)
        print(f"Row inserted into '{table}': {row}")

        # Index maintenance: add for PK and UNIQUE columns
        row_id = len(rows)  # new row index after append
        for col, meta in schema["columns"].items():
            if meta.get("primary_key") or meta.get("unique"):
                idx = Index(table, col)
                idx.add(row.get(col), str(row_id))

    def _select(self, ast):
        table = ast["table"]
        condition = ast.get("condition")
        schema = self.catalog.get_schema(table)
        if not schema:
            raise ValueError(f"Table '{table}' does not exist")

        rows = self.storage.read_all(table)

        if not condition:
            for r in rows:
                print(r)
            return

        col, val = condition["column"], condition["value"]
        if col not in schema["columns"]:
            raise ValueError(f"Column '{col}' does not exist in table '{table}'")

        # Try index first
        idx_path = os.path.join(DATA_DIR, f"{table}_{col}.idx")
        if os.path.exists(idx_path):
            idx = Index(table, col)
            row_ids = idx.lookup(val)
            if not row_ids:
                print(f"No matching rows found in '{table}'")
                return
            for i, r in enumerate(rows):
                if str(i) in row_ids:
                    print(r)
        else:
            # Fallback: full scan
            matched = False
            for r in rows:
                if str(r.get(col)) == val:
                    print(r)
                    matched = True
            if not matched:
                print(f"No matching rows found in '{table}'")

    def _update(self, ast):
        table = ast["table"]
        set_clause = ast["set"]
        condition = ast["condition"]

        schema = self.catalog.get_schema(table)
        if not schema:
            raise ValueError(f"Table '{table}' does not exist")

        rows = self.storage.read_all(table)
        updated = False
        new_rows = []

        for i, r in enumerate(rows):
            if str(r.get(condition["column"])) == condition["value"]:
                # Prepare candidate row and type-check
                candidate = r.copy()
                candidate.update(set_clause)
                self._enforce_types(schema, candidate)

                # Incremental index maintenance for PK/UNIQUE columns
                for col, meta in schema["columns"].items():
                    if meta.get("primary_key") or meta.get("unique"):
                        old_val = r.get(col)
                        new_val = candidate.get(col)
                        if old_val != new_val:
                            idx = Index(table, col)
                            idx.remove(old_val, str(i))
                            idx.add(new_val, str(i))

                r = candidate
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

    def _delete(self, ast):
        table = ast["table"]
        condition = ast["condition"]

        schema = self.catalog.get_schema(table)
        if not schema:
            raise ValueError(f"Table '{table}' does not exist")

        rows = self.storage.read_all(table)
        new_rows = []
        deleted_count = 0

        for i, r in enumerate(rows):
            if str(r.get(condition["column"])) == condition["value"]:
                # Incremental index maintenance for PK/UNIQUE columns
                for col, meta in schema["columns"].items():
                    if meta.get("primary_key") or meta.get("unique"):
                        idx = Index(table, col)
                        idx.remove(r.get(col), str(i))
                deleted_count += 1
                continue  # skip (deleted)
            new_rows.append(r)

        # Rewrite file
        file = self.storage._table_file(table)
        with open(file, "w") as f:
            for row in new_rows:
                f.write(json.dumps(row) + "\n")

        # Note: row IDs shift after deletion; index now contains stale IDs.
        # To keep IDs accurate, we remap them once after deletions.
        # Lightweight remap: rebuild only if any deletions occurred.
        if deleted_count > 0:
            self._remap_index_ids_after_compaction(table, schema, new_rows)

        if deleted_count > 0:
            print(f"Deleted {deleted_count} row(s) from '{table}' where {condition['column']}={condition['value']}")
        else:
            print(f"No matching rows found in '{table}'")

    # -----------------------------
    # Helpers: constraints & types
    # -----------------------------

    def _enforce_primary_key(self, schema, rows, row, table):
        pk_cols = [c for c, meta in schema["columns"].items() if meta.get("primary_key")]
        for pk in pk_cols:
            for r in rows:
                if str(r.get(pk)) == str(row.get(pk)):
                    raise ValueError(f"Duplicate primary key '{pk}={row.get(pk)}' in table '{table}'")

    def _enforce_unique(self, schema, rows, row, table):
        unique_cols = [c for c, meta in schema["columns"].items() if meta.get("unique")]
        for uc in unique_cols:
            for r in rows:
                if str(r.get(uc)) == str(row.get(uc)):
                    raise ValueError(f"Duplicate unique value '{uc}={row.get(uc)}' in table '{table}'")

    def _enforce_types(self, schema, row):
        for col, meta in schema["columns"].items():
            val = row.get(col)
            if val is None:
                continue
            col_type = meta["type"].upper()

            if col_type == "INTEGER":
                if not str(val).isdigit():
                    raise ValueError(f"Column '{col}' expects INTEGER, got '{val}'")
            elif col_type == "FLOAT":
                try:
                    float(val)
                except ValueError:
                    raise ValueError(f"Column '{col}' expects FLOAT, got '{val}'")
            elif col_type == "BOOLEAN":
                if str(val).upper() not in ["TRUE", "FALSE"]:
                    raise ValueError(f"Column '{col}' expects BOOLEAN (TRUE/FALSE), got '{val}'")
            elif col_type == "DATE":
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(val)):
                    raise ValueError(f"Column '{col}' expects DATE (YYYY-MM-DD), got '{val}'")
            # TEXT accepts anything

    # -----------------------------
    # Helpers: index maintenance
    # -----------------------------

    def _rebuild_indexes(self, table, schema):
        # Only rebuild PK and UNIQUE indexes for simplicity
        indexed_cols = [c for c, m in schema["columns"].items() if m.get("primary_key") or m.get("unique")]
        if not indexed_cols:
            return

        rows = self.storage.read_all(table)

        for col in indexed_cols:
            idx = Index(table, col)
            # Reset index file
            with open(idx.file, "w") as f:
                json.dump({}, f)
            # Rebuild mappings
            for i, r in enumerate(rows):
                idx.add(r.get(col), str(i))

    def _remap_index_ids_after_compaction(self, table, schema, rows):
        """
        After deletions, row IDs shift. This remaps index entries to new row IDs.
        It’s a targeted rebuild using the in-memory 'rows' just written.
        """
        indexed_cols = [c for c, m in schema["columns"].items() if m.get("primary_key") or m.get("unique")]
        if not indexed_cols:
            return

        for col in indexed_cols:
            idx = Index(table, col)
            # Reset index file
            with open(idx.file, "w") as f:
                json.dump({}, f)
            # Rebuild mappings with new positions
            for i, r in enumerate(rows):
                idx.add(r.get(col), str(i))