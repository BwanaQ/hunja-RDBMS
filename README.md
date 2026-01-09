# MiniRDBMS

A lightweight relational database management system (RDBMS) implemented in Python.  
This project is built as part of the Pesapal JDEV26 challenge to demonstrate clear thinking, determination, and systems design skills.

## Features

- Table creation and deletion (`CREATE TABLE`, `DROP TABLE`)
- Supported column types: `INTEGER`, `TEXT`, `BOOLEAN`, `FLOAT`, `DATE`
- CRUD operations (`INSERT`, `SELECT`, `UPDATE`, `DELETE`)
- Primary key and unique constraints
- Basic indexing (`CREATE INDEX`, `DROP INDEX`)
- Simple joins (nested loop implementation)
- Interactive REPL with SQL‑like syntax
- Trivial web app demo (Flask) showcasing CRUD and joins

## Quickstart

```bash
git clone https://github.com/BwanaQ/hunja-RDBMS.git
cd hunja-RDBMS
python -m rdbms.repl