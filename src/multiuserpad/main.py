import os
import json
import subprocess

from flask import Flask, render_template
from flask import Response, request, redirect, session, abort
from flask_session import Session

from config import config
from creds import get_creds
import discordutil
import twitchutil
from whiteboard import update_redis_wb, get_redis_wb, default_wb_image
from sessionutil import invalidate_session
from runtime import get_autosave_filename


def init_flask():
    app_init = Flask(__name__)

    ss = get_creds()
    app_init.config["SECRET_KEY"] = ss["session_key"]

    app_init.config["SESSION_TYPE"] = "redis"
    Session(app_init)  # Start the web session

    return app_init


# wsgi (in uwsgi) workaround for "application":
app = init_flask()
application = app


@app.route("/")
def home():
    return render_template("home.html", wsurl=config.MY_WS_URL)


app.add_url_rule("/login", view_func=discordutil.discord_login)
app.add_url_rule("/api/ident/cb", view_func=discordutil.discord_login_cb)
app.add_url_rule("/logintwitch", view_func=twitchutil.twitch_login)
app.add_url_rule("/api/ident/twitchcb", view_func=twitchutil.twitch_login_cb)


@app.route("/logout")
def logout():
    invalidate_session()
    return redirect("/")


def is_authorized():
    # allow other auth, but for now all one role
    result = False
    if "discord" in session:
        if "authorized" in session["discord"]:
            if session["discord"]["authorized"] == True:
                result = True
    return result


def get_profile():
    result = {}
    if "discord" in session:
        discord = session["discord"]
        result = {
            "full_username": discord["full_username"],
            "avatar_url": discord["avatar_url"],
            "id": discord["id"],
        }
    return result


@app.route("/user")
def user_home():
    if is_authorized():
        # TODO: send users that have discord but are not authorized to signup
        return render_template(
            "userhome.html",
            wsurl=config.MY_WS_URL,
            profile=get_profile(),
            lenv={
                "extension": config.CODE_EXTENSION,
                "wbrefresh": config.WHITEBOARD_REFRESH_MS,
            },
        )
    else:
        abort(401)


# TODO: add session specifics to this
# TODO: auth this before using a push notification
# TODO: tell web clients to reload the board if it changed
@app.route("/wb", methods=["GET", "POST"])
def whiteboard_update():
    if request.method == "GET":
        # TODO: allow other image types
        img = get_redis_wb()
        if img is None:
            img = default_wb_image
        return Response(img, mimetype="image/png")
    elif request.method == "POST":
        # TODO: record image type as well
        rawdata = request.get_data()
        update_redis_wb(rawdata)
        return "ok"


@app.errorhandler(401)
def custom_401(_):
    return render_template("401.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=config.MY_WEB_PORT)
