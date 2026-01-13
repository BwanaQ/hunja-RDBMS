# rdbms/repl.py
import os
import shutil

from rdbms.parser import parse
from rdbms.executor import Executor
from rdbms.catalog import Catalog

DATA_DIR = "data"

def run_repl():
    exec = Executor()
    catalog = Catalog()
    print("MiniRDBMS v0.2 — type SQL or .help")
    while True:
        try:
            line = input("db> ").strip()
            if not line:
                continue

            # Meta commands
            if line.startswith("."):
                if line == ".help":
                    print("Commands: .help, .tables, .schema [table], .quit")
                elif line == ".tables":
                    tables = catalog.list_tables()
                    if tables:
                        print(" ".join(tables))
                    else:
                        print("No tables found.")

                elif line.startswith(".schema"):
                    parts = line.split()
                    if len(parts) == 1:
                        # Show all tables
                        schema = catalog.load()
                        for table, meta in schema.items():
                            print(f"Table '{table}': {meta['columns']}")
                    elif len(parts) == 2:
                        table = parts[1]
                        schema = catalog.get_schema(table)
                        if schema:
                            print(f"Schema for '{table}': {schema['columns']}")
                        else:
                            print(f"No such table: {table}")
                    else:
                        print("Usage: .schema [table]")
                elif line == ".reset":
                    if os.path.exists(DATA_DIR):
                        shutil.rmtree(DATA_DIR)
                        print("Data folder wiped. All tables and rows removed.")
                    else:
                        print("No data folder found.")
        
                elif line == ".quit":
                    print("Bye.")
                    break
                else:
                    print("Unknown meta command.")
                continue

            # SQL execution
            ast = parse(line)
            exec.execute(ast)

        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_repl()