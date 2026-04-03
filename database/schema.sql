CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT
);

CREATE TABLE preferences (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);