import urllib.request
import urllib.error
import json
from logging import error

from config import CREDENTIALS_URL


def get_creds():
    if not hasattr(get_creds, "creds"):
        get_creds.creds = {
            "session_key": "MOCKSECRETKEY",
            "client_id": "MOCKCLIENTID",
            "client_secret": "MOCKCLIENTSECRET",
        }
        try:
            with urllib.request.urlopen(CREDENTIALS_URL) as response_file:
                get_creds.creds = json.load(response_file)
        except urllib.error.URLError:
            error("Credentials fetch at CREDENTIALS_URL, using mock")
    return get_creds.creds
