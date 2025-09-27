import os
import subprocess
import threading

import dotenv

import lib.api

dotenv.load_dotenv()


class ProcessWithCallback:
    def __init__(self, command: list, callback):
        self._terminate_event = threading.Event()
        self._command = command
        self._callback = callback
        self._proc = None
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def _run(self):
        self._proc = subprocess.Popen(
            self._command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        finished = False
        while not finished:
            try:
                self._proc.wait(timeout=1)
                finished = True
            except subprocess.TimeoutExpired:
                if self._terminate_event.is_set():
                    self._proc.terminate()
                    return

        # I think this might be a problem because technically we're calling the
        # callback WITHIN the thread spawned to run the process. Instead we need
        # to post something back? TODO
        # (but it seems to work...)

        self._callback()

    def terminate(self):
        self._terminate_event.set()
        self._thread.join()


class AlbumPlayer:
    def __init__(self, genre: str, album_data: dict):
        self._genre = genre
        self._album_data = album_data
        self._track_index = 0
        self._track_count = len(album_data["tracks"])
        self._proc = None
        self._api_key = os.environ["MIRLO_API_KEY"]

    def get_album_name(self) -> str:
        return self._album_data["title"]

    def get_artist_name(self) -> str:
        return self._album_data["artist"]["name"]

    def _track_finished_callback(self):
        # The track finished, so the process/thread finished.
        self._proc = None
        if self._track_index < self._track_count:
            self.play_next_track()
        else:
            self.stop()

    def play_next_track(self):
        if self._proc:
            self._proc.terminate()
            self._proc = None

        track = self._album_data["tracks"][self._track_index]
        track_id = track["id"]
        self._track_index += 1

        self._proc = ProcessWithCallback(
            [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-infbuf",
                "-headers",
                f"mirlo-api-key: {self._api_key}",
                f"{lib.api.base_url}/tracks/{track_id}/stream/playlist.m3u8",
            ],
            self._track_finished_callback,
        )

    def stop(self):
        if self._proc:
            self._proc.terminate()
            self._proc = None
