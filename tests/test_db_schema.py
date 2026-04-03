import json
import os
import sqlite3
import sys
import tempfile
import uuid
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "test_clauseflag.db")


@pytest.fixture()
def db_conn(db_path):
    with patch("main.DB_PATH", db_path):
        from main import init_db

        init_db()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def _table_columns(conn: sqlite3.Connection, table: str) -> dict[str, str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"]: row["type"] for row in rows}


# ---------- users table ----------


def test_users_table_exists_with_correct_columns(db_conn):
    cols = _table_columns(db_conn, "users")
    assert "id" in cols
    assert "username" in cols
    assert "password_hash" in cols
    assert "created_at" in cols


def test_insert_and_retrieve_user(db_conn):
    user_id = str(uuid.uuid4())
    db_conn.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, "alice", "hashed_pw_123"),
    )
    db_conn.commit()
    row = db_conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    assert row["username"] == "alice"
    assert row["password_hash"] == "hashed_pw_123"
    assert row["created_at"] is not None


def test_username_unique_constraint(db_conn):
    db_conn.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), "bob", "hash1"),
    )
    db_conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), "bob", "hash2"),
        )


# ---------- history table ----------


def test_history_table_exists_with_correct_columns(db_conn):
    cols = _table_columns(db_conn, "history")
    assert "id" in cols
    assert "user_id" in cols
    assert "url" in cols
    assert "analysis_result" in cols
    assert "created_at" in cols


def test_insert_and_retrieve_history(db_conn):
    user_id = str(uuid.uuid4())
    db_conn.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, "carol", "hash_c"),
    )

    history_id = str(uuid.uuid4())
    result_json = json.dumps({"safe": 3, "watch": 1, "danger": 0})
    db_conn.execute(
        "INSERT INTO history (id, user_id, url, analysis_result) VALUES (?, ?, ?, ?)",
        (history_id, user_id, "https://example.com/tos", result_json),
    )
    db_conn.commit()

    row = db_conn.execute(
        "SELECT * FROM history WHERE id = ?", (history_id,)
    ).fetchone()
    assert row["user_id"] == user_id
    assert row["url"] == "https://example.com/tos"
    assert json.loads(row["analysis_result"]) == {"safe": 3, "watch": 1, "danger": 0}
    assert row["created_at"] is not None


def test_history_rejects_missing_user_id(db_conn):
    db_conn.execute("PRAGMA foreign_keys = ON")
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "INSERT INTO history (id, user_id, url, analysis_result) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), None, "https://example.com", "{}"),
        )


# ---------- init_db is idempotent ----------


def test_init_db_idempotent(db_path):
    with patch("main.DB_PATH", db_path):
        from main import init_db

        init_db()
        init_db()  # second call must not raise

    conn = sqlite3.connect(db_path)
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()
    assert {"analyses", "clauses", "users", "history"} <= tables
