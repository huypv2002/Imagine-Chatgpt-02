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

-- Users (đăng ký/đăng nhập tool desktop)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 0,
    max_sessions INTEGER DEFAULT 3,
    expires_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    last_login_at TEXT
);

-- Stats
CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    total_generated INTEGER DEFAULT 0,
    total_success INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0
);
