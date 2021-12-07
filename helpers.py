import os
import requests
import urllib.parse
# import re
from flask import redirect, render_template, request, session
from functools import wraps

# Builds apology page with corresponding error message  
def apology(message, code=400):
    """Render message as an apology to user. """
    def escape(s):
        # Via https://github.com/jacebrowning/memegen#special-characters

        # Replaces special characters
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)

        return s

    # Renders apology template with corresponding error message
    return render_template("apology.html", top=code, bottom=escape(message))

# Decorate routes to require login.
def login_required(f):
    # https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function