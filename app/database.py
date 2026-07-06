import json
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "data" / "catalogue.sqlite"

JSON_FIELDS = {
    "education_levels",
    "cities",
    "required_skills",
    "preferred_skills",
    "interests",
}


def connect(db_path=DEFAULT_DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            min_age INTEGER NOT NULL,
            max_age INTEGER NOT NULL,
            education_levels TEXT NOT NULL,
            cities TEXT NOT NULL,
            remote_allowed INTEGER NOT NULL,
            required_skills TEXT NOT NULL,
            preferred_skills TEXT NOT NULL,
            min_experience_months INTEGER NOT NULL,
            fee_inr INTEGER NOT NULL,
            min_weekly_hours INTEGER NOT NULL,
            interests TEXT NOT NULL,
            requires_laptop INTEGER NOT NULL,
            starts_within_days INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()


def encode_item(item):
    encoded = dict(item)
    for field in JSON_FIELDS:
        encoded[field] = json.dumps(encoded.get(field, []))
    encoded["remote_allowed"] = int(bool(encoded.get("remote_allowed", False)))
    encoded["requires_laptop"] = int(bool(encoded.get("requires_laptop", False)))
    encoded["active"] = int(bool(encoded.get("active", True)))
    return encoded


def row_to_item(row):
    item = dict(row)
    for field in JSON_FIELDS:
        item[field] = json.loads(item[field])
    item["remote_allowed"] = bool(item["remote_allowed"])
    item["requires_laptop"] = bool(item["requires_laptop"])
    item["active"] = bool(item["active"])
    return item


def list_items(connection, include_inactive=True):
    query = "SELECT * FROM items"
    params = ()
    if not include_inactive:
        query += " WHERE active = ?"
        params = (1,)
    query += " ORDER BY name"
    return [row_to_item(row) for row in connection.execute(query, params)]


def get_item(connection, item_id):
    row = connection.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return row_to_item(row) if row else None


def upsert_item(connection, item):
    encoded = encode_item(item)
    connection.execute(
        """
        INSERT INTO items (
            id, name, category, description, min_age, max_age, education_levels,
            cities, remote_allowed, required_skills, preferred_skills,
            min_experience_months, fee_inr, min_weekly_hours, interests,
            requires_laptop, starts_within_days, active
        )
        VALUES (
            :id, :name, :category, :description, :min_age, :max_age,
            :education_levels, :cities, :remote_allowed, :required_skills,
            :preferred_skills, :min_experience_months, :fee_inr,
            :min_weekly_hours, :interests, :requires_laptop,
            :starts_within_days, :active
        )
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            category = excluded.category,
            description = excluded.description,
            min_age = excluded.min_age,
            max_age = excluded.max_age,
            education_levels = excluded.education_levels,
            cities = excluded.cities,
            remote_allowed = excluded.remote_allowed,
            required_skills = excluded.required_skills,
            preferred_skills = excluded.preferred_skills,
            min_experience_months = excluded.min_experience_months,
            fee_inr = excluded.fee_inr,
            min_weekly_hours = excluded.min_weekly_hours,
            interests = excluded.interests,
            requires_laptop = excluded.requires_laptop,
            starts_within_days = excluded.starts_within_days,
            active = excluded.active
        """,
        encoded,
    )
    connection.commit()
    return get_item(connection, item["id"])


def delete_item(connection, item_id):
    cursor = connection.execute("DELETE FROM items WHERE id = ?", (item_id,))
    connection.commit()
    return cursor.rowcount > 0
