import sqlite3
import os
from typing import Dict

from flask import current_app, g

EXPLANATIONS_FEEDBACK_TABLE = "explanations_table"


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
