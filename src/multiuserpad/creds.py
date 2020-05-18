import urllib.request
import urllib.error
import json
from logging import error

from config import config


def get_creds():
    if not hasattr(get_creds, "creds"):
        get_creds.creds = {
            "session_key": "MOCKSECRETKEY",
            "client_id": "MOCKCLIENTID",
            "client_secret": "MOCKCLIENTSECRET",
            "twitch_client_id": "MOCKCLIENTID",
            "twitch_client_secret": "MOCKCLIENTID",
        }
        try:
            with urllib.request.urlopen(config.CREDENTIALS_URL) as response_file:
                get_creds.creds = json.load(response_file)
        except urllib.error.URLError:
            error("Credentials fetch at CREDENTIALS_URL, using mock")
    return get_creds.creds
