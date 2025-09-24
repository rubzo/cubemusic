import os

import dotenv
import requests

import pprint
import ipdb

import subprocess


dotenv.load_dotenv()

API_BASE_URL = "https://mirlo.space/v1"

GENRES = ["pop", "grunge", "jazz", "8-bit", "classical"]


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
        if self._active_proc:
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

    def is_finished(self) -> bool:
        return self._track_index >= self._track_count


def get_url(url: str) -> dict:
    api_key = os.environ["MIRLO_API_KEY"]
    response = requests.get(
        f"{API_BASE_URL}{url}",
        headers={"mirlo-api-key": api_key},
    )
    return response.json()


def main():
    while True:
        genre = input("Give a genre> ")

        response = get_url(f"/trackGroups?tag={genre}&orderBy=random&take=1")
        album_data = response["results"][0]

        player = AlbumPlayer(genre, album_data)

        player.play_next_track()

        while not player.is_finished():
            input("Press Enter for next track!")
            player.play_next_track()


if __name__ == "__main__":
    main()
