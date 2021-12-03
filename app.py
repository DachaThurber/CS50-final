import os
from re import S
from random import randint

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask.helpers import make_response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///sleep.db")

# Make sure API key is set
#if not os.environ.get("API_KEY"):
#    raise RuntimeError("API_KEY not set")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def home():
    return apology("TODO")

# Not entirely sure GET and POST are both needed here
    # How to change when date is new???
@app.route("/wakeup", methods=["GET", "POST"])
@login_required
def wakeup():

    value = randint(1, 30)
    
    both = db.execute("SELECT quote, link FROM affirmations WHERE id=?", value)

    name = db.execute("SELECT username FROM users WHERE id=?", session["user_id"])

    return render_template("wakeup.html", quote=both[0]["quote"], link=both[0]["link"], name=name[0]["username"])

@app.route("/findfriends", methods=["GET", "POST"])
@login_required
def findfriends():
    
    if request.method == "POST":

        username = request.form.get("username")

        if not username:
            return apology("must provide valid username", 403)

        row = db.execute("SELECT id FROM users WHERE username = ?", username)

        # If user does not exist
        if not row:
            return apology("user does not exist", 403)

        follower_id = row[0]["id"]

        # Ensure username isn't current user's own ID
        if follower_id == session["user_id"]:
            return apology("cannot follow own account", 403)

        # Ensure user doesn't already follow other user
        check = db.execute("SELECT follower_id FROM followers WHERE followee_id = ?", session["user_id"])

        for x in check:
            if check[x]['follower_id'] == follower_id:
                return apology("you already follow this user", 403)

        db.execute("INSERT INTO followers(follower_id, followee_id) VALUES(?,?)", follower_id, session["user_id"])

        return render_template("ffsuccess.html", username=username)

    else:
        return render_template("findfriends.html")

@app.route("/report", methods=["GET", "POST"])
@login_required
def report():

    if request.method == "POST":

        date = request.form.get("date")
        bedtime = request.form.get("bedtime")
        wakeup = request.form.get("wakeup")
        rating = request.form.get("rating")

        # Ensure fields were submitted
        if not date:
            return apology("must provide date", 403)
        if not bedtime:
            return apology("must provide bedtime", 403)
        if not wakeup:
            return apology("must provide wakeup", 403)
        #if not rating:
            #return apology("must provide rating", 403)
        
        db.execute("INSERT INTO sleeplog(date, bedtime, wakeup, rating, user_id) VALUES (?, ?, ?, ?, ?)", date, bedtime, wakeup, rating, session["user_id"])

        return redirect("/")
    else:
        return render_template("report.html")


# Courtesy of https://medium.com/@rovai/from-data-to-graph-a-web-jorney-with-flask-and-sqlite-6c2ec9c0ad0
global numSamples
@app.route("/data", methods=["GET", "POST"])
def data():
    if request.method == "POST":
        global numSamples
        numSamples = maxRowsTable()
        if (numSamples > 101):
            numSamples = 100
        numSamples = int (request.form['numSamples'])
        numMaxSamples = maxRowsTable()
        if (numSamples > numMaxSamples):
            numSamples = (numMaxSamples-1)
        templateData = {
      		'numSamples'	: numSamples
	    }
        return render_template('data.html', **templateData) 
    else:
        return render_template("data.html")

def getHistData(numSamples):

    data = db.execute("SELECT * FROM sleeplog WHERE user_id = ? ORDER BY date DESC LIMIT "+str(numSamples), session["user_id"])
    dates = []
    bedtimes = []
    wakeups = []
    ratings = []

    for row in reversed(data):
        dates.append((list(row.values()))[0])
        bedtimes.append((list(row.values()))[1])
        wakeups.append((list(row.values()))[2])
        ratings.append((list(row.values()))[3])

    return dates, bedtimes, wakeups, ratings

def maxRowsTable():
    maxNumberRows = 2
    for row in db.execute("SELECT COUNT(bedtime) FROM sleeplog WHERE user_id = ?", session["user_id"]):
        maxNumberRows=((list(row.values()))[0])
        
    return maxNumberRows

@app.route('/plot/sleep_time')
def plot_temp():
	dates, bedtimes, wakeups, ratigns = getHistData(numSamples)
	ys = wakeups
	fig = Figure()
	axis = fig.add_subplot(1, 1, 1)
	axis.set_title("Sleep Time")
	axis.set_xlabel("Nights")
	axis.grid(True)
	xs = range(numSamples)
	axis.plot(xs, ys)
	canvas = FigureCanvas(fig)
	output = io.BytesIO()
	canvas.print_png(output)
	response = make_response(output.getvalue())
	response.mimetype = 'image/png'
	return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # Query database for existing usernames
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username is unique
        if len(rows) == 1:
            return apology("username already in use", 400)

        # Ensure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 400)

        # Store User's information
        username = request.form.get("username")
        hash = generate_password_hash(request.form.get("password"))
        country = request.form.get("country")
        state = request.form.get("state")
        gender = request.form.get("gender")
        birthday = request.form.get("birthday")
        if state != "":
            db.execute("INSERT INTO users (username, hash, country, state, gender, birthday) VALUES(?,?,?,?,?,?)", username, hash, country, state, gender, birthday)
        else:
            db.execute("INSERT INTO users (username, hash, country, gender, birthday) VALUES(?,?,?,?,?)", username, hash, country, gender, birthday)

        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
