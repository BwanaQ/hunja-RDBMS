from flask import Flask, render_template, request, redirect, url_for, flash
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rdbms.parser import parse
from rdbms.executor import Executor

app = Flask(__name__)
# Required for flash()
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

executor = Executor()

def run_sql_and_flash(sql, success_msg=None):
    """Execute SQL AST and flash error or optional success message."""
    res = executor.execute(parse(sql))
    if not res.get("ok"):
        flash(res.get("error", "Unknown error"), "error")
        return False
    if success_msg:
        flash(success_msg, "success")
    return True

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
        executor.execute(parse("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, event_id INTEGER, UNIQUE(user_id, event_id));"))

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
    max_id = 0
    for r in rows:
        try:
            rid = int(r.get("id"))
            if rid > max_id:
                max_id = rid
        except Exception:
            continue
    next_id = max_id + 1

    # Escape/sanitize inputs
    name = escape(request.form.get("name", ""))
    email = escape(request.form.get("email", ""))

    # Build and execute INSERT using the computed id
    sql = f"INSERT INTO users (id, name, email) VALUES ({next_id}, '{name}', '{email}');"
    run_sql_and_flash(sql, success_msg="User created.")
    return redirect(url_for("users"))

@app.route("/users/delete/<id>")
def delete_user(id):
    run_sql_and_flash(f"DELETE FROM users WHERE id={id};", success_msg="User deleted.")
    return redirect(url_for("users"))

@app.route("/users/edit/<id>")
def edit_user(id):
    rows = executor.storage.read_all("users")
    user = next((u for u in rows if str(u.get("id")) == str(id)), None)
    return render_template("edit_user.html", user=user)

@app.route("/users/update/<id>", methods=["POST"])
def update_user(id):
    name = escape(request.form.get("name", ""))
    email = escape(request.form.get("email", ""))
    sql = f"UPDATE users SET name='{name}', email='{email}' WHERE id={id};"
    run_sql_and_flash(sql, success_msg="User updated.")
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
    run_sql_and_flash(sql, success_msg="Event created.")
    return redirect(url_for("events"))

@app.route("/events/delete/<id>")
def delete_event(id):
    run_sql_and_flash(f"DELETE FROM events WHERE id={id};", success_msg="Event deleted.")
    return redirect(url_for("events"))

@app.route("/events/edit/<id>")
def edit_event(id):
    rows = executor.storage.read_all("events")
    event = next((e for e in rows if str(e.get("id")) == str(id)), None)
    return render_template("edit_event.html", event=event)

@app.route("/events/update/<id>", methods=["POST"])
def update_event(id):
    title = escape(request.form.get("title", ""))
    date = escape(request.form.get("date", ""))
    sql = f"UPDATE events SET title='{title}', date='{date}' WHERE id={id};"
    run_sql_and_flash(sql, success_msg="Event updated.")
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
        flash("Invalid event or buyer selection.", "error")
        return redirect(url_for("tickets"))

    # By default store buyer_id in buyer_name column (string). If you prefer the buyer's name,
    # look it up from users and store the name instead.
    buyer_value = escape(str(buyer_id_int))

    # Build and execute INSERT using server-assigned id
    sql = f"INSERT INTO tickets (id, event_id, buyer_name) VALUES ({next_id}, {event_id_int}, '{buyer_value}');"
    run_sql_and_flash(sql, success_msg="Ticket created.")
    return redirect(url_for("tickets"))

# Delete unchanged
@app.route("/tickets/delete/<id>")
def delete_ticket(id):
    run_sql_and_flash(f"DELETE FROM tickets WHERE id={id};", success_msg="Ticket deleted.")
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
        flash("Invalid event or buyer selection.", "error")
        return redirect(url_for("tickets"))

    # If you want to store buyer name instead of buyer id, look up the user and use their name:
    # users = executor.storage.read_all("users")
    # buyer_row = next((u for u in users if str(u.get("id")) == str(buyer_id_int)), None)
    # buyer_value = escape(buyer_row.get("name")) if buyer_row else escape(str(buyer_id_int))
    buyer_value = escape(str(buyer_id_int))

    sql = f"UPDATE tickets SET event_id={event_id_int}, buyer_name='{buyer_value}' WHERE id={id};"
    run_sql_and_flash(sql, success_msg="Ticket updated.")
    return redirect(url_for("tickets"))

# Orders listing: include users and events for dropdowns and joined display
@app.route("/orders")
def orders():
    orders = executor.storage.read_all("orders")
    events = executor.storage.read_all("events")
    users = executor.storage.read_all("users")
    return render_template("orders.html", orders=orders, events=events, users=users)

# Add order: compute next id server-side and validate foreign keys
@app.route("/orders/add", methods=["POST"])
def add_order():
    # compute next id
    rows = executor.storage.read_all("orders")
    max_id = 0
    for r in rows:
        try:
            rid = int(r.get("id"))
            if rid > max_id:
                max_id = rid
        except Exception:
            continue
    next_id = max_id + 1

    user_id = request.form.get("user_id")
    event_id = request.form.get("event_id")
    try:
        user_id_int = int(user_id)
        event_id_int = int(event_id)
    except Exception:
        flash("Invalid user or event selection.", "error")
        return redirect(url_for("orders"))

    # FK existence checks
    users = executor.storage.read_all("users")
    events = executor.storage.read_all("events")
    if not any(str(u.get("id")) == str(user_id_int) for u in users):
        flash("Selected user does not exist.", "error")
        return redirect(url_for("orders"))
    if not any(str(e.get("id")) == str(event_id_int) for e in events):
        flash("Selected event does not exist.", "error")
        return redirect(url_for("orders"))

    sql = f"INSERT INTO orders (id, user_id, event_id) VALUES ({next_id}, {user_id_int}, {event_id_int});"
    run_sql_and_flash(sql, success_msg="Order created.")
    return redirect(url_for("orders"))

# Delete order
@app.route("/orders/delete/<id>")
def delete_order(id):
    run_sql_and_flash(f"DELETE FROM orders WHERE id={id};", success_msg="Order deleted.")
    return redirect(url_for("orders"))

# Edit order: provide events and users for dropdowns
@app.route("/orders/edit/<id>")
def edit_order(id):
    rows = executor.storage.read_all("orders")
    order = next((o for o in rows if str(o.get("id")) == str(id)), None)
    events = executor.storage.read_all("events")
    users = executor.storage.read_all("users")
    return render_template("edit_order.html", order=order, events=events, users=users)

# Update order
@app.route("/orders/update/<id>", methods=["POST"])
def update_order(id):
    user_id = request.form.get("user_id")
    event_id = request.form.get("event_id")
    try:
        user_id_int = int(user_id)
        event_id_int = int(event_id)
    except Exception:
        flash("Invalid user or event selection.", "error")
        return redirect(url_for("orders"))

    # Optional FK checks as above
    users = executor.storage.read_all("users")
    events = executor.storage.read_all("events")
    if not any(str(u.get("id")) == str(user_id_int) for u in users):
        flash("Selected user does not exist.", "error")
        return redirect(url_for("orders"))
    if not any(str(e.get("id")) == str(event_id_int) for e in events):
        flash("Selected event does not exist.", "error")
        return redirect(url_for("orders"))

    sql = f"UPDATE orders SET user_id={user_id_int}, event_id={event_id_int} WHERE id={id};"
    run_sql_and_flash(sql, success_msg="Order updated.")
    return redirect(url_for("orders"))

if __name__ == "__main__":
    # Run the Flask dev server
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))