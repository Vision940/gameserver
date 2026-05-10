CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,

  username TEXT NOT NULL UNIQUE,
  password_hash TEXT,

  status TEXT NOT NULL DEFAULT 'requested'
    CHECK (status IN ('requested', 'approved', 'banned', 'rejected')),

  created_by TEXT NOT NULL,
  created_on_host TEXT NOT NULL,

  approved_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
  approved_at TIMESTAMPTZ,

  banned_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
  banned_at TIMESTAMPTZ,
  banned_reason TEXT,

  rejected_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
  rejected_at TIMESTAMPTZ,
  rejected_reason TEXT,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ
);

CREATE INDEX idx_users_status
ON users (status);

CREATE TABLE user_api_keys (
  id BIGSERIAL PRIMARY KEY,

  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  key_hash TEXT NOT NULL UNIQUE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  last_used_at TIMESTAMPTZ
);

CREATE INDEX idx_user_api_keys_user
ON user_api_keys (user_id);

CREATE INDEX idx_user_api_keys_last_used
ON user_api_keys (last_used_at);

CREATE INDEX idx_user_api_keys_expires
ON user_api_keys (expires_at);

CREATE VIEW user_profiles AS
SELECT
  id,
  username,
  status,
  created_at,
  last_seen_at
FROM users;

