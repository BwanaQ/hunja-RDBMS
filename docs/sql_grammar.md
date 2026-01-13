# SQL Grammar (Subset)

This document defines the supported SQL‑like syntax for MiniRDBMS.

---

## Supported Statements

### Table Definition
```sql
CREATE TABLE table_name (
  column_name TYPE [PRIMARY KEY] [UNIQUE],
  ...
);

DROP TABLE table_name;

Data Manipulation

INSERT INTO table_name (col1, col2, ...)
VALUES (val1, val2, ...);

SELECT col1, col2
FROM table_name
[WHERE condition]
[JOIN other_table ON table.col = other_table.col];

UPDATE table_name
SET col1 = val1, col2 = val2
WHERE condition;

DELETE FROM table_name
WHERE condition;

Indexing

CREATE INDEX index_name ON table_name(column_name);
DROP INDEX index_name;

Data Types

INTEGER

TEXT

BOOLEAN

FLOAT

DATE (stored as ISO string YYYY-MM-DD)

Conditions

Equality: col = value

Conjunctions: AND, OR

Simple comparisons: <, >, <=, >= (optional stretch goal)

Joins

Inner join only:

SELECT a.col1, b.col2
FROM table_a a
JOIN table_b b ON a.id = b.a_id;

Meta Commands (REPL only)

.help → show help

.tables → list tables

.schema table_name → show schema
