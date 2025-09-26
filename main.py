import datetime
import json
import os
import random
import subprocess
import time

import dotenv
import requests


dotenv.load_dotenv()

API_BASE_URL = "https://mirlo.space/v1"

GENRES = ["pop", "rock", "jazz", "videogame", "ambient"]


class AlbumPlayer:
    def __init__(self, genre: str, album_data: dict):
        self._genre = genre
        self._album_data = album_data
        self._track_index = 0
        self._track_count = len(album_data["tracks"])
        self._active_proc = None
        self._api_key = os.environ["MIRLO_API_KEY"]

    def get_album_name(self) -> str:
        return self._album_data["title"]

    def get_artist_name(self) -> str:
        return self._album_data["artist"]["name"]

    def play_next_track(self):
        if self._active_proc and self._active_proc.poll() is None:
            self._active_proc.terminate()

        track = self._album_data["tracks"][self._track_index]
        track_id = track["id"]
        self._track_index += 1

        self._active_proc = subprocess.Popen(
            [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-infbuf",
                "-headers",
                f"mirlo-api-key: {self._api_key}",
                f"https://mirlo.space/v1/tracks/{track_id}/stream/playlist.m3u8",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def check_if_track_finished(self) -> bool:
        if self._active_proc:
            return self._active_proc.poll() is not None
        return True

    def is_finished(self) -> bool:
        return self._track_index >= self._track_count


def get_url(url: str) -> dict:
    api_key = os.environ["MIRLO_API_KEY"]
    response = requests.get(
        f"{API_BASE_URL}{url}",
        headers={"mirlo-api-key": api_key},
    )
    return response.json()


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


def get_week_id() -> int:
    now = datetime.datetime.now(datetime.UTC)
    year = now.year
    week = now.isocalendar()[1]
    return year * 100 + week


class State:
    SELECTING_GENRE = 0
    PLAYING_TRACK = 1


class Vibecube:
    def __init__(self):
        if os.path.exists("db.json"):
            with open("db.json", "r") as f:
                self.db = json.load(f)
        else:
            self.db = create_db()
            save_db(self.db)

        self.state = State.SELECTING_GENRE
        self.album_player = None

    def run(self):
        if self.state == State.SELECTING_GENRE:
            self.handle_selecting_genre()
            return False
        elif self.state == State.PLAYING_TRACK:
            if self.album_player.check_if_track_finished():
                if self.album_player.is_finished():
                    print("Album finished, stopping...")
                    return True
                else:
                    print("Track finished, playing next track...")
                    self.album_player.play_next_track()
                    return False

    def select_albumish(self, albums: list) -> dict:
        random.shuffle(albums)

        for album in albums:
            total_duration = 0
            for track in album["tracks"]:
                # Only count things that can be streamed (isPreview -> can be streamed)
                if track["isPreview"]:
                    total_duration += track["metadata"]["format"]["duration"]
            if total_duration >= 20 * 60:
                return album

    def find_new_album(self, genre: str) -> dict:
        response = get_url(f"/trackGroups?tag={genre}")
        return self.select_albumish(response["results"])

    def handle_selecting_genre(self):
        print(f"Available genres: {', '.join(GENRES)}")
        valid = False

        while not valid:
            genre = input("Select a genre> ")
            if genre in GENRES:
                valid = True
            else:
                print("Invalid genre!")

        week_id = get_week_id()

        genre_info = self.db["genres"][genre]
        if genre_info["week_assigned"] != week_id:
            album_data = self.find_new_album(genre)
            genre_info["album_id"] = album_data["id"]
            genre_info["week_assigned"] = week_id
            save_db(self.db)
        else:
            album_id = genre_info["album_id"]
            album_data = get_url(f"/trackGroups/{album_id}")["result"]
            genre_info["album_id"] = album_data["id"]
            genre_info["week_assigned"] = week_id

        self.album_player = AlbumPlayer(genre, album_data)
        self.album_player.play_next_track()

        artist_name = self.album_player.get_artist_name()
        album_name = self.album_player.get_album_name()
        print(f"Now playing: {artist_name} - {album_name}")

        self.state = State.PLAYING_TRACK

    def skip(self):
        if self.state == State.PLAYING_TRACK and self.album_player:
            self.album_player.play_next_track()


def main():
    vibecube = Vibecube()

    while True:
        exited = vibecube.run()
        if exited:
            break
        time.sleep(1)


if __name__ == "__main__":
    main()
