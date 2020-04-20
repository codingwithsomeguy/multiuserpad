import json
from urllib.parse import urlparse, urlunparse

# TODO: WIP - moving all to config.json

# WIP: temporary bridge json holder
config = json.load(open("config.json"))

MY_HOST_NAME = urlparse(config["server"]["web"]["url"]).hostname
MY_WEB_PORT = urlparse(config["server"]["web"]["url"]).port
MY_WS_PORT = urlparse(config["server"]["web_socket"]["url"]).port

MY_WHITEBOARD_REFRESH_MS = config["parameters"]["whiteboard_refresh_ms"]
# TODO: just read this, but reassemble with urlunparse
MY_URL = "http://%s:%d" % (MY_HOST_NAME, MY_WEB_PORT)
MY_WS_URL = "ws://%s:%d/" % (MY_HOST_NAME, MY_WS_PORT)

CREDENTIALS_URL = config["credentials_url"]

DISCORD_API_URL = config["auth"]["discord"]["url"]
DISCORD_CDN_URL = config["auth"]["discord"]["cdn"]

TWITCH_API_URL = config["auth"]["twitch"]["url"]

CODE_DIR = config["parameters"]["temporary_code_directory"]
CODE_EXTENSION = config["parameters"]["code_extension"]
