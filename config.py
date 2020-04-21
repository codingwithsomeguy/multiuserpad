import json
from urllib.parse import urlparse, urlunparse


class Config:
    def __init__(self):
        # TODO: rename config --> raw_config
        config = json.load(open("config.json"))

        self.MY_HOST_NAME = urlparse(
            config["server"]["web"]["url"]).hostname
        self.MY_WEB_PORT = urlparse(
            config["server"]["web"]["url"]).port
        self.MY_WS_PORT = urlparse(
            config["server"]["web_socket"]["url"]).port

        self.WHITEBOARD_REFRESH_MS = config["parameters"]["whiteboard_refresh_ms"]

        # TODO: don't reassemble these, just read direct
        self.MY_URL = "http://%s:%d" % (self.MY_HOST_NAME, self.MY_WEB_PORT)
        self.MY_WS_URL = "ws://%s:%d/" % (self.MY_HOST_NAME, self.MY_WS_PORT)

        self.CREDENTIALS_URL = config["credentials_url"]

        self.DISCORD_API_URL = config["auth"]["discord"]["url"]
        self.DISCORD_CDN_URL = config["auth"]["discord"]["cdn"]

        self.TWITCH_API_URL = config["auth"]["twitch"]["url"]

        self.CODE_DIR = config["parameters"]["temporary_code_directory"]
        self.CODE_EXTENSION = config["parameters"]["code_extension"]


# TODO: get this out of global space (wrap in util func or have main
#  handle it)
config = Config()
