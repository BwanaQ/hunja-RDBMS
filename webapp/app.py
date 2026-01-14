from flask import Flask, render_template, request, redirect, url_for
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rdbms.parser import parse
from rdbms.executor import Executor

app = Flask(__name__)
executor = Executor()

# Escape helper for all string inputs
def escape(value):
    if value is None:
        return ""
    return value.replace("'", "''").replace('"', '""')

# Ensure demo tables exist
def init_schema():
    try:
        executor.execute(parse("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT UNIQUE, email TEXT);"))
        executor.execute(parse("CREATE TABLE events (id INTEGER PRIMARY KEY, title TEXT, date DATE);"))
        executor.execute(parse("CREATE TABLE tickets (id INTEGER PRIMARY KEY, event_id INTEGER, buyer_name TEXT, UNIQUE(event_id, buyer_name));"))
    except Exception:
        pass

init_schema()

@app.route("/")
def index():
    return render_template("base.html")

# ---------------- USERS ----------------
@app.route("/users")
def users():
    rows = executor.storage.read_all("users")
    return render_template("users.html", users=rows)

@app.route("/users/add", methods=["POST"])
def add_user():
    # Read existing rows to compute next id
    rows = executor.storage.read_all("users")
    # Determine next id (assume stored ids are strings or ints)
    max_id = 0
    for r in rows:
        try:
            rid = int(r.get("id"))
            if rid > max_id:
                max_id = rid
        except Exception:
            continue
    next_id = max_id + 1

    # Escape/sanitize inputs as before
    name = escape(request.form.get("name", ""))
    email = escape(request.form.get("email", ""))

    # Build and execute INSERT using the computed id
    sql = f"INSERT INTO users (id, name, email) VALUES ({next_id}, '{name}', '{email}');"
    result = executor.execute(parse(sql))
    if not result.get("ok"):
        # If you want to surface errors to the UI, you can flash result["error"]
        # For now, just redirect back to users page
        return redirect(url_for("users"))
    return redirect(url_for("users"))


@app.route("/users/delete/<id>")
def delete_user(id):
    executor.execute(parse(f"DELETE FROM users WHERE id={id};"))
    return redirect(url_for("users"))

@app.route("/users/edit/<id>")
def edit_user(id):
    rows = executor.storage.read_all("users")
    user = next((u for u in rows if u["id"] == id), None)
    return render_template("edit_user.html", user=user)

@app.route("/users/update/<id>", methods=["POST"])
def update_user(id):
    name = escape(request.form["name"])
    email = escape(request.form["email"])
    sql = f"UPDATE users SET name='{name}', email='{email}' WHERE id={id};"
    executor.execute(parse(sql))
    return redirect(url_for("users"))

# ---------------- EVENTS ----------------
@app.route("/events")
def events():
    rows = executor.storage.read_all("events")
    return render_template("events.html", events=rows)

@app.route("/events/add", methods=["POST"])
def add_event():
    # Compute next id from existing rows
    rows = executor.storage.read_all("events")
    max_id = 0
    for r in rows:
        try:
            rid = int(r.get("id"))
            if rid > max_id:
                max_id = rid
        except Exception:
            continue
    next_id = max_id + 1

    # Sanitize inputs
    title = escape(request.form.get("title", ""))
    date = escape(request.form.get("date", ""))

    # Build and execute INSERT with server-assigned id
    sql = f"INSERT INTO events (id, title, date) VALUES ({next_id}, '{title}', '{date}');"
    result = executor.execute(parse(sql))
    # Optionally surface errors to the UI; for now redirect back
    return redirect(url_for("events"))

@app.route("/events/delete/<id>")
def delete_event(id):
    executor.execute(parse(f"DELETE FROM events WHERE id={id};"))
    return redirect(url_for("events"))

@app.route("/events/edit/<id>")
def edit_event(id):
    rows = executor.storage.read_all("events")
    event = next((e for e in rows if e["id"] == id), None)
    return render_template("edit_event.html", event=event)

@app.route("/events/update/<id>", methods=["POST"])
def update_event(id):
    title = escape(request.form["title"])
    date = escape(request.form["date"])
    sql = f"UPDATE events SET title='{title}', date='{date}' WHERE id={id};"
    executor.execute(parse(sql))
    return redirect(url_for("events"))

# ---------------- TICKETS ----------------
# Tickets listing: include users and events so template can render dropdown labels
@app.route("/tickets")
def tickets():
    tickets = executor.storage.read_all("tickets")
    events = executor.storage.read_all("events")
    users = executor.storage.read_all("users")
    return render_template("tickets.html", tickets=tickets, events=events, users=users)

# Add ticket: compute next id server-side and use dropdown values
@app.route("/tickets/add", methods=["POST"])
def add_ticket():
    # compute next id
    rows = executor.storage.read_all("tickets")
    max_id = 0
    for r in rows:
        try:
            rid = int(r.get("id"))
            if rid > max_id:
                max_id = rid
        except Exception:
            continue
    next_id = max_id + 1

    # get selected values (from dropdowns)
    event_id = request.form.get("event_id")
    buyer_id = request.form.get("buyer_id")

    # basic validation: ensure numeric ids
    try:
        event_id_int = int(event_id)
        buyer_id_int = int(buyer_id)
    except Exception:
        return redirect(url_for("tickets"))

    # Build and execute INSERT using server-assigned id
    sql = f"INSERT INTO tickets (id, event_id, buyer_name) VALUES ({next_id}, {event_id_int}, '{escape(str(buyer_id_int))}');"
    # Note: buyer_name in schema is a TEXT; we store buyer id as buyer_name if you want buyer name instead,
    # see alternative below to store buyer name label instead of id.
    executor.execute(parse(sql))
    return redirect(url_for("tickets"))

# Delete unchanged
@app.route("/tickets/delete/<id>")
def delete_ticket(id):
    executor.execute(parse(f"DELETE FROM tickets WHERE id={id};"))
    return redirect(url_for("tickets"))

# Edit: provide events and users so edit form can show dropdowns with current selection
@app.route("/tickets/edit/<id>")
def edit_ticket(id):
    rows = executor.storage.read_all("tickets")
    ticket = next((t for t in rows if str(t.get("id")) == str(id)), None)
    events = executor.storage.read_all("events")
    users = executor.storage.read_all("users")
    return render_template("edit_ticket.html", ticket=ticket, events=events, users=users)

# Update: validate dropdown values and apply update
@app.route("/tickets/update/<id>", methods=["POST"])
def update_ticket(id):
    event_id = request.form.get("event_id")
    buyer_id = request.form.get("buyer_id")

    try:
        event_id_int = int(event_id)
        buyer_id_int = int(buyer_id)
    except Exception:
        return redirect(url_for("tickets"))

    # If you want to store buyer name instead of buyer id, look up the user and use their name:
    # users = executor.storage.read_all("users")
    # buyer_row = next((u for u in users if str(u.get("id")) == str(buyer_id_int)), None)
    # buyer_value = escape(buyer_row.get("name")) if buyer_row else escape(str(buyer_id_int))
    buyer_value = escape(str(buyer_id_int))

    sql = f"UPDATE tickets SET event_id={event_id_int}, buyer_name='{buyer_value}' WHERE id={id};"
    executor.execute(parse(sql))
    return redirect(url_for("tickets"))

