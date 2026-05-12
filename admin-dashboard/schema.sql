-- Image generation history
CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    model TEXT DEFAULT 'gpt-image-2',
    ratio TEXT DEFAULT '1:1',
    status TEXT DEFAULT 'pending',
    file_name TEXT,
    error TEXT,
    account_name TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT
);

-- Accounts/sessions
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    type TEXT DEFAULT 'free',
    status TEXT DEFAULT 'active',
    quota INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    last_used_at TEXT
);

-- Stats
CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    total_generated INTEGER DEFAULT 0,
    total_success INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0
);
