import os

import dotenv
import requests

import pprint
import ipdb

import subprocess


dotenv.load_dotenv()

API_BASE_URL = "https://mirlo.space/v1"


def get_url(url: str) -> dict:
    api_key = os.environ["MIRLO_API_KEY"]
    response = requests.get(
        f"{API_BASE_URL}{url}",
        headers={"mirlo-api-key": api_key},
    )
    return response.json()


def main():
    genre = input("Give a genre> ")
    album_data = get_url(f"/trackGroups?tag={genre}&orderBy=random&take=1")["results"][
        0
    ]
    album_name = album_data["title"]
    artist_name = album_data["artist"]["name"]
    print(f"Playing {album_name} by {artist_name}")

    tracks = album_data["tracks"]

    first_track_id = tracks[0]["id"]

    api_key = os.environ["MIRLO_API_KEY"]
    proc = subprocess.Popen(
        [
            "ffplay",
            "-nodisp",
            "-headers",
            f"mirlo-api-key: {api_key}",
            f"https://mirlo.space/v1/tracks/{first_track_id}/stream/playlist.m3u8",
        ]
    )
    proc.wait()


if __name__ == "__main__":
    main()
