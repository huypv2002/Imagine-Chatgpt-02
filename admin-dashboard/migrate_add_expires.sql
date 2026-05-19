-- Migration: Add expires_at column to users table
-- Run this on existing D1 database to add subscription expiration support

ALTER TABLE users ADD COLUMN expires_at TEXT;

-- Optional: Set all existing active users to unlimited (no expiration)
-- UPDATE users SET expires_at = NULL WHERE is_active = 1;

-- Example: Set a user to expire in 30 days from now
-- UPDATE users SET expires_at = datetime('now', '+30 days') WHERE username = 'example_user';

-- Example: Set a user to expire on a specific date
-- UPDATE users SET expires_at = '2025-07-01 23:59:59' WHERE username = 'example_user';
