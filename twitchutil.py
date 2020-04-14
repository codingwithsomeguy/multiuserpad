# TODO: Generalize this with the discordutil module, factor out oauth

import logging
from urllib.parse import urlencode
import requests
import json

from flask import request, redirect, session
from creds import get_creds
import config
from sessionutil import invalidate_session


def twitch_login():
    ss = get_creds()
    params = {
        "client_id": ss["twitch_client_id"],
        "redirect_uri": "%s/api/ident/twitchcb" % config.MY_URL,
        "state": True,
        "response_type": "code",
        "scope": "openid",  # not user_read, id_token, or user_subscriptions
        # need to request objects for the later userinfo request
        "claims": json.dumps({
            "id_token": {},
            "userinfo": {
                "picture": "null",
                "preferred_username": "null",
            }
        })
    }
    redirect_url = "%s/oauth2/authorize?%s" % (
        config.TWITCH_API_URL, urlencode(params))
    return redirect(redirect_url)


def twitch_login_cb():
    user_authenticated = False
    result = "Missing code"

    code = request.args.get("code")
    scope = request.args.get("scope")

    if code is not None and scope == "openid":
        # fetch a token
        user_authenticated = fetch_twitch_token(code)

    if user_authenticated == True:
        user_fetch_worked = fetch_twitch_user()
        if not user_fetch_worked:
            invalidate_session()
            return redirect("/")
        return redirect("/user")
    return result


# TODO: this should be cached until expiration
# The server can reuse this for API requests
# TODO: factor this out with discord auth to oauth..auth
def fetch_twitch_token(code):
    # on success, session has the token to use
    ss = get_creds()
    result = False
    body_payload = {
        "client_id": ss["twitch_client_id"],
        "client_secret": ss["twitch_client_secret"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "%s/api/ident/twitchcb" % config.MY_URL,
    }
    # redirect_uri may need to match original cb URI (twitch_login_cb)
    extra_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(
        "%s/oauth2/token" % config.TWITCH_API_URL,
        data=urlencode(body_payload),
        headers=extra_headers)
    logging.debug("fetch_twitch_token: headers: %s\n\traw response: %s" % (
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


def fetch_twitch_user():
    if "token_response" not in session:
        return False

    token = session["token_response"]
    if "token_type" not in token or "access_token" not in token:
        return False

    auth_header_token_type = ""
    # token request returns "bearer", not "Bearer" sometimes
    if token["token_type"] in ["bearer", "Bearer"]:
        auth_header_token_type = "Bearer"

    # this are attached to session in fetch_twitch_token
    extra_headers = {
        "Authorization": "%s %s" % (
            auth_header_token_type,
            token["access_token"]
        ),
    }
    response = requests.get(
        "%s/oauth2/userinfo" % config.TWITCH_API_URL,
        headers=extra_headers)
    logging.debug("fetch_twitch_user: headers: %s\n\traw response: %s" % (
        response.headers, response.text))

    twitch_avatar_url = None
    twitch_username = None
    twitch_id = None
    try:
        logging.debug("fetch_twitch_user response: %s" % response.text)
        parsed_response = json.loads(response.text)
        twitch_id = parsed_response["sub"]
        twitch_username = parsed_response["preferred_username"]
        twitch_avatar_url = parsed_response["picture"]
    except ValueError as e:
        logging.error("ValueError: " + e)
        return False

    ss = get_creds()
    # TODO: move away from "discord" to a generic auth provider
    session["discord"] = {
        "full_username": twitch_username,
        # TODO: get the right avatar from picture
        "avatar_url": twitch_avatar_url,
        "id": twitch_id,
        "authorized": twitch_id in ss["authorized_twitch_ids"]
    }
    return True
