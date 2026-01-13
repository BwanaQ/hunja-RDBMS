
---

## 📄 `docs/design.md`

```markdown
# Design Overview

MiniRDBMS is a simple relational database engine implemented in Python.  
It demonstrates core database concepts: storage, indexing, constraints, query parsing, and execution.

---

## Architecture

### Storage Engine
- **Data files:** One file per table (`data/<table>.db`) storing rows as JSON lines.
- **Catalog:** `catalog.json` stores table schemas, constraints, and index metadata.
- **Row IDs:** Monotonic integer per table for internal reference.

### Indexes
- **Hash indexes:** Dict‑like mapping for equality lookups (`col=value`).
- **Index files:** Stored separately (`index/<table>_<col>.idx`).
- **Maintenance:** Updated on insert/update/delete.

### Constraints
- **Primary key:** Enforced via index lookup.
- **Unique:** Checked before insert/update.

### Query Engine
- **Parser:** Tokenizer + recursive descent parser for subset SQL.
- **Executor:**
  - **Selection:** Table scan or index lookup.
  - **Projection:** Column filtering.
  - **Join:** Nested loop join (phase 1).
  - **Update/Delete:** Apply filters, rewrite rows, update indexes.

### REPL
- Interactive shell with command history.
- Supports `.help`, `.tables`, `.schema`.

### Web Demo
- Flask app using MiniRDBMS as backend.
- Routes for events and tickets.
- Demonstrates CRUD and join queries.

---

## Design Decisions
- **JSON storage:** Human‑readable, easy to debug.
- **Hash indexes:** Simple and efficient for equality queries.
- **Nested loop joins:** Straightforward to implement; sufficient for demo scale.
- **No transactions:** Simplifies implementation; atomic file writes only.
- **SQL subset:** Keeps parser small and deterministic.

---

## Roadmap
- Add range indexes for `<`, `>`, `BETWEEN`.
- Implement write‑ahead log for crash safety.
- Support outer joins.
- Add CSV import/export.
- Optimize query planner for join order.