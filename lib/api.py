import os

import requests

base_url = "https://mirlo.space/v1"


def get_url(url: str) -> dict:
    api_key = os.environ["MIRLO_API_KEY"]
    response = requests.get(
        f"{base_url}{url}",
        headers={"mirlo-api-key": api_key},
    )
    return response.json()
