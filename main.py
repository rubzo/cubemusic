import datetime
import json
import os
import queue
import random
import threading

from lib.album_player import AlbumPlayer
from lib.api import get_url
from lib.db import create_db, save_db
from lib.genres import GENRES
from lib.commands import (
    parse_command,
    QuitCommand,
    CubeCommand,
    SkipCommand,
    UncubeCommand,
)


def get_week_id() -> int:
    now = datetime.datetime.now(datetime.UTC)
    year = now.year
    week = now.isocalendar()[1]
    return year * 100 + week


class State:
    IDLE = 0
    PLAYING = 1


class Vibecube:
    def __init__(self):
        if os.path.exists("db.json"):
            with open("db.json", "r") as f:
                self.db = json.load(f)
        else:
            self.db = create_db()
            save_db(self.db)

        self.state = State.IDLE
        self.album_player = None

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

    def handle_command(self, command):
        if isinstance(command, CubeCommand):
            self._handle_cube_command(command)
        elif isinstance(command, SkipCommand):
            self._handle_skip()
        elif isinstance(command, UncubeCommand):
            self._handle_uncube()
        elif isinstance(command, QuitCommand):
            self._handle_quit()

    def _handle_cube_command(self, command: CubeCommand):
        if self.state == State.PLAYING:
            self._handle_uncube()

        genre = command.get_genre()

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

        if self.album_player:
            self.album_player.stop()
            self.album_player = None

        self.album_player = AlbumPlayer(genre, album_data)
        self.album_player.play_next_track()

        genre_info["artist"] = self.album_player.get_artist_name()
        genre_info["album"] = self.album_player.get_album_name()
        save_db(self.db)

        # artist_name = self.album_player.get_artist_name()
        # album_name = self.album_player.get_album_name()
        # print(f"Now playing: {artist_name} - {album_name}")

        self.state = State.PLAYING

    def _handle_skip(self):
        if self.state == State.PLAYING and self.album_player:
            self.album_player.play_next_track()

    def _handle_uncube(self):
        if self.state == State.PLAYING and self.album_player:
            self.album_player.stop()
            self.album_player = None
            self.state = State.IDLE

    def _handle_quit(self):
        self._handle_uncube()


def run_thread(command_queue, shutdown_event):
    vibecube = Vibecube()

    while not shutdown_event.is_set():
        try:
            command = command_queue.get(timeout=1)
            vibecube.handle_command(command)
        except queue.Empty:
            pass


def main():
    print("Welcome to CubeMusic!")
    print("---------------------")
    print()
    print("Commands:")
    print(" - cube <genre> [start playing this genre]")
    print(" - uncube [stop playing]")
    print(" - skip [skip to next track]")
    print(" - quit [stop the player and exit]")
    print()
    print("Available Genres: " + ", ".join(GENRES))
    print()

    command_queue = queue.Queue()
    shutdown_event = threading.Event()

    thread = threading.Thread(target=run_thread, args=(command_queue, shutdown_event))
    thread.start()

    # Commands:

    # cube <genre>
    # uncube
    # skip
    # quit

    while True:
        command_str = input("Enter a command: ")

        try:
            command = parse_command(command_str)
        except ValueError:
            print("Invalid command.")
            continue

        if isinstance(command, CubeCommand):
            if command.get_genre() not in GENRES:
                print("Invalid genre.")
                continue

        command_queue.put(command)

        if isinstance(command, QuitCommand):
            break

    shutdown_event.set()
    thread.join()
    print("Goodbye!")


if __name__ == "__main__":
    main()
