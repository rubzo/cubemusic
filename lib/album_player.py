import dotenv
import os
import subprocess

import lib.api

dotenv.load_dotenv()


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
                f"{lib.api.base_url}/tracks/{track_id}/stream/playlist.m3u8",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self):
        if self._active_proc:
            self._active_proc.terminate()
            self._active_proc = None

    def check_if_track_finished(self) -> bool:
        if self._active_proc:
            return self._active_proc.poll() is not None
        return True

    def is_finished(self) -> bool:
        return self._track_index >= self._track_count
