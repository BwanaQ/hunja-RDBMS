-- Demo script for MiniRDBMS
-- Showcases table creation, CRUD, indexing, and joins

-- 1. Create tables
CREATE TABLE events (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE,
  date DATE
);

CREATE TABLE tickets (
  id INTEGER PRIMARY KEY,
  event_id INTEGER,
  buyer_name TEXT,
  UNIQUE(event_id, buyer_name)
);

-- 2. Insert sample data
INSERT INTO events (id, name, date)
VALUES (1, 'Kitui Tech Meetup', '2026-01-20');

INSERT INTO events (id, name, date)
VALUES (2, 'Nairobi Dev Night', '2026-02-05');

INSERT INTO tickets (id, event_id, buyer_name)
VALUES (101, 1, 'Alice');

INSERT INTO tickets (id, event_id, buyer_name)
VALUES (102, 1, 'Bob');

INSERT INTO tickets (id, event_id, buyer_name)
VALUES (103, 2, 'Charlie');

-- 3. Basic queries
SELECT * FROM events;

SELECT * FROM tickets WHERE event_id = 1;

-- 4. Update and delete
UPDATE events SET name = 'Kitui Developer Meetup' WHERE id = 1;

DELETE FROM tickets WHERE buyer_name = 'Bob';

-- 5. Index creation
CREATE INDEX idx_events_date ON events(date);

-- 6. Join query
SELECT tickets.id, tickets.buyer_name, events.name, events.date
FROM tickets
JOIN events ON tickets.event_id = events.id
WHERE events.date = '2026-01-20';