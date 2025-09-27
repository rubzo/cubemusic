import json

from lib.genres import GENRES


def create_db() -> dict:
    db = {"genres": {}}
    for genre in GENRES:
        db["genres"][genre] = {
            "name": genre,
            "album_id": None,
            "week_assigned": None,
        }

    return db


def save_db(db: dict):
    with open("db.json", "w") as f:
        json.dump(db, f, indent=4)
