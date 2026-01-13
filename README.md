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
```
## Example session:
```bash
CREATE TABLE events (
  id INTEGER PRIMARY KEY,
  name TEXT,
  date DATE
);

INSERT INTO events (id, name, date)
VALUES (1, 'Kitui Tech Meetup', '2026-01-20');

SELECT * FROM events;
```
## 🌐 Web Demo

Run the Flask app:
```bash
cd webapp
python app.py
```

## Endpoints:
```bash
/events → list/create events

/tickets → list/create tickets (with join to events)
```

## 📂 Repository Structure
```bash
rdbms/
├─ README.md
├─ docs/
│  ├─ design.md
│  ├─ sql_grammar.md
├─ rdbms/        # Core engine
├─ webapp/       # Flask demo
├─ tests/        # Unit tests
└─ examples/     # Demo SQL scripts
```
## ⚠️ Limitations

No transaction support (atomic file writes only)

Joins limited to inner joins

Indexes support equality lookups only

SQL grammar is a simplified subset

## 🙌 Credits

Inspired by SQLite architecture and educational RDBMS projects

Built in Python 3.12

