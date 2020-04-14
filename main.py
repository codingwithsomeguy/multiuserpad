import os

from flask import Flask, render_template, request, redirect, session, abort
from flask_session import Session

import config
from creds import get_creds
import discordutil
import twitchutil
from sessionutil import invalidate_session


# TODO: use subprocess, check this
# TODO: capture fd's from subprocess
KNOWN_EXECUTION_MODELS = {
    "c": "cd '%s' && gcc '%s' -o webinput -lm && ./webinput",
    "py": "cd '%s' && python3 '%s'",
    "js": "cd '%s' && node '%s'"
}


def init_flask():
    app_init = Flask(__name__)

    ss = get_creds()
    app_init.config["SECRET_KEY"] = ss["session_key"]

    app_init.config["SESSION_TYPE"] = "redis"
    Session(app_init)    # Start the web session

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
app.add_url_rule("/api/ident/twitchcb",
    view_func=twitchutil.twitch_login_cb)


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
            "id": discord["id"]
        }
    return result


@app.route("/user")
def user_home():
    if is_authorized():
        # TODO: send users that have discord but are not authorized to signup
        return render_template("userhome.html",
                               wsurl=config.MY_WS_URL, profile=get_profile(),
                               lenv={
                                   "extension": config.CODE_EXTENSION,
                                   "wbrefresh": config.MY_WHITEBOARD_REFRESH_MS})
    else:
        abort(401)


def get_autosave_filename():
    as_filename = "autosrc.%s" % config.CODE_EXTENSION
    autosave_file = os.path.join(config.CODE_DIR, as_filename)
    return autosave_file


def do_load():
    autosave_file = get_autosave_filename()
    text = ""
    try:
        text = open(autosave_file, "r").read()
    except FileNotFoundError:
        pass
    return text


def do_save(text):
    # TODO: use a real temp file?
    autosave_file = get_autosave_filename()
    # TODO: take this from the autosave filename
    os.makedirs(config.CODE_DIR, exist_ok=True)
    open(autosave_file, "w").write(text)
    return autosave_file


@app.route("/load")
def load():
    if is_authorized():
        return do_load()
    abort(401)


# TODO: change to save, not autosave (that's a client thing)
@app.route("/autosave", methods=['POST'])
def autosave():
    if is_authorized():
        rawdata = request.get_data()
        # TODO: make sure this is text before calling decode!!!
        text = rawdata.decode("utf-8")
        do_save(text)
        return "autosaved"
    abort(401)



@app.route("/execute", methods=['POST'])
def do_execute():
    if is_authorized():
        rawdata = request.get_data()
        # TODO: make sure this is text before calling decode!!!
        text = rawdata.decode("utf-8")
        temp_filename = do_save(text)
        # TODO: check which env to do based on extension passed in
        #   or the session / need some variables
        selected_model = "py"
        if config.CODE_EXTENSION in KNOWN_EXECUTION_MODELS:
            selected_model = config.CODE_EXTENSION
        cmd_pattern = KNOWN_EXECUTION_MODELS[selected_model]
        cmd = cmd_pattern % (config.CODE_DIR, temp_filename)
        execution_output = os.popen(cmd, "r").read()
        return execution_output
    abort(401)


# TODO: don't write to disk
# TODO: add session specifics to this
# TODO: auth this
# TODO: tell web clients to reload the board if it changed
@app.route("/wbupdate", methods=['POST'])
def whiteboard_update():
    rawdata = request.get_data()
    open("static/wb.png", "wb").write(rawdata)
    return "ok"


@app.errorhandler(401)
def custom_401(_):
    return render_template("401.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9892)
