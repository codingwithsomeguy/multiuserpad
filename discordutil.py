import json
import logging
from urllib.parse import urlencode

from flask import redirect, request, session
import requests

from creds import get_creds
import config
from sessionutil import invalidate_session


def login():
    ss = get_creds()
    params = {
        "client_id": ss["client_id"],
        "client_secret": ss["client_secret"],
        "redirect_uri": "%s/api/ident/cb" % config.MY_URL,
        "response_type": "code",
        "scope": "identify"
    }
    redirect_url = "%s/oauth2/authorize?%s" % (
        config.DISCORD_API_URL, urlencode(params))
    return redirect(redirect_url)


# TODO: discord hitting this callback will write the access_token
#  on terminal in the dev server
def discord_login_cb():
    user_authenticated = False
    result = "Missing code"

    # need to exchange code for a token
    code = request.args.get("code")
    if code is not None:
        result = "Code was %s" % code
        user_authenticated = fetch_token(code)
    if user_authenticated == True:
        #logging.debug("session:", session)
        discord_user_fetch_worked = fetch_discord_user()
        if not discord_user_fetch_worked:
            invalidate_session()
            return redirect("/")
        return redirect("/user")
    else:
        # consider removing the session here
        return redirect("/")
    return result


def fetch_token(code):
    SS = get_creds()
    result = False
    body_payload = {
        "client_id": SS["client_id"],
        "client_secret": SS["client_secret"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "%s/api/ident/cb" % config.MY_URL,
        "scope": "identify"
    }
    # redirect_uri may need to match original cb URI (discord_login_cb)
    extra_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(
        "%s/oauth2/token" % config.DISCORD_API_URL,
        data=urlencode(body_payload),
        headers=extra_headers)
    logging.debug("fetch_token: headers: %s\n\traw response: %s" % (
        response.headers, response.text))
    try:
        token_response = json.loads(response.text)
        if "access_token" in token_response and "refresh_token" in token_response:
            session["token_response"] = token_response
            result = True
        else:
            logging.warn("NO refresh_token AVAILABLE, BAD AUTH!")
    except ValueError as e:
        logging.error("ValueError: " + e)
        result = False

    return result


def fetch_discord_user():
    if "token_response" not in session:
        return False

    token = session["token_response"]
    if "token_type" not in token or "access_token" not in token:
        return False

    # TODO: get this from env, not hard coded auth
    extra_headers = {
        "Authorization": "%s %s" % (
            token["token_type"],
            token["access_token"]
        ),
    }
    response = requests.get(
        "%s/users/@me" % config.DISCORD_API_URL,
        headers=extra_headers)
    logging.debug("fetch_discord_user: headers: %s\n\traw response: %s" % (
        response.headers, response.text))

    discord_avatar_url = None
    discord_full_username = None
    discord_id = None
    try:
        logging.debug("response: %s" % response.text)
        parsed_response = json.loads(response.text)
        discord_avatar_url = "%s/avatars/%s/%s.png" % (
            config.DISCORD_CDN_URL,
            parsed_response["id"], parsed_response["avatar"])
        discord_full_username = "%s#%s" % (
            parsed_response["username"], parsed_response["discriminator"])
        discord_id = parsed_response["id"]
    except ValueError as e:
        logging.error("ValueError: " + e)
        return False

    ss = get_creds()
    session["discord"] = {
        "full_username": discord_full_username,
        "avatar_url": discord_avatar_url,
        "id": discord_id,
        "authorized": discord_id in ss["authorized_discord_ids"]
    }

    return True
