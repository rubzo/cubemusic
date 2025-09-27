import datetime
import json
import os
import random
import time


from lib.album_player import AlbumPlayer
from lib.api import get_url
from lib.db import create_db, save_db
from lib.genres import GENRES


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
