from flask import session


def invalidate_session():
    keys_to_delete = [k for k in session.keys()]
    for k in keys_to_delete:
        del session[k]
