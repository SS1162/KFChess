import hashlib
import hmac
import os
import sqlite3


class AccountError(Exception):
    pass


class AccountService:
    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username      TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                elo           INTEGER NOT NULL DEFAULT 1200
            )
            """
        )
        self._conn.commit()

    def create_account(self, username: str, password: str) -> None:
        existing = self._conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            raise AccountError(f"Username already exists: {username!r}")

        salt = os.urandom(16).hex()
        digest = hashlib.sha256((salt + password).encode()).hexdigest()
        password_hash = f"{salt}${digest}"

        self._conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        self._conn.commit()

    def login_or_register(self, username: str, password: str) -> int:
        exists = self._conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()

        if exists:
            return self.authenticate(username, password)
        else:
            self.create_account(username, password)
            return self.authenticate(username, password)

    def authenticate(self, username: str, password: str) -> int:
        row = self._conn.execute(
            "SELECT password_hash, elo FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            raise AccountError(f"Unknown username: {username!r}")

        stored_hash, elo = row
        salt, expected_digest = stored_hash.split("$", 1)
        actual_digest = hashlib.sha256((salt + password).encode()).hexdigest()
        if not hmac.compare_digest(actual_digest, expected_digest):
            raise AccountError("Invalid password")

        return elo
