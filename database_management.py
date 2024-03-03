import sqlite3
import os
from typing import Dict

from flask import current_app, g

EXPLANATIONS_FEEDBACK_TABLE = "explanations_table"
SOURCE_ID_MAPPING_TABLE = "source_id_mapping"


def get_db_path():
    return os.path.join(
        current_app.config["DATABASE_FOLDER"], current_app.config["DATABASE"]
    )


def prepare_db():
    db_path = get_db_path()
    db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    cur = db.cursor()
    cur.execute(
        f"""CREATE TABLE IF NOT EXISTS {EXPLANATIONS_FEEDBACK_TABLE}(
                explanation_id INTEGER PRIMARY KEY,
                time INTEGER NOT NULL,
                defect_code TEXT NOT NULL,
                good INTEGER,
                comment TEXT,
                source_code TEXT,
                source_code_hash TEXT,
                line INTEGER,
                explanations_hash TEXT,
                explanation TEXT,
                user_id TEXT,
                extra TEXT
            )"""
    )

    cur.execute(
        f"""CREATE TABLE IF NOT EXISTS {SOURCE_ID_MAPPING_TABLE}(
            mapping_id INTEGER PRIMARY KEY,
            time INTEGER NOT NULL,
            source_id TEXT,
            source_code_hash TEXT
        )"""
    )


def get_db():
    db_path = get_db_path()

    if "db" not in g:
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    return g.db


def close_db():
    db = g.pop("db", None)

    if db is not None:
        db.close()


def with_db(func):
    def inner(*args, **kwargs):
        db = get_db()
        func(db, *args, **kwargs)
        close_db()

    return inner


@with_db
def store_feedback_in_db(db, feedback: Dict[str, str]):
    sorted_keys = sorted(feedback)
    cursor = db.cursor()
    cursor.execute(
        f"INSERT INTO {EXPLANATIONS_FEEDBACK_TABLE}({', '.join(sorted_keys)}) "
        f"VALUES({', '.join(':' + key for key in sorted_keys)})",
        feedback,
    )
    db.commit()


@with_db
def store_source_id_in_mapping(db, source_id: str, time: int, code_hash: str):
    cursor = db.cursor()
    cursor.execute(
        f"INSERT INTO {SOURCE_ID_MAPPING_TABLE}(time, source_id, source_code_hash)  VALUES(?, ?, ?)",
        (time, source_id, code_hash),
    )
    db.commit()
