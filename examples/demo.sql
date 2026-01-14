-- Schema setup
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT UNIQUE, email TEXT);
CREATE TABLE events (id INTEGER PRIMARY KEY, title TEXT, date DATE);
CREATE TABLE tickets (id INTEGER PRIMARY KEY, event_id INTEGER, buyer_name TEXT, UNIQUE(event_id, buyer_name));
CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, event_id INTEGER, UNIQUE(user_id, event_id));

-- Seed users
INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');
INSERT INTO users (id, name, email) VALUES (2, 'Bob', 'bob@example.com');

-- Seed events
INSERT INTO events (id, title, date) VALUES (100, 'Tech Meetup', '2026-01-20');
INSERT INTO events (id, title, date) VALUES (101, 'Music Festival', '2026-02-15');

-- Tickets with composite UNIQUE
INSERT INTO tickets (id, event_id, buyer_name) VALUES (1, 100, 'Alice');
INSERT INTO tickets (id, event_id, buyer_name) VALUES (2, 100, 'Bob');
INSERT INTO tickets (id, event_id, buyer_name) VALUES (3, 101, 'Alice');
INSERT INTO tickets (id, event_id, buyer_name) VALUES (4, 100, 'Alice'); -- should fail

-- Updates
UPDATE tickets SET buyer_name='Charlie' WHERE id=2; -- valid
UPDATE tickets SET event_id=100 WHERE id=3; -- should fail

-- Delete
DELETE FROM tickets WHERE id=1;

-- Orders for join demo
INSERT INTO orders (id, user_id, event_id) VALUES (1, 1, 100);
INSERT INTO orders (id, user_id, event_id) VALUES (2, 2, 101);

-- Queries
SELECT * FROM users;
SELECT * FROM events;
SELECT * FROM tickets;

-- Single join demos
SELECT users.name, orders.event_id FROM users INNER JOIN orders ON users.id = orders.user_id;
SELECT events.title, orders.user_id FROM events INNER JOIN orders ON events.id = orders.event_id;