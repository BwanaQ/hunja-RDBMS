from rdbms.parser import parse
from rdbms.executor import Executor

def run_repl():
    exec = Executor()
    print("MiniRDBMS v0.1 — type SQL or .help")
    while True:
        try:
            line = input("db> ").strip()
            if not line:
                continue
            if line.startswith("."):
                if line == ".help":
                    print("Commands: .help, .tables, .schema <table>")
                elif line == ".tables":
                    print(exec.catalog.list_tables())
                else:
                    print("Unknown meta command.")
                continue
            ast = parse(line)
            exec.execute(ast)
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        except Exception as e:
            print(f"Error: {e}")