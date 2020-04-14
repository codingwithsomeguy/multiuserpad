import urllib.request
import urllib.error
import json
from config import CREDENTIALS_URL
from logging import error


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
        except urllib.error.URLError as e:
            error("Credentials fetch at CREDENTIALS_URL, using mock")
    return get_creds.creds
